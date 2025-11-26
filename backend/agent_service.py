"""
LangChain v1 Agent Service for HenryBot AI Assistant.
Handles chat interactions with streaming and tool usage.
"""

import asyncio
import json
import logging
import os
import re
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from api_types import TranslateRequest, TranslationOptions
from translation_service import SYSTEM_PROMPT as TRANSLATION_SYSTEM_PROMPT
from translation_service import perform_translation

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
log_level = os.getenv("LOG_LEVEL", "WARNING")
logger.setLevel(getattr(logging, log_level.upper()))
# Create console handler if not already present
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/mistral-small-3.2-24b-instruct")
AGENT_MODEL = os.getenv("AGENT_MODEL", "mistralai/mistral-small-3.2-24b-instruct")


# Global context for current session during tool execution
_current_session_options: Optional[Dict[str, Any]] = None


def get_current_session_options() -> Dict[str, Any]:
    """
    Get translation options from current session context.
    
    Returns:
        Dictionary with translation options (optimize, include_comments, etc.)
        Returns default values if no session context is set.
    """
    if _current_session_options:
        return _current_session_options
    # Return default options
    return {
        "optimize": False,
        "include_comments": True,
        "mimic_defaults": False,
        "smart": False,
        "translate_erc20": False,
    }


def set_session_options_context(options: Optional[Dict[str, Any]]) -> None:
    """
    Set current session options context for tool execution.
    
    Args:
        options: Dictionary with translation options or None to clear context
    """
    global _current_session_options
    _current_session_options = options


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
    """
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
    "thinking",
    "using_tool",
    "reading_code",
    "preprocessing",
    "translating",
    "generating",
    "fetching_docs",
    "completing",
    "done",
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


class ChatAgent:
    """LangChain v1 agent for code generation and assistance."""

    def __init__(self):
        """Initialize the agent with tools."""
        self.llm = ChatOpenAI(
            model=AGENT_MODEL,
            temperature=0.7,
            api_key=API_KEY,
            base_url=API_URL.replace("/chat/completions", "") if API_URL else None,
        )

        # Define tools
        self.tools = self._create_tools()

        # Create agent using create_agent
        self.system_prompt = self._get_system_prompt()
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

        # Session storage for conversation history
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        
        # Session storage for translation options
        self.session_options: Dict[str, Dict[str, Any]] = {}

    def _create_tools(self) -> List:
        """Create tools the agent can use."""

        @tool
        def resolve_solidity_imports(code: str) -> str:
            """
            Resolves Solidity import statements by replacing them with actual contract code.
            CRITICAL: ALWAYS use this tool FIRST if the code contains 'import' statements.
            """
            try:
                logger.warning(f"Resolving imports for code of length: {len(code)}")

                if "import" not in code:
                    logger.warning("No imports detected in code")
                    return "✓ No imports detected. Code is ready for translation."

                from translate_oz import replace_imports

                # Extract imports from each line
                imports = [parse_import_line(line) for line in code.split("\n")]
                imports = [imp for imp in imports if imp]

                if not imports:
                    logger.warning("No import statements found in code")
                    return "✓ No import statements found. Code is ready for translation."

                logger.warning(f"Found {len(imports)} import(s): {imports}")

                # Replace imports with their implementations
                replacement_text = replace_imports(imports)

                # Remove import lines from code
                code_lines = code.split("\n")
                code_without_imports = "\n".join([line for line in code_lines if not line.strip().startswith("import ")])
                preprocessed_code = f"{replacement_text}\n\n{code_without_imports}"

                logger.warning(f"Imports resolved. New code length: {len(preprocessed_code)}")

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
                return f"❌ Error resolving imports: {str(e)}"

        @tool
        def translate_evm_to_ralph(code: str) -> str:
            """
            Translates EVM/Solidity code to Ralph language for Alephium blockchain.
            
            Uses the translation preferences set by the user at the beginning of the conversation.
            These preferences control optimization, comments, and other translation behaviors.

            IMPORTANT: If the code contains 'import' statements, use resolve_solidity_imports FIRST.
            """
            try:
                logger.warning(f"Starting translation for code of length: {len(code)}")

                # Safety fallback: check if imports are still present
                if "import" in code and ("@openzeppelin" in code.lower() or ".sol" in code):
                    logger.warning("⚠️ Code contains imports but wasn't preprocessed! Preprocessing now...")
                    from translate_oz import replace_imports

                    imports = [parse_import_line(line) for line in code.split("\n")]
                    imports = [imp for imp in imports if imp]

                    if imports:
                        logger.warning(f"Fallback preprocessing: Found {len(imports)} import(s)")
                        replacement_text = replace_imports(imports)
                        code_lines = code.split("\n")
                        code = "\n".join([line for line in code_lines if not line.strip().startswith("import ")])
                        code = f"{replacement_text}\n\n{code}"
                        logger.warning("Fallback preprocessing completed")

                # Get options from session context
                session_opts = get_current_session_options()
                logger.warning(f"Using session options: {session_opts}")

                # Create translation request with session options
                request = TranslateRequest(
                    source_code=code,
                    options=TranslationOptions(
                        optimize=session_opts.get("optimize", False),
                        include_comments=session_opts.get("include_comments", True),
                        mimic_defaults=session_opts.get("mimic_defaults", False),
                        translate_erc20=session_opts.get("translate_erc20", False),
                        smart=session_opts.get("smart", False),
                    ),
                )

                translated = ""

                async def _get_translation():
                    result = ""
                    async for chunk, _, _, _ in perform_translation(request, stream=False):
                        result += chunk
                    return result

                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                translated = loop.run_until_complete(_get_translation())

                logger.warning(f"Translation completed. Output length: {len(translated)}")
                return f"Translated Ralph code:\n```ralph\n{translated}\n```\n\n"
            except Exception as e:
                logger.error(f"Translation tool error: {e}", exc_info=True)
                return f"Error translating code: {str(e)}"

        @tool
        def get_ralph_documentation() -> str:
            """Returns Ralph language documentation and examples."""
            return TRANSLATION_SYSTEM_PROMPT

        @tool
        def generate_ralph_template(contract_type: str) -> str:
            """Generates a Ralph contract template (token, nft, marketplace)."""
            templates = {
                "token": """### Ralph Token Template

