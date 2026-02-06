#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
MODULE_PATH = REPO_ROOT / "src" / "specify_cli" / "template_packager.py"

spec = importlib.util.spec_from_file_location("template_packager", MODULE_PATH)
if spec is None or spec.loader is None:
    raise SystemExit("ERROR: Failed to load template_packager module.")
template_packager = importlib.util.module_from_spec(spec)
sys.modules["template_packager"] = template_packager
spec.loader.exec_module(template_packager)

TemplatePackagerError = template_packager.TemplatePackagerError
build_commands_for_agents = template_packager.build_commands_for_agents
AGENT_OUTPUT = template_packager.AGENT_OUTPUT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package Spec Kit command templates into agent-specific command files.",
    )
    parser.add_argument(
        "--ai",
        dest="agents",
        default="all",
        help="Agent(s) to build for (comma-separated) or 'all'.",
    )
    parser.add_argument(
        "--script",
        dest="script_variant",
        choices=("sh", "ps"),
        default="sh",
        help="Script variant to substitute for {SCRIPT}.",
    )
    parser.add_argument(
        "--templates-dir",
        default=str(REPO_ROOT / "templates" / "commands"),
        help="Directory containing command templates.",
    )
    parser.add_argument(
        "--out",
        default=str(REPO_ROOT),
        help="Output directory (defaults to repo root).",
    )
    parser.add_argument(
        "--include-vscode-settings",
        action="store_true",
        help="Include templates/vscode-settings.json for Copilot outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.agents == "all":
        agents = list(AGENT_OUTPUT.keys())
    else:
        agents = [a.strip() for a in args.agents.split(",") if a.strip()]

    templates_dir = Path(args.templates_dir).expanduser().resolve()
    output_dir = Path(args.out).expanduser().resolve()

    try:
        results = build_commands_for_agents(
            templates_dir=templates_dir,
            output_dir=output_dir,
            agents=agents,
            script_variant=args.script_variant,
            include_vscode_settings=args.include_vscode_settings,
        )
    except TemplatePackagerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for agent, paths in results.items():
        print(f"{agent}: wrote {len(paths)} file(s)")
        for path in paths:
            rel = path.relative_to(output_dir)
            print(f"  - {rel}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
