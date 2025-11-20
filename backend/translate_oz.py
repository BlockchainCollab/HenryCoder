import logging
import os
from translation_context import DOCS_DIR

logger = logging.getLogger(__name__)

# Dict of OpenZeppelin imports to be ignored during translation, mapped to their replacement comments.
IGNORED_IMPORTS: dict[str, str] = {
  "@openzeppelin/contracts/utils/Context.sol": "// Context is excluded as Ralph has a different convention for each msg data fetch.",
  "@openzeppelin/contracts/utils/Multicall.sol": "// Multicall contract is omitted as Ralph can deal with multiple calls via TX Scripts and chained calls.",
  "@openzeppelin/contracts/utils/ReentrancyGuard.sol": "// ReentrancyGuard contract is omitted as Alephium VM blocks reentrancy on protocol level.",
  "@openzeppelin/contracts/utils/introspection/ERC165.sol": "// ERC165 contract is omitted because Ralph can't perform low level calls.",
  "@openzeppelin/contracts/utils/introspection/IERC165.sol": "// IERC165 interface is omitted because Ralph can't perform low level calls.",
}


def load_replacement_libs() -> dict[str, str]:
  """Load replacement text from files present under `documentation/openzeppelin`
  
  Each file corresponds 1:1 to its solidity import path,
  ex. import '@openzeppelin/contracts/utils/Ownable.sol' is located under `documentation/openzeppelin/contracts/utils/Ownable.ral`
  Here we load all translated files to a dict so they are readily accessible.
  """
  replacement_libs: dict[str, str] = {}

  openzeppelin_dir = os.path.join(DOCS_DIR, "openzeppelin")
  for root, _, files in os.walk(openzeppelin_dir):
    for file in files:
      if file.endswith(".ral"):
        file_path = os.path.join(root, file)
        import_path = file_path.replace(openzeppelin_dir + os.sep, "").replace(os.sep, "/").replace(".ral", ".sol")
        try:
          with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            replacement_libs[f"@openzeppelin/{import_path}"] = content
        except Exception as e:
          logger.error(f"Error loading replacement lib {import_path}: {e}")
          raise RuntimeError("Failed to load replacement libraries") from e
  
  return replacement_libs

REPLACEMENT_LIBS: dict[str, str] = load_replacement_libs()
print(f"Loaded {len(REPLACEMENT_LIBS)} OpenZeppelin replacement libraries.")

def replace_imports(imports: list[str]) -> str:
  """Given a list of solidity import paths, return the concatenated replacement text for those imports.
  
  If an import is in IGNORED_IMPORTS, its comment replacement is used.
  If an import is in REPLACEMENT_LIBS, its loaded content is used.
  Otherwise, "// [IMPORT_PATH] is not available" is used
  """
  replacement_texts = []
  for imp in imports:
    ignored = IGNORED_IMPORTS.get(imp)
    if ignored:
      replacement_texts.append(ignored)
    elif imp in REPLACEMENT_LIBS:
      replacement_texts.append(REPLACEMENT_LIBS[imp])
    else:
      replacement_texts.append(f"// {imp} is not available")
  return "\n\n".join(replacement_texts)
