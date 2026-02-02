"""
Accordo Agent Command Line Interface

A CLI for generating Concerto models from natural language descriptions.
Similar to gemini-cli or claude code, providing an interactive and
command-based interface.

Usage:
    accordo generate "description"
    accordo validate file.cto
    accordo preview "description"
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add src to path if running directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import required packages, provide helpful error if missing
try:
    import click
except ImportError:
    print("Error: 'click' package not installed.")
    print("Install with: pip install click")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
except ImportError:
    print("Error: 'rich' package not installed.")
    print("Install with: pip install rich")
    sys.exit(1)

# Optional: dotenv for loading .env files
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional - environment variables can be set directly
    pass

# Rich console for pretty output
console = Console()


def check_api_key() -> bool:
    """Check if Groq API key is set."""
    if os.getenv("GROQ_API_KEY"):
        return True
    
    console.print(Panel(
        "[red bold]❌ GROQ_API_KEY not set![/]\n\n"
        "To get a free API key:\n"
        "  1. Go to [link=https://console.groq.com/keys]https://console.groq.com/keys[/link]\n"
        "  2. Sign up / Log in\n"
        "  3. Create a new API key\n\n"
        "Then run:\n"
        "  [cyan]export GROQ_API_KEY=your_key_here[/]",
        title="API Key Required",
        border_style="red"
    ))
    return False


@click.group()
@click.version_option(version="0.1.0", prog_name="accordo")
def cli():
    """
    🤖 Accordo Agent - Generate Concerto models from natural language
    
    An agentic workflow that converts natural language contract requirements
    into valid Concerto (.cto) model files.
    
    Examples:
    
        accordo generate "I need a loan agreement with borrower name and amount"
        
        accordo validate output/model.cto
        
        accordo preview "A vehicle rental contract"
    """
    pass


@cli.command()
@click.argument("description")
@click.option(
    "--namespace", "-n",
    help="Preferred namespace (e.g., org.example.loan)"
)
@click.option(
    "--context", "-c",
    help="Additional context or constraints"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="./output",
    help="Output directory for generated files"
)
@click.option(
    "--no-save",
    is_flag=True,
    help="Don't save to file, just print output"
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Minimal output"
)
def generate(
    description: str,
    namespace: Optional[str],
    context: Optional[str],
    output: str,
    no_save: bool,
    quiet: bool
):
    """
    Generate a Concerto model from a natural language description.
    
    DESCRIPTION is your natural language description of the contract/model
    you want to create.
    
    Examples:
    
        accordo generate "A loan agreement with borrower, amount, and rate"
        
        accordo generate "Vehicle rental contract" -n org.rental
        
        accordo generate "Employee contract with salary" -o ./models
    """
    if not check_api_key():
        sys.exit(1)
    
    if not quiet:
        console.print(Panel(
            f"[cyan]{description}[/]",
            title="📝 Input Description",
            border_style="blue"
        ))
    
    try:
        from src.workflow import AccordoWorkflow
        
        workflow = AccordoWorkflow(
            verbose=not quiet,
            output_dir=output
        )
        
        result = workflow.run(
            description=description,
            namespace=namespace,
            context=context,
            save=not no_save
        )
        
        if result.success:
            if not quiet:
                console.print()
                console.print(Panel(
                    Syntax(result.cto_content, "javascript", theme="monokai"),
                    title="✅ Generated Concerto Model",
                    border_style="green"
                ))
                
                if not no_save:
                    console.print(f"\n💾 Saved to: [cyan]{output}/[/]")
            else:
                # Quiet mode - just print the CTO
                print(result.cto_content)
        else:
            console.print(Panel(
                f"[red]{result.error_message}[/]\n\n"
                f"Errors encountered:\n" + 
                "\n".join(f"  • {e}" for e in result.validation_errors),
                title="❌ Generation Failed",
                border_style="red"
            ))
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed validation output"
)
def validate(file: str, verbose: bool):
    """
    Validate a Concerto (.cto) model file.
    
    FILE is the path to the .cto file to validate.
    
    Examples:
    
        accordo validate model.cto
        
        accordo validate output/org_example_loan.cto -v
    """
    try:
        from src.tools.concerto_tools import validate_cto_file, ValidationStatus
        
        file_path = Path(file)
        
        console.print(f"🔍 Validating: [cyan]{file_path}[/]")
        
        result = validate_cto_file(file_path)
        
        if result.is_valid:
            console.print(Panel(
                "[green bold]✅ Model is valid![/]",
                title="Validation Result",
                border_style="green"
            ))
            
            if verbose and result.ast_json:
                console.print("\n[dim]AST parsed successfully[/]")
        else:
            status_emoji = {
                ValidationStatus.SYNTAX_ERROR: "📝",
                ValidationStatus.TYPE_ERROR: "🔤",
                ValidationStatus.UNKNOWN_ERROR: "❓"
            }
            
            console.print(Panel(
                f"[red bold]❌ Validation failed![/]\n\n"
                f"{status_emoji.get(result.status, '❌')} Status: [yellow]{result.status.value}[/]\n\n"
                f"Error: {result.error_message}\n\n"
                f"{f'Details: {result.error_details}' if result.error_details else ''}",
                title="Validation Result",
                border_style="red"
            ))
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


@cli.command()
@click.argument("description")
@click.option(
    "--namespace", "-n",
    help="Preferred namespace"
)
def preview(description: str, namespace: Optional[str]):
    """
    Preview the structured intent without generating CTO.
    
    This shows what the Requirements Analyst extracts from your
    description, before the Model Generator creates the CTO.
    
    Useful for debugging or understanding how your description
    is interpreted.
    
    Examples:
    
        accordo preview "A loan agreement with borrower and amount"
    """
    if not check_api_key():
        sys.exit(1)
    
    console.print(Panel(
        f"[cyan]{description}[/]",
        title="📝 Input Description",
        border_style="blue"
    ))
    
    try:
        from src.agents.requirements_agent import RequirementsAnalystAgent
        from src.models import UserRequest
        
        agent = RequirementsAnalystAgent(verbose=False)
        request = UserRequest(
            description=description,
            preferred_namespace=namespace
        )
        
        console.print("\n🔍 Analyzing requirements...\n")
        
        intent, error = agent.analyze(request)
        
        if error:
            console.print(f"[red]Analysis failed: {error}[/]")
            sys.exit(1)
        
        # Display as table
        table = Table(title="Structured Intent")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Namespace", f"{intent.namespace}@{intent.version}")
        table.add_row("Concepts", str(len(intent.concepts)))
        
        console.print(table)
        
        for concept in intent.concepts:
            console.print(f"\n[bold]Concept: {concept.name}[/]")
            if concept.description:
                console.print(f"[dim]{concept.description}[/]")
            
            field_table = Table()
            field_table.add_column("Field", style="cyan")
            field_table.add_column("Type", style="yellow")
            field_table.add_column("Optional", style="magenta")
            field_table.add_column("Description", style="dim")
            
            for field in concept.fields:
                type_str = f"{field.type}{'[]' if field.is_array else ''}"
                opt_str = "Yes" if field.optional else "No"
                field_table.add_row(
                    field.name,
                    type_str,
                    opt_str,
                    field.description or ""
                )
            
            console.print(field_table)
        
        # Show what CTO would be generated
        console.print("\n[bold]Preview CTO:[/]")
        console.print(Panel(
            Syntax(intent.to_cto(), "javascript", theme="monokai"),
            border_style="dim"
        ))
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


@cli.command()
def info():
    """
    Show information about the Accordo Agent.
    """
    console.print(Panel(
        "[bold cyan]🤖 Accordo Agent[/]\n\n"
        "[dim]GSoC 2026 MVP - Agentic Workflow for Accord Project Templates[/]\n\n"
        "[bold]Architecture:[/]\n"
        "  • Requirements Analyst Agent: NL → Structured Intent\n"
        "  • Model Generator Agent: Intent → Valid .cto\n"
        "  • Validation via @accordproject/concerto-cli\n\n"
        "[bold]LLM Provider:[/]\n"
        f"  • Groq (Model: {os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')})\n\n"
        "[bold]Links:[/]\n"
        "  • GitHub: [link]https://github.com/adarshh347/dummy-accordo-agent[/link]\n"
        "  • Accord Project: [link]https://accordproject.org[/link]\n"
        "  • Groq Console: [link]https://console.groq.com/keys[/link]",
        title="About",
        border_style="cyan"
    ))
    
    # Check status
    table = Table(title="Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    
    # Check API key
    api_status = "✅ Configured" if os.getenv("GROQ_API_KEY") else "❌ Not set"
    table.add_row("GROQ_API_KEY", api_status)
    
    # Check concerto-cli
    try:
        import subprocess
        result = subprocess.run(
            ["npx", "concerto", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent.parent.parent
        )
        cli_version = result.stdout.strip() if result.returncode == 0 else "Not found"
        table.add_row("concerto-cli", f"✅ v{cli_version}")
    except Exception:
        table.add_row("concerto-cli", "❌ Not found")
    
    console.print(table)


@cli.command()
@click.argument("description")
@click.option("--iterations", "-i", default=1, help="Number of models to generate")
def batch(description: str, iterations: int):
    """
    Generate multiple model variations (for testing).
    
    DESCRIPTION is the base description to use.
    """
    if not check_api_key():
        sys.exit(1)
    
    console.print(f"Generating {iterations} model(s)...\n")
    
    from src.workflow import AccordoWorkflow
    
    workflow = AccordoWorkflow(verbose=False)
    
    successes = 0
    failures = 0
    
    for i in range(iterations):
        console.print(f"[dim]Iteration {i+1}/{iterations}...[/]", end=" ")
        result = workflow.run(description, save=False)
        
        if result.success:
            console.print("[green]✓[/]")
            successes += 1
        else:
            console.print(f"[red]✗ {result.error_message}[/]")
            failures += 1
    
    console.print(f"\nResults: [green]{successes} succeeded[/], [red]{failures} failed[/]")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
