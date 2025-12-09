"""
Gas Estimation Service for Ralph Smart Contracts.
Provides static gas cost analysis based on Alephium's gas schedule.

Gas constants sourced from Alephium repository:
- protocol/src/main/scala/org/alephium/protocol/vm/GasSchedule.scala
- protocol/src/main/scala/org/alephium/protocol/model/Transaction.scala
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# =============================================================================
# Gas Constants from Alephium Protocol
# =============================================================================

class GasTier(Enum):
    """Base gas tiers from Alephium VM."""
    ZERO = 0
    BASE = 2
    VERY_LOW = 3
    LOW = 5
    MID = 8
    HIGH = 10


# Transaction base costs
TX_BASE_GAS = 1_000
TX_INPUT_BASE_GAS = 2_000
TX_OUTPUT_BASE_GAS = 4_500

# Minimum gas requirement
MINIMAL_GAS = 20_000

# Contract operations
GAS_CREATE = 32_000
GAS_COPY_CREATE = 24_000
GAS_DESTROY = 2_000
GAS_CONTRACT_EXISTS = 800
GAS_MIGRATE = 32_000
GAS_BALANCE = 30
CONTRACT_STATE_UPDATE_BASE_GAS = 5_000

# Signature verification
GAS_SIGNATURE = 2_000
GAS_EC_RECOVER = 2_500

# Call gas
GAS_CALL = 200

# Default gas price (100 nanoALPH = 100 * 10^-9 ALPH)
DEFAULT_GAS_PRICE_NANOALPH = 100


def gas_hash(byte_length: int) -> int:
    """Calculate hash gas cost: baseGas + extraGasPerWord * wordLength."""
    word_length = (byte_length + 7) // 8
    return 30 + 6 * word_length


def gas_log(num_fields: int) -> int:
    """Calculate log/event gas cost: gasBase + gasPerData * n."""
    return 100 + 20 * num_fields


def gas_bytes_concat(byte_length: int) -> int:
    """Calculate ByteVec concat gas: GasVeryLow + byteLength."""
    return GasTier.VERY_LOW.value + byte_length


def gas_bytes_slice(byte_length: int) -> int:
    """Calculate ByteVec slice gas: GasVeryLow + byteLength."""
    return GasTier.VERY_LOW.value + byte_length


def contract_load_gas(estimated_size: int) -> int:
    """Calculate contract loading gas: 800 + wordLength(estimatedSize)."""
    word_length = (estimated_size + 7) // 8
    return 800 + word_length


# =============================================================================
# Gas Operation Categories
# =============================================================================

class GasOperation(Enum):
    """Gas operation categories with accurate Alephium costs."""
    
    # Transaction base costs
    TX_BASE = ("Transaction Base", TX_BASE_GAS)
    TX_INPUT_BASE = ("Input Base", TX_INPUT_BASE_GAS)
    TX_OUTPUT_BASE = ("Output Base", TX_OUTPUT_BASE_GAS)
    
    # Storage operations
    LOAD_FIELD = ("Load Field (immutable)", GasTier.VERY_LOW.value)
    LOAD_MUT_FIELD = ("Load Field (mutable)", GasTier.VERY_LOW.value)
    STORE_MUT_FIELD = ("Store Field (mutable)", GasTier.VERY_LOW.value)
    CONTRACT_STATE_UPDATE = ("Contract State Update", CONTRACT_STATE_UPDATE_BASE_GAS)
    
    # Mapping operations (estimated based on storage + lookup)
    MAPPING_ACCESS = ("Mapping Read", GAS_CONTRACT_EXISTS + GasTier.LOW.value)
    MAPPING_INSERT = ("Mapping Insert", CONTRACT_STATE_UPDATE_BASE_GAS + GAS_CREATE // 4)
    MAPPING_REMOVE = ("Mapping Remove", CONTRACT_STATE_UPDATE_BASE_GAS)
    MAPPING_CONTAINS = ("Mapping Contains", GAS_CONTRACT_EXISTS)
    
    # Arithmetic operations
    ARITHMETIC_SIMPLE = ("Arithmetic (add/sub)", GasTier.VERY_LOW.value)
    ARITHMETIC_COMPLEX = ("Arithmetic (mul/div/mod)", GasTier.LOW.value)
    MOD_ARITHMETIC = ("Modular Arithmetic", GasTier.MID.value)
    
    # Comparison & logic
    COMPARISON = ("Comparison", GasTier.VERY_LOW.value)
    LOGIC = ("Logic Op", GasTier.VERY_LOW.value)
    BITWISE = ("Bitwise Op", GasTier.LOW.value)
    
    # Hashing (base cost, actual varies by input size)
    HASH_BLAKE2B = ("Blake2b Hash", 36)  # 30 + 6 * 1 word
    HASH_KECCAK = ("Keccak256 Hash", 36)
    HASH_SHA256 = ("SHA256 Hash", 36)
    HASH_SHA3 = ("SHA3 Hash", 36)
    
    # Signature verification
    SIGNATURE_VERIFY = ("Signature Verify", GAS_SIGNATURE)
    EC_RECOVER = ("EC Recover", GAS_EC_RECOVER)
    
    # Control flow
    BRANCH = ("Branch/Condition", GasTier.MID.value)
    LOOP_ITERATION = ("Loop Iteration", GasTier.MID.value)
    ASSERT = ("Assert", GasTier.VERY_LOW.value)
    
    # Function calls
    FUNCTION_CALL = ("Internal Call", GAS_CALL)
    EXTERNAL_CALL = ("External Call", GAS_CALL + GAS_CONTRACT_EXISTS)
    
    # Asset operations
    TRANSFER_ALPH = ("Transfer ALPH", GasTier.LOW.value)
    TRANSFER_TOKEN = ("Transfer Token", GasTier.LOW.value)
    APPROVE_ALPH = ("Approve ALPH", GasTier.LOW.value)
    APPROVE_TOKEN = ("Approve Token", GasTier.LOW.value)
    TOKEN_REMAINING = ("Token Remaining", GasTier.LOW.value)
    ALPH_REMAINING = ("ALPH Remaining", GasTier.LOW.value)
    
    # Contract operations
    CREATE_CONTRACT = ("Create Contract", GAS_CREATE)
    COPY_CREATE_CONTRACT = ("Copy Create Contract", GAS_COPY_CREATE)
    DESTROY_SELF = ("Destroy Self", GAS_DESTROY)
    CONTRACT_EXISTS = ("Contract Exists", GAS_CONTRACT_EXISTS)
    SELF_ADDRESS = ("Self Address", GasTier.VERY_LOW.value)
    SELF_CONTRACT_ID = ("Self Contract ID", GasTier.VERY_LOW.value)
    CALLER_ADDRESS = ("Caller Address", GasTier.LOW.value)
    CALLER_CONTRACT_ID = ("Caller Contract ID", GasTier.LOW.value)
    
    # Memory/Stack
    STACK_OP = ("Stack Op (dup/swap/pop)", GasTier.BASE.value)
    LOAD_LOCAL = ("Load Local", GasTier.VERY_LOW.value)
    STORE_LOCAL = ("Store Local", GasTier.VERY_LOW.value)
    BYTEVEC_CONCAT = ("ByteVec Concat", GasTier.VERY_LOW.value + 32)  # Assume 32 bytes
    BYTEVEC_SLICE = ("ByteVec Slice", GasTier.VERY_LOW.value + 32)
    BYTEVEC_SIZE = ("ByteVec Size", GasTier.BASE.value)
    
    # Events (base cost, varies by fields)
    LOG_EVENT = ("Log Event", 100)
    LOG_FIELD = ("Log Field", 20)
    
    # Constants
    CONST_LOAD = ("Constant Load", GasTier.BASE.value)
    
    def __init__(self, description: str, base_cost: int):
        self.description = description
        self.base_cost = base_cost


# =============================================================================
# Gas Breakdown Data Structure
# =============================================================================

@dataclass
class GasBreakdown:
    """Detailed gas breakdown by operation type."""
    operations: Dict[str, int] = field(default_factory=dict)
    counts: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def add(self, operation: GasOperation, count: int = 1, multiplier: int = 1) -> None:
        """Add gas cost for an operation."""
        cost = operation.base_cost * count * multiplier
        key = operation.description
        self.operations[key] = self.operations.get(key, 0) + cost
        self.counts[key] = self.counts.get(key, 0) + count
    
    def add_custom(self, description: str, gas_cost: int, count: int = 1) -> None:
        """Add custom gas cost."""
        self.operations[description] = self.operations.get(description, 0) + gas_cost
        self.counts[description] = self.counts.get(description, 0) + count
    
    @property
    def total_gas(self) -> int:
        """Total gas units (minimum MINIMAL_GAS)."""
        return max(MINIMAL_GAS, sum(self.operations.values()))
    
    @property
    def raw_gas(self) -> int:
        """Raw gas units without minimum."""
        return sum(self.operations.values())
    
    def to_alph(self, gas_price_nanoalph: int = DEFAULT_GAS_PRICE_NANOALPH) -> float:
        """
        Convert gas to ALPH.
        
        Args:
            gas_price_nanoalph: Gas price in nanoALPH (default: 100 nanoALPH)
        
        Returns:
            Cost in ALPH
        """
        # 1 ALPH = 10^18 attoALPH = 10^9 nanoALPH
        return (self.total_gas * gas_price_nanoalph) / 1e9
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "breakdown": [
                {
                    "operation": op,
                    "count": self.counts.get(op, 0),
                    "gas_cost": cost,
                }
                for op, cost in sorted(self.operations.items(), key=lambda x: -x[1])
            ],
            "raw_gas": self.raw_gas,
            "total_gas": self.total_gas,
            "minimal_gas": MINIMAL_GAS,
            "estimated_cost_alph": round(self.to_alph(), 10),
            "gas_price_nanoalph": DEFAULT_GAS_PRICE_NANOALPH,
            "warnings": self.warnings,
        }


# =============================================================================
# Ralph Gas Estimator
# =============================================================================

class RalphGasEstimator:
    """Static gas estimator for Ralph smart contracts."""
    
    # Regex patterns for Ralph code analysis
    PATTERNS = {
        # State field access (mutable and immutable)
        "load_mut_field": re.compile(r'\b(mut\s+\w+)\s*(?!=)', re.MULTILINE),
        "store_mut_field": re.compile(r'\b(\w+)\s*=(?!=)', re.MULTILINE),
        
        # Mapping operations
        "mapping_access": re.compile(r'(\w+)\[([^\]]+)\](?!\s*=)', re.MULTILINE),
        "mapping_insert": re.compile(r'(\w+)\.insert!\s*\(', re.MULTILINE),
        "mapping_remove": re.compile(r'(\w+)\.remove!\s*\(', re.MULTILINE),
        "mapping_contains": re.compile(r'(\w+)\.contains!\s*\(', re.MULTILINE),
        
        # Arithmetic
        "arithmetic_simple": re.compile(r'[\+\-](?!=)', re.MULTILINE),
        "arithmetic_complex": re.compile(r'[\*\/\%](?!=)', re.MULTILINE),
        "mod_arithmetic": re.compile(r'\b(addModN|subModN|mulModN)!\s*\(', re.MULTILINE),
        
        # Comparison & logic
        "comparison": re.compile(r'[<>]=?|[!=]=', re.MULTILINE),
        "logic": re.compile(r'\b(&&|\|\||!)\b', re.MULTILINE),
        "bitwise": re.compile(r'\b(&|\||\^|<<|>>)\b(?!=)', re.MULTILINE),
        
        # Hashing
        "blake2b": re.compile(r'\bblake2b!\s*\(', re.MULTILINE),
        "keccak256": re.compile(r'\bkeccak256!\s*\(', re.MULTILINE),
        "sha256": re.compile(r'\bsha256!\s*\(', re.MULTILINE),
        "sha3": re.compile(r'\bsha3!\s*\(', re.MULTILINE),
        
        # Signature verification
        "verify_secp256k1": re.compile(r'\bverifySecP256K1!\s*\(', re.MULTILINE),
        "verify_ed25519": re.compile(r'\bverifyED25519!\s*\(', re.MULTILINE),
        "ec_recover": re.compile(r'\bethEcRecover!\s*\(', re.MULTILINE),
        "check_caller": re.compile(r'\bcheckCaller!\s*\(', re.MULTILINE),
        
        # Control flow
        "if_statement": re.compile(r'\bif\s*[\(\{]', re.MULTILINE),
        "while_loop": re.compile(r'\bwhile\s*[\(\{]', re.MULTILINE),
        "for_loop": re.compile(r'\bfor\s*[\(\{]', re.MULTILINE),
        "assert": re.compile(r'\bassert!\s*\(', re.MULTILINE),
        
        # Function definitions and calls
        "function_def": re.compile(r'\b(pub\s+)?fn\s+(\w+)\s*[\(\[]', re.MULTILINE),
        "function_call": re.compile(r'\b([a-z][a-zA-Z0-9]*)\s*\((?![^)]*->)', re.MULTILINE),
        
        # Asset operations
        "transfer_alph": re.compile(r'\btransferAlph(FromSelf|ToSelf)?!\s*\(', re.MULTILINE),
        "transfer_token": re.compile(r'\btransferToken(FromSelf|ToSelf)?!\s*\(', re.MULTILINE),
        "approve_alph": re.compile(r'\bapproveAlph!\s*\(', re.MULTILINE),
        "approve_token": re.compile(r'\bapproveToken!\s*\(', re.MULTILINE),
        "alph_remaining": re.compile(r'\balphRemaining!\s*\(', re.MULTILINE),
        "token_remaining": re.compile(r'\btokenRemaining!\s*\(', re.MULTILINE),
        "burn_token": re.compile(r'\bburnToken!\s*\(', re.MULTILINE),
        
        # Contract operations
        "create_contract": re.compile(r'\bcreateContract!\s*\(', re.MULTILINE),
        "create_contract_token": re.compile(r'\bcreateContractWithToken!\s*\(', re.MULTILINE),
        "copy_create_contract": re.compile(r'\bcopyCreateContract(WithToken)?!\s*\(', re.MULTILINE),
        "destroy_self": re.compile(r'\bdestroyself!\s*\(', re.MULTILINE),
        "migrate": re.compile(r'\bmigrate(WithFields)?!\s*\(', re.MULTILINE),
        "contract_exists": re.compile(r'\bcontractExists!\s*\(', re.MULTILINE),
        "self_address": re.compile(r'\bselfAddress!\s*\(', re.MULTILINE),
        "self_contract_id": re.compile(r'\bselfContractId!\s*\(', re.MULTILINE),
        "caller_address": re.compile(r'\bcallerAddress!\s*\(', re.MULTILINE),
        "caller_contract_id": re.compile(r'\bcallerContractId!\s*\(', re.MULTILINE),
        
        # External calls (method calls on contract references)
        "external_call": re.compile(r'\b(\w+)\.(\w+)\s*\(', re.MULTILINE),
        
        # Events
        "emit_event": re.compile(r'\bemit\s+(\w+)\s*\(([^)]*)\)', re.MULTILINE),
        
        # ByteVec operations
        "bytevec_concat": re.compile(r'\b(concat|⧺)\s*\(', re.MULTILINE),
        "bytevec_slice": re.compile(r'\b(byteVecSlice|slice)!\s*\(', re.MULTILINE),
        "bytevec_size": re.compile(r'\bsize!\s*\(', re.MULTILINE),
        
        # State variable declarations
        "mut_state_decl": re.compile(r'\b(mut\s+\w+)\s*:', re.MULTILINE),
        "mapping_decl": re.compile(r'\b(Map|mapping)\s*\[', re.MULTILINE),
        
        # Constants
        "const_decl": re.compile(r'\bconst\s+\w+\s*=', re.MULTILINE),
    }
    
    def __init__(self):
        """Initialize the estimator."""
        pass
    
    def _extract_function_body(self, ralph_code: str, function_name: str) -> Optional[str]:
        """Extract a specific function's body from the code."""
        # Try to find the function
        func_pattern = re.compile(
            rf'\b(?:pub\s+)?fn\s+{re.escape(function_name)}\s*[\(\[]',
            re.MULTILINE
        )
        match = func_pattern.search(ralph_code)
        if not match:
            return None
        
        # Find the opening brace
        start_pos = match.end()
        brace_pos = ralph_code.find('{', start_pos)
        if brace_pos == -1:
            return None
        
        # Find matching closing brace
        brace_count = 1
        end_pos = brace_pos + 1
        for i, char in enumerate(ralph_code[brace_pos + 1:]):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = brace_pos + 1 + i + 1
                    break
        
        return ralph_code[match.start():end_pos]
    
    def estimate(self, ralph_code: str, function_name: Optional[str] = None) -> GasBreakdown:
        """
        Estimate gas cost for Ralph code.
        
        Args:
            ralph_code: The Ralph source code to analyze
            function_name: Specific function to estimate (None = entire contract)
        
        Returns:
            GasBreakdown with detailed cost analysis
        """
        breakdown = GasBreakdown()
        code_to_analyze = ralph_code
        
        # Extract specific function if requested
        if function_name:
            func_body = self._extract_function_body(ralph_code, function_name)
            if func_body:
                code_to_analyze = func_body
            else:
                breakdown.warnings.append(f"Function '{function_name}' not found, analyzing entire contract")
        
        # Transaction base costs
        breakdown.add(GasOperation.TX_BASE)
        breakdown.add(GasOperation.TX_INPUT_BASE)
        breakdown.add(GasOperation.TX_OUTPUT_BASE)
        
        # Detect state complexity
        mut_state_count = len(self.PATTERNS["mut_state_decl"].findall(ralph_code))
        mapping_count = len(self.PATTERNS["mapping_decl"].findall(ralph_code))
        
        if mut_state_count:
            breakdown.warnings.append(f"Contract has {mut_state_count} mutable state field(s)")
        if mapping_count:
            breakdown.warnings.append(f"Contract has {mapping_count} mapping(s) - costs vary by usage")
        
        # Mapping operations
        mapping_access = len(self.PATTERNS["mapping_access"].findall(code_to_analyze))
        mapping_insert = len(self.PATTERNS["mapping_insert"].findall(code_to_analyze))
        mapping_remove = len(self.PATTERNS["mapping_remove"].findall(code_to_analyze))
        mapping_contains = len(self.PATTERNS["mapping_contains"].findall(code_to_analyze))
        
        if mapping_access:
            breakdown.add(GasOperation.MAPPING_ACCESS, mapping_access)
        if mapping_insert:
            breakdown.add(GasOperation.MAPPING_INSERT, mapping_insert)
        if mapping_remove:
            breakdown.add(GasOperation.MAPPING_REMOVE, mapping_remove)
        if mapping_contains:
            breakdown.add(GasOperation.MAPPING_CONTAINS, mapping_contains)
        
        # State field operations
        store_ops = len(self.PATTERNS["store_mut_field"].findall(code_to_analyze))
        if store_ops and mut_state_count:
            # Estimate state updates
            estimated_updates = min(store_ops, mut_state_count * 2)
            breakdown.add(GasOperation.CONTRACT_STATE_UPDATE, estimated_updates)
        
        # Arithmetic operations
        arith_simple = len(self.PATTERNS["arithmetic_simple"].findall(code_to_analyze))
        arith_complex = len(self.PATTERNS["arithmetic_complex"].findall(code_to_analyze))
        mod_arith = len(self.PATTERNS["mod_arithmetic"].findall(code_to_analyze))
        
        if arith_simple:
            breakdown.add(GasOperation.ARITHMETIC_SIMPLE, arith_simple)
        if arith_complex:
            breakdown.add(GasOperation.ARITHMETIC_COMPLEX, arith_complex)
        if mod_arith:
            breakdown.add(GasOperation.MOD_ARITHMETIC, mod_arith)
        
        # Comparison & logic
        comparisons = len(self.PATTERNS["comparison"].findall(code_to_analyze))
        logic_ops = len(self.PATTERNS["logic"].findall(code_to_analyze))
        bitwise_ops = len(self.PATTERNS["bitwise"].findall(code_to_analyze))
        
        if comparisons:
            breakdown.add(GasOperation.COMPARISON, comparisons)
        if logic_ops:
            breakdown.add(GasOperation.LOGIC, logic_ops)
        if bitwise_ops:
            breakdown.add(GasOperation.BITWISE, bitwise_ops)
        
        # Hash operations
        blake2b = len(self.PATTERNS["blake2b"].findall(code_to_analyze))
        keccak = len(self.PATTERNS["keccak256"].findall(code_to_analyze))
        sha256 = len(self.PATTERNS["sha256"].findall(code_to_analyze))
        sha3 = len(self.PATTERNS["sha3"].findall(code_to_analyze))
        
        if blake2b:
            breakdown.add(GasOperation.HASH_BLAKE2B, blake2b)
        if keccak:
            breakdown.add(GasOperation.HASH_KECCAK, keccak)
        if sha256:
            breakdown.add(GasOperation.HASH_SHA256, sha256)
        if sha3:
            breakdown.add(GasOperation.HASH_SHA3, sha3)
        
        # Signature verification
        secp256k1 = len(self.PATTERNS["verify_secp256k1"].findall(code_to_analyze))
        ed25519 = len(self.PATTERNS["verify_ed25519"].findall(code_to_analyze))
        ec_recover = len(self.PATTERNS["ec_recover"].findall(code_to_analyze))
        check_caller = len(self.PATTERNS["check_caller"].findall(code_to_analyze))
        
        if secp256k1:
            breakdown.add(GasOperation.SIGNATURE_VERIFY, secp256k1)
        if ed25519:
            breakdown.add(GasOperation.SIGNATURE_VERIFY, ed25519)
        if ec_recover:
            breakdown.add(GasOperation.EC_RECOVER, ec_recover)
        if check_caller:
            breakdown.add(GasOperation.SIGNATURE_VERIFY, check_caller)
        
        # Control flow
        if_count = len(self.PATTERNS["if_statement"].findall(code_to_analyze))
        while_count = len(self.PATTERNS["while_loop"].findall(code_to_analyze))
        for_count = len(self.PATTERNS["for_loop"].findall(code_to_analyze))
        assert_count = len(self.PATTERNS["assert"].findall(code_to_analyze))
        
        if if_count:
            breakdown.add(GasOperation.BRANCH, if_count)
        if while_count:
            # Estimate 10 iterations per loop (conservative)
            breakdown.add(GasOperation.LOOP_ITERATION, while_count, multiplier=10)
            breakdown.warnings.append(f"While loop(s) detected ({while_count}) - actual cost depends on iterations")
        if for_count:
            breakdown.add(GasOperation.LOOP_ITERATION, for_count, multiplier=10)
            breakdown.warnings.append(f"For loop(s) detected ({for_count}) - actual cost depends on iterations")
        if assert_count:
            breakdown.add(GasOperation.ASSERT, assert_count)
        
        # Function calls
        func_calls = len(self.PATTERNS["function_call"].findall(code_to_analyze))
        # Subtract built-in calls that were already counted
        builtin_count = (blake2b + keccak + sha256 + sha3 + secp256k1 + ed25519 + 
                        ec_recover + check_caller + assert_count + mapping_insert + 
                        mapping_remove + mapping_contains)
        internal_calls = max(0, func_calls - builtin_count)
        if internal_calls:
            breakdown.add(GasOperation.FUNCTION_CALL, internal_calls)
        
        # External calls
        external_matches = self.PATTERNS["external_call"].findall(code_to_analyze)
        # Filter out known non-external patterns (like mapping.insert)
        external_calls = len([m for m in external_matches 
                             if m[1] not in ('insert', 'remove', 'contains', 'get')])
        if external_calls:
            breakdown.add(GasOperation.EXTERNAL_CALL, external_calls)
        
        # Asset operations
        transfer_alph = len(self.PATTERNS["transfer_alph"].findall(code_to_analyze))
        transfer_token = len(self.PATTERNS["transfer_token"].findall(code_to_analyze))
        approve_alph = len(self.PATTERNS["approve_alph"].findall(code_to_analyze))
        approve_token = len(self.PATTERNS["approve_token"].findall(code_to_analyze))
        alph_remaining = len(self.PATTERNS["alph_remaining"].findall(code_to_analyze))
        token_remaining = len(self.PATTERNS["token_remaining"].findall(code_to_analyze))
        burn_token = len(self.PATTERNS["burn_token"].findall(code_to_analyze))
        
        if transfer_alph:
            breakdown.add(GasOperation.TRANSFER_ALPH, transfer_alph)
        if transfer_token:
            breakdown.add(GasOperation.TRANSFER_TOKEN, transfer_token)
        if approve_alph:
            breakdown.add(GasOperation.APPROVE_ALPH, approve_alph)
        if approve_token:
            breakdown.add(GasOperation.APPROVE_TOKEN, approve_token)
        if alph_remaining:
            breakdown.add(GasOperation.ALPH_REMAINING, alph_remaining)
        if token_remaining:
            breakdown.add(GasOperation.TOKEN_REMAINING, token_remaining)
        if burn_token:
            breakdown.add_custom("Burn Token", CONTRACT_STATE_UPDATE_BASE_GAS, burn_token)
        
        # Contract operations
        create_contract = len(self.PATTERNS["create_contract"].findall(code_to_analyze))
        create_contract_token = len(self.PATTERNS["create_contract_token"].findall(code_to_analyze))
        copy_create = len(self.PATTERNS["copy_create_contract"].findall(code_to_analyze))
        destroy_self = len(self.PATTERNS["destroy_self"].findall(code_to_analyze))
        migrate = len(self.PATTERNS["migrate"].findall(code_to_analyze))
        contract_exists = len(self.PATTERNS["contract_exists"].findall(code_to_analyze))
        self_address = len(self.PATTERNS["self_address"].findall(code_to_analyze))
        self_contract_id = len(self.PATTERNS["self_contract_id"].findall(code_to_analyze))
        caller_address = len(self.PATTERNS["caller_address"].findall(code_to_analyze))
        caller_contract_id = len(self.PATTERNS["caller_contract_id"].findall(code_to_analyze))
        
        if create_contract:
            breakdown.add(GasOperation.CREATE_CONTRACT, create_contract)
            breakdown.warnings.append("Contract creation detected - consider child contract sizes")
        if create_contract_token:
            breakdown.add(GasOperation.CREATE_CONTRACT, create_contract_token)
        if copy_create:
            breakdown.add(GasOperation.COPY_CREATE_CONTRACT, copy_create)
        if destroy_self:
            breakdown.add(GasOperation.DESTROY_SELF, destroy_self)
        if migrate:
            breakdown.add_custom("Migrate Contract", GAS_MIGRATE, migrate)
        if contract_exists:
            breakdown.add(GasOperation.CONTRACT_EXISTS, contract_exists)
        if self_address:
            breakdown.add(GasOperation.SELF_ADDRESS, self_address)
        if self_contract_id:
            breakdown.add(GasOperation.SELF_CONTRACT_ID, self_contract_id)
        if caller_address:
            breakdown.add(GasOperation.CALLER_ADDRESS, caller_address)
        if caller_contract_id:
            breakdown.add(GasOperation.CALLER_CONTRACT_ID, caller_contract_id)
        
        # Events
        event_matches = self.PATTERNS["emit_event"].findall(code_to_analyze)
        if event_matches:
            breakdown.add(GasOperation.LOG_EVENT, len(event_matches))
            for event_name, event_args in event_matches:
                field_count = len([f for f in event_args.split(',') if f.strip()])
                if field_count:
                    breakdown.add(GasOperation.LOG_FIELD, field_count)
        
        # ByteVec operations
        bytevec_concat = len(self.PATTERNS["bytevec_concat"].findall(code_to_analyze))
        bytevec_slice = len(self.PATTERNS["bytevec_slice"].findall(code_to_analyze))
        bytevec_size = len(self.PATTERNS["bytevec_size"].findall(code_to_analyze))
        
        if bytevec_concat:
            breakdown.add(GasOperation.BYTEVEC_CONCAT, bytevec_concat)
        if bytevec_slice:
            breakdown.add(GasOperation.BYTEVEC_SLICE, bytevec_slice)
        if bytevec_size:
            breakdown.add(GasOperation.BYTEVEC_SIZE, bytevec_size)
        
        return breakdown
    
    def estimate_function(self, ralph_code: str, function_name: str) -> GasBreakdown:
        """Estimate gas for a specific function."""
        return self.estimate(ralph_code, function_name)
    
    def estimate_all_functions(self, ralph_code: str) -> Dict[str, GasBreakdown]:
        """Estimate gas for all functions in a contract."""
        results = {}
        
        # Find all function names
        for match in self.PATTERNS["function_def"].finditer(ralph_code):
            func_name = match.group(2)
            results[func_name] = self.estimate_function(ralph_code, func_name)
        
        return results
    
    def format_report(self, breakdown: GasBreakdown, function_name: Optional[str] = None) -> str:
        """Format a human-readable gas estimation report."""
        header = "## Gas Estimation" + (f" for `{function_name}`" if function_name else " (Full Contract)")
        
        report = [
            header,
            "",
            "### Summary",
            f"- **Total Gas Units:** {breakdown.total_gas:,}",
            f"- **Raw Gas (before minimum):** {breakdown.raw_gas:,}",
            f"- **Minimum Gas:** {MINIMAL_GAS:,}",
            f"- **Estimated Cost:** {breakdown.to_alph():.10f} ALPH",
            f"- **Gas Price:** {DEFAULT_GAS_PRICE_NANOALPH} nanoALPH",
            "",
            "### Breakdown by Operation",
            "",
            "| Operation | Count | Gas Cost |",
            "|-----------|-------|----------|",
        ]
        
        for item in breakdown.to_dict()["breakdown"]:
            report.append(f"| {item['operation']} | {item['count']} | {item['gas_cost']:,} |")
        
        if breakdown.warnings:
            report.extend([
                "",
                "### ⚠️ Notes",
                "",
            ])
            for warning in breakdown.warnings:
                report.append(f"- {warning}")
        
        report.extend([
            "",
            "---",
            "*This is a static estimation based on code analysis. Actual gas costs may vary based on:*",
            "- *Loop iteration counts*",
            "- *Mapping entry sizes*",
            "- *Contract state complexity*",
            "- *Runtime conditions*",
        ])
        
        return "\n".join(report)


