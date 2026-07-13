#!/usr/bin/env python3
"""Validate AI Team workflow work-item anchors without parsing prose."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


def _issue_repo(url: str) -> tuple[str, str, str]:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"invalid issue URL: {url}")
    try:
        issue_index = parts.index("issues")
    except ValueError as exc:
        raise ValueError(f"coding issue URL must contain /issues/<id>: {url}") from exc
    if issue_index < 2 or issue_index + 1 >= len(parts):
        raise ValueError(f"coding issue URL must contain repository and issue id: {url}")
    return parsed.scheme, parsed.netloc.lower(), "/".join(parts[:issue_index])


def _split_urls(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        values = value
    else:
        values = str(value).replace("\n", ",").split(",")
    return [str(item).strip() for item in values if str(item).strip()]


def validate(inputs: dict[str, object]) -> dict[str, object]:
    work_type = str(inputs.get("work_type", "auto"))
    planning_mode = str(inputs.get("planning_mode", "standard"))
    primary = str(inputs.get("coding_issue_url", "")).strip()
    handoff = str(inputs.get("handoff_requirement_url", "")).strip()
    related = _split_urls(inputs.get("also_resolves_issue_urls"))

    if work_type in {"auto", "unclear", ""}:
        raise ValueError(
            "work_type must be resolved after intake classification and before the formal work-item gate"
        )
    if work_type == "bug" and not primary:
        raise ValueError("bug work requires a primary coding_issue_url")
    if work_type == "feature" and bool(primary) == bool(handoff):
        raise ValueError(
            "feature work requires exactly one primary anchor: "
            "coding_issue_url or handoff_requirement_url"
        )
    if planning_mode == "compact" and work_type == "new-project":
        raise ValueError("new-project work requires standard planning mode")
    if work_type == "new-project" and not (primary or handoff):
        raise ValueError(
            "new-project work requires a coding issue/project charter URL or handoff_requirement_url"
        )
    if related and not primary:
        raise ValueError("also_resolves_issue_urls requires a primary coding_issue_url")

    primary_repo = _issue_repo(primary) if primary else None
    seen = {primary} if primary else set()
    for url in related:
        if url in seen:
            raise ValueError(f"duplicate coding issue URL: {url}")
        seen.add(url)
        if _issue_repo(url) != primary_repo:
            raise ValueError(
                "all also-resolved issues must belong to the primary coding repository"
            )

    if handoff:
        parsed = urlparse(handoff)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"invalid handoff requirement URL: {handoff}")

    return {
        "work_type": work_type,
        "planning_mode": planning_mode,
        "primary_anchor": primary or handoff or None,
        "also_resolves_count": len(related),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    if not args.run_id or any(part in args.run_id for part in ("/", "\\", "..")):
        parser.error("run id must be a simple directory name")

    inputs_path = (
        args.project_root
        / ".specify"
        / "workflows"
        / "runs"
        / args.run_id
        / "inputs.json"
    )
    try:
        payload = json.loads(inputs_path.read_text(encoding="utf-8"))
        inputs = payload.get("inputs", payload)
        if not isinstance(inputs, dict):
            raise ValueError("workflow inputs must be a JSON object")
        result = validate(inputs)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"AI Team work-item gate failed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
