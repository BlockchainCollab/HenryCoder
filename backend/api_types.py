from typing import Any, Dict, Optional

from pydantic import BaseModel


class TranslationOptions(BaseModel):
    optimize: bool
    include_comments: bool
    mimic_defaults: bool
    translate_erc20: bool = False  # Whether to translate ERC20 to Alephium native
    smart: bool = False  # Whether to use the smart LLM model for translation


class PreviousTranslation(BaseModel):
    source_code: str
    warnings: list[str] = []
    errors: list[str] = []


class TranslateRequest(BaseModel):
    source_code: str
    options: TranslationOptions
    previous_translation: Optional[PreviousTranslation] = None


class TranslateResponse(BaseModel):
    translated_code: str
    reasoning: str
    warnings: list[str] = []
    errors: list[str] = []


# Chat API Types
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    context: Optional[Dict[str, Any]] = None  # Additional context (e.g., current code)
    options: Optional[Dict[str, Any]] = None  # Translation options (optimize, include_comments, etc.)


class ChatResponse(BaseModel):
    message: str
    session_id: str
    timestamp: str


# Gas Estimation API Types
class GasEstimateRequest(BaseModel):
    ralph_code: str
    function_name: Optional[str] = None  # Specific function to estimate (None = entire contract)


class GasOperationBreakdown(BaseModel):
    operation: str
    count: int
    gas_cost: int


class GasEstimateResponse(BaseModel):
    breakdown: list[GasOperationBreakdown]
    raw_gas: int
    total_gas: int
    minimal_gas: int
    estimated_cost_alph: float
    gas_price_nanoalph: int
    warnings: list[str]
    report: str  # Markdown formatted report


class GasEstimateAllFunctionsResponse(BaseModel):
    functions: Dict[str, GasEstimateResponse]
    summary_report: str  # Markdown formatted summary


# Annotated Gas Estimation (for frontend gutter decorations)
class GasFunctionAnnotation(BaseModel):
    function_name: str
    start_line: int
    end_line: int
    total_gas: int
    raw_gas: int
    estimated_cost_alph: float
    breakdown: list[GasOperationBreakdown]  # Top 5 operations
    warnings: list[str]


class GasAnnotationSummary(BaseModel):
    total_functions: int
    average_gas: int
    most_expensive_function: Optional[str]
    most_expensive_gas: int


class GasAnnotatedResponse(BaseModel):
    annotations: list[GasFunctionAnnotation]
    summary: GasAnnotationSummary
    gas_price_nanoalph: int
    minimal_gas: int
