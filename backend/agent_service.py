"""
LangChain v1 Agent Service for HenryBot AI Assistant.
Handles chat interactions with streaming and tool usage.
Using Reworked Agentic System V2 with granular state manipulation tools.
"""
import aiohttp
import asyncio
import contextvars
import logging
import os
import re
from typing import Any, AsyncGenerator, Callable, Dict, List, Literal, Optional

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field as PydanticField

from translation_context import RALPH_DETAILS
from translation_service import SYSTEM_PROMPT as TRANSLATION_SYSTEM_PROMPT, perform_fim_translation
from translate_oz import PRETRANSLATED_LIBS, get_pretranslated_code
from code_doctor import fix_common_errors

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

_session_options_var: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar("session_options", default=None)
_translation_queue_var: contextvars.ContextVar[Optional[asyncio.Queue]] = contextvars.ContextVar("translation_queue", default=None)
_session_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("session_id", default=None)
_solidity_source_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("solidity_source", default=None)

def get_current_session_options() -> Dict[str, Any]:
    return _session_options_var.get() or {
        "optimize": False,
        "include_comments": True,
        "mimic_defaults": False,
        "smart": False,
        "translate_erc20": False,
    }

def set_session_options_context(options: Optional[Dict[str, Any]]) -> None:
    _session_options_var.set(options)

def get_translation_queue() -> Optional[asyncio.Queue]:
    return _translation_queue_var.get()

def set_translation_queue(q: Optional[asyncio.Queue]) -> None:
    _translation_queue_var.set(q)

def set_current_session_id(session_id: Optional[str]) -> None:
    _session_id_var.set(session_id)

def get_current_solidity_source() -> Optional[str]:
    return _solidity_source_var.get()

def set_current_solidity_source(source: Optional[str]) -> None:
    _solidity_source_var.set(source)

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
    hidden: bool = False  # Used to skip rendering builtin/pretranslated code in the final output
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
    hidden: bool = False  # Used to skip rendering builtin/pretranslated code in the final output
    parents: List[str] = []
    events: List[RalphEvent] = []
    public_methods: str = "" # Definitions of public methods

class Struct(BaseModel):
    name: str
    fields: List[Field]

class RalphSource(BaseModel):
    preTranslated: str = ""
    global_structs: List[Struct] = []
    global_enums: List[RalphEnum] = []
    global_consts: List[Constant] = []
    interfaces: Dict[str, Interface] = {}
    contracts: Dict[str, Contract] = {}

    def render(self, tag_body: None | str = None) -> str:
        """Renders the entire Ralph source code from the AST. Tag body allows tagging body of a specific contract or interface to assist in translation efforts with <|fim_start|> <|fim_end|>."""
        lines = []
        TWO_EMPTY_LINES = ["", ""]

        # 0. Pre-translated libraries
        if self.preTranslated:
            lines.append(self.preTranslated)
            lines.extend(TWO_EMPTY_LINES)

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
                lines.append(f"  mut {struct_field.name}: {struct_field.type},") 
            lines.append("}")
            lines.extend(TWO_EMPTY_LINES)

        # 4. Interfaces
        for iname, iface in self.interfaces.items():
            if iface.hidden:
                continue

            parents = ""
            if iface.parents:
                parents = f" extends {', '.join(iface.parents)}"
            lines.append(f"Interface {iname}{parents} {{")
            
            if iface.events:
                for iface_event in iface.events:
                    fields = ", ".join([f"{f.name}: {f.type}" for f in iface_event.fields])
                    lines.append(f"    event {iface_event.name}({fields})")
                lines.append("")
            
            if iface.public_methods or tag_body == iname:
                if tag_body == iname:
                    lines.append("  <|fim_start|>")
                if iface.public_methods:
                    lines.append(f"  {iface.public_methods.strip()}")
                if tag_body == iname:
                    lines.append("  <|fim_end|>")

            lines.append("}")
            lines.extend(TWO_EMPTY_LINES)

        # 5. Contracts
        for cname, contr in self.contracts.items():
            if contr.hidden:
                continue

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
            # 1. Maps
            if contr.maps:
                for map_name, map_def in contr.maps.items():
                    lines.append(f"  mapping[{map_def.key_type}, {map_def.value_type}] {map_name}")
                lines.append("")

            # 2. Events
            if contr.events:
                for c_event in contr.events:
                    fields = ", ".join([f"{f.name}: {f.type}" for f in c_event.fields])
                    lines.append(f"  event {c_event.name}({fields})")
                lines.append("")

            # 3. Consts
            if contr.consts:
                for c_const in contr.consts:
                     lines.append(f"  const {c_const.name} = {c_const.value}")
                lines.append("")

            # 4. Enums
            for c_enum in contr.enums:
                lines.append(f"  enum {c_enum.name} {{")
                for v in c_enum.values:
                    lines.append(f"    {v.name} = {v.value}")
                lines.append("  }")
                lines.append("")

            # 5. Methods
            if contr.methods or tag_body == cname:
                if tag_body == cname:
                    lines.append("  <|fim_start|>")

                # It's multiline content, but appending it directly may still work as expected.
                lines.append("  " + contr.methods)
                if tag_body == cname:
                    lines.append("  <|fim_end|>")

            lines.append("}")
            lines.extend(TWO_EMPTY_LINES)

        return "\n".join(lines)


