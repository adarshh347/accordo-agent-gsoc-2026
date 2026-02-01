"""
Concerto CLI Tool Wrappers

This module provides Python wrappers around the @accordproject/concerto-cli
for parsing and validating Concerto (.cto) models.

The wrappers execute the CLI as subprocess calls and parse the output
to provide structured results to the agent workflow.
"""

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class ValidationStatus(Enum):
    """Status of a validation operation."""
    SUCCESS = "success"
    SYNTAX_ERROR = "syntax_error"
    TYPE_ERROR = "type_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ValidationResult:
    """Result of validating a Concerto model."""
    status: ValidationStatus
    is_valid: bool
    error_message: Optional[str] = None
    error_line: Optional[int] = None
    error_details: Optional[str] = None
    ast_json: Optional[dict] = None
    
    def __str__(self) -> str:
        if self.is_valid:
            return "✅ Model is valid"
        return f"❌ {self.status.value}: {self.error_message}"


@dataclass 
class ParseResult:
    """Result of parsing a Concerto model to AST."""
    success: bool
    ast: Optional[dict] = None
    error_message: Optional[str] = None


def _get_project_root() -> Path:
    """Get the project root directory (where package.json is located)."""
    # Start from current file and walk up to find package.json
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "package.json").exists():
            return current
        current = current.parent
    # Fallback to current working directory
    return Path.cwd()


def _get_npx_command() -> list[str]:
    """Get the npx command with proper path."""
    return ["npx", "concerto"]


def parse_cto_file(cto_path: str | Path) -> ParseResult:
    """
    Parse a .cto file and return its AST.
    
    Args:
        cto_path: Path to the .cto file
        
    Returns:
        ParseResult with the AST if successful, or error message if failed
    """
    cto_path = Path(cto_path).resolve()
    if not cto_path.exists():
        return ParseResult(
            success=False,
            error_message=f"File not found: {cto_path}"
        )
    
    project_root = _get_project_root()
    cmd = _get_npx_command() + ["parse", "--model", str(cto_path)]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout.strip()
        stderr = result.stderr.strip()
        
        # Check for error in output (concerto outputs errors to stdout sometimes)
        if "error:" in output.lower() or "error:" in stderr.lower():
            error_text = output if "error:" in output.lower() else stderr
            # Extract error message
            error_match = re.search(r'error:\s*(.+)', error_text, re.IGNORECASE)
            error_msg = error_match.group(1) if error_match else error_text
            return ParseResult(
                success=False,
                error_message=error_msg
            )
        
        # Try to parse JSON output
        if output.startswith("{"):
            try:
                ast = json.loads(output)
                return ParseResult(success=True, ast=ast)
            except json.JSONDecodeError:
                pass
        
        # If we get here with no error, consider it success
        if result.returncode == 0 and output:
            try:
                ast = json.loads(output)
                return ParseResult(success=True, ast=ast)
            except json.JSONDecodeError:
                return ParseResult(
                    success=False,
                    error_message=f"Failed to parse CLI output as JSON: {output[:200]}"
                )
        
        return ParseResult(
            success=False,
            error_message=f"Unexpected output: {output[:200] if output else stderr[:200]}"
        )
        
    except subprocess.TimeoutExpired:
        return ParseResult(
            success=False,
            error_message="Command timed out after 30 seconds"
        )
    except Exception as e:
        return ParseResult(
            success=False,
            error_message=f"Error running concerto CLI: {str(e)}"
        )


def parse_cto_string(cto_content: str) -> ParseResult:
    """
    Parse CTO content from a string.
    
    Creates a temporary file and parses it.
    
    Args:
        cto_content: The CTO model content as a string
        
    Returns:
        ParseResult with the AST if successful
    """
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.cto', 
        delete=False
    ) as f:
        f.write(cto_content)
        temp_path = f.name
    
    try:
        return parse_cto_file(temp_path)
    finally:
        os.unlink(temp_path)


