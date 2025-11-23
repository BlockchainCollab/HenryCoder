"""
LangChain Agent Service for HenryBot AI Assistant.
Handles chat interactions with stage streaming and tool usage.

Note: ConversationBufferMemory is deprecated in LangChain but still functional.
For production, consider migrating to LangGraph for state management.
"""

import asyncio
import json
import logging
import os
import re
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional

import httpx
from dotenv import load_dotenv
from langchain.agents import create_agent, AgentState
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from api_types import TranslateRequest, TranslationOptions
from translation_service import SYSTEM_PROMPT as TRANSLATION_SYSTEM_PROMPT
from translation_service import perform_translation

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
# Create console handler if not already present
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/mistral-small-3.2-24b-instruct")
AGENT_MODEL = os.getenv("AGENT_MODEL", "mistralai/mistral-small-3.2-24b-instruct")


def parse_import_line(line: str) -> str:
    """
    Extracts the import path from a Solidity import statement.

    Supports:
      - Simple: import "path";
      - Named: import {A, B} from "path";
      - Wildcard: import * as name from 'path';

    Args:
        line: A single line of Solidity code

    Returns:
        The import path (without quotes), or empty string if not a valid import.

    Examples:
        >>> parse_import_line('import "@openzeppelin/contracts/token/ERC20/ERC20.sol";')
        '@openzeppelin/contracts/token/ERC20/ERC20.sol'
        >>> parse_import_line('import {SignatureChecker} from "@openzeppelin/contracts/utils/cryptography/SignatureChecker.sol";')
        '@openzeppelin/contracts/utils/cryptography/SignatureChecker.sol'
        >>> parse_import_line('import * as SafeMath from "hardhat/console.sol";')
        'hardhat/console.sol'
        >>> parse_import_line('not an import')
        ''
    """
    import re

    line = line.strip()
    if not line.startswith("import "):
        return ""

    # Try "from" style: import ... from "path" or import ... from 'path'
    match = re.search(r'from\s+["\']([^"\']+)["\']', line)
    if match:
        return match.group(1)

    # Try simple style: import "path" or import 'path'
    match = re.search(r'import\s+["\']([^"\']+)["\']', line)
    if match:
        return match.group(1)

    return ""


# Define stage types
AgentStage = Literal[
    "thinking",  # Agent is analyzing the request
    "using_tool",  # Agent decided to use a tool
    "reading_code",  # Reading/parsing provided code
    "preprocessing",  # Resolving imports
    "translating",  # Translating code (tool)
    "generating",  # Generating new code
    "fetching_docs",  # Fetching documentation
    "completing",  # Finalizing response
    "done",  # Response complete
]


class StreamEvent:
    """Factory for creating stream events."""

    @staticmethod
    def content(chunk: str) -> Dict[str, Any]:
        """Content chunk event."""
        return {"type": "content", "data": chunk}

    @staticmethod
    def stage(stage: AgentStage, message: str = "") -> Dict[str, Any]:
        """Stage change event."""
        stage_messages = {
            "thinking": "🤔 Analyzing your request...",
            "using_tool": "🔧 Preparing tools...",
            "reading_code": "📖 Reading your code...",
            "preprocessing": "📦 Resolving imports...",
            "translating": "🔄 Translating to Ralph...",
            "generating": "✨ Generating code...",
            "fetching_docs": "📚 Fetching documentation...",
            "completing": "✅ Finalizing response...",
            "done": "✓ Complete",
        }

        return {
            "type": "stage",
            "data": {"stage": stage, "message": message or stage_messages.get(stage, "Processing...")},
        }

    @staticmethod
    def tool_start(tool_name: str, tool_input: str) -> Dict[str, Any]:
        """Tool execution start event."""
        return {
            "type": "tool_start",
            "data": {"tool": tool_name, "input": tool_input[:100] + "..." if len(tool_input) > 100 else tool_input},
        }

    @staticmethod
    def tool_end(tool_name: str, success: bool = True) -> Dict[str, Any]:
        """Tool execution end event."""
        return {"type": "tool_end", "data": {"tool": tool_name, "success": success}}

    @staticmethod
    def error(error_message: str) -> Dict[str, Any]:
        """Error event."""
        return {"type": "error", "data": {"message": error_message}}