# =============================================================================
# Function Line Detection
# =============================================================================

@dataclass
class FunctionLocation:
    """Location information for a function in the code."""
    name: str
    start_line: int
    end_line: int


def find_function_locations(ralph_code: str) -> List[FunctionLocation]:
    """
    Find the line numbers where each function is defined.
    
    Args:
        ralph_code: The Ralph source code
    
    Returns:
        List of FunctionLocation with name and line numbers
    """
    locations = []
    lines = ralph_code.split('\n')
    
    # Pattern to match function definitions
    func_pattern = re.compile(r'\b(?:pub\s+)?fn\s+(\w+)\s*[\(\[]')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        match = func_pattern.search(line)
        
        if match:
            func_name = match.group(1)
            start_line = i + 1  # 1-indexed
            
            # Find the opening brace
            brace_start = -1
            search_line = i
            while search_line < len(lines) and brace_start == -1:
                brace_pos = lines[search_line].find('{')
                if brace_pos != -1:
                    brace_start = search_line
                else:
                    search_line += 1
            
            if brace_start == -1:
                i += 1
                continue
            
            # Count braces to find end of function
            brace_count = 0
            end_line = brace_start
            
            for j in range(brace_start, len(lines)):
                for char in lines[j]:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_line = j + 1  # 1-indexed
                            break
                if brace_count == 0:
                    break
            
            locations.append(FunctionLocation(
                name=func_name,
                start_line=start_line,
                end_line=end_line
            ))
        
        i += 1
    
    return locations


