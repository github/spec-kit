"""
speckit.memory.features - Quick feature mode for small fixes.

Simplified workflow for tasks < 4 hours: minimal spec, basic plan, quick tasks.
"""

import json
from pathlib import Path
from typing import Optional, List

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Quick feature templates
QUICK_SPEC_TEMPLATE = """# {feature_name}

> **Type**: Quick Feature
> **Estimated**: {estimated_hours} hours
> **Created**: {date}

---

## Overview

{description}

---

## Scope

**In Scope:**
{in_scope}

**Out of Scope:**
- Deep research (use /speckit.specify for complex features)
- Major architecture changes
- Breaking API changes

---

## Acceptance Criteria

1. {criterion_1}
2. {criterion_2}
3. Works without breaking existing functionality

---

## Notes

This is a quick feature for tasks < 4 hours. For larger features, use `/speckit.specify` for full specification.
"""

QUICK_PLAN_TEMPLATE = """# Implementation Plan: {feature_name}

## Approach

{approach}

## Tasks

1. [ ] Task 1 - {task_1}
2. [ ] Task 2 - {task_2}
3. [ ] Task 3 - Testing
4. [ ] Verification

## Notes

Use existing patterns from project memory where applicable.
"""


def collect_quick_feature_info() -> dict:
    """Collect information for quick feature interactively.

    Returns:
        Dict with feature info
    """
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel.fit(
            "[bold cyan]Quick Feature Mode[/bold cyan]",
            "For small tasks < 4 hours"
        ))

    feature_info = {
        "name": "",
        "description": "",
        "estimated_hours": 0,
        "in_scope": [],
        "acceptance_criteria": []
    }

    # Feature name
    if RICH_AVAILABLE:
        feature_info["name"] = Prompt.ask(
            "[yellow]Feature name[/yellow]",
            default="quick-fix"
        )
    else:
        feature_info["name"] = input("Feature name (default: quick-fix): ").strip() or "quick-fix"

    # Description
    if RICH_AVAILABLE:
        console.print("\n[dim]Brief description of what needs to be done:[/dim]")
        feature_info["description"] = Prompt.ask(
            "[yellow]Description[/yellow]",
            default="Fix small bug"
        )
    else:
        print("\nDescription:")
        feature_info["description"] = input().strip()

    # Estimation
    if RICH_AVAILABLE:
        hours_str = Prompt.ask(
            "[yellow]Estimated hours[/yellow]",
            default="2"
        )
        try:
            feature_info["estimated_hours"] = int(hours_str)
        except:
            feature_info["estimated_hours"] = 2
    else:
        print("\nEstimated hours (default: 2):")
        hours_str = input().strip() or "2"
        try:
            feature_info["estimated_hours"] = int(hours_str)
        except:
            feature_info["estimated_hours"] = 2

    # In scope items
    if RICH_AVAILABLE:
        console.print("\n[dim]What's in scope (one per line, empty line to finish):[/dim]")
        scope_items = []
        while True:
            item = Prompt.ask("[dim]Item[/dim]", default="")
            if not item:
                break
            scope_items.append(item)
        feature_info["in_scope"] = scope_items
    else:
        print("\nIn scope (one per line, empty line to finish):")
        scope_items = []
        while True:
            item = input("Item: ").strip()
            if not item:
                break
            scope_items.append(item)
        feature_info["in_scope"] = scope_items

    # Acceptance criteria
    if RICH_AVAILABLE:
        console.print("\n[dim]Acceptance criteria (one per line, empty line to finish):[/dim]")
        criteria = []
        while True:
            criterion = Prompt.ask("[dim]Criterion[/dim]", default="")
            if not criterion:
                break
            criteria.append(criterion)
        feature_info["acceptance_criteria"] = criteria or [
            "Fix works as expected",
            "No regressions"
        ]
    else:
        print("\nAcceptance criteria (one per line, empty line to finish):")
        criteria = []
        while True:
            criterion = input("Criterion: ").strip()
            if not criterion:
                break
            criteria.append(criterion)
        feature_info["acceptance_criteria"] = criteria or ["Fix works"]

    return feature_info


def generate_quick_spec(feature_info: dict, specs_dir: Path) -> Optional[Path]:
    """Generate quick spec file.

    Args:
        feature_info: Feature information
        specs_dir: Specs directory

    Returns:
        Path to created spec file
    """
    from datetime import datetime

    # Find next available feature number
    existing_specs = list(specs_dir.glob("[0-9]*-*"))
    if existing_specs:
        numbers = []
        for spec_dir in existing_specs:
            try:
                num = int(spec_dir.name.split("-")[0])
                numbers.append(num)
            except:
                pass
        next_num = max(numbers) + 1 if numbers else 1
    else:
        next_num = 1

    # Create spec directory
    feature_slug = feature_info["name"].lower().replace(" ", "-").replace("_", "-")
    spec_dir = specs_dir / f"{next_num:03d}-{feature_slug}"
    spec_dir.mkdir(parents=True, exist_ok=True)

    # Generate spec content
    spec_content = QUICK_SPEC_TEMPLATE.format(
        feature_name=feature_info["name"],
        estimated_hours=feature_info["estimated_hours"],
        date=datetime.now().strftime("%Y-%m-%d"),
        description=feature_info["description"],
        in_scope="\n".join(f"- {item}" for item in feature_info["in_scope"]),
        criterion_1=feature_info["acceptance_criteria"][0] if feature_info["acceptance_criteria"] else "Works as expected",
        criterion_2=feature_info["acceptance_criteria"][1] if len(feature_info["acceptance_criteria"]) > 1 else "No regressions"
    )

    # Write spec
    spec_file = spec_dir / "spec.md"
    spec_file.write_text(spec_content, encoding="utf-8")

    return spec_file