```ralph
Contract Token(symbol: ByteVec, name: ByteVec, decimals: U256, supply: U256) {
    event Transfer(from: Address, to: Address, amount: U256)

    @using(preapprovedAssets = true, checkExternalCaller = false)
    pub fn transfer(to: Address, amount: U256) -> () {
        transferTokenFromSelf!(to, selfTokenId!(), amount)
        emit Transfer(callerAddress!(), to, amount)
    }
}
```

Key features:
- Constructor parameters capture token metadata and initial supply
- `transfer` uses `transferTokenFromSelf!` to move the native token held by the contract
- Emits a `Transfer` event that matches common token semantics

Extend this template with tracking state (balances, allowances) for a fully fledged FT.
""",
                "nft": """### Ralph NFT Template

```ralph
Contract NFT(collectionId: ByteVec, mut owner: Address, mut tokenURI: ByteVec) {
    event Transfer(from: Address, to: Address, tokenId: ByteVec)

    @using(updateFields = true, checkExternalCaller = false)
    pub fn transferNFT(to: Address) -> () {
        checkCaller!(callerAddress!() == owner, ErrorCodes.Unauthorized)
        owner = to
        emit Transfer(callerAddress!(), to, collectionId)
    }

    enum ErrorCodes {
        Unauthorized = 0
    }
}
```

Extend with metadata storage, minting helpers, or royalties as needed.
""",
                "marketplace": """### Ralph Marketplace Template

```ralph
Contract Marketplace(mut owner: Address) {
    mapping[ByteVec, Listing] listings

    struct Listing {
        seller: Address,
        price: U256,
        active: Bool
    }

    @using(updateFields = true)
    pub fn listItem(tokenId: ByteVec, price: U256) -> () {
        assert!(!listings.contains!(tokenId), ErrorCodes.AlreadyListed)
        listings.insert!(tokenId, Listing { seller: callerAddress!(), price: price, active: true })
    }

    enum ErrorCodes {
        AlreadyListed = 0
    }
}
```

