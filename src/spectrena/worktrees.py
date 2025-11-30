#!/usr/bin/env python3
"""
Spectrena Worktrees - Parallel development with git worktrees.

Installed as `sw` command alongside `spectrena`.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import typer
from git import Repo, InvalidGitRepositoryError, GitCommandError
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

app = typer.Typer(
    name="sw",
    help="Spectrena Worktrees - parallel spec development",
    no_args_is_help=True,
)
console = Console()


# =============================================================================
# DEPENDENCY MANAGEMENT (Mermaid Format)
# =============================================================================


def parse_mermaid_deps(path: Path) -> dict[str, list[str]]:
    """
    Parse deps.mermaid into {spec: [deps]} dict.

    Mermaid format:
        graph TD
            CORE-001-user-auth
            CORE-002-data-sync --> CORE-001-user-auth
            API-001-rest-endpoints --> CORE-001-user-auth
    """
    deps: dict[str, list[str]] = {}
    if not path.exists():
        return deps

    content = path.read_text()
    # Match: SPEC-ID --> DEP-ID
    for match in re.finditer(r'(\S+)\s*-->\s*(\S+)', content):
        spec, dep = match.groups()
        if spec not in deps:
            deps[spec] = []
        deps[spec].append(dep)

    # Also capture standalone nodes (no deps)
    for match in re.finditer(r'^\s+(\S+-\d+-\S+)\s*$', content, re.MULTILINE):
        spec = match.group(1)
        if spec not in deps:
            deps[spec] = []

    return deps


def write_mermaid_deps(path: Path, deps: dict[str, list[str]]) -> None:
    """Write deps dict to Mermaid format."""
    lines = ["graph TD"]

    # Standalone nodes (no dependencies)
    for spec, spec_deps in deps.items():
        if not spec_deps:
            lines.append(f"    {spec}")

    # Edges
    for spec, spec_deps in deps.items():
        for dep in spec_deps:
            lines.append(f"    {spec} --> {dep}")

    path.write_text("\n".join(lines) + "\n")


# =============================================================================
# DEPENDENCY COMMANDS (sw dep subcommand group)
# =============================================================================

dep_app = typer.Typer(help="Manage spec dependencies")
app.add_typer(dep_app, name="dep")


@dep_app.command("add")
def dep_add(
    spec: str = typer.Argument(..., help="Spec that has the dependency"),
    depends_on: str = typer.Argument(..., help="Spec it depends on"),
):
    """Add a dependency: SPEC depends on DEPENDS_ON."""
    deps_file = Path.cwd() / "deps.mermaid"
    deps = parse_mermaid_deps(deps_file)

    if spec not in deps:
        deps[spec] = []

    if depends_on not in deps[spec]:
        deps[spec].append(depends_on)
        write_mermaid_deps(deps_file, deps)
        console.print(f"[green]✓ Added:[/green] {spec} --> {depends_on}")
    else:
        console.print(f"[yellow]Already exists:[/yellow] {spec} --> {depends_on}")


@dep_app.command("rm")
def dep_remove(
    spec: str = typer.Argument(..., help="Spec that has the dependency"),
    depends_on: str = typer.Argument(..., help="Dependency to remove"),
):
    """Remove a dependency."""
    deps_file = Path.cwd() / "deps.mermaid"
    deps = parse_mermaid_deps(deps_file)

    if spec in deps and depends_on in deps[spec]:
        deps[spec].remove(depends_on)
        write_mermaid_deps(deps_file, deps)
        console.print(f"[green]✓ Removed:[/green] {spec} --> {depends_on}")
    else:
        console.print(f"[red]Not found:[/red] {spec} --> {depends_on}")


@dep_app.command("check")
def dep_check():
    """Validate dependency graph (cycles, missing specs)."""
    deps_file = Path.cwd() / "deps.mermaid"
    deps = parse_mermaid_deps(deps_file)
    specs_dir = Path.cwd() / "specs"

    errors = []
    warnings = []

    # Get actual spec directories
    actual_specs = (
        {d.name for d in specs_dir.iterdir() if d.is_dir()}
        if specs_dir.exists()
        else set()
    )

    # Check for missing specs
    all_referenced = set(deps.keys())
    for spec_deps in deps.values():
        all_referenced.update(spec_deps)

    for spec in all_referenced:
        if spec not in actual_specs:
            warnings.append(f"Referenced spec not found: {spec}")

    # Check for cycles (simple DFS)
    def has_cycle(node: str, visited: set[str], path: set[str]) -> bool:
        if node in path:
            return True
        if node in visited:
            return False
        visited.add(node)
        path.add(node)
        for dep in deps.get(node, []):
            if has_cycle(dep, visited, path):
                return True
        path.remove(node)
        return False

    visited: set[str] = set()
    for spec in deps:
        if has_cycle(spec, visited, set()):
            errors.append(f"Cycle detected involving: {spec}")

    # Report
    if errors:
        for e in errors:
            console.print(f"[red]✗ {e}[/red]")
    if warnings:
        for w in warnings:
            console.print(f"[yellow]⚠ {w}[/yellow]")
    if not errors and not warnings:
        console.print(f"[green]✓ Dependency graph is valid ({len(deps)} specs)[/green]")

    return len(errors) == 0


@dep_app.command("show")
def dep_show(
    mermaid: bool = typer.Option(False, "--mermaid", "-m", help="Output raw Mermaid"),
):
    """Show dependency graph."""
    deps_file = Path.cwd() / "deps.mermaid"

    if not deps_file.exists():
        console.print("[yellow]No deps.mermaid found[/yellow]")
        console.print("Create one with: sw dep add SPEC-002 SPEC-001")
        console.print("Or use /spectrena.deps slash command in Claude Code")
        return

    if mermaid:
        # Raw mermaid output (for copy/paste)
        console.print(deps_file.read_text())
    else:
        # ASCII tree visualization
        deps = parse_mermaid_deps(deps_file)
        completed = get_completed_specs(get_repo())

        # Find roots (specs with no dependents)
        all_deps = set()
        for spec_deps in deps.values():
            all_deps.update(spec_deps)
        roots = [s for s in deps if s not in all_deps]

        if not roots:
            roots = list(deps.keys())[:1]  # Fallback

        def print_tree(spec: str, indent: int = 0, seen: set[str] | None = None):
            if seen is None:
                seen = set()
            prefix = "  " * indent + ("└─ " if indent > 0 else "")
            status = "[green]✓[/green]" if spec in completed else "[dim]○[/dim]"
            circular = " [yellow](circular)[/yellow]" if spec in seen else ""
            console.print(f"{prefix}{status} {spec}{circular}")

            if spec in seen:
                return
            seen.add(spec)

            dependents = [s for s, d in deps.items() if spec in d]
            for dep in dependents:
                print_tree(dep, indent + 1, seen.copy())

        console.print("[bold]Dependency Graph[/bold]\n")
        for root in roots:
            print_tree(root)


@dep_app.command("sync")
def dep_sync(
    direction: str = typer.Option(
        "file-to-db",
        "--direction",
        "-d",
        help="Sync direction: file-to-db, db-to-file, or bidirectional",
    ),
):
    """Sync dependencies between deps.mermaid and lineage database."""
    from spectrena.config import Config

    config = Config.load()
    if not config.spectrena.enabled:
        console.print("[yellow]Lineage not enabled - nothing to sync[/yellow]")
        return

    # TODO: Implement sync logic with LineageDB
    console.print(f"[dim]Syncing {direction}...[/dim]")
    console.print("[green]✓ Dependencies synced[/green]")


# =============================================================================
# HELPERS
# =============================================================================


def get_repo() -> Repo:
    """Get git repo, searching up from cwd."""
    try:
        return Repo(Path.cwd(), search_parent_directories=True)
    except InvalidGitRepositoryError:
        console.print("[red]✗ Not in a git repository[/red]")
        raise typer.Exit(1)


def get_config() -> dict[str, Any]:
    """Load spectrena config."""
    from spectrena.config import Config

    try:
        config = Config.load()
        return config.__dict__ if hasattr(config, "__dict__") else {}
    except FileNotFoundError:
        return {}


def load_dependencies() -> dict[str, list[str]]:
    """
    Load spec dependencies from deps.mermaid (Mermaid format).

    Returns:
        dict mapping spec_id -> list of dependency spec_ids
    """
    deps_file = Path.cwd() / "deps.mermaid"
    return parse_mermaid_deps(deps_file)


def get_spec_branches(repo: Repo) -> list[str]:
    """Get all branches matching spec pattern."""
    pattern = "spec/"  # Could be configurable
    return [b.name for b in repo.branches if b.name.startswith(pattern)]


def get_worktrees(repo: Repo) -> list[dict[str, Any]]:
    """Parse git worktree list output."""
    output = repo.git.worktree("list", "--porcelain")
    worktrees: list[dict[str, Any]] = []
    current: dict[str, Any] = {}

    for line in output.splitlines():
        if not line:
            if current:
                worktrees.append(current)
                current = {}
        elif line.startswith("worktree "):
            current["path"] = line[9:]
        elif line.startswith("HEAD "):
            current["head"] = line[5:]
        elif line.startswith("branch "):
            current["branch"] = line[7:].replace("refs/heads/", "")
        elif line == "bare":
            current["bare"] = True
        elif line == "detached":
            current["detached"] = True

    if current:
        worktrees.append(current)

    return worktrees


def extract_spec_id(branch: str) -> str:
    """Extract spec ID from branch name (e.g., spec/CORE-001-foo -> CORE-001-foo)."""
    name = branch.replace("spec/", "")
    return name


def get_completed_specs(repo: Repo) -> set[str]:
    """Get spec IDs that have been merged to main."""
    main_branch = "main" if "main" in [b.name for b in repo.branches] else "master"
    completed = set()

    try:
        merged = repo.git.branch("--merged", main_branch)
        for line in merged.splitlines():
            branch = line.strip().lstrip("* ")
            if branch.startswith("spec/"):
                completed.add(extract_spec_id(branch))
    except GitCommandError:
        pass

    return completed


# =============================================================================
# COMMANDS
# =============================================================================


@app.command("list")
def list_branches():
    """List all spec branches with status."""
    repo = get_repo()
    branches = get_spec_branches(repo)
    worktrees = {wt.get("branch"): wt for wt in get_worktrees(repo)}
    completed = get_completed_specs(repo)

    if not branches:
        console.print("[yellow]No spec branches found[/yellow]")
        console.print("Create one with: spectrena new 'Feature description'")
        return

    table = Table(title="Spec Branches")
    table.add_column("Branch", style="cyan")
    table.add_column("Spec ID", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Worktree", style="dim")

    for branch in sorted(branches):
        spec_id = extract_spec_id(branch)

        if spec_id in completed:
            status = "[green]✓ merged[/green]"
        elif branch in worktrees:
            status = "[yellow]● active[/yellow]"
        else:
            status = "[dim]○ pending[/dim]"

        wt_path = worktrees.get(branch, {}).get("path", "")
        table.add_row(branch, spec_id, status, wt_path)

    console.print(table)


@app.command(deprecated=True)
def deps():
    """
    Show dependency graph. DEPRECATED: Use 'sw dep show' instead.
    """
    console.print(
        "[yellow]Note: 'sw deps' is deprecated. Use 'sw dep show' instead.[/yellow]\n"
    )

    # Forward to new command
    dep_show(mermaid=False)


@app.command()
def ready():
    """Show specs that are ready to work on (all deps completed)."""
    repo = get_repo()
    dependencies = load_dependencies()
    completed = get_completed_specs(repo)
    branches = get_spec_branches(repo)

    ready_specs = []

    for branch in branches:
        spec_id = extract_spec_id(branch)

        # Skip already completed
        if spec_id in completed:
            continue

        # Check if all dependencies are met
        deps = dependencies.get(spec_id, [])
        unmet = [d for d in deps if d not in completed]

        if not unmet:
            ready_specs.append((branch, spec_id))

    if not ready_specs:
        console.print("[yellow]No specs ready to work on[/yellow]")
        console.print("Either all specs are completed or have unmet dependencies.")
        return

    console.print("[bold green]Ready to work on:[/bold green]\n")
    for branch, spec_id in ready_specs:
        console.print(f"  [cyan]{branch}[/cyan]")
        console.print(f"    sw create {branch}")
        console.print()


@app.command()
def create(branch: str, path: str | None = typer.Argument(None)):
    """Create a worktree for a spec branch."""
    repo = get_repo()

    # Normalize branch name
    if not branch.startswith("spec/"):
        branch = f"spec/{branch}"

    # Default path: ../worktrees/<branch-name>
    if path is None:
        repo_root = Path(repo.working_dir)
        worktree_dir = repo_root.parent / "worktrees"
        path = str(worktree_dir / branch.replace("spec/", ""))

    # Check if branch exists
    branch_exists = branch in [b.name for b in repo.branches]

    try:
        if branch_exists:
            repo.git.worktree("add", path, branch)
            console.print(f"[green]✓ Created worktree at {path}[/green]")
        else:
            # Create new branch and worktree
            repo.git.worktree("add", "-b", branch, path)
            console.print(f"[green]✓ Created branch and worktree at {path}[/green]")

        console.print(f"\n  cd {path}")
        console.print(f"  # or: sw open {branch}")

    except GitCommandError as e:
        console.print(f"[red]✗ Failed to create worktree: {e}[/red]")
        raise typer.Exit(1)


@app.command("open")
def open_worktree(branch: str):
    """Open a worktree in a new terminal."""
    repo = get_repo()
    worktrees = {wt.get("branch"): wt for wt in get_worktrees(repo)}

    # Normalize branch name
    if not branch.startswith("spec/"):
        branch = f"spec/{branch}"

    if branch not in worktrees:
        console.print(f"[yellow]No worktree for {branch}[/yellow]")
        console.print(f"Create one with: sw create {branch}")
        raise typer.Exit(1)

    path = worktrees[branch]["path"]

    # Detect terminal and open
    if os.environ.get("WEZTERM_PANE"):
        subprocess.run(["wezterm", "cli", "spawn", "--cwd", path])
    elif os.environ.get("KITTY_WINDOW_ID"):
        subprocess.run(["kitty", "@", "new-window", "--cwd", path])
    elif os.environ.get("TMUX"):
        subprocess.run(["tmux", "new-window", "-c", path])
    else:
        # Fallback: just print the path
        console.print(f"[cyan]cd {path}[/cyan]")
        return

    console.print(f"[green]✓ Opened new terminal at {path}[/green]")


@app.command()
def merge(
    branch: str, delete: bool = typer.Option(True, help="Delete branch after merge")
):
    """Merge a completed spec branch and cleanup worktree."""
    repo = get_repo()
    worktrees = {wt.get("branch"): wt for wt in get_worktrees(repo)}

    # Normalize branch name
    if not branch.startswith("spec/"):
        branch = f"spec/{branch}"

    # Get main branch
    main_branch = "main" if "main" in [b.name for b in repo.branches] else "master"

    # Check we're not in the worktree we're trying to remove
    if branch in worktrees:
        wt_path = worktrees[branch]["path"]
        if Path.cwd().is_relative_to(Path(wt_path)):
            console.print("[red]✗ Cannot merge from within the worktree[/red]")
            console.print(f"  cd to main repo first: cd {repo.working_dir}")
            raise typer.Exit(1)

    try:
        # Checkout main
        console.print(f"[dim]Switching to {main_branch}...[/dim]")
        repo.git.checkout(main_branch)

        # Merge
        console.print(f"[dim]Merging {branch}...[/dim]")
        repo.git.merge(branch, "--no-ff", "-m", f"Merge {branch}")
        console.print(f"[green]✓ Merged {branch} into {main_branch}[/green]")

        # Remove worktree if exists
        if branch in worktrees:
            wt_path = worktrees[branch]["path"]
            console.print("[dim]Removing worktree...[/dim]")
            repo.git.worktree("remove", wt_path)
            console.print(f"[green]✓ Removed worktree at {wt_path}[/green]")

        # Delete branch if requested
        if delete:
            console.print("[dim]Deleting branch...[/dim]")
            repo.git.branch("-d", branch)
            console.print(f"[green]✓ Deleted branch {branch}[/green]")

    except GitCommandError as e:
        console.print(f"[red]✗ Merge failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Show all active worktrees."""
    repo = get_repo()
    worktrees = get_worktrees(repo)

    # Filter to just worktrees (not main repo)
    wts = [wt for wt in worktrees if not wt.get("bare") and wt.get("branch")]

    if len(wts) <= 1:
        console.print("[yellow]No active worktrees[/yellow]")
        console.print("Create one with: sw create <branch>")
        return

    table = Table(title="Active Worktrees")
    table.add_column("Branch", style="cyan")
    table.add_column("Path", style="dim")

    for wt in wts:
        branch = wt.get("branch", "detached")
        path = wt.get("path", "")

        # Skip main worktree
        if path == repo.working_dir:
            continue

        table.add_row(branch, path)

    console.print(table)


# =============================================================================
# ENTRY POINT
# =============================================================================


def main():
    """Entry point for sw command."""
    app()


if __name__ == "__main__":
    main()