def generate_quick_plan(feature_info: dict, spec_dir: Path) -> Optional[Path]:
    """Generate quick plan file.

    Args:
        feature_info: Feature information
        spec_dir: Spec directory

    Returns:
        Path to created plan file
    """
    # Generate plan content
    plan_content = QUICK_PLAN_TEMPLATE.format(
        feature_name=feature_info["name"],
        approach=f"Direct implementation of {feature_info['description']}",
        task_1=feature_info["in_scope"][0] if feature_info["in_scope"] else "Implement fix",
        task_2=feature_info["in_scope"][1] if len(feature_info["in_scope"]) > 1 else "Test implementation"
    )

    # Write plan
    plan_file = spec_dir / "plan.md"
    plan_file.write_text(plan_content, encoding="utf-8")

    return plan_file


def generate_quick_tasks(feature_info: dict, spec_dir: Path) -> Optional[Path]:
    """Generate quick tasks file.

    Args:
        feature_info: Feature information
        spec_dir: Spec directory

    Returns:
        Path to created tasks file
    """
    from datetime import datetime

    # Generate tasks content
    tasks_content = f"""# Implementation Tasks: {feature_info['name']}

> **Feature**: Quick feature
> **Type**: Bug fix / Small feature
> **Estimate**: {feature_info['estimated_hours']} hours
> **Created**: {datetime.now().strftime("%Y-%m-%d")}

---

## Overview

Quick feature for small fix/improvement.

---

## Tasks

### Phase 1: Implementation

- [ ] T001 Implement {feature_info['in_scope'][0] if feature_info['in_scope'] else 'the fix'}
- [ ] T002 Implement {feature_info['in_scope'][1] if len(feature_info['in_scope']) > 1 else 'testing'}

### Phase 2: Testing

- [ ] T003 Verify fix works
- [ ] T004 Check for regressions

### Phase 3: Completion

- [ ] T005 Update documentation
- [ ] T006 Commit and verify

---

## Notes

For larger features, use full `/speckit.tasks` workflow.
"""

    # Write tasks
    tasks_file = spec_dir / "tasks.md"
    tasks_file.write_text(tasks_content, encoding="utf-8")

    return tasks_file


def speckit_memory_features(
    interactive: bool = True,
    specs_dir: Optional[Path] = None
) -> int:
    """Quick feature creation command.

    Usage:
        python -m speckit_memory_features
        python -m speckit_memory_features --non-interactive

    Args:
        interactive: Use interactive prompts
        specs_dir: Specs directory path

    Returns:
        Exit code (0 = success)
    """
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel.fit(
            "[bold cyan]speckit.memory.features[/bold cyan]",
            "Quick feature mode for small fixes"
        ))

    # Determine specs directory
    if not specs_dir:
        cwd = Path.cwd()
        # Check if we're in a spec directory
        if (cwd / "spec.md").exists():
            specs_dir = cwd.parent
        elif (cwd / "specs").exists():
            specs_dir = cwd / "specs"
        else:
            # Try parent
            parent = cwd.parent
            if (parent / "specs").exists():
                specs_dir = parent / "specs"
            else:
                # Use current project's specs
                specs_dir = cwd / "specs"

    if not specs_dir or not specs_dir.exists():
        if RICH_AVAILABLE:
            console.print("[red]Error:[/red] Could not find specs directory")
        return 1

    # Collect feature info
    if interactive:
        feature_info = collect_quick_feature_info()
    else:
        # Non-interactive mode: use defaults
        feature_info = {
            "name": "quick-fix",
            "description": "Quick fix or improvement",
            "estimated_hours": 2,
            "in_scope": ["Fix issue", "Test"],
            "acceptance_criteria": ["Works as expected"]
        }

    # Generate files
    if RICH_AVAILABLE:
        console.print(f"\n[cyan]Creating quick feature:[/cyan] {feature_info['name']}")
        console.print(f"  Estimated: {feature_info['estimated_hours']} hours")
        console.print(f"  Specs dir: {specs_dir}")

    try:
        # Generate spec
        spec_file = generate_quick_spec(feature_info, specs_dir)
        if RICH_AVAILABLE:
            console.print(f"[green]✓[/green] Spec: {spec_file.relative_to(specs_dir.parent)}")

        # Generate plan
        plan_file = generate_quick_plan(feature_info, spec_file.parent)
        if RICH_AVAILABLE:
            console.print(f"[green]✓[/green] Plan: {plan_file.relative_to(specs_dir.parent)}")

        # Generate tasks
        tasks_file = generate_quick_tasks(feature_info, spec_file.parent)
        if RICH_AVAILABLE:
            console.print(f"[green]✓[/green] Tasks: {tasks_file.relative_to(specs_dir.parent)}")

        if RICH_AVAILABLE:
            console.print("\n[bold green]Quick feature created![/bold green]")
            console.print(f"\n[dim]Next steps:[/dim]")
            console.print(f"1. Review: {spec_file.relative_to(specs_dir.parent)}")
            console.print(f"2. Implement: /speckit.implement")
            console.print(f"3. For larger features, use: /speckit.specify")

        return 0

    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]Error creating feature:[/red] {e}")
        return 1


if __name__ == "__main__":
    import sys

    # Parse args
    interactive = "--non-interactive" not in sys.argv
    specs_dir_str = None

    for i, arg in enumerate(sys.argv):
        if arg.startswith("--specs-dir=") and i > 0:
            specs_dir_str = arg.split("=", 1)[1]

    specs_dir = Path(specs_dir_str) if specs_dir_str else None

    sys.exit(speckit_memory_features(interactive, specs_dir))
