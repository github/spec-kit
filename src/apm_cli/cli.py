"""Command-line interface for Agent Package Manager (APM)."""

import sys
import os
import click
from pathlib import Path
from colorama import init, Fore, Style
from typing import List

# APM imports - use absolute imports everywhere for consistency
from apm_cli.version import get_version
from apm_cli.compilation import AgentsCompiler, CompilationConfig
from apm_cli.primitives.discovery import discover_primitives
from apm_cli.utils.console import (
    _rich_success, _rich_error, _rich_info, _rich_warning, _rich_echo, 
    _rich_panel, _create_files_table, _get_console, STATUS_SYMBOLS
)
from apm_cli.commands.deps import deps

# APM Dependencies - Import for Task 5 integration
try:
    from apm_cli.models.apm_package import APMPackage, DependencyReference
    from apm_cli.deps.apm_resolver import APMDependencyResolver
    from apm_cli.deps.github_downloader import GitHubPackageDownloader
    APM_DEPS_AVAILABLE = True
except ImportError as e:
    # Graceful fallback if APM dependencies are not available
    APM_DEPS_AVAILABLE = False
    _APM_IMPORT_ERROR = str(e)

# Initialize colorama for fallback
init(autoreset=True)

# Legacy colorama constants for compatibility
TITLE = f"{Fore.CYAN}{Style.BRIGHT}"
SUCCESS = f"{Fore.GREEN}{Style.BRIGHT}"
ERROR = f"{Fore.RED}{Style.BRIGHT}"
INFO = f"{Fore.BLUE}"
WARNING = f"{Fore.YELLOW}"
HIGHLIGHT = f"{Fore.MAGENTA}{Style.BRIGHT}"
RESET = Style.RESET_ALL


def _get_template_dir():
    """Get the path to the templates directory."""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = sys._MEIPASS
        return Path(base_path) / 'templates'
    else:
        # Running in development
        cli_dir = Path(__file__).parent
        # Go up to the src directory, then up to the repo root, then to templates
        template_dir = cli_dir.parent.parent / 'templates'
        return template_dir


# Lazy loading for Rich components to improve startup performance
_console = None

def _get_console():
    """Get Rich console instance with lazy loading."""
    global _console
    if _console is None:
        from rich.console import Console
        from rich.theme import Theme
        
        custom_theme = Theme({
            "info": "cyan",
            "warning": "yellow", 
            "error": "bold red",
            "success": "bold green",
            "highlight": "bold magenta",
            "muted": "dim white",
            "accent": "bold blue",
            "title": "bold cyan"
        })
        
        _console = Console(theme=custom_theme)
    return _console


def _rich_blank_line():
    """Print a blank line with Rich if available, otherwise use click."""
    console = _get_console()
    if console:
        console.print()
    else:
        click.echo()


def _lazy_yaml():
    """Lazy import for yaml module to improve startup performance."""
    try:
        import yaml
        return yaml
    except ImportError:
        raise ImportError("PyYAML is required but not installed")


def _lazy_prompt():
    """Lazy import for Rich Prompt to improve startup performance."""
    try:
        from rich.prompt import Prompt
        return Prompt
    except ImportError:
        return None


def _lazy_confirm():
    """Lazy import for Rich Confirm to improve startup performance."""
    try:
        from rich.prompt import Confirm
        return Confirm
    except ImportError:
        return None


def _check_orphaned_packages():
    """Check for packages in apm_modules/ that are not declared in apm.yml.
    
    Returns:
        List[str]: List of orphaned package names in org/repo format
    """
    try:
        from pathlib import Path
        
        # Check if apm.yml exists
        if not Path('apm.yml').exists():
            return []
        
        # Check if apm_modules exists
        apm_modules_dir = Path('apm_modules')
        if not apm_modules_dir.exists():
            return []
        
        # Parse apm.yml to get declared dependencies
        try:
            apm_package = APMPackage.from_apm_yml(Path('apm.yml'))
            declared_deps = apm_package.get_apm_dependencies()
            declared_repos = set(dep.repo_url for dep in declared_deps)
            declared_names = set()
            for dep in declared_deps:
                if '/' in dep.repo_url:
                    declared_names.add(dep.repo_url.split('/')[-1])
                else:
                    declared_names.add(dep.repo_url)
        except Exception:
            return []  # If can't parse apm.yml, assume no orphans
        
        # Find installed packages and check for orphans (org-namespaced structure)
        orphaned_packages = []
        for org_dir in apm_modules_dir.iterdir():
            if org_dir.is_dir() and not org_dir.name.startswith('.'):
                for repo_dir in org_dir.iterdir():
                    if repo_dir.is_dir() and not repo_dir.name.startswith('.'):
                        org_repo_name = f"{org_dir.name}/{repo_dir.name}"
                        
                        # Check if orphaned
                        if org_repo_name not in declared_repos:
                            orphaned_packages.append(org_repo_name)
        
        return orphaned_packages
    except Exception:
        return []  # Return empty list if any error occurs


def _load_template_file(template_name, filename, **variables):
    """Load a template file and substitute variables."""
    template_dir = _get_template_dir()
    template_path = template_dir / template_name / filename
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Simple template substitution using string replace
    for var_name, var_value in variables.items():
        content = content.replace(f'{{{{{var_name}}}}}', str(var_value))
    
    return content


def print_version(ctx, param, value):
    """Print version and exit."""
    if not value or ctx.resilient_parsing:
        return
    
    console = _get_console()
    if console:
        from rich.text import Text  # type: ignore
        from rich.panel import Panel  # type: ignore
        version_text = Text()
        version_text.append("Agent Package Manager (APM) CLI", style="bold cyan")
        version_text.append(f" version {get_version()}", style="white")
        console.print(Panel(
            version_text,
            border_style="cyan",
            padding=(0, 1)
        ))
    else:
        # Graceful fallback when Rich isn't available (e.g., stripped automation environment)
        click.echo(f"{TITLE}Agent Package Manager (APM) CLI{RESET} version {get_version()}")
    
    ctx.exit()

@click.group(help="Agent Package Manager (APM): The package manager for AI-Native Development")
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True, help="Show version and exit.")
@click.pass_context
def cli(ctx):
    """Main entry point for the APM CLI."""
    ctx.ensure_object(dict)


# Register command groups
cli.add_command(deps)


@cli.command(help="Initialize a new APM project")
@click.argument('project_name', required=False)
@click.option('--force', '-f', is_flag=True, help="Overwrite existing files without confirmation")
@click.option('--yes', '-y', is_flag=True, help="Skip interactive questionnaire and use defaults")
@click.pass_context
def init(ctx, project_name, force, yes):
    """Initialize a new APM project (like npm init)."""
    try:
        # Handle explicit current directory
        if project_name == '.':
            project_name = None
            
        # Determine project directory and name
        if project_name:
            project_dir = Path(project_name)
            project_dir.mkdir(exist_ok=True)
            os.chdir(project_dir)
            _rich_info(f"Created project directory: {project_name}", symbol="folder")
            final_project_name = project_name
        else:
            project_dir = Path.cwd()
            final_project_name = project_dir.name
            
        # Check for existing APM project
        apm_yml_exists = Path('apm.yml').exists()
        existing_files = []
        if apm_yml_exists:
            existing_files.append('apm.yml')
        if Path('hello-world.prompt.md').exists():
            existing_files.append('hello-world.prompt.md')
        if Path('README.md').exists():
            existing_files.append('README.md')
            
        # Handle existing project
        if existing_files and not force:
            _rich_warning("Existing APM project detected:")
            for file in existing_files:
                _rich_echo(f"  - {file}", style="muted")
            _rich_blank_line()
            
            if not yes:
                Confirm = _lazy_confirm()
                if Confirm:
                    try:
                        confirm = Confirm.ask("Continue and overwrite existing files?")
                    except Exception:
                        confirm = click.confirm("Continue and overwrite existing files?")
                else:
                    confirm = click.confirm("Continue and overwrite existing files?")
                
                if not confirm:
                    _rich_info("Initialization cancelled.")
                    return
            else:
                _rich_info("--yes specified, continuing with overwrite...")
        
        # Get project configuration (interactive mode or defaults)
        if not yes and not apm_yml_exists:
            config = _interactive_project_setup(final_project_name)
        else:
            # Use defaults or preserve existing config
            if apm_yml_exists and not force:
                config = _merge_existing_config(final_project_name)
            else:
                config = _get_default_config(final_project_name)
        
        _rich_success(f"Initializing APM project: {config['name']}", symbol="rocket")
        
        # Create files from config
        _create_project_files(config)
        
        _rich_success("APM project initialized successfully!", symbol="sparkles")
        
        # Next steps with better formatting
        next_steps = [
            f"1. {STATUS_SYMBOLS['sparkles']} apm compile - Generate AGENTS.md from your primitives",
            f"2. {STATUS_SYMBOLS['gear']} apm install - Install dependencies", 
            f"3. {STATUS_SYMBOLS['running']} apm run start --param name=\"Your Handle\" - Run the start script"
        ]
        
        try:
            _rich_panel("\n".join(next_steps), title="Next Steps", style="green")
        except (ImportError, NameError):
            _rich_info("Next steps:")
            for step in next_steps:
                click.echo(f"  {step}")
        
    except Exception as e:
        _rich_error(f"Error initializing project: {e}")
        sys.exit(1)


