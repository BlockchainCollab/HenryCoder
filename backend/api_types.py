from pydantic import BaseModel

class TranslationOptions(BaseModel):
    optimize: bool = False
    include_comments: bool = True
    mimic_defaults: bool = False

class TranslateRequest(BaseModel):
    source_code: str
    options: TranslationOptions

class TranslateResponse(BaseModel):
    translated_code: str
    reasoning: str
    warnings: list[str] = []
    errors: list[str] = []
