USER_PROMPT_TEMPLATE = (
    'Now, translate the following EVM code. There is no limit to how long the output can be. IMPORTANT: Only provide the resulting Ralph code WITHOUT "```ralph" markdown or any other information. '
    "Optimize: {optimize}. "
    "Include comments: {include_comments}. "
    "Mimic Solidity defaults when loading from map key that does not exist: {mimic_defaults}."
    "\n--- EVM Code to Translate ---\n{source_code}\n--- End EVM Code ---"
)

LOG_TEMPLATE = (
    "Translation request received with options: "
    "optimize={optimize}, include_comments={include_comments}, mimic_defaults={mimic_defaults}. "
    "LLM model: {llm_model}, API URL: {api_url}"
)
