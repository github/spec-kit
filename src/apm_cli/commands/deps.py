"""APM dependency management commands."""

import sys
import shutil
import click
from pathlib import Path
from typing import List, Optional, Dict, Any

# Import existing APM components
from ..models.apm_package import APMPackage, ValidationResult, validate_apm_package
from ..utils.console import _rich_success, _rich_error, _rich_info, _rich_warning

# Import APM dependency system components (with fallback)
from ..deps.github_downloader import GitHubPackageDownloader
from ..deps.apm_resolver import APMDependencyResolver



@click.group(help="🔗 Manage APM package dependencies")
def deps():
    """APM dependency management commands."""
    pass


@deps.command(name="list", help="📋 List installed APM dependencies")
def list_packages():
    """Show all installed APM dependencies with context files and agent workflows."""
    try:
        # Import Rich components with fallback
        from rich.table import Table
        from rich.console import Console
        console = Console()
        has_rich = True
    except ImportError:
        has_rich = False
        console = None
    
    try:
        project_root = Path(".")
        apm_modules_path = project_root / "apm_modules"
        
        # Check if apm_modules exists
        if not apm_modules_path.exists():
            if has_rich:
                console.print("💡 No APM dependencies installed yet", style="cyan")
                console.print("Run 'specify apm install' to install dependencies from apm.yml", style="dim")
            else:
                click.echo("💡 No APM dependencies installed yet")
                click.echo("Run 'specify apm install' to install dependencies from apm.yml")
            return
        
        # Load project dependencies to check for orphaned packages
        declared_deps = set()
        try:
            apm_yml_path = project_root / "apm.yml"
            if apm_yml_path.exists():
                project_package = APMPackage.from_apm_yml(apm_yml_path)
                for dep in project_package.get_apm_dependencies():
                    declared_deps.add(dep.repo_url)
        except Exception:
            pass  # Continue without orphan detection if apm.yml parsing fails
        
        # Scan for installed packages in org-namespaced structure
        installed_packages = []
        orphaned_packages = []
        for org_dir in apm_modules_path.iterdir():
            if org_dir.is_dir() and not org_dir.name.startswith('.'):
                for package_dir in org_dir.iterdir():
                    if package_dir.is_dir() and not package_dir.name.startswith('.'):
                        try:
                            # org/repo format
                            org_repo_name = f"{org_dir.name}/{package_dir.name}"
                            
                            # Try to load package metadata
                            apm_yml_path = package_dir / "apm.yml"
                            if apm_yml_path.exists():
                                package = APMPackage.from_apm_yml(apm_yml_path)
                                # Count context files and workflows separately
                                context_count, workflow_count = _count_package_files(package_dir)
                                
                                # Check if this package is orphaned
                                is_orphaned = org_repo_name not in declared_deps
                                if is_orphaned:
                                    orphaned_packages.append(org_repo_name)
                                
                                installed_packages.append({
                                    'name': org_repo_name,
                                    'version': package.version or 'unknown', 
                                    'source': 'orphaned' if is_orphaned else 'github',
                                    'context': context_count,
                                    'workflows': workflow_count,
                                    'path': str(package_dir),
                                    'is_orphaned': is_orphaned
                                })
                            else:
                                # Package without apm.yml - show basic info
                                context_count, workflow_count = _count_package_files(package_dir)
                                is_orphaned = True  # Assume orphaned if no apm.yml
                                orphaned_packages.append(org_repo_name)
                                
                                installed_packages.append({
                                    'name': org_repo_name,
                                    'version': 'unknown',
                                    'source': 'orphaned',
                                    'context': context_count,
                                    'workflows': workflow_count,
                                    'path': str(package_dir),
                                    'is_orphaned': is_orphaned
                                })
                        except Exception as e:
                            click.echo(f"⚠️ Warning: Failed to read package {org_dir.name}/{package_dir.name}: {e}")
        
        if not installed_packages:
            if has_rich:
                console.print("💡 apm_modules/ directory exists but contains no valid packages", style="cyan")
            else:
                click.echo("💡 apm_modules/ directory exists but contains no valid packages")
            return
        
        # Display packages in table format
        if has_rich:
            table = Table(title="📋 APM Dependencies", show_header=True, header_style="bold cyan")
            table.add_column("Package", style="bold white")
            table.add_column("Version", style="yellow") 
            table.add_column("Source", style="blue")
            table.add_column("Context", style="green")
            table.add_column("Workflows", style="magenta")
            
            for pkg in installed_packages:
                table.add_row(
                    pkg['name'],
                    pkg['version'],
                    pkg['source'],
                    f"{pkg['context']} files",
                    f"{pkg['workflows']} workflows"
                )
            
            console.print(table)
            
            # Show orphaned packages warning
            if orphaned_packages:
                console.print(f"\n⚠️  {len(orphaned_packages)} orphaned package(s) found (not in apm.yml):", style="yellow")
                for pkg in orphaned_packages:
                    console.print(f"  • {pkg}", style="dim yellow")
                console.print("\n💡 Run 'specify apm prune' to remove orphaned packages", style="cyan")
        else:
            # Fallback text table
            click.echo("📋 APM Dependencies:")
            click.echo("┌─────────────────────┬─────────┬──────────────┬─────────────┬─────────────┐")
            click.echo("│ Package             │ Version │ Source       │ Context     │ Workflows   │")
            click.echo("├─────────────────────┼─────────┼──────────────┼─────────────┼─────────────┤")
            
            for pkg in installed_packages:
                name = pkg['name'][:19].ljust(19)
                version = pkg['version'][:7].ljust(7)
                source = pkg['source'][:12].ljust(12)
                context = f"{pkg['context']} files".ljust(11)
                workflows = f"{pkg['workflows']} wf".ljust(11)
                click.echo(f"│ {name} │ {version} │ {source} │ {context} │ {workflows} │")
            
            click.echo("└─────────────────────┴─────────┴──────────────┴─────────────┴─────────────┘")
            
            # Show orphaned packages warning
            if orphaned_packages:
                click.echo(f"\n⚠️  {len(orphaned_packages)} orphaned package(s) found (not in apm.yml):")
                for pkg in orphaned_packages:
                    click.echo(f"  • {pkg}")
                click.echo("\n💡 Run 'specify apm prune' to remove orphaned packages")

    except Exception as e:
        _rich_error(f"Error listing dependencies: {e}")
        sys.exit(1)


