from pydantic import BaseModel
from typing import Optional, Dict, Any

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

class ChatResponse(BaseModel):
    message: str
    session_id: str
    timestamp: str