# --- Session Storage ---

_sessions: Dict[str, RalphSource] = {}
_session_locks: Dict[str, asyncio.Lock] = {}

def get_session_source() -> RalphSource:
    session_id = _session_id_var.get()
    if not session_id:
        raise ValueError("No active session ID")
    if session_id not in _sessions:
        _sessions[session_id] = RalphSource()
    return _sessions[session_id]

def get_session_lock() -> asyncio.Lock:
    session_id = _session_id_var.get()
    if not session_id:
        raise ValueError("No active session ID")
    if session_id not in _session_locks:
        _session_locks[session_id] = asyncio.Lock()
    return _session_locks[session_id]

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


def _extract_ralph_code(text: str) -> str:
    """
    Extract Ralph code or generic code block from text containing markdown code fences.
    Ensures that trailing/leading whitespace and markdown fences are removed.
    """
    cleaned_content = text.strip()
    if "```" in cleaned_content:
        match = re.search(r"```(?:ralph)?\s*(.*?)\s*```", cleaned_content, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            return "\n".join(
                [l for l in cleaned_content.split("\n") if not l.strip().startswith("```")]
            ).strip()
    return cleaned_content


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
    
    IMPORTANT: When extending a parent contract, you MUST define all fields required by the parent contracts.
    You MUST ensure the mutability (immutable vs mutable) of the field matches the parent contract's definition exactly.
    If a parent has `mut fieldName: T`, the child MUST also declare `fieldName: T` in `fieldsMutable`.
    Failure to match mutability will cause compilation errors.

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
    
    errors = []
    if not name[0].isupper():
        errors.append(f"Contract name '{name}' must start with an uppercase letter.")
    
    for f in fieldsImmutable:
        if not f.name[0].islower():
            errors.append(f"Immutable field '{f.name}' must start with a lowercase letter.")
    for f in fieldsMutable:
        if not f.name[0].islower():
            errors.append(f"Mutable field '{f.name}' must start with a lowercase letter.")
    
    # Validate field types and mutability with reference to parent contracts
    for parent in parentContracts:
        if parent in source.contracts:
            p_contract = source.contracts[parent]
            # Check immutable fields
            for p_field in p_contract.fields_immutable:
                if p_field.name not in [f.name for f in fieldsImmutable]:
                    errors.append(f"Missing immutable field '{p_field.name}' required by parent contract '{parent}'.")
            # Check mutable fields
            for p_field in p_contract.fields_mutable:
                if p_field.name not in [f.name for f in fieldsMutable]:
                    errors.append(f"Missing mutable field '{p_field.name}' required by parent contract '{parent}'.")

    if errors:
        if len(errors) == 1:
            return f"Error when creating contract {name}: {errors[0]}"
        return "Multiple validation errors when creating contract " + name + ":\n- " + "\n- ".join(errors)

    contract = Contract(
        name=name,
        abstract=abstract,
        parent_contracts=parentContracts,
        parent_interfaces=parentInterfaces,
        fields_immutable=fieldsImmutable,
        fields_mutable=fieldsMutable
    )
    source.contracts[name] = contract
    return f"Created contract {name} with immutable fields ({', '.join(f.name for f in fieldsImmutable)}) and mutable fields ({', '.join(f.name for f in fieldsMutable)})"

@tool
def createInterface(name: str, parents: List[str]) -> str:
    """Creates a new Interface definition."""
    source = get_session_source()
    if name in source.interfaces:
        return f"Error: Interface {name} already exists."
    source.interfaces[name] = Interface(name=name, parents=parents)
    return f"Created interface {name} with parents {', '.join(parents)}"

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
    return f"Created global struct {struct.name} with mutable fields ({', '.join(f.name for f in struct.fields)})"

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
async def translateFunctions(interfaceOrContractName: str) -> str:
    """
    Translates the functions/methods for a specific Contract or Interface.
    It uses the original Solidity source code (from the chat session) and the current partial Ralph structure.
    It automatically fills in the code using an advanced FIM (Fill-In-the-Middle) LLM.
    Args:
        interfaceOrContractName: The name of the contract or interface to populate methods for.
    """
    source = get_session_source()
    if interfaceOrContractName not in source.contracts and interfaceOrContractName not in source.interfaces:
        return f"Error: {interfaceOrContractName} not found in contracts or interfaces."

    solidity_code = get_current_solidity_source()
    if not solidity_code:
        return "Error: No Solidity source code found in current session context. Please provide the source code."

    # Use a lock to ensure sequential execution of translation tasks for the same session
    lock = get_session_lock()
    async with lock:
        # Render with FIM tags - re-fetch source inside lock to ensure latest state
        # (Though source object is mutable reference, so self.source is fine, but rendering needs to be atomic w.r.t other updates)
        try:
            ralph_structure = source.render(tag_body=interfaceOrContractName)
        except Exception as e:
            return f"Error rendering Ralph structure: {e}"

        full_content = ""
        queue = get_translation_queue()

        try:
            if queue:
                # Notify UI
                await queue.put({"type": "stage", "data": {"stage": "translating", "message": f"Translating methods for {interfaceOrContractName}..."}})
            
            # Determine if we should use the smart model based on session options
            session_opts = get_current_session_options()
            is_smart = session_opts.get("smart", False)

            async for chunk, reasoning, warnings, errors in perform_fim_translation(solidity_code, ralph_structure, smart=is_smart):
                if chunk:
                    full_content += chunk
                    if queue:
                        await queue.put({"type": "translation_chunk", "data": chunk})
            
        except Exception as e:
            logger.error(f"FIM translation failed: {e}")
            return f"Error during translation: {e}"

        # Clean content and remove markdown fences if present
        cleaned_content = _extract_ralph_code(full_content)
        
        # Get mapping names from the contract to pass to code doctor
        mapping_names = set()
        if interfaceOrContractName in source.contracts:
            mapping_names = set(source.contracts[interfaceOrContractName].maps.keys())
        
        # Apply code doctor with mapping context
        cleaned_content = fix_common_errors(cleaned_content, mappings=mapping_names)

        if interfaceOrContractName in source.contracts:
            source.contracts[interfaceOrContractName].methods = cleaned_content
        elif interfaceOrContractName in source.interfaces:
            source.interfaces[interfaceOrContractName].public_methods = cleaned_content
        
        return f"Successfully translated and updated functions for {interfaceOrContractName}."

def fields_validator(contract: Contract, new_fields: List[Field]) -> tuple[Optional[str], List[Field], List[str]]:
    """
    Validates fields to be added to a contract.
    Returns: (error_message, fields_to_add, ignored_field_names)
    Checks uniqueness across BOTH mutable and immutable fields.
    """
    # Check for uniqueness across ALL existing fields
    all_existing_names = {f.name for f in contract.fields_immutable + contract.fields_mutable}
    
    to_add = []
    ignored = []
    batch_names = set()

    for f in new_fields:
        if not f.name[0].islower():
            return f"Error: Field '{f.name}' must start with a lowercase letter.", [], []
        
        if f.name in all_existing_names or f.name in batch_names:
            ignored.append(f.name)
        else:
            to_add.append(f)
            batch_names.add(f.name)
            
    return None, to_add, ignored

@tool
def addMutableFieldsToContract(contractName: str, fields: List[Field]) -> str:
    """Adds mutable fields to a contract. Field names must start with a lowercase letter."""
    source = get_session_source()
    if contractName not in source.contracts:
        return f"Error: Contract {contractName} not found."
    
    contract = source.contracts[contractName]
    error, added, ignored = fields_validator(contract, fields)
    
    if error:
        return error
        
    contract.fields_mutable.extend(added)
    
    msg = f"Added mutable ({', '.join(f.name for f in added)}) to contract {contractName}"
    if ignored:
        msg += f", ignored ({', '.join(ignored)}) because they already exist"
    return msg

@tool
def addImmutableFieldsToContract(contractName: str, fields: List[Field]) -> str:
    """Adds immutable fields (constructor params) to a contract. Field names must start with a lowercase letter."""
    source = get_session_source()
    if contractName not in source.contracts:
        return f"Error: Contract {contractName} not found."
    
    contract = source.contracts[contractName]
    error, added, ignored = fields_validator(contract, fields)
    
    if error:
        return error
    
    contract.fields_immutable.extend(added)
    
    msg = f"Added immutable ({', '.join(f.name for f in added)}) to contract {contractName}"
    if ignored:
        msg += f", ignored ({', '.join(ignored)}) because they already exist"
    return msg

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
    """
    Adds maps (mappings) to a contract. Map names must start with a lowercase letter.
    
    Args:
        contractName: Name of the contract to add maps to.
        maps: List of map definitions, each with {name, key_type, value_type}.
              key_type must be one of: Bool, U256, I256, Address, ByteVec.
              value_type can be any Ralph type.
    """
    source = get_session_source()
    if contractName not in source.contracts:
        return f"Error: Contract {contractName} not found."
    
    added_maps = []
    for m in maps:
        if not isinstance(m, dict):
            continue
        m_name = m.get('name')
        if not m_name:
            continue
        
        # Validate map name starts with lowercase
        if not m_name[0].islower():
            return f"Error: Map name '{m_name}' must start with a lowercase letter."
        
        key_type = m.get('key_type')
        value_type = m.get('value_type')
        if not key_type or not value_type:
            continue
        
        # Validate value_type is not a mapping (nested mappings not allowed in Ralph)
        if 'mapping' in value_type.lower():
            return f"Error: Nested mappings are not allowed in Ralph. Map '{m_name}' has a mapping as value_type."
        source.contracts[contractName].maps[m_name] = MapDef(key_type=key_type, value_type=value_type)
        added_maps.append(m_name)
    
    return f"Added maps ({', '.join(added_maps)}) to {contractName}"

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
def loadPreTranslatedLibrary(libraryName: str) -> str:
    """
    Loads a pre-translated library (like OpenZeppelin contracts) into the Ralph source.
    Use this when you encounter an import that matches one of the available pre-translated libraries.
    Args:
        libraryName: just the name of the contract or interface to import ex. "IERC20", "ERC20".
    """
    source = get_session_source()
    
    # Check for duplicates in already loaded hidden contracts and interfaces
    hidden_contracts = [name for name, c in source.contracts.items() if c.hidden]
    hidden_interfaces = [name for name, i in source.interfaces.items() if i.hidden]
    
    if libraryName in hidden_contracts or libraryName in hidden_interfaces:
        return f"Warning: PreTranslated Library {libraryName} is already loaded in the scope."
    
    # Auto-import corresponding interface for ERC20/ERC721
    interface_mapping = {"ERC20": "IERC20", "ERC721": "IERC721"}
    also_loaded_interface = None
    if libraryName in interface_mapping:
        interface_name = interface_mapping[libraryName]
        if interface_name not in hidden_interfaces:
            interface_result = get_pretranslated_code(interface_name)
            if interface_result:
                interface_content, interface_specs = interface_result
                source.preTranslated += "\n\n" + interface_content
                also_loaded_interface = interface_name
                if interface_specs:
                    for spec in interface_specs:
                        name = spec.get("name")
                        type_ = spec.get("type")
                        if type_ == "interface":
                            parents = spec.get("parent_contracts", []) + spec.get("parent_interfaces", [])
                            source.interfaces[name] = Interface(
                                name=name,
                                hidden=True,
                                parents=parents
                            )
    
    # Try direct match
    result = get_pretranslated_code(libraryName)

    if result:
        content, specs = result
        source.preTranslated += "\n\n" + content
        
        if specs:
            for spec in specs:
                name = spec.get("name")
                type_ = spec.get("type")
                
                if type_ == "interface":
                    # For interfaces, combine parents
                    parents = spec.get("parent_contracts", []) + spec.get("parent_interfaces", [])
                    source.interfaces[name] = Interface(
                        name=name,
                        hidden=True,
                        parents=parents
                    )
                else:
                    # For contracts
                    source.contracts[name] = Contract(
                        name=name,
                        abstract=spec.get("abstract", False),
                        hidden=True,
                        fields_immutable=[Field(**f) for f in spec.get("fields_immutable", [])],
                        fields_mutable=[Field(**f) for f in spec.get("fields_mutable", [])],
                        parent_contracts=spec.get("parent_contracts", []),
                        parent_interfaces=spec.get("parent_interfaces", [])
                    )

        loaded_msg = f"Loaded PreTranslated library {libraryName}"
        if also_loaded_interface:
            loaded_msg += f" (also auto-loaded {also_loaded_interface})"
        loaded_msg += f" and added to source scope. Content:\n{content}"
        return loaded_msg
    
    return f"Error: PreTranslated library {libraryName} not found."

@tool
def finalizeAndRenderTranslation() -> str:
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
    def tool_start(tool_name: str, tool_input: str, run_id: Optional[str] = None) -> Dict[str, Any]:
        return {"type": "tool_start", "data": {"tool": tool_name, "input": tool_input, "run_id": run_id}}

    @staticmethod
    def tool_end(tool_name: str, success: bool = True, run_id: Optional[str] = None) -> Dict[str, Any]:
        return {"type": "tool_end", "data": {"tool": tool_name, "success": success, "run_id": run_id}}

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
            addEventsToInterface,
            translateFunctions, addMutableFieldsToContract, addImmutableFieldsToContract,
            removeImmutableFieldFromContract, removeMutableFieldFromContract,
            addMapsToContract, addEventsToContract, addConstantsToContract, addEnumsToContract,
            finalizeAndRenderTranslation, loadPreTranslatedLibrary
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

        # Pre-process available libraries for the prompt
        available_libs = list(PRETRANSLATED_LIBS.keys())
        formatted_libs = "\n".join([f"- {lib}" for lib in available_libs])

        # Prompt
        system_prompt = (
            "You are HenryCoder, an expert AI assistant for Alephium blockchain development and Ralph smart contract programming.\n\n"
            f"{TRANSLATION_SYSTEM_PROMPT}\n\n"
            "AGENCY INSTRUCTIONS:\n"
            "You are now acting as a State-Action Agent using a set of granular tools to build a Ralph contract structure from scratch.\n"
            "Instead of outputting code directly, you MUST use the provided tools to build the 'RalphSource' AST.\n"
            "1. Analyze the input Solidity code.\n"
            "2. CHECK imports against the Available Pre-Translated Libraries list below. If found, use `loadPreTranslatedLibrary` immediately.\n"
            "3. Identify all Contracts, Interfaces, Structs, Enums, and Constants.\n"
            "4. Use `createContract`, `createInterface`, etc. to assert their existence, unless they are already loaded from a pre-translated library. Make sure to include parent contracts and interfaces.\n"
            "5. Use `addMutableFieldsToContract`, `addImmutableFieldsToContract`, `addMapsToContract`, etc. to populate them.\n"
            "6. Translate logic and methods by calling `translateFunctions` for each contract/interface. This uses FIM to intelligently implement the body.\n"
            "7. FINALLY, call `finalizeAndRenderTranslation` to get the result string and return it to the user.\n"
            "\n"
            "Available Pre-Translated Libraries (Use `loadPreTranslatedLibrary` for these instead of translating manually):\n"
            f"{formatted_libs}\n\n"
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
        if session_id in _session_locks:
            del _session_locks[session_id]

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
        
        # Store the current message as the solidity source for translation context
        set_current_solidity_source(message)
        
        # Translation queue for real-time code chunks if needed (used by tools if they emit chunks)
        translation_chunk_queue: asyncio.Queue = asyncio.Queue()
        set_translation_queue(translation_chunk_queue)

        try:
            yield StreamEvent.stage("thinking", "Working...")

            if session_id not in self.sessions:
                self.sessions[session_id] = []
            
            chat_history = self.sessions[session_id]
            
            final_output = ""
            
            # Retry configuration
            max_retries = 1
            retry_count = 0
            last_error = None
            
            while retry_count <= max_retries:
                try:
                    # We process the stream from the compiled graph using an iterator to allow
                    # concurrent draining of the translation_chunk_queue.
                    agent_aiter = self.agent.astream_events(
                        {"messages": chat_history + [{"role": "user", "content": message}]},
                        version="v1"
                    ).__aiter__()
                    
                    agent_task = asyncio.create_task(agent_aiter.__anext__())
                    queue_task = asyncio.create_task(translation_chunk_queue.get())
            
                    try:
                        while True:
                            done, _ = await asyncio.wait(
                                [agent_task, queue_task],
                                return_when=asyncio.FIRST_COMPLETED
                            )
                            
                            if queue_task in done:
                                try:
                                    item = queue_task.result()
                                    yield item
                                except Exception as e:
                                    logger.error(f"Error reading from translation queue: {e}")
                                queue_task = asyncio.create_task(translation_chunk_queue.get())
                                
                            if agent_task in done:
                                try:
                                    event = agent_task.result()
                                    
                                    kind = event["event"]
                                    run_id = event.get("run_id")
                                    
                                    if kind == "on_tool_start":
                                        name = event.get('name', 'unknown_tool')
                                        inputs = event['data'].get('input')
                                        # format input for display if it's a dict
                                        input_str = str(inputs)
                                        yield StreamEvent.tool_start(name, input_str, run_id)
                                    
                                    elif kind == "on_tool_end":
                                        name = event.get('name', 'unknown_tool')
                                        yield StreamEvent.tool_end(name, success=True, run_id=run_id)
                                        # Render and yield code snapshot after each tool
                                        try:
                                            source = get_session_source()
                                            code_snapshot = source.render()
                                            yield StreamEvent.code_snapshot(code_snapshot)
                                        except Exception as render_err:
                                            logger.warning(f"Failed to render code snapshot: {render_err}")
                                    
                                    elif kind == "on_chat_model_stream":
                                        # We can stream tokens if we want, but for tool usage we often want the final result
                                        # But the requirement asks for tool events mostly.
                                        # If there is content output (non-tool), we can capture it.
                                        chunk = event['data'].get('chunk')
                                        if chunk and hasattr(chunk, 'content') and chunk.content:
                                             final_output += chunk.content
                                             # If we want to stream text content to user:
                                             # yield StreamEvent.content(chunk.content))
                                    
                                    agent_task = asyncio.create_task(agent_aiter.__anext__())
                                except StopAsyncIteration:
                                    # Finished agent stream. Drain remaining queue items.
                                    queue_task.cancel()
                                    while not translation_chunk_queue.empty():
                                        yield translation_chunk_queue.get_nowait()
                                    break
                    finally:
                        if not agent_task.done():
                            agent_task.cancel()
                        if not queue_task.done():
                            queue_task.cancel()
                    
                    # If we get here without exception, break out of retry loop
                    break
                    
                except Exception as e:
                    last_error = e
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.warning(f"Agent stream error, retrying ({retry_count}/{max_retries}): {e}")
                        yield StreamEvent.stage("retrying", f"Retrying... ({retry_count}/{max_retries})")
                        await asyncio.sleep(0.5)  # Brief delay before retry
                    else:
                        raise last_error

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
            solidity_context = f"## Original Solidity Code\n```solidity\n{solidity_code}\n```\n"
        
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
                fixed_code = _extract_ralph_code(fixed_code)
                
                if not fixed_code:
                    logger.warning(f"Empty fix result on iteration {iterations}")
                    continue
                
                current_code = fixed_code
                
                # Emit code snapshot
                yield StreamEvent.code_snapshot(fixed_code)
                
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


    async def _compile_ralph_code(self, code: str) -> Dict[str, Any]:
        node_url = os.getenv("NODE_URL", "https://node.testnet.alephium.org")
        compile_endpoint = f"{node_url}/contracts/compile-project"
        
        compile_request = {
            "code": code,
            "compilerOptions": {
                "ignoreUnusedConstantsWarnings": False,
                "ignoreUnusedVariablesWarnings": False,
                "ignoreUnusedFieldsWarnings": False,
                "ignoreUnusedPrivateFunctionsWarnings": False,
                "ignoreUpdateFieldsCheckWarnings": False,
                "ignoreCheckExternalCallerWarnings": False,
                "ignoreUnusedFunctionReturnWarnings": False,
                "skipAbstractContractCheck": False,
                "skipTests": False
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(compile_endpoint, json=compile_request) as resp:
                    if resp.status == 200:
                        try:
                            result = await resp.json()
                            warnings = result.get("warnings", [])
                            # Also collect warnings from contracts and scripts
                            for contract in result.get("contracts", []):
                                warnings.extend(contract.get("warnings", []))
                            for script in result.get("scripts", []):
                                warnings.extend(script.get("warnings", []))
                                
                            if warnings:
                                # Treat warnings as errors
                                error_msg = "Compilation Warnings (treated as errors):\n" + "\n".join(warnings)
                                logger.info(f"Compilation warnings (treated as errors):\n{error_msg}")
                                return {"success": False, "error": error_msg}
                        except Exception:
                            warnings = []
                        return {"success": True, "warnings": warnings}
                    else:
                        error_text = await resp.text()
                        # Check for abstract contract message (not a real error)
                        if "Code generation is not supported for abstract contract" in error_text:
                            return {"success": True}
                        logger.info(f"Compilation error:\n{error_text}")
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