class StreamingCallbackHandler:
    """Placeholder for v1 - callbacks are handled differently via streaming."""
    pass


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
        self.agent = create_openai_tools_agent(llm=self.llm, tools=self.tools, prompt=self.prompt)

        # Session storage for conversation history
        self.sessions: Dict[str, ConversationBufferMemory] = {}

    def _create_tools(self) -> List[Tool]:
        """Create tools the agent can use."""

        def resolve_imports_tool(code: str) -> str:
            """
            Resolves Solidity import statements by replacing them with actual contract code.
            CRITICAL: ALWAYS use this tool FIRST if the code contains 'import' statements.
            Supports OpenZeppelin imports like '@openzeppelin/contracts/token/ERC20/ERC20.sol'.
            Returns the code with all imports replaced by their actual implementation.
            """
            try:
                logger.info(f"Resolving imports for code of length: {len(code)}")

                # Check if code has imports
                if "import" not in code:
                    logger.info("No imports detected in code")
                    return "✓ No imports detected. Code is ready for translation."

                # Import the preprocessing function
                from translate_oz import replace_imports

                # Extract imports from each line using the module-level parser
                imports = [parse_import_line(line) for line in code.split("\n")]
                imports = [imp for imp in imports if imp]  # Filter out empty strings

                if not imports:
                    logger.info("No import statements found in code")
                    return "✓ No import statements found. Code is ready for translation."

                logger.info(f"Found {len(imports)} import(s): {imports}")

                # Replace imports with their implementations
                replacement_text = replace_imports(imports)

                # Remove import lines from code (any line starting with 'import ')
                code_lines = code.split("\n")
                code_without_imports = "\n".join(
                    [line for line in code_lines if not line.strip().startswith("import ")]
                )
                preprocessed_code = f"{replacement_text}\n\n{code_without_imports}"

                logger.info(f"Imports resolved. New code length: {len(preprocessed_code)}")

                return f"""✓ Imports successfully resolved!

Found and resolved {len(imports)} import(s):
{chr(10).join(f'  - {imp}' for imp in imports)}

Preprocessed code (ready for translation):
```solidity
{preprocessed_code}
```

NEXT STEP: Use translate_evm_to_ralph with this preprocessed code."""

            except Exception as e:
                logger.error(f"Import resolution error: {e}", exc_info=True)
                return f"❌ Error resolving imports: {str(e)}\n\nThe code can still be translated, but imports won't be resolved."

        async def translate_code_tool(code: str) -> str:
            """
            Translates EVM/Solidity code to Ralph language for Alephium blockchain.

            IMPORTANT: If the code contains 'import' statements, you should use resolve_solidity_imports FIRST,
            then use this tool with the preprocessed code.

            This tool may take 1-2 minutes for complex contracts.
            """
            try:
                logger.info(f"Starting translation for code of length: {len(code)}")

                # Safety fallback: check if imports are still present
                if "import" in code and ("@openzeppelin" in code.lower() or ".sol" in code):
                    logger.warning("⚠️ Code contains imports but wasn't preprocessed! Preprocessing now as fallback...")
                    from translate_oz import replace_imports

                    # Extract imports from each line using the module-level parser
                    imports = [parse_import_line(line) for line in code.split("\n")]
                    imports = [imp for imp in imports if imp]  # Filter out empty strings

                    if imports:
                        logger.info(f"Fallback preprocessing: Found {len(imports)} import(s)")
                        replacement_text = replace_imports(imports)
                        # Remove import lines from code
                        code_lines = code.split("\n")
                        code = "\n".join([line for line in code_lines if not line.strip().startswith("import ")])
                        code = f"{replacement_text}\n\n{code}"
                        logger.info("Fallback preprocessing completed")

                # Use smart mode for faster, better translations
                request = TranslateRequest(
                    source_code=code,
                    options=TranslationOptions(
                        optimize=False,
                        include_comments=True,
                        mimic_defaults=False,
                        translate_erc20=False,
                        smart=True,  # Use the faster SMART_LLM_MODEL
                    ),
                )

                translated = ""
                async for chunk, _, _, _ in perform_translation(request, stream=False):
                    translated += chunk

                logger.info(f"Translation completed. Output length: {len(translated)}")
                return f"Translated Ralph code:\n```ralph\n{translated}\n```"
            except Exception as e:
                logger.error(f"Translation tool error: {e}", exc_info=True)
                return f"Error translating code: {str(e)}"

        def get_ralph_docs() -> str:
            """Returns Ralph language documentation and examples."""
            # Return the full translation system prompt which contains all Ralph documentation
            return TRANSLATION_SYSTEM_PROMPT

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
}""",
            }

            return templates.get(contract_type.lower(), "Template not found. Available types: token, nft, marketplace")

        return [
            Tool(
                name="resolve_solidity_imports",
                description="""CRITICAL: ALWAYS use this tool FIRST if Solidity code contains 'import' statements!
                
