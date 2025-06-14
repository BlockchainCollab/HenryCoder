import json
import os
from typing import AsyncGenerator
import openai
from dotenv import load_dotenv
from .translation_context import RALPH_DETAILS, EXAMPLE_TRANSLATIONS

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), "translations")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "documentation")

if not API_KEY or not API_URL or not LLM_MODEL:
    raise RuntimeError("API_KEY, API_URL, and LLM_MODEL must be set in the environment variables.")

SYSTEM_PROMPT = "\n".join([
        "You are an expert EVM to Ralph translator.",
        "Translate the following EVM (Solidity) code to Ralph, adhering to the Ralph language specifications and best practices.",
        "Consider the following details about the Ralph language:",
        RALPH_DETAILS,
        "\nHere are some examples of EVM to Ralph translations:",
        EXAMPLE_TRANSLATIONS
    ])

async def perform_translation(
    source_code: str, optimize: bool, include_comments: bool, mimic_defaults: bool = False, stream: bool = False
) -> AsyncGenerator[tuple[str, str, list[str], list[str]], None]:
    """
    Performs the translation using OpenAI-compatible API via the OpenAI Python client.
    If `stream` is True, yields translation chunks incrementally.
    """
    warnings: list[str] = []
    errors: list[str] = []

    print(
        "Translation request received with options: "
        f"optimize={optimize}, include_comments={include_comments}, mimic_defaults={mimic_defaults}. "
        f"LLM model: {LLM_MODEL}, API URL: {API_URL}",
        flush=True
    )
    
    # Second prompt with the actual translation request
    user_prompt_parts = [
        "Now, translate the following EVM code. There is no limit to how long the output can be. IMPORTANT: Only provide the resulting Ralph code WITHOUT \"```ralph\" markdown or any other information. "
        f"Optimize: {optimize}. "
        f"Include comments: {include_comments}. "
        f"Mimic Solidity defaults when loading from map key that does not exist: {mimic_defaults}.",
        f"\n--- EVM Code to Translate ---\n{source_code}\n--- End EVM Code ---",
        "\n--- Translated Ralph Code ---"
    ]
    
    user_prompt = "\n".join(user_prompt_parts)

    # Set up OpenAI client for DeepInfra endpoint
    client = openai.AsyncOpenAI(
        api_key=API_KEY,
        base_url=API_URL.replace("/chat/completions", "")
    )

    # Define common parameters for API calls
    common_parameters = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 32000,
        "temperature": 0.0
    }

    try:
        if stream:
            response = await client.chat.completions.create(
                **common_parameters,
                stream=True
            )
            async for chunk in response:
                content = getattr(chunk.choices[0].delta, "content", "")
                reasoning = getattr(chunk.choices[0].delta, "reasoning", "")
                if content or reasoning:
                    yield content, reasoning, warnings, errors
        else:
            response = await client.chat.completions.create(
                **common_parameters,
                stream=False
            )
            translated_code = response.choices[0].message.content
            reasoning = response.choices[0].message.reasoning if hasattr(response.choices[0].message, 'reasoning') else ""
            yield translated_code, reasoning, warnings, errors
    except Exception as e:
        raise RuntimeError(f"OpenAI/DeepInfra API request failed: {str(e)}") from e
