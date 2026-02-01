#!/usr/bin/env python3
"""
Quick verification script for concerto_tools.

This script can be run directly without pytest to verify
the concerto CLI wrapper is working correctly.

Usage:
    python3 scripts/verify_tools.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.concerto_tools import (
    parse_cto_file,
    parse_cto_string,
    validate_cto_file,
    validate_cto_string,
    validate_model,
    ValidationStatus,
)

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def test_parse_valid_model():
    """Test parsing a valid model."""
    print("Testing: parse_cto_file (valid model)...", end=" ")
    result = parse_cto_file(EXAMPLES_DIR / "valid_model.cto")
    
    if result.success and result.ast:
        print("✅ PASS")
        return True
    else:
        print(f"❌ FAIL: {result.error_message}")
        return False


def test_parse_syntax_error():
    """Test parsing a model with syntax error."""
    print("Testing: parse_cto_file (syntax error)...", end=" ")
    result = parse_cto_file(EXAMPLES_DIR / "invalid_model_syntax.cto")
    
    if not result.success and result.error_message:
        print("✅ PASS (correctly detected error)")
        return True
    else:
        print("❌ FAIL: Should have detected syntax error")
        return False


def test_validate_valid_model():
    """Test validating a valid model."""
    print("Testing: validate_cto_file (valid model)...", end=" ")
    result = validate_cto_file(EXAMPLES_DIR / "valid_model.cto")
    
    if result.is_valid and result.status == ValidationStatus.SUCCESS:
        print("✅ PASS")
        return True
    else:
        print(f"❌ FAIL: {result.error_message}")
        return False


def test_validate_type_error():
    """Test validating a model with undefined type."""
    print("Testing: validate_cto_file (type error)...", end=" ")
    result = validate_cto_file(EXAMPLES_DIR / "invalid_model_type.cto")
    
    if not result.is_valid and result.status == ValidationStatus.TYPE_ERROR:
        print("✅ PASS (correctly detected type error)")
        return True
    else:
        print(f"❌ FAIL: Expected TYPE_ERROR, got {result.status}")
        return False


def test_validate_string():
    """Test validating CTO content as a string."""
    print("Testing: validate_cto_string...", end=" ")
    
    cto_content = """
    namespace org.test.quick@1.0.0
    
    concept QuickTest {
        o String name
        o Integer count optional
    }
    """
    result = validate_cto_string(cto_content)
    
    if result.is_valid:
        print("✅ PASS")
        return True
    else:
        print(f"❌ FAIL: {result.error_message}")
        return False


def test_validate_model_dict():
    """Test high-level validate_model function."""
    print("Testing: validate_model (dict output)...", end=" ")
    
    cto_content = """
    namespace org.test.dict@1.0.0
    
    concept DictTest {
        o String value
    }
    """
    result = validate_model(cto_content)
    
    expected_keys = {"valid", "status", "error", "details", "suggestion"}
    if isinstance(result, dict) and expected_keys.issubset(result.keys()):
        if result["valid"]:
            print("✅ PASS")
            return True
        else:
            print(f"❌ FAIL: {result}")
            return False
    else:
        print(f"❌ FAIL: Missing keys in result: {result}")
        return False


def test_validate_model_with_error():
    """Test validate_model with an error case."""
    print("Testing: validate_model (with suggestion)...", end=" ")
    
    cto_content = """
    namespace org.test.bad@1.0.0
    
    concept BadTest {
        o UnknownType value
    }
    """
    result = validate_model(cto_content)
    
    if not result["valid"] and result["suggestion"]:
        print("✅ PASS (suggestion provided)")
        print(f"   └── Suggestion: {result['suggestion']}")
        return True
    else:
        print(f"❌ FAIL: Expected error with suggestion, got {result}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Concerto Tools Verification")
    print("=" * 60)
    print()
    
    tests = [
        test_parse_valid_model,
        test_parse_syntax_error,
        test_validate_valid_model,
        test_validate_type_error,
        test_validate_string,
        test_validate_model_dict,
        test_validate_model_with_error,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ FAIL: Exception - {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