# =============================================================================
# Public API
# =============================================================================

# Singleton instance
_estimator: Optional[RalphGasEstimator] = None


def get_gas_estimator() -> RalphGasEstimator:
    """Get or create the global gas estimator instance."""
    global _estimator
    if _estimator is None:
        _estimator = RalphGasEstimator()
    return _estimator


def estimate_gas(ralph_code: str, function_name: Optional[str] = None) -> Dict:
    """
    Estimate gas for Ralph code.
    
    Args:
        ralph_code: The Ralph source code
        function_name: Optional specific function to analyze
    
    Returns:
        Dictionary with gas estimation details
    """
    estimator = get_gas_estimator()
    breakdown = estimator.estimate(ralph_code, function_name)
    result = breakdown.to_dict()
    result["report"] = estimator.format_report(breakdown, function_name)
    return result


def estimate_all_functions(ralph_code: str) -> Dict[str, Dict]:
    """
    Estimate gas for all functions in Ralph code.
    
    Args:
        ralph_code: The Ralph source code
    
    Returns:
        Dictionary mapping function names to their estimation details
    """
    estimator = get_gas_estimator()
    results = {}
    
    for func_name, breakdown in estimator.estimate_all_functions(ralph_code).items():
        result = breakdown.to_dict()
        result["report"] = estimator.format_report(breakdown, func_name)
        results[func_name] = result
    
    return results


