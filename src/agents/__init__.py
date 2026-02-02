"""
Agent definitions for the Accordo workflow.

This module contains the two core agents:
- Requirements Analyst Agent: Converts natural language → structured intent
- Concerto Model Generator Agent: Converts structured intent → .cto files
"""

from src.agents.requirements_agent import RequirementsAnalystAgent, analyze_requirements
from src.agents.model_agent import ModelGeneratorAgent, generate_model

__all__ = [
    "RequirementsAnalystAgent",
    "ModelGeneratorAgent",
    "analyze_requirements",
    "generate_model",
]
