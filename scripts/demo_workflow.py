#!/usr/bin/env python3
"""
Demo script for the Accordo Agent workflow.

This script demonstrates the agent workflow without requiring 
a full pip install. Run it directly with python3.

Usage:
    # Set your Groq API key
    export GROQ_API_KEY=your_key_here
    
    # Run the demo
    python3 scripts/demo_workflow.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Check for API key before importing
import os
if not os.getenv("GROQ_API_KEY"):
    print("❌ ERROR: GROQ_API_KEY environment variable not set")
    print("")
    print("To get a free API key:")
    print("  1. Go to https://console.groq.com/keys")
    print("  2. Sign up / Log in")
    print("  3. Create a new API key")
    print("")
    print("Then run:")
    print("  export GROQ_API_KEY=your_key_here")
    print("  python3 scripts/demo_workflow.py")
    sys.exit(1)


def demo_structured_intent():
    """Demo: Test the data models and CTO generation."""
    print("\n" + "=" * 60)
    print("Demo 1: Structured Intent → CTO (No LLM)")
    print("=" * 60)
    
    from src.models import StructuredIntent, ConceptDefinition, FieldDefinition
    
    # Create a structured intent manually
    intent = StructuredIntent(
        namespace="org.example.rental",
        version="1.0.0",
        concepts=[
            ConceptDefinition(
                name="VehicleRental",
                description="A vehicle rental agreement",
                fields=[
                    FieldDefinition(name="renterName", type="String", description="Name of renter"),
                    FieldDefinition(name="vehicleType", type="String", description="Type of vehicle"),
                    FieldDefinition(name="dailyRate", type="Double", description="Daily rental rate"),
                    FieldDefinition(name="rentalDays", type="Integer", description="Number of rental days"),
                    FieldDefinition(name="startDate", type="DateTime", description="Start date", optional=True),
                ]
            )
        ]
    )
    
    # Generate CTO
    cto = intent.to_cto()
    print("\nGenerated CTO:")
    print("-" * 40)
    print(cto)
    
    # Validate it
    from src.tools.concerto_tools import validate_model
    result = validate_model(cto)
    
    print("-" * 40)
    if result["valid"]:
        print("✅ Validation: PASSED")
    else:
        print(f"❌ Validation: FAILED - {result['error']}")
    
    return result["valid"]


def demo_requirements_analyst():
    """Demo: Test the Requirements Analyst agent."""
    print("\n" + "=" * 60)
    print("Demo 2: Requirements Analyst Agent (With LLM)")
    print("=" * 60)
    
    from src.agents.requirements_agent import RequirementsAnalystAgent
    from src.models import UserRequest
    
    # Create user request
    description = """
    I need a model for a simple employment contract. It should have:
    - Employee's full name
    - Job title
    - Start date
    - Annual salary
    - Whether they are full-time or not
    """
    
    print(f"\nInput description:\n{description.strip()}")
    print("-" * 40)
    
    agent = RequirementsAnalystAgent(verbose=True)
    request = UserRequest(description=description)
    
    intent, error = agent.analyze(request)
    
    if error:
        print(f"\n❌ Analysis failed: {error}")
        return False
    
    print("\n✅ Structured Intent extracted:")
    print(f"   Namespace: {intent.namespace}@{intent.version}")
    for concept in intent.concepts:
        print(f"\n   Concept: {concept.name}")
        for field in concept.fields:
            opt = " (optional)" if field.optional else ""
            print(f"     - {field.name}: {field.type}{opt}")
    
    return True


def demo_full_workflow():
    """Demo: Test the full workflow."""
    print("\n" + "=" * 60)
    print("Demo 3: Full Workflow (NL → CTO)")
    print("=" * 60)
    
    from src.workflow import AccordoWorkflow
    
    description = """
    Create a model for a software license agreement with:
    - Licensor name
    - Licensee name  
    - Software name
    - License type (e.g., MIT, Apache)
    - Issue date
    - Whether it's a perpetual license
    - Optional expiration date
    """
    
    print(f"\nInput description:\n{description.strip()}")
    print("-" * 40)
    
    workflow = AccordoWorkflow(verbose=True, output_dir="./output")
    result = workflow.run(description, save=True)
    
    return result.success


def main():
    """Run all demos."""
    print("\n" + "🚀 " * 20)
    print("   ACCORDO AGENT - DEMO")
    print("🚀 " * 20)
    
    results = []
    
    # Demo 1: No LLM needed
    try:
        results.append(("Structured Intent → CTO", demo_structured_intent()))
    except Exception as e:
        print(f"❌ Demo 1 failed: {e}")
        results.append(("Structured Intent → CTO", False))
    
    # Demo 2: Needs LLM
    try:
        results.append(("Requirements Analyst", demo_requirements_analyst()))
    except Exception as e:
        print(f"❌ Demo 2 failed: {e}")
        results.append(("Requirements Analyst", False))
    
    # Demo 3: Full workflow
    try:
        results.append(("Full Workflow", demo_full_workflow()))
    except Exception as e:
        print(f"❌ Demo 3 failed: {e}")
        results.append(("Full Workflow", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("DEMO SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
