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
from api_types import (
    ChatRequest,
    ChatResponse,
    GasEstimateAllFunctionsResponse,
    GasEstimateRequest,
    GasEstimateResponse,
    TranslateRequest,
    TranslateResponse,
)
from agent_service import get_agent
from gas_estimator import estimate_all_functions, estimate_gas, estimate_with_annotations, get_gas_estimator
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

    # Headers to prevent proxy buffering and ensure proper streaming
    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # Disable NGINX buffering
        "Connection": "keep-alive",
    }
    return StreamingResponse(
        translation_generator(), 
        media_type="application/json",
        headers=headers
    )


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok", "version": "0.1.0"}


# =============================================================================
# Gas Estimation Endpoints
# =============================================================================


@app.post("/api/gas/estimate", response_model=GasEstimateResponse)
async def estimate_gas_endpoint(request: GasEstimateRequest):
    """
    Estimate gas costs for Ralph smart contract code.
    
    Provides a detailed breakdown of gas costs by operation type,
    including storage operations, computations, asset transfers, and more.
    
    Args:
        request: Contains ralph_code and optional function_name
    
    Returns:
        Detailed gas estimation with breakdown and cost in ALPH
    """
    if not request.ralph_code.strip():
        raise HTTPException(status_code=400, detail="Please provide Ralph code for gas estimation.")
    
    try:
        result = estimate_gas(
            ralph_code=request.ralph_code,
            function_name=request.function_name if request.function_name else None
        )
        return GasEstimateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gas estimation failed: {str(e)}")


