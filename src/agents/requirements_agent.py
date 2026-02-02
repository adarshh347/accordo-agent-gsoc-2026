"""
Requirements Analyst Agent

This agent analyzes natural language descriptions of contracts/models
and extracts structured requirements that can be used to generate
Concerto model files.

Role: Natural Language → Structured Intent (JSON)
"""

import json
import logging
from typing import Optional

from src.llm_client import get_llm_client, LLMResponse
from src.models import (
    StructuredIntent,
    ConceptDefinition,
    FieldDefinition,
    UserRequest,
)
from src.prompts.templates import build_analyst_prompt

logger = logging.getLogger(__name__)


class RequirementsAnalystAgent:
    """
    Agent that analyzes natural language requirements and extracts
    structured intent for Concerto model generation.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the Requirements Analyst agent.
        
        Args:
            verbose: If True, print debug information.
        """
        self.verbose = verbose
        self.llm = get_llm_client()
    
    def analyze(self, request: UserRequest) -> tuple[Optional[StructuredIntent], Optional[str]]:
        """
        Analyze a user request and extract structured intent.
        
        Args:
            request: The user's natural language request.
            
        Returns:
            Tuple of (StructuredIntent, error_message).
            If successful, error_message is None.
            If failed, StructuredIntent is None.
        """
        if self.verbose:
            print(f"\n🔍 Analyzing requirements...")
            print(f"   Input: {request.description[:100]}...")
        
        # Build prompts
        system_prompt, user_prompt = build_analyst_prompt(
            description=request.description,
            additional_context=request.additional_context or ""
        )
        
        # Call LLM for JSON response
        parsed_json, error = self.llm.chat_json(system_prompt, user_prompt)
        
        if error:
            logger.error(f"LLM call failed: {error}")
            return None, f"Failed to analyze requirements: {error}"
        
        if self.verbose:
            print(f"   LLM Response received")
        
        # Validate and convert to StructuredIntent
        try:
            intent = self._parse_response(parsed_json)
            
            # Apply preferred namespace if provided
            if request.preferred_namespace:
                intent.namespace = request.preferred_namespace
            
            if self.verbose:
                print(f"   ✅ Extracted {len(intent.concepts)} concept(s)")
                for concept in intent.concepts:
                    print(f"      - {concept.name}: {len(concept.fields)} fields")
            
            return intent, None
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None, f"Failed to parse structured intent: {e}"
    
    def _parse_response(self, data: dict) -> StructuredIntent:
        """
        Parse the LLM response into a StructuredIntent model.
        
        Args:
            data: The parsed JSON from the LLM.
            
        Returns:
            StructuredIntent model.
            
        Raises:
            ValueError: If the response is invalid.
        """
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data)}")
        
        # Extract namespace
        namespace = data.get("namespace", "org.example.generated")
        version = data.get("version", "1.0.0")
        
        # Parse concepts
        concepts = []
        for concept_data in data.get("concepts", []):
            fields = []
            
            for field_data in concept_data.get("fields", []):
                field = FieldDefinition(
                    name=self._to_camel_case(field_data.get("name", "unknown")),
                    type=self._normalize_type(field_data.get("type", "String")),
                    description=field_data.get("description"),
                    optional=field_data.get("optional", False),
                    is_array=field_data.get("is_array", False)
                )
                fields.append(field)
            
            concept = ConceptDefinition(
                name=self._to_pascal_case(concept_data.get("name", "UnnamedConcept")),
                description=concept_data.get("description"),
                fields=fields
            )
            concepts.append(concept)
        
        if not concepts:
            raise ValueError("No concepts found in response")
        
        return StructuredIntent(
            namespace=namespace,
            version=version,
            concepts=concepts
        )
    
    def _to_camel_case(self, name: str) -> str:
        """Convert a name to camelCase."""
        # Handle already camelCase
        if name and name[0].islower() and "_" not in name and " " not in name:
            return name
        
        # Split by underscore or space
        parts = name.replace("-", "_").replace(" ", "_").split("_")
        
        if not parts:
            return "unknown"
        
        # First word lowercase, rest capitalized
        result = parts[0].lower()
        for part in parts[1:]:
            if part:
                result += part.capitalize()
        
        return result
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert a name to PascalCase."""
        # Split by underscore or space
        parts = name.replace("-", "_").replace(" ", "_").split("_")
        
        if not parts:
            return "Unknown"
        
        # All words capitalized
        return "".join(part.capitalize() for part in parts if part)
    
    def _normalize_type(self, type_str: str) -> str:
        """Normalize type string to valid Concerto type."""
        type_map = {
            "string": "String",
            "str": "String",
            "text": "String",
            "int": "Integer",
            "integer": "Integer",
            "number": "Integer",
            "long": "Long",
            "double": "Double",
            "float": "Double",
            "decimal": "Double",
            "bool": "Boolean",
            "boolean": "Boolean",
            "date": "DateTime",
            "datetime": "DateTime",
            "time": "DateTime",
            "timestamp": "DateTime",
        }
        
        normalized = type_map.get(type_str.lower(), type_str)
        
        # Ensure first letter is capitalized
        if normalized and normalized[0].islower():
            normalized = normalized[0].upper() + normalized[1:]
        
        return normalized


# Convenience function
def analyze_requirements(description: str, context: str = "") -> tuple[Optional[StructuredIntent], Optional[str]]:
    """
    Analyze natural language requirements.
    
    Args:
        description: Natural language description of the model.
        context: Optional additional context.
        
    Returns:
        Tuple of (StructuredIntent, error_message).
    """
    agent = RequirementsAnalystAgent(verbose=True)
    request = UserRequest(
        description=description,
        additional_context=context if context else None
    )
    return agent.analyze(request)
