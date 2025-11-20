"""
LangChain Agent Service for HenryBot AI Assistant.
Handles chat interactions with stage streaming and tool usage.

Note: ConversationBufferMemory is deprecated in LangChain but still functional.
For production, consider migrating to LangGraph for state management.
"""

import logging
import warnings
from typing import AsyncGenerator, List, Dict, Any, Optional, Literal

# Suppress LangChain deprecation warnings - ConversationBufferMemory still works fine
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import BaseCallbackHandler
from translation_context import RALPH_DETAILS, EXAMPLE_TRANSLATIONS
from translation_service import perform_translation
from api_types import TranslateRequest, TranslationOptions
import os
from dotenv import load_dotenv
import json
import asyncio

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/mistral-small-3.2-24b-instruct")
AGENT_MODEL = os.getenv("AGENT_MODEL", "mistralai/mistral-small-3.2-24b-instruct")

# Define stage types
AgentStage = Literal[
    "thinking",          # Agent is analyzing the request
    "using_tool",        # Agent decided to use a tool
    "reading_code",      # Reading/parsing provided code
    "translating",       # Translating code (tool)
    "generating",        # Generating new code
    "fetching_docs",     # Fetching documentation
    "completing",        # Finalizing response
    "done"              # Response complete
]


class StreamEvent:
    """Factory for creating stream events."""
    
    @staticmethod
    def content(chunk: str) -> Dict[str, Any]:
        """Content chunk event."""
        return {
            "type": "content",
            "data": chunk
        }
    
    @staticmethod
    def stage(stage: AgentStage, message: str = "") -> Dict[str, Any]:
        """Stage change event."""
        stage_messages = {
            "thinking": "🤔 Analyzing your request...",
            "using_tool": "🔧 Preparing tools...",
            "reading_code": "📖 Reading your code...",
            "translating": "🔄 Translating to Ralph...",
            "generating": "✨ Generating code...",
            "fetching_docs": "📚 Fetching documentation...",
            "completing": "✅ Finalizing response...",
            "done": "✓ Complete"
        }
        
        return {
            "type": "stage",
            "data": {
                "stage": stage,
                "message": message or stage_messages.get(stage, "Processing...")
            }
        }
    
    @staticmethod
    def tool_start(tool_name: str, tool_input: str) -> Dict[str, Any]:
        """Tool execution start event."""
        return {
            "type": "tool_start",
            "data": {
                "tool": tool_name,
                "input": tool_input[:100] + "..." if len(tool_input) > 100 else tool_input
            }
        }
    
    @staticmethod
    def tool_end(tool_name: str, success: bool = True) -> Dict[str, Any]:
        """Tool execution end event."""
        return {
            "type": "tool_end",
            "data": {
                "tool": tool_name,
                "success": success
            }
        }
    
    @staticmethod
    def error(error_message: str) -> Dict[str, Any]:
        """Error event."""
        return {
            "type": "error",
            "data": {
                "message": error_message
            }
        }


class StreamingCallbackHandler(BaseCallbackHandler):
    """Custom callback handler to emit events during agent execution."""
    
    def __init__(self, event_queue: asyncio.Queue):
        super().__init__()
        self.event_queue = event_queue
        self.current_tool = None
    
    def on_llm_start(self, *args, **kwargs):
        """Called when LLM starts generating."""
        try:
            self.event_queue.put_nowait(StreamEvent.stage("thinking"))
        except Exception as e:
            logger.error(f"Error in on_llm_start: {e}")
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        """Called when a tool starts executing."""
        try:
            tool_name = serialized.get("name", "unknown")
            self.current_tool = tool_name
            
            # Map tool to stage
            stage_map = {
                "translate_evm_to_ralph": "translating",
                "get_ralph_documentation": "fetching_docs",
                "generate_ralph_template": "generating"
            }
            
            stage = stage_map.get(tool_name, "using_tool")
            self.event_queue.put_nowait(StreamEvent.stage(stage))
            self.event_queue.put_nowait(StreamEvent.tool_start(tool_name, input_str))
            logger.info(f"Tool started: {tool_name}")
        except Exception as e:
            logger.error(f"Error in on_tool_start: {e}")
    
    def on_tool_end(self, output: str, **kwargs):
        """Called when a tool finishes executing."""
        try:
            if self.current_tool:
                logger.info(f"Tool completed: {self.current_tool}")
                self.event_queue.put_nowait(StreamEvent.tool_end(self.current_tool))
                self.current_tool = None
            self.event_queue.put_nowait(StreamEvent.stage("completing"))
        except Exception as e:
            logger.error(f"Error in on_tool_end: {e}")
    
    def on_tool_error(self, error: Exception, **kwargs):
        """Called when a tool encounters an error."""
        try:
            if self.current_tool:
                logger.error(f"Tool error: {self.current_tool} - {error}")
                self.event_queue.put_nowait(StreamEvent.tool_end(self.current_tool, success=False))
                self.event_queue.put_nowait(StreamEvent.error(str(error)))
                self.current_tool = None
        except Exception as e:
            logger.error(f"Error in on_tool_error: {e}")


