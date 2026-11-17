"""Opt-in agent completion receipts, independent of process exit status."""

import hashlib
import json
from pathlib import Path, PurePosixPath


def completion_errors(config):
    value = config.get("verify_completion", False)
    if not isinstance(value, bool):
        return ["verify_completion must be true or false"]
    if value and config.get("capture") is not True:
        return ["verify_completion requires capture: true"]
    return []


def completion_prompt(nonce):
    return (
        f"\n\nWorkflow completion contract: completion_nonce={nonce}. "
        "Finish your response with exactly one line: SPECKIT_RESULT followed by a JSON object "
        'with keys nonce, status, artifacts. Use status="completed" only after the requested '
        "stage is actually complete. Missing prerequisites, unanswered clarification questions, "
        'failed tools or unfinished coding mean status="blocked". Artifacts is a nonempty '
        "mapping from project-relative forward-slash paths of this stage's actual output files "
        "to their SHA-256 hashes. Include every principal stage output. Do not write a receipt "
        "file or modify files outside this stage's ownership. Existing valid outputs may be "
        "reported after review. Coding completion does not mean tests passed. "
        "Use the exact nonce above; never reuse a prior completion response."
    )


def verify_completion(result, nonce, project_root):
    if any(result.get(k) for k in ("stdout_truncated", "timed_out", "interrupted")):
        raise ValueError(
            "Completion evidence is incomplete; the command was not verified"
        )
    lines = [
        line[len("SPECKIT_RESULT ") :]
        for line in result.get("stdout", "").splitlines()
        if line.startswith("SPECKIT_RESULT ")
    ]
    if len(lines) != 1:
        raise ValueError(
            "Missing or ambiguous completion receipt; exit code zero is insufficient"
        )
    try:
        receipt = json.loads(lines[0])
        if not isinstance(receipt, dict) or receipt.get("nonce") != nonce:
            raise ValueError("Completion receipt belongs to another invocation")
        if receipt.get("status") != "completed":
            raise ValueError("Agent reported blocked or incomplete work")
        artifacts = receipt.get("artifacts")
        if not isinstance(artifacts, dict) or not artifacts or not project_root:
            raise ValueError("Completion requires project output artifacts")
        root = Path(project_root).resolve()
        for name, expected in artifacts.items():
            relative = PurePosixPath(name)
            if (
                not name
                or relative.is_absolute()
                or ".." in relative.parts
                or ":" in name
                or "\\" in name
                or relative.as_posix() != name
            ):
                raise ValueError("Invalid completion artifact path")
            path = root.joinpath(*relative.parts)
            if not path.resolve().is_relative_to(root):
                raise ValueError("Completion artifact escapes project")
            current = path
            while current != root:
                if current.is_symlink():
                    raise ValueError("Symlinked completion artifact")
                current = current.parent
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError("Completion artifact is missing or empty")
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("Completion artifact differs from reported content")
        return receipt
    except (OSError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid or unreadable completion evidence") from exc
