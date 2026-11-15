"""Tests for the MCP-to-CLI subprocess adapter."""

import json
import subprocess
import sys
from unittest.mock import patch

import pytest

from specify_cli.mcp_server.catalog import CommandAdapterError
from specify_cli.mcp_server.executor import run_command

VERSION_PAYLOAD = {
    "cli_version": "1.2.3",
    "runtime": {"python": "3.13.1", "openssl": "OpenSSL 3.4.0"},
    "system": {
        "platform": "ExampleOS",
        "architecture": "example64",
        "os_version": "ExampleOS 4.5",
    },
    "features": {"workflow_catalog": True},
}


def _completed(
    returncode: int,
    *,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout=stdout.encode(),
        stderr=stderr.encode(),
    )


def test_run_version_invokes_canonical_cli_without_shell_and_returns_direct_payload():
    with patch(
        "specify_cli.mcp_server.executor.subprocess.run",
        return_value=_completed(0, stdout=json.dumps(VERSION_PAYLOAD)),
    ) as subprocess_run:
        result = run_command("version")

    assert result.model_dump() == VERSION_PAYLOAD
    assert subprocess_run.call_args.args[0] == [
        sys.executable,
        "-P",
        "-m",
        "specify_cli.mcp_server._worker",
        "version",
        "--json",
    ]
    assert "shell" not in subprocess_run.call_args.kwargs
    assert subprocess_run.call_args.kwargs["check"] is False


def test_run_rejects_unsupported_command_without_starting_process():
    with (
        patch("specify_cli.mcp_server.executor.subprocess.run") as subprocess_run,
        pytest.raises(CommandAdapterError) as captured,
    ):
        run_command("check")

    assert captured.value.code == "unavailable_command"
    subprocess_run.assert_not_called()


def test_run_version_ignores_shadow_worker_in_current_directory(
    monkeypatch,
    tmp_path,
):
    shadow_package = tmp_path / "specify_cli" / "mcp_server"
    shadow_package.mkdir(parents=True)
    (shadow_package.parent / "__init__.py").write_text("", encoding="utf-8")
    (shadow_package / "__init__.py").write_text("", encoding="utf-8")
    (shadow_package / "_worker.py").write_text(
        "print('shadow worker executed')\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    result = run_command("version")

    assert result.cli_version != "shadow worker executed"


def test_run_propagates_structured_cli_failure():
    failure = {
        "error": {
            "code": "internal_error",
            "message": "Unable to collect version information.",
            "details": {},
        }
    }
    with patch(
        "specify_cli.mcp_server.executor.subprocess.run",
        return_value=_completed(1, stderr=json.dumps(failure)),
    ), pytest.raises(CommandAdapterError) as captured:
        run_command("version")

    assert captured.value.payload() == failure


@pytest.mark.parametrize(
    ("completed", "reason"),
    [
        (_completed(0), "invalid_success_output"),
        (_completed(0, stdout="not-json"), "invalid_success_output"),
        (
            _completed(0, stdout=json.dumps({"cli_version": "1.2.3"})),
            "invalid_success_payload",
        ),
        (
            _completed(
                0,
                stdout=json.dumps(
                    {
                        **VERSION_PAYLOAD,
                        "features": {"workflow_catalog": "true"},
                    }
                ),
            ),
            "invalid_success_payload",
        ),
        (
            _completed(0, stdout=json.dumps(VERSION_PAYLOAD), stderr="warning"),
            "mixed_success_output",
        ),
        (_completed(1), "invalid_failure_output"),
        (_completed(1, stderr="not-json"), "invalid_failure_output"),
        (
            _completed(
                1,
                stderr=json.dumps(
                    {
                        "error": {
                            "code": "internal_error",
                            "message": "failed",
                        }
                    }
                ),
            ),
            "invalid_failure_payload",
        ),
        (
            _completed(
                1,
                stdout=json.dumps(VERSION_PAYLOAD),
                stderr=json.dumps(
                    {
                        "error": {
                            "code": "internal_error",
                            "message": "failed",
                            "details": {},
                        }
                    }
                ),
            ),
            "mixed_failure_output",
        ),
    ],
)
def test_run_rejects_invalid_or_mixed_machine_output(completed, reason):
    with patch(
        "specify_cli.mcp_server.executor.subprocess.run",
        return_value=completed,
    ), pytest.raises(CommandAdapterError) as captured:
        run_command("version")

    assert captured.value.code == "adapter_internal_error"
    assert captured.value.details == {"command": "version", "reason": reason}


def test_run_sanitizes_process_launch_failure():
    with patch(
        "specify_cli.mcp_server.executor.subprocess.run",
        side_effect=OSError("SECRET=/private/path"),
    ), pytest.raises(CommandAdapterError) as captured:
        run_command("version")

    assert captured.value.details == {
        "command": "version",
        "reason": "process_launch_failed",
    }
    assert "SECRET" not in json.dumps(captured.value.payload())


def test_run_normalizes_invalid_utf8_as_adapter_failure():
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=b"\xff",
        stderr=b"",
    )
    with (
        patch(
            "specify_cli.mcp_server.executor.subprocess.run",
            return_value=completed,
        ),
        pytest.raises(CommandAdapterError) as captured,
    ):
        run_command("version")

    assert captured.value.code == "adapter_internal_error"
    assert captured.value.details == {
        "command": "version",
        "reason": "invalid_utf8",
    }