class ChatAgent:
    """
    LangChain agent for code generation and assistance with stage streaming.
    """
    
    def __init__(self):
        # Initialize LLM with streaming support
        self.llm = ChatOpenAI(
            model=AGENT_MODEL,
            temperature=0.7,
            streaming=True,
            api_key=API_KEY,
            base_url=API_URL.replace("/chat/completions", "") if API_URL else None,
        )
        
        # Define tools the agent can use
        self.tools = self._create_tools()
        
        # Create agent prompt
        self.prompt = self._create_prompt()
        
        # Create agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Session storage for conversation history
        self.sessions: Dict[str, ConversationBufferMemory] = {}
    
    def _create_tools(self) -> List[Tool]:
        """Create tools the agent can use."""
        
        async def translate_code_tool(code: str) -> str:
            """Translates EVM/Solidity code to Ralph language. This may take 1-2 minutes for complex contracts."""
            try:
                logger.info(f"Starting translation for code of length: {len(code)}")
                
                # Use smart mode for faster, better translations
                request = TranslateRequest(
                    source_code=code,
                    options=TranslationOptions(
                        optimize=False,
                        include_comments=True,
                        mimic_defaults=False,
                        translate_erc20=False,
                        smart=True  # Use the faster SMART_LLM_MODEL
                    )
                )
                
                translated = ""
                async for chunk, _, _, _ in perform_translation(request, stream=False):
                    translated += chunk
                
                logger.info(f"Translation completed. Output length: {len(translated)}")
                return f"Translated Ralph code:\n```ralph\n{translated}\n```"
            except Exception as e:
                logger.error(f"Translation tool error: {e}")
                return f"Error translating code: {str(e)}"
        
        def get_ralph_docs() -> str:
            """Returns Ralph language documentation and examples."""
            return f"Ralph Language Documentation:\n\n{RALPH_DETAILS[:3000]}\n\nExample Translations:\n\n{EXAMPLE_TRANSLATIONS[:2000]}"
        
        def generate_ralph_template(contract_type: str) -> str:
            """Generates a Ralph contract template based on type (token, nft, marketplace, etc.)."""
            templates = {
                "token": """Contract Token(symbol: ByteVec, name: ByteVec, decimals: U256, supply: U256) {
  
  event Transfer(from: Address, to: Address, amount: U256)
  
  @using(preapprovedAssets = true, checkExternalCaller = false)
  pub fn transfer(to: Address, amount: U256) -> () {
    transferTokenFromSelf!(to, selfTokenId!(), amount)
    emit Transfer(callerAddress!(), to, amount)
  }
  
  pub fn getSymbol() -> ByteVec {
    return symbol
  }
  
  pub fn getName() -> ByteVec {
    return name
  }
  
  pub fn getDecimals() -> U256 {
    return decimals
  }
  
  pub fn getTotalSupply() -> U256 {
    return supply
  }
}""",
                "nft": """Contract NFT(collectionId: ByteVec, mut owner: Address, mut tokenURI: ByteVec) {
  
  event Transfer(from: Address, to: Address, tokenId: ByteVec)
  
  @using(updateFields = true, checkExternalCaller = false)
  pub fn transferNFT(to: Address) -> () {
    checkCaller!(callerAddress!() == owner, ErrorCodes.Unauthorized)
    let oldOwner = owner
    owner = to
    emit Transfer(oldOwner, to, collectionId)
  }
  
  pub fn getOwner() -> Address {
    return owner
  }
  
  pub fn getTokenURI() -> ByteVec {
    return tokenURI
  }
  
  enum ErrorCodes {
    Unauthorized = 0
  }
}""",
                "marketplace": """Contract Marketplace(mut owner: Address) {
  
  mapping[ByteVec, Listing] listings
  
  struct Listing {
    seller: Address,
    price: U256,
    active: Bool
  }
  
  event ItemListed(tokenId: ByteVec, seller: Address, price: U256)
  event ItemSold(tokenId: ByteVec, seller: Address, buyer: Address, price: U256)
  
  @using(updateFields = true)
  pub fn listItem(tokenId: ByteVec, price: U256) -> () {
    assert!(!listings.contains!(tokenId), ErrorCodes.AlreadyListed)
    let listing = Listing { seller: callerAddress!(), price: price, active: true }
    listings.insert!(tokenId, listing)
    emit ItemListed(tokenId, callerAddress!(), price)
  }
  
  @using(preapprovedAssets = true, updateFields = true, checkExternalCaller = false)
  pub fn buyItem(tokenId: ByteVec) -> () {
    assert!(listings.contains!(tokenId), ErrorCodes.NotListed)
    let listing = listings[tokenId]
    assert!(listing.active, ErrorCodes.NotActive)
    
    transferTokenToSelf!(callerAddress!(), ALPH, listing.price)
    transferTokenFromSelf!(listing.seller, ALPH, listing.price)
    
    listings.remove!(callerAddress!(), tokenId)
    emit ItemSold(tokenId, listing.seller, callerAddress!(), listing.price)
  }
  
  enum ErrorCodes {
    AlreadyListed = 0,
    NotListed = 1,
    NotActive = 2
  }
}"""
            }
            
            return templates.get(contract_type.lower(), "Template not found. Available types: token, nft, marketplace")
        
        return [
            Tool(
                name="translate_evm_to_ralph",
                description="Translates EVM/Solidity smart contract code to Ralph language for Alephium blockchain. Use when user provides Solidity/EVM code.",
                func=translate_code_tool,
                coroutine=translate_code_tool
            ),
            Tool(
                name="get_ralph_documentation",
                description="Returns Ralph language documentation, syntax, built-in functions, and examples. Use when user asks about Ralph language features.",
                func=get_ralph_docs
            ),
            Tool(
                name="generate_ralph_template",
                description="Generates a Ralph contract template. Available types: token, nft, marketplace. Use when user wants to start a new contract.",
                func=generate_ralph_template
            )
        ]
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the agent prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are HenryBot, an expert AI assistant for Alephium blockchain development and Ralph smart contract programming.

