"""
LangChain v1 Agent Service for HenryBot AI Assistant.
Handles chat interactions with streaming and tool usage.
Using Reworked Agentic System V2 with granular state manipulation tools.
"""
import aiohttp
import asyncio
import logging
import os
import queue
import re
from typing import Any, AsyncGenerator, Callable, Dict, List, Literal, Optional, Tuple, Union

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field as PydanticField, field_validator

from api_types import TranslateRequest, TranslationOptions
from translation_context import RALPH_DETAILS
from translation_service import SYSTEM_PROMPT as TRANSLATION_SYSTEM_PROMPT

# Type for translation chunk callback
TranslationChunkCallback = Callable[[str], None]

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
AGENT_MODEL = os.getenv("AGENT_MODEL", "mistralai/mistral-small-3.2-24b-instruct")
LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/devstral-2512:free")

# --- Global Context Management ---

_current_session_options: Optional[Dict[str, Any]] = None
_current_translation_queue: Optional[asyncio.Queue] = None
_current_session_id: Optional[str] = None

def get_current_session_options() -> Dict[str, Any]:
    if _current_session_options:
        return _current_session_options
    return {
        "optimize": False,
        "include_comments": True,
        "mimic_defaults": False,
        "smart": False,
        "translate_erc20": False,
    }

def set_session_options_context(options: Optional[Dict[str, Any]]) -> None:
    global _current_session_options
    _current_session_options = options

def get_translation_queue() -> Optional[asyncio.Queue]:
    return _current_translation_queue

def set_translation_queue(q: Optional[asyncio.Queue]) -> None:
    global _current_translation_queue
    _current_translation_queue = q

def set_current_session_id(session_id: Optional[str]) -> None:
    global _current_session_id
    _current_session_id = session_id

async def emit_translation_chunk(chunk: str) -> None:
    queue = get_translation_queue()
    if queue is not None:
        await queue.put({"type": "translation_chunk", "data": chunk})

# --- New Data Structures for Ralph AST ---

class Field(BaseModel):
    name: str = PydanticField(..., description="Name of the field")
    type: str = PydanticField(..., description="Ralph type of the field (e.g. U256, Address, Bool)")

class MapDef(BaseModel):
    key_type: Literal["Bool", "U256", "I256", "Address", "ByteVec"]
    value_type: str

class Constant(BaseModel):
    name: str
    type: str
    value: str

class EnumValue(BaseModel):
    name: str
    value: int

class RalphEnum(BaseModel):
    name: str
    values: List[EnumValue]

class RalphEvent(BaseModel):
    name: str
    fields: List[Field]

# --- Tool Input Schemas ---

class EventDef(BaseModel):
    name: str = PydanticField(..., description="Name of the event")
    fields: List[Field] = PydanticField(default=[], description="List of fields in the event")

class Contract(BaseModel):
    name: str
    abstract: bool
    fields_immutable: List[Field] = []
    fields_mutable: List[Field] = []
    parent_contracts: List[str] = []
    parent_interfaces: List[str] = []
    maps: Dict[str, MapDef] = {}
    events: List[RalphEvent] = []
    consts: List[Constant] = []
    enums: List[RalphEnum] = []
    methods: str = "" # Body of methods (Ralph code)

class Interface(BaseModel):
    name: str
    parents: List[str] = []
    events: List[RalphEvent] = []
    public_methods: str = "" # Definitions of public methods

class Struct(BaseModel):
    name: str
    fields: List[Field]