Resolves Solidity imports (especially OpenZeppelin like '@openzeppelin/contracts/...') by replacing them with actual contract code.

When to use:
- Code contains 'import' keyword
- Code has '@openzeppelin' imports
- Code references external .sol files
- ALWAYS before calling translate_evm_to_ralph if imports are present

Returns: Solidity imports translated to Ralph.""",
                func=resolve_imports_tool,
            ),
            Tool(
                name="translate_evm_to_ralph",
                description="""Translates EVM/Solidity smart contract code to Ralph language for Alephium blockchain.

IMPORTANT WORKFLOW:
1. If code has imports → FIRST use resolve_solidity_imports
2. Then use this tool with the preprocessed code

Use when: User provides Solidity/EVM code to translate.
Note: Takes 1-2 minutes for complex contracts.""",
                func=translate_code_tool,
                coroutine=translate_code_tool,
            ),
            Tool(
                name="get_ralph_documentation",
                description="Returns Ralph language documentation, syntax, built-in functions, and examples. Use when user asks about Ralph language features.",
                func=get_ralph_docs,
            ),
            Tool(
                name="generate_ralph_template",
                description="Generates a Ralph contract template. Available types: token, nft, marketplace. Use when user wants to start a new contract.",
                func=generate_ralph_template,
            ),
        ]

    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the agent prompt template using the translation system prompt."""
        # Use the same Ralph documentation that the translation service uses
        # Escape curly braces in the translation prompt to avoid template variable conflicts
        escaped_translation_prompt = TRANSLATION_SYSTEM_PROMPT.replace("{", "{{").replace("}", "}}")

        # Build the system message by concatenating parts
        system_message_parts = [
            "You are HenryBot, an expert AI assistant for Alephium blockchain development and Ralph smart contract programming.\n\n",
            escaped_translation_prompt,
            "\n\nYour capabilities:\n",
            "- Translate EVM/Solidity code to Ralph language\n",
            "- Resolve Solidity import statements (OpenZeppelin, etc.)\n",
            "- Answer questions about Ralph syntax and best practices\n",
            "- Generate Ralph contract templates\n",
            "- Debug and improve Ralph code\n",
            "- Explain Alephium blockchain concepts\n\n",
            "CRITICAL WORKFLOW FOR CODE WITH IMPORTS:\n",
            "1. Check if the code contains 'import' statements\n",
            "2. If YES → ALWAYS use resolve_solidity_imports tool FIRST\n",
            "3. Then use translate_evm_to_ralph with the preprocessed code from step 2\n",
            "4. If NO imports → directly use translate_evm_to_ralph\n\n",
            "Example:\n",
            "User provides: import '@openzeppelin/contracts/token/ERC20/ERC20.sol'; contract Token is ERC20 {{}}\n",
            "Step 1: Use resolve_solidity_imports → Get preprocessed code\n",
            "Step 2: Use translate_evm_to_ralph with preprocessed code → Get Ralph translation\n",
            "NEVER skip resolve_solidity_imports if imports are present!\n\n",
            "Guidelines:\n",
            "- When using a tool that returns code (translate_evm_to_ralph, generate_ralph_template), ALWAYS include the full tool output in your response\n",
            "- The tool output already contains the code - you should explain it briefly but MUST include the complete tool result\n",
            "- Follow Ralph best practices (naming conventions, annotations, error handling)\n",
            "- Be concise but thorough\n",
            "- The user needs to see the actual code, not just a summary\n\n",
            "IMPORTANT: When a tool returns translated code or a template, your response should be:\n",
            "1. Brief intro (1 sentence)\n",
            "2. The COMPLETE tool output (including all code)\n",
            "3. Brief explanation of key points (2-3 sentences)\n\n",
            "Current conversation:",
        ]
        system_message = "".join(system_message_parts)

        return ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

    def get_or_create_memory(self, session_id: str) -> ConversationBufferMemory:
        """Get or create conversation memory for a session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                input_key="input",  # Specify which input key to use for memory
                output_key="output",  # Specify which output key to use for memory
            )
        return self.sessions[session_id]

    async def chat(
        self, message: str, session_id: str = "default", stream: bool = True
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
            if "```" in message or any(
                keyword in message.lower() for keyword in ["translate", "convert", "code", "contract"]
            ):
                yield StreamEvent.stage("reading_code", "Detecting code in your message...")

            memory = self.get_or_create_memory(session_id)

            # Create event queue for callback handler
            event_queue = asyncio.Queue()
            callback_handler = StreamingCallbackHandler(event_queue)

            logger.info(f"Created callback handler: {callback_handler}")
            logger.info(f"Available callback methods: {[m for m in dir(callback_handler) if m.startswith('on_')]}")

            # Create agent executor
            agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5,
                callbacks=[callback_handler],
                return_intermediate_steps=True,  # Include tool outputs in the stream
            )

            logger.info(f"Agent executor created with {len(agent_executor.callbacks)} callbacks")

            # Prepare inputs - Ralph context is now in the system prompt
            inputs = {"input": message}

            if stream:
                # Create tasks for agent execution and event processing
                async def process_agent():
                    try:
                        logger.info("Starting agent stream...")
                        async for chunk in agent_executor.astream(inputs):
                            logger.info(f"Received chunk with keys: {list(chunk.keys())}")

                            # Handle different chunk types
                            if "actions" in chunk:
                                # This comes BEFORE tool execution
                                logger.info(f"Actions chunk with {len(chunk['actions'])} actions")
                                for action in chunk["actions"]:
                                    tool_name = action.tool
                                    logger.info(f"Agent taking action: {tool_name}")

                                    # Manually emit tool_start event since callbacks might not fire in astream
                                    stage_map = {
                                        "resolve_solidity_imports": "preprocessing",
                                        "translate_evm_to_ralph": "translating",
                                        "get_ralph_documentation": "fetching_docs",
                                        "generate_ralph_template": "generating",
                                    }
                                    stage = stage_map.get(tool_name, "using_tool")
                                    await event_queue.put(StreamEvent.stage(stage))
                                    await event_queue.put(
                                        StreamEvent.tool_start(tool_name, str(action.tool_input)[:100])
                                    )

                            elif "steps" in chunk:
                                # This comes AFTER tool execution
                                logger.info(f"Steps chunk with {len(chunk['steps'])} steps")
                                for step in chunk["steps"]:
                                    if hasattr(step, "action"):
                                        tool_name = step.action.tool
                                        logger.info(f"Step completed for tool: {tool_name}")
                                        # Manually emit tool_end event
                                        await event_queue.put(StreamEvent.tool_end(tool_name))

                                    if hasattr(step, "observation") and step.observation:
                                        # Send tool output as content
                                        logger.info(
                                            f"Sending tool observation to frontend: {len(step.observation)} chars"
                                        )
                                        await event_queue.put(StreamEvent.content(step.observation + "\n\n"))

                            elif "output" in chunk:
                                # Final agent response
                                logger.info(f"Final output chunk: {len(chunk['output'])} chars")
                                await event_queue.put(StreamEvent.content(chunk["output"]))

                        logger.info("Agent stream completed")
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
                                yield StreamEvent.stage(
                                    "translating", "🔄 Still translating... Complex contracts take 1-2 minutes"
                                )
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
