import logging
import os
import time
from typing import AsyncGenerator
import openai
from dotenv import load_dotenv
from api_types import TranslateRequest
from translation_context import RALPH_DETAILS, EXAMPLE_TRANSLATIONS
from templates import USER_PROMPT_TEMPLATE, LOG_TEMPLATE

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), "translations")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "documentation")
DUMP_DIR = os.path.join(os.path.dirname(__file__), "dumps")
MAX_DUMP_LENGTH = 100000

if API_KEY is None or API_URL is None or LLM_MODEL is None:
    raise RuntimeError(
        "API_KEY, API_URL, and LLM_MODEL must be set in the environment variables."
    )

SYSTEM_PROMPT = (
    "You are an expert EVM to Ralph translator."
    "Translate the following EVM (Solidity) code to Ralph, adhering to the Ralph language specifications and best practices."
    "Consider the following details about the Ralph language:"
    f"{RALPH_DETAILS}"
    "\nHere are some examples of EVM to Ralph translations:"
    f"{EXAMPLE_TRANSLATIONS}"
)


async def perform_translation(
    translate_request: TranslateRequest,
    stream: bool
) -> AsyncGenerator[tuple[str, str, list[str], list[str]], None]:
    """
    Performs the translation using OpenAI-compatible API via the OpenAI Python client.
    If `stream` is True, yields translation chunks incrementally.
    """
    warnings: list[str] = []
    errors: list[str] = []
    optimize = translate_request.options.optimize
    include_comments = translate_request.options.include_comments
    mimic_defaults = translate_request.options.mimic_defaults
    source_code = translate_request.source_code
    previous = translate_request.previous_translation

    print(
        LOG_TEMPLATE.format(
            optimize=optimize,
            include_comments=include_comments,
            mimic_defaults=mimic_defaults,
            llm_model=LLM_MODEL,
            api_url=API_URL,
        ),
        flush=True,
    )

    user_prompt = USER_PROMPT_TEMPLATE.format(
        optimize=optimize,
        include_comments=include_comments,
        mimic_defaults=mimic_defaults,
        source_code=source_code,
    )

    client = openai.AsyncOpenAI(
        api_key=API_KEY, base_url=API_URL.replace("/chat/completions", "")
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    if previous:
        messages.append(
            {
                "role": "assistant",
                "content": previous.source_code
            }
        )
        messages.append(
            {
                "role": "user",
                "content": (
                    f"The code produced the following erors: {"\n\n".join(previous.errors)}\n\n"
                    "Fix the translation. Only return the corrected code without any additional text."
                )
            }
        )

    common_parameters = {
        "model": LLM_MODEL,
        "messages": messages,
        "max_tokens": 32000,
        "temperature": 0.0,
    }

    try:
        if stream:
            response = await client.chat.completions.create(
                **common_parameters, stream=True
            )
            async for chunk in response:
                content = getattr(chunk.choices[0].delta, "content", "")
                reasoning = getattr(chunk.choices[0].delta, "reasoning", "")
                if content or reasoning:
                    yield content, reasoning, warnings, errors
        else:
            response = await client.chat.completions.create(
                **common_parameters, stream=False
            )
            translated_code = response.choices[0].message.content
            reasoning = (
                response.choices[0].message.reasoning
                if hasattr(response.choices[0].message, "reasoning")
                else ""
            )
            yield translated_code, reasoning, warnings, errors
    except Exception as e:
        raise RuntimeError(f"OpenAI/DeepInfra API request failed: {str(e)}") from e


def dump_translation(request: TranslateRequest, translated_code: str) -> None:
    """
    Dumps the translation details to a file.
    """
    sep = "-" * 10  # section separator
    content = (
        f"{sep} Options: {sep}\n{request.options.model_dump_json(indent=2)}\n"
        f"{sep} Source Code: {sep}\n{request.source_code}\n"
        f"{sep} Translated Code: {sep}\n{translated_code}\n"
    )
    if len(content) > MAX_DUMP_LENGTH:
        content = content[:MAX_DUMP_LENGTH] + "\n\n[Content truncated due to size limit]"

    try:
        os.makedirs(DUMP_DIR, exist_ok=True)
        nanosecond_timestamp = time.time_ns()
        dump_file = os.path.join(DUMP_DIR, f"translation_{nanosecond_timestamp}.txt")
        with open(dump_file, "x", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        logging.error(f"Failed to dump translation: {e}")
