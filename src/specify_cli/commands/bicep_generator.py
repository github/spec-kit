"""Bicep template generator command for GitHub Copilot integration.

This module provides the main entry point for the Bicep template generation
functionality within the Specify CLI framework.
"""

import asyncio
import logging
import typer
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
import sys

from ..bicep.generator import BicepGenerator
from ..bicep.mcp_client import MCPClient
from ..bicep.orchestrator import GenerationOrchestrator
from ..bicep.analyzer import ProjectAnalyzer
from ..bicep.questionnaire import InteractiveQuestionnaire
from ..bicep.best_practices_validator import BestPracticesValidator
from ..bicep.template_patterns import TemplatePatternGenerator
from ..bicep.arm_validator import ARMTemplateValidator
# Phase 4 imports
from ..bicep.template_orchestrator import TemplateUpdateOrchestrator
from ..bicep.dependency_resolver import DependencyResolver
from ..bicep.architecture_reviewer import ArchitectureReviewer, ReviewScope
from ..bicep.models.template_update import TemplateUpdateManifest

app = typer.Typer(help="Generate Azure Bicep templates from project analysis")
console = Console()
logger = logging.getLogger(__name__)


@app.command()
def generate(
    project_path: Optional[Path] = typer.Argument(None, help="Path to project root for analysis"),
    output_dir: Optional[Path] = typer.Option(None, help="Output directory for generated templates"),
    environments: Optional[List[str]] = typer.Option(None, help="Target deployment environments"),
    region: Optional[str] = typer.Option(None, help="Primary Azure region for deployment"),
    subscription: Optional[str] = typer.Option(None, help="Azure subscription ID"),
    update_only: bool = typer.Option(False, help="Only update existing templates"),
    validate: bool = typer.Option(True, help="Validate templates using ARM"),
    best_practices: bool = typer.Option(True, help="Run best practices validation"),
    use_patterns: bool = typer.Option(True, help="Use architecture patterns when applicable"),
    pattern: Optional[str] = typer.Option(None, help="Force specific architecture pattern"),
    backup: bool = typer.Option(True, help="Create backup files during updates"),
    interactive: bool = typer.Option(True, help="Ask questions for missing information"),
    verbose: bool = typer.Option(False, help="Enable detailed output logging"),
    dry_run: bool = typer.Option(False, help="Show what would be generated without creating files"),
):
    """Generate Azure Bicep templates from project analysis."""
    
    # Set up logging
    if verbose:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Resolve project path
    if project_path is None:
        project_path = Path.cwd()
    else:
        project_path = project_path.resolve()
    
    if not project_path.exists() or not project_path.is_dir():
        console.print(f"[red]Error:[/red] Project path does not exist: {project_path}")
        raise typer.Exit(1)
    
    # Resolve output directory
    if output_dir is None:
        output_dir = project_path / "infrastructure"
    
    console.print(Panel.fit(
        f"🚀 Azure Bicep Template Generator\n\n"
        f"Project: {project_path.name}\n"
        f"Path: {project_path}\n"
        f"Output: {output_dir}",
        title="Bicep Generator",
        border_style="blue"
    ))
    
    if dry_run:
        console.print("[yellow]Running in dry-run mode - no files will be created[/yellow]\n")
    
    try:
        # Run the async generation process
        asyncio.run(_run_generation(
            project_path=project_path,
            output_dir=output_dir,
            environments=environments,
            region=region,
            subscription=subscription,
            update_only=update_only,
            validate=validate,
            best_practices=best_practices,
            use_patterns=use_patterns,
            pattern=pattern,
            backup=backup,
            interactive=interactive,
            verbose=verbose,
            dry_run=dry_run
        ))
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Generation cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"\n[red]Error during generation:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


