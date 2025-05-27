import json
import os
from typing import AsyncGenerator
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), "translations")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "documentation")

if not API_KEY or not API_URL or not LLM_MODEL:
    raise RuntimeError("API_KEY, API_URL, and LLM_MODEL must be set in the environment variables.")

def load_ralph_details() -> str:
    """
    Loads and concatenates markdown files in the documentation directory
    in a specific order, followed by any remaining markdown files.
    """
    if not os.path.exists(DOCS_DIR):
        return "Ralph language details not found. Please ensure documentation directory exists."
    
    markdown_content = []
    
    # Define priority order for documentation files
    priority_files = [
        "types.md", 
        "operators.md", 
        "functions.md", 
        "contracts.md", 
        "built-in-functions.md"
    ]
    
    try:
        # First add priority files in specified order
        for filename in priority_files:
            file_path = os.path.join(DOCS_DIR, filename)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    markdown_content.append(f"--- {filename} ---\n{content}")
            else:
                print(f"Warning: {filename} not found in documentation directory.")
        
        # Then add any remaining markdown files
        for filename in sorted(os.listdir(DOCS_DIR)):
            if filename.endswith('.md') and filename not in priority_files:
                file_path = os.path.join(DOCS_DIR, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    markdown_content.append(f"--- {filename} ---\n{content}")
        
        if not markdown_content:
            return "No markdown files found in documentation directory."
            
        return "\n\n".join(markdown_content)
    except Exception as e:
        print(f"Error loading documentation: {e}")
        raise RuntimeError("Failed to load Ralph details") from e

def load_example_translations() -> str:
    """     
    Loads example translations from the translations directory.
    Files are expected to be named in1.sol, out1.sol, in2.sol, out2.sol, etc.
    Returns a concatenated string of all examples with clear separators.
    """
    concat_parts = []
    
    if not os.path.exists(TRANSLATIONS_DIR):
        print(f"Translations directory not found: {TRANSLATIONS_DIR}")
        return ""
    
    i = 1
    while True:
        in_path = os.path.join(TRANSLATIONS_DIR, f"in{i}.sol")
        out_path = os.path.join(TRANSLATIONS_DIR, f"out{i}.ral")
        
        if not (os.path.exists(in_path) and os.path.exists(out_path)):
            break
            
        try:
            with open(in_path, "r", encoding="utf-8") as f_in, open(out_path, "r", encoding="utf-8") as f_out:
                input_content = f_in.read()
                output_content = f_out.read()
                
                # Add to concat parts with clear separators
                concat_parts.append(f"--- Example {i} Input (in{i}.sol) ---\n{input_content}")
                concat_parts.append(f"--- Example {i} Output (out{i}.ral) ---\n{output_content}")
            
            i += 1
        except Exception as e:
            print(f"Error loading example translation pair {i}: {e}")
            raise RuntimeError("Failed to load example translations") from e
    
    if not concat_parts:
        return "No example translations found."
        
    return "\n\n".join(concat_parts)

async def perform_translation(
    source_code: str, optimize: bool, include_comments: bool, mimic_defaults: bool = False, stream: bool = False
) -> AsyncGenerator[tuple[str, list[str], list[str]], None]:
    """
    Performs the translation using OpenAI-compatible API via the OpenAI Python client.
    If `stream` is True, yields translation chunks incrementally.
    """
    warnings: list[str] = []
    errors: list[str] = []

    ralph_details = load_ralph_details()
    example_translations = load_example_translations()

    print(
        "Translation request received with options: "
        f"optimize={optimize}, include_comments={include_comments}, mimic_defaults={mimic_defaults}. "
        f"LLM model: {LLM_MODEL}, API URL: {API_URL}",
        flush=True
    )
    
    # First prompt for caching on deepseek backend
    system_prompt = "\n".join([
        "You are an expert EVM to Ralph translator.",
        "Translate the following EVM (Solidity) code to Ralph, adhering to the Ralph language specifications and best practices.",
        "Consider the following details about the Ralph language:",
        ralph_details,
        "\nHere are some examples of EVM to Ralph translations:",
        example_translations
    ])
    
    # Second prompt with the actual translation request
    user_prompt_parts = [
        "Now, translate the following EVM code. Only provide the resulting Ralph code without \"```ralph\" markdown. "
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
            {"role": "system", "content": system_prompt},
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
                if content:
                    yield content, warnings, errors
        else:
            response = await client.chat.completions.create(
                **common_parameters,
                stream=False
            )
            translated_code = response.choices[0].message.content
            yield translated_code, warnings, errors
    except Exception as e:
        raise RuntimeError(f"OpenAI/DeepInfra API request failed: {str(e)}") from e
