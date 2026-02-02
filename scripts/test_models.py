#!/usr/bin/env python3
"""
Test script for validating the data models and CTO generation.

This script tests the non-LLM parts of the workflow that can run
without an API key.

Usage:
    python3 scripts/test_models.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_field_to_cto():
    """Test FieldDefinition.to_cto_line()"""
    print("Testing: FieldDefinition.to_cto_line()...", end=" ")
    
    from src.models import FieldDefinition
    
    # Required string field
    field1 = FieldDefinition(name="borrowerName", type="String")
    assert field1.to_cto_line() == "  o String borrowerName"
    
    # Optional field
    field2 = FieldDefinition(name="startDate", type="DateTime", optional=True)
    assert field2.to_cto_line() == "  o DateTime startDate optional"
    
    # Array field
    field3 = FieldDefinition(name="tags", type="String", is_array=True)
    assert field3.to_cto_line() == "  o String[] tags"
    
    print("✅ PASS")
    return True


def test_concept_to_cto():
    """Test ConceptDefinition.to_cto()"""
    print("Testing: ConceptDefinition.to_cto()...", end=" ")
    
    from src.models import ConceptDefinition, FieldDefinition
    
    concept = ConceptDefinition(
        name="LoanAgreement",
        fields=[
            FieldDefinition(name="amount", type="Double"),
            FieldDefinition(name="borrower", type="String"),
        ]
    )
    
    cto = concept.to_cto()
    
    assert "concept LoanAgreement {" in cto
    assert "o Double amount" in cto
    assert "o String borrower" in cto
    assert cto.endswith("}")
    
    print("✅ PASS")
    return True


def test_intent_to_cto():
    """Test StructuredIntent.to_cto()"""
    print("Testing: StructuredIntent.to_cto()...", end=" ")
    
    from src.models import StructuredIntent, ConceptDefinition, FieldDefinition
    
    intent = StructuredIntent(
        namespace="org.example.loan",
        version="1.0.0",
        concepts=[
            ConceptDefinition(
                name="LoanAgreement",
                fields=[
                    FieldDefinition(name="amount", type="Double"),
                    FieldDefinition(name="rate", type="Double"),
                ]
            )
        ]
    )
    
    cto = intent.to_cto()
    
    assert cto.startswith("namespace org.example.loan@1.0.0")
    assert "concept LoanAgreement {" in cto
    
    print("✅ PASS")
    return True


def test_intent_validation():
    """Test that generated CTO passes validation"""
    print("Testing: Intent → CTO → Validate...", end=" ")
    
    from src.models import StructuredIntent, ConceptDefinition, FieldDefinition
    from src.tools.concerto_tools import validate_cto_string
    
    intent = StructuredIntent(
        namespace="org.test.validation",
        version="1.0.0",
        concepts=[
            ConceptDefinition(
                name="TestConcept",
                fields=[
                    FieldDefinition(name="name", type="String"),
                    FieldDefinition(name="count", type="Integer"),
                    FieldDefinition(name="rate", type="Double", optional=True),
                ]
            )
        ]
    )
    
    cto = intent.to_cto()
    result = validate_cto_string(cto)
    
    if result.is_valid:
        print("✅ PASS")
        return True
    else:
        print(f"❌ FAIL: {result.error_message}")
        print(f"Generated CTO:\n{cto}")
        return False


def test_prompt_builders():
    """Test prompt builder functions"""
    print("Testing: Prompt builders...", end=" ")
    
    from src.prompts.templates import (
        build_analyst_prompt,
        build_generator_prompt,
        build_fix_prompt,
    )
    
    # Analyst prompt
    sys_prompt, user_prompt = build_analyst_prompt(
        description="Test description",
        additional_context="Extra context"
    )
    assert len(sys_prompt) > 100
    assert "Test description" in user_prompt
    
    # Generator prompt
    sys_prompt, user_prompt = build_generator_prompt('{"test": "data"}')
    assert len(sys_prompt) > 100
    assert "test" in user_prompt
    
    # Fix prompt
    sys_prompt, user_prompt = build_fix_prompt(
        cto_content="namespace test",
        error_message="Test error"
    )
    assert "Test error" in user_prompt
    
    print("✅ PASS")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Data Model & CTO Generation Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_field_to_cto,
        test_concept_to_cto,
        test_intent_to_cto,
        test_intent_validation,
        test_prompt_builders,
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
            print(f"❌ FAIL: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