class RalphSource(BaseModel):
    global_structs: List[Struct] = []
    global_enums: List[RalphEnum] = []
    global_consts: List[Constant] = []
    interfaces: Dict[str, Interface] = {}
    contracts: Dict[str, Contract] = {}

    def render(self) -> str:
        """Renders the entire Ralph source code from the AST."""
        lines = []
        TWO_EMPTY_LINES = ["", ""]

        # 1. Global constants
        if self.global_consts:
            for g_const in self.global_consts:
                lines.append(f"const {g_const.name}: {g_const.type} = {g_const.value}") 
            lines.extend(TWO_EMPTY_LINES)

        # 2. Global Enums
        for g_enum in self.global_enums:
            lines.append(f"enum {g_enum.name} {{")
            for enum_val in g_enum.values:
                lines.append(f"    {enum_val.name} = {enum_val.value}")
            lines.append("}")
            lines.extend(TWO_EMPTY_LINES)

        # 3. Global Structs
        for g_struct in self.global_structs:
            lines.append(f"struct {g_struct.name} {{")
            for struct_field in g_struct.fields:
                lines.append(f"    {struct_field.name}: {struct_field.type},") 
            lines.append("}")
            lines.extend(TWO_EMPTY_LINES)

        # 4. Interfaces
        for iname, iface in self.interfaces.items():
            parents = ""
            if iface.parents:
                parents = f" extends {', '.join(iface.parents)}"
            lines.append(f"Interface {iname}{parents} {{")
            
            if iface.events:
                for iface_event in iface.events:
                    fields = ", ".join([f"{f.name}: {f.type}" for f in iface_event.fields])
                    lines.append(f"    event {iface_event.name}({fields})")
                lines.extend(TWO_EMPTY_LINES)
            
            if iface.public_methods:
                lines.append(f"    {iface.public_methods.strip()}")
            lines.append("}")
            lines.extend(TWO_EMPTY_LINES)

        # 5. Contracts
        for cname, contr in self.contracts.items():
            abstract = "Abstract " if contr.abstract else ""
            
            # Inheritance Logic: Resolve parent contract arguments and infer missing fields
            parent_calls = []
            additional_params = []
            existing_field_names = set(f.name for f in contr.fields_immutable) | set(f.name for f in contr.fields_mutable)

            for parent_name in contr.parent_contracts:
                if parent_name in self.contracts:
                    parent = self.contracts[parent_name]
                    p_args = []
                    
                    # Process parent fields to build args and infer missing ones on child
                    for pf in parent.fields_immutable:
                        p_args.append(pf.name)
                        if pf.name not in existing_field_names:
                            additional_params.append(f"{pf.name}: {pf.type}  // required by {parent_name}")
                            existing_field_names.add(pf.name)
                    
                    for pf in parent.fields_mutable:
                        p_args.append(pf.name)
                        if pf.name not in existing_field_names:
                            additional_params.append(f"mut {pf.name}: {pf.type}  // required by {parent_name}")
                            existing_field_names.add(pf.name)
                            
                    parent_calls.append(f"{parent_name}({', '.join(p_args)})")
                else:
                    # Parent is likely a built-in or interface, or not found in AST
                    parent_calls.append(parent_name)
            
            parents_str = ""
            if parent_calls:
                parents_str = f" extends {', '.join(parent_calls)}"

            implements_str = ""
            if contr.parent_interfaces:
                implements_str = f" implements {', '.join(contr.parent_interfaces)}"
            
            params = []
            for f in contr.fields_immutable:
                params.append(f"{f.name}: {f.type}")
            for f in contr.fields_mutable:
                params.append(f"mut {f.name}: {f.type}")
            
            # Add the inferred fields
            params.extend(additional_params)
            
            if len(params) == 0:
                params_str = ""
            else:
                params_str = "\n  " + ",\n  ".join(params) + "\n"
            
            lines.append(f"{abstract}Contract {cname}({params_str}){parents_str}{implements_str} {{")
            
            # Inner constructs
            if contr.events:
                for c_event in contr.events:
                    fields = ", ".join([f"{f.name}: {f.type}" for f in c_event.fields])
                    lines.append(f"  event {c_event.name}({fields})")
                lines.append("")

            if contr.consts:
                for c_const in contr.consts:
                     lines.append(f"  const {c_const.name} = {c_const.value}")
                lines.append("")

            for c_enum in contr.enums:
                lines.append(f"  enum {c_enum.name} {{")
                for v in c_enum.values:
                    lines.append(f"    {v.name} = {v.value}")
                lines.append("  }")
                lines.append("")

            # Maps
            if contr.maps:
                for map_name, map_def in contr.maps.items():
                    lines.append(f"  mapping[{map_def.key_type}, {map_def.value_type}] {map_name}")
                lines.append("")
            
            if contr.methods:
                # Indent methods
                method_lines = contr.methods.strip().split('\n')
                for ml in method_lines:
                    lines.append(f"  {ml}")

            lines.append("}")
            lines.extend(TWO_EMPTY_LINES)

        return "\n".join(lines)


