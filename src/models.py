"""
Data models for the Accordo Agent workflow.

These Pydantic models define the structured data that flows
between agents in the workflow.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConcertoType(str, Enum):
    """Supported Concerto primitive types."""
    STRING = "String"
    INTEGER = "Integer"
    LONG = "Long"
    DOUBLE = "Double"
    BOOLEAN = "Boolean"
    DATETIME = "DateTime"


class FieldDefinition(BaseModel):
    """Definition of a single field in a concept."""
    
    name: str = Field(
        ...,
        description="Field name in camelCase",
        pattern=r'^[a-z][a-zA-Z0-9]*$'
    )
    type: str = Field(
        ...,
        description="Concerto type (String, Integer, Double, Boolean, DateTime, or custom)"
    )
    description: Optional[str] = Field(
        None,
        description="Human-readable description of the field"
    )
    optional: bool = Field(
        False,
        description="Whether the field is optional"
    )
    is_array: bool = Field(
        False,
        description="Whether the field is an array"
    )
    
    def to_cto_line(self) -> str:
        """Convert field to CTO syntax."""
        type_str = f"{self.type}[]" if self.is_array else self.type
        optional_str = " optional" if self.optional else ""
        return f"  o {type_str} {self.name}{optional_str}"


class ConceptDefinition(BaseModel):
    """Definition of a Concerto concept."""
    
    name: str = Field(
        ...,
        description="Concept name in PascalCase",
        pattern=r'^[A-Z][a-zA-Z0-9]*$'
    )
    description: Optional[str] = Field(
        None,
        description="Human-readable description of the concept"
    )
    fields: list[FieldDefinition] = Field(
        default_factory=list,
        description="List of fields in the concept"
    )
    is_abstract: bool = Field(
        False,
        description="Whether this is an abstract concept"
    )
    extends: Optional[str] = Field(
        None,
        description="Parent concept to extend"
    )
    identified_by: Optional[str] = Field(
        None,
        description="Field name that identifies instances"
    )
    
    def to_cto(self) -> str:
        """Convert concept to CTO syntax."""
        lines = []
        
        # Build declaration line
        abstract = "abstract " if self.is_abstract else ""
        identified = f" identified by {self.identified_by}" if self.identified_by else ""
        extends = f" extends {self.extends}" if self.extends else ""
        
        lines.append(f"{abstract}concept {self.name}{identified}{extends} {{")
        
        # Add fields
        for field in self.fields:
            lines.append(field.to_cto_line())
        
        lines.append("}")
        
        return "\n".join(lines)


class StructuredIntent(BaseModel):
    """
    Structured intent extracted from natural language requirements.
    
    This is the output of the Requirements Analyst Agent and the
    input to the Concerto Model Generator Agent.
    """
    
    namespace: str = Field(
        ...,
        description="Concerto namespace (e.g., 'org.example.loan')",
        pattern=r'^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$'
    )
    version: str = Field(
        "1.0.0",
        description="Semantic version",
        pattern=r'^\d+\.\d+\.\d+$'
    )
    concepts: list[ConceptDefinition] = Field(
        ...,
        description="List of concepts to generate",
        min_length=1
    )
    imports: list[str] = Field(
        default_factory=list,
        description="External namespaces to import"
    )
    
    def to_cto(self) -> str:
        """Convert the entire structured intent to CTO syntax."""
        lines = []
        
        # Namespace with version
        lines.append(f"namespace {self.namespace}@{self.version}")
        lines.append("")
        
        # Imports
        for imp in self.imports:
            lines.append(f"import {imp}")
        if self.imports:
            lines.append("")
        
        # Concepts
        for concept in self.concepts:
            lines.append(concept.to_cto())
            lines.append("")
        
        return "\n".join(lines).strip() + "\n"


class GenerationResult(BaseModel):
    """Result of the CTO generation process."""
    
    success: bool = Field(
        ...,
        description="Whether generation was successful"
    )
    cto_content: Optional[str] = Field(
        None,
        description="Generated CTO content if successful"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if generation failed"
    )
    attempts: int = Field(
        1,
        description="Number of generation attempts"
    )
    validation_errors: list[str] = Field(
        default_factory=list,
        description="List of validation errors encountered"
    )


class UserRequest(BaseModel):
    """User's natural language request for model generation."""
    
    description: str = Field(
        ...,
        description="Natural language description of the desired model",
        min_length=10
    )
    preferred_namespace: Optional[str] = Field(
        None,
        description="Optional preferred namespace"
    )
    additional_context: Optional[str] = Field(
        None,
        description="Additional context or constraints"
    )