def estimate_with_annotations(ralph_code: str) -> Dict:
    """
    Estimate gas for all functions with line number annotations.
    
    This is designed for frontend gutter decorations - provides
    gas costs mapped to specific line numbers.
    
    Args:
        ralph_code: The Ralph source code
    
    Returns:
        Dictionary with function estimates and line mappings
    """
    estimator = get_gas_estimator()
    
    # Get function locations
    locations = find_function_locations(ralph_code)
    
    # Get gas estimates for each function
    function_estimates = estimator.estimate_all_functions(ralph_code)
    
    # Build annotated results
    annotations = []
    
    for loc in locations:
        if loc.name in function_estimates:
            breakdown = function_estimates[loc.name]
            annotations.append({
                "function_name": loc.name,
                "start_line": loc.start_line,
                "end_line": loc.end_line,
                "total_gas": breakdown.total_gas,
                "raw_gas": breakdown.raw_gas,
                "estimated_cost_alph": round(breakdown.to_alph(), 10),
                "breakdown": breakdown.to_dict()["breakdown"][:5],  # Top 5 operations
                "warnings": breakdown.warnings,
            })
    
    # Calculate contract-level summary
    total_functions = len(annotations)
    avg_gas = sum(a["total_gas"] for a in annotations) / total_functions if total_functions > 0 else 0
    max_gas_func = max(annotations, key=lambda x: x["total_gas"]) if annotations else None
    
    return {
        "annotations": annotations,
        "summary": {
            "total_functions": total_functions,
            "average_gas": round(avg_gas),
            "most_expensive_function": max_gas_func["function_name"] if max_gas_func else None,
            "most_expensive_gas": max_gas_func["total_gas"] if max_gas_func else 0,
        },
        "gas_price_nanoalph": DEFAULT_GAS_PRICE_NANOALPH,
        "minimal_gas": MINIMAL_GAS,
    }
