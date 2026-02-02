"""
Accordo Agent Workflow Orchestrator

This module ties together all agents to provide the complete
workflow from natural language input to valid .cto output.
"""

import os
from pathlib import Path
from typing import Optional

from src.agents.requirements_agent import RequirementsAnalystAgent
from src.agents.model_agent import ModelGeneratorAgent
from src.models import UserRequest, StructuredIntent, GenerationResult


class AccordoWorkflow:
    """
    Main workflow orchestrator that coordinates agents to generate
    Concerto models from natural language descriptions.
    """
    
    def __init__(self, verbose: bool = True, output_dir: Optional[str] = None):
        """
        Initialize the workflow.
        
        Args:
            verbose: If True, print progress information.
            output_dir: Directory to save generated .cto files.
        """
        self.verbose = verbose
        self.output_dir = Path(output_dir) if output_dir else Path("./output")
        
        # Initialize agents
        self.analyst = RequirementsAnalystAgent(verbose=verbose)
        self.generator = ModelGeneratorAgent(verbose=verbose)
    
    def run(
        self,
        description: str,
        namespace: Optional[str] = None,
        context: Optional[str] = None,
        save: bool = True
    ) -> GenerationResult:
        """
        Run the complete workflow from description to .cto file.
        
        Args:
            description: Natural language description of the model.
            namespace: Optional preferred namespace.
            context: Optional additional context.
            save: If True, save the generated .cto file.
            
        Returns:
            GenerationResult with the outcome.
        """
        if self.verbose:
            print("\n" + "=" * 60)
            print("🚀 Accordo Agent - Generating Concerto Model")
            print("=" * 60)
        
        # Step 1: Create user request
        request = UserRequest(
            description=description,
            preferred_namespace=namespace,
            additional_context=context
        )
        
        # Step 2: Analyze requirements
        if self.verbose:
            print("\n📋 PHASE 1: Requirements Analysis")
            print("-" * 40)
        
        intent, error = self.analyst.analyze(request)
        
        if error:
            if self.verbose:
                print(f"\n❌ Analysis failed: {error}")
            return GenerationResult(
                success=False,
                error_message=f"Requirements analysis failed: {error}",
                attempts=0
            )
        
        if self.verbose:
            print(f"\n   Structured Intent:")
            print(f"   - Namespace: {intent.namespace}@{intent.version}")
            for concept in intent.concepts:
                print(f"   - Concept: {concept.name}")
                for field in concept.fields:
                    opt = " (optional)" if field.optional else ""
                    arr = "[]" if field.is_array else ""
                    print(f"     • {field.name}: {field.type}{arr}{opt}")
        
        # Step 3: Generate model
        if self.verbose:
            print("\n📝 PHASE 2: Model Generation")
            print("-" * 40)
        
        result = self.generator.generate(intent)
        
        # Step 4: Save if successful
        if result.success and save:
            if self.verbose:
                print("\n💾 PHASE 3: Saving Output")
                print("-" * 40)
            
            output_path = self._save_model(intent, result.cto_content)
            
            if self.verbose:
                print(f"   Saved to: {output_path}")
        
        # Final summary
        if self.verbose:
            print("\n" + "=" * 60)
            if result.success:
                print("✅ SUCCESS - Model generated and validated!")
            else:
                print(f"❌ FAILED - {result.error_message}")
            print("=" * 60)
            
            if result.success:
                print("\n📄 Generated CTO:")
                print("-" * 40)
                print(result.cto_content)
        
        return result
    
    def _save_model(self, intent: StructuredIntent, cto_content: str) -> Path:
        """
        Save the generated model to a file.
        
        Args:
            intent: The structured intent (for naming).
            cto_content: The CTO content to save.
            
        Returns:
            Path to the saved file.
        """
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename from namespace
        filename = intent.namespace.replace(".", "_") + ".cto"
        output_path = self.output_dir / filename
        
        # Write file
        output_path.write_text(cto_content)
        
        return output_path
    
    def preview(self, description: str) -> Optional[StructuredIntent]:
        """
        Preview the structured intent without generating CTO.
        
        Useful for debugging the requirements analysis phase.
        
        Args:
            description: Natural language description.
            
        Returns:
            StructuredIntent if successful, None otherwise.
        """
        request = UserRequest(description=description)
        intent, error = self.analyst.analyze(request)
        
        if error:
            print(f"❌ Analysis failed: {error}")
            return None
        
        return intent


# Convenience function for simple usage
def generate(
    description: str,
    namespace: Optional[str] = None,
    context: Optional[str] = None,
    save: bool = True,
    verbose: bool = True
) -> GenerationResult:
    """
    Generate a Concerto model from a natural language description.
    
    Args:
        description: Natural language description of the model.
        namespace: Optional preferred namespace.
        context: Optional additional context.
        save: If True, save the generated .cto file.
        verbose: If True, print progress information.
        
    Returns:
        GenerationResult with the outcome.
    
    Example:
        >>> result = generate("I need a loan agreement with borrower name and amount")
        >>> if result.success:
        ...     print(result.cto_content)
    """
    workflow = AccordoWorkflow(verbose=verbose)
    return workflow.run(description, namespace, context, save)
