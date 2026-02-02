"""
Concerto Model Generator Agent

This agent takes structured intent and generates valid Concerto (.cto)
model files, using validation tools to ensure correctness.

Role: Structured Intent → Valid .cto file
"""

import logging
from typing import Optional

from src.llm_client import get_llm_client, LLMResponse
from src.models import StructuredIntent, GenerationResult
from src.prompts.templates import build_generator_prompt, build_fix_prompt
from src.tools.concerto_tools import validate_model, ValidationStatus

logger = logging.getLogger(__name__)


class ModelGeneratorAgent:
    """
    Agent that generates valid Concerto (.cto) models from structured intent.
    
    Uses a validation loop to ensure the generated model is syntactically
    and semantically correct.
    """
    
    MAX_RETRIES = 3
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the Model Generator agent.
        
        Args:
            verbose: If True, print debug information.
        """
        self.verbose = verbose
        self.llm = get_llm_client()
    
    def generate(self, intent: StructuredIntent) -> GenerationResult:
        """
        Generate a Concerto model from structured intent.
        
        Implements a validation loop that:
        1. Generates CTO from intent (or uses built-in method)
        2. Validates the CTO
        3. If invalid, uses LLM to fix and retries
        
        Args:
            intent: The structured intent from Requirements Analyst.
            
        Returns:
            GenerationResult with the CTO content if successful.
        """
        if self.verbose:
            print(f"\n🔧 Generating Concerto model...")
            print(f"   Namespace: {intent.namespace}@{intent.version}")
            print(f"   Concepts: {[c.name for c in intent.concepts]}")
        
        # First, try using the built-in CTO generation from StructuredIntent
        # This is deterministic and follows our templates
        cto_content = intent.to_cto()
        
        if self.verbose:
            print(f"\n   Generated initial CTO ({len(cto_content)} chars)")
        
        # Validation loop
        attempts = 0
        validation_errors = []
        
        while attempts < self.MAX_RETRIES:
            attempts += 1
            
            if self.verbose:
                print(f"\n   Attempt {attempts}/{self.MAX_RETRIES}: Validating...")
            
            # Validate the current CTO
            result = validate_model(cto_content)
            
            if result["valid"]:
                if self.verbose:
                    print(f"   ✅ Validation passed!")
                
                return GenerationResult(
                    success=True,
                    cto_content=cto_content,
                    attempts=attempts,
                    validation_errors=validation_errors
                )
            
            # Validation failed
            error_msg = result.get("error", "Unknown error")
            validation_errors.append(error_msg)
            
            if self.verbose:
                print(f"   ❌ Validation failed: {error_msg}")
                if result.get("suggestion"):
                    print(f"   💡 Suggestion: {result['suggestion']}")
            
            # Use LLM to fix the model
            if attempts < self.MAX_RETRIES:
                if self.verbose:
                    print(f"   🔄 Attempting to fix...")
                
                fixed_cto = self._fix_model(
                    cto_content=cto_content,
                    error_message=error_msg,
                    error_details=result.get("details", ""),
                    suggestion=result.get("suggestion", "")
                )
                
                if fixed_cto:
                    cto_content = fixed_cto
                else:
                    if self.verbose:
                        print(f"   ⚠️ Fix attempt failed")
        
        # All retries exhausted
        if self.verbose:
            print(f"\n   ❌ Failed after {attempts} attempts")
        
        return GenerationResult(
            success=False,
            cto_content=cto_content,  # Return last attempt
            error_message=f"Validation failed after {attempts} attempts",
            attempts=attempts,
            validation_errors=validation_errors
        )
    
    def generate_with_llm(self, intent: StructuredIntent) -> GenerationResult:
        """
        Generate CTO model using LLM instead of deterministic template.
        
        This method uses the LLM to generate the CTO, which may produce
        more nuanced output but is less predictable.
        
        Args:
            intent: The structured intent.
            
        Returns:
            GenerationResult with the CTO content.
        """
        if self.verbose:
            print(f"\n🤖 Generating Concerto model with LLM...")
        
        # Build prompts
        import json
        intent_json = json.dumps(intent.model_dump(), indent=2)
        system_prompt, user_prompt = build_generator_prompt(intent_json)
        
        # Call LLM
        response = self.llm.chat(system_prompt, user_prompt)
        
        if not response.success:
            return GenerationResult(
                success=False,
                error_message=f"LLM call failed: {response.error}",
                attempts=1
            )
        
        cto_content = self._clean_cto_response(response.content)
        
        # Now proceed with validation loop
        return self._validate_and_fix(cto_content)
    
    def _fix_model(
        self,
        cto_content: str,
        error_message: str,
        error_details: str = "",
        suggestion: str = ""
    ) -> Optional[str]:
        """
        Use LLM to fix a model with validation errors.
        
        Args:
            cto_content: The current (invalid) CTO content.
            error_message: The validation error message.
            error_details: Additional error details.
            suggestion: Suggested fix.
            
        Returns:
            Fixed CTO content, or None if fix failed.
        """
        system_prompt, user_prompt = build_fix_prompt(
            cto_content=cto_content,
            error_message=error_message,
            error_details=error_details,
            suggestion=suggestion
        )
        
        response = self.llm.chat(system_prompt, user_prompt)
        
        if not response.success:
            logger.error(f"Fix attempt failed: {response.error}")
            return None
        
        fixed = self._clean_cto_response(response.content)
        
        # Ensure the fix is different from the original
        if fixed.strip() == cto_content.strip():
            logger.warning("LLM returned identical content")
            return None
        
        return fixed
    
    def _validate_and_fix(self, cto_content: str) -> GenerationResult:
        """
        Run the validation and fix loop.
        
        Args:
            cto_content: Initial CTO content.
            
        Returns:
            GenerationResult after validation loop.
        """
        attempts = 0
        validation_errors = []
        
        while attempts < self.MAX_RETRIES:
            attempts += 1
            
            result = validate_model(cto_content)
            
            if result["valid"]:
                return GenerationResult(
                    success=True,
                    cto_content=cto_content,
                    attempts=attempts,
                    validation_errors=validation_errors
                )
            
            error_msg = result.get("error", "Unknown error")
            validation_errors.append(error_msg)
            
            if attempts < self.MAX_RETRIES:
                fixed = self._fix_model(
                    cto_content=cto_content,
                    error_message=error_msg,
                    error_details=result.get("details", ""),
                    suggestion=result.get("suggestion", "")
                )
                if fixed:
                    cto_content = fixed
        
        return GenerationResult(
            success=False,
            cto_content=cto_content,
            error_message=f"Validation failed after {attempts} attempts",
            attempts=attempts,
            validation_errors=validation_errors
        )
    
    def _clean_cto_response(self, content: str) -> str:
        """
        Clean LLM response to extract raw CTO content.
        
        Removes markdown code blocks and extra whitespace.
        
        Args:
            content: Raw LLM response.
            
        Returns:
            Cleaned CTO content.
        """
        content = content.strip()
        
        # Remove markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            cleaned_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```"):
                    in_block = not in_block
                    continue
                if in_block or not content.startswith("```"):
                    cleaned_lines.append(line)
            content = "\n".join(cleaned_lines)
        
        return content.strip()


# Convenience function
def generate_model(intent: StructuredIntent) -> GenerationResult:
    """
    Generate a Concerto model from structured intent.
    
    Args:
        intent: The structured intent.
        
    Returns:
        GenerationResult with the CTO content.
    """
    agent = ModelGeneratorAgent(verbose=True)
    return agent.generate(intent)