# --- Session Storage ---

_sessions: Dict[str, RalphSource] = {}

def get_session_source() -> RalphSource:
    if not _current_session_id:
        raise ValueError("No active session ID")
    if _current_session_id not in _sessions:
        _sessions[_current_session_id] = RalphSource()
    return _sessions[_current_session_id]

def _safe_parse_fields(fields: Any) -> List[Field]:
    """Helper to safely parse fields that might be malformed by the LLM."""
    if not isinstance(fields, list):
        return []
    
    parsed = []
    for f in fields:
        if isinstance(f, dict):
            try:
                parsed.append(Field(**f))
            except Exception:
                continue
        elif isinstance(f, str):
            # Attempt to parse "name: type" string
            if ":" in f:
                parts = f.split(":", 1)
                parsed.append(Field(name=parts[0].strip(), type=parts[1].strip()))
    return parsed


# --- Helper for human readable logs ---

# We can rely on StreamEvent.tool_start to show the action, 
# provided the tool name and input is descriptive enough. 
# But the requirement says "display... in short form ex. 'Creating contract MyContract'".
# We will ensure our tools return descriptive strings or the UI handles it.
# The `agent_service.py` typically emits `tool_start` with `tool` and `input`.

# --- Tools Definitions ---

@tool
def createContract(name: str, abstract: bool, parentInterfaces: List[str], parentContracts: List[str], fieldsImmutable: List[Field], fieldsMutable: List[Field]) -> str:
    """
    Creates a new Contract definition in the Ralph source.
    Naming convention:
        - Contract name MUST start with an uppercase letter.
        - Field names MUST start with a lowercase letter.
    Args:
        name: Name of the contract.
        abstract: Whether it is abstract.
        parentInterfaces: List of parent interfaces.
        parentContracts: List of parent contracts to extend.
        fieldsImmutable: List of immutable fields (constants that are set on contract creation).
        fieldsMutable: List of mutable fields (mutable state vars).
    """
    source = get_session_source()
    if name in source.contracts:
        return f"Error: Contract {name} already exists."
    
    if not name[0].isupper():
        return f"Error: Contract name '{name}' must start with an uppercase letter."
    
    for f in fieldsImmutable:
        if not f.name[0].islower():
            return f"Error: Immutable field '{f.name}' must start with a lowercase letter."
    for f in fieldsMutable:
        if not f.name[0].islower():
            return f"Error: Mutable field '{f.name}' must start with a lowercase letter."

    contract = Contract(
        name=name,
        abstract=abstract,
        parent_contracts=parentContracts,
        parent_interfaces=parentInterfaces,
        fields_immutable=fieldsImmutable,
        fields_mutable=fieldsMutable
    )
    source.contracts[name] = contract
    return f"Created contract {name}"

@tool
def createInterface(name: str, parents: List[str]) -> str:
    """Creates a new Interface definition."""
    source = get_session_source()
    if name in source.interfaces:
        return f"Error: Interface {name} already exists."
    source.interfaces[name] = Interface(name=name, parents=parents)
    return f"Created interface {name}"

@tool
def createGlobalStruct(struct: Struct) -> str:
    """Creates a global struct. Field names must start with a lowercase letter."""
    source = get_session_source()
    if not struct.name[0].isupper():
        return f"Error: Struct name '{struct.name}' must start with an uppercase letter."
    for f in struct.fields:
        if not f.name[0].islower():
            return f"Error: Struct field '{f.name}' must start with a lowercase letter."
    source.global_structs.append(struct)
    return f"Created global struct {struct.name}"