def validate_cto_file(cto_path: str | Path) -> ValidationResult:
    """
    Validate a .cto file for both syntax and type correctness.
    
    Uses 'concerto compile' to perform full validation including
    type resolution and semantic checks.
    
    Args:
        cto_path: Path to the .cto file
        
    Returns:
        ValidationResult with status and any error details
    """
    cto_path = Path(cto_path).resolve()
    if not cto_path.exists():
        return ValidationResult(
            status=ValidationStatus.UNKNOWN_ERROR,
            is_valid=False,
            error_message=f"File not found: {cto_path}"
        )
    
    # First, try to parse (catches syntax errors)
    parse_result = parse_cto_file(cto_path)
    if not parse_result.success:
        # Check if it's a syntax error
        return ValidationResult(
            status=ValidationStatus.SYNTAX_ERROR,
            is_valid=False,
            error_message=parse_result.error_message,
            error_details=_extract_error_details(parse_result.error_message)
        )
    
    # Now compile to check for type errors
    project_root = _get_project_root()
    
    # Create temp output dir
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = _get_npx_command() + [
            "compile",
            "--model", str(cto_path),
            "--target", "JSONSchema",
            "--output", temp_dir
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            combined_output = result.stdout + result.stderr
            
            # Check for errors
            if "error:" in combined_output.lower():
                error_match = re.search(
                    r'error:\s*(.+?)(?:\n|$)', 
                    combined_output, 
                    re.IGNORECASE | re.DOTALL
                )
                error_msg = error_match.group(1).strip() if error_match else combined_output
                
                # Determine error type
                if "undeclared type" in error_msg.lower():
                    status = ValidationStatus.TYPE_ERROR
                elif "expected" in error_msg.lower():
                    status = ValidationStatus.SYNTAX_ERROR
                else:
                    status = ValidationStatus.UNKNOWN_ERROR
                
                return ValidationResult(
                    status=status,
                    is_valid=False,
                    error_message=error_msg,
                    error_details=_extract_error_details(error_msg)
                )
            
            # Check for success message
            if "compiled to" in combined_output.lower():
                return ValidationResult(
                    status=ValidationStatus.SUCCESS,
                    is_valid=True,
                    ast_json=parse_result.ast
                )
            
            # If exit code is 0 and no error, assume success
            if result.returncode == 0:
                return ValidationResult(
                    status=ValidationStatus.SUCCESS,
                    is_valid=True,
                    ast_json=parse_result.ast
                )
            
            return ValidationResult(
                status=ValidationStatus.UNKNOWN_ERROR,
                is_valid=False,
                error_message=f"Unexpected result: {combined_output[:200]}"
            )
            
        except subprocess.TimeoutExpired:
            return ValidationResult(
                status=ValidationStatus.UNKNOWN_ERROR,
                is_valid=False,
                error_message="Command timed out after 30 seconds"
            )
        except Exception as e:
            return ValidationResult(
                status=ValidationStatus.UNKNOWN_ERROR,
                is_valid=False,
                error_message=f"Error running concerto CLI: {str(e)}"
            )


def validate_cto_string(cto_content: str) -> ValidationResult:
    """
    Validate CTO content from a string.
    
    Creates a temporary file and validates it.
    
    Args:
        cto_content: The CTO model content as a string
        
    Returns:
        ValidationResult with status and any error details
    """
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.cto',
        delete=False
    ) as f:
        f.write(cto_content)
        temp_path = f.name
    
    try:
        return validate_cto_file(temp_path)
    finally:
        os.unlink(temp_path)


def _extract_error_details(error_message: str | None) -> str | None:
    """Extract actionable details from an error message."""
    if not error_message:
        return None
    
    details = []
    
    # Extract line number if present
    line_match = re.search(r'line\s*(\d+)', error_message, re.IGNORECASE)
    if line_match:
        details.append(f"Error on line {line_match.group(1)}")
    
    # Extract expected tokens
    expected_match = re.search(r'expected\s*(.+?)(?:but|$)', error_message, re.IGNORECASE)
    if expected_match:
        details.append(f"Expected: {expected_match.group(1).strip()}")
    
    # Extract undeclared type
    type_match = re.search(r'undeclared type\s*"([^"]+)"', error_message, re.IGNORECASE)
    if type_match:
        details.append(f"Unknown type: {type_match.group(1)}")
    
    # Extract property info
    prop_match = re.search(r'property\s+([^\s.]+\.[^\s.]+)', error_message)
    if prop_match:
        details.append(f"In property: {prop_match.group(1)}")
    
    return " | ".join(details) if details else None


# Convenience function for the agent workflow
def validate_model(cto_content: str) -> dict:
    """
    High-level validation function for use by agents.
    
    Args:
        cto_content: The CTO model content as a string
        
    Returns:
        A dictionary with validation results suitable for LLM consumption
    """
    result = validate_cto_string(cto_content)
    
    return {
        "valid": result.is_valid,
        "status": result.status.value,
        "error": result.error_message,
        "details": result.error_details,
        "suggestion": _get_fix_suggestion(result) if not result.is_valid else None
    }


def _get_fix_suggestion(result: ValidationResult) -> str | None:
    """Generate a fix suggestion based on the error type."""
    if result.is_valid:
        return None
    
    if result.status == ValidationStatus.SYNTAX_ERROR:
        if "}" in str(result.error_message):
            return "Check for missing closing braces '}' in your model"
        if "expected" in str(result.error_message).lower():
            return "There's a syntax error - check the structure of your declarations"
        return "Review the syntax of your Concerto model"
    
    if result.status == ValidationStatus.TYPE_ERROR:
        if result.error_details and "Unknown type:" in result.error_details:
            type_name = result.error_details.split("Unknown type:")[-1].strip().split()[0]
            return f"The type '{type_name}' is not defined. Use a primitive type (String, Integer, Double, Boolean, DateTime) or define the type first"
        return "One or more types used in the model are not defined"
    
    return "Review the error message and fix the model accordingly"
