# backend/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv

# Import the translation service
from translation_service import perform_translation
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json

load_dotenv()

app = FastAPI()

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly list all allowed methods
    allow_headers=["Content-Type", "Authorization", "Accept"],  # Explicitly list all allowed headers
    expose_headers=["Content-Length"],  # Headers that can be exposed to the client
    max_age=600,  # How long the results of a preflight request can be cached (in seconds)
)

class TranslationOptions(BaseModel):
    optimize: bool = False
    include_comments: bool = True
    mimic_defaults: bool = False

class TranslateRequest(BaseModel):
    source_code: str
    options: TranslationOptions

class TranslateResponse(BaseModel):
    translated_code: str
    warnings: List[str] = []
    errors: List[str] = []

@app.post("/api/translate")
async def translate_code(request: TranslateRequest):
    """
    Translates an EVM contract to Ralph using the translation_service.
    """
    source_code = request.source_code
    options = request.options

    print(f"Received translation request with options: {options}")

    if not source_code.strip():
        raise HTTPException(status_code=400, detail="Please provide EVM code for translation.")

    # Call the translation service
    translated_code = ""
    all_warnings = []
    all_errors = []
    async for chunk, warnings, errors in perform_translation(
        source_code=source_code,
        optimize=options.optimize,
        include_comments=options.include_comments,
        mimic_defaults=options.mimic_defaults,
        stream=False  # Ensure streaming is off for this endpoint
    ):
        translated_code += chunk
        all_warnings.extend(warnings)
        all_errors.extend(errors)

    if all_errors:
        print(f"Translation failed with errors: {all_errors}")
        raise HTTPException(status_code=500, detail={"message": "Translation failed due to internal errors.", "errors": all_errors})
    
    return TranslateResponse(
        translated_code=translated_code,
        warnings=all_warnings,
        errors=all_errors
    )

@app.post("/api/translate/stream")
async def translate_code_stream(request: TranslateRequest):
    """
    Streams the translation of an EVM contract to Ralph.
    """
    source_code = request.source_code
    options = request.options

    if not source_code.strip():
        raise HTTPException(status_code=400, detail="Please provide EVM code for translation.")

    async def translation_generator():
        async for chunk, warnings, errors in perform_translation(
            source_code=source_code,
            optimize=options.optimize,
            include_comments=options.include_comments,
            mimic_defaults=options.mimic_defaults,
            stream=True
        ):
            data = {
                "translated_code": chunk,
                "warnings": warnings,
                "errors": errors
            }
            yield json.dumps(data) + "\n"

    return StreamingResponse(translation_generator(), media_type="application/json")

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok", "version": "0.1.0"}

