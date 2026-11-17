#!/usr/bin/env python3
"""Component: workflow context; target: developer workstation; task: fork workflow.

Resolve stage inputs without creating artifacts or changing the feature pointer.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

from common import resolve_template_content, TemplateResolutionError  # noqa: E402 - disable cache writes before local imports
from workflow_common import architecture, environment, paths, require_files, tasks  # noqa: E402

REQUIRED = {
    "architecture": ["CONSTITUTION", "SPEC"],
    "environment": ["CONSTITUTION", "SPEC", "ARCHITECTURE"],
    "plan": ["CONSTITUTION", "SPEC", "ARCHITECTURE", "ENVIRONMENT"],
    "taskscode": ["CONSTITUTION", "SPEC", "ARCHITECTURE", "ENVIRONMENT", "PLAN"],
    "analyze": [
        "CONSTITUTION",
        "SPEC",
        "ARCHITECTURE",
        "ENVIRONMENT",
        "PLAN",
        "TASKS_CODE",
    ],
    "impcode": [
        "CONSTITUTION",
        "SPEC",
        "ARCHITECTURE",
        "ENVIRONMENT",
        "PLAN",
        "TASKS_CODE",
    ],
    "deployment": [
        "CONSTITUTION",
        "SPEC",
        "ARCHITECTURE",
        "ENVIRONMENT",
        "PLAN",
        "TASKS_CODE",
        "CODE_PROGRESS",
    ],
    "test": [
        "CONSTITUTION",
        "SPEC",
        "ARCHITECTURE",
        "ENVIRONMENT",
        "PLAN",
        "TASKS_CODE",
        "CODE_PROGRESS",
    ],
}


def context(stage: str) -> dict:
    selected = paths()
    require_files(selected, REQUIRED[stage])
    if stage == "environment":
        architecture(selected)
    elif stage in {"plan", "taskscode"}:
        environment(selected)
    elif stage in {"impcode", "deployment", "test"}:
        tasks(selected)
    # Analyze must be able to report malformed inventories, cycles and bad targets.
    payload = {key: str(value) for key, value in selected.items()}
    payload["PYTHON"] = sys.executable
    payload["PROGRESS_HELPER"] = str(
        Path(__file__).with_name("code_progress.py").resolve()
    )
    if stage != "impcode":
        name = {
            "taskscode": "tasks-code",
            "test": "test-report",
            "analyze": "analysis",
        }.get(stage, stage)
        template = resolve_template_content(name + "-template", selected["REPO_ROOT"])
        if not template or not template.strip():
            raise ValueError(
                f"Missing {name}-template; reinstall shared infrastructure"
            )
        payload["TEMPLATE_CONTENT"] = template
    payload["AVAILABLE_DOCS"] = sorted(
        p.name for p in selected["FEATURE_DIR"].iterdir()
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=REQUIRED)
    parser.add_argument(
        "--json", action="store_true", help="JSON is the default output"
    )
    args = parser.parse_args(argv)
    try:
        print(json.dumps(context(args.stage), ensure_ascii=True))
        return 0
    except (OSError, ValueError, TemplateResolutionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