async def _run_generation(
    project_path: Path,
    output_dir: Path,
    environments: Optional[List[str]],
    region: Optional[str],
    subscription: Optional[str],
    update_only: bool,
    validate: bool,
    best_practices: bool,
    use_patterns: bool,
    pattern: Optional[str],
    backup: bool,
    interactive: bool,
    verbose: bool,
    dry_run: bool
) -> None:
    """Run the async generation process."""
    
    # Initialize MCP client for Azure resource information
    mcp_client = None
    try:
        if verbose:
            console.print("[dim]Initializing Azure MCP client...[/dim]")
        mcp_client = MCPClient()
        await mcp_client.connect()
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not connect to Azure MCP server: {e}")
        console.print("Continuing without real-time Azure schema validation...")
    
    try:
        # Initialize generator
        generator = BicepGenerator(
            project_path=project_path,
            output_path=output_dir,
            mcp_client=mcp_client
        )
        
        # Prepare user requirements
        user_requirements = {}
        if not interactive:
            # Build requirements from command line args
            if environments:
                user_requirements["environments"] = environments
            if region:
                user_requirements["primary_location"] = region
            # Set other defaults
            user_requirements["project_confirmation"] = True
            user_requirements["final_confirmation"] = True
        
        # Generate templates with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Add progress tasks
            analysis_task = progress.add_task("Analyzing project structure...", total=None)
            
            if not dry_run:
                # Actually generate templates
                output_files = await generator.generate_templates(
                    interactive=interactive,
                    user_requirements=user_requirements if not interactive else None
                )
                
                progress.update(analysis_task, description="✅ Analysis complete")
                generation_task = progress.add_task("Generating templates...", total=None)
                progress.update(generation_task, description="✅ Templates generated")
                
                # Show results
                _show_generation_results(output_files, generator.deployment_config)
                
                # Show next steps
                _show_next_steps(output_dir, generator.deployment_config)
                
            else:
                # Dry run - just show what would be generated
                progress.update(analysis_task, description="✅ Analysis complete (dry run)")
                
                # Run analysis only
                await generator._analyze_project()
                
                if interactive:
                    await generator._collect_user_requirements_interactive()
                else:
                    generator.user_requirements = user_requirements
                
                generator._create_deployment_configuration()
                
                # Show what would be generated
                _show_dry_run_results(generator, output_dir)
    
    finally:
        if mcp_client:
            await mcp_client.disconnect()


def _show_generation_results(output_files: dict, deployment_config) -> None:
    """Show the results of template generation."""
    console.print("\n✅ Template generation completed successfully!\n")
    
    # Create results table
    table = Table(title="Generated Files", show_header=True, header_style="bold blue")
    table.add_column("Type", style="cyan")
    table.add_column("File", style="green")
    table.add_column("Size", justify="right", style="magenta")
    
    for file_type, file_path in output_files.items():
        if file_path.exists():
            size = file_path.stat().st_size
            size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
            table.add_row(file_type.title().replace('-', ' '), str(file_path.name), size_str)
    
    console.print(table)
    
    # Show environment summary
    if deployment_config:
        console.print(f"\n📋 Configured Environments:")
        for env_name, env_config in deployment_config.environments.items():
            console.print(f"  • {env_name.title()}: {env_config.location}")


def _show_next_steps(output_dir: Path, deployment_config) -> None:
    """Show next steps for the user."""
    console.print(Panel.fit(
        "📝 Next Steps:\n\n"
        f"1. Review generated templates in: {output_dir}\n"
        "2. Customize parameter files for your environments\n"
        "3. Set up secure parameters (passwords) in Azure Key Vault\n"
        "4. Test deployment with: ./deploy.ps1 -Environment dev -ResourceGroupName <rg-name>\n"
        "5. Set up CI/CD pipeline for automated deployments\n\n"
        f"📚 Documentation: {output_dir / 'README.md'}",
        title="What's Next?",
        border_style="green"
    ))


def _show_dry_run_results(generator: BicepGenerator, output_dir: Path) -> None:
    """Show what would be generated in dry run mode."""
    console.print("\n🔍 Dry Run Results - Files that would be generated:\n")
    
    analysis = generator.analysis_result
    config = generator.deployment_config
    
    # Project analysis summary
    console.print(f"📊 Project Analysis:")
    console.print(f"  • Type: {analysis.project_type.value}")
    console.print(f"  • Frameworks: {', '.join([f.value for f in analysis.detected_frameworks])}")
    console.print(f"  • Confidence: {analysis.confidence_score:.1%}")
    console.print(f"  • Total Files: {analysis.total_files}")
    
    # Resource requirements
    console.print(f"\n🏗️  Resource Requirements:")
    for req in analysis.resource_requirements[:5]:  # Show top 5
        priority_emoji = "🔴" if req.priority.name == "HIGH" else "🟡" if req.priority.name == "MEDIUM" else "🟢"
        console.print(f"  {priority_emoji} {req.resource_type.value.replace('_', ' ').title()}: {req.justification}")
    
    if len(analysis.resource_requirements) > 5:
        console.print(f"  ... and {len(analysis.resource_requirements) - 5} more resources")
    
    # Files that would be generated
    console.print(f"\n📁 Files that would be created in {output_dir}:")
    files_to_create = [
        "main.bicep",
        "README.md",
        "deploy.ps1", 
        "deploy.sh"
    ]
    
    if config:
        for env_name in config.environments:
            files_to_create.append(f"main.{env_name}.bicepparam")
    
    for file_name in files_to_create:
        console.print(f"  📄 {file_name}")
    
    console.print(f"\n[dim]Run without --dry-run to generate actual files[/dim]")


