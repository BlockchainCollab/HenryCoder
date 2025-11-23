# backend/main.py
import json
import os
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import the translation service
from api_types import TranslateRequest, TranslateResponse
from translation_service import dump_translation, perform_translation

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
    reasoning = ""
    all_warnings = []
    all_errors = []
    async for chunk, reasoning_chunk, warnings, errors in perform_translation(
        request, stream=False  # Ensure streaming is off for this endpoint
    ):
        translated_code += chunk
        reasoning += reasoning_chunk
        all_warnings.extend(warnings)
        all_errors.extend(errors)

    if all_errors:
        print(f"Translation failed with errors: {all_errors}")
        raise HTTPException(
            status_code=500, detail={"message": "Translation failed due to internal errors.", "errors": all_errors}
        )

    return TranslateResponse(
        translated_code=translated_code, reasoning=reasoning, warnings=all_warnings, errors=all_errors
    )


@app.post("/api/translate/stream")
async def translate_code_stream(request: TranslateRequest):
    """
    Streams the translation of an EVM contract to Ralph.
    """
    source_code = request.source_code

    if not source_code.strip():
        raise HTTPException(status_code=400, detail="Please provide EVM code for translation.")

    async def translation_generator():
        complete_code = ""
        async for chunk, reasoning, warnings, errors in perform_translation(request, stream=True):
            complete_code += chunk
            data = {"translated_code": chunk, "reasoning_chunk": reasoning, "warnings": warnings, "errors": errors}
            yield json.dumps(data) + "\n"
        # Dump translation to file
        dump_translation(request, complete_code)

    return StreamingResponse(translation_generator(), media_type="application/json")


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok", "version": "0.1.0"}


import logging
from datetime import datetime

# Chat endpoints
from agent_service import get_agent
from api_types import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streams chat responses with stage updates from the LangChain agent.
    """
    agent = get_agent()

    async def chat_generator():
        try:
            async for event in agent.chat(
                message=request.message, session_id=request.session_id or "default", stream=True
            ):
                # Send event as JSON line
                yield json.dumps(event) + "\n"
        except Exception as e:
            logger.error(f"Chat streaming error: {e}", exc_info=True)
            error_event = {"type": "error", "data": {"message": str(e)}}
            yield json.dumps(error_event) + "\n"

    return StreamingResponse(chat_generator(), media_type="application/x-ndjson")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Non-streaming chat endpoint.
    """
    agent = get_agent()

    response_text = ""
    try:
        async for event in agent.chat(
            message=request.message, session_id=request.session_id or "default", stream=False
        ):
            if event.get("type") == "content":
                response_text += event.get("data", "")
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        message=response_text, session_id=request.session_id or "default", timestamp=datetime.utcnow().isoformat()
    )


@app.delete("/api/chat/session/{session_id}")
async def clear_chat_session(session_id: str):
    """
    Clears chat history for a session.
    """
    agent = get_agent()
    agent.clear_session(session_id)
    return {"status": "ok", "message": f"Session {session_id} cleared"}
