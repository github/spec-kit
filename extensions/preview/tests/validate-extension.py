#!/usr/bin/env python3
"""Validate the preview extension package."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    manifest_path = ROOT / "extension.yml"
    command_path = ROOT / "commands" / "speckit.preview.html.md"

    if not manifest_path.is_file():
        fail("extension.yml is missing")
    if not command_path.is_file():
        fail("commands/speckit.preview.html.md is missing")

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    extension = manifest.get("extension", {})
    commands = manifest.get("provides", {}).get("commands", [])

    if extension.get("id") != "preview":
        fail("extension.id must be preview")
    if extension.get("version") != "1.0.0":
        fail("extension.version must be 1.0.0")
    if extension.get("repository") != "https://github.com/bigsmartben/spec-kit-preview":
        fail("extension.repository must point to the standalone repository")
    if len(commands) != 1:
        fail("expected exactly one command")

    command = commands[0]
    if command.get("name") != "speckit.preview.html":
        fail("command name must be speckit.preview.html")
    if command.get("file") != "commands/speckit.preview.html.md":
        fail("command file path is incorrect")

    content = command_path.read_text(encoding="utf-8")
    required_phrases = [
        "specs/<feature>/preview/index.html",
        "self-contained HTML",
        "inline CSS and JavaScript",
        "No external network dependencies",
        "Prototype Assumptions",
        "Do not modify source code",
        "not a production implementation",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in content]
    if missing:
        fail(f"command file missing required phrases: {missing}")

    print("preview extension package is valid")


if __name__ == "__main__":
    main()

