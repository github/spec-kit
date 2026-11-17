"""Explicit shared asset inventory for the fork's integration delivery tests."""

COMMANDS = (
    "constitution",
    "specify",
    "clarify",
    "architecture",
    "environment",
    "plan",
    "taskscode",
    "analyze",
    "impcode",
    "deployment",
    "test",
)


def expanded_inventory(files):
    result = set(files)
    # Keep agent-specific paths/extensions while changing the core inventory.
    for path in files:
        for separator in (".", "-"):
            marker = "speckit" + separator + "plan"
            if marker in path:
                for old in ("tasks", "implement", "checklist", "converge"):
                    result.discard(path.replace(marker, "speckit" + separator + old))
                result.update(
                    path.replace(marker, "speckit" + separator + name)
                    for name in COMMANDS
                )
    shell = (
        "powershell/workflow.ps1"
        if any("/powershell/" in p for p in files)
        else "bash/workflow.sh"
    )
    result.add(".specify/scripts/" + shell)
    result.update(
        ".specify/scripts/python/" + name + ".py"
        for name in (
            "common",
            "check_prerequisites",
            "create_new_feature",
            "resolve_template",
            "setup_plan",
            "setup_tasks",
            "workflow_common",
            "workflow_context",
            "code_progress",
        )
    )
    result.update(
        ".specify/templates/" + name + "-template.md"
        for name in (
            "architecture",
            "environment",
            "tasks-code",
            "analysis",
            "deployment",
            "test-report",
        )
    )
    return sorted(result)
