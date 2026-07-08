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
    save_init_options,
)
from specify_cli.agents import CommandRegistrar
from tests.conftest import requires_bash


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "agent-context"
BASH = shutil.which("bash")
POWERSHELL = (
    shutil.which("pwsh") or shutil.which("powershell.exe") or shutil.which("powershell")
)


def _write_ext_config(project_root: Path, **overrides: object) -> None:
    """Write a minimal agent-context extension config directly.

    The CLI no longer owns the extension config — the bundled extension does —
    so tests write it themselves rather than going through any CLI helper.
    """
    cfg: dict = {
        "context_file": overrides.get("context_file", ""),
        "context_files": overrides.get("context_files", []),
        "context_markers": overrides.get(
            "context_markers",
            {
                "start": "<!-- SPECKIT START -->",
                "end": "<!-- SPECKIT END -->",
            },
        ),
    }
    path = (
        project_root
        / ".specify"
        / "extensions"
        / "agent-context"
        / "agent-context-config.yml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(cfg, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


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




def _install_agent_context_config(project_root: Path, **overrides: object) -> None:
    _write_ext_config(project_root, **overrides)
    # Mirror the real install layout: the extension ships its own
    # agent->context-file defaults map alongside the config. Self-seeding
    # tests depend on it, so require it to exist and always copy it rather
    # than silently skipping when it is missing.
    defaults_src = EXT_DIR / "agent-context-defaults.json"
    assert defaults_src.is_file(), (
        f"bundled agent-context defaults map missing: {defaults_src}"
    )
    defaults_dst = (
        project_root
        / ".specify"
        / "extensions"
        / "agent-context"
        / "agent-context-defaults.json"
    )
    defaults_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(defaults_src, defaults_dst)


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


# ── CLI does not resolve agent context placeholders ──────────────────────────


class TestSkillPlaceholderContextResolution:
    """The CLI no longer resolves any ``__CONTEXT_FILE__`` placeholder.

    Agent context files are owned entirely by the opt-in agent-context
    extension, so the CLI neither reads integration metadata nor the
    extension config when rendering commands/skills.
    """

    def test_cli_does_not_resolve_context_placeholder(self, tmp_path):
        content = CommandRegistrar.resolve_skill_placeholders(
            "codex",
            {},
            "Read __CONTEXT_FILE__",
            tmp_path,
        )
        assert content == "Read __CONTEXT_FILE__"

    def test_extension_config_does_not_influence_resolution(self, tmp_path):
        # Even a populated extension config must not influence resolution.
        _write_ext_config(
            tmp_path,
            context_file="FROM_CONFIG.md",
            context_files=["ALSO_CONFIG.md"],
        )

        content = CommandRegistrar.resolve_skill_placeholders(
            "claude",
            {},
            "Read __CONTEXT_FILE__",
            tmp_path,
        )
        assert "FROM_CONFIG.md" not in content
        assert "ALSO_CONFIG.md" not in content
        assert content == "Read __CONTEXT_FILE__"


# ── CLI no longer owns the agent-context extension config ────────────────────


class TestCliDoesNotManageExtensionConfig:
    """The Python codebase must not read or write the extension config."""

    def test_config_helpers_are_removed(self):
        import specify_cli

        for name in (
            "_load_agent_context_config",
            "_save_agent_context_config",
            "_update_agent_context_config_file",
            "_AGENT_CTX_EXT_CONFIG",
        ):
            assert not hasattr(specify_cli, name), name

    def test_no_agent_context_config_symbols_in_source(self):
        src = PROJECT_ROOT / "src" / "specify_cli"
        offenders = []
        for path in src.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "agent-context-config" in text or "agent_context_config" in text:
                offenders.append(str(path.relative_to(PROJECT_ROOT)))
        assert not offenders, offenders

    def test_update_init_options_does_not_create_ext_config(self, tmp_path):
        from specify_cli.integrations import INTEGRATION_REGISTRY
        from specify_cli.integrations._helpers import (
            _update_init_options_for_integration,
        )

        _update_init_options_for_integration(
            tmp_path, INTEGRATION_REGISTRY["claude"], script_type="sh"
        )

        cfg = (
            tmp_path
            / ".specify"
            / "extensions"
            / "agent-context"
            / "agent-context-config.yml"
        )
        assert not cfg.exists()

    def test_clear_init_options_does_not_create_ext_config(self, tmp_path):
        from specify_cli.integrations._helpers import (
            _clear_init_options_for_integration,
        )

        save_init_options(tmp_path, {"integration": "claude", "ai": "claude"})
        _clear_init_options_for_integration(tmp_path, "claude")

        cfg = (
            tmp_path
            / ".specify"
            / "extensions"
            / "agent-context"
            / "agent-context-config.yml"
        )
        assert not cfg.exists()


# ── Extension self-seeds its target from the active integration ──────────────


class TestExtensionSelfSeed:
    """When its own config declares no target, the bundled extension derives
    the context file from the active integration using its OWN bundled
    agent->context-file defaults map (no Specify CLI dependency)."""

    @requires_bash
    def test_bash_script_self_seeds_from_active_integration(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        # Config present but empty — no context_file / context_files.
        _install_agent_context_config(project, context_file="", context_files=[])
        # Active integration recorded in init-options.json (codex -> AGENTS.md).
        save_init_options(project, {"integration": "codex", "ai": "codex"})

        result = _run_bash_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        assert "agent-context: updated AGENTS.md" in (result.stderr + result.stdout)
        assert (project / "AGENTS.md").exists()
        assert "<!-- SPECKIT START -->" in (
            project / "AGENTS.md"
        ).read_text(encoding="utf-8")

    @requires_bash
    def test_bash_script_nothing_to_do_without_integration(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(project, context_file="", context_files=[])

        result = _run_bash_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        assert "nothing to do" in (result.stderr + result.stdout)


_MDC_CONTEXT_FILE = ".cursor/rules/specify-rules.mdc"


class TestPlanDiscovery:
    """Mtime fallback must find plans in nested spec layouts (#3024).

    Repos using SPECIFY_FEATURE_DIRECTORY place plans at
    ``specs/<scope>/<feature>/plan.md``; a one-level ``specs/*/plan.md``
    glob never matches those.
    """

    @staticmethod
    def _make_plans(project: Path) -> Path:
        # Older flat plan plus a newer nested plan: recursive discovery
        # must pick the nested one by mtime.
        flat = project / "specs" / "old-feature" / "plan.md"
        flat.parent.mkdir(parents=True)
        flat.write_text("flat plan\n", encoding="utf-8")
        os.utime(flat, (1_000_000_000, 1_000_000_000))
        nested = project / "specs" / "scope" / "new-feature" / "plan.md"
        nested.parent.mkdir(parents=True)
        nested.write_text("nested plan\n", encoding="utf-8")
        return nested

    @requires_bash
    def test_bash_script_finds_nested_plan(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(
            project,
            context_file="AGENTS.md",
            context_files=["AGENTS.md"],
        )
        self._make_plans(project)

        result = _run_bash_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        content = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "specs/scope/new-feature/plan.md" in content

    @pytest.mark.skipif(POWERSHELL is None, reason="PowerShell not available")
    def test_powershell_script_finds_nested_plan(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(
            project,
            context_file="AGENTS.md",
            context_files=["AGENTS.md"],
        )
        self._make_plans(project)

        result = _run_powershell_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        content = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "specs/scope/new-feature/plan.md" in content


class TestMdcFrontmatter:
    """Cursor-style ``.mdc`` targets must carry ``alwaysApply: true`` frontmatter
    so the rule file is auto-loaded; non-``.mdc`` targets must not gain any."""

    @requires_bash
    def test_bash_script_prepends_mdc_frontmatter(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(project, context_file=_MDC_CONTEXT_FILE)

        result = _run_bash_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        text = (project / _MDC_CONTEXT_FILE).read_text(encoding="utf-8")
        assert text.startswith("---\nalwaysApply: true\n---\n")
        assert "<!-- SPECKIT START -->" in text

    @requires_bash
    def test_bash_script_mdc_frontmatter_is_idempotent(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(project, context_file=_MDC_CONTEXT_FILE)

        _run_bash_agent_context_script(project)
        result = _run_bash_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        text = (project / _MDC_CONTEXT_FILE).read_text(encoding="utf-8")
        assert text.count("alwaysApply: true") == 1

    @requires_bash
    def test_bash_script_repairs_existing_mdc_frontmatter(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(project, context_file=_MDC_CONTEXT_FILE)
        target = project / _MDC_CONTEXT_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "---\ndescription: My rules\nalwaysApply: false\n---\n\nUser notes\n",
            encoding="utf-8",
        )

        result = _run_bash_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        text = target.read_text(encoding="utf-8")
        assert "alwaysApply: true" in text
        assert "alwaysApply: false" not in text
        assert "description: My rules" in text
        assert "User notes" in text

    @requires_bash
    def test_bash_script_skips_frontmatter_for_non_mdc(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(project, context_file="AGENTS.md")

        result = _run_bash_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        text = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "alwaysApply" not in text
        assert text.startswith("<!-- SPECKIT START -->")

    @pytest.mark.skipif(POWERSHELL is None, reason="PowerShell not available")
    def test_powershell_script_prepends_mdc_frontmatter(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(project, context_file=_MDC_CONTEXT_FILE)

        result = _run_powershell_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        text = (project / _MDC_CONTEXT_FILE).read_text(encoding="utf-8")
        assert text.startswith("---\nalwaysApply: true\n---\n")
        assert "<!-- SPECKIT START -->" in text

    @pytest.mark.skipif(POWERSHELL is None, reason="PowerShell not available")
    def test_powershell_script_repairs_existing_mdc_frontmatter(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(project, context_file=_MDC_CONTEXT_FILE)
        target = project / _MDC_CONTEXT_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "---\ndescription: My rules\nalwaysApply: false\n---\n\nUser notes\n",
            encoding="utf-8",
        )

        result = _run_powershell_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        text = target.read_text(encoding="utf-8")
        assert "alwaysApply: true" in text
        assert "alwaysApply: false" not in text
        assert "description: My rules" in text
        assert "User notes" in text

    @pytest.mark.skipif(POWERSHELL is None, reason="PowerShell not available")
    def test_powershell_script_skips_frontmatter_for_non_mdc(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        _install_agent_context_config(project, context_file="AGENTS.md")

        result = _run_powershell_agent_context_script(project)

        assert result.returncode == 0, result.stderr + result.stdout
        text = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "alwaysApply" not in text
        assert text.startswith("<!-- SPECKIT START -->")


_LEGACY_CONTEXT = (
    "# CLAUDE.md\n\n"
    "Some user notes.\n\n"
    "<!-- SPECKIT START -->\n"
    "Legacy managed section written by an older Spec Kit version.\n"
    "<!-- SPECKIT END -->\n\n"
    "More user notes.\n"
)


class TestBackwardCompatibility:
    """Legacy projects must keep working; the CLI never touches their artifacts."""

    def _seed_legacy_project(self, project_root: Path) -> Path:
        ctx = project_root / "CLAUDE.md"
        ctx.write_text(_LEGACY_CONTEXT, encoding="utf-8")
        _write_ext_config(project_root, context_file="CLAUDE.md")
        save_init_options(project_root, {"integration": "claude", "ai": "claude"})
        return ctx

    def test_integration_setup_leaves_legacy_artifacts_untouched(self, tmp_path):
        from specify_cli.integrations import INTEGRATION_REGISTRY
        from specify_cli.integrations.manifest import IntegrationManifest

        project = tmp_path / "legacy"
        project.mkdir()
        ctx = self._seed_legacy_project(project)
        cfg_path = (
            project / ".specify" / "extensions" / "agent-context"
            / "agent-context-config.yml"
        )
        before_ctx = ctx.read_text(encoding="utf-8")
        before_cfg = cfg_path.read_text(encoding="utf-8")

        integration = INTEGRATION_REGISTRY["claude"]
        m = IntegrationManifest("claude", project)
        integration.setup(project, m)

        assert ctx.read_text(encoding="utf-8") == before_ctx
        assert cfg_path.read_text(encoding="utf-8") == before_cfg

    def test_integration_switch_and_uninstall_leave_legacy_artifacts_untouched(
        self, tmp_path
    ):
        from specify_cli.integrations import INTEGRATION_REGISTRY
        from specify_cli.integrations._helpers import (
            _clear_init_options_for_integration,
            _update_init_options_for_integration,
        )

        project = tmp_path / "legacy"
        project.mkdir()
        ctx = self._seed_legacy_project(project)
        cfg_path = (
            project / ".specify" / "extensions" / "agent-context"
            / "agent-context-config.yml"
        )
        before_ctx = ctx.read_text(encoding="utf-8")
        before_cfg = cfg_path.read_text(encoding="utf-8")

        # Switch to a different integration.
        _update_init_options_for_integration(
            project, INTEGRATION_REGISTRY["gemini"], script_type="sh"
        )
        assert ctx.read_text(encoding="utf-8") == before_ctx
        assert cfg_path.read_text(encoding="utf-8") == before_cfg

        # Uninstall.
        _clear_init_options_for_integration(project, "gemini")
        assert ctx.read_text(encoding="utf-8") == before_ctx
        assert cfg_path.read_text(encoding="utf-8") == before_cfg