# =====================================================
# PHASE 4 ADVANCED COMMANDS
# =====================================================

@app.command()
def update(
    project_path: Optional[Path] = typer.Argument(None, help="Path to project root"),
    manifest_path: Optional[Path] = typer.Option(None, help="Path to template update manifest"),
    force: bool = typer.Option(False, help="Force update regardless of changes"),
    environments: Optional[List[str]] = typer.Option(None, help="Target environments to update"),
    strategy: str = typer.Option("incremental", help="Update strategy (conservative, incremental, aggressive)"),
    verbose: bool = typer.Option(False, help="Enable detailed output logging"),
):
    """Update existing templates based on project changes (Phase 4)."""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    if not project_path:
        project_path = Path.cwd()
    
    console.print(Panel("🔄 Template Update Orchestration", style="blue bold"))
    
    try:
        # Initialize components
        template_manager = None  # Would be properly initialized
        project_analyzer = ProjectAnalyzer()
        bicep_generator = BicepGenerator(template_manager, None, None)
        arm_validator = ARMTemplateValidator()
        best_practices_validator = BestPracticesValidator()
        
        orchestrator = TemplateUpdateOrchestrator(
            template_manager,
            project_analyzer,
            bicep_generator,
            arm_validator,
            best_practices_validator
        )
        
        # Run update orchestration
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Orchestrating template updates...", total=None)
            
            manifest, messages = asyncio.run(orchestrator.orchestrate_update(
                project_path=project_path,
                manifest_path=manifest_path,
                force_update=force,
                target_environments=environments
            ))
        
        # Display results
        for message in messages:
            console.print(f"  {message}")
        
        console.print("\n✅ Template update orchestration completed successfully!")
        
    except Exception as e:
        console.print(f"\n❌ Template update failed: {str(e)}", style="bold red")
        raise typer.Exit(1)


@app.command()
def dependencies(
    project_path: Optional[Path] = typer.Argument(None, help="Path to project root"),
    resolve_conflicts: bool = typer.Option(False, help="Resolve dependency conflicts"),
    show_graph: bool = typer.Option(True, help="Show dependency graph"),
    optimize: bool = typer.Option(False, help="Optimize dependency graph"),
    verbose: bool = typer.Option(False, help="Enable detailed output logging"),
):
    """Analyze and resolve template dependencies (Phase 4)."""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    if not project_path:
        project_path = Path.cwd()
    
    console.print(Panel("🔗 Dependency Analysis", style="blue bold"))
    
    try:
        resolver = DependencyResolver()
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Analyzing dependencies...", total=None)
            
            # This would be properly implemented with actual resources
            resources = []  # Load from project analysis
            graph = resolver.analyze_dependencies(resources)
        
        # Show results
        console.print(f"\n📊 Dependency Analysis Results:")
        console.print(f"  • Nodes: {len(graph.nodes)}")
        console.print(f"  • Dependencies: {sum(len(deps) for deps in graph.edges.values())}")
        
        # Detect cycles
        cycles = resolver.detect_cycles(graph)
        if cycles:
            console.print(f"  ⚠️  Circular dependencies detected: {len(cycles)}")
            
            if resolve_conflicts:
                resolutions = resolver.resolve_cycles(graph, cycles)
                console.print("\n🔧 Resolution Strategies:")
                for resolution in resolutions:
                    console.print(f"  Cycle: {' -> '.join(resolution['cycle'])}")
                    if resolution['recommended_action']:
                        console.print(f"    Recommended: {resolution['recommended_action']['description']}")
        
        # Show deployment order
        deployment_order = resolver.calculate_deployment_order(graph)
        console.print(f"\n📋 Deployment Order ({len(deployment_order)} groups):")
        for i, group in enumerate(deployment_order, 1):
            console.print(f"  Group {i}: {', '.join(group)}")
        
        console.print("\n✅ Dependency analysis completed successfully!")
        
    except Exception as e:
        console.print(f"\n❌ Dependency analysis failed: {str(e)}", style="bold red")
        raise typer.Exit(1)