@tool
def createGlobalEnum(enum: RalphEnum) -> str:
    """Creates a global enum. Enum names and enum values must start with an uppercase letter."""
    source = get_session_source()
    if not enum.name[0].isupper():
        return f"Error: Enum name '{enum.name}' must start with an uppercase letter."
    for v in enum.values:
        if not v.name[0].isupper():
             return f"Error: Enum value '{v.name}' must start with an uppercase letter."
    source.global_enums.append(enum)
    return f"Created global enum {enum.name}"

@tool
def createGlobalConstant(constant: Constant) -> str:
    """
    Creates a global constant. 
    It is recommended to use SCREAMING_SNAKE_CASE for constant names.
    The name MUST start with an uppercase letter.
    """
    source = get_session_source()
    if not constant.name[0].isupper():
        return f"Error: Constant '{constant.name}' must start with an uppercase letter."
    source.global_consts.append(constant)
    return f"Created global constant {constant.name}"

# Interface Scope Tools

@tool
def replaceFunctionDeclarations(interfaceName: str, functionDeclarations: str) -> str:
    """Replaces the body of an interface with provided function declarations."""
    source = get_session_source()
    if interfaceName not in source.interfaces:
        return f"Error: Interface {interfaceName} not found."
    source.interfaces[interfaceName].public_methods = functionDeclarations
    return f"Updated function declarations for interface {interfaceName}"

@tool
def addEventsToInterface(interfaceName: str, events: List[EventDef]) -> str:
    """Adds events to an interface. Event field names must start with a lowercase letter."""
    source = get_session_source()
    if interfaceName not in source.interfaces:
        return f"Error: Interface {interfaceName} not found."
    
    for e in events:
        for f in e.fields:
            if not f.name[0].islower():
                return f"Error: Event field '{f.name}' in event '{e.name}' must start with a lowercase letter."
    
    parsed_events = [RalphEvent(name=e.name, fields=e.fields) for e in events]
    source.interfaces[interfaceName].events.extend(parsed_events)
    return f"Added {len(parsed_events)} events to interface {interfaceName}"

# Contract Scope Tools

@tool
def replaceFunctionDefinitions(contractName: str, functionDefinitions: str) -> str:
    """
    Replaces the body of a contract with provided function definitions.
    Use this to add the Logic/Methods to the contract.
    """
    source = get_session_source()
    if contractName not in source.contracts:
        return f"Error: Contract {contractName} not found."
    source.contracts[contractName].methods = functionDefinitions
    return f"Updated function definitions for contract {contractName}"

@tool
def addMutableFieldsToContract(contractName: str, fields: List[Field]) -> str:
    """Adds mutable fields to a contract. Field names must start with a lowercase letter."""
    source = get_session_source()
    if contractName not in source.contracts:
        return f"Error: Contract {contractName} not found."
    for f in fields:
        if not f.name[0].islower():
            return f"Error: Mutable field '{f.name}' must start with a lowercase letter."
    source.contracts[contractName].fields_mutable.extend(fields)
    return f"Added {len(fields)} mutable fields to {contractName}"

@tool
def addImmutableFieldsToContract(contractName: str, fields: List[Field]) -> str:
    """Adds immutable fields (constructor params) to a contract. Field names must start with a lowercase letter."""
    source = get_session_source()
    if contractName not in source.contracts:
        return f"Error: Contract {contractName} not found."
    for f in fields:
        if not f.name[0].islower():
            return f"Error: Immutable field '{f.name}' must start with a lowercase letter."
    source.contracts[contractName].fields_immutable.extend(fields)
    return f"Added {len(fields)} immutable fields to {contractName}"

@tool
def removeImmutableFieldFromContract(contractName: str, fieldName: str) -> str:
    """Removes an immutable field from a contract."""
    source = get_session_source()
    if contractName not in source.contracts:
        return f"Error: Contract {contractName} not found."
    source.contracts[contractName].fields_immutable = [f for f in source.contracts[contractName].fields_immutable if f.name != fieldName]
    return f"Removed immutable field {fieldName} from {contractName}"