def _validate_and_add_packages_to_apm_yml(packages, dry_run=False):
    """Validate packages exist and can be accessed, then add to apm.yml dependencies section."""
    import yaml
    from pathlib import Path
    import subprocess
    import tempfile
    
    apm_yml_path = Path('apm.yml')
    
    # Read current apm.yml
    try:
        with open(apm_yml_path, 'r') as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        _rich_error(f"Failed to read apm.yml: {e}")
        sys.exit(1)
    
    # Ensure dependencies structure exists
    if 'dependencies' not in data:
        data['dependencies'] = {}
    if 'apm' not in data['dependencies']:
        data['dependencies']['apm'] = []
    
    current_deps = data['dependencies']['apm'] or []
    validated_packages = []
    
    # First, validate all packages
    _rich_info(f"Validating {len(packages)} package(s)...")
    
    for package in packages:
        # Validate package format (should be owner/repo)
        if '/' not in package:
            _rich_error(f"Invalid package format: {package}. Use 'owner/repo' format.")
            continue
            
        # Check if package is already in dependencies
        if package in current_deps:
            _rich_warning(f"Package {package} already exists in apm.yml")
            continue
            
        # Validate package exists and is accessible
        if _validate_package_exists(package):
            validated_packages.append(package)
            _rich_info(f"✓ {package} - accessible")
        else:
            _rich_error(f"✗ {package} - not accessible or doesn't exist")
    
    if not validated_packages:
        if dry_run:
            _rich_warning("No new valid packages to add")
        return []
    
    if dry_run:
        _rich_info(f"Dry run: Would add {len(validated_packages)} package(s) to apm.yml:")
        for pkg in validated_packages:
            _rich_info(f"  + {pkg}")
        return validated_packages
    
    # Add validated packages to dependencies
    for package in validated_packages:
        current_deps.append(package)
        _rich_info(f"Added {package} to apm.yml")
    
    # Update dependencies
    data['dependencies']['apm'] = current_deps
    
    # Write back to apm.yml
    try:
        with open(apm_yml_path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        _rich_success(f"Updated apm.yml with {len(validated_packages)} new package(s)")
    except Exception as e:
        _rich_error(f"Failed to write apm.yml: {e}")
        sys.exit(1)
    
    return validated_packages


def _validate_package_exists(package):
    """Validate that a package exists and is accessible on GitHub."""
    import subprocess
    import tempfile
    import os
    
    # Try to do a shallow clone to test accessibility
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Try cloning with minimal fetch
            cmd = [
                'git', 'ls-remote', '--heads', '--exit-code',
                f'https://github.com/{package}.git'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False


@cli.command(help="Install APM and MCP dependencies from apm.yml")
@click.argument('packages', nargs=-1)
@click.option('--runtime', help="Target specific runtime only (copilot, codex, vscode)")
@click.option('--exclude', help="Exclude specific runtime from installation")
@click.option('--only', type=click.Choice(['apm', 'mcp']), help="Install only specific dependency type")
@click.option('--update', is_flag=True, help="Update dependencies to latest Git references")
@click.option('--dry-run', is_flag=True, help="Show what would be installed without installing")
@click.pass_context
def install(ctx, packages, runtime, exclude, only, update, dry_run):
    """Install APM and MCP dependencies from apm.yml (like npm install).
    
    This command automatically detects AI runtimes from your apm.yml scripts and installs
    MCP servers for all detected and available runtimes. It also installs APM package
    dependencies from GitHub repositories.
    
    Examples:
        apm install                             # Install existing deps from apm.yml
        apm install org/pkg1                    # Add package to apm.yml and install
        apm install org/pkg1 org/pkg2           # Add multiple packages and install
        apm install --exclude codex             # Install for all except Codex CLI
        apm install --only=apm                  # Install only APM dependencies
        apm install --only=mcp                  # Install only MCP dependencies
        apm install --update                    # Update dependencies to latest Git refs
        apm install --dry-run                   # Show what would be installed
    """
    try:
        # Check if apm.yml exists
        if not Path('apm.yml').exists():
            _rich_error("No apm.yml found. Run 'apm init' first.")
            sys.exit(1)
        
        # If packages are specified, validate and add them to apm.yml first
        if packages:
            validated_packages = _validate_and_add_packages_to_apm_yml(packages, dry_run)
            if not validated_packages and not dry_run:
                _rich_error("No valid packages to install")
                sys.exit(1)
        
        _rich_info("Installing dependencies from apm.yml...")
        
        # Parse apm.yml to get both APM and MCP dependencies
        try:
            apm_package = APMPackage.from_apm_yml(Path('apm.yml'))
        except Exception as e:
            _rich_error(f"Failed to parse apm.yml: {e}")
            sys.exit(1)
        
        # Get APM and MCP dependencies
        apm_deps = apm_package.get_apm_dependencies()
        mcp_deps = apm_package.get_mcp_dependencies()
        
        # Determine what to install based on --only flag
        should_install_apm = only != 'mcp'
        should_install_mcp = only != 'apm'
        
        # Show what will be installed if dry run
        if dry_run:
            _rich_info("Dry run mode - showing what would be installed:")
            
            if should_install_apm and apm_deps:
                _rich_info(f"APM dependencies ({len(apm_deps)}):")
                for dep in apm_deps:
                    action = "update" if update else "install"
                    _rich_info(f"  - {dep.repo_url}#{dep.reference or 'main'} → {action}")
            
            if should_install_mcp and mcp_deps:
                _rich_info(f"MCP dependencies ({len(mcp_deps)}):")
                for dep in mcp_deps:
                    _rich_info(f"  - {dep}")
            
            if not apm_deps and not mcp_deps:
                _rich_warning("No dependencies found in apm.yml")
            
            _rich_success("Dry run complete - no changes made")
            return
        
        # Install APM dependencies first (if requested)
        if should_install_apm and apm_deps:
            if not APM_DEPS_AVAILABLE:
                _rich_error("APM dependency system not available")
                _rich_info(f"Import error: {_APM_IMPORT_ERROR}")
                sys.exit(1)
            
            try:
                _install_apm_dependencies(apm_package, update)
            except Exception as e:
                _rich_error(f"Failed to install APM dependencies: {e}")
                sys.exit(1)
        elif should_install_apm and not apm_deps:
            _rich_info("No APM dependencies found in apm.yml")
        
        # Continue with MCP installation (existing logic)
        if should_install_mcp and mcp_deps:
            _install_mcp_dependencies(mcp_deps, runtime, exclude)
        elif should_install_mcp and not mcp_deps:
            _rich_warning("No MCP dependencies found in apm.yml")
        
        # Final success message
        _rich_blank_line()
        if only:
            _rich_success(f"{only.upper()} dependencies installation complete")
        else:
            _rich_success("Dependencies installation complete")
        
    except Exception as e:
        _rich_error(f"Error installing dependencies: {e}")
        sys.exit(1)


@cli.command(help="Remove APM packages not listed in apm.yml")
@click.option('--dry-run', is_flag=True, help="Show what would be removed without removing")
@click.pass_context
def prune(ctx, dry_run):
    """Remove installed APM packages that are not listed in apm.yml (like npm prune).
    
    This command cleans up the apm_modules/ directory by removing packages that
    were previously installed but are no longer declared as dependencies in apm.yml.
    
    Examples:
        apm prune           # Remove orphaned packages
        apm prune --dry-run # Show what would be removed
    """
    try:
        # Check if apm.yml exists
        if not Path('apm.yml').exists():
            _rich_error("No apm.yml found. Run 'specify apm init' first.")
            sys.exit(1)
        
        # Check if apm_modules exists
        apm_modules_dir = Path('apm_modules')
        if not apm_modules_dir.exists():
            _rich_info("No apm_modules/ directory found. Nothing to prune.")
            return
        
        _rich_info("Analyzing installed packages vs apm.yml...")
        
        # Parse apm.yml to get declared dependencies
        try:
            apm_package = APMPackage.from_apm_yml(Path('apm.yml'))
            declared_deps = apm_package.get_apm_dependencies()
            # Keep full org/repo format (e.g., "github/design-guidelines")
            declared_repos = set()
            declared_names = set()  # For directory name matching
            for dep in declared_deps:
                declared_repos.add(dep.repo_url)
                # Also track directory names for filesystem matching
                if '/' in dep.repo_url:
                    package_name = dep.repo_url.split('/')[-1]
                    declared_names.add(package_name)
                else:
                    declared_names.add(dep.repo_url)
        except Exception as e:
            _rich_error(f"Failed to parse apm.yml: {e}")
            sys.exit(1)
        
        # Find installed packages in apm_modules/ (now org-namespaced)
        installed_packages = {}  # {"github/design-guidelines": "github/design-guidelines"}
        if apm_modules_dir.exists():
            for org_dir in apm_modules_dir.iterdir():
                if org_dir.is_dir() and not org_dir.name.startswith('.'):
                    # Check if this is an org directory with packages inside
                    for repo_dir in org_dir.iterdir():
                        if repo_dir.is_dir() and not repo_dir.name.startswith('.'):
                            org_repo_name = f"{org_dir.name}/{repo_dir.name}"
                            installed_packages[org_repo_name] = org_repo_name
        
        # Find orphaned packages (installed but not declared)
        orphaned_packages = {}
        for org_repo_name, display_name in installed_packages.items():
            if org_repo_name not in declared_repos:
                orphaned_packages[org_repo_name] = display_name
        
        if not orphaned_packages:
            _rich_success("No orphaned packages found. apm_modules/ is clean.")
            return
        
        # Show what will be removed
        _rich_info(f"Found {len(orphaned_packages)} orphaned package(s):")
        for dir_name, display_name in orphaned_packages.items():
            if dry_run:
                _rich_info(f"  - {display_name} (would be removed)")
            else:
                _rich_info(f"  - {display_name}")
        
        if dry_run:
            _rich_success("Dry run complete - no changes made")
            return
        
        # Remove orphaned packages
        removed_count = 0
        for org_repo_name, display_name in orphaned_packages.items():
            # Convert org/repo to filesystem path
            org_name, repo_name = org_repo_name.split('/', 1)
            pkg_path = apm_modules_dir / org_name / repo_name
            try:
                import shutil
                shutil.rmtree(pkg_path)
                _rich_info(f"✓ Removed {display_name}")
                removed_count += 1
                
                # Clean up empty org directory
                org_path = apm_modules_dir / org_name
                if org_path.exists() and not any(org_path.iterdir()):
                    org_path.rmdir()
                    
            except Exception as e:
                _rich_error(f"✗ Failed to remove {display_name}: {e}")
        
        # Final summary
        if removed_count > 0:
            _rich_success(f"Pruned {removed_count} orphaned package(s)")
        else:
            _rich_warning("No packages were removed")
        
    except Exception as e:
        _rich_error(f"Error pruning packages: {e}")
        sys.exit(1)


@cli.command(help="Remove APM packages from apm.yml and apm_modules")
@click.argument('packages', nargs=-1, required=True)
@click.option('--dry-run', is_flag=True, help="Show what would be removed without removing")
@click.pass_context
def uninstall(ctx, packages, dry_run):
    """Remove APM packages from apm.yml and apm_modules (like npm uninstall).
    
    This command removes packages from both the apm.yml dependencies list
    and the apm_modules/ directory. It's the opposite of 'apm install <package>'.
    
    Examples:
        apm uninstall github/design-guidelines    # Remove one package
        apm uninstall org/pkg1 org/pkg2           # Remove multiple packages
        apm uninstall github/pkg --dry-run        # Show what would be removed
    """
    try:
        # Check if apm.yml exists
        if not Path('apm.yml').exists():
            _rich_error("No apm.yml found. Run 'apm init' first.")
            sys.exit(1)
        
        if not packages:
            _rich_error("No packages specified. Specify packages to uninstall.")
            sys.exit(1)
        
        _rich_info(f"Uninstalling {len(packages)} package(s)...")
        
        # Read current apm.yml
        import yaml
        apm_yml_path = Path('apm.yml')
        try:
            with open(apm_yml_path, 'r') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            _rich_error(f"Failed to read apm.yml: {e}")
            sys.exit(1)
        
        # Ensure dependencies structure exists
        if 'dependencies' not in data:
            data['dependencies'] = {}
        if 'apm' not in data['dependencies']:
            data['dependencies']['apm'] = []
        
        current_deps = data['dependencies']['apm'] or []
        packages_to_remove = []
        packages_not_found = []
        
        # Validate which packages can be removed
        for package in packages:
            # Validate package format (should be owner/repo)
            if '/' not in package:
                _rich_error(f"Invalid package format: {package}. Use 'owner/repo' format.")
                continue
                
            # Check if package exists in dependencies
            if package in current_deps:
                packages_to_remove.append(package)
                _rich_info(f"✓ {package} - found in apm.yml")
            else:
                packages_not_found.append(package)
                _rich_warning(f"✗ {package} - not found in apm.yml")
        
        if not packages_to_remove:
            _rich_warning("No packages found in apm.yml to remove")
            return
        
        if dry_run:
            _rich_info(f"Dry run: Would remove {len(packages_to_remove)} package(s):")
            for pkg in packages_to_remove:
                _rich_info(f"  - {pkg} from apm.yml")
                # Check if package exists in apm_modules
                package_name = pkg.split('/')[-1]
                apm_modules_dir = Path('apm_modules')
                if apm_modules_dir.exists() and (apm_modules_dir / package_name).exists():
                    _rich_info(f"  - {package_name} from apm_modules/")
            _rich_success("Dry run complete - no changes made")
            return
        
        # Remove packages from apm.yml
        for package in packages_to_remove:
            current_deps.remove(package)
            _rich_info(f"Removed {package} from apm.yml")
        
        # Update dependencies in apm.yml
        data['dependencies']['apm'] = current_deps
        
        # Write back to apm.yml
        try:
            with open(apm_yml_path, 'w') as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
            _rich_success(f"Updated apm.yml (removed {len(packages_to_remove)} package(s))")
        except Exception as e:
            _rich_error(f"Failed to write apm.yml: {e}")
            sys.exit(1)
        
        # Remove packages from apm_modules/
        apm_modules_dir = Path('apm_modules')
        removed_from_modules = 0
        
        if apm_modules_dir.exists():
            for package in packages_to_remove:
                package_name = package.split('/')[-1]  # Extract package name
                package_path = apm_modules_dir / package_name
                
                if package_path.exists():
                    try:
                        import shutil
                        shutil.rmtree(package_path)
                        _rich_info(f"✓ Removed {package_name} from apm_modules/")
                        removed_from_modules += 1
                    except Exception as e:
                        _rich_error(f"✗ Failed to remove {package_name} from apm_modules/: {e}")
                else:
                    _rich_warning(f"Package {package_name} not found in apm_modules/")
        
        # Final summary
        summary_lines = []
        summary_lines.append(f"Removed {len(packages_to_remove)} package(s) from apm.yml")
        if removed_from_modules > 0:
            summary_lines.append(f"Removed {removed_from_modules} package(s) from apm_modules/")
        
        _rich_success("Uninstall complete: " + ", ".join(summary_lines))
        
        if packages_not_found:
            _rich_warning(f"Note: {len(packages_not_found)} package(s) were not found in apm.yml")
        
    except Exception as e:
        _rich_error(f"Error uninstalling packages: {e}")
        sys.exit(1)

def _install_apm_dependencies(apm_package: 'APMPackage', update_refs: bool = False):
    """Install APM package dependencies.
    
    Args:
        apm_package: Parsed APM package with dependencies
        update_refs: Whether to update existing packages to latest refs
    """
    if not APM_DEPS_AVAILABLE:
        raise RuntimeError("APM dependency system not available")
    
    apm_deps = apm_package.get_apm_dependencies()
    if not apm_deps:
        return
    
    _rich_info(f"Installing APM dependencies ({len(apm_deps)})...")
    
    # Resolve dependencies
    resolver = APMDependencyResolver()
    project_root = Path.cwd()
    
    try:
        dependency_graph = resolver.resolve_dependencies(project_root)
        
        # Check for circular dependencies
        if dependency_graph.circular_dependencies:
            _rich_error("Circular dependencies detected:")
            for circular in dependency_graph.circular_dependencies:
                cycle_path = " → ".join(circular.cycle_path)
                _rich_error(f"  {cycle_path}")
            raise RuntimeError("Cannot install packages with circular dependencies")
        
        # Get flattened dependencies for installation
        flat_deps = dependency_graph.flattened_dependencies
        deps_to_install = flat_deps.get_installation_list()
        
        if not deps_to_install:
            _rich_info("No APM dependencies to install", symbol="check")
            return
        
        # Create apm_modules directory
        apm_modules_dir = project_root / "apm_modules"
        apm_modules_dir.mkdir(exist_ok=True)
        
        # Install each dependency
        downloader = GitHubPackageDownloader()
        installed_count = 0
        
        for dep_ref in deps_to_install:
            # Determine installation directory using namespaced structure
            # e.g., github/design-guidelines -> apm_modules/github/design-guidelines/
            if dep_ref.alias:
                # If alias is provided, use it directly (assume user handles namespacing)
                install_name = dep_ref.alias
                install_path = apm_modules_dir / install_name
            else:
                # Use org/repo structure to prevent collisions
                repo_parts = dep_ref.repo_url.split('/')
                if len(repo_parts) >= 2:
                    org_name = repo_parts[0]
                    repo_name = repo_parts[1]
                    install_path = apm_modules_dir / org_name / repo_name
                else:
                    # Fallback for invalid repo URLs
                    install_path = apm_modules_dir / dep_ref.repo_url
            
            # Skip if already exists and not updating
            if install_path.exists() and not update_refs:
                _rich_info(f"✓ {dep_ref.repo_url} (cached)")
                continue
            
            # Download the package
            try:
                _rich_info(f"  {dep_ref.repo_url}#{dep_ref.reference or 'main'}")
                
                package_info = downloader.download_package(str(dep_ref), install_path)
                installed_count += 1
                
                _rich_success(f"✓ {dep_ref.repo_url}")
                
            except Exception as e:
                _rich_error(f"❌ Failed to install {dep_ref.repo_url}: {e}")
                # Continue with other packages instead of failing completely
                continue
        
        # Update .gitignore
        _update_gitignore_for_apm_modules()
        
        _rich_success(f"Installed {installed_count} APM dependencies")
        
    except Exception as e:
        raise RuntimeError(f"Failed to resolve APM dependencies: {e}")


def _install_mcp_dependencies(mcp_deps: List[str], runtime: str = None, exclude: str = None):
    """Install MCP dependencies using existing logic.
    
    Args:
        mcp_deps: List of MCP dependency names
        runtime: Target specific runtime only 
        exclude: Exclude specific runtime from installation
    """
    if not mcp_deps:
        _rich_warning("No MCP dependencies found in apm.yml")
        return
        
    _rich_info(f"Installing MCP dependencies ({len(mcp_deps)})...")
    
    # Show dependencies in a nice list
    console = _get_console()
    if console:
        try:
            from rich.table import Table
            dep_table = Table(show_header=False, box=None, padding=(0, 1))
            dep_table.add_column("Icon", style="cyan")
            dep_table.add_column("Dependency", style="white")
            
            for dep in mcp_deps:
                dep_table.add_row("•", dep)
            
            console.print(dep_table)
        except Exception:
            for dep in mcp_deps:
                click.echo(f"  - {dep}")
    else:
        for dep in mcp_deps:
            click.echo(f"  - {dep}")
    
    # Runtime detection and multi-runtime installation (existing logic)
    if runtime:
        # Single runtime mode
        target_runtimes = [runtime]
        _rich_info(f"Targeting specific runtime: {runtime}")
    else:
        # Auto-detect from scripts but filter to MCP-compatible runtimes only
        config = _load_apm_config()
        detected_runtimes = _detect_runtimes_from_scripts(config.get('scripts', {}) if config else {})
        available_runtimes = _filter_available_runtimes(detected_runtimes)
        if exclude:
            available_runtimes = [r for r in available_runtimes if r != exclude]
        target_runtimes = available_runtimes
        
        if detected_runtimes:
            _rich_info(f"Detected runtimes: {', '.join(detected_runtimes)}")
            if available_runtimes:
                _rich_info(f"Available runtimes: {', '.join(available_runtimes)}")
            else:
                _rich_warning("No detected runtimes support MCP installation")
                _rich_info("Supported runtimes: vscode, copilot")
        
        # Fall back to VS Code if no runtimes detected
        if not target_runtimes:
            target_runtimes = ['vscode']
            _rich_info("No runtimes detected, using VS Code as fallback")
        if exclude:
            target_runtimes = [r for r in target_runtimes if r != exclude]
    
    # Use the new registry operations module for better server detection
    try:
        from apm_cli.registry.operations import MCPServerOperations
        
        operations = MCPServerOperations()
        
        # Early validation: check if all servers exist in registry (fail-fast like npm)
        _rich_info(f"Validating {len(mcp_deps)} servers...")
        valid_servers, invalid_servers = operations.validate_servers_exist(mcp_deps)
        
        if invalid_servers:
            _rich_error(f"Server(s) not found in registry: {', '.join(invalid_servers)}")
            _rich_info("Run 'apm mcp search <query>' to find available servers")
            raise RuntimeError(f"Cannot install {len(invalid_servers)} missing server(s)")
        
        if not valid_servers:
            _rich_success("No servers to install")
            return
            
        # Check which valid servers actually need installation
        servers_to_install = operations.check_servers_needing_installation(target_runtimes, valid_servers)
        
        if not servers_to_install:
            _rich_success("All MCP servers already configured")
        else:
            # Batch fetch server info once to avoid duplicate registry calls
            _rich_info(f"Installing {len(servers_to_install)} servers...")
            server_info_cache = operations.batch_fetch_server_info(servers_to_install)
            
            # Collect both environment and runtime variables using cached server info
            shared_env_vars = operations.collect_environment_variables(servers_to_install, server_info_cache)
            shared_runtime_vars = operations.collect_runtime_variables(servers_to_install, server_info_cache)
            
            # Install for each target runtime using cached server info and shared variables
            for rt in target_runtimes:
                _rich_info(f"Configuring {rt}...")
                _install_for_runtime(rt, servers_to_install, shared_env_vars, server_info_cache, shared_runtime_vars)
                
    except ImportError:
        _rich_warning("Registry operations not available")
        _rich_error("Cannot validate MCP servers without registry operations")
        raise RuntimeError("Registry operations module required for MCP installation")


def _update_gitignore_for_apm_modules():
    """Add apm_modules/ to .gitignore if not already present."""
    gitignore_path = Path('.gitignore')
    apm_modules_pattern = 'apm_modules/'
    
    # Read current .gitignore content
    current_content = []
    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                current_content = [line.rstrip('\n\r') for line in f.readlines()]
        except Exception as e:
            _rich_warning(f"Could not read .gitignore: {e}")
            return
    
    # Check if apm_modules/ is already in .gitignore
    if any(line.strip() == apm_modules_pattern for line in current_content):
        return  # Already present
    
    # Add apm_modules/ to .gitignore
    try:
        with open(gitignore_path, 'a', encoding='utf-8') as f:
            # Add a blank line before our entry if file isn't empty
            if current_content and current_content[-1].strip():
                f.write('\n')
            f.write(f'\n# APM dependencies\n{apm_modules_pattern}\n')
        
        _rich_info(f"Added {apm_modules_pattern} to .gitignore")
    except Exception as e:
        _rich_warning(f"Could not update .gitignore: {e}")


def _load_apm_config():
    """Load configuration from apm.yml."""
    if Path('apm.yml').exists():
        with open('apm.yml', 'r') as f:
            yaml = _lazy_yaml()
            return yaml.safe_load(f)
    return None


def _detect_runtimes_from_scripts(scripts: dict) -> List[str]:
    """Extract runtime commands from apm.yml scripts."""
    import re
    from builtins import list as builtin_list
    detected = set()
    
    for script_name, command in scripts.items():
        # Simple regex matching for runtime commands
        if re.search(r'\bcopilot\b', command):
            detected.add('copilot')
        if re.search(r'\bcodex\b', command):
            detected.add('codex')
        if re.search(r'\bllm\b', command):
            detected.add('llm')
    
    return builtin_list(detected)


def _filter_available_runtimes(detected_runtimes: List[str]) -> List[str]:
    """Filter to only runtimes that are actually installed and support MCP."""
    from apm_cli.factory import ClientFactory
    
    # First filter to only MCP-compatible runtimes
    try:
        # Get supported client types from factory
        mcp_compatible = []
        for rt in detected_runtimes:
            try:
                ClientFactory.create_client(rt)
                mcp_compatible.append(rt)
            except ValueError:
                # Runtime not supported by MCP client factory
                continue
        
        # Then filter to only installed runtimes
        try:
            from apm_cli.runtime.manager import RuntimeManager
            manager = RuntimeManager()
            
            return [rt for rt in mcp_compatible if manager.is_runtime_available(rt)]
        except ImportError:
            # Fallback to basic shutil check
            import shutil
            available = []
            for rt in mcp_compatible:
                if shutil.which(rt):
                    available.append(rt)
            return available
            
    except ImportError:
        # If factory is not available, fall back to known MCP runtimes
        mcp_compatible = [rt for rt in detected_runtimes if rt in ['vscode', 'copilot']]
        
        import shutil
        return [rt for rt in mcp_compatible if shutil.which(rt)]


def _install_for_runtime(runtime: str, mcp_deps: List[str], shared_env_vars: dict = None, server_info_cache: dict = None, shared_runtime_vars: dict = None):
    """Install MCP dependencies for a specific runtime."""
    try:
        from apm_cli.factory import ClientFactory
        from apm_cli.core.operations import install_package
        
        # Get the appropriate client for the runtime
        client = ClientFactory.create_client(runtime)
        
        for dep in mcp_deps:
            click.echo(f"  Installing {dep}...")
            try:
                result = install_package(runtime, dep, shared_env_vars=shared_env_vars, server_info_cache=server_info_cache, shared_runtime_vars=shared_runtime_vars)
                # Only show warnings for actual failures, not skips due to conflicts
                if result['failed']:
                    click.echo(f"  ✗ Failed to install {dep}")
                # Safe installer provides comprehensive feedback for success/skip cases
            except Exception as install_error:
                click.echo(f"  ✗ Failed to install {dep}: {install_error}")
                
    except ImportError as e:
        _rich_warning(f"Core operations not available for runtime {runtime}: {e}")
        _rich_info(f"Dependencies for {runtime}: {', '.join(mcp_deps)}")
    except ValueError as e:
        _rich_warning(f"Runtime {runtime} not supported: {e}")
        _rich_info(f"Supported runtimes: vscode, copilot, codex, llm")
    except Exception as e:
        _rich_error(f"Error installing for runtime {runtime}: {e}")


def _get_default_script():
    """Get the default script (start) from apm.yml scripts."""
    config = _load_apm_config()
    if config and 'scripts' in config and 'start' in config['scripts']:
        return 'start'
    return None


def _list_available_scripts():
    """List all available scripts from apm.yml."""
    config = _load_apm_config()
    if config and 'scripts' in config:
        return config['scripts']
    return {}


@cli.command(help="Run a script with parameters")
@click.argument('script_name', required=False)
@click.option('--param', '-p', multiple=True, help="Parameter in format name=value")
@click.pass_context
def run(ctx, script_name, param):
    """Run a script from apm.yml (uses 'start' script if no name specified)."""
    try:
        # If no script name specified, use 'start' script
        if not script_name:
            script_name = _get_default_script()
            if not script_name:
                _rich_error("No script specified and no 'start' script defined in apm.yml")
                _rich_info("Available scripts:")
                scripts = _list_available_scripts()
                
                console = _get_console()
                if console:
                    try:
                        from rich.table import Table
                        # Show available scripts in a table
                        table = Table(show_header=False, box=None, padding=(0, 1))
                        table.add_column("Icon", style="cyan")
                        table.add_column("Script", style="highlight")
                        table.add_column("Command", style="white")
                        
                        for name, command in scripts.items():
                            table.add_row("  ", name, command)
                        
                        console.print(table)
                    except Exception:
                        for name, command in scripts.items():
                            click.echo(f"  - {HIGHLIGHT}{name}{RESET}: {command}")
                else:
                    for name, command in scripts.items():
                        click.echo(f"  - {HIGHLIGHT}{name}{RESET}: {command}")
                sys.exit(1)
                
        _rich_info(f"Running script: {script_name}", symbol="running")
        
        # Parse parameters
        params = {}
        for p in param:
            if '=' in p:
                param_name, value = p.split('=', 1)
                params[param_name] = value
                _rich_echo(f"  - {param_name}: {value}", style="muted")
                
        # Import and use script runner
        try:
            from apm_cli.core.script_runner import ScriptRunner
            
            script_runner = ScriptRunner()
            success = script_runner.run_script(script_name, params)
            
            if not success:
                _rich_error("Script execution failed")
                sys.exit(1)
                
            _rich_blank_line()
            _rich_success("Script executed successfully!", symbol="sparkles")
            
        except ImportError as ie:
            _rich_warning("Script runner not available yet")
            _rich_info(f"Import error: {ie}")
            _rich_info(f"Would run script: {script_name} with params {params}")
        except Exception as ee:
            _rich_error(f"Script execution error: {ee}")
            sys.exit(1)
            
    except Exception as e:
        _rich_error(f"Error running script: {e}")
        sys.exit(1)


@cli.command(help="Preview a script's compiled prompt files")
@click.argument('script_name', required=False)
@click.option('--param', '-p', multiple=True, help="Parameter in format name=value")
@click.pass_context
def preview(ctx, script_name, param):
    """Preview compiled prompt files for a script."""
    try:
        # If no script name specified, use 'start' script
        if not script_name:
            script_name = _get_default_script()
            if not script_name:
                _rich_error("No script specified and no 'start' script defined in apm.yml")
                sys.exit(1)
                
        _rich_info(f"Previewing script: {script_name}", symbol="info")
        
        # Parse parameters
        params = {}
        for p in param:
            if '=' in p:
                param_name, value = p.split('=', 1)
                params[param_name] = value
                _rich_echo(f"  - {param_name}: {value}", style="muted")
                
        # Import and use script runner for preview
        try:
            from apm_cli.core.script_runner import ScriptRunner
            
            script_runner = ScriptRunner()
            
            # Get the script command
            scripts = script_runner.list_scripts()
            if script_name not in scripts:
                _rich_error(f"Script '{script_name}' not found")
                sys.exit(1)
                
            command = scripts[script_name]
            
            try:
                # Show original and compiled commands in panels
                _rich_panel(command, title="📄 Original command", style="blue")
                
                # Auto-compile prompts to show what would be executed
                compiled_command, compiled_prompt_files = script_runner._auto_compile_prompts(command, params)
                
                if compiled_prompt_files:
                    _rich_panel(compiled_command, title="⚡ Compiled command", style="green")
                else:
                    _rich_panel(compiled_command, title="⚡ Command (no prompt compilation)", style="yellow")
                    _rich_warning(f"No .prompt.md files found in command. APM only compiles files ending with '.prompt.md'")
                
                # Show compiled files if any .prompt.md files were processed
                if compiled_prompt_files:
                    file_list = []
                    for prompt_file in compiled_prompt_files:
                        output_name = Path(prompt_file).stem.replace('.prompt', '') + '.txt'
                        compiled_path = Path('.apm/compiled') / output_name
                        file_list.append(str(compiled_path))
                    
                    files_content = "\n".join([f"📄 {file}" for file in file_list])
                    _rich_panel(files_content, title="📁 Compiled prompt files", style="cyan")
                else:
                    _rich_panel(
                        "No .prompt.md files were compiled.\n\n" +
                        "APM only compiles files ending with '.prompt.md' extension.\n" +
                        "Other files are executed as-is by the runtime.", 
                        title="ℹ️  Compilation Info", 
                        style="cyan"
                    )
                
            except (ImportError, NameError):
                # Fallback display
                _rich_info("Original command:")
                click.echo(f"  {command}")
                
                compiled_command, compiled_prompt_files = script_runner._auto_compile_prompts(command, params)
                
                if compiled_prompt_files:
                    _rich_info("Compiled command:")
                    click.echo(f"  {compiled_command}")
                    
                    _rich_info("Compiled prompt files:")
                    for prompt_file in compiled_prompt_files:
                        output_name = Path(prompt_file).stem.replace('.prompt', '') + '.txt'
                        compiled_path = Path('.apm/compiled') / output_name
                        click.echo(f"  - {compiled_path}")
                else:
                    _rich_warning("Command (no prompt compilation):")
                    click.echo(f"  {compiled_command}")
                    _rich_info("APM only compiles files ending with '.prompt.md' extension.")
                    
            _rich_blank_line()
            _rich_success(f"Preview complete! Use 'apm run {script_name}' to execute.", symbol="sparkles")
            
        except ImportError:
            _rich_warning("Script runner not available yet")
            
    except Exception as e:
        _rich_error(f"Error previewing script: {e}")
        sys.exit(1)


@cli.command(help="List available scripts in the current project")
@click.pass_context
def list(ctx):
    """List all available scripts from apm.yml."""
    try:
        scripts = _list_available_scripts()
        
        if not scripts:
            _rich_warning("No scripts found.")
            
            # Show helpful example in a panel
            example_content = """scripts:
  start: "codex run main.prompt.md"
  fast: "llm prompt main.prompt.md -m github/gpt-4o-mini" """
            
            try:
                _rich_panel(example_content, title=f"{STATUS_SYMBOLS['info']} Add scripts to your apm.yml file", style="blue")
            except (ImportError, NameError):
                _rich_info("💡 Add scripts to your apm.yml file:")
                click.echo("scripts:")
                click.echo("  start: \"codex run main.prompt.md\"")
                click.echo("  fast: \"llm prompt main.prompt.md -m github/gpt-4o-mini\"")
            return
        
        # Show default script if 'start' exists
        default_script = 'start' if 'start' in scripts else None
        
        console = _get_console()
        if console:
            try:
                from rich.table import Table
                # Create a nice table for scripts
                table = Table(title="📋 Available Scripts", show_header=True, header_style="bold cyan")
                table.add_column("", style="cyan", width=3)
                table.add_column("Script", style="bold white", min_width=12)
                table.add_column("Command", style="white")
                
                for name, command in scripts.items():
                    icon = STATUS_SYMBOLS["default"] if name == default_script else "  "
                    table.add_row(icon, name, command)
                
                console.print(table)
                
                if default_script:
                    console.print(f"\n[muted]{STATUS_SYMBOLS['info']} {STATUS_SYMBOLS['default']} = default script (runs when no script name specified)[/muted]")
                    
            except Exception:
                # Fallback to simple output
                _rich_info("Available scripts:")
                for name, command in scripts.items():
                    icon = STATUS_SYMBOLS["default"] if name == default_script else "  "
                    click.echo(f"  {icon} {HIGHLIGHT}{name}{RESET}: {command}")
                if default_script:
                    click.echo(f"\n{STATUS_SYMBOLS['info']} {STATUS_SYMBOLS['default']} = default script")
        else:
            # Fallback to simple output
            _rich_info("Available scripts:")
            for name, command in scripts.items():
                icon = STATUS_SYMBOLS["default"] if name == default_script else "  "
                click.echo(f"  {icon} {HIGHLIGHT}{name}{RESET}: {command}")
            if default_script:
                click.echo(f"\n{STATUS_SYMBOLS['info']} {STATUS_SYMBOLS['default']} = default script")
            # Fallback to simple output
            _rich_info("Available scripts:")
            for name, command in scripts.items():
                prefix = "📍 " if name == default_script else "   "
                click.echo(f"{prefix}{HIGHLIGHT}{name}{RESET}: {command}")
                
            if default_script:
                _rich_info("📍 = default script (runs when no script name specified)")
            
    except Exception as e:
        _rich_error(f"Error listing scripts: {e}")
        sys.exit(1)


def _display_validation_errors(errors):
    """Display validation errors in a Rich table with actionable feedback."""
    try:
        console = _get_console()
        if console:
            from rich.table import Table
            
            error_table = Table(title="❌ Primitive Validation Errors", show_header=True, header_style="bold red")
            error_table.add_column("File", style="bold red", min_width=20)
            error_table.add_column("Error", style="white", min_width=30)
            error_table.add_column("Suggestion", style="yellow", min_width=25)
            
            for error in errors:
                file_path = str(error) if hasattr(error, '__str__') else "Unknown"
                # Extract file path from error string if it contains file info
                if ":" in file_path:
                    parts = file_path.split(":", 1)
                    file_name = parts[0] if len(parts) > 1 else "Unknown"
                    error_msg = parts[1].strip() if len(parts) > 1 else file_path
                else:
                    file_name = "Unknown"
                    error_msg = file_path
                
                # Provide actionable suggestions based on error type
                suggestion = _get_validation_suggestion(error_msg)
                error_table.add_row(file_name, error_msg, suggestion)
            
            console.print(error_table)
            return
        
    except (ImportError, NameError):
        pass
    
    # Fallback to simple text output
    _rich_error("Validation errors found:")
    for error in errors:
        click.echo(f"  ❌ {error}")


def _get_validation_suggestion(error_msg):
    """Get actionable suggestions for validation errors."""
    if "Missing 'description'" in error_msg:
        return "Add 'description: Your description here' to frontmatter"
    elif "Missing 'applyTo'" in error_msg:
        return "Add 'applyTo: \"**/*.py\"' to frontmatter"
    elif "Empty content" in error_msg:
        return "Add markdown content below the frontmatter"
    else:
        return "Check primitive structure and frontmatter"


def _watch_mode(output, chatmode, no_links, dry_run):
    """Watch for changes in .apm/ directories and auto-recompile."""
    try:
        # Try to import watchdog for file system monitoring
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        import time
        
        class APMFileHandler(FileSystemEventHandler):
            def __init__(self, output, chatmode, no_links, dry_run):
                self.output = output
                self.chatmode = chatmode
                self.no_links = no_links
                self.dry_run = dry_run
                self.last_compile = 0
                self.debounce_delay = 1.0  # 1 second debounce
                
            def on_modified(self, event):
                if event.is_directory:
                    return
                    
                # Check if it's a relevant file
                if (event.src_path.endswith('.md') or 
                    event.src_path.endswith('apm.yml')):
                    
                    # Debounce rapid changes
                    current_time = time.time()
                    if current_time - self.last_compile < self.debounce_delay:
                        return
                    
                    self.last_compile = current_time
                    self._recompile(event.src_path)
            
            def _recompile(self, changed_file):
                """Recompile after file change."""
                try:
                    _rich_info(f"File changed: {changed_file}", symbol="eyes")
                    _rich_info("Recompiling...", symbol="gear")
                    
                    # Create configuration from apm.yml with overrides
                    config = CompilationConfig.from_apm_yml(
                        output_path=self.output if self.output != "AGENTS.md" else None,
                        chatmode=self.chatmode,
                        resolve_links=not self.no_links if self.no_links else None,
                        dry_run=self.dry_run
                    )
                    
                    # Create compiler and compile
                    compiler = AgentsCompiler(".")
                    result = compiler.compile(config)
                    
                    if result.success:
                        if self.dry_run:
                            _rich_success("Recompilation successful (dry run)", symbol="sparkles")
                        else:
                            _rich_success(f"Recompiled to {result.output_path}", symbol="sparkles")
                    else:
                        _rich_error("Recompilation failed")
                        for error in result.errors:
                            click.echo(f"  ❌ {error}")
                    
                except Exception as e:
                    _rich_error(f"Error during recompilation: {e}")
        
        # Set up file watching
        event_handler = APMFileHandler(output, chatmode, no_links, dry_run)
        observer = Observer()
        
        # Watch patterns for APM files
        watch_paths = []
        
        # Check for .apm directory
        if Path(".apm").exists():
            observer.schedule(event_handler, ".apm", recursive=True)
            watch_paths.append(".apm/")
        
        # Check for .github/instructions and chatmodes
        if Path(".github/instructions").exists():
            observer.schedule(event_handler, ".github/instructions", recursive=True)
            watch_paths.append(".github/instructions/")
            
        if Path(".github/chatmodes").exists():
            observer.schedule(event_handler, ".github/chatmodes", recursive=True)
            watch_paths.append(".github/chatmodes/")
        
        # Watch apm.yml if it exists
        if Path("apm.yml").exists():
            observer.schedule(event_handler, ".", recursive=False)
            watch_paths.append("apm.yml")
        
        if not watch_paths:
            _rich_warning("No APM directories found to watch")
            _rich_info("Run 'apm init' to create an APM project")
            return
        
        # Start watching
        observer.start()
        _rich_info(f"👀 Watching for changes in: {', '.join(watch_paths)}", symbol="eyes")
        _rich_info("Press Ctrl+C to stop watching...", symbol="info")
        
        # Do initial compilation
        _rich_info("Performing initial compilation...", symbol="gear")
        
        config = CompilationConfig.from_apm_yml(
            output_path=output if output != "AGENTS.md" else None,
            chatmode=chatmode,
            resolve_links=not no_links if no_links else None,
            dry_run=dry_run
        )
        
        compiler = AgentsCompiler(".")
        result = compiler.compile(config)
        
        if result.success:
            if dry_run:
                _rich_success("Initial compilation successful (dry run)", symbol="sparkles")
            else:
                _rich_success(f"Initial compilation complete: {result.output_path}", symbol="sparkles")
        else:
            _rich_error("Initial compilation failed")
            for error in result.errors:
                click.echo(f"  ❌ {error}")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            _rich_info("Stopped watching for changes", symbol="info")
        
        observer.join()
        
    except ImportError:
        _rich_error("Watch mode requires the 'watchdog' library")
        _rich_info("Install it with: uv pip install watchdog")
        _rich_info("Or reinstall APM CLI: uv pip install -e . (from the apm-cli directory)")
        sys.exit(1)
    except Exception as e:
        _rich_error(f"Error in watch mode: {e}")
        sys.exit(1)


@cli.command(help="🚀 Compile APM context into distributed AGENTS.md files")
@click.option('--output', '-o', default="AGENTS.md", help="Output file path (for single-file mode)")
@click.option('--dry-run', is_flag=True, help="🔍 Preview compilation without writing files (shows placement decisions)")
@click.option('--no-links', is_flag=True, help="Skip markdown link resolution")
@click.option('--chatmode', help="Chatmode to prepend to AGENTS.md files")
@click.option('--watch', is_flag=True, help="Auto-regenerate on changes")
@click.option('--validate', is_flag=True, help="Validate primitives without compiling")
@click.option('--with-constitution/--no-constitution', default=True, show_default=True, help="Include Spec Kit constitution block at top if memory/constitution.md present")
# Distributed compilation options (Task 7)
@click.option('--single-agents', is_flag=True, help="📄 Force single-file compilation (legacy mode)")
@click.option('--verbose', '-v', is_flag=True, help="🔍 Show detailed source attribution and optimizer analysis")
@click.option('--local-only', is_flag=True, help="🏠 Ignore dependencies, compile only local primitives")
@click.option('--clean', is_flag=True, help="🧹 Remove orphaned AGENTS.md files that are no longer generated")
@click.pass_context
def compile(ctx, output, dry_run, no_links, chatmode, watch, validate, with_constitution, 
           single_agents, verbose, local_only, clean):
    """Compile APM context into distributed AGENTS.md files.
    
    By default, uses distributed compilation to generate multiple focused AGENTS.md 
    files across your directory structure following the Minimal Context Principle.
    
    Use --single-agents for traditional single-file compilation when needed.
    
    Advanced options:
    • --dry-run: Preview compilation without writing files (shows placement decisions)
    • --verbose: Show detailed source attribution and optimizer analysis
    • --local-only: Ignore dependencies, compile only local .apm/ primitives
    • --clean: Remove orphaned AGENTS.md files that are no longer generated
    """
    try:
        # Check if this is an APM project first
        from pathlib import Path
        if not Path('apm.yml').exists():
            _rich_error("❌ Not an APM project - no apm.yml found")
            _rich_info("💡 To initialize an APM project, run:")
            _rich_info("   specify init --use-apm")
            _rich_info("   # or")  
            _rich_info("   specify apm init")
            sys.exit(1)

        # Check if there are any instruction files to compile
        from .compilation.constitution import find_constitution
        
        apm_modules_exists = Path("apm_modules").exists()
        constitution_exists = find_constitution(Path(".")).exists()
        
        # Check if .apm directory has actual content
        apm_dir = Path(".apm")
        local_apm_has_content = (apm_dir.exists() and 
                                (any(apm_dir.rglob("*.instructions.md")) or 
                                 any(apm_dir.rglob("*.chatmode.md"))))
        
        # If no primitive sources exist, check deeper to provide better feedback
        if not apm_modules_exists and not local_apm_has_content and not constitution_exists:
            # Check if .apm directories exist but are empty
            has_empty_apm = apm_dir.exists() and not any(apm_dir.rglob("*.instructions.md")) and not any(apm_dir.rglob("*.chatmode.md"))
            
            if has_empty_apm:
                _rich_error("❌ No instruction files found in .apm/ directory")
                _rich_info("💡 To add instructions, create files like:")
                _rich_info("   .apm/instructions/coding-standards.instructions.md")
                _rich_info("   .apm/chatmodes/backend-engineer.chatmode.md")
            else:
                _rich_error("❌ No APM content found to compile")
                _rich_info("💡 To get started:")
                _rich_info("   1. Install APM dependencies: specify apm install <owner>/<repo>")
                _rich_info("   2. Or create local instructions: mkdir -p .apm/instructions")
                _rich_info("   3. Then create .instructions.md or .chatmode.md files")
            
            if not dry_run:  # Don't exit on dry-run to allow testing
                sys.exit(1)

        # Validation-only mode
        if validate:
            _rich_info("Validating APM context...", symbol="gear")
            compiler = AgentsCompiler(".")
            try:
                primitives = discover_primitives(".")
            except Exception as e:
                _rich_error(f"Failed to discover primitives: {e}")
                _rich_info(f"💡 Error details: {type(e).__name__}")
                sys.exit(1)
            validation_errors = compiler.validate_primitives(primitives)
            if validation_errors:
                _display_validation_errors(validation_errors)
                _rich_error(f"Validation failed with {len(validation_errors)} errors")
                sys.exit(1)
            _rich_success("All primitives validated successfully!", symbol="sparkles")
            _rich_info(f"Validated {primitives.count()} primitives:")
            _rich_info(f"  • {len(primitives.chatmodes)} chatmodes")
            _rich_info(f"  • {len(primitives.instructions)} instructions")
            _rich_info(f"  • {len(primitives.contexts)} contexts")
            return

        # Watch mode
        if watch:
            _watch_mode(output, chatmode, no_links, dry_run)
            return

        _rich_info("Starting context compilation...", symbol="cogs")

        # Build config with distributed compilation flags (Task 7)
        config = CompilationConfig.from_apm_yml(
            output_path=output if output != "AGENTS.md" else None,
            chatmode=chatmode,
            resolve_links=not no_links if no_links else None,
            dry_run=dry_run,
            single_agents=single_agents,
            trace=verbose,
            local_only=local_only,
            debug=verbose,
            clean_orphaned=clean
        )
        config.with_constitution = with_constitution

        # Handle distributed vs single-file compilation
        if config.strategy == "distributed" and not single_agents:
            _rich_info("Using distributed compilation (multiple AGENTS.md files)")
            if dry_run:
                _rich_info("Dry run mode: showing placement without writing files", symbol="eye")
            if verbose:
                _rich_info("Verbose mode: showing source attribution and optimizer analysis", symbol="magnifying_glass")
        else:
            _rich_info("Using single-file compilation (legacy mode)", symbol="page")

        # Perform compilation
        compiler = AgentsCompiler(".")
        result = compiler.compile(config)

        if result.success:
            # Handle different compilation modes
            if config.strategy == "distributed" and not single_agents:
                # Distributed compilation results - output already shown by professional formatter
                # Just show final success message
                if dry_run:
                    # Success message for dry run already included in formatter output
                    pass
                else:
                    # Success message for actual compilation
                    _rich_success("Compilation completed successfully!", symbol="check")
                
            else:
                # Traditional single-file compilation - keep existing logic
                # Perform initial compilation in dry-run to get generated body (without constitution)
                intermediate_config = CompilationConfig(
                    output_path=config.output_path,
                    chatmode=config.chatmode,
                    resolve_links=config.resolve_links,
                    dry_run=True,  # force
                    with_constitution=config.with_constitution,
                    strategy="single-file"
                )
                intermediate_result = compiler.compile(intermediate_config)

                if intermediate_result.success:
                    # Perform constitution injection / preservation
                    from apm_cli.compilation.injector import ConstitutionInjector
                    injector = ConstitutionInjector(base_dir=".")
                    output_path = Path(config.output_path)
                    final_content, c_status, c_hash = injector.inject(intermediate_result.content, with_constitution=config.with_constitution, output_path=output_path)

                    # Compute deterministic Build ID (12-char SHA256) over content with placeholder removed
                    from apm_cli.compilation.constants import BUILD_ID_PLACEHOLDER
                    import hashlib
                    lines = final_content.splitlines()
                    # Identify placeholder line index
                    try:
                        idx = lines.index(BUILD_ID_PLACEHOLDER)
                    except ValueError:
                        idx = None
                    hash_input_lines = [l for i, l in enumerate(lines) if i != idx]
                    hash_bytes = "\n".join(hash_input_lines).encode("utf-8")
                    build_id = hashlib.sha256(hash_bytes).hexdigest()[:12]
                    if idx is not None:
                        lines[idx] = f"<!-- Build ID: {build_id} -->"
                        final_content = "\n".join(lines) + ("\n" if final_content.endswith("\n") else "")

                    if not dry_run:
                        # Only rewrite when content materially changes (creation, update, missing constitution case)
                        if c_status in ("CREATED", "UPDATED", "MISSING"):
                            try:
                                _atomic_write(output_path, final_content)
                            except OSError as e:
                                _rich_error(f"Failed to write final AGENTS.md: {e}")
                                sys.exit(1)
                        else:
                            _rich_info("No changes detected; preserving existing AGENTS.md for idempotency")

                    # Report success at the top
                    if dry_run:
                        _rich_success("Context compilation completed successfully (dry run)", symbol="check")
                    else:
                        _rich_success(f"Context compiled successfully to {output_path}", symbol="sparkles")

                    stats = intermediate_result.stats  # timestamp removed; stats remain version + counts
                    
                    # Add spacing before summary table
                    _rich_blank_line()
                    
                    # Single comprehensive compilation summary table
                    try:
                        console = _get_console()
                        if console:
                            from rich.table import Table
                            import os
                            
                            table = Table(title="Compilation Summary", show_header=True, header_style="bold cyan")
                            table.add_column("Component", style="bold white", min_width=15)
                            table.add_column("Count", style="cyan", min_width=8)
                            table.add_column("Details", style="white", min_width=20)

                            # Constitution row
                            constitution_details = f"Hash: {c_hash or '-'}"
                            table.add_row("Spec-kit Constitution", c_status, constitution_details)
                            
                            # Primitives rows
                            table.add_row("Instructions", str(stats.get('instructions', 0)), "✅ All validated")
                            table.add_row("Contexts", str(stats.get('contexts', 0)), "✅ All validated") 
                            table.add_row("Chatmodes", str(stats.get('chatmodes', 0)), "✅ All validated")
                            
                            # Output row with file size
                            try:
                                file_size = os.path.getsize(output_path) if not dry_run else 0
                                size_str = f"{file_size/1024:.1f}KB" if file_size > 0 else "Preview"
                                output_details = f"{output_path.name} ({size_str})"
                            except:
                                output_details = f"{output_path.name}"
                            
                            table.add_row("Output", "✨ SUCCESS", output_details)
                            
                            console.print(table)
                        else:
                            # Fallback for no Rich console
                            _rich_info(f"Processed {stats.get('primitives_found', 0)} primitives:")
                            _rich_info(f"  • {stats.get('instructions', 0)} instructions")
                            _rich_info(f"  • {stats.get('contexts', 0)} contexts")
                            _rich_info(f"Constitution status: {c_status} hash={c_hash or '-'}")
                    except Exception:
                        # Fallback for any errors
                        _rich_info(f"Processed {stats.get('primitives_found', 0)} primitives:")
                        _rich_info(f"  • {stats.get('instructions', 0)} instructions") 
                        _rich_info(f"  • {stats.get('contexts', 0)} contexts")
                        _rich_info(f"Constitution status: {c_status} hash={c_hash or '-'}")

                    if dry_run:
                        preview = final_content[:500] + ("..." if len(final_content) > 500 else "")
                        _rich_panel(preview, title="📋 Generated Content Preview", style="cyan")
                    else:
                        next_steps = [
                            f"Review the generated {output} file",
                            "Install MCP dependencies: apm install",
                            "Execute agentic workflows: apm run <script> --param key=value",
                        ]
                        try:
                            console = _get_console()
                            if console:
                                from rich.panel import Panel
                                steps_content = "\n".join(f"• {step}" for step in next_steps)
                                console.print(Panel(steps_content, title="💡 Next Steps", border_style="blue"))
                            else:
                                _rich_info("Next steps:")
                                for step in next_steps:
                                    click.echo(f"  • {step}")
                        except (ImportError, NameError):
                            _rich_info("Next steps:")
                            for step in next_steps:
                                click.echo(f"  • {step}")
        
        # Common error handling for both compilation modes  
        # Note: Warnings are handled by professional formatters for distributed mode
        if config.strategy != "distributed" or single_agents:
            # Only show warnings for single-file mode (backward compatibility)
            if result.warnings:
                _rich_warning(f"Compilation completed with {len(result.warnings)} warnings:")
                for warning in result.warnings:
                    click.echo(f"  ⚠️  {warning}")

        if result.errors:
            _rich_error(f"Compilation failed with {len(result.errors)} errors:")
            for error in result.errors:
                click.echo(f"  ❌ {error}")
            sys.exit(1)

        # Check for orphaned packages after successful compilation
        try:
            orphaned_packages = _check_orphaned_packages()
            if orphaned_packages:
                _rich_blank_line()
                _rich_warning(f"⚠️ Found {len(orphaned_packages)} orphaned package(s) that were included in compilation:")
                for pkg in orphaned_packages:
                    _rich_info(f"  • {pkg}")
                _rich_info("💡 Run 'specify apm prune' to remove orphaned packages")
        except Exception:
            pass  # Continue if orphan check fails

    except ImportError as e:
        _rich_error(f"Compilation module not available: {e}")
        _rich_info("This might be a development environment issue.")
        sys.exit(1)
    except Exception as e:
        _rich_error(f"Error during compilation: {e}")
        sys.exit(1)


@cli.command(help="Configure APM CLI")
@click.option('--show', is_flag=True, help="Show current configuration")
@click.pass_context
def config(ctx, show):
    """Configure APM CLI settings."""
    try:
        if show:
            try:
                # Lazy import rich table
                from rich.table import Table  # type: ignore
                console = _get_console()
                # Create configuration display
                config_table = Table(title="⚙️  Current APM Configuration", show_header=True, header_style="bold cyan")
                config_table.add_column("Category", style="bold yellow", min_width=12)
                config_table.add_column("Setting", style="white", min_width=15)
                config_table.add_column("Value", style="cyan")
                
                # Show apm.yml if in project
                if Path('apm.yml').exists():
                    config = _load_apm_config()
                    config_table.add_row("Project", "Name", config.get('name', 'Unknown'))
                    config_table.add_row("", "Version", config.get('version', 'Unknown'))
                    config_table.add_row("", "Entrypoint", config.get('entrypoint', 'None'))
                    config_table.add_row("", "MCP Dependencies", str(len(config.get('dependencies', {}).get('mcp', []))))
                    
                    # Show compilation configuration
                    compilation_config = config.get('compilation', {})
                    if compilation_config:
                        config_table.add_row("Compilation", "Output", compilation_config.get('output', 'AGENTS.md'))
                        config_table.add_row("", "Chatmode", compilation_config.get('chatmode', 'auto-detect'))
                        config_table.add_row("", "Resolve Links", str(compilation_config.get('resolve_links', True)))
                    else:
                        config_table.add_row("Compilation", "Status", "Using defaults (no config)")
                else:
                    config_table.add_row("Project", "Status", "Not in an APM project directory")
                
                config_table.add_row("Global", "APM CLI Version", get_version())
                
                console.print(config_table)
                
            except (ImportError, NameError):
                # Fallback display
                _rich_info("Current APM Configuration:")
                
                if Path('apm.yml').exists():
                    config = _load_apm_config()
                    click.echo(f"\n{HIGHLIGHT}Project (apm.yml):{RESET}")
                    click.echo(f"  Name: {config.get('name', 'Unknown')}")
                    click.echo(f"  Version: {config.get('version', 'Unknown')}")
                    click.echo(f"  Entrypoint: {config.get('entrypoint', 'None')}")
                    click.echo(f"  MCP Dependencies: {len(config.get('dependencies', {}).get('mcp', []))}")
                else:
                    _rich_info("Not in an APM project directory")
                    
                click.echo(f"\n{HIGHLIGHT}Global:{RESET}")
                click.echo(f"  APM CLI Version: {get_version()}")
            
        else:
            _rich_info("Use --show to display configuration")
            
    except Exception as e:
        _rich_error(f"Error showing configuration: {e}")
        sys.exit(1)


@cli.group(help="Manage AI runtimes")
def runtime():
    """Manage AI runtime installations and configurations."""
    pass


def _atomic_write(path: Path, data: str) -> None:
    """Atomically write text data to path (best-effort)."""
    import os, tempfile
    fd, tmp_name = tempfile.mkstemp(prefix="apm-write-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(data)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


@cli.group(help="Manage MCP servers")
def mcp():
    """Manage MCP server discovery and information."""
    pass


@runtime.command(help="Set up a runtime")
@click.argument('runtime_name', type=click.Choice(['copilot', 'codex', 'llm']))
@click.option('--version', help="Specific version to install")
@click.option('--vanilla', is_flag=True, help="Install runtime without APM configuration (uses runtime's native defaults)")
def setup(runtime_name, version, vanilla):
    """Set up an AI runtime with APM-managed installation."""
    try:
        _rich_info(f"Setting up {runtime_name} runtime...")
        
        from apm_cli.runtime.manager import RuntimeManager
        
        manager = RuntimeManager()
        success = manager.setup_runtime(runtime_name, version, vanilla)
        
        if not success:
            sys.exit(1)
        else:
            _rich_success(f"{runtime_name} runtime setup complete!", symbol="sparkles")
            
    except Exception as e:
        _rich_error(f"Error setting up runtime: {e}")
        sys.exit(1)


@runtime.command(help="List available and installed runtimes")
def list():
    """List all available runtimes and their installation status."""
    try:
        from apm_cli.runtime.manager import RuntimeManager
        
        manager = RuntimeManager()
        runtimes = manager.list_runtimes()
        
        try:
            from rich.table import Table  # type: ignore
            console = _get_console()
            # Create a nice table for runtimes
            table = Table(title="🤖 Available Runtimes", show_header=True, header_style="bold cyan")
            table.add_column("Status", style="green", width=8)
            table.add_column("Runtime", style="bold white", min_width=10)
            table.add_column("Description", style="white")
            table.add_column("Details", style="muted")
            
            for name, info in runtimes.items():
                status_icon = STATUS_SYMBOLS["check"] if info["installed"] else STATUS_SYMBOLS["cross"]
                status_text = "Installed" if info["installed"] else "Not installed"
                
                details = ""
                if info["installed"]:
                    details_list = [f"Path: {info['path']}"]
                    if "version" in info:
                        details_list.append(f"Version: {info['version']}")
                    details = "\n".join(details_list)
                
                table.add_row(
                    f"{status_icon} {status_text}",
                    name,
                    info['description'],
                    details
                )
            
            console.print(table)
            
        except (ImportError, NameError):
            # Fallback to simple output
            _rich_info("Available Runtimes:")
            click.echo()
            
            for name, info in runtimes.items():
                status_icon = "✅" if info["installed"] else "❌"
                status_text = "Installed" if info["installed"] else "Not installed"
                
                click.echo(f"{status_icon} {HIGHLIGHT}{name}{RESET}")
                click.echo(f"   Description: {info['description']}")
                click.echo(f"   Status: {status_text}")
                
                if info["installed"]:
                    click.echo(f"   Path: {info['path']}")
                    if "version" in info:
                        click.echo(f"   Version: {info['version']}")
                
                click.echo()
            
    except Exception as e:
        _rich_error(f"Error listing runtimes: {e}")
        sys.exit(1)


@runtime.command(help="Remove an installed runtime")
@click.argument('runtime_name', type=click.Choice(['copilot', 'codex', 'llm']))
@click.confirmation_option(prompt='Are you sure you want to remove this runtime?')
def remove(runtime_name):
    """Remove an installed runtime from APM management."""
    try:
        _rich_info(f"Removing {runtime_name} runtime...")
        
        from apm_cli.runtime.manager import RuntimeManager
        
        manager = RuntimeManager()
        success = manager.remove_runtime(runtime_name)
        
        if not success:
            sys.exit(1)
        else:
            _rich_success(f"{runtime_name} runtime removed successfully!", symbol="sparkles")
            
    except Exception as e:
        _rich_error(f"Error removing runtime: {e}")
        sys.exit(1)


@runtime.command(help="Check which runtime will be used")
def status():
    """Show which runtime APM will use for execution."""
    try:
        from apm_cli.runtime.manager import RuntimeManager
        
        manager = RuntimeManager()
        available_runtime = manager.get_available_runtime()
        preference = manager.get_runtime_preference()
        
        try:
            # Create a nice status display
            status_content = f"""Preference order: {' → '.join(preference)}

Active runtime: {available_runtime if available_runtime else 'None available'}"""
            
            if not available_runtime:
                status_content += f"\n\n{STATUS_SYMBOLS['info']} Run 'apm runtime setup copilot' to install the primary runtime"
            
            _rich_panel(status_content, title="📊 Runtime Status", style="cyan")
            
        except (ImportError, NameError):
            # Fallback display
            _rich_info("Runtime Status:")
            click.echo()
            
            click.echo(f"Preference order: {' → '.join(preference)}")
            
            if available_runtime:
                _rich_success(f"Active runtime: {available_runtime}")
            else:
                _rich_error("No runtimes available")
                _rich_info("Run 'apm runtime setup copilot' to install the primary runtime")
            
    except Exception as e:
        _rich_error(f"Error checking runtime status: {e}")
        sys.exit(1)


@mcp.command(help="Search MCP servers in registry")
@click.argument('query', required=True)
@click.option('--limit', default=10, help="Number of results to show")
@click.pass_context
def search(ctx, query, limit):
    """Search for MCP servers in the registry."""
    try:
        from apm_cli.registry.integration import RegistryIntegration
        registry = RegistryIntegration("https://api.mcp.github.com")
        servers = registry.search_packages(query)[:limit]
        
        console = _get_console()
        if not console:
            # Fallback for non-rich environments
            click.echo(f"Searching for: {query}")
            if not servers:
                click.echo("No servers found")
                return
            for server in servers:
                click.echo(f"  {server.get('name', 'Unknown')}")
                click.echo(f"    {server.get('description', 'No description')[:80]}")
            return
        
        # Professional header with search context
        console.print(f"\n[bold cyan]MCP Registry Search[/bold cyan]")
        console.print(f"[muted]Query: {query}[/muted]")
        
        if not servers:
            console.print(f"\n[yellow]⚠[/yellow] No MCP servers found matching '[bold]{query}[/bold]'")
            console.print("\n[muted]💡 Try broader search terms or check the spelling[/muted]")
            return
        
        # Results summary
        total_shown = len(servers)
        console.print(f"\n[green]✓[/green] Found [bold]{total_shown}[/bold] MCP server{'s' if total_shown != 1 else ''}")
        
        # Professional results table
        from rich.table import Table
        table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
        table.add_column("Name", style="bold white", no_wrap=True, min_width=20)
        table.add_column("Description", style="white", ratio=1)
        table.add_column("Latest", style="cyan", justify="center", min_width=8)
        
        for server in servers:
            name = server.get("name", "Unknown")
            desc = server.get("description", "No description available")
            version = server.get("version", "—")
            
            # Intelligent description truncation
            if len(desc) > 80:
                # Find a good break point near the limit
                truncate_pos = 77
                if ' ' in desc[70:85]:
                    space_pos = desc.rfind(' ', 70, 85)
                    if space_pos > 70:
                        truncate_pos = space_pos
                desc = desc[:truncate_pos] + "..."
            
            table.add_row(name, desc, version)
        
        console.print(table)
        
        # Helpful next steps
        console.print(f"\n[muted]💡 Use [bold cyan]apm mcp show <name>[/bold cyan] for detailed information[/muted]")
        if total_shown == limit:
            console.print(f"[muted]   Use [bold cyan]--limit {limit * 2}[/bold cyan] to see more results[/muted]")
        
    except Exception as e:
        _rich_error(f"Error searching registry: {e}")
        sys.exit(1)


@mcp.command(help="Show detailed MCP server information")
@click.argument('server_name', required=True)
@click.pass_context  
def show(ctx, server_name):
    """Show detailed information about an MCP server."""
    try:
        from apm_cli.registry.integration import RegistryIntegration
        registry = RegistryIntegration("https://api.mcp.github.com")
        
        console = _get_console()
        if not console:
            # Fallback for non-rich environments
            click.echo(f"Getting details for: {server_name}")
            try:
                server_info = registry.get_package_info(server_name)
                click.echo(f"Name: {server_info.get('name', 'Unknown')}")
                click.echo(f"Description: {server_info.get('description', 'No description')}")
                click.echo(f"Repository: {server_info.get('repository', {}).get('url', 'Unknown')}")
            except ValueError:
                click.echo(f"Server '{server_name}' not found")
                sys.exit(1)
            return
        
        # Professional loading indicator
        console.print(f"\n[bold cyan]MCP Server Details[/bold cyan]")
        console.print(f"[muted]Fetching: {server_name}[/muted]")
        
        try:
            server_info = registry.get_package_info(server_name)
        except ValueError:
            console.print(f"\n[red]✗[/red] MCP server '[bold]{server_name}[/bold]' not found in registry")
            console.print(f"\n[muted]💡 Use [bold cyan]apm mcp search <query>[/bold cyan] to find available servers[/muted]")
            sys.exit(1)
        
        # Main server information in professional table format
        name = server_info.get('name', 'Unknown')
        description = server_info.get('description', 'No description available')
        
        # Get key metadata
        version = "Unknown"
        if "version_detail" in server_info:
            version = server_info["version_detail"].get("version", "Unknown")
        elif "version" in server_info:
            version = server_info["version"]
        
        repo_url = "Unknown"
        if "repository" in server_info:
            repo_url = server_info["repository"].get("url", "Unknown")
        
        # Professional server info table with consistent styling
        from rich.table import Table
        
        # Main server information table
        info_table = Table(title=f"📦 MCP Server: {name}", show_header=True, header_style="bold cyan", border_style="cyan")
        info_table.add_column("Property", style="bold white", min_width=12)
        info_table.add_column("Value", style="white", min_width=40)
        
        info_table.add_row("Name", f"[bold white]{name}[/bold white]")
        info_table.add_row("Version", f"[cyan]{version}[/cyan]")
        info_table.add_row("Description", description)
        info_table.add_row("Repository", repo_url)
        if "id" in server_info:
            info_table.add_row("Registry ID", server_info["id"][:8] + "...")
        
        # Add deployment type information
        remotes = server_info.get("remotes", [])
        packages = server_info.get("packages", [])
        
        deployment_info = []
        if remotes:
            for remote in remotes:
                transport_type = remote.get("transport_type", "unknown")
                if transport_type == "sse":
                    deployment_info.append("🌐 Remote SSE Endpoint")
        if packages:
            deployment_info.append("📦 Local Package")
        
        if deployment_info:
            info_table.add_row("Deployment Type", " + ".join(deployment_info))
        
        console.print(info_table)
        
        # Show remote endpoints if available
        if remotes:
            remote_table = Table(title="🌐 Remote Endpoints", show_header=True, header_style="bold cyan", border_style="cyan")
            remote_table.add_column("Type", style="yellow", width=10)
            remote_table.add_column("URL", style="white", min_width=40)
            remote_table.add_column("Features", style="cyan", min_width=20)
            
            for remote in remotes:
                transport_type = remote.get("transport_type", "unknown")
                url = remote.get("url", "unknown")
                
                # Describe features/limitations of remote endpoints
                features = "Hosted by provider"
                if "github" in name.lower():
                    features = "No toolset customization"
                
                remote_table.add_row(transport_type.upper(), url, features)
            
            console.print(remote_table)
        
        # Installation packages in consistent table format
        if packages:
            pkg_table = Table(title="📦 Local Packages", show_header=True, header_style="bold cyan", border_style="cyan")
            pkg_table.add_column("Registry", style="yellow", width=10)
            pkg_table.add_column("Package", style="white", min_width=25)
            pkg_table.add_column("Runtime", style="cyan", width=8, justify="center")
            pkg_table.add_column("Features", style="green", min_width=20)
            
            for pkg in packages:
                registry_name = pkg.get("registry_name", "unknown")
                pkg_name = pkg.get("name", "unknown")
                runtime_hint = pkg.get("runtime_hint", "—")
                
                # Describe features of local packages
                features = "Full configuration control"
                if "github" in name.lower():
                    features = "Supports GITHUB_TOOLSETS"
                
                # Truncate long package names intelligently
                if len(pkg_name) > 25:
                    pkg_name = pkg_name[:22] + "..."
                
                pkg_table.add_row(registry_name, pkg_name, runtime_hint, features)
            
            console.print(pkg_table)
        
        # Installation instructions in structured table format
        install_name = server_info.get('name', server_name)
        install_table = Table(title="✨ Installation Guide", show_header=True, header_style="bold cyan", border_style="green")
        install_table.add_column("Step", style="bold white", width=5)
        install_table.add_column("Action", style="white", min_width=30)
        install_table.add_column("Command/Config", style="cyan", min_width=25)
        
        install_table.add_row("1", "Add to apm.yml dependencies", f"[yellow]mcp:[/yellow] [cyan]- {install_name}[/cyan]")
        install_table.add_row("2", "Install dependencies", "[bold cyan]apm install[/bold cyan]")
        install_table.add_row("3", "Direct install (coming soon)", f"[bold cyan]apm install {install_name}[/bold cyan]")
        
        console.print(install_table)
        
    except Exception as e:
        _rich_error(f"Error getting server details: {e}")
        sys.exit(1)


@mcp.command(help="List all available MCP servers")
@click.option('--limit', default=20, help="Number of results to show")
@click.pass_context
def list(ctx, limit):
    """List all available MCP servers in the registry."""
    try:
        from apm_cli.registry.integration import RegistryIntegration
        registry = RegistryIntegration("https://api.mcp.github.com")
        
        console = _get_console()
        if not console:
            # Fallback for non-rich environments
            click.echo("Fetching available MCP servers...")
            servers = registry.list_available_packages()[:limit]
            if not servers:
                click.echo("No servers found")
                return
            for server in servers:
                click.echo(f"  {server.get('name', 'Unknown')}")
                click.echo(f"    {server.get('description', 'No description')[:80]}")
            return
        
        # Professional header
        console.print(f"\n[bold cyan]MCP Registry Catalog[/bold cyan]")
        console.print(f"[muted]Discovering available servers...[/muted]")
        
        servers = registry.list_available_packages()[:limit]
        
        if not servers:
            console.print(f"\n[yellow]⚠[/yellow] No MCP servers found in registry")
            console.print(f"\n[muted]💡 The registry might be temporarily unavailable[/muted]")
            return
        
        # Results summary with pagination info
        total_shown = len(servers)
        console.print(f"\n[green]✓[/green] Showing [bold]{total_shown}[/bold] MCP servers")
        if total_shown == limit:
            console.print(f"[muted]Use [bold cyan]--limit {limit * 2}[/bold cyan] to see more results[/muted]")
        
        # Professional catalog table
        from rich.table import Table
        table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
        table.add_column("Name", style="bold white", no_wrap=True, min_width=25)
        table.add_column("Description", style="white", ratio=1)
        table.add_column("Latest", style="cyan", justify="center", min_width=8)
        
        for server in servers:
            name = server.get("name", "Unknown")
            desc = server.get("description", "No description available")
            version = server.get("version", "—")
            
            # Intelligent description truncation
            if len(desc) > 80:
                # Find a good break point near the limit
                truncate_pos = 77
                if ' ' in desc[70:85]:
                    space_pos = desc.rfind(' ', 70, 85)
                    if space_pos > 70:
                        truncate_pos = space_pos
                desc = desc[:truncate_pos] + "..."
            
            table.add_row(name, desc, version)
        
        console.print(table)
        
        # Helpful navigation
        console.print(f"\n[muted]💡 Use [bold cyan]apm mcp show <name>[/bold cyan] for detailed information[/muted]")
        console.print(f"[muted]   Use [bold cyan]apm mcp search <query>[/bold cyan] to find specific servers[/muted]")
        
    except Exception as e:
        _rich_error(f"Error listing servers: {e}")
        sys.exit(1)


def _interactive_project_setup(default_name):
    """Interactive setup for new APM projects."""
    try:
        # Lazy import rich pieces
        from rich.console import Console  # type: ignore
        from rich.panel import Panel  # type: ignore
        from rich.prompt import Prompt, Confirm  # type: ignore
        console = _get_console() or Console()
        console.print("\n[info]Setting up your APM project...[/info]")
        console.print("[muted]Press ^C at any time to quit.[/muted]\n")

        name = Prompt.ask("Project name", default=default_name).strip()
        version = Prompt.ask("Version", default="1.0.0").strip()
        description = Prompt.ask("Description", default=f"A {name} APM application").strip()
        author = Prompt.ask("Author", default="Your Name").strip()

        summary_content = f"""name: {name}
version: {version}
description: {description}
author: {author}"""
        console.print(Panel(summary_content, title="About to create", border_style="cyan"))

        if not Confirm.ask("\nIs this OK?", default=True):
            console.print("[info]Aborted.[/info]")
            sys.exit(0)
        
    except (ImportError, NameError):
        # Fallback to click prompts
        _rich_info("Setting up your APM project...")
        _rich_info("Press ^C at any time to quit.")
        
        name = click.prompt("Project name", default=default_name).strip()
        version = click.prompt("Version", default="1.0.0").strip()
        description = click.prompt("Description", default=f"A {name} APM application").strip()
        author = click.prompt("Author", default="Your Name").strip()
        
        click.echo(f"\n{INFO}About to create:{RESET}")
        click.echo(f"  name: {name}")
        click.echo(f"  version: {version}")
        click.echo(f"  description: {description}")
        click.echo(f"  author: {author}")
        
        if not click.confirm("\nIs this OK?", default=True):
            _rich_info("Aborted.")
            sys.exit(0)
    
    return {
        'name': name,
        'version': version,
        'description': description,
        'author': author
    }


def _merge_existing_config(default_name):
    """Merge existing apm.yml with defaults for missing fields."""
    try:
        with open('apm.yml', 'r') as f:
            yaml = _lazy_yaml()
            existing_config = yaml.safe_load(f) or {}
    except Exception:
        existing_config = {}
    
    # Preserve existing values, fill in missing ones
    config = {
        'name': existing_config.get('name', default_name),
        'version': existing_config.get('version', '1.0.0'),
        'description': existing_config.get('description', f"A {default_name} APM application"),
        'author': existing_config.get('author', 'Your Name')
    }
    
    _rich_info("Preserving existing configuration where possible")
    return config


def _get_default_config(project_name):
    """Get default configuration for new projects."""
    return {
        'name': project_name,
        'version': '1.0.0',
        'description': f"A {project_name} APM application",
        'author': 'Your Name'
    }


def _create_project_files(config):
    """Create project files from configuration."""
    # Create apm.yml
    apm_yml_content = _load_template_file('hello-world', 'apm.yml', 
                                          project_name=config['name'],
                                          version=config.get('version', '1.0.0'),
                                          description=config.get('description', f"A {config['name']} APM application"),
                                          author=config.get('author', 'Your Name'))
    with open('apm.yml', 'w') as f:
        f.write(apm_yml_content)
    
    # Create hello-world.prompt.md from template
    prompt_content = _load_template_file('hello-world', 'hello-world.prompt.md',
                                         project_name=config['name'])
    with open('hello-world.prompt.md', 'w') as f:
        f.write(prompt_content)
        
    # Create feature-implementation.prompt.md from template
    feature_content = _load_template_file('hello-world', 'feature-implementation.prompt.md',
                                         project_name=config['name'])
    with open('feature-implementation.prompt.md', 'w') as f:
        f.write(feature_content)
        
    # Create README.md from template
    readme_content = _load_template_file('hello-world', 'README.md',
                                         project_name=config['name'])
    with open('README.md', 'w') as f:
        f.write(readme_content)
    
    # Create .apm directory structure and copy all primitive files
    apm_dir = Path('.apm')
    apm_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    for subdir in ['chatmodes', 'instructions', 'context']:
        (apm_dir / subdir).mkdir(exist_ok=True)
    
    # Copy primitive files
    primitive_files = [
        '.apm/chatmodes/default.chatmode.md',
        '.apm/chatmodes/backend-engineer.chatmode.md',
        '.apm/instructions/typescript.instructions.md',
        '.apm/instructions/python.instructions.md',
        '.apm/instructions/testing.instructions.md',
        '.apm/context/project-info.context.md',
        '.apm/context/architecture.context.md'
    ]
    
    for primitive_file in primitive_files:
        try:
            primitive_content = _load_template_file('hello-world', primitive_file,
                                                   project_name=config['name'])
            output_path = Path(primitive_file)
            with open(output_path, 'w') as f:
                f.write(primitive_content)
        except Exception as e:
            # Don't fail if individual primitive files can't be loaded
            _rich_warning(f"Could not create {primitive_file}: {e}")
            continue


def main():
    """Main entry point for the CLI."""
    try:
        cli(obj={})
    except Exception as e:
        click.echo(f"{ERROR}Error: {e}{RESET}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
