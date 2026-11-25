"""Regression tests for scripts/python/resolve_template.py raw UTF-8 output."""

from __future__ import annotations

import io
import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts.python import resolve_template
from tests.parity_helpers import (
    PROJECT_ROOT,
    install_scripts,
    install_section_stack,
    make_repo,
    py_cmd,
)

SCRIPT = "resolve-template"


def _narrow_env(io_encoding: str | None) -> dict[str, str]:
    env = dict(os.environ)
    for key in list(env):
        if key.startswith("SPECIFY_"):
            env.pop(key)
    env.pop("PYTHONPATH", None)
    env.pop("SPECKIT_PYTHON", None)
    env.pop("PYTHONIOENCODING", None)
    env.pop("PYTHONUTF8", None)
    if os.name == "nt":
        env["PYTHONUTF8"] = "0"
    if io_encoding is not None:
        env["PYTHONIOENCODING"] = io_encoding
    return env


def _run_raw(
    cmd: list[str], cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, timeout=30)


@pytest.mark.parametrize(
    "io_encoding",
    [
        pytest.param(
            None,
            marks=pytest.mark.skipif(
                os.name != "nt", reason="Windows default pipe encoding"
            ),
        ),
        "cp1252",
        "ascii",
    ],
    ids=["windows-default", "cp1252", "ascii"],
)
def test_raw_output_emits_stock_tasks_template_utf8_under_narrow_stdout(
    tmp_path: Path, io_encoding: str | None
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    expected = (PROJECT_ROOT / "templates" / "tasks-template.md").read_bytes()
    assert "\U0001f3af".encode("utf-8") in expected
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True)
    (templates / "tasks-template.md").write_bytes(expected)

    result = _run_raw(
        py_cmd(repo, SCRIPT, "tasks-template"),
        repo,
        _narrow_env(io_encoding),
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert result.stderr == b""
    assert result.stdout == expected


@pytest.mark.parametrize(
    "raw_bytes",
    [
        b"# Spec\r\nLine 2\r\n",
        b"# Spec\nLine 2\n",
        b"# Spec\r\nBody: \xe2\x86\x92 \xe5\x8a\x9f\xe8\x83\xbd \xf0\x9f\x8e\xaf\r\n",
        b"# Spec\nBody: \xe2\x86\x92 \xe5\x8a\x9f\xe8\x83\xbd \xf0\x9f\x8e\xaf\n",
    ],
    ids=["ascii-crlf", "ascii-lf", "utf8-crlf", "utf8-lf"],
)
def test_raw_output_preserves_exact_utf8_bytes_and_line_endings(
    tmp_path: Path, raw_bytes: bytes
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True)
    (templates / "sample-template.md").write_bytes(raw_bytes)

    result = _run_raw(
        py_cmd(repo, SCRIPT, "sample-template"),
        repo,
        _narrow_env("cp1252"),
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert result.stderr == b""
    assert result.stdout == raw_bytes


def test_json_output_still_emits_ascii_json_with_unicode_and_crlf(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    expected = "# Spec \U0001f3af\r\n\u529f\u80fd \u2192 ok\r\n"
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True)
    (templates / "sample-template.md").write_bytes(expected.encode("utf-8"))

    result = _run_raw(
        py_cmd(repo, SCRIPT, "sample-template", "--json"),
        repo,
        _narrow_env("ascii"),
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert result.stderr == b""
    assert result.stdout.isascii()
    assert json.loads(result.stdout.decode("ascii")) == {
        "TEMPLATE_NAME": "sample-template",
        "TEMPLATE_CONTENT": expected,
    }


def test_missing_template_exits_1_with_empty_stdout_under_narrow_pipe(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path, "proj-\u529f\u80fd")
    install_scripts(repo, SCRIPT)

    result = _run_raw(
        py_cmd(repo, SCRIPT, "missing-template"),
        repo,
        _narrow_env("ascii"),
    )

    assert result.returncode == 1
    assert result.stdout == b""
    assert b"ERROR: Could not resolve required missing-template" in result.stderr
    assert b"Traceback" not in result.stderr


def test_template_resolution_error_exits_1_with_empty_stdout_under_narrow_pipe(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    name, _ = install_section_stack(
        repo, "# Missing\n", "new\n", selector="\u65e5\u672c\u8a9e"
    )

    result = _run_raw(
        py_cmd(repo, SCRIPT, name),
        repo,
        _narrow_env("ascii"),
    )

    assert result.returncode == 1
    assert result.stdout == b""
    assert b"SECTION_NOT_FOUND" in result.stderr
    assert b"Traceback" not in result.stderr


def test_main_falls_back_when_stdout_lacks_buffer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo(tmp_path)
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True)
    expected = "# Title \U0001f3af\n"
    (templates / "sample-template.md").write_bytes(expected.encode("utf-8"))
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(repo))

    out = io.StringIO()
    err = io.StringIO()
    monkeypatch.setattr(resolve_template.sys, "stdout", out)
    monkeypatch.setattr(resolve_template.sys, "stderr", err)

    assert resolve_template.main(["sample-template"]) == 0
    assert out.getvalue() == expected
    assert err.getvalue() == ""

    assert resolve_template.main(["missing-template"]) == 1
    assert "ERROR: Could not resolve required missing-template" in err.getvalue()