@deps.command(help="🌳 Show dependency tree structure")  
def tree():
    """Display dependencies in hierarchical tree format showing context and workflows."""
    try:
        # Import Rich components with fallback
        from rich.tree import Tree
        from rich.console import Console
        console = Console()
        has_rich = True
    except ImportError:
        has_rich = False
        console = None
    
    try:
        project_root = Path(".")
        apm_modules_path = project_root / "apm_modules"
        
        # Load project info
        project_name = "my-project"
        try:
            apm_yml_path = project_root / "apm.yml"
            if apm_yml_path.exists():
                root_package = APMPackage.from_apm_yml(apm_yml_path)
                project_name = root_package.name
        except Exception:
            pass
        
        if has_rich:
            # Create Rich tree
            root_tree = Tree(f"[bold cyan]{project_name}[/bold cyan] (local)")
            
            # Check if apm_modules exists
            if not apm_modules_path.exists():
                root_tree.add("[dim]No dependencies installed[/dim]")
            else:
                # Add each dependency as a branch
                for package_dir in apm_modules_path.iterdir():
                    if package_dir.is_dir():
                        try:
                            package_info = _get_package_display_info(package_dir)
                            branch = root_tree.add(f"[green]{package_info['display_name']}[/green]")
                            
                            # Add context files and workflows as sub-items
                            context_files = _get_detailed_context_counts(package_dir)
                            workflow_count = _count_workflows(package_dir)
                            
                            # Show context files by type
                            for context_type, count in context_files.items():
                                if count > 0:
                                    branch.add(f"[dim]{count} {context_type}[/dim]")
                            
                            # Show workflows
                            if workflow_count > 0:
                                branch.add(f"[bold magenta]{workflow_count} agent workflows[/bold magenta]")
                            
                            if not any(count > 0 for count in context_files.values()) and workflow_count == 0:
                                branch.add("[dim]no context or workflows[/dim]")
                                
                        except Exception as e:
                            branch = root_tree.add(f"[red]{package_dir.name}[/red] [dim](error loading)[/dim]")
            
            console.print(root_tree)
            
        else:
            # Fallback text tree
            click.echo(f"{project_name} (local)")
            
            if not apm_modules_path.exists():
                click.echo("└── No dependencies installed")
                return
            
            package_dirs = [d for d in apm_modules_path.iterdir() if d.is_dir()]
            
            for i, package_dir in enumerate(package_dirs):
                is_last = i == len(package_dirs) - 1
                prefix = "└── " if is_last else "├── "
                
                try:
                    package_info = _get_package_display_info(package_dir)
                    click.echo(f"{prefix}{package_info['display_name']}")
                    
                    # Add context files and workflows
                    context_files = _get_detailed_context_counts(package_dir)
                    workflow_count = _count_workflows(package_dir)
                    sub_prefix = "    " if is_last else "│   "
                    
                    items_shown = False
                    for context_type, count in context_files.items():
                        if count > 0:
                            click.echo(f"{sub_prefix}├── {count} {context_type}")
                            items_shown = True
                    
                    if workflow_count > 0:
                        click.echo(f"{sub_prefix}├── {workflow_count} agent workflows")
                        items_shown = True
                            
                    if not items_shown:
                        click.echo(f"{sub_prefix}└── no context or workflows")
                        
                except Exception as e:
                    click.echo(f"{prefix}{package_dir.name} (error loading)")

    except Exception as e:
        _rich_error(f"Error showing dependency tree: {e}")
        sys.exit(1)


