import logging
import os
import time
from typing import AsyncGenerator

import openai
from dotenv import load_dotenv

from api_types import TranslateRequest
from templates import LOG_TEMPLATE, UPGRADE_TEMPLATE, get_user_prompt
from translation_context import EXAMPLE_TRANSLATIONS, RALPH_DETAILS

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.getenv("LLM_MODEL")
SMART_LLM_MODEL = os.getenv("SMART_LLM_MODEL")
TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), "translations")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "documentation")
DUMP_DIR = os.path.join(os.path.dirname(__file__), "dumps")
MAX_DUMP_LENGTH = 100000

if API_KEY is None or API_URL is None or LLM_MODEL is None or SMART_LLM_MODEL is None:
    raise RuntimeError("API_KEY, API_URL, LLM_MODEL and SMART_LLM_MODEL must be set in the environment variables.")

def build_translation_system_prompt() -> str:
    """
    Builds the system prompt for translation based on provided options.
    
    Args:
        optimize: Whether to apply performance optimizations
        include_comments: Whether to include explanatory comments
        mimic_defaults: Whether to mimic Solidity defaults for map access
        smart: Whether to use smart/advanced translation mode
        translate_erc20: Whether to translate ERC20 to native Alephium tokens
    
    Returns:
        The complete system prompt string
    """
    base_prompt = (
        "You are an expert EVM to Ralph translator. "
        "Translate the user provided EVM (Solidity) code to Ralph, adhering to the Ralph language specifications and best practices.\n\n"
        "TRANSLATION GUIDELINES:\n"
        "1. Output clean, production-ready Ralph code without instructional comments\n"
        "2. For Solidity interfaces: Convert to Ralph Interfaces\n"
        "3. For Solidity contracts: Provide complete, working Ralph contract implementations\n"
        "4. Include only business logic comments, NOT syntax explanation comments\n"
        "5. Use proper Ralph annotations (@using) where needed\n"
        "6. Handle errors with assert! and integer error codes\n"
        "7. Every translated function can include an additional comment explaining the differences in behavior between Solidity and Ralph, if present. These comments must be one line long and start with '// @@@'.\n"
        "   Example: // @@@ Solidity allows dynamic array parameters, but Ralph only supports fixed-size arrays.\n\n"
        "8. Annotate every translated feature that is redundant in Ralph with @@@ comment, ex. ReentrancyGuard\n"
        "AVOID:\n"
        # "- Comments like 'Ralph doesn't have X, so we use Y'\n"
        # "- Explaining basic syntax differences in comments\n"
        "- Tutorial-style comments\n"
        "- Verbose explanations of language features\n\n"
        # "- Instructional comments about type mappings\n\n"
        "EXPECTED OUTPUT:\n"
        "Just the translated Ralph code with minimal, relevant comments.\n"
        "The code should be ready to use without requiring the user to understand the translation process.\n\n"
        "Ralph Language Details:\n"
        f"{RALPH_DETAILS}\n\n"
        # "Example Translations:\n"
        # f"{EXAMPLE_TRANSLATIONS}"
    )
    
    return base_prompt


def build_fim_system_prompt() -> str:
    """
    Builds the system prompt for FIM (Fill-In-the-Middle) function translation.
    """
    return (
        "You are an expert Ralph smart contract developer.\n"
        "TASK: Implement the functions/methods for a specific Ralph contract or interface.\n"
        "INPUTS:\n"
        "1. Original Solidity Code (Reference Logic)\n"
        "2. Partial Ralph Code (Context & Structure) containing a <|fim_start|> ... <|fim_end|> block.\n"
        "INSTRUCTIONS:\n"
        "1. Generate valid Ralph code to fill the gap between <|fim_start|> and <|fim_end|>.\n"
        "2. Output ONLY the code inside the block. Do NOT include the tags or surrounding code.\n"
        "3. Accurately translate the logic from the Solidity source, respecting Ralph's UTXO model.\n"
        "4. Use the fields, maps, events, and constants defined in the Partial Ralph Code.\n"
        "5. For contracts: Implement public functions, private functions, and getters.\n"
        "6. For interfaces: Define the public method signatures.\n"
        "7. Include brief comments explaining complex translations only.\n"
        "8. Do NOT duplicate methods found in parent contracts.\n"
        "9. Every translated function can include an additional comment explaining the differences in behavior between Solidity and Ralph, if present. These comments must be one line long and start with '@@@'.\n"
        "   Example: @@@ Solidity allows dynamic array parameters, but Ralph only supports fixed-size arrays.\n\n"
        "10. Use curly braces syntax when calling functions (even when calling own functions) that have preapprovedAssets annotation\n\n"
        f"Ralph Language Details:\n\n{RALPH_DETAILS}"
    )