@tool
def removeMutableFieldFromContract(contractName: str, fieldName: str) -> str:
    """Removes a mutable field from a contract."""
    source = get_session_source()
    if contractName not in source.contracts:
        return f"Error: Contract {contractName} not found."
    source.contracts[contractName].fields_mutable = [f for f in source.contracts[contractName].fields_mutable if f.name != fieldName]
    return f"Removed mutable field {fieldName} from {contractName}"

@tool
def addMapsToContract(contractName: str, maps: List[Dict[str, Any]]) -> str:
    """Adds maps to a contract. Input list of {name, key_type, value_type}."""
    source = get_session_source()
    if contractName not in source.contracts:
        return f"Error: Contract {contractName} not found."
    for m in maps:
        if not isinstance(m, dict):
            continue
        # Assuming format {name: 'foo', key_type: 'Address', value_type: 'U256'}
        # But MapDef expects key_type, value_type
        # We need to parse correctly.
        # The schema in requirements: Map: {key_type: "Bool" | "U256" | "I256" | "Address" | "ByteVec", value_type: string }
        # And Contract has "maps: Map[]" which implies name is somewhere.
        # Reworked.md says: `addMapsToContract(contractName: string, maps: Map[]): void`
        # But `Contract` struct in reworked.md says `maps: Map[]`. 
        # Map definition in reworked.md: `{key_type: ..., value_type: ...}`. It misses the NAME.
        # I will assume the input dictionary has a 'name' field for the map variable name.
        m_name = m.get('name')
        if not m_name:
            continue
        key_type = m.get('key_type')
        value_type = m.get('value_type')
        if not key_type or not value_type:
            continue
        source.contracts[contractName].maps[m_name] = MapDef(key_type=key_type, value_type=value_type)
    return f"Added {len(maps)} maps to {contractName}"

@tool
def addEventsToContract(contractName: str, events: List[EventDef]) -> str:
    """Adds events to a contract. Event field names must start with a lowercase letter."""
    source = get_session_source()
    if contractName not in source.contracts:
        return f"Error: Contract {contractName} not found."
    
    for e in events:
        for f in e.fields:
            if not f.name[0].islower():
                return f"Error: Event field '{f.name}' in event '{e.name}' must start with a lowercase letter."
    
    parsed_events = []
    for e in events:
        # e is now a Pydantic object, not a dict
        parsed_events.append(RalphEvent(name=e.name, fields=e.fields))
    
    source.contracts[contractName].events.extend(parsed_events)
    return f"Added {len(parsed_events)} events to {contractName}"

@tool
def addConstantsToContract(contractName: str, constants: List[Constant]) -> str:
    """
    Adds constants to a contract.
    It is recommended to use SCREAMING_SNAKE_CASE for constant names.
    The name MUST start with an uppercase letter.
    """
    source = get_session_source()
    if contractName not in source.contracts:
        return f"Error: Contract {contractName} not found."
    for c in constants:
        if not c.name[0].isupper():
            return f"Error: Constant '{c.name}' must start with an uppercase letter."
    source.contracts[contractName].consts.extend(constants)
    return f"Added {len(constants)} constants to {contractName}"

@tool
def addEnumsToContract(contractName: str, enums: List[RalphEnum]) -> str:
    """Adds enums to a contract. Enum names and enum values must start with an uppercase letter."""
    source = get_session_source()
    if contractName not in source.contracts:
        return f"Error: Contract {contractName} not found."
    
    for e in enums:
        if not e.name[0].isupper():
            return f"Error: Enum name '{e.name}' must start with an uppercase letter."
        for v in e.values:
            if not v.name[0].isupper():
                return f"Error: Enum value '{v.name}' in enum '{e.name}' must start with an uppercase letter."
    
    source.contracts[contractName].enums.extend(enums)
    return f"Added {len(enums)} enums to {contractName}"

