"""
DSPy Commands for Specify CLI

Provides Typer commands for working with DSPy (Declarative Self-improving Python)
to enable LLM-powered specification generation and optimization.
"""

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

console = Console()

# Create the DSPy subcommand app
dspy_app = typer.Typer(
    name="dspy",
    help="DSPy commands for LLM-powered specification generation",
    add_completion=False,
)

# Default configuration file path
DEFAULT_CONFIG_PATH = Path(".specify") / "dspy_config.json"

# Supported LM providers
LM_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1", "o1-mini", "o1-preview"],
        "env_var": "OPENAI_API_KEY",
    },
    "anthropic": {
        "name": "Anthropic",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        "env_var": "ANTHROPIC_API_KEY",
    },
    "google": {
        "name": "Google",
        "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"],
        "env_var": "GOOGLE_API_KEY",
    },
    "ollama": {
        "name": "Ollama (Local)",
        "models": ["llama3.2", "llama3.1", "mistral", "codellama", "qwen2.5-coder"],
        "env_var": None,
    },
}


def check_dspy_available():
    """Check if DSPy is available and raise error if not."""
    if not DSPY_AVAILABLE:
        console.print(Panel(
            "[red]DSPy is not installed.[/red]\n\n"
            "Install it with:\n"
            "[cyan]pip install dspy[/cyan]\n\n"
            "Or reinstall specify-cli with DSPy support.",
            title="DSPy Not Available",
            border_style="red"
        ))
        raise typer.Exit(1)


def load_config(config_path: Path = None) -> dict:
    """Load DSPy configuration from file."""
    path = config_path or DEFAULT_CONFIG_PATH
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {}


def save_config(config: dict, config_path: Path = None):
    """Save DSPy configuration to file."""
    path = config_path or DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
    console.print(f"[green]Configuration saved to {path}[/green]")


def get_configured_lm(config: dict = None):
    """Get a configured DSPy LM instance based on stored config."""
    check_dspy_available()

    if config is None:
        config = load_config()

    provider = config.get("provider", "openai")
    model = config.get("model", "gpt-4o-mini")

    provider_info = LM_PROVIDERS.get(provider, {})
    env_var = provider_info.get("env_var")

    # Check for API key if required
    if env_var and not os.getenv(env_var):
        console.print(Panel(
            f"[red]Missing API key for {provider_info.get('name', provider)}[/red]\n\n"
            f"Set the [cyan]{env_var}[/cyan] environment variable:\n"
            f"[dim]export {env_var}=your-api-key[/dim]",
            title="API Key Required",
            border_style="red"
        ))
        raise typer.Exit(1)

    # Configure the LM based on provider
    if provider == "openai":
        lm = dspy.LM(f"openai/{model}")
    elif provider == "anthropic":
        lm = dspy.LM(f"anthropic/{model}")
    elif provider == "google":
        lm = dspy.LM(f"google/{model}")
    elif provider == "ollama":
        base_url = config.get("base_url", "http://localhost:11434")
        lm = dspy.LM(f"ollama_chat/{model}", api_base=base_url)
    else:
        lm = dspy.LM(f"{provider}/{model}")

    return lm


