from pydantic import BaseModel
from typing import Optional

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
