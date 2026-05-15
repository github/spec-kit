"""Shared test helpers for the Spec Kit test suite."""

import os
import re
import shutil
import subprocess
import sys

import pytest
import yaml

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _has_working_bash() -> bool:
    """Check whether a functional native bash is available.

    On Windows, ``subprocess.run(["bash", ...])`` uses CreateProcess,
    which searches System32 *before* PATH — so it may find the WSL
    launcher even when Git-for-Windows bash appears first in PATH via
    ``shutil.which``.  We therefore probe with bare ``"bash"`` (the
    same way test helpers invoke it) to get an accurate result.

    On Windows, only Git-for-Windows bash (MSYS2/MINGW) is accepted.
    The WSL launcher is rejected because it runs in a separate Linux
    filesystem and cannot handle native Windows paths used by the
    test fixtures.

    Set SPECKIT_TEST_BASH=1 to force-enable bash tests regardless.
    """
    if os.environ.get("SPECKIT_TEST_BASH") == "1":
        return True
    if shutil.which("bash") is None:
        return False
    # Probe with bare "bash" — same as the test helpers — so that
    # Windows CreateProcess resolution order is respected.
    try:
        r = subprocess.run(
            ["bash", "-c", "echo ok"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0 or "ok" not in r.stdout:
            return False
    except (OSError, subprocess.TimeoutExpired):
        return False
    # On Windows, verify we have MSYS/MINGW bash (Git for Windows),
    # not the WSL launcher which can't handle native paths.
    if sys.platform == "win32":
        try:
            u = subprocess.run(
                ["bash", "-c", "uname -s"],
                capture_output=True, text=True, timeout=5,
            )
            kernel = u.stdout.strip().upper()
            if not any(k in kernel for k in ("MSYS", "MINGW", "CYGWIN")):
                return False
        except (OSError, subprocess.TimeoutExpired):
            return False
    return True


requires_bash = pytest.mark.skipif(
    not _has_working_bash(), reason="working bash not available"
)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from Rich-formatted CLI output."""
    return _ANSI_ESCAPE_RE.sub("", text)


# ---------------------------------------------------------------------------
# Auth config isolation — prevents tests from reading ~/.specify/auth.json
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_auth_config(monkeypatch):
    """Ensure no test reads the real ~/.specify/auth.json."""
    from specify_cli.authentication import http as _auth_http
    monkeypatch.setattr(_auth_http, "_config_override", [])
    # Also clear the per-process cache so tests that unset _config_override
    # won't see a previously cached real-file result.
    monkeypatch.setattr(_auth_http, "_config_cache", None)


@pytest.fixture(autouse=True)
def _default_implement_preset_source(tmp_path, monkeypatch):
    """Use a local external implement preset for tests that run init."""
    if os.environ.get("SPECKIT_IMPLEMENT_PRESET_SOURCE"):
        return

    preset_dir = tmp_path / "default-implement-preset"
    (preset_dir / "commands").mkdir(parents=True, exist_ok=True)
    (preset_dir / "workflows" / "speckit-orchestrated-implement").mkdir(
        parents=True,
        exist_ok=True,
    )
    (preset_dir / "preset.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": "implement",
                    "name": "Orchestrated Implement",
                    "version": "1.0.0",
                    "description": "Test orchestrated implement preset",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "templates": [
                        {
                            "type": "command",
                            "name": "speckit.implement",
                            "file": "commands/speckit.implement.md",
                            "strategy": "replace",
                            "replaces": "speckit.implement",
                        }
                    ],
                    "workflows": [
                        {
                            "id": "speckit-orchestrated-implement",
                            "file": "workflows/speckit-orchestrated-implement/workflow.yml",
                        }
                    ],
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (preset_dir / "commands" / "speckit.implement.md").write_text(
        "---\ndescription: Test orchestrated implement\n---\n\n"
        "Run workflow or handoff shard. Use handoff JSON when provided.\n",
        encoding="utf-8",
    )
    (preset_dir / "workflows" / "speckit-orchestrated-implement" / "workflow.yml").write_text(
        """
schema_version: "1.0"
workflow:
  id: "speckit-orchestrated-implement"
  name: "Orchestrated Implementation"
  version: "1.0.0"
steps:
  - id: one
    type: shell
    run: "echo ok"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("SPECKIT_IMPLEMENT_PRESET_SOURCE", str(preset_dir))