@tool
def lookupTranslation(solidityClassNameOrInterface: str) -> str:
    """Looks up a translation for a known Solidity class or interface (like IERC20)."""
    # Simple dictionary lookup for now.
    predefined = {
        "IERC20": "Interface IERC20 { ... }", # Placeholder
        "ERC20": "Contract ERC20(...) { ... }", # Placeholder
    }
    return predefined.get(solidityClassNameOrInterface, "Translation not found.")

@tool
def finalizeandRenderTranslation() -> str:
    """
    Finalizes the translation creation process and returns the full Ralph source code.
    Call this when you have finished reconstructing the contract.
    """
    source = get_session_source()
    return source.render()

# --- Stream Event & Agent ---

AgentStage = Literal[
    "thinking", "using_tool", "reading_code", "preprocessing",
    "translating", "generating", "fetching_docs", "completing", "done", "analysing", "fixing"
]

class StreamEvent:
    @staticmethod
    def content(chunk: str) -> Dict[str, Any]:
        return {"type": "content", "data": chunk}
    
    @staticmethod
    def translation_chunk(chunk: str) -> Dict[str, Any]:
        return {"type": "translation_chunk", "data": chunk}

    @staticmethod
    def stage(stage: AgentStage, message: str = "") -> Dict[str, Any]:
        return {"type": "stage", "data": {"stage": stage, "message": message}}

    @staticmethod
    def tool_start(tool_name: str, tool_input: str) -> Dict[str, Any]:
        return {"type": "tool_start", "data": {"tool": tool_name, "input": tool_input}}

    @staticmethod
    def tool_end(tool_name: str, success: bool = True) -> Dict[str, Any]:
        return {"type": "tool_end", "data": {"tool": tool_name, "success": success}}

    @staticmethod
    def code_snapshot(code: str) -> Dict[str, Any]:
        return {"type": "code_snapshot", "data": code}

    @staticmethod
    def error(error_message: str) -> Dict[str, Any]:
        return {"type": "error", "data": {"message": error_message}}

