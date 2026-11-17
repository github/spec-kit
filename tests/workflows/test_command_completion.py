import json

import pytest

from specify_cli.workflows.base import StepContext, StepStatus
from specify_cli.workflows.step.command import CommandStep


def test_zero_exit_without_completion_is_not_success(monkeypatch, tmp_path):
    monkeypatch.setattr(
        CommandStep,
        "_try_dispatch",
        staticmethod(
            lambda *a, **k: {
                "exit_code": 0,
                "stdout": "Blocked: tool launcher unavailable",
                "stderr": "",
            }
        ),
    )
    result = CommandStep().execute(
        {
            "id": "constitution",
            "command": "speckit.constitution",
            "verify_completion": True,
            "capture": True,
        },
        StepContext(project_root=str(tmp_path)),
    )
    assert result.status == StepStatus.FAILED


@pytest.mark.parametrize(
    "mode",
    ["complete", "blocked", "stale", "missing", "escape", "bad_hash", "truncated"],
)
def test_verified_completion(monkeypatch, tmp_path, mode):
    import hashlib
    import re

    artifact = tmp_path / "report.md"
    artifact.write_text("Real report", encoding="utf-8")

    def dispatch(*args, **kwargs):
        nonce = re.search(r"completion_nonce=([a-f0-9]+)", args[3])[1]
        payload = {
            "nonce": nonce,
            "status": "completed",
            "artifacts": {
                "report.md": hashlib.sha256(artifact.read_bytes()).hexdigest()
            },
        }
        if mode == "blocked":
            payload["status"] = "blocked"
        if mode == "stale":
            payload["nonce"] = "old"
        if mode == "missing":
            artifact.unlink()
        if mode == "escape":
            payload["artifacts"] = {"../report.md": "x"}
        if mode == "bad_hash":
            payload["artifacts"]["report.md"] = "wrong"
        return {
            "exit_code": 0,
            "stdout": "SPECKIT_RESULT " + json.dumps(payload),
            "stderr": "",
            "stdout_truncated": mode == "truncated",
        }

    monkeypatch.setattr(CommandStep, "_try_dispatch", staticmethod(dispatch))
    result = CommandStep().execute(
        {
            "id": "analyze",
            "command": "speckit.analyze",
            "verify_completion": True,
            "capture": True,
        },
        StepContext(project_root=str(tmp_path)),
    )
    assert result.status == (
        StepStatus.COMPLETED if mode == "complete" else StepStatus.FAILED
    )


def test_completion_requires_capture():
    assert CommandStep().validate(
        {"id": "x", "command": "x", "verify_completion": True}
    )


@pytest.mark.parametrize("value", ["true", 1, None, []])
def test_invalid_completion_setting_never_dispatches(monkeypatch, tmp_path, value):
    def unexpected_dispatch(*args, **kwargs):
        pytest.fail("Invalid configuration must fail before dispatch")

    monkeypatch.setattr(CommandStep, "_try_dispatch", staticmethod(unexpected_dispatch))
    config = {"id": "x", "command": "x", "capture": True, "verify_completion": value}
    assert CommandStep().validate(config)
    assert (
        CommandStep().execute(config, StepContext(project_root=str(tmp_path))).status
        == StepStatus.FAILED
    )


@pytest.mark.parametrize(
    "stdout",
    [
        "SPECKIT_RESULT {",
        "SPECKIT_RESULT null",
        'SPECKIT_RESULT {"nonce":"current","status":"completed","artifacts":{}}',
        "SPECKIT_RESULT {}\nSPECKIT_RESULT {}",
    ],
)
def test_invalid_receipts_are_rejected(tmp_path, stdout):
    from specify_cli.workflows.step.command._completion import verify_completion

    with pytest.raises(ValueError):
        verify_completion({"stdout": stdout}, "current", tmp_path)