@dspy_app.command()
def configure(
    provider: str = typer.Option(None, "--provider", "-p", help="LM provider: openai, anthropic, google, ollama"),
    model: str = typer.Option(None, "--model", "-m", help="Model name to use"),
    base_url: str = typer.Option(None, "--base-url", help="Base URL for Ollama or custom endpoints"),
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
):
    """
    Configure DSPy language model settings.

    Examples:
        specify dspy configure --provider openai --model gpt-4o
        specify dspy configure --provider anthropic --model claude-3-5-sonnet-20241022
        specify dspy configure --provider ollama --model llama3.2 --base-url http://localhost:11434
        specify dspy configure --show
    """
    check_dspy_available()

    config = load_config()

    if show:
        if not config:
            console.print("[yellow]No DSPy configuration found.[/yellow]")
            console.print("[dim]Run 'specify dspy configure --provider <provider> --model <model>' to set up.[/dim]")
            return

        table = Table(title="DSPy Configuration", show_header=True, header_style="bold cyan")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")

        for key, value in config.items():
            table.add_row(key, str(value))

        console.print(table)

        # Show available providers
        console.print("\n[bold]Available Providers:[/bold]")
        for pkey, pinfo in LM_PROVIDERS.items():
            env_status = ""
            if pinfo.get("env_var"):
                env_set = os.getenv(pinfo["env_var"])
                env_status = " [green](configured)[/green]" if env_set else " [red](API key missing)[/red]"
            console.print(f"  [cyan]{pkey}[/cyan]: {pinfo['name']}{env_status}")
        return

    if provider:
        if provider not in LM_PROVIDERS:
            console.print(f"[red]Unknown provider: {provider}[/red]")
            console.print(f"[dim]Available: {', '.join(LM_PROVIDERS.keys())}[/dim]")
            raise typer.Exit(1)
        config["provider"] = provider

        # Set default model if not specified
        if not model and not config.get("model"):
            config["model"] = LM_PROVIDERS[provider]["models"][0]

    if model:
        config["model"] = model

    if base_url:
        config["base_url"] = base_url

    if provider or model or base_url:
        save_config(config)

        # Show the new configuration
        console.print(Panel(
            f"[bold]Provider:[/bold] {config.get('provider', 'not set')}\n"
            f"[bold]Model:[/bold] {config.get('model', 'not set')}\n"
            f"[bold]Base URL:[/bold] {config.get('base_url', 'default')}",
            title="[green]DSPy Configuration Updated[/green]",
            border_style="green"
        ))
    else:
        console.print("[yellow]No changes made. Use --provider, --model, or --base-url to configure.[/yellow]")
        console.print("[dim]Use --show to view current configuration.[/dim]")


