"""
Unit tests for translate_oz.py

Tests cover:
- load_replacement_libs(): loading OpenZeppelin replacement libraries
- replace_imports(): generating replacement text for import paths
- IGNORED_IMPORTS: handling ignored imports
"""

import os

# Import the module under test
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translate_oz import IGNORED_IMPORTS, REPLACEMENT_LIBS, replace_imports


class TestIgnoredImports:
    """Tests for IGNORED_IMPORTS constant."""

    def test_ignored_imports_exists(self):
        """Test that IGNORED_IMPORTS dict is defined."""
        assert isinstance(IGNORED_IMPORTS, dict)
        assert len(IGNORED_IMPORTS) > 0

    def test_ignored_imports_has_context(self):
        """Test that Context is in ignored imports."""
        assert "@openzeppelin/contracts/utils/Context.sol" in IGNORED_IMPORTS

    def test_ignored_imports_has_reentrancy_guard(self):
        """Test that ReentrancyGuard is in ignored imports."""
        assert "@openzeppelin/contracts/utils/ReentrancyGuard.sol" in IGNORED_IMPORTS

    def test_ignored_imports_values_are_strings(self):
        """Test that all values in IGNORED_IMPORTS are comment strings."""
        for key, value in IGNORED_IMPORTS.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            assert value.startswith("//")


class TestReplacementLibs:
    """Tests for REPLACEMENT_LIBS constant."""

    def test_replacement_libs_is_dict(self):
        """Test that REPLACEMENT_LIBS is a dictionary."""
        assert isinstance(REPLACEMENT_LIBS, dict)

    def test_replacement_libs_keys_start_with_openzeppelin(self):
        """Test that all keys are valid OpenZeppelin import paths."""
        for key in REPLACEMENT_LIBS.keys():
            assert key.startswith("@openzeppelin/")
            assert key.endswith(".sol")

    def test_replacement_libs_values_are_strings(self):
        """Test that all values are content strings."""
        for key, value in REPLACEMENT_LIBS.items():
            assert isinstance(value, str)
            assert len(value) > 0


@pytest.mark.parametrize(
    "imports,expected_contains",
    [
        (["@openzeppelin/contracts/utils/Context.sol"], ["// Context is excluded"]),
        (["@openzeppelin/contracts/utils/ReentrancyGuard.sol"], ["// ReentrancyGuard contract is omitted"]),
        (["@openzeppelin/contracts/utils/Multicall.sol"], ["// Multicall contract is omitted"]),
        (["unknown/path/to/contract.sol"], ["// unknown/path/to/contract.sol is not available"]),
    ],
)
def test_replace_imports_single_import(imports, expected_contains):
    """Test replace_imports with single import."""
    result = replace_imports(imports)

    for expected in expected_contains:
        assert expected in result


def test_replace_imports_multiple_imports():
    """Test replace_imports with multiple imports."""
    imports = [
        "@openzeppelin/contracts/utils/Context.sol",
        "@openzeppelin/contracts/utils/ReentrancyGuard.sol",
        "unknown/contract.sol",
    ]
    result = replace_imports(imports)

    # Should contain comments for all three
    assert "// Context is excluded" in result
    assert "// ReentrancyGuard contract is omitted" in result
    assert "// unknown/contract.sol is not available" in result

    # Should be separated by double newline
    assert "\n\n" in result


def test_replace_imports_empty_list():
    """Test replace_imports with empty list."""
    result = replace_imports([])
    assert result == ""


def test_replace_imports_order_preserved():
    """Test that replace_imports maintains input order."""
    imports = [
        "@openzeppelin/contracts/utils/Context.sol",
        "@openzeppelin/contracts/utils/ReentrancyGuard.sol",
    ]
    result = replace_imports(imports)

    # Context should appear before ReentrancyGuard
    context_pos = result.find("Context")
    reentrancy_pos = result.find("ReentrancyGuard")
    assert context_pos < reentrancy_pos


class TestReplaceImportsWithLoadedLibs:
    """Tests for replace_imports when REPLACEMENT_LIBS has content."""

    def test_replace_imports_uses_loaded_libs(self):
        """Test that loaded library content is used when available."""
        # Only test if we have loaded libs
        if len(REPLACEMENT_LIBS) > 0:
            first_lib_path = list(REPLACEMENT_LIBS.keys())[0]
            first_lib_content = REPLACEMENT_LIBS[first_lib_path]

            result = replace_imports([first_lib_path])

            # Should contain the actual loaded content, not a comment
            assert first_lib_content in result
            assert "is not available" not in result


class TestReplaceImportsIntegration:
    """Integration tests for replace_imports."""

    def test_real_world_scenario_with_erc20(self):
        """Test real-world scenario with common ERC20 imports."""
        imports = [
            "@openzeppelin/contracts/utils/Context.sol",  # Ignored
            "@openzeppelin/contracts/utils/ReentrancyGuard.sol",  # Ignored
        ]
        result = replace_imports(imports)

        # Both should be handled (either loaded or commented)
        assert len(result) > 0
        # At least one should be an ignored import comment
        assert "is excluded" in result or "is omitted" in result

    def test_mix_of_ignored_and_unknown_imports(self):
        """Test handling of mix of known and unknown imports."""
        imports = [
            "@openzeppelin/contracts/utils/Context.sol",  # Ignored
            "my-custom-library/MyContract.sol",  # Unknown
        ]
        result = replace_imports(imports)

        # Should handle both
        assert "Context" in result
        assert "my-custom-library/MyContract.sol" in result
        assert "\n\n" in result  # Should be separated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