@app.post("/api/gas/estimate/all", response_model=GasEstimateAllFunctionsResponse)
async def estimate_all_functions_endpoint(request: GasEstimateRequest):
    """
    Estimate gas costs for ALL functions in a Ralph contract.
    
    Analyzes each function separately and provides individual breakdowns
    plus a summary comparison table.
    
    Args:
        request: Contains ralph_code (function_name is ignored)
    
    Returns:
        Gas estimation for each function with summary
    """
    if not request.ralph_code.strip():
        raise HTTPException(status_code=400, detail="Please provide Ralph code for gas estimation.")
    
    try:
        results = estimate_all_functions(request.ralph_code)
        
        if not results:
            raise HTTPException(status_code=400, detail="No functions found in the provided Ralph code.")
        
        # Build response
        functions = {}
        for func_name, result in results.items():
            functions[func_name] = GasEstimateResponse(**result)
        
        # Generate summary report
        estimator = get_gas_estimator()
        summary_lines = [
            "# Gas Estimation Summary",
            "",
            "## Function Comparison",
            "",
            "| Function | Total Gas | Est. Cost (ALPH) |",
            "|----------|-----------|------------------|",
        ]
        
        for func_name, response in sorted(functions.items(), key=lambda x: -x[1].total_gas):
            summary_lines.append(
                f"| `{func_name}` | {response.total_gas:,} | {response.estimated_cost_alph:.10f} |"
            )
        
        summary_lines.extend([
            "",
            "---",
            f"*Analyzed {len(functions)} function(s)*",
        ])
        
        return GasEstimateAllFunctionsResponse(
            functions=functions,
            summary_report="\n".join(summary_lines)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gas estimation failed: {str(e)}")


from api_types import GasAnnotatedResponse


@app.post("/api/gas/estimate/annotated", response_model=GasAnnotatedResponse)
async def estimate_annotated_endpoint(request: GasEstimateRequest):
    """
    Estimate gas costs with line number annotations for frontend display.
    
    Returns gas estimates mapped to specific line numbers, designed for
    gutter decorations in the code viewer.
    
    Args:
        request: Contains ralph_code (function_name is ignored)
    
    Returns:
        Annotated gas estimates with line positions for each function
    """
    if not request.ralph_code.strip():
        raise HTTPException(status_code=400, detail="Please provide Ralph code for gas estimation.")
    
    try:
        result = estimate_with_annotations(request.ralph_code)
        return GasAnnotatedResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gas estimation failed: {str(e)}")


@app.get("/api/gas/constants")
async def get_gas_constants():
    """
    Get Alephium gas constants used for estimation.
    
    Returns the base gas costs for various operations,
    useful for understanding how estimations are calculated.
    """
    from gas_estimator import (
        CONTRACT_STATE_UPDATE_BASE_GAS,
        DEFAULT_GAS_PRICE_NANOALPH,
        GAS_CALL,
        GAS_CONTRACT_EXISTS,
        GAS_COPY_CREATE,
        GAS_CREATE,
        GAS_DESTROY,
        GAS_EC_RECOVER,
        GAS_SIGNATURE,
        GasTier,
        MINIMAL_GAS,
        TX_BASE_GAS,
        TX_INPUT_BASE_GAS,
        TX_OUTPUT_BASE_GAS,
    )
    
    return {
        "transaction": {
            "tx_base_gas": TX_BASE_GAS,
            "tx_input_base_gas": TX_INPUT_BASE_GAS,
            "tx_output_base_gas": TX_OUTPUT_BASE_GAS,
            "minimal_gas": MINIMAL_GAS,
        },
        "gas_tiers": {
            tier.name.lower(): tier.value for tier in GasTier
        },
        "contract_operations": {
            "gas_create": GAS_CREATE,
            "gas_copy_create": GAS_COPY_CREATE,
            "gas_destroy": GAS_DESTROY,
            "gas_contract_exists": GAS_CONTRACT_EXISTS,
            "contract_state_update_base": CONTRACT_STATE_UPDATE_BASE_GAS,
        },
        "cryptography": {
            "gas_signature": GAS_SIGNATURE,
            "gas_ec_recover": GAS_EC_RECOVER,
        },
        "calls": {
            "gas_call": GAS_CALL,
        },
        "pricing": {
            "default_gas_price_nanoalph": DEFAULT_GAS_PRICE_NANOALPH,
            "description": "1 ALPH = 10^9 nanoALPH",
        },
    }


import logging
from datetime import datetime

# Chat endpoints

logger = logging.getLogger(__name__)


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streams chat responses with stage updates from the LangChain agent.
    Accepts optional translation options that are stored for the session.
    """
    agent = get_agent()

    async def chat_generator():
        try:
            async for event in agent.chat(
                message=request.message,
                session_id=request.session_id or "default",
                stream=True,
                options=request.options,  # Pass options to agent
            ):
                # Send event as JSON line
                yield json.dumps(event) + "\n"
        except Exception as e:
            logger.error(f"Chat streaming error: {e}", exc_info=True)
            error_event = {"type": "error", "data": {"message": str(e)}}
            yield json.dumps(error_event) + "\n"

    # Headers to prevent proxy buffering and ensure proper streaming
    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # Disable NGINX buffering
        "Connection": "keep-alive",
    }
    return StreamingResponse(chat_generator(), media_type="application/json", headers=headers)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Non-streaming chat endpoint.
    Accepts optional translation options that are stored for the session.
    """
    agent = get_agent()

    response_text = ""
    try:
        async for event in agent.chat(
            message=request.message,
            session_id=request.session_id or "default",
            stream=False,
            options=request.options,  # Pass options to agent
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


# Fix Code Endpoint
from api_types import FixCodeRequest, FixCodeResponse


@app.post("/api/chat/fix")
async def fix_code(request: FixCodeRequest):
    """
    Fixes Ralph code based on a compilation error with streaming progress.
    
    Uses the AI agent to analyze the error and apply targeted fixes.
    Iterates up to 3 times to ensure the fix compiles successfully.
    Streams stage updates for progress tracking.
    
    Args:
        request: Contains ralph_code and error message
    
    Returns:
        Streaming response with stage events and final result
    """
    if not request.ralph_code.strip():
        raise HTTPException(status_code=400, detail="Please provide Ralph code to fix.")
    
    if not request.error.strip():
        raise HTTPException(status_code=400, detail="Please provide the compilation error.")
    
    agent = get_agent()
    
    async def fix_generator():
        try:
            async for event in agent.fix_code(
                ralph_code=request.ralph_code,
                error=request.error,
                solidity_code=request.solidity_code,
                max_iterations=3
            ):
                yield json.dumps(event) + "\n"
        except Exception as e:
            logger.error(f"Fix code streaming error: {e}", exc_info=True)
            error_event = {"type": "error", "data": {"message": str(e)}}
            yield json.dumps(error_event) + "\n"
    
    return StreamingResponse(fix_generator(), media_type="application/x-ndjson")