# Keep original SYSTEM_PROMPT for backwards compatibility
SYSTEM_PROMPT = build_translation_system_prompt()


def preprocess_source_code(source_code: str) -> str:
    """
    Preprocesses the source code before translation.
    Currently a placeholder for any future preprocessing steps.
    """

    return source_code


async def perform_fim_translation(
    solidity_code: str,
    ralph_code: str,
    smart: bool = True
) -> AsyncGenerator[tuple[str, str, list[str], list[str]], None]:
    """
    Performs FIM translation to fill in functions.
    Yields chunks: (content, reasoning, warnings, errors)
    """
    warnings: list[str] = []
    errors: list[str] = []
    
    # We use the smart model for coding tasks usually
    model = SMART_LLM_MODEL if smart else LLM_MODEL

    system_prompt = build_fim_system_prompt()
    
    user_prompt = (
        "Here is the context for the translation:\n\n"
        "=== ORIGINAL SOLIDITY CODE ===\n"
        f"{solidity_code}\n\n"
        "=== PARTIAL RALPH CODE (TARGET) ===\n"
        f"{ralph_code}\n\n"
        "Please generate the code to fill the <|fim_start|> ... <|fim_end|> block."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Convert to API format
    input_messages = []
    for msg in messages:
        input_messages.append({
            "type": "message",
            "role": msg["role"],
            "content": msg["content"]
        })

    try:
        async with openai.AsyncOpenAI(
            api_key=API_KEY, 
            base_url=API_URL.replace("/chat/completions", "")
        ) as client:
            temp = 1.0 if "gemini" in model else 0.2
            
            response = await client.responses.create(
                model=model,
                input=input_messages,
                max_output_tokens=20000,
                temperature=temp,
                stream=True
            )
            
            async for event in response:
                content = ""
                reasoning = ""

                if event.type == "response.output_text.delta":
                    content = event.delta
                elif event.type == "response.reasoning_text.delta":
                    reasoning = event.delta
                
                if content or reasoning:
                    yield content, reasoning, warnings, errors
                    
    except Exception as e:
        # Fallback handling or re-raise
        raise RuntimeError(f"FIM Translation failed: {str(e)}") from e


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

    # Check for import markers and split if they exist
    resolved_imports = ""
    code = source_code
    if "/* IMPORTS_START */" in source_code and "/* IMPORTS_END */" in source_code:
        resolved_imports, code = source_code.split("/* IMPORTS_START */\n")[1].split("/* IMPORTS_END */")

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
        source_code=code,
    )

    # Build system prompt with options
    system_prompt = build_translation_system_prompt()
    imports_prompt = f"// INCLUDED PRE-TRANSLATED LIBRARIES: \n{resolved_imports}\n\n// END OF INCLUDED PRE-TRANSLATED LIBRARIES - this code is freely available in the global scope, do not duplicate it\n"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": imports_prompt},
        {"role": "user", "content": user_prompt}
    ]

    if previous:
        messages.append({"role": "assistant", "content": previous.source_code})
        messages.append(
            {"role": "user", "content": UPGRADE_TEMPLATE.format(previous_errors="\n\n".join(previous.errors))}
        )

    # Convert messages to OpenRouter Responses API input format
    input_messages = []
    for msg in messages:
        input_messages.append({
            "type": "message",
            "role": msg["role"],
            "content": msg["content"]
        })

    try:
        async with openai.AsyncOpenAI(
            api_key=API_KEY, 
            base_url=API_URL.replace("/chat/completions", "")
        ) as client:
            if not stream:
                raise RuntimeError("Non-streaming mode is not supported anymore.")
            if resolved_imports:
                yield resolved_imports + "\n", "", warnings, errors
            
            temp = 1.0 if "gemini" in model else 0.2

            response = await client.responses.create(
                model=model,
                input=input_messages,
                max_output_tokens=25000 if translate_request.options.smart else 40000,
                temperature=temp,
                stream=True
            )
            
            async for event in response:
                content = ""
                reasoning = ""

                if event.type == "response.output_text.delta":
                    content = event.delta
                elif event.type == "response.reasoning_text.delta":
                    reasoning = event.delta
                
                if content or reasoning:
                    yield content, reasoning, warnings, errors

    except Exception as e:
        raise RuntimeError(f"OpenRouter Responses API request failed: {str(e)}") from e


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