@app.command()
def sync(
    project_path: Optional[Path] = typer.Argument(None, help="Path to project root"),
    source_env: str = typer.Option("prod", help="Source environment to sync from"),
    target_envs: List[str] = typer.Option(..., help="Target environments to sync to"),
    manifest_path: Optional[Path] = typer.Option(None, help="Path to template update manifest"),
    dry_run: bool = typer.Option(False, help="Show what would be synchronized"),
    verbose: bool = typer.Option(False, help="Enable detailed output logging"),
):
    """Synchronize templates across environments (Phase 4)."""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    if not project_path:
        project_path = Path.cwd()
    
    console.print(Panel("🔄 Environment Synchronization", style="blue bold"))
    
    try:
        # Load or create manifest
        if manifest_path and manifest_path.exists():
            with open(manifest_path, 'r') as f:
                import json
                manifest_data = json.load(f)
            manifest = TemplateUpdateManifest(**manifest_data)
        else:
            manifest = TemplateUpdateManifest(
                project_path=project_path,
                project_name=project_path.name
            )
        
        # Initialize orchestrator
        orchestrator = TemplateUpdateOrchestrator(None, None, None, None, None)
        
        if dry_run:
            console.print(f"\n🔍 Dry Run - Would synchronize:")
            console.print(f"  From: {source_env}")
            console.print(f"  To: {', '.join(target_envs)}")
            console.print(f"  Templates: {len(manifest.templates)} versions available")
        else:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Synchronizing environments...", total=None)
                
                sync_results = asyncio.run(orchestrator.synchronize_environments(
                    manifest, source_env, target_envs
                ))
            
            console.print(f"\n📊 Synchronization Results:")
            for env, success in sync_results.items():
                status = "✅" if success else "❌"
                console.print(f"  {status} {env}")
        
        console.print("\n✅ Environment synchronization completed successfully!")
        
    except Exception as e:
        console.print(f"\n❌ Environment synchronization failed: {str(e)}", style="bold red")
        raise typer.Exit(1)


@app.command()
def review(
    project_path: Optional[Path] = typer.Argument(None, help="Path to project root"),
    scope: str = typer.Option("all", help="Review scope (compliance, cost, performance, security, reliability, all)"),
    output_format: str = typer.Option("table", help="Output format (table, json, yaml)"),
    save_report: Optional[Path] = typer.Option(None, help="Save detailed report to file"),
    verbose: bool = typer.Option(False, help="Enable detailed output logging"),
):
    """Conduct architecture review and optimization analysis (Phase 4)."""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    if not project_path:
        project_path = Path.cwd()
    
    console.print(Panel("🏗️ Architecture Review", style="blue bold"))
    
    try:
        # Initialize components
        best_practices_validator = BestPracticesValidator()
        reviewer = ArchitectureReviewer(best_practices_validator)
        
        # Convert scope string to enum
        review_scope = ReviewScope(scope.lower())
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task(f"Conducting {scope} review...", total=None)
            
            # This would load actual templates from the project
            templates = {}  # Load from project
            parameters = {}  # Load parameters
            
            result = asyncio.run(reviewer.conduct_review(
                project_path=project_path,
                templates=templates,
                parameters=parameters,
                scope=review_scope
            ))
        
        # Display results
        console.print(f"\n📊 Architecture Review Results:")
        console.print(f"  • Overall Score: {result.overall_score:.1f}/100")
        console.print(f"  • Compliance: {result.compliance_score:.1f}/100")
        console.print(f"  • Cost Efficiency: {result.cost_efficiency_score:.1f}/100")
        console.print(f"  • Performance: {result.performance_score:.1f}/100")
        console.print(f"  • Security: {result.security_score:.1f}/100")
        console.print(f"  • Reliability: {result.reliability_score:.1f}/100")
        
        # Show recommendations
        if result.recommendations:
            console.print(f"\n🔧 Top Recommendations:")
            top_recs = result.get_prioritized_recommendations()[:5]
            for i, rec in enumerate(top_recs, 1):
                priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                emoji = priority_emoji.get(rec.priority.value, "🔵")
                console.print(f"  {i}. {emoji} {rec.title}")
                console.print(f"     Impact: {rec.impact} | Effort: {rec.effort}")
                if rec.estimated_savings:
                    console.print(f"     Potential savings: ${rec.estimated_savings:.2f}/month")
        
        # Show cost analysis if available
        if result.cost_analysis:
            console.print(f"\n💰 Cost Analysis:")
            console.print(f"  • Estimated Monthly Cost: ${result.cost_analysis.estimated_monthly_cost:.2f}")
            console.print(f"  • Potential Savings: ${result.cost_analysis.get_total_savings():.2f}")
            console.print(f"  • Cost Alerts: {len(result.cost_analysis.cost_alerts)}")
        
        # Save detailed report if requested
        if save_report:
            with open(save_report, 'w') as f:
                import json
                json.dump(result.__dict__, f, indent=2, default=str)
            console.print(f"\n💾 Detailed report saved to: {save_report}")
        
        console.print("\n✅ Architecture review completed successfully!")
        
    except Exception as e:
        console.print(f"\n❌ Architecture review failed: {str(e)}", style="bold red")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()