@deps.command(help="🧹 Remove all APM dependencies")
def clean():
    """Remove entire apm_modules/ directory."""
    project_root = Path(".")
    apm_modules_path = project_root / "apm_modules"
    
    if not apm_modules_path.exists():
        _rich_info("No apm_modules/ directory found - already clean")
        return
    
    # Show what will be removed
    package_count = len([d for d in apm_modules_path.iterdir() if d.is_dir()])
    
    _rich_warning(f"This will remove the entire apm_modules/ directory ({package_count} packages)")
    
    # Confirmation prompt
    try:
        from rich.prompt import Confirm
        confirm = Confirm.ask("Continue?")
    except ImportError:
        confirm = click.confirm("Continue?")
    
    if not confirm:
        _rich_info("Operation cancelled")
        return
    
    try:
        shutil.rmtree(apm_modules_path)
        _rich_success("Successfully removed apm_modules/ directory")
    except Exception as e:
        _rich_error(f"Error removing apm_modules/: {e}")
        sys.exit(1)


@deps.command(help="🔄 Update APM dependencies")
@click.argument('package', required=False)
def update(package: Optional[str]):
    """Update specific package or all if no package specified."""
    
    project_root = Path(".")
    apm_modules_path = project_root / "apm_modules"
    
    if not apm_modules_path.exists():
        _rich_info("No apm_modules/ directory found - no packages to update")
        return
    
    # Get project dependencies to validate updates
    try:
        apm_yml_path = project_root / "apm.yml"
        if not apm_yml_path.exists():
            _rich_error("No apm.yml found in current directory")
            return
            
        project_package = APMPackage.from_apm_yml(apm_yml_path)
        project_deps = project_package.get_apm_dependencies()
        
        if not project_deps:
            _rich_info("No APM dependencies defined in apm.yml")
            return
            
    except Exception as e:
        _rich_error(f"Error reading apm.yml: {e}")
        return
    
    if package:
        # Update specific package
        _update_single_package(package, project_deps, apm_modules_path)
    else:
        # Update all packages
        _update_all_packages(project_deps, apm_modules_path)


