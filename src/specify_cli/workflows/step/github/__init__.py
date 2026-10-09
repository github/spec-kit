"""GitHub workflow step: add an explicit label to an issue or pull request."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression

_NUMBER = re.compile(r"[1-9][0-9]*\Z")
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def _run(args: list[str], root: Path, *, input_text: str | None = None) -> str:
    try:
        result = subprocess.run(
            args,
            cwd=root,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"{args[0]} request failed: {exc}") from exc
    if result.returncode:
        # CLI stderr may contain authentication details; never include it in run state.
        raise ValueError(f"{args[0]} request failed (exit code {result.returncode})")
    return result.stdout.strip()


def _api(root: Path, endpoint: str, *, labels: list[str] | None = None) -> Any:
    method = "POST" if labels is not None else "GET"
    args = ["gh", "api", "--method", method, endpoint]
    if labels is not None:
        args.extend(["--input", "-"])
    raw = _run(
        args,
        root,
        input_text=json.dumps({"labels": labels}) if labels is not None else None,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"GitHub returned invalid JSON for {endpoint}") from exc


def _resolved(value: Any, context: StepContext) -> Any:
    if isinstance(value, str) and "{{" in value:
        return evaluate_expression(value, context)
    return value


def _number(value: Any) -> int:
    if isinstance(value, bool) or not (
        (isinstance(value, int) and value > 0)
        or (isinstance(value, str) and _NUMBER.fullmatch(value))
    ):
        raise ValueError("'number' must be a positive integer")
    return int(value)


def _repository(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not _REPOSITORY.fullmatch(value)
        or any(part in (".", "..") for part in value.split("/"))
    ):
        raise ValueError("'repository' must be a GitHub owner/repo name")
    return value


def _label(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 50
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise ValueError(
            "'label' must be a non-empty label name of at most 50 characters without control characters"
        )
    return value


def _label_names(value: Any) -> set[str]:
    if not isinstance(value, list) or not all(
        isinstance(entry, dict) and isinstance(entry.get("name"), str)
        for entry in value
    ):
        raise ValueError("GitHub returned an invalid label list")
    return {entry["name"].casefold() for entry in value}


class GitHubStep(StepBase):
    """Add only the label explicitly specified by a workflow author."""

    type_key = "github"

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if config.get("operation") != "add-label":
            errors.append("GitHub step 'operation' must be add-label.")
        if config.get("target") not in ("issue", "pull_request"):
            errors.append("GitHub step 'target' must be issue or pull_request.")
        for key in config.keys() - {
            "id",
            "type",
            "operation",
            "target",
            "repository",
            "number",
            "label",
            "continue_on_error",
        }:
            errors.append(f"GitHub step has unsupported field {key!r}.")
        if "number" not in config:
            errors.append("GitHub step requires 'number'.")
        elif not (isinstance(config["number"], str) and "{{" in config["number"]):
            try:
                _number(config["number"])
            except ValueError as exc:
                errors.append(str(exc))
        if "repository" not in config:
            errors.append("GitHub step requires 'repository'.")
        elif not (
            isinstance(config["repository"], str) and "{{" in config["repository"]
        ):
            try:
                _repository(config["repository"])
            except ValueError as exc:
                errors.append(str(exc))
        if "label" not in config:
            errors.append("GitHub step requires 'label'.")
        elif not (isinstance(config["label"], str) and "{{" in config["label"]):
            try:
                _label(config["label"])
            except ValueError as exc:
                errors.append(str(exc))
        return errors

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        try:
            errors = self.validate(config)
            if errors:
                raise ValueError("; ".join(errors))
            number = _number(_resolved(config["number"], context))
            label = _label(_resolved(config["label"], context))
            repository = _repository(_resolved(config["repository"], context))
            root = Path(context.project_root or ".").resolve()
            url = f"https://api.github.com/repos/{repository}"
            target = config["target"]
            kind = "pulls" if target == "pull_request" else "issues"
            resource = _api(root, f"{url}/{kind}/{number}")
            if (
                not isinstance(resource, dict)
                or resource.get("number") != number
                or (target == "issue" and "pull_request" in resource)
            ):
                raise ValueError(
                    f"GitHub {target} #{number} does not match the requested target"
                )
            existing = _label_names(resource.get("labels"))
            output = {
                "repository": repository,
                "target": target,
                "number": number,
                "label": label,
                "added": False,
            }
            if label.casefold() in existing:
                return StepResult(output=output)
            labels = _api(root, f"{url}/issues/{number}/labels", labels=[label])
            if label.casefold() not in _label_names(labels):
                raise ValueError(
                    f"GitHub did not apply label {label!r} to {target} #{number}"
                )
            output["added"] = True
            return StepResult(output=output)
        except (ValueError, OSError) as exc:
            return StepResult(status=StepStatus.FAILED, error=f"GitHub step: {exc}")
