"""GitHub workflow step: post comments, retrieve posted artifacts, or check out a PR."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}\Z")
_NUMBER = re.compile(r"[1-9][0-9]*\Z")
_ORIGIN = re.compile(
    r"(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?\Z"
)
_MARKER = re.compile(
    r"<!-- speckit-github:v2 artifact=([A-Za-z0-9_-]+) "
    r"run=([A-Za-z0-9_-]+) step=([A-Za-z0-9_-]+) "
    r"bytes=([0-9]+) sha256=([a-f0-9]{64}) -->\Z"
)
_MARKER_PREFIX = "<!-- speckit-github:"


def _run(args: list[str], root: Path, *, input_text: str | None = None) -> str:
    try:
        result = subprocess.run(
            args, cwd=root, input=input_text, capture_output=True, text=True,
            timeout=60, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"{args[0]} request failed: {exc}") from exc
    if result.returncode:
        # Do not echo CLI stderr: authentication errors can contain sensitive data.
        raise ValueError(
            f"{args[0]} request failed (exit code {result.returncode}): "
            f"{' '.join(args[1:3])}"
        )
    return result.stdout.strip()


def _api(root: Path, endpoint: str, *, method: str = "GET", data: dict[str, str] | None = None,
         paginated: bool = False) -> Any:
    args = ["gh", "api", "--method", method, endpoint]
    if paginated:
        args.extend(["--paginate", "--slurp"])
    if data is not None:
        args.extend(["--input", "-"])
    raw = _run(args, root, input_text=json.dumps(data) if data is not None else None)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"GitHub returned invalid JSON for {endpoint}") from exc


def _project_path(root: Path, value: str, *, writing: bool) -> Path:
    path = Path(value)
    if (not value or path.is_absolute() or "\\" in value
            or any(part in ("..", ".") for part in value.split("/"))):
        raise ValueError(f"Path must be relative and inside the project: {value!r}")
    candidate = root / path
    if candidate == root:
        raise ValueError("Path must name a file inside the project")
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlinked paths are not allowed: {value!r}")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes the project: {value!r}")
    if writing:
        if candidate.exists():
            raise ValueError(f"Destination already exists: {value!r}")
    elif not candidate.is_file():
        raise ValueError(f"File does not exist: {value!r}")
    return candidate


def _write_artifact(root: Path, destination: Path, body: str) -> None:
    """Create a new file through directory handles; refuse symlinked parents."""
    data = body.encode("utf-8")
    if os.name == "nt":
        destination.parent.mkdir(parents=True, exist_ok=True)
        _project_path(root, str(destination.relative_to(root)), writing=True)
        with destination.open("xb") as stream:
            stream.write(data)
        return

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory = os.open(root, flags)
    try:
        for part in destination.relative_to(root).parts[:-1]:
            try:
                child = os.open(part, flags, dir_fd=directory)
            except FileNotFoundError:
                try:
                    os.mkdir(part, dir_fd=directory)
                except FileExistsError:
                    pass
                child = os.open(part, flags, dir_fd=directory)
            os.close(directory)
            directory = child
        name = destination.name
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=directory)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
        except OSError:
            os.unlink(name, dir_fd=directory)
            raise
    finally:
        os.close(directory)


def _resolved(value: Any, context: StepContext) -> Any:
    if isinstance(value, str) and "{{" in value:
        return evaluate_expression(value, context)
    return value


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{name}' must be a non-empty string")
    return value


def _number(value: Any) -> int:
    if isinstance(value, bool) or not (
        (isinstance(value, int) and value > 0)
        or (isinstance(value, str) and _NUMBER.fullmatch(value))
    ):
        raise ValueError("'number' must be a positive integer")
    return int(value)


def _identity(root: Path) -> tuple[str, str]:
    origin = _run(["git", "remote", "get-url", "origin"], root)
    match = _ORIGIN.fullmatch(origin)
    if not match:
        raise ValueError("GitHub step requires a github.com origin remote")
    repo = f"{match[1]}/{match[2]}"
    # Use absolute API endpoints; a GH_HOST override must not redirect requests
    # to an unexpected host. gh manages authentication without exposing a token.
    return repo, f"https://api.github.com/repos/{repo}"


def _comments(root: Path, url: str) -> list[dict[str, Any]]:
    pages = _api(root, f"{url}/comments?per_page=100", paginated=True)
    if not isinstance(pages, list) or not all(isinstance(page, list) for page in pages):
        raise ValueError("GitHub returned an invalid comment list")
    comments = [comment for page in pages for comment in page]
    if not all(isinstance(comment, dict) for comment in comments):
        raise ValueError("GitHub returned an invalid comment")
    return comments


def _marked(comment: dict[str, Any]) -> tuple[str, str, str, str, str] | None:
    text = comment.get("body")
    if not isinstance(text, str) or _MARKER_PREFIX not in text:
        return None
    body, sep, marker = text.rpartition("\n\n")
    match = _MARKER.fullmatch(marker) if sep else None
    encoded = body.encode("utf-8")
    if not match or hashlib.sha256(encoded).hexdigest() != match[5]:
        raise ValueError("GitHub artifact has an invalid marker or content digest")
    artifact_bytes = int(match[4])
    if artifact_bytes > len(encoded):
        raise ValueError("GitHub artifact has an invalid byte length")
    try:
        artifact = encoded[:artifact_bytes].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("GitHub artifact has an invalid UTF-8 boundary") from exc
    return body, match[1], match[2], match[3], artifact


def _author(comment: dict[str, Any]) -> str | None:
    user = comment.get("user")
    return user.get("login") if isinstance(user, dict) else None


class GitHubStep(StepBase):
    """Run bounded GitHub operations through an authenticated gh CLI."""

    type_key = "github"

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        operation = config.get("operation")
        if operation not in ("comment", "fetch-artifact", "checkout-pr"):
            errors.append(
                "GitHub step 'operation' must be comment, fetch-artifact, or checkout-pr."
            )
            return errors
        expected = {
            "comment": {"id", "type", "operation", "target", "number", "body", "body_file",
                        "body_files", "artifact", "maintainer_action", "continue_on_error"},
            "fetch-artifact": {"id", "type", "operation", "target", "number", "artifact",
                               "write_to", "continue_on_error"},
            "checkout-pr": {"id", "type", "operation", "number", "continue_on_error"},
        }[operation]
        for key in config.keys() - expected:
            errors.append(f"GitHub step has unsupported field {key!r}.")
        if operation != "checkout-pr" and config.get("target") not in ("issue", "pull_request"):
            errors.append("GitHub step 'target' must be issue or pull_request.")
        if "number" not in config:
            errors.append("GitHub step requires 'number'.")
        elif not (isinstance(config["number"], str) and "{{" in config["number"]):
            try:
                _number(config["number"])
            except ValueError as exc:
                errors.append(str(exc))
        if operation == "comment":
            if sum(key in config for key in ("body", "body_file", "body_files")) != 1:
                errors.append("GitHub comment requires exactly one of body, body_file, body_files.")
            if "body_files" in config and (
                not isinstance(config["body_files"], list) or not config["body_files"]
                or not all(isinstance(v, str) and v.strip() for v in config["body_files"])
            ):
                errors.append("'body_files' must be a non-empty list of paths.")
            action = config.get("maintainer_action")
            if action is not None and (
                not isinstance(action, dict) or set(action) != {"summary", "possible_labels"}
                or not isinstance(action["summary"], str)
                or not isinstance(action["possible_labels"], list)
                or not all(isinstance(v, str) and v.strip() for v in action["possible_labels"])
            ):
                errors.append(
                    "'maintainer_action' requires a summary and a list of possible_labels."
                )
        if operation == "fetch-artifact" and "write_to" not in config:
            errors.append("GitHub fetch-artifact requires 'write_to'.")
        if "artifact" in config and not (
            isinstance(config["artifact"], str) and _IDENTIFIER.fullmatch(config["artifact"])
        ):
            errors.append(
                "'artifact' must be a stable alphanumeric identifier (hyphens/underscores allowed)."
            )
        if operation == "fetch-artifact" and "artifact" not in config:
            errors.append("GitHub fetch-artifact requires 'artifact'.")
        for name in ("body", "body_file", "write_to"):
            if name in config and not isinstance(config[name], str):
                errors.append(f"'{name}' must be a string.")
        return errors

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        try:
            errors = self.validate(config)
            if errors:
                raise ValueError("; ".join(errors))
            if not context.project_root:
                raise ValueError("GitHub step requires a project root")
            if context.inside_fan_out:
                raise ValueError(
                    "GitHub steps cannot run inside fan-out "
                    "(run/step retry identity is not unique per item)"
                )
            root = Path(context.project_root).resolve()
            repo, url = _identity(root)
            number = _number(_resolved(config["number"], context))
            operation = config["operation"]
            if operation == "checkout-pr":
                return self._checkout(root, url, number)
            target = config["target"]
            resource_kind = "pulls" if target == "pull_request" else "issues"
            resource = _api(root, f"{url}/{resource_kind}/{number}")
            if (not isinstance(resource, dict) or resource.get("number") != number
                    or (target == "issue" and "pull_request" in resource)):
                raise ValueError(f"GitHub {target} #{number} does not match the requested target")
            issue_url = f"{url}/issues/{number}"
            if operation == "comment":
                return self._comment(config, context, root, repo, issue_url, number)
            return self._fetch(config, context, root, repo, issue_url)
        except (ValueError, OSError, UnicodeError) as exc:
            return StepResult(status=StepStatus.FAILED, error=f"GitHub step: {exc}")

    @staticmethod
    def _viewer(root: Path, repo: str) -> str:
        if (os.environ.get("GITHUB_ACTIONS") == "true"
                and os.environ.get("GITHUB_REPOSITORY", "").lower() == repo.lower()):
            try:
                installation = _api(
                    root, "https://api.github.com/installation/repositories"
                )
            except ValueError:
                # A user token used inside Actions does not have this installation
                # endpoint. It must identify itself through /user instead.
                pass
            else:
                repositories = installation.get("repositories") if isinstance(installation, dict) else None
                if (not isinstance(repositories, list)
                        or installation.get("total_count") != 1
                        or len(repositories) != 1
                        or not isinstance(repositories[0], dict)
                        or not isinstance(repositories[0].get("full_name"), str)
                        or repositories[0]["full_name"].lower() != repo.lower()):
                    raise ValueError(
                        "Actions installation token must be scoped to this repository only"
                    )
                return "github-actions[bot]"
        user = _api(root, "https://api.github.com/user")
        if not isinstance(user, dict):
            raise ValueError("GitHub returned an invalid authenticated user")
        return _string(user.get("login"), "authenticated user login")

    def _comment(self, config: dict[str, Any], context: StepContext, root: Path,
                 repo: str, issue_url: str, number: int) -> StepResult:
        if "body" in config:
            body = _string(_resolved(config["body"], context), "body")
        elif "body_file" in config:
            source = _string(_resolved(config["body_file"], context), "body_file")
            path = _project_path(root, source, writing=False)
            body = path.read_bytes().decode("utf-8")
        else:
            paths = [
                _project_path(root, _string(_resolved(p, context), "body_files entry"), writing=False)
                for p in config["body_files"]
            ]
            body = "\n\n".join(path.read_bytes().decode("utf-8") for path in paths)
        if not body.strip():
            raise ValueError("Comment body must not be empty")
        artifact_bytes = len(body.encode("utf-8"))
        action = config.get("maintainer_action")
        if action is not None:
            summary = _string(_resolved(action["summary"], context), "maintainer_action.summary")
            labels = [
                _string(_resolved(label, context), "possible_labels")
                for label in action["possible_labels"]
            ]
            proposed = ", ".join(labels) if labels else "None"
            body += (
                f"\n\n### Maintainer action (proposal only)\n{summary}"
                f"\n\nPossible labels: {proposed}"
            )
        artifact = config.get("artifact", "-")
        run_id = _string(context.run_id, "run_id")
        step_id = _string(config["id"], "id")
        if not all(_IDENTIFIER.fullmatch(value) for value in (run_id, step_id)) or (
            artifact != "-" and not _IDENTIFIER.fullmatch(artifact)
        ):
            raise ValueError("Artifact, run ID, and step ID must be safe identifiers")
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        marked_body = (f"{body}\n\n<!-- speckit-github:v2 artifact={artifact} "
                       f"run={run_id} step={step_id} bytes={artifact_bytes} sha256={digest} -->")
        viewer = self._viewer(root, repo)
        existing = []
        for comment in _comments(root, issue_url):
            marked = _marked(comment)
            if marked and marked[2:4] == (run_id, step_id):
                existing.append((comment, marked))
        if len(existing) > 1:
            raise ValueError("Multiple comments exist for this run and step")
        if existing:
            comment, marked = existing[0]
            if marked[0] != body or marked[1] != artifact or _author(comment) != viewer:
                raise ValueError(
                    "Existing run/step comment differs or is not owned by the authenticated user"
                )
            comment_id = comment.get("id")
        else:
            posted = _api(root, f"{issue_url}/comments", method="POST", data={"body": marked_body})
            if not isinstance(posted, dict):
                raise ValueError("GitHub returned an invalid posted comment")
            if _author(posted) != viewer:
                raise ValueError("Posted comment author does not match the authenticated identity")
            comment_id = posted.get("id")
        if not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id <= 0:
            raise ValueError("GitHub comment has no valid ID")
        return StepResult(output={"repository": repo, "number": number, "comment_id": comment_id,
                                  "artifact": artifact if artifact != "-" else None})

    def _fetch(self, config: dict[str, Any], context: StepContext, root: Path,
               repo: str, issue_url: str) -> StepResult:
        name = _string(_resolved(config["write_to"], context), "write_to")
        destination = _project_path(root, name, writing=True)
        viewer = self._viewer(root, repo)
        matches = []
        for comment in _comments(root, issue_url):
            marked = _marked(comment)
            if marked and marked[1] == config["artifact"]:
                matches.append((comment, marked[4]))
        if len(matches) != 1:
            raise ValueError(
                f"Expected exactly one trusted artifact {config['artifact']!r}; "
                f"found {len(matches)}"
            )
        comment, body = matches[0]
        if _author(comment) != viewer:
            raise ValueError("GitHub artifact was not posted by the authenticated user")
        comment_id = comment.get("id")
        if not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id <= 0:
            raise ValueError("GitHub artifact has no valid comment ID")
        try:
            _write_artifact(root, destination, body)
        except FileExistsError as exc:
            raise ValueError(f"Destination already exists: {destination}") from exc
        except OSError as exc:
            raise ValueError(f"Cannot write artifact: {exc}") from exc
        return StepResult(output={"path": str(destination), "comment_id": comment_id})

    @staticmethod
    def _checkout(root: Path, url: str, number: int) -> StepResult:
        pr = _api(root, f"{url}/pulls/{number}")
        head = pr.get("head") if isinstance(pr, dict) else None
        sha = head.get("sha") if isinstance(head, dict) else None
        if not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{40}", sha):
            raise ValueError("GitHub PR has no valid head SHA")
        _run(["git", "fetch", "origin", f"pull/{number}/head"], root)
        fetched = _run(["git", "rev-parse", "FETCH_HEAD"], root)
        if fetched != sha:
            raise ValueError(
                "Fetched PR head differs from the GitHub PR head; retry after the PR settles"
            )
        _run(["git", "-c", "advice.detachedHead=false", "checkout", "--detach", sha], root)
        if _run(["git", "rev-parse", "HEAD"], root) != sha:
            raise ValueError("Checked-out HEAD differs from the GitHub PR head")
        return StepResult(output={"head_sha": sha, "number": number})
