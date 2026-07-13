#!/usr/bin/env python3
"""Publish an approved intake issue and route it into a formal AI Team workflow."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import yaml


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
Runner = Callable[..., subprocess.CompletedProcess[str]]


class IntakeRouteError(RuntimeError):
    """Raised when publication or formal workflow routing cannot be verified."""


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise IntakeRouteError(f"required intake artifact is missing: {path}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise IntakeRouteError(f"intake artifact must be a YAML mapping: {path}")
    return loaded


def _frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        raise IntakeRouteError(f"issue draft is missing: {path}")
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise IntakeRouteError("issue draft must start with YAML frontmatter")
    try:
        _, raw, body = text.split("---", 2)
    except ValueError as exc:
        raise IntakeRouteError("issue draft frontmatter is not closed") from exc
    metadata = yaml.safe_load(raw) or {}
    if not isinstance(metadata, dict):
        raise IntakeRouteError("issue draft frontmatter must be a mapping")
    return metadata, body.lstrip()


def _atomic_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        yaml.safe_dump(payload, handle, allow_unicode=True, sort_keys=False)
        temporary = Path(handle.name)
    temporary.replace(path)


def _run_dir(project_root: Path, run_id: str) -> Path:
    if not run_id or any(part in run_id for part in ("/", "\\", "..")):
        raise IntakeRouteError("run id must be a simple directory name")
    return project_root / ".specify" / "workflows" / "runs" / run_id


def _intake_dir(project_root: Path, intake_slug: str) -> Path:
    if not SLUG_PATTERN.fullmatch(intake_slug):
        raise IntakeRouteError("intake slug must be lower-kebab text")
    return project_root / ".specify" / "ai-team" / "intake" / intake_slug


def _workflow_inputs(project_root: Path, run_id: str) -> dict[str, Any]:
    path = _run_dir(project_root, run_id) / "inputs.json"
    if not path.is_file():
        raise IntakeRouteError(f"workflow inputs are missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    inputs = payload.get("inputs", payload)
    if not isinstance(inputs, dict):
        raise IntakeRouteError("workflow inputs must be a JSON object")
    return inputs


def _require_approved_gate(project_root: Path, run_id: str, gate_id: str) -> None:
    path = _run_dir(project_root, run_id) / "state.json"
    if not path.is_file():
        raise IntakeRouteError(f"workflow state is missing: {path}")
    state = json.loads(path.read_text(encoding="utf-8"))
    choice = (
        state.get("step_results", {})
        .get(gate_id, {})
        .get("output", {})
        .get("choice")
    )
    if str(choice).lower() != "approve":
        raise IntakeRouteError(f"gate {gate_id} is not approved")


def _verified_issue_url(raw_output: str, repository: str) -> str:
    candidates = re.findall(r"https?://[^\s]+/issues/\d+", raw_output)
    if not candidates:
        raise IntakeRouteError("issue publisher did not return a verifiable issue URL")
    url = candidates[-1].rstrip(".,)")
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 4 or "/".join(parts[:2]).lower() != repository.lower():
        raise IntakeRouteError("published issue URL does not match target repository")
    return url


def publish_issue(
    *,
    project_root: Path,
    run_id: str,
    intake_slug: str,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    """Publish exactly the issue draft approved by the workflow gate."""
    project_root = project_root.resolve()
    _require_approved_gate(project_root, run_id, "review-intake-boundary")
    _require_approved_gate(project_root, run_id, "review-issue-draft")
    intake_dir = _intake_dir(project_root, intake_slug)
    intake = _load_yaml(intake_dir / "intake.yml")
    draft, issue_body = _frontmatter(intake_dir / "issue-draft.md")

    work_type = str(intake.get("work_type", ""))
    if work_type not in {"bug", "feature", "new-project"}:
        raise IntakeRouteError(
            "intake work_type must be resolved to bug, feature, or new-project"
        )
    privacy = str(intake.get("privacy_class", "unknown"))
    if privacy not in {"public-safe", "confidential"}:
        raise IntakeRouteError("privacy_class must be resolved before publication")
    planning_mode = str(intake.get("planning_mode", "standard"))
    if planning_mode not in {"standard", "compact"}:
        raise IntakeRouteError("planning_mode must be standard or compact")

    expected_type = "type/bug" if work_type == "bug" else "type/feature"
    if draft.get("type_label") != expected_type:
        raise IntakeRouteError("issue draft type does not match intake classification")
    repository = str(draft.get("target_repository", ""))
    if not REPOSITORY_PATTERN.fullmatch(repository):
        raise IntakeRouteError("target_repository must use owner/repository form")
    title = str(draft.get("title", "")).strip()
    if not title:
        raise IntakeRouteError("issue draft title is required")

    feature_decision = str(
        intake.get("feature_decision_evidence", "not-applicable")
    )
    accepted = work_type == "bug" or feature_decision == "accepted"
    if work_type in {"feature", "new-project"} and accepted:
        if not intake.get("feature_approver") or not intake.get("feature_approver_role"):
            raise IntakeRouteError(
                "accepted feature requires Technical Committee or delegated approver evidence"
            )
    state_label = "state/accepted" if accepted else "state/draft"

    command = [
        "gh",
        "issue",
        "create",
        "--repo",
        repository,
        "--title",
        title,
        "--body",
        issue_body,
        "--label",
        expected_type,
        "--label",
        state_label,
    ]
    try:
        completed = runner(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise IntakeRouteError(f"issue publisher could not start: {exc}") from exc
    if completed.returncode != 0:
        raise IntakeRouteError(
            f"issue publisher failed: {completed.stderr.strip() or completed.stdout.strip()}"
        )
    issue_url = _verified_issue_url(completed.stdout, repository)

    route_status = "ready"
    if privacy == "confidential":
        route_status = "awaiting-handoff"
    elif work_type in {"feature", "new-project"} and not accepted:
        route_status = "awaiting-feature-acceptance"
    result = {
        "intake_slug": intake_slug,
        "work_type": work_type,
        "privacy_class": privacy,
        "planning_mode": planning_mode,
        "issue_url": issue_url,
        "issue_repository": repository,
        "issue_state": state_label,
        "route_status": route_status,
        "feature_approver": intake.get("feature_approver"),
        "feature_approver_role": intake.get("feature_approver_role"),
    }
    _atomic_yaml(intake_dir / "result.yml", result)
    return result


def route_formal_workflow(
    *,
    project_root: Path,
    run_id: str,
    intake_slug: str,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    """Launch the formal workflow from the publisher's structured result."""
    project_root = project_root.resolve()
    intake_dir = _intake_dir(project_root, intake_slug)
    result_path = intake_dir / "result.yml"
    result = _load_yaml(result_path)
    if result.get("route_status") != "ready":
        return result

    inputs = _workflow_inputs(project_root, run_id)
    request = str(inputs.get("request", "")).strip()
    if not request:
        raise IntakeRouteError("original intake request is missing")
    issue_url = str(result["issue_url"])
    work_type = str(result["work_type"])
    if work_type == "bug":
        parts = [part for part in urlparse(issue_url).path.split("/") if part]
        work_slug = f"bug-{parts[1].lower()}-{parts[-1]}"
        command = [
            "specify", "workflow", "run", "ai-team-bugfix",
            "--input", f"request={request}",
            "--input", f"work_slug={work_slug}",
            "--input", "work_type=bug",
            "--input", f"coding_issue_url={issue_url}",
        ]
    elif work_type in {"feature", "new-project"}:
        planning_mode = "standard" if work_type == "new-project" else result["planning_mode"]
        command = [
            "specify", "workflow", "run", "ai-team-sdd",
            "--input", f"request={request}",
            "--input", f"work_type={work_type}",
            "--input", f"planning_mode={planning_mode}",
            "--input", f"coding_issue_url={issue_url}",
        ]
    else:
        raise IntakeRouteError("published intake has unsupported work_type")

    try:
        completed = runner(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise IntakeRouteError(f"formal workflow could not start: {exc}") from exc
    if completed.returncode != 0:
        result["route_status"] = "launch-failed"
        result["launch_error"] = completed.stderr.strip() or completed.stdout.strip()
        _atomic_yaml(result_path, result)
        raise IntakeRouteError(f"formal workflow failed to start: {result['launch_error']}")
    result["route_status"] = "launched"
    result["formal_workflow"] = "ai-team-bugfix" if work_type == "bug" else "ai-team-sdd"
    result["formal_workflow_output"] = completed.stdout.strip()
    _atomic_yaml(result_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("publish", "route"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--intake-slug", required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        if args.action == "publish":
            result = publish_issue(
                project_root=args.project_root,
                run_id=args.run_id,
                intake_slug=args.intake_slug,
            )
        else:
            result = route_formal_workflow(
                project_root=args.project_root,
                run_id=args.run_id,
                intake_slug=args.intake_slug,
            )
    except (IntakeRouteError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"AI Team intake routing failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