Add buying, cancelation, and fee logic to suit your use case.
""",
            }

            return templates.get(contract_type.lower(), "Template not found. Available: token, nft, marketplace")

        return [resolve_solidity_imports, translate_evm_to_ralph, get_ralph_documentation, generate_ralph_template]

    def _get_system_prompt(self) -> str:
        """Build the system prompt for the agent."""
        return (
            "You are HenryBot, an expert AI assistant for Alephium blockchain development and Ralph smart contract programming.\n\n"
            f"{TRANSLATION_SYSTEM_PROMPT}\n\n"
            "Your capabilities:\n"
            "- Translate EVM/Solidity code to Ralph language\n"
            "- Resolve Solidity import statements (OpenZeppelin, etc.)\n"
            "- Answer questions about Ralph syntax and best practices\n"
            "- Generate Ralph contract templates\n"
            "- Debug and improve Ralph code\n\n"
            "CRITICAL WORKFLOW FOR CODE WITH IMPORTS:\n"
            "1. Check if the code contains 'import' statements\n"
            "2. If YES → ALWAYS use resolve_solidity_imports tool FIRST\n"
            "3. Then use translate_evm_to_ralph with the preprocessed code\n"
            "4. If NO imports → directly use translate_evm_to_ralph\n\n"
            "When using tools that return code, include the full output in your response."
        )

    async def chat(
        self,
        message: str,
        session_id: str = "default",
        stream: bool = True,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a chat message and yield streaming events.

        Args:
            message: User's message
            session_id: Session identifier for conversation history
            stream: Whether to stream the response
            options: Translation options (stored in session on first message)

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

            # Get or create message history for this session
            if session_id not in self.sessions:
                self.sessions[session_id] = []

            # Store options if provided (typically on first message)
            if options is not None:
                self.set_session_options(session_id, options)
                logger.info(f"Options set for session {session_id}: {options}")

            # Set session context for tools to access
            session_opts = self.get_session_options(session_id)
            set_session_options_context(session_opts)
            logger.info(f"Session context set with options: {session_opts}")

            # Invoke the agent with streaming
            full_response = ""
            try:
                yield StreamEvent.stage("generating", "Processing...")

                # Stream events from the agent directly
                async for event in self.agent.astream_events({"messages": [{"role": "user", "content": message}]}):
                    event_type = event.get("event")

                    if event_type == "on_tool_start":
                        tool_name = event.get("name", "unknown")
                        yield StreamEvent.stage("using_tool")
                        yield StreamEvent.tool_start(tool_name, message[:100])

                    elif event_type == "on_tool_end":
                        tool_name = event.get("name", "unknown")
                        tool_data = event.get("data", {})
                        tool_output = tool_data.get("output")
                        
                        # ✅ Extract string content from ToolMessage
                        if tool_output:
                            # ToolMessage has a .content attribute with the actual string
                            if hasattr(tool_output, 'content'):
                                output_text = tool_output.content
                            elif isinstance(tool_output, str):
                                output_text = tool_output
                            elif isinstance(tool_output, dict):
                                output_text = tool_output.get("output", "")
                            else:
                                # Fallback: convert to string
                                output_text = str(tool_output)
                            
                            # Now send the string, not the ToolMessage object
                            if tool_name == "translate_evm_to_ralph" and output_text:
                                yield StreamEvent.content(output_text)
                        yield StreamEvent.tool_end(tool_name)

                    elif event_type == "on_chat_model_stream":
                        chunk = event.get("data", {}).get("chunk")
                        if chunk and hasattr(chunk, "content"):
                            content = chunk.content
                            if content:
                                full_response += content
                                yield StreamEvent.content(content)

                    elif event_type == "on_chain_end":
                        output = event.get("data", {}).get("output")
                        if isinstance(output, str):
                            final_text = output
                        elif isinstance(output, dict):
                            final_text = output.get("output", "")
                        else:
                            final_text = str(output)

                        if final_text:
                            full_response += final_text
                            yield StreamEvent.content(final_text)

                # Store message in history
                self.sessions.setdefault(session_id, [])
                self.sessions[session_id].append({"role": "user", "content": message})
                self.sessions[session_id].append({"role": "assistant", "content": full_response})

                yield StreamEvent.stage("done")

            except Exception as e:
                logger.error(f"Agent invocation error: {e}", exc_info=True)
                yield StreamEvent.error(f"Error: {str(e)}")
            finally:
                # Clean up session context after execution
                set_session_options_context(None)
                logger.info("Session context cleaned up")

        except Exception as e:
            logger.error(f"Chat agent error: {e}", exc_info=True)
            yield StreamEvent.error(f"Error: {str(e)}")

    def set_session_options(self, session_id: str, options: Dict[str, Any]) -> None:
        """
        Store translation options for a session.
        
        Args:
            session_id: Session identifier
            options: Dictionary with translation options
        """
        self.session_options[session_id] = options
        logger.info(f"Stored options for session {session_id}: {options}")

    def get_session_options(self, session_id: str) -> Dict[str, Any]:
        """
        Get translation options for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with translation options or default values
        """
        return self.session_options.get(session_id, {
            "optimize": False,
            "include_comments": True,
            "mimic_defaults": False,
            "smart": False,
            "translate_erc20": False,
        })

    def clear_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
        if session_id in self.session_options:
            del self.session_options[session_id]
            logger.info(f"Cleared options for session: {session_id}")


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