@dspy_app.command()
def run(
    signature: str = typer.Argument(..., help="DSPy signature (e.g., 'question -> answer' or 'context, question -> answer')"),
    input_text: str = typer.Option(None, "--input", "-i", help="Input text for the signature"),
    input_file: Path = typer.Option(None, "--file", "-f", help="Read input from file"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Write output to file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """
    Run a DSPy signature with input.

    Examples:
        specify dspy run "question -> answer" --input "What is Python?"
        specify dspy run "context, question -> answer" --file context.txt --input "Summarize this"
        specify dspy run "text -> summary" --file document.md --output summary.txt
    """
    check_dspy_available()

    config = load_config()
    if not config:
        console.print("[red]DSPy not configured. Run 'specify dspy configure' first.[/red]")
        raise typer.Exit(1)

    # Get input
    if input_file:
        if not input_file.exists():
            console.print(f"[red]File not found: {input_file}[/red]")
            raise typer.Exit(1)
        file_content = input_file.read_text()
    else:
        file_content = None

    if not input_text and not file_content:
        console.print("[red]Provide input with --input or --file[/red]")
        raise typer.Exit(1)

    # Configure DSPy
    lm = get_configured_lm(config)
    dspy.configure(lm=lm)

    # Parse signature and create predictor
    try:
        predictor = dspy.Predict(signature)
    except Exception as e:
        console.print(f"[red]Invalid signature: {e}[/red]")
        raise typer.Exit(1)

    # Prepare inputs based on signature
    inputs = {}
    sig_parts = signature.split("->")
    if len(sig_parts) == 2:
        input_fields = [f.strip() for f in sig_parts[0].split(",")]

        # Map inputs to fields
        if len(input_fields) == 1:
            inputs[input_fields[0]] = input_text or file_content
        elif len(input_fields) == 2 and file_content and input_text:
            inputs[input_fields[0]] = file_content
            inputs[input_fields[1]] = input_text
        else:
            inputs[input_fields[0]] = input_text or file_content

    if verbose:
        console.print(Panel(
            f"[bold]Signature:[/bold] {signature}\n"
            f"[bold]Provider:[/bold] {config.get('provider')}\n"
            f"[bold]Model:[/bold] {config.get('model')}\n"
            f"[bold]Inputs:[/bold] {list(inputs.keys())}",
            title="Running DSPy Signature",
            border_style="cyan"
        ))

    # Run the predictor
    try:
        with console.status("[cyan]Running DSPy signature...[/cyan]"):
            result = predictor(**inputs)

        # Extract output field from signature
        output_field = sig_parts[1].strip() if len(sig_parts) == 2 else "output"
        output_value = getattr(result, output_field, str(result))

        if output_file:
            output_file.write_text(str(output_value))
            console.print(f"[green]Output written to {output_file}[/green]")
        else:
            console.print(Panel(
                str(output_value),
                title=f"[green]Result ({output_field})[/green]",
                border_style="green"
            ))

        if verbose:
            console.print("\n[dim]Full result object:[/dim]")
            console.print(result)

    except Exception as e:
        console.print(f"[red]Error running signature: {e}[/red]")
        raise typer.Exit(1)


@dspy_app.command()
def generate(
    spec_type: str = typer.Argument(..., help="Type of specification to generate: requirement, user-story, task, plan"),
    description: str = typer.Option(..., "--description", "-d", help="Description or context for generation"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Write output to file"),
    format_type: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, ttl, json"),
):
    """
    Generate specifications using DSPy.

    Examples:
        specify dspy generate requirement -d "User authentication system"
        specify dspy generate user-story -d "As a user, I want to login" -o story.md
        specify dspy generate task -d "Implement login API" --format ttl
        specify dspy generate plan -d "Build a REST API for user management"
    """
    check_dspy_available()

    config = load_config()
    if not config:
        console.print("[red]DSPy not configured. Run 'specify dspy configure' first.[/red]")
        raise typer.Exit(1)

    # Define signatures for different spec types
    signatures = {
        "requirement": "description -> requirement_id, title, description, acceptance_criteria, priority",
        "user-story": "description -> story_id, as_a, i_want, so_that, acceptance_criteria",
        "task": "description -> task_id, title, description, steps, estimated_effort, dependencies",
        "plan": "description -> plan_id, title, overview, phases, milestones, risks, success_criteria",
    }

    if spec_type not in signatures:
        console.print(f"[red]Unknown spec type: {spec_type}[/red]")
        console.print(f"[dim]Available: {', '.join(signatures.keys())}[/dim]")
        raise typer.Exit(1)

    # Configure DSPy
    lm = get_configured_lm(config)
    dspy.configure(lm=lm)

    # Create a more sophisticated signature class for structured output
    if spec_type == "requirement":
        class GenerateRequirement(dspy.Signature):
            """Generate a formal software requirement specification."""
            description: str = dspy.InputField(desc="Description of the requirement")
            requirement_id: str = dspy.OutputField(desc="Unique requirement identifier (e.g., REQ-001)")
            title: str = dspy.OutputField(desc="Short title for the requirement")
            requirement_text: str = dspy.OutputField(desc="Formal requirement statement")
            acceptance_criteria: str = dspy.OutputField(desc="List of acceptance criteria")
            priority: str = dspy.OutputField(desc="Priority level: High, Medium, or Low")

        predictor = dspy.Predict(GenerateRequirement)

    elif spec_type == "user-story":
        class GenerateUserStory(dspy.Signature):
            """Generate a user story in standard format."""
            description: str = dspy.InputField(desc="Description or context for the user story")
            story_id: str = dspy.OutputField(desc="Unique story identifier (e.g., US-001)")
            as_a: str = dspy.OutputField(desc="The user role")
            i_want: str = dspy.OutputField(desc="The desired functionality")
            so_that: str = dspy.OutputField(desc="The benefit or value")
            acceptance_criteria: str = dspy.OutputField(desc="List of acceptance criteria")

        predictor = dspy.Predict(GenerateUserStory)

    elif spec_type == "task":
        class GenerateTask(dspy.Signature):
            """Generate a development task specification."""
            description: str = dspy.InputField(desc="Description of the task")
            task_id: str = dspy.OutputField(desc="Unique task identifier (e.g., TASK-001)")
            title: str = dspy.OutputField(desc="Short task title")
            task_description: str = dspy.OutputField(desc="Detailed task description")
            steps: str = dspy.OutputField(desc="Implementation steps")
            estimated_effort: str = dspy.OutputField(desc="Estimated effort (e.g., 2 hours, 1 day)")
            dependencies: str = dspy.OutputField(desc="Dependencies on other tasks or requirements")

        predictor = dspy.Predict(GenerateTask)

    else:  # plan
        class GeneratePlan(dspy.Signature):
            """Generate a project implementation plan."""
            description: str = dspy.InputField(desc="Description of what to plan")
            plan_id: str = dspy.OutputField(desc="Unique plan identifier (e.g., PLAN-001)")
            title: str = dspy.OutputField(desc="Plan title")
            overview: str = dspy.OutputField(desc="Plan overview and objectives")
            phases: str = dspy.OutputField(desc="Implementation phases")
            milestones: str = dspy.OutputField(desc="Key milestones")
            risks: str = dspy.OutputField(desc="Potential risks and mitigations")
            success_criteria: str = dspy.OutputField(desc="Success criteria for the plan")

        predictor = dspy.Predict(GeneratePlan)

    # Run generation
    try:
        with console.status(f"[cyan]Generating {spec_type}...[/cyan]"):
            result = predictor(description=description)

        # Format output based on format_type
        if format_type == "markdown":
            output = format_as_markdown(spec_type, result)
        elif format_type == "ttl":
            output = format_as_ttl(spec_type, result)
        elif format_type == "json":
            output = format_as_json(spec_type, result)
        else:
            output = str(result)

        if output_file:
            output_file.write_text(output)
            console.print(f"[green]Output written to {output_file}[/green]")
        else:
            if format_type == "markdown":
                console.print(Panel(output, title=f"[green]Generated {spec_type.title()}[/green]", border_style="green"))
            elif format_type == "ttl":
                syntax = Syntax(output, "turtle", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"[green]Generated {spec_type.title()} (Turtle)[/green]", border_style="green"))
            elif format_type == "json":
                syntax = Syntax(output, "json", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"[green]Generated {spec_type.title()} (JSON)[/green]", border_style="green"))
            else:
                console.print(output)

    except Exception as e:
        console.print(f"[red]Error generating {spec_type}: {e}[/red]")
        raise typer.Exit(1)


def format_as_markdown(spec_type: str, result) -> str:
    """Format DSPy result as Markdown."""
    if spec_type == "requirement":
        return f"""# {getattr(result, 'title', 'Requirement')}

**ID:** {getattr(result, 'requirement_id', 'REQ-XXX')}
**Priority:** {getattr(result, 'priority', 'Medium')}

## Description

{getattr(result, 'requirement_text', getattr(result, 'description', ''))}

## Acceptance Criteria

{getattr(result, 'acceptance_criteria', '')}
"""
    elif spec_type == "user-story":
        return f"""# User Story: {getattr(result, 'story_id', 'US-XXX')}

**As a** {getattr(result, 'as_a', '')}

**I want** {getattr(result, 'i_want', '')}

**So that** {getattr(result, 'so_that', '')}

## Acceptance Criteria

{getattr(result, 'acceptance_criteria', '')}
"""
    elif spec_type == "task":
        return f"""# {getattr(result, 'title', 'Task')}

**ID:** {getattr(result, 'task_id', 'TASK-XXX')}
**Estimated Effort:** {getattr(result, 'estimated_effort', 'TBD')}

## Description

{getattr(result, 'task_description', getattr(result, 'description', ''))}

## Implementation Steps

{getattr(result, 'steps', '')}

## Dependencies

{getattr(result, 'dependencies', 'None')}
"""
    else:  # plan
        return f"""# {getattr(result, 'title', 'Implementation Plan')}

**ID:** {getattr(result, 'plan_id', 'PLAN-XXX')}

## Overview

{getattr(result, 'overview', '')}

## Phases

{getattr(result, 'phases', '')}

## Milestones

{getattr(result, 'milestones', '')}

## Risks

{getattr(result, 'risks', '')}

## Success Criteria

{getattr(result, 'success_criteria', '')}
"""


def format_as_ttl(spec_type: str, result) -> str:
    """Format DSPy result as RDF Turtle."""
    prefix = """@prefix spec: <http://spec-kit.dev/ontology#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""
    if spec_type == "requirement":
        req_id = getattr(result, 'requirement_id', 'REQ-001').replace('-', '_')
        return prefix + f"""spec:{req_id} a spec:FunctionalRequirement ;
    rdfs:label "{getattr(result, 'title', '')}" ;
    spec:priority "{getattr(result, 'priority', 'Medium')}" ;
    spec:description \"\"\"{getattr(result, 'requirement_text', getattr(result, 'description', ''))}\"\"\" ;
    spec:acceptanceCriteria \"\"\"{getattr(result, 'acceptance_criteria', '')}\"\"\" .
"""
    elif spec_type == "user-story":
        story_id = getattr(result, 'story_id', 'US-001').replace('-', '_')
        return prefix + f"""spec:{story_id} a spec:UserStory ;
    spec:asA "{getattr(result, 'as_a', '')}" ;
    spec:iWant "{getattr(result, 'i_want', '')}" ;
    spec:soThat "{getattr(result, 'so_that', '')}" ;
    spec:acceptanceCriteria \"\"\"{getattr(result, 'acceptance_criteria', '')}\"\"\" .
"""
    elif spec_type == "task":
        task_id = getattr(result, 'task_id', 'TASK-001').replace('-', '_')
        return prefix + f"""spec:{task_id} a spec:Task ;
    rdfs:label "{getattr(result, 'title', '')}" ;
    spec:description \"\"\"{getattr(result, 'task_description', getattr(result, 'description', ''))}\"\"\" ;
    spec:estimatedEffort "{getattr(result, 'estimated_effort', 'TBD')}" ;
    spec:steps \"\"\"{getattr(result, 'steps', '')}\"\"\" .
"""
    else:  # plan
        plan_id = getattr(result, 'plan_id', 'PLAN-001').replace('-', '_')
        return prefix + f"""spec:{plan_id} a spec:Plan ;
    rdfs:label "{getattr(result, 'title', '')}" ;
    spec:overview \"\"\"{getattr(result, 'overview', '')}\"\"\" ;
    spec:phases \"\"\"{getattr(result, 'phases', '')}\"\"\" ;
    spec:milestones \"\"\"{getattr(result, 'milestones', '')}\"\"\" ;
    spec:risks \"\"\"{getattr(result, 'risks', '')}\"\"\" ;
    spec:successCriteria \"\"\"{getattr(result, 'success_criteria', '')}\"\"\" .
"""


def format_as_json(spec_type: str, result) -> str:
    """Format DSPy result as JSON."""
    data = {}

    if spec_type == "requirement":
        data = {
            "id": getattr(result, 'requirement_id', 'REQ-001'),
            "type": "FunctionalRequirement",
            "title": getattr(result, 'title', ''),
            "description": getattr(result, 'requirement_text', getattr(result, 'description', '')),
            "priority": getattr(result, 'priority', 'Medium'),
            "acceptanceCriteria": getattr(result, 'acceptance_criteria', ''),
        }
    elif spec_type == "user-story":
        data = {
            "id": getattr(result, 'story_id', 'US-001'),
            "type": "UserStory",
            "asA": getattr(result, 'as_a', ''),
            "iWant": getattr(result, 'i_want', ''),
            "soThat": getattr(result, 'so_that', ''),
            "acceptanceCriteria": getattr(result, 'acceptance_criteria', ''),
        }
    elif spec_type == "task":
        data = {
            "id": getattr(result, 'task_id', 'TASK-001'),
            "type": "Task",
            "title": getattr(result, 'title', ''),
            "description": getattr(result, 'task_description', getattr(result, 'description', '')),
            "estimatedEffort": getattr(result, 'estimated_effort', 'TBD'),
            "steps": getattr(result, 'steps', ''),
            "dependencies": getattr(result, 'dependencies', ''),
        }
    else:  # plan
        data = {
            "id": getattr(result, 'plan_id', 'PLAN-001'),
            "type": "Plan",
            "title": getattr(result, 'title', ''),
            "overview": getattr(result, 'overview', ''),
            "phases": getattr(result, 'phases', ''),
            "milestones": getattr(result, 'milestones', ''),
            "risks": getattr(result, 'risks', ''),
            "successCriteria": getattr(result, 'success_criteria', ''),
        }

    return json.dumps(data, indent=2)


@dspy_app.command()
def optimize(
    module_file: Path = typer.Argument(..., help="Path to Python file containing DSPy module"),
    train_file: Path = typer.Option(..., "--train", "-t", help="Path to training data (JSON)"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Output path for optimized module"),
    optimizer: str = typer.Option("bootstrap", "--optimizer", help="Optimizer: bootstrap, mipro, copro"),
    max_demos: int = typer.Option(4, "--max-demos", help="Maximum number of demonstrations"),
):
    """
    Optimize a DSPy module with training data.

    The training data should be a JSON file with a list of examples:
    [
        {"input": "...", "output": "..."},
        ...
    ]

    Examples:
        specify dspy optimize my_module.py --train examples.json
        specify dspy optimize my_module.py --train examples.json --optimizer mipro
    """
    check_dspy_available()

    config = load_config()
    if not config:
        console.print("[red]DSPy not configured. Run 'specify dspy configure' first.[/red]")
        raise typer.Exit(1)

    if not module_file.exists():
        console.print(f"[red]Module file not found: {module_file}[/red]")
        raise typer.Exit(1)

    if not train_file.exists():
        console.print(f"[red]Training file not found: {train_file}[/red]")
        raise typer.Exit(1)

    # Load training data
    try:
        with open(train_file) as f:
            train_data = json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON in training file: {e}[/red]")
        raise typer.Exit(1)

    # Configure DSPy
    lm = get_configured_lm(config)
    dspy.configure(lm=lm)

    console.print(Panel(
        f"[bold]Module:[/bold] {module_file}\n"
        f"[bold]Training examples:[/bold] {len(train_data)}\n"
        f"[bold]Optimizer:[/bold] {optimizer}\n"
        f"[bold]Max demos:[/bold] {max_demos}",
        title="Starting Optimization",
        border_style="cyan"
    ))

    # Convert training data to DSPy examples
    examples = [dspy.Example(**ex).with_inputs(*[k for k in ex.keys() if k != 'output']) for ex in train_data]

    console.print(f"[cyan]Loaded {len(examples)} training examples[/cyan]")
    console.print(f"[yellow]Note: Full optimization requires loading the module dynamically.[/yellow]")
    console.print(f"[dim]This is a demonstration of the optimization interface.[/dim]")

    # For a real implementation, we would:
    # 1. Import the module dynamically
    # 2. Create the appropriate optimizer
    # 3. Run optimization
    # 4. Save the optimized module

    if output_file:
        console.print(f"[green]Optimized module would be saved to: {output_file}[/green]")


@dspy_app.command()
def info():
    """
    Show DSPy installation and configuration information.
    """
    table = Table(title="DSPy Information", show_header=True, header_style="bold cyan")
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="white")

    if DSPY_AVAILABLE:
        table.add_row("DSPy Installed", "[green]Yes[/green]")
        table.add_row("DSPy Version", dspy.__version__ if hasattr(dspy, '__version__') else "unknown")
    else:
        table.add_row("DSPy Installed", "[red]No[/red]")

    config = load_config()
    if config:
        table.add_row("Configured", "[green]Yes[/green]")
        table.add_row("Provider", config.get("provider", "not set"))
        table.add_row("Model", config.get("model", "not set"))
        if "base_url" in config:
            table.add_row("Base URL", config.get("base_url"))
    else:
        table.add_row("Configured", "[yellow]No[/yellow]")

    # Check API keys
    table.add_row("", "")
    table.add_row("[bold]API Keys[/bold]", "")
    for provider, info in LM_PROVIDERS.items():
        if info.get("env_var"):
            env_set = os.getenv(info["env_var"])
            status = "[green]Set[/green]" if env_set else "[dim]Not set[/dim]"
            table.add_row(f"  {info['name']}", status)

    console.print(table)

    if not DSPY_AVAILABLE:
        console.print("\n[yellow]Install DSPy with: pip install dspy[/yellow]")


def get_dspy_app():
    """Return the DSPy Typer app for integration with main CLI."""
    return dspy_app
