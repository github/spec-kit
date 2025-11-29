#!/usr/bin/env python3
"""
Spectrena Worktrees - Parallel development with git worktrees.

Installed as `sw` command alongside `spectrena`.
"""

import os
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
    Load spec dependencies from .specify/dependencies.txt

    Format:
        SPEC-002: SPEC-001
        SPEC-003: SPEC-001, SPEC-002

    Returns:
        dict mapping spec_id -> list of dependency spec_ids
    """
    deps_file = Path.cwd() / ".specify" / "dependencies.txt"
    deps = {}

    if not deps_file.exists():
        return deps

    for line in deps_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" in line:
            spec, dep_list = line.split(":", 1)
            spec = spec.strip()
            dependencies = [d.strip() for d in dep_list.split(",") if d.strip()]
            deps[spec] = dependencies

    return deps


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
    """Extract spec ID from branch name (e.g., spec/CORE-001-foo -> CORE-001)."""
    name = branch.replace("spec/", "")
    parts = name.split("-")
    if len(parts) >= 2:
        # Assume format: COMPONENT-NNN-slug
        return f"{parts[0]}-{parts[1]}"
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
        console.print("Create one with: sw create spec/COMPONENT-NNN-description")
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


@app.command()
def deps():
    """Show dependency graph."""
    dependencies = load_dependencies()
    completed = get_completed_specs(get_repo())

    if not dependencies:
        console.print("[yellow]No dependencies defined[/yellow]")
        console.print("Add them to: .specify/dependencies.txt")
        return

    # Build reverse lookup (what depends on X)
    dependents: dict[str, list[str]] = {}
    all_specs = set(dependencies.keys())
    for spec, deps_list in dependencies.items():
        all_specs.update(deps_list)
        for dep in deps_list:
            dependents.setdefault(dep, []).append(spec)

    # Find roots (specs with no dependencies)
    roots = [s for s in all_specs if s not in dependencies or not dependencies[s]]

    def build_tree(spec: str, tree: Tree, visited: set[str]) -> None:
        if spec in visited:
            tree.add(f"[dim]{spec} (circular)[/dim]")
            return
        visited.add(spec)

        status = "[green]✓[/green]" if spec in completed else "[dim]○[/dim]"
        branch = tree.add(f"{status} {spec}")

        for dependent in dependents.get(spec, []):
            build_tree(dependent, branch, visited.copy())

    tree = Tree("[bold]Dependency Graph[/bold]")
    for root in sorted(roots):
        build_tree(root, tree, set())

    console.print(tree)


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
