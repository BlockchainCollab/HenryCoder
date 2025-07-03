from pydantic import BaseModel
from typing import Optional

class TranslationOptions(BaseModel):
    optimize: bool
    include_comments: bool
    mimic_defaults: bool

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