@deps.command(help="ℹ️ Show detailed package information")
@click.argument('package', required=True)
def info(package: str):
    """Show detailed information about a specific package including context files and workflows."""
    project_root = Path(".")
    apm_modules_path = project_root / "apm_modules"
    
    if not apm_modules_path.exists():
        _rich_error("No apm_modules/ directory found")
        _rich_info("Run 'specify apm install' to install dependencies first")
        sys.exit(1)
    
    # Find the package directory
    package_path = None
    for package_dir in apm_modules_path.iterdir():
        if package_dir.is_dir() and package_dir.name == package:
            package_path = package_dir
            break
    
    if not package_path:
        _rich_error(f"Package '{package}' not found in apm_modules/")
        _rich_info("Available packages:")
        
        for package_dir in apm_modules_path.iterdir():
            if package_dir.is_dir():
                click.echo(f"  - {package_dir.name}")
        sys.exit(1)
    
    try:
        # Load package information
        package_info = _get_detailed_package_info(package_path)
        
        # Display with Rich panel if available
        try:
            from rich.panel import Panel
            from rich.console import Console
            from rich.text import Text
            console = Console()
            
            content_lines = []
            content_lines.append(f"[bold]Name:[/bold] {package_info['name']}")
            content_lines.append(f"[bold]Version:[/bold] {package_info['version']}")
            content_lines.append(f"[bold]Description:[/bold] {package_info['description']}")
            content_lines.append(f"[bold]Author:[/bold] {package_info['author']}")
            content_lines.append(f"[bold]Source:[/bold] {package_info['source']}")
            content_lines.append(f"[bold]Install Path:[/bold] {package_info['install_path']}")
            content_lines.append("")
            content_lines.append("[bold]Context Files:[/bold]")
            
            for context_type, count in package_info['context_files'].items():
                if count > 0:
                    content_lines.append(f"  • {count} {context_type}")
            
            if not any(count > 0 for count in package_info['context_files'].values()):
                content_lines.append("  • No context files found")
                
            content_lines.append("")
            content_lines.append("[bold]Agent Workflows:[/bold]")
            if package_info['workflows'] > 0:
                content_lines.append(f"  • {package_info['workflows']} executable workflows")
            else:
                content_lines.append("  • No agent workflows found")
            
            content = "\n".join(content_lines)
            panel = Panel(content, title=f"ℹ️ Package Info: {package}", border_style="cyan")
            console.print(panel)
            
        except ImportError:
            # Fallback text display
            click.echo(f"ℹ️ Package Info: {package}")
            click.echo("=" * 40)
            click.echo(f"Name: {package_info['name']}")
            click.echo(f"Version: {package_info['version']}")
            click.echo(f"Description: {package_info['description']}")
            click.echo(f"Author: {package_info['author']}")
            click.echo(f"Source: {package_info['source']}")
            click.echo(f"Install Path: {package_info['install_path']}")
            click.echo("")
            click.echo("Context Files:")
            
            for context_type, count in package_info['context_files'].items():
                if count > 0:
                    click.echo(f"  • {count} {context_type}")
            
            if not any(count > 0 for count in package_info['context_files'].values()):
                click.echo("  • No context files found")
                
            click.echo("")
            click.echo("Agent Workflows:")
            if package_info['workflows'] > 0:
                click.echo(f"  • {package_info['workflows']} executable workflows")
            else:
                click.echo("  • No agent workflows found")
    
    except Exception as e:
        _rich_error(f"Error reading package information: {e}")
        sys.exit(1)


# Helper functions

def _count_package_files(package_path: Path) -> tuple[int, int]:
    """Count context files and workflows in a package.
    
    Returns:
        tuple: (context_count, workflow_count)
    """
    apm_dir = package_path / ".apm"
    if not apm_dir.exists():
        # Also check root directory for .prompt.md files
        workflow_count = len(list(package_path.glob("*.prompt.md")))
        return 0, workflow_count
    
    context_count = 0
    context_dirs = ['instructions', 'chatmodes', 'contexts']
    
    for context_dir in context_dirs:
        context_path = apm_dir / context_dir
        if context_path.exists() and context_path.is_dir():
            context_count += len(list(context_path.glob("*.md")))
    
    # Count workflows in both .apm/prompts and root directory
    workflow_count = 0
    prompts_path = apm_dir / "prompts"
    if prompts_path.exists() and prompts_path.is_dir():
        workflow_count += len(list(prompts_path.glob("*.prompt.md")))
    
    # Also check root directory for .prompt.md files
    workflow_count += len(list(package_path.glob("*.prompt.md")))
    
    return context_count, workflow_count


def _count_workflows(package_path: Path) -> int:
    """Count agent workflows (.prompt.md files) in a package."""
    _, workflow_count = _count_package_files(package_path)
    return workflow_count


def _get_detailed_context_counts(package_path: Path) -> Dict[str, int]:
    """Get detailed context file counts by type."""
    apm_dir = package_path / ".apm"
    if not apm_dir.exists():
        return {'instructions': 0, 'chatmodes': 0, 'contexts': 0}
    
    counts = {}
    context_types = {
        'instructions': ['instructions.md'],
        'chatmodes': ['chatmode.md'], 
        'contexts': ['context.md', 'memory.md']
    }
    
    for context_type, extensions in context_types.items():
        count = 0
        context_path = apm_dir / context_type
        if context_path.exists() and context_path.is_dir():
            for ext in extensions:
                count += len(list(context_path.glob(f"*.{ext}")))
        counts[context_type] = count
    
    return counts