Your capabilities:
- Translate EVM/Solidity code to Ralph language
- Answer questions about Ralph syntax and best practices
- Generate Ralph contract templates
- Debug and improve Ralph code
- Explain Alephium blockchain concepts

Ralph Language Context:
{ralph_context}

Guidelines:
- When using a tool that returns code (translate_evm_to_ralph, generate_ralph_template), ALWAYS include the full tool output in your response
- The tool output already contains the code - you should explain it briefly but MUST include the complete tool result
- Follow Ralph best practices (naming conventions, annotations, error handling)
- Be concise but thorough
- The user needs to see the actual code, not just a summary

IMPORTANT: When a tool returns translated code or a template, your response should be:
1. Brief intro (1 sentence)
2. The COMPLETE tool output (including all code)
3. Brief explanation of key points (2-3 sentences)

Current conversation:"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
    
    def get_or_create_memory(self, session_id: str) -> ConversationBufferMemory:
        """Get or create conversation memory for a session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                input_key="input",  # Specify which input key to use for memory
                output_key="output"  # Specify which output key to use for memory
            )
        return self.sessions[session_id]
    
    async def chat(
        self,
        message: str,
        session_id: str = "default",
        stream: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a chat message and yield streaming events.
        
        Args:
            message: User's message
            session_id: Session identifier for conversation history
            stream: Whether to stream the response
            
        Yields:
            Dict with event type and data
        """
        try:
            # Initial stage
            yield StreamEvent.stage("thinking", "Analyzing your request...")
            
            # Check if message contains code
            if "```" in message or any(keyword in message.lower() for keyword in ["translate", "convert", "code", "contract"]):
                yield StreamEvent.stage("reading_code", "Detecting code in your message...")
            
            memory = self.get_or_create_memory(session_id)
            
            # Create event queue for callback handler
            event_queue = asyncio.Queue()
            callback_handler = StreamingCallbackHandler(event_queue)
            
            # Create agent executor
            agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5,
                callbacks=[callback_handler],
                return_intermediate_steps=True  # Include tool outputs in the stream
            )
            
            # Prepare inputs
            inputs = {
                "input": message,
                "ralph_context": f"{RALPH_DETAILS[:2000]}..."
            }
            
            if stream:
                # Create tasks for agent execution and event processing
                async def process_agent():
                    try:
                        async for chunk in agent_executor.astream(inputs):
                            # Handle different chunk types
                            if "output" in chunk:
                                # Final agent response
                                await event_queue.put(StreamEvent.content(chunk["output"]))
                            elif "steps" in chunk:
                                # Intermediate tool outputs
                                for step in chunk["steps"]:
                                    if hasattr(step, "observation") and step.observation:
                                        # Send tool output as content
                                        logger.info(f"Sending tool observation to frontend: {len(step.observation)} chars")
                                        await event_queue.put(StreamEvent.content(step.observation + "\n\n"))
                            elif "actions" in chunk:
                                # Log actions being taken
                                for action in chunk["actions"]:
                                    logger.info(f"Agent taking action: {action.tool}")
                        
                        # Signal completion
                        await event_queue.put(StreamEvent.stage("done"))
                        await event_queue.put(None)  # Sentinel to stop queue processing
                    except Exception as e:
                        logger.error(f"Agent execution error: {e}", exc_info=True)
                        await event_queue.put(StreamEvent.error(str(e)))
                        await event_queue.put(None)
                
                # Start agent processing
                agent_task = asyncio.create_task(process_agent())
                
                # Yield events from queue with timeout to prevent hanging
                last_event_time = asyncio.get_event_loop().time()
                while True:
                    try:
                        # Wait for event with timeout
                        event = await asyncio.wait_for(event_queue.get(), timeout=15.0)
                        if event is None:  # Sentinel value
                            break
                        yield event
                        last_event_time = asyncio.get_event_loop().time()
                    except asyncio.TimeoutError:
                        # Send keep-alive update if no events for 15 seconds
                        current_time = asyncio.get_event_loop().time()
                        if current_time - last_event_time > 10:
                            # Check if task is still running
                            if not agent_task.done():
                                yield StreamEvent.stage("translating", "🔄 Still translating... Complex contracts take 1-2 minutes")
                                last_event_time = current_time
                
                # Wait for agent to finish
                await agent_task
            else:
                # Non-streaming response
                yield StreamEvent.stage("generating")
                result = await agent_executor.ainvoke(inputs)
                yield StreamEvent.content(result["output"])
                yield StreamEvent.stage("done")
                
        except Exception as e:
            logger.error(f"Chat agent error: {e}", exc_info=True)
            yield StreamEvent.error(f"I encountered an error: {str(e)}. Please try rephrasing your question.")
    
    def clear_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")


# Global agent instance
_agent: Optional[ChatAgent] = None


def get_agent() -> ChatAgent:
    """Get or create the global chat agent instance."""
    global _agent
    if _agent is None:
        logger.info("Initializing ChatAgent...")
        _agent = ChatAgent()
        logger.info("ChatAgent initialized successfully")
    return _agent
