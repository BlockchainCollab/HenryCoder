import pytest

# Import the parser from the agent module. The test runner's working dir
# (backend/) makes `agent_service` importable as a top-level module.
from agent_service import parse_import_line


@pytest.mark.parametrize(
    "line,expected",
    [
        ('import "@openzeppelin/contracts/token/ERC20/ERC20.sol";', "@openzeppelin/contracts/token/ERC20/ERC20.sol"),
        ("import '@openzeppelin/contracts/access/Ownable.sol';", "@openzeppelin/contracts/access/Ownable.sol"),
        (
            'import {SignatureChecker} from "@openzeppelin/contracts/utils/cryptography/SignatureChecker.sol";',
            "@openzeppelin/contracts/utils/cryptography/SignatureChecker.sol",
        ),
        (
            "import {SignatureChecker} from '@openzeppelin/contracts/utils/cryptography/SignatureChecker.sol';",
            "@openzeppelin/contracts/utils/cryptography/SignatureChecker.sol",
        ),
        (
            'import * as OZ from "@openzeppelin/contracts/utils/SafeMath.sol";',
            "@openzeppelin/contracts/utils/SafeMath.sol",
        ),
        ('import "hardhat/console.sol";', "hardhat/console.sol"),
        (
            '  import   "@openzeppelin/contracts/token/ERC20/ERC20.sol"  ;  ',
            "@openzeppelin/contracts/token/ERC20/ERC20.sol",
        ),
        ("not an import", ""),
        ("", ""),
        ('// import "@openzeppelin/contracts/token/ERC20/ERC20.sol";', ""),
        ('import "@openzeppelin/contracts/utils/SafeMath.sol" ;', "@openzeppelin/contracts/utils/SafeMath.sol"),
    ],
)
def test_parse_import_line_cases(line, expected):
    """Basic parametrized tests for parse_import_line."""
    assert parse_import_line(line) == expected


def test_extract_imports_from_block():
    code = """
// SPDX-License-Identifier: MIT
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import { SafeMath, SafeAdd } from "@openzeppelin/contracts/utils/SafeMath.sol";
import {Unauthorized, add as func, Point} from "./Foo.sol";

contract MyContract {}
"""
    lines = code.split("\n")
    imports = [parse_import_line(l) for l in lines]
    imports = [i for i in imports if i]

    assert len(imports) == 3
    assert "@openzeppelin/contracts/token/ERC20/ERC20.sol" in imports
    assert "@openzeppelin/contracts/utils/SafeMath.sol" in imports
    assert "./Foo.sol" in imports
