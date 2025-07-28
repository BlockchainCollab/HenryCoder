USER_PROMPT_TEMPLATE = (
    "--- EVM Code to Translate ---\n{source_code}\n--- End EVM Code ---\n\n"
    'Now, translate the above EVM code. There is no limit to how long the output can be. IMPORTANT: Only provide the resulting Ralph code WITHOUT "```ralph" markdown or any other information. '
    "Optimize: {optimize}. "
    "Include comments: {include_comments}. "
    "Mimic Solidity defaults when loading from map key that does not exist: {mimic_defaults}. "
    "{translate_erc20}\n"
    "Solidity to Ralph translators often make the following errors:\n"
    "- Using commas \",\" in enums.\n"
    "- Defining state variables inside contract body.\n"
    "- Using an underscore \"_\" in front of a function name.\n"
)

ERC20_NOTICE = "Translate ERC20 transfers and approvals to native Alephium tokens. Translate token addresses to `ByteVec`.  Comment out other calls to IERC20 methods and notice that they are unsupported."

def get_user_prompt(
    optimize: bool,
    include_comments: bool,
    mimic_defaults: bool,
    translate_erc20: bool,
    source_code: str
) -> str:
    """
    Generates the user prompt for translation based on the provided options.
    """
    return USER_PROMPT_TEMPLATE.format(
        optimize=optimize,
        include_comments=include_comments,
        mimic_defaults=mimic_defaults,
        translate_erc20=ERC20_NOTICE if translate_erc20 else "",
        source_code=source_code
    )

LOG_TEMPLATE = (
    "Translation request received with options: "
    "optimize={optimize}, include_comments={include_comments}, mimic_defaults={mimic_defaults}, translate_erc20={translate_erc20}. "
    "LLM model: {llm_model}, API URL: {api_url}"
)

UPGRADE_TEMPLATE = (
    "The code produced the following erors: {previous_errors}\n\n"
    "Solidity to Ralph translators often make the following errors:\n"
    "- Using commas \",\" in enums.\n"
    "- Defining state variables inside contract body.\n"
    "- Using an underscore \"_\" in front of a function name.\n"
    "Fix the translation. Fix the common errors. Only return the corrected code without any additional text."
)