def _get_package_display_info(package_path: Path) -> Dict[str, str]:
    """Get package display information."""
    try:
        apm_yml_path = package_path / "apm.yml"
        if apm_yml_path.exists():
            package = APMPackage.from_apm_yml(apm_yml_path)
            version_info = f"@{package.version}" if package.version else "@unknown"
            return {
                'display_name': f"{package.name}{version_info}",
                'name': package.name,
                'version': package.version or 'unknown'
            }
        else:
            return {
                'display_name': f"{package_path.name}@unknown",
                'name': package_path.name,
                'version': 'unknown'
            }
    except Exception:
        return {
            'display_name': f"{package_path.name}@error",
            'name': package_path.name,
            'version': 'error'
        }


def _get_detailed_package_info(package_path: Path) -> Dict[str, Any]:
    """Get detailed package information for the info command."""
    try:
        apm_yml_path = package_path / "apm.yml"
        if apm_yml_path.exists():
            package = APMPackage.from_apm_yml(apm_yml_path)
            context_count, workflow_count = _count_package_files(package_path)
            return {
                'name': package.name,
                'version': package.version or 'unknown',
                'description': package.description or 'No description',
                'author': package.author or 'Unknown',
                'source': package.source or 'local',
                'install_path': str(package_path.resolve()),
                'context_files': _get_detailed_context_counts(package_path),
                'workflows': workflow_count
            }
        else:
            context_count, workflow_count = _count_package_files(package_path)
            return {
                'name': package_path.name,
                'version': 'unknown',
                'description': 'No apm.yml found',
                'author': 'Unknown',
                'source': 'unknown',
                'install_path': str(package_path.resolve()),
                'context_files': _get_detailed_context_counts(package_path),
                'workflows': workflow_count
            }
    except Exception as e:
        return {
            'name': package_path.name,
            'version': 'error',
            'description': f'Error loading package: {e}',
            'author': 'Unknown',
            'source': 'unknown',
            'install_path': str(package_path.resolve()),
            'context_files': {'instructions': 0, 'chatmodes': 0, 'contexts': 0},
            'workflows': 0
        }


def _update_single_package(package_name: str, project_deps: List, apm_modules_path: Path):
    """Update a specific package."""
    # Find the dependency reference for this package
    target_dep = None
    for dep in project_deps:
        if dep.get_display_name() == package_name or dep.repo_url.split('/')[-1] == package_name:
            target_dep = dep
            break
    
    if not target_dep:
        _rich_error(f"Package '{package_name}' not found in apm.yml dependencies")
        return
    
    # Find the installed package directory
    package_dir = None
    if target_dep.alias:
        package_dir = apm_modules_path / target_dep.alias
    else:
        package_dir = apm_modules_path / package_name
        
    if not package_dir.exists():
        _rich_error(f"Package '{package_name}' not installed in apm_modules/")
        _rich_info(f"Run 'apm install' to install it first")
        return
    
    try:
        downloader = GitHubPackageDownloader()
        _rich_info(f"Updating {target_dep.repo_url}...")
        
        # Download latest version
        package_info = downloader.download_package(str(target_dep), package_dir)
        
        _rich_success(f"✅ Updated {target_dep.repo_url}")
        
    except Exception as e:
        _rich_error(f"Failed to update {package_name}: {e}")


def _update_all_packages(project_deps: List, apm_modules_path: Path):
    """Update all packages."""
    if not project_deps:
        _rich_info("No APM dependencies to update")
        return
        
    _rich_info(f"Updating {len(project_deps)} APM dependencies...")
    
    downloader = GitHubPackageDownloader()
    updated_count = 0
    
    for dep in project_deps:
        # Determine package directory
        if dep.alias:
            package_dir = apm_modules_path / dep.alias
        else:
            package_dir = apm_modules_path / dep.repo_url.split('/')[-1]
            
        if not package_dir.exists():
            _rich_warning(f"⚠️ {dep.repo_url} not installed - skipping")
            continue
            
        try:
            _rich_info(f"  Updating {dep.repo_url}...")
            package_info = downloader.download_package(str(dep), package_dir)
            updated_count += 1
            _rich_success(f"  ✅ {dep.repo_url}")
            
        except Exception as e:
            _rich_error(f"  ❌ Failed to update {dep.repo_url}: {e}")
            continue
    
    _rich_success(f"Updated {updated_count} of {len(project_deps)} packages")