class ChatAgent:
    def __init__(self):
        # Tools list
        self.tools = [
            createContract, createInterface, createGlobalStruct, createGlobalEnum, createGlobalConstant,
            replaceFunctionDeclarations, addEventsToInterface,
            replaceFunctionDefinitions, addMutableFieldsToContract, addImmutableFieldsToContract,
            removeImmutableFieldFromContract, removeMutableFieldFromContract,
            addMapsToContract, addEventsToContract, addConstantsToContract, addEnumsToContract,
            lookupTranslation, finalizeandRenderTranslation
        ]

        # LLM
        self.llm = ChatOpenAI(
            model=AGENT_MODEL,
            temperature=0.1,
            api_key=API_KEY,
            base_url=API_URL,
        )
        
        self.fix_llm = ChatOpenAI(
            model=LLM_MODEL,
            temperature=0.3, # Higher temp for creativity in fixing
            api_key=API_KEY,
            base_url=API_URL,
        )

        # Prompt
        system_prompt = (
            "You are HenryBot, an expert AI assistant for Alephium blockchain development and Ralph smart contract programming.\n\n"
            f"{TRANSLATION_SYSTEM_PROMPT}\n\n"
            "AGENCY INSTRUCTIONS:\n"
            "You are now acting as a State-Action Agent using a set of granular tools to build a Ralph contract structure from scratch.\n"
            "Instead of outputting code directly, you MUST use the provided tools to build the 'RalphSource' AST.\n"
            "1. Analyze the input Solidity code.\n"
            "2. Identify all Contracts, Interfaces, Structs, Enums, and Constants.\n"
            "3. Use `createContract`, `createInterface`, etc. to assert their existence.\n"
            "4. Use `addMutableFieldsToContract`, `addImmutableFieldsToContract`, `addMapsToContract`, etc. to populate them.\n"
            "5. Translate logic and methods, then use `replaceFunctionDefinitions` or `replaceFunctionDeclarations` to inject them.\n"
            "6. FINALLY, call `finalizeandRenderTranslation` to get the result string and return it to the user.\n"
            "\n"
            "You must orchestrate this process step-by-step. Do not hallucinate tools."
        )

        self.agent = create_agent(self.llm, self.tools, system_prompt=system_prompt)
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.session_options: Dict[str, Dict[str, Any]] = {}

    def set_session_options(self, session_id: str, options: Dict[str, Any]) -> None:
        self.session_options[session_id] = options

    def get_session_options(self, session_id: str) -> Dict[str, Any]:
        return self.session_options.get(session_id, {
            "optimize": False,
            "include_comments": True,
            "mimic_defaults": False,
            "smart": False,
            "translate_erc20": False,
        })
    
    def clear_session(self, session_id: str) -> None:
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.session_options:
            del self.session_options[session_id]
        if session_id in _sessions:
            del _sessions[session_id]

    async def chat(
        self,
        message: str,
        session_id: str = "default",
        stream: bool = True,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        # State Management
        set_current_session_id(session_id)
        if options:
            self.set_session_options(session_id, options)
        session_opts = self.get_session_options(session_id)
        set_session_options_context(session_opts)
        
        # Translation queue for real-time code chunks if needed (used by tools if they emit chunks)
        translation_chunk_queue: asyncio.Queue = asyncio.Queue()
        set_translation_queue(translation_chunk_queue)

        try:
            yield StreamEvent.stage("thinking", "Analyzing...")

            if session_id not in self.sessions:
                self.sessions[session_id] = []
            
            chat_history = self.sessions[session_id]

            # Yield events for the frontend
            yield StreamEvent.stage("generating", "Building Ralph Source...")
            
            final_output = ""
            
            # We process the stream from the compiled graph
            async for event in self.agent.astream_events(
                {"messages": chat_history + [{"role": "user", "content": message}]},
                version="v1"
            ):
                kind = event["event"]
                
                if kind == "on_tool_start":
                    name = event.get('name', 'unknown_tool')
                    inputs = event['data'].get('input')
                    # format input for display if it's a dict
                    input_str = str(inputs)
                    yield StreamEvent.tool_start(name, input_str)
                
                elif kind == "on_tool_end":
                    name = event.get('name', 'unknown_tool')
                    yield StreamEvent.tool_end(name, success=True)
                    # Render and yield code snapshot after each tool
                    try:
                        source = get_session_source()
                        code_snapshot = source.render()
                        yield StreamEvent.code_snapshot(code_snapshot)
                    except Exception as render_err:
                        logger.warning(f"Failed to render code snapshot: {render_err}")
                
                elif kind == "on_chain_end":
                    # In LangGraph, we look for the final message from the model
                    # But simpler to look for "on_chat_model_stream" or "on_chat_model_end" for content
                    pass
                
                elif kind == "on_chat_model_stream":
                    # We can stream tokens if we want, but for tool usage we often want the final result
                    # But the requirement asks for tool events mostly.
                    # If there is content output (non-tool), we can capture it.
                    chunk = event['data'].get('chunk')
                    if chunk and hasattr(chunk, 'content') and chunk.content:
                         final_output += chunk.content
                         # If we want to stream text content to user:
                         # yield StreamEvent.content(chunk.content))

            yield StreamEvent.stage("done")
            
        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            yield StreamEvent.error(str(e))
        finally:
            set_current_session_id(None)
            set_session_options_context(None)
            set_translation_queue(None)

    async def fix_code(
        self,
        ralph_code: str,
        error: str,
        solidity_code: Optional[str] = None,
        max_iterations: int = 3,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Fix Ralph code based on a compilation error.
        Iterates up to max_iterations times.
        """
        current_code = ralph_code
        current_error = error
        iterations = 0
        
        yield StreamEvent.stage("analysing", "🔍 Analysing the error...")
        
        solidity_context = ""
        if solidity_code:
            solidity_context = f"## Original Solidity Code\\n```solidity\\n{solidity_code}\\n```\\n"
        
        fix_system_prompt = f"""You are an expert Ralph smart contract developer.
Your task is to fix Ralph code that has compilation errors.

## Ralph Language Reference
{RALPH_DETAILS}
{solidity_context}
## CRITICAL RULES - VIOLATION WILL CAUSE FAILURE:
1. Analyze the error message and fix ONLY the specific syntax/compilation error mentioned
2. You MUST keep ALL existing code - every function, every field, every event, every line
3. NEVER delete or simplify code - only modify the specific broken syntax
4. NEVER return a shorter or simpler version of the contract
5. Return ONLY the complete fixed Ralph code with ALL original functionality preserved
6. Do NOT include any explanation, markdown, or comments about what you changed
7. Do NOT wrap the code in ```ralph``` blocks
"""

        for iteration in range(max_iterations):
            iterations += 1
            logger.info(f"Fix iteration {iterations}/{max_iterations}")
            yield StreamEvent.stage("fixing", f"🔧 Fixing the code (iteration {iterations}/{max_iterations})...")
            
            fix_prompt = f"""Fix this Ralph code compilation error.

ERROR MESSAGE TO FIX:
{current_error}

COMPLETE RALPH CODE (you must return ALL of it with only the error fixed):
{current_code}
"""

            try:
                response = await self.fix_llm.ainvoke([
                    {"role": "system", "content": fix_system_prompt},
                    {"role": "user", "content": fix_prompt}
                ])
                
                fixed_code = response.content.strip()
                fixed_code = self._extract_ralph_code(fixed_code)
                
                if not fixed_code:
                    logger.warning(f"Empty fix result on iteration {iterations}")
                    continue
                
                current_code = fixed_code
                
                # Check compilation
                compile_result = await self._compile_ralph_code(fixed_code)
                
                if compile_result["success"]:
                    logger.info(f"Fix successful after {iterations} iteration(s)")
                    yield StreamEvent.stage("done", "✅ Fix complete!")
                    yield {
                        "type": "result",
                        "data": {
                            "fixed_code": fixed_code,
                            "iterations": iterations,
                            "success": True
                        }
                    }
                    return
                else:
                    current_error = compile_result.get("error", "Unknown compilation error")
                    logger.info(f"Compilation still failing: {current_error[:100]}...")
                    
            except Exception as e:
                logger.error(f"Fix iteration {iterations} failed: {e}", exc_info=True)
                continue
        
        yield StreamEvent.stage("done", "⚠️ Fix complete (with remaining errors)")
        yield {
            "type": "result",
            "data": {
                "fixed_code": current_code,
                "iterations": iterations,
                "success": False
            }
        }

    def _extract_ralph_code(self, text: str) -> str:
        ralph_match = re.search(r'```ralph\\s*\\n([\\s\\S]*?)```', text)
        if ralph_match:
            return ralph_match.group(1).strip()
        code_match = re.search(r'```\\s*\\n?([\\s\\S]*?)```', text)
        if code_match:
            return code_match.group(1).strip()
        return text.strip()

    async def _compile_ralph_code(self, code: str) -> Dict[str, Any]:
        node_url = os.getenv("NODE_URL", "https://node.testnet.alephium.org")
        compile_endpoint = f"{node_url}/contracts/compile-project"
        
        compile_request = {
            "code": code,
            "compilerOptions": {
                "ignoreUnusedConstantsWarnings": True,
                "ignoreUnusedVariablesWarnings": True,
                "ignoreUnusedFieldsWarnings": True,
                "ignoreUnusedPrivateFunctionsWarnings": True,
                "ignoreUnusedFunctionReturnWarnings": True,
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(compile_endpoint, json=compile_request) as resp:
                    if resp.status == 200:
                        return {"success": True}
                    else:
                        error_text = await resp.text()
                        return {"success": False, "error": error_text}
        except Exception as e:
            logger.error(f"Compilation check failed: {e}")
            return {"success": False, "error": str(e)}

# Global Instance
_agent: Optional[ChatAgent] = None

def get_agent() -> ChatAgent:
    global _agent
    if _agent is None:
        _agent = ChatAgent()
    return _agent
