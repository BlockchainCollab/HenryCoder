import logging
import os
import time
from typing import AsyncGenerator

import openai
from dotenv import load_dotenv

from api_types import TranslateRequest
from templates import LOG_TEMPLATE, UPGRADE_TEMPLATE, get_user_prompt
from translate_oz import replace_imports
from translation_context import EXAMPLE_TRANSLATIONS, RALPH_DETAILS

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
SMART_LLM_MODEL = os.getenv("SMART_LLM_MODEL")
TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), "translations")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "documentation")
DUMP_DIR = os.path.join(os.path.dirname(__file__), "dumps")
MAX_DUMP_LENGTH = 100000

if API_KEY is None or API_URL is None or LLM_MODEL is None or SMART_LLM_MODEL is None:
    raise RuntimeError("API_KEY, API_URL, LLM_MODEL and SMART_LLM_MODEL must be set in the environment variables.")

SYSTEM_PROMPT = (
    "You are an expert EVM to Ralph translator. "
    "Translate the user provided EVM (Solidity) code to Ralph, adhering to the Ralph language specifications and best practices.\n\n"
    "TRANSLATION GUIDELINES:\n"
    "1. Output clean, production-ready Ralph code without instructional comments\n"
    "2. For Solidity interfaces: Convert to Ralph Abstract Contracts or Traits\n"
    "3. For Solidity contracts: Provide complete, working Ralph contract implementations\n"
    "4. Include only business logic comments, NOT syntax explanation comments\n"
    "5. Use proper Ralph annotations (@using) where needed\n"
    "6. Handle errors with assert! and proper error codes\n\n"
    "7. Every translated function must include an additional comment explaining the differences in behavior between Solidity and Ralph, if any. These comments must be one line long and start with '@@@'.\n"
    "   Example: @@@ Solidity allows implicit type conversion, Ralph requires explicit casting.\n\n"
    "AVOID:\n"
    # "- Comments like 'Ralph doesn't have X, so we use Y'\n"
    # "- Explaining basic syntax differences in comments\n"
    "- Tutorial-style comments\n"
    "- Verbose explanations of language features\n"
    "- Instructional comments about type mappings\n\n"
    "EXPECTED OUTPUT:\n"
    "Just the translated Ralph code with minimal, relevant comments.\n"
    "The code should be ready to use without requiring the user to understand the translation process.\n\n"
    "Ralph Language Details:\n"
    f"{RALPH_DETAILS}\n\n"
    "Example Translations:\n"
    f"{EXAMPLE_TRANSLATIONS}"
)


def preprocess_source_code(source_code: str) -> str:
    """
    Preprocesses the source code before translation.
    Currently a placeholder for any future preprocessing steps.
    """

    return source_code


async def perform_translation(
    translate_request: TranslateRequest, stream: bool
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
    translate_erc20 = translate_request.options.translate_erc20
    source_code = translate_request.source_code
    previous = translate_request.previous_translation
    model = SMART_LLM_MODEL if translate_request.options.smart else LLM_MODEL

    print(
        LOG_TEMPLATE.format(
            optimize=optimize,
            include_comments=include_comments,
            mimic_defaults=mimic_defaults,
            translate_erc20=translate_erc20,
            llm_model=model,
            api_url=API_URL,
        ),
        flush=True,
    )

    user_prompt = get_user_prompt(
        optimize=optimize,
        include_comments=include_comments,
        mimic_defaults=mimic_defaults,
        translate_erc20=translate_erc20,
        source_code=source_code,
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}]

    if previous:
        messages.append({"role": "assistant", "content": previous.source_code})
        messages.append(
            {"role": "user", "content": UPGRADE_TEMPLATE.format(previous_errors="\n\n".join(previous.errors))}
        )

    common_parameters = {
        "model": model,
        "messages": messages,
        "max_tokens": 32000,
        "temperature": 0.0,
    }

    try:
        async with openai.AsyncOpenAI(
            api_key=API_KEY, 
            base_url=API_URL.replace("/chat/completions", "")
        ) as client:
            if stream:
                response = await client.chat.completions.create(**common_parameters, stream=True)
                async for chunk in response:
                    content = getattr(chunk.choices[0].delta, "content", "")
                    reasoning = getattr(chunk.choices[0].delta, "reasoning", "")
                    if content or reasoning:
                        yield content, reasoning, warnings, errors
            else:
                response = await client.chat.completions.create(**common_parameters, stream=False)
                translated_code = response.choices[0].message.content
                reasoning = (
                    response.choices[0].message.reasoning if hasattr(response.choices[0].message, "reasoning") else ""
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
