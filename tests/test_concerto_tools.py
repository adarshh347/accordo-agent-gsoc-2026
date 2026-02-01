"""
Tests for concerto_tools module.

Tests the Python wrapper around concerto-cli for parsing
and validating Concerto (.cto) models.
"""

import pytest
from pathlib import Path

from src.tools.concerto_tools import (
    parse_cto_file,
    parse_cto_string,
    validate_cto_file,
    validate_cto_string,
    validate_model,
    ValidationStatus,
)


# Test fixtures - paths to example files
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
VALID_MODEL = EXAMPLES_DIR / "valid_model.cto"
INVALID_SYNTAX = EXAMPLES_DIR / "invalid_model_syntax.cto"
INVALID_TYPE = EXAMPLES_DIR / "invalid_model_type.cto"


class TestParseCtoFile:
    """Tests for parse_cto_file function."""
    
    def test_parse_valid_model(self):
        """Should successfully parse a valid .cto file."""
        result = parse_cto_file(VALID_MODEL)
        
        assert result.success is True
        assert result.ast is not None
        assert result.error_message is None
        assert "namespace" in str(result.ast) or "$class" in result.ast
    
    def test_parse_invalid_syntax(self):
        """Should fail to parse a model with syntax errors."""
        result = parse_cto_file(INVALID_SYNTAX)
        
        assert result.success is False
        assert result.error_message is not None
        assert "expected" in result.error_message.lower() or "error" in result.error_message.lower()
    
    def test_parse_nonexistent_file(self):
        """Should return error for non-existent file."""
        result = parse_cto_file("/nonexistent/path.cto")
        
        assert result.success is False
        assert "not found" in result.error_message.lower()


class TestParseCtoString:
    """Tests for parse_cto_string function."""
    
    def test_parse_valid_string(self):
        """Should successfully parse valid CTO content."""
        cto_content = """
        namespace org.test@1.0.0
        
        concept TestConcept {
            o String name
        }
        """
        result = parse_cto_string(cto_content)
        
        assert result.success is True
        assert result.ast is not None
    
    def test_parse_invalid_string(self):
        """Should fail to parse invalid CTO content."""
        cto_content = """
        namespace org.broken@1.0.0
        
        concept Broken {
            o String name
        """  # Missing closing brace
        result = parse_cto_string(cto_content)
        
        assert result.success is False
        assert result.error_message is not None


class TestValidateCtoFile:
    """Tests for validate_cto_file function."""
    
    def test_validate_valid_model(self):
        """Should validate a correct .cto file successfully."""
        result = validate_cto_file(VALID_MODEL)
        
        assert result.is_valid is True
        assert result.status == ValidationStatus.SUCCESS
        assert result.error_message is None
    
    def test_validate_syntax_error(self):
        """Should detect syntax errors."""
        result = validate_cto_file(INVALID_SYNTAX)
        
        assert result.is_valid is False
        assert result.status == ValidationStatus.SYNTAX_ERROR
        assert result.error_message is not None
    
    def test_validate_type_error(self):
        """Should detect type errors (undefined types)."""
        result = validate_cto_file(INVALID_TYPE)
        
        assert result.is_valid is False
        assert result.status == ValidationStatus.TYPE_ERROR
        assert "FakeType" in result.error_message or "undeclared" in result.error_message.lower()


class TestValidateCtoString:
    """Tests for validate_cto_string function."""
    
    def test_validate_valid_string(self):
        """Should validate correct CTO content."""
        cto_content = """
        namespace org.test@1.0.0
        
        concept TestConcept {
            o String name
            o Integer count optional
        }
        """
        result = validate_cto_string(cto_content)
        
        assert result.is_valid is True
        assert result.status == ValidationStatus.SUCCESS
    
    def test_validate_syntax_error_string(self):
        """Should detect syntax errors in string content."""
        cto_content = """
        namespace org.broken@1.0.0
        
        concept {  // Missing concept name
            o String name
        }
        """
        result = validate_cto_string(cto_content)
        
        assert result.is_valid is False


class TestValidateModel:
    """Tests for the high-level validate_model function."""
    
    def test_validate_model_returns_dict(self):
        """Should return a dictionary with expected keys."""
        cto_content = """
        namespace org.test@1.0.0
        
        concept ValidConcept {
            o String name
        }
        """
        result = validate_model(cto_content)
        
        assert isinstance(result, dict)
        assert "valid" in result
        assert "status" in result
        assert "error" in result
        assert "details" in result
        assert "suggestion" in result
    
    def test_validate_model_valid(self):
        """Should return valid=True for valid content."""
        cto_content = """
        namespace org.test@1.0.0
        
        concept ValidConcept {
            o String name
        }
        """
        result = validate_model(cto_content)
        
        assert result["valid"] is True
        assert result["status"] == "success"
        assert result["suggestion"] is None
    
    def test_validate_model_provides_suggestion(self):
        """Should provide a fix suggestion for invalid content."""
        cto_content = """
        namespace org.test@1.0.0
        
        concept BadConcept {
            o UnknownType value
        }
        """
        result = validate_model(cto_content)
        
        assert result["valid"] is False
        assert result["suggestion"] is not None
        assert len(result["suggestion"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
