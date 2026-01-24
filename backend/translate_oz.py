import logging
import os

OZ_DIR = os.path.join(os.path.dirname(__file__), "openzeppelin")

logger = logging.getLogger(__name__)

# Dict of OpenZeppelin imports to be ignored during translation, mapped to their replacement comments.
IGNORED_IMPORTS: dict[str, str] = {
    "@openzeppelin/contracts/utils/Context.sol": "// @@@ Ralph uses built-in functions to fetch transaction data.",
    "@openzeppelin/contracts/utils/Multicall.sol": "// @@@ Ralph deals with multiple calls via TX Scripts and chained calls.",
    "@openzeppelin/contracts/utils/ReentrancyGuard.sol": "// @@@ Alephium VM blocks reentrancy on protocol level.",
    "@openzeppelin/contracts/utils/introspection/ERC165.sol": "// @@@ Ralph can't perform low level calls.",
    "@openzeppelin/contracts/utils/introspection/IERC165.sol": "// @@@ Ralph can't perform low level calls.",
    # ERC20 Extensions wchich are not applicable in Ralph's native token model
    "@openzeppelin/contracts/token/ERC20/extensions/IERC20Permit.sol": "// @@@ Ralph uses per-transaction approvals via brace syntax {owner -> tokenId: amount}, eliminating the need for signature-based approvals.",
    "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol": "// @@@ Ralph uses per-transaction approvals via brace syntax, making gasless approval signatures unnecessary.",
    "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol": "// @@@ Ralph's UTXO model stores balances in UTXOs, not contract storage, making historical balance/voting power tracking impossible.",
    "@openzeppelin/contracts/token/ERC20/extensions/ERC20Wrapper.sol": "// @@@ Alephium tokens are native UTXOs and cannot be wrapped in the ERC20 sense. Use vault/escrow patterns instead.",
    "@openzeppelin/contracts/token/ERC20/extensions/ERC20FlashMint.sol": "// @@@ Ralph cannot mint and burn tokens atomically within a single transaction.",
    "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol": "// @@@ ERC4626 (Tokenized Vault) is omitted because it requires contract-managed balances. Ralph's native tokens are UTXOs, not contract storage.",
    "@openzeppelin/contracts/token/ERC20/extensions/ERC1363.sol": "// @@@ Ralph token transfers are native operations without callback mechanisms.",
    "@openzeppelin/contracts/token/ERC20/extensions/ERC20Crosschain.sol": "// @@@ Alephium has native cross-group sharding. Bridging requires Alephium-specific implementation.",
    "@openzeppelin/contracts/token/ERC20/extensions/draft-ERC20Bridgeable.sol": "// @@@ Alephium has native cross-group sharding. Bridging requires Alephium-specific implementation.",
    "@openzeppelin/contracts/token/ERC20/extensions/draft-ERC20TemporaryApproval.sol": "// @@@ Ralph approvals are already temporary by design - per-transaction via brace syntax.",
    "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol": "// @@@ Ralph's IFungibleToken interface already includes getSymbol(), getName(), getDecimals(), and getTotalSupply() out of the box.",
    "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol": "// @@@ Alephium doesn't allow pausing token transfers; transfers occur at the native layer.",
    "@openzeppelin/contracts/token/ERC20/extensions/ERC20Capped.sol": "// @@@ Contract deployer creates a fixed supply in the contract UTXO at deployment, so ERC20Capped behavior is represented by the deployment UTXO rather than runtime cap checks.",
    # ERC721 Extensions which are not applicable or have limited applicability in Ralph's NFT model
    "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol": "// @@@ Ralph token transfers are native UTXO operations without callback mechanisms. No receiver interface needed.",
    "@openzeppelin/contracts/token/ERC721/extensions/ERC721Pausable.sol": "// @@@ Alephium doesn't allow pausing native token transfers; NFT transfers occur at the UTXO layer.",
    "@openzeppelin/contracts/token/ERC721/extensions/ERC721Votes.sol": "// @@@ Ralph's UTXO model stores NFT ownership in UTXOs, not contract storage, making historical voting power tracking impossible.",
    "@openzeppelin/contracts/token/ERC721/extensions/ERC721Wrapper.sol": "// @@@ Alephium NFTs are native sub-contracts and cannot be wrapped in the ERC721 sense. Use vault/escrow patterns instead.",
    "@openzeppelin/contracts/token/ERC721/extensions/ERC721Consecutive.sol": "// @@@ Ralph's sub-contract model already uses consecutive indices. Batch minting creates multiple sub-contracts requiring ALPH deposits.",
    "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol": "// @@@ Ralph's INFTCollection interface already provides totalSupply() and nftByIndex(). Owner-level enumeration (tokenOfOwnerByIndex) requires off-chain indexing.",
    "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol": "// @@@ Ralph's INFTCollection interface provides totalSupply() and nftByIndex(). Owner-level enumeration requires off-chain indexing.",
    "@openzeppelin/contracts/token/ERC721/extensions/IERC721Metadata.sol": "// @@@ Ralph's INFT interface includes getTokenUri(). Collection name/symbol are stored on the collection contract.",
    "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol": "// @@@ Ralph's NFT sub-contracts store tokenUri directly. This is supported out of the box via NFTCollectionBase and INFT.getTokenUri().",
    "@openzeppelin/contracts/token/ERC721/utils/ERC721Holder.sol": "// @@@ Ralph contracts receive tokens explicitly via functions with assetsInContract annotation, not receiver callbacks.",
    "@openzeppelin/contracts/token/ERC721/utils/ERC721Utils.sol": "// @@@ Ralph's native token model doesn't use receiver callbacks. Transfers are atomic UTXO operations.",
}


