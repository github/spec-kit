"""Tests for the bundled ``agent-context`` extension and related plumbing."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from specify_cli import (
    _load_agent_context_config,
    _save_agent_context_config,
    load_init_options,
    save_init_options,
)
from specify_cli.agents import CommandRegistrar
from specify_cli.integrations.base import IntegrationBase
from specify_cli.integrations.claude import ClaudeIntegration
from tests.conftest import requires_bash


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "agent-context"
BASH = shutil.which("bash")
POWERSHELL = (
    shutil.which("pwsh") or shutil.which("powershell.exe") or shutil.which("powershell")
)


def _write_ext_config(project_root: Path, **overrides: object) -> None:
    """Write a minimal agent-context extension config."""
    cfg: dict = {
        "context_file": overrides.get("context_file", ""),
        "context_files": overrides.get("context_files", []),
        "context_markers": overrides.get(
            "context_markers",
            {
                "start": IntegrationBase.CONTEXT_MARKER_START,
                "end": IntegrationBase.CONTEXT_MARKER_END,
            },
        ),
    }
    _save_agent_context_config(project_root, cfg)


# ── Bundled extension layout ─────────────────────────────────────────────────


class TestExtensionLayout:
    """The bundled agent-context extension ships a complete package."""

    def test_extension_yml_exists(self):
        assert (EXT_DIR / "extension.yml").is_file()

    def test_extension_yml_has_required_fields(self):
        manifest = yaml.safe_load((EXT_DIR / "extension.yml").read_text())
        assert manifest["extension"]["id"] == "agent-context"
        assert manifest["extension"]["name"] == "Coding Agent Context"
        assert manifest["extension"]["author"] == "spec-kit-core"
        # Provides at least the manual update command
        commands = {c["name"] for c in manifest["provides"]["commands"]}
        assert "speckit.agent-context.update" in commands

    def test_readme_exists(self):
        readme = EXT_DIR / "README.md"
        assert readme.is_file()
        text = readme.read_text(encoding="utf-8")
        assert "Coding Agent Context Extension" in text

    def test_config_template_exists(self):
        cfg = EXT_DIR / "agent-context-config.yml"
        assert cfg.is_file()
        parsed = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        assert "context_file" in parsed
        assert "context_markers" in parsed

    def test_command_file_exists(self):
        cmd = EXT_DIR / "commands" / "speckit.agent-context.update.md"
        assert cmd.is_file()
        assert "agent-context-config.yml" in cmd.read_text(encoding="utf-8")

    def test_command_file_documents_context_file_constraints(self):
        text = (
            EXT_DIR / "commands" / "speckit.agent-context.update.md"
        ).read_text(encoding="utf-8")
        assert "context file(s)" in text
        assert "Windows drive paths" in text
        assert "backslash separators" in text

    def test_bundled_scripts_exist(self):
        assert (EXT_DIR / "scripts" / "bash" / "update-agent-context.sh").is_file()
        assert (EXT_DIR / "scripts" / "powershell" / "update-agent-context.ps1").is_file()

    def test_bash_script_reads_extension_config(self):
        text = (EXT_DIR / "scripts" / "bash" / "update-agent-context.sh").read_text(
            encoding="utf-8"
        )
        # The script must consult the extension config, not init-options.json
        assert "agent-context-config.yml" in text
        assert "context_file" in text
        assert "context_markers" in text


# ── Catalog registration ─────────────────────────────────────────────────────


class TestCatalogEntry:
    def test_catalog_lists_agent_context_as_bundled(self):
        catalog = json.loads(
            (PROJECT_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8")
        )
        entry = catalog["extensions"]["agent-context"]
        assert entry["bundled"] is True
        assert entry["id"] == "agent-context"
        assert entry["author"] == "spec-kit-core"


# ── Marker resolution from extension config ──────────────────────────────────


class _CtxIntegration(ClaudeIntegration):
    """Use Claude as a concrete integration with a context_file."""


class _NoContextIntegration(IntegrationBase):
    """Minimal integration with no context_file for base-class fallback tests."""


def _install_agent_context_config(project_root: Path, **overrides: object) -> None:
    _write_ext_config(project_root, **overrides)


def _bash_posix_path(path: Path) -> str:
    """Convert a Windows path to the POSIX form used by the available bash."""
    resolved = str(path.resolve())
    if os.name != "nt":
        return resolved

    if BASH:
        converted = subprocess.run(
            [
                BASH,
                "-lc",
                "command -v cygpath >/dev/null 2>&1 && cygpath -u \"$1\"",
                "bash",
                resolved,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if converted.returncode == 0 and converted.stdout.strip():
            return converted.stdout.strip()

    drive = path.drive.rstrip(":").lower()
    posix = path.as_posix()
    return f"/mnt/{drive}{posix[2:]}" if drive else posix


def _ensure_test_python_on_path(project_root: Path) -> Path:
    """Create python/python3 shims that run the current pytest interpreter."""
    shim_dir = project_root / ".test-python-bin"
    shim_dir.mkdir(exist_ok=True)
    python_exe = Path(sys.executable).resolve()
    shell_python = _bash_posix_path(python_exe)

    for name in ("python", "python3"):
        shell_shim = shim_dir / name
        shell_shim.write_text(
            f"#!/usr/bin/env sh\nexec {shlex_quote(shell_python)} \"$@\"\n",
            encoding="utf-8",
            newline="\n",
        )
        shell_shim.chmod(0o755)

        if os.name == "nt":
            cmd_shim = shim_dir / f"{name}.cmd"
            cmd_shim.write_text(
                f'@echo off\r\n"{python_exe}" %*\r\n',
                encoding="utf-8",
            )

    return shim_dir


def _current_pythonpath() -> str:
    """Return sys.path entries needed by child script interpreters."""
    entries = [
        entry
        for entry in sys.path
        if isinstance(entry, str) and entry
    ]
    existing = os.environ.get("PYTHONPATH")
    if existing:
        entries.extend(entry for entry in existing.split(os.pathsep) if entry)
    return os.pathsep.join(dict.fromkeys(entries))


def _bundled_script_env(
    project_root: Path,
    *,
    for_bash: bool = False,
    speckit_python: str | None = None,
) -> dict[str, str]:
    env = os.environ.copy()
    shim_dir = _ensure_test_python_on_path(project_root)
    env["PATH"] = str(shim_dir) + os.pathsep + env.get("PATH", "")
    env["SPECKIT_PYTHON"] = (
        speckit_python
        if speckit_python is not None
        else (_bash_posix_path(Path(sys.executable)) if for_bash else sys.executable)
    )
    pythonpath = _current_pythonpath()
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    return env


def _run_bash_agent_context_script(
    project_root: Path,
    *,
    speckit_python: str | None = None,
) -> subprocess.CompletedProcess:
    script = EXT_DIR / "scripts" / "bash" / "update-agent-context.sh"
    env = _bundled_script_env(
        project_root,
        for_bash=True,
        speckit_python=speckit_python,
    )
    if os.name == "nt":
        root = _bash_posix_path(project_root)
        script_path = _bash_posix_path(script)
        shim_dir = _bash_posix_path(_ensure_test_python_on_path(project_root))
        command = (
            f"export PATH={shlex_quote(shim_dir)}:\"$PATH\"; "
            f"cd {shlex_quote(root)} && {shlex_quote(script_path)}"
        )
        return subprocess.run(
            [BASH, "-lc", command],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
    return subprocess.run(
        [BASH, str(script)],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def shlex_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _run_powershell_agent_context_script(project_root: Path) -> subprocess.CompletedProcess:
    script = EXT_DIR / "scripts" / "powershell" / "update-agent-context.ps1"
    env = _bundled_script_env(project_root)
    return subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _run_powershell_agent_context_script_with_env(
    project_root: Path,
    *,
    speckit_python: str,
) -> subprocess.CompletedProcess:
    script = EXT_DIR / "scripts" / "powershell" / "update-agent-context.ps1"
    env = _bundled_script_env(project_root, speckit_python=speckit_python)
    return subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestContextMarkerResolution:
    def test_defaults_when_ext_config_missing(self, tmp_path):
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == IntegrationBase.CONTEXT_MARKER_START
        assert end == IntegrationBase.CONTEXT_MARKER_END

    def test_defaults_when_markers_field_missing(self, tmp_path):
        """Config file exists with context_file but no context_markers key."""
        cfg_path = (
            tmp_path / ".specify" / "extensions" / "agent-context"
            / "agent-context-config.yml"
        )
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text("context_file: CLAUDE.md\n", encoding="utf-8")
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == IntegrationBase.CONTEXT_MARKER_START
        assert end == IntegrationBase.CONTEXT_MARKER_END

    def test_custom_markers_respected(self, tmp_path):
        _write_ext_config(
            tmp_path,
            context_markers={"start": "<!-- BEGIN -->", "end": "<!-- END -->"},
        )
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == "<!-- BEGIN -->"
        assert end == "<!-- END -->"

    def test_partial_override_falls_back_for_missing_side(self, tmp_path):
        _write_ext_config(tmp_path, context_markers={"start": "<!-- ONLY START -->"})
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == "<!-- ONLY START -->"
        assert end == IntegrationBase.CONTEXT_MARKER_END

    def test_invalid_markers_fall_back(self, tmp_path):
        _write_ext_config(tmp_path, context_markers={"start": 42, "end": ""})
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == IntegrationBase.CONTEXT_MARKER_START
        assert end == IntegrationBase.CONTEXT_MARKER_END


# ── upsert_context_section / remove_context_section honor markers ───────────


class TestUpsertWithCustomMarkers:
    def _setup(self, tmp_path: Path, markers: dict | None = None) -> _CtxIntegration:
        _write_ext_config(
            tmp_path,
            context_file="CLAUDE.md",
            **({"context_markers": markers} if markers is not None else {}),
        )
        return _CtxIntegration()

    def test_upsert_uses_default_markers(self, tmp_path):
        i = self._setup(tmp_path)
        result = i.upsert_context_section(tmp_path)
        assert result is not None
        text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert IntegrationBase.CONTEXT_MARKER_START in text
        assert IntegrationBase.CONTEXT_MARKER_END in text

    def test_upsert_uses_custom_markers(self, tmp_path):
        i = self._setup(
            tmp_path, {"start": "<!-- BEGIN -->", "end": "<!-- END -->"}
        )
        i.upsert_context_section(tmp_path)
        text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert "<!-- BEGIN -->" in text
        assert "<!-- END -->" in text
        # Defaults must not appear
        assert IntegrationBase.CONTEXT_MARKER_START not in text
        assert IntegrationBase.CONTEXT_MARKER_END not in text

    def test_upsert_replaces_existing_custom_section(self, tmp_path):
        i = self._setup(
            tmp_path, {"start": "<!-- BEGIN -->", "end": "<!-- END -->"}
        )
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text(
            "# header\n\n<!-- BEGIN -->\nold body\n<!-- END -->\n\nfooter\n",
            encoding="utf-8",
        )
        i.upsert_context_section(tmp_path, plan_path="specs/001-foo/plan.md")
        text = ctx.read_text(encoding="utf-8")
        assert "old body" not in text
        assert "specs/001-foo/plan.md" in text
        assert text.startswith("# header\n")
        assert "footer" in text

    def test_upsert_uses_configured_context_files(self, tmp_path):
        _write_ext_config(
            tmp_path,
            context_file="CLAUDE.md",
            context_files=["AGENTS.md", "CLAUDE.md"],
        )
        i = _CtxIntegration()
        result = i.upsert_context_section(
            tmp_path, plan_path="specs/001-foo/plan.md"
        )
        assert result == tmp_path / "AGENTS.md"
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (tmp_path / name).read_text(encoding="utf-8")
            assert IntegrationBase.CONTEXT_MARKER_START in text
            assert "specs/001-foo/plan.md" in text

    def test_context_files_deduplicate_with_platform_semantics(self, tmp_path):
        duplicate = "agents.md" if os.name == "nt" else "AGENTS.md"
        _write_ext_config(
            tmp_path,
            context_file="CLAUDE.md",
            context_files=["AGENTS.md", "CLAUDE.md", duplicate],
        )

        files = _CtxIntegration()._resolve_context_files(tmp_path)

        assert files == ["AGENTS.md", "CLAUDE.md"]

    def test_empty_context_files_falls_back_to_config_context_file(self, tmp_path):
        _write_ext_config(
            tmp_path,
            context_file="AGENTS.md",
            context_files=[],
        )

        files = _CtxIntegration()._resolve_context_files(tmp_path)

        assert files == ["AGENTS.md"]

    def test_config_context_file_takes_precedence_over_class_default(self, tmp_path):
        _write_ext_config(
            tmp_path,
            context_file="AGENTS.md",
        )

        i = _CtxIntegration()
        result = i.upsert_context_section(
            tmp_path, plan_path="specs/001-foo/plan.md"
        )

        assert result == tmp_path / "AGENTS.md"
        assert (tmp_path / "AGENTS.md").exists()
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_config_context_file_fallback_rejects_invalid_path(self, tmp_path):
        _write_ext_config(
            tmp_path,
            context_file="../outside.md",
            context_files=[],
        )

        with pytest.raises(ValueError, match="project-relative|must not contain"):
            _CtxIntegration()._resolve_context_files(tmp_path)

    def test_remove_uses_configured_context_files(self, tmp_path):
        _write_ext_config(
            tmp_path,
            context_file="CLAUDE.md",
            context_files=["AGENTS.md", "CLAUDE.md"],
        )
        i = _CtxIntegration()
        for name in ("AGENTS.md", "CLAUDE.md"):
            (tmp_path / name).write_text(
                f"head\n{IntegrationBase.CONTEXT_MARKER_START}\nbody\n"
                f"{IntegrationBase.CONTEXT_MARKER_END}\ntail\n",
                encoding="utf-8",
            )
        assert i.remove_context_section(tmp_path) is True
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (tmp_path / name).read_text(encoding="utf-8")
            assert "body" not in text
            assert "head" in text
            assert "tail" in text

    @pytest.mark.parametrize(
        "bad_path",
        [
            "../outside.md",
            "nested/../../outside.md",
            "nested\\outside.md",
            str(Path("/tmp/outside.md")),
            "C:/tmp/outside.md",
            "C:tmp/outside.md",
        ],
    )
    def test_upsert_rejects_context_files_outside_project(self, tmp_path, bad_path):
        _write_ext_config(
            tmp_path,
            context_file="CLAUDE.md",
            context_files=["AGENTS.md", bad_path],
        )
        i = _CtxIntegration()
        with pytest.raises(ValueError, match="project-relative|must not contain"):
            i.upsert_context_section(tmp_path)

        assert not (tmp_path / "AGENTS.md").exists()
        assert not (tmp_path.parent / "outside.md").exists()

    @pytest.mark.parametrize(
        "bad_path",
        [
            "../outside.md",
            "nested\\outside.md",
            str(Path("/tmp/outside.md")),
            "C:/tmp/outside.md",
            "C:tmp/outside.md",
        ],
    )
    def test_remove_rejects_context_files_outside_project(self, tmp_path, bad_path):
        _write_ext_config(
            tmp_path,
            context_file="CLAUDE.md",
            context_files=["AGENTS.md", bad_path],
        )
        outside = tmp_path.parent / "outside.md"
        outside.write_text(
            f"{IntegrationBase.CONTEXT_MARKER_START}\nbody\n"
            f"{IntegrationBase.CONTEXT_MARKER_END}\n",
            encoding="utf-8",
        )
        i = _CtxIntegration()
        with pytest.raises(ValueError, match="project-relative|must not contain"):
            i.remove_context_section(tmp_path)

        assert "body" in outside.read_text(encoding="utf-8")

    def test_remove_uses_custom_markers(self, tmp_path):
        i = self._setup(
            tmp_path, {"start": "<!-- BEGIN -->", "end": "<!-- END -->"}
        )
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text(
            "preamble\n\n<!-- BEGIN -->\nbody\n<!-- END -->\nepilogue\n",
            encoding="utf-8",
        )
        removed = i.remove_context_section(tmp_path)
        assert removed is True
        remaining = ctx.read_text(encoding="utf-8")
        assert "<!-- BEGIN -->" not in remaining
        assert "<!-- END -->" not in remaining
        assert "body" not in remaining
        assert "preamble" in remaining
        assert "epilogue" in remaining

    def test_remove_with_default_markers_unchanged_when_custom_in_file(self, tmp_path):
        # Extension config absent → default markers used. File contains only
        # custom markers — nothing should be removed.
        i = _CtxIntegration()
        ctx = tmp_path / "CLAUDE.md"
        original = "x\n<!-- BEGIN -->\nbody\n<!-- END -->\n"
        ctx.write_text(original, encoding="utf-8")
        assert i.remove_context_section(tmp_path) is False
        assert ctx.read_text(encoding="utf-8") == original


# ── Extension disabled gates setup/teardown ──────────────────────────────────


def _write_registry(project_root: Path, *, enabled: bool) -> None:
    registry = project_root / ".specify" / "extensions" / ".registry"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "extensions": {
                    "agent-context": {
                        "version": "1.0.0",
                        "enabled": enabled,
                    }
                },
            }
        ),
        encoding="utf-8",
    )


class TestExtensionEnabledGate:
    def test_enabled_helper_default_when_no_registry(self, tmp_path):
        assert IntegrationBase._agent_context_extension_enabled(tmp_path) is True

    def test_enabled_helper_when_entry_present(self, tmp_path):
        _write_registry(tmp_path, enabled=True)
        assert IntegrationBase._agent_context_extension_enabled(tmp_path) is True

    def test_disabled_helper_when_entry_disabled(self, tmp_path):
        _write_registry(tmp_path, enabled=False)
        assert IntegrationBase._agent_context_extension_enabled(tmp_path) is False

    def test_upsert_skipped_when_disabled(self, tmp_path):
        _write_registry(tmp_path, enabled=False)
        i = _CtxIntegration()
        result = i.upsert_context_section(tmp_path)
        assert result is None
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_upsert_disabled_ignores_bad_context_files_config(self, tmp_path):
        _write_registry(tmp_path, enabled=False)
        _write_ext_config(
            tmp_path,
            context_file="CLAUDE.md",
            context_files=["../disabled-upsert-outside.md"],
        )
        i = _CtxIntegration()
        assert i.upsert_context_section(tmp_path) is None
        assert not (tmp_path.parent / "disabled-upsert-outside.md").exists()

    def test_remove_skipped_when_disabled(self, tmp_path):
        _write_registry(tmp_path, enabled=False)
        i = _CtxIntegration()
        ctx = tmp_path / "CLAUDE.md"
        original = (
            f"head\n{IntegrationBase.CONTEXT_MARKER_START}\nbody\n"
            f"{IntegrationBase.CONTEXT_MARKER_END}\ntail\n"
        )
        ctx.write_text(original, encoding="utf-8")
        assert i.remove_context_section(tmp_path) is False
        # File must be unchanged when extension is disabled
        assert ctx.read_text(encoding="utf-8") == original

    def test_remove_disabled_ignores_bad_context_files_config(self, tmp_path):
        _write_registry(tmp_path, enabled=False)
        _write_ext_config(
            tmp_path,
            context_file="CLAUDE.md",
            context_files=["../disabled-remove-outside.md"],
        )
        outside = tmp_path.parent / "disabled-remove-outside.md"
        outside.write_text(
            f"{IntegrationBase.CONTEXT_MARKER_START}\nbody\n"
            f"{IntegrationBase.CONTEXT_MARKER_END}\n",
            encoding="utf-8",
        )
        i = _CtxIntegration()
        assert i.remove_context_section(tmp_path) is False
        assert "body" in outside.read_text(encoding="utf-8")

    def test_context_file_display_disabled_uses_config_context_file(
        self, tmp_path
    ):
        _write_registry(tmp_path, enabled=False)
        _write_ext_config(
            tmp_path,
            context_file="AGENTS.md",
            context_files=["../outside.md"],
        )
        i = _CtxIntegration()
        assert i._context_file_display(tmp_path) == "AGENTS.md"

    def test_context_file_display_disabled_without_context_file_returns_string(
        self, tmp_path
    ):
        _write_registry(tmp_path, enabled=False)
        i = _NoContextIntegration()
        assert i._context_file_display(tmp_path) == ""


class TestSkillPlaceholderContextValidation:
    @pytest.mark.parametrize(
        "bad_path",
        [
            "../outside.md",
            "nested/../../outside.md",
            "nested\\outside.md",
            str(Path("/tmp/outside.md")),
            "C:/tmp/outside.md",
            "C:tmp/outside.md",
        ],
    )
    def test_context_files_reject_invalid_config_paths(self, tmp_path, bad_path):
        _write_ext_config(
            tmp_path,
            context_file="AGENTS.md",
            context_files=["AGENTS.md", bad_path],
        )

        with pytest.raises(ValueError, match="project-relative|must not contain"):
            CommandRegistrar.resolve_skill_placeholders(
                "codex",
                {},
                "Read __CONTEXT_FILE__",
                tmp_path,
            )

    @pytest.mark.parametrize(
        "bad_path",
        [
            "../outside.md",
            "C:tmp/outside.md",
        ],
    )
    def test_context_file_rejects_invalid_config_path(self, tmp_path, bad_path):
        _write_ext_config(
            tmp_path,
            context_file=bad_path,
            context_files=[],
        )

        with pytest.raises(ValueError, match="project-relative|must not contain"):
            CommandRegistrar.resolve_skill_placeholders(
                "codex",
                {},
                "Read __CONTEXT_FILE__",
                tmp_path,
            )

    def test_enabled_extension_rejects_invalid_legacy_init_options_path(
        self, tmp_path
    ):
        save_init_options(tmp_path, {"context_file": "../outside.md"})

        with pytest.raises(ValueError, match="must not contain"):
            CommandRegistrar.resolve_skill_placeholders(
                "codex",
                {},
                "Read __CONTEXT_FILE__",
                tmp_path,
            )

    def test_disabled_extension_ignores_invalid_context_files(self, tmp_path):
        _write_registry(tmp_path, enabled=False)
        _write_ext_config(
            tmp_path,
            context_file="AGENTS.md",
            context_files=["../outside.md"],
        )
        save_init_options(tmp_path, {"context_file": "AGENTS.md"})

        content = CommandRegistrar.resolve_skill_placeholders(
            "codex",
            {},
            "Read __CONTEXT_FILE__",
            tmp_path,
        )

        assert content == "Read AGENTS.md"

    def test_disabled_extension_uses_extension_context_file_before_init_options(
        self, tmp_path
    ):
        _write_registry(tmp_path, enabled=False)
        _write_ext_config(
            tmp_path,
            context_file="AGENTS.md",
            context_files=["CLAUDE.md"],
        )
        save_init_options(tmp_path, {"context_file": "LEGACY.md"})

        content = CommandRegistrar.resolve_skill_placeholders(
            "codex",
            {},
            "Read __CONTEXT_FILE__",
            tmp_path,
        )

        assert content == "Read AGENTS.md"

    def test_context_files_deduplicate_with_platform_semantics(self, tmp_path):
        duplicate = "agents.md" if os.name == "nt" else "AGENTS.md"
        _write_ext_config(
            tmp_path,
            context_file="AGENTS.md",
            context_files=["AGENTS.md", "CLAUDE.md", duplicate],
        )

        content = CommandRegistrar.resolve_skill_placeholders(
            "codex",
            {},
            "Read __CONTEXT_FILE__",
            tmp_path,
        )

        assert content == "Read AGENTS.md, CLAUDE.md"


class TestBundledUpdaterPathValidation:
    def test_bundled_script_env_makes_yaml_importable(self, tmp_path):
        env = _bundled_script_env(tmp_path)

        result = subprocess.run(
            [env["SPECKIT_PYTHON"], "-c", "import yaml"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, result.stderr + result.stdout

    @requires_bash
    def test_bash_script_trims_context_file_fallback(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(
            project,
            context_file="  AGENTS.md  ",
            context_files=[],
        )

        result = _run_bash_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        assert "agent-context: updated AGENTS.md" in (result.stderr + result.stdout)
        assert (project / "AGENTS.md").exists()
        assert not (project / "  AGENTS.md  ").exists()

    @requires_bash
    def test_bash_script_rejects_symlink_escape(self, tmp_path):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        project.mkdir()
        outside.mkdir()
        _install_agent_context_config(
            project,
            context_file="AGENTS.md",
            context_files=["link/out.md"],
        )

        if os.name == "nt":
            root = _bash_posix_path(tmp_path)
            create_link = subprocess.run(
                [
                    BASH,
                    "-lc",
                    f"ln -s {shlex_quote(root + '/outside')} "
                    f"{shlex_quote(root + '/project/link')}",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if create_link.returncode != 0:
                pytest.skip(f"symlink unavailable: {create_link.stderr}")
        else:
            try:
                (project / "link").symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                pytest.skip(f"symlink unavailable: {exc}")

        result = _run_bash_agent_context_script(project)

        assert result.returncode == 1
        assert "resolves outside the project root" in result.stderr
        assert not (outside / "out.md").exists()

    @requires_bash
    def test_bash_script_deduplicates_context_files_in_order(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        duplicate = "agents.md" if os.name == "nt" else "AGENTS.md"
        _install_agent_context_config(
            project,
            context_file="AGENTS.md",
            context_files=["AGENTS.md", "CLAUDE.md", duplicate],
        )

        result = _run_bash_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        output = result.stderr + result.stdout
        assert output.count("agent-context: updated AGENTS.md") == 1
        assert output.count("agent-context: updated CLAUDE.md") == 1
        assert "agent-context: updated agents.md" not in output

    @requires_bash
    def test_bash_script_falls_back_from_invalid_speckit_python(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(
            project,
            context_file="AGENTS.md",
            context_files=["AGENTS.md"],
        )

        result = _run_bash_agent_context_script(
            project,
            speckit_python="/definitely/missing/python",
        )

        assert result.returncode == 0, result.stderr + result.stdout
        assert "agent-context: updated AGENTS.md" in (result.stderr + result.stdout)
        assert (project / "AGENTS.md").exists()

    @pytest.mark.skipif(POWERSHELL is None, reason="PowerShell not available")
    def test_powershell_script_rejects_backslash_context_files(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(
            project,
            context_file="AGENTS.md",
            context_files=["nested\\AGENTS.md"],
        )

        result = _run_powershell_agent_context_script(project)

        assert result.returncode == 1
        assert "must not contain backslash separators" in (
            result.stderr + result.stdout
        )
        assert not (project / "nested" / "AGENTS.md").exists()

    @pytest.mark.skipif(POWERSHELL is None, reason="PowerShell not available")
    def test_powershell_script_rejects_drive_qualified_context_files(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(
            project,
            context_file="AGENTS.md",
            context_files=["C:tmp/outside.md"],
        )

        result = _run_powershell_agent_context_script(project)

        assert result.returncode == 1
        assert "must be project-relative paths" in (result.stderr + result.stdout)
        assert not (project / "tmp" / "outside.md").exists()

    @pytest.mark.skipif(POWERSHELL is None, reason="PowerShell not available")
    def test_powershell_script_deduplicates_context_files_in_order(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        duplicate = "agents.md" if os.name == "nt" else "AGENTS.md"
        _install_agent_context_config(
            project,
            context_file="AGENTS.md",
            context_files=["AGENTS.md", "CLAUDE.md", duplicate],
        )

        result = _run_powershell_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        output = result.stderr + result.stdout
        assert output.count("agent-context: updated AGENTS.md") == 1
        assert output.count("agent-context: updated CLAUDE.md") == 1
        assert "agent-context: updated agents.md" not in output

    @pytest.mark.skipif(POWERSHELL is None, reason="PowerShell not available")
    def test_powershell_script_falls_back_from_invalid_speckit_python(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(
            project,
            context_file="AGENTS.md",
            context_files=["AGENTS.md"],
        )

        result = _run_powershell_agent_context_script_with_env(
            project,
            speckit_python=str(project / "missing-python"),
        )

        assert result.returncode == 0, result.stderr + result.stdout
        assert "agent-context: updated AGENTS.md" in (result.stderr + result.stdout)
        assert (project / "AGENTS.md").exists()

    @pytest.mark.skipif(
        POWERSHELL is None or os.name != "nt",
        reason="Windows PowerShell junction test requires Windows",
    )
    def test_powershell_script_rejects_junction_escape(self, tmp_path):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        project.mkdir()
        outside.mkdir()
        _install_agent_context_config(
            project,
            context_file="AGENTS.md",
            context_files=["link/out.md"],
        )

        create_link = subprocess.run(
            [
                POWERSHELL,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                (
                    "New-Item -ItemType Junction "
                    f"-Path {str(project / 'link')!r} "
                    f"-Target {str(outside)!r} | Out-Null"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if create_link.returncode != 0:
            pytest.skip(f"junction unavailable: {create_link.stderr}")

        result = _run_powershell_agent_context_script(project)

        assert result.returncode == 1
        assert "resolves outside the project root" in (result.stderr + result.stdout)
        assert not (outside / "out.md").exists()


# ── Extension config writers ─────────────────────────────────────────────────


class TestExtensionConfigWriters:
    def test_clear_init_options_clears_ext_config_context_file(self, tmp_path):
        from specify_cli import _clear_init_options_for_integration

        save_init_options(
            tmp_path,
            {"integration": "claude", "ai": "claude"},
        )
        _write_ext_config(tmp_path, context_file="CLAUDE.md")
        _clear_init_options_for_integration(tmp_path, "claude")
        cfg = _load_agent_context_config(tmp_path)
        assert cfg.get("context_file") == ""

    def test_clear_init_options_creates_ext_config_when_missing(self, tmp_path):
        from specify_cli import _clear_init_options_for_integration

        save_init_options(
            tmp_path,
            {"integration": "claude", "ai": "claude"},
        )
        _clear_init_options_for_integration(tmp_path, "claude")
        cfg = _load_agent_context_config(tmp_path)
        assert cfg.get("context_file") == ""

    def test_clear_init_options_removes_legacy_context_keys_even_when_not_active(
        self, tmp_path
    ):
        from specify_cli import _clear_init_options_for_integration

        save_init_options(
            tmp_path,
            {
                "integration": "copilot",
                "ai": "copilot",
                "context_file": "CLAUDE.md",
                "context_markers": {"start": "<!-- X -->", "end": "<!-- Y -->"},
            },
        )
        _clear_init_options_for_integration(tmp_path, "claude")
        opts = load_init_options(tmp_path)
        assert opts["integration"] == "copilot"
        assert opts["ai"] == "copilot"
        assert "context_file" not in opts
        assert "context_markers" not in opts

    def test_update_init_options_writes_context_file_to_ext_config(self, tmp_path):
        from specify_cli import _update_init_options_for_integration

        # Pre-create the extension config so _update_init_options_for_integration
        # updates it (rather than skipping it when ext config doesn't exist yet).
        _write_ext_config(tmp_path, context_file="")
        i = _CtxIntegration()
        _update_init_options_for_integration(tmp_path, i, script_type="sh")
        # init-options.json must NOT have context_file or context_markers
        opts = load_init_options(tmp_path)
        assert "context_file" not in opts
        assert "context_markers" not in opts
        # Extension config must have them
        cfg = _load_agent_context_config(tmp_path)
        assert cfg["context_file"] == i.context_file
        assert "context_markers" in cfg

    def test_update_init_options_preserves_context_files(self, tmp_path):
        from specify_cli import _update_init_options_for_integration

        _write_ext_config(
            tmp_path,
            context_file="AGENTS.md",
            context_files=["AGENTS.md", "CLAUDE.md"],
        )
        i = _CtxIntegration()
        _update_init_options_for_integration(tmp_path, i, script_type="sh")
        cfg = _load_agent_context_config(tmp_path)
        assert cfg["context_file"] == i.context_file
        assert cfg["context_files"] == ["AGENTS.md", "CLAUDE.md"]

    def test_update_init_options_preserves_empty_context_files(self, tmp_path):
        from specify_cli import _update_init_options_for_integration

        _write_ext_config(
            tmp_path,
            context_file="AGENTS.md",
            context_files=[],
        )
        i = _CtxIntegration()
        _update_init_options_for_integration(tmp_path, i, script_type="sh")
        cfg = _load_agent_context_config(tmp_path)
        assert cfg["context_file"] == i.context_file
        assert cfg["context_files"] == []

    def test_update_init_options_normalizes_invalid_context_files(self, tmp_path):
        from specify_cli import _update_init_options_for_integration

        _write_ext_config(tmp_path, context_file="AGENTS.md")
        cfg = _load_agent_context_config(tmp_path)
        cfg["context_files"] = "AGENTS.md"
        _save_agent_context_config(tmp_path, cfg)

        i = _CtxIntegration()
        _update_init_options_for_integration(tmp_path, i, script_type="sh")
        cfg = _load_agent_context_config(tmp_path)
        assert cfg["context_file"] == i.context_file
        assert cfg["context_files"] == []

    def test_clear_init_options_clears_context_files(self, tmp_path):
        from specify_cli import _clear_init_options_for_integration

        save_init_options(
            tmp_path,
            {"integration": "claude", "ai": "claude"},
        )
        _write_ext_config(
            tmp_path,
            context_file="CLAUDE.md",
            context_files=["AGENTS.md", "CLAUDE.md"],
        )
        _clear_init_options_for_integration(tmp_path, "claude")
        cfg = _load_agent_context_config(tmp_path)
        assert cfg.get("context_file") == ""
        assert "context_files" not in cfg

    def test_update_init_options_preserves_custom_markers(self, tmp_path):
        from specify_cli import _update_init_options_for_integration

        _write_ext_config(
            tmp_path,
            context_file="",
            context_markers={"start": "<!-- B -->", "end": "<!-- E -->"},
        )
        i = _CtxIntegration()
        _update_init_options_for_integration(tmp_path, i)
        cfg = _load_agent_context_config(tmp_path)
        assert cfg["context_markers"] == {"start": "<!-- B -->", "end": "<!-- E -->"}

    def test_reinit_preserves_custom_markers(self, tmp_path):
        """specify init (reinit) must not overwrite user-customised markers."""
        from specify_cli import _update_agent_context_config_file

        # Simulate existing project with custom markers
        _write_ext_config(
            tmp_path,
            context_file="CLAUDE.md",
            context_markers={"start": "<!-- CUSTOM -->", "end": "<!-- /CUSTOM -->"},
        )
        # Re-running init updates context_file but must preserve markers
        _update_agent_context_config_file(
            tmp_path, "CLAUDE.md", preserve_markers=True
        )
        cfg = _load_agent_context_config(tmp_path)
        assert cfg["context_markers"] == {
            "start": "<!-- CUSTOM -->",
            "end": "<!-- /CUSTOM -->",
        }


# ── Deprecation warning on upsert ────────────────────────────────────────────


class TestDeprecationWarning:
    def test_upsert_emits_deprecation_warning(self, tmp_path, capsys):
        """upsert_context_section must emit a deprecation notice on stdout."""
        from tests.conftest import strip_ansi

        i = _CtxIntegration()
        _write_ext_config(tmp_path, context_file="CLAUDE.md")
        i.upsert_context_section(tmp_path)
        captured = capsys.readouterr()
        plain = strip_ansi(captured.out)
        assert "Deprecation" in plain
        assert "v0.12.0" in plain
        assert "agent-context" in plain

    def test_upsert_no_warning_when_disabled(self, tmp_path, capsys):
        """No deprecation warning when agent-context extension is disabled."""
        _write_registry(tmp_path, enabled=False)
        i = _CtxIntegration()
        i.upsert_context_section(tmp_path)
        captured = capsys.readouterr()
        assert "Deprecation" not in captured.out


# ── Corrupt / invalid extension config ───────────────────────────────────────


class TestCorruptExtensionConfig:
    def test_marker_resolution_with_corrupt_yaml(self, tmp_path):
        """Corrupt YAML in agent-context-config.yml falls back to defaults."""
        cfg_path = (
            tmp_path / ".specify" / "extensions" / "agent-context"
            / "agent-context-config.yml"
        )
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(": invalid: yaml: {{{\n", encoding="utf-8")
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == IntegrationBase.CONTEXT_MARKER_START
        assert end == IntegrationBase.CONTEXT_MARKER_END

    def test_upsert_with_corrupt_config_uses_defaults(self, tmp_path):
        """upsert_context_section still works when config YAML is corrupt."""
        cfg_path = (
            tmp_path / ".specify" / "extensions" / "agent-context"
            / "agent-context-config.yml"
        )
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text("not valid yaml: {{{\n", encoding="utf-8")
        i = _CtxIntegration()
        result = i.upsert_context_section(tmp_path)
        assert result is not None
        text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert IntegrationBase.CONTEXT_MARKER_START in text
        assert IntegrationBase.CONTEXT_MARKER_END in text

    def test_marker_resolution_with_non_dict_yaml(self, tmp_path):
        """Config file containing a scalar (not a dict) falls back to defaults."""
        cfg_path = (
            tmp_path / ".specify" / "extensions" / "agent-context"
            / "agent-context-config.yml"
        )
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text("just a string\n", encoding="utf-8")
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == IntegrationBase.CONTEXT_MARKER_START
        assert end == IntegrationBase.CONTEXT_MARKER_END