def load_replacement_libs() -> dict[str, str]:
    """Load replacement text from files present under `documentation/openzeppelin`

    Each file corresponds 1:1 to its solidity import path,
    ex. import '@openzeppelin/contracts/utils/Ownable.sol' is located under `documentation/openzeppelin/contracts/utils/Ownable.ral`
    Here we load all translated files to a dict so they are readily accessible.
    """
    replacement_libs: dict[str, str] = {}

    for root, _, files in os.walk(OZ_DIR):
        for file in files:
            if file.endswith(".ral"):
                file_path = os.path.join(root, file)
                import_path = file_path.replace(OZ_DIR + os.sep, "").replace(os.sep, "/").replace(".ral", ".sol")
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
    # dict to deduplicate imports and cover special cases
    replacements: dict[str, str] = {}
    
    for imp in imports:
        # Normalize relative imports to absolute paths
        if ("openzeppelin" in imp) and not imp.startswith("@openzeppelin"):
            imp = "@openzeppelin/" + imp.split("openzeppelin/")[1]

        # If the path is ignored we will provide a short information in this format:
        #   // @@@ Ralph handles X in a different manner than solidity
        #   // [name.sol] is omitted
        if ignored := IGNORED_IMPORTS.get(imp):
            sol_name = imp.split("/")[-1]
            ignored += f"\n// {sol_name} is omitted"
            replacements[imp] = ignored
        elif replacementLib := REPLACEMENT_LIBS.get(imp):
            replacements[imp] = replacementLib
        else:
            replacements[imp] = f"// {imp} is not available"

    def find_interface_lib(lib_path: str) -> None | str:
        """Return path to a related interface library. (The path may not exist)"""
        src = lib_path.split("/")
        if src[-1].startswith("I"):
            return None # already an interface
        return "/".join(src[:-1] + ["I" + src[-1]])

    for key in list(replacements.keys()):
        interface_lib = find_interface_lib(key)
        if interface_lib and interface_lib not in replacements:
            if interface_content := REPLACEMENT_LIBS.get(interface_lib):
                replacements[interface_lib] = interface_content

    return "\n\n".join(replacements.values())

### Agentic system overhauled imports

def get_pretranslated_libs() -> dict[str, str]:
    """Return a dict of available OpenZeppelin imports and generic class names and their replacement text for agentic model.
    
    The keys are simply class names in lowercase (ex. 'ownable') and the values are the replacement text or ignore text.
    """
    res: dict[str, str] = {}

    for lib, explanation in IGNORED_IMPORTS.items():
        class_name = lib.split("/")[-1].replace(".sol", "")
        comment = f"// {class_name} is not needed in Ralph."
        res[class_name.lower()] = explanation + "\n" + comment

    for lib, content in REPLACEMENT_LIBS.items():
        class_name = lib.split("/")[-1].replace(".sol", "")
        res[class_name.lower()] = content

    return res

# Preload the pretranslated libs for use in agent_service (keys are class/interface names in lowercase)"""
PRETRANSLATED_LIBS = get_pretranslated_libs()
