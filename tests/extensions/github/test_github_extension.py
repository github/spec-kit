"""Tests for the bundled ``github`` extension (extensions/github/).

Validates:
- Bundled layout (manifest, README, command file, script twins)
- Catalog registration and wheel/source resolution via ``_locate_bundled_extension``
- Manifest validation, including that no alias claims the core command name
- Install/uninstall through ``ExtensionManager``
- Rendered command artifacts across command mode and skills mode, and in
  particular that ``{SCRIPT}`` resolves to a script the extension actually
  ships under ``.specify/extensions/github/scripts/`` rather than to core
- The ``before_taskstoissues`` / ``after_taskstoissues`` hook contract
- Behaviour of the bash and Python ``resolve-tasks`` twins
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml

from specify_cli import _locate_bundled_extension
from tests.conftest import requires_bash


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "github"
CORE_COMMAND = PROJECT_ROOT / "templates" / "commands" / "taskstoissues.md"

COMMAND_NAME = "speckit.github.taskstoissues"
COMMAND_FILE = EXT_DIR / "commands" / f"{COMMAND_NAME}.md"

# The three script twins, keyed by the frontmatter variant that selects them.
SCRIPT_TWINS = {
    "sh": "scripts/bash/resolve-tasks.sh",
    "ps": "scripts/powershell/resolve-tasks.ps1",
    "py": "scripts/python/resolve_tasks.py",
}


def _supported_agents() -> list[str]:
    """Every integration Spec Kit can register commands for."""
    from specify_cli.agents import CommandRegistrar

    return sorted(CommandRegistrar().AGENT_CONFIGS)


SUPPORTED_AGENTS = _supported_agents()


def _manifest_dict() -> dict:
    return yaml.safe_load((EXT_DIR / "extension.yml").read_text(encoding="utf-8"))


def _command_frontmatter() -> dict:
    from specify_cli.agents import CommandRegistrar

    frontmatter, _ = CommandRegistrar().parse_frontmatter(
        COMMAND_FILE.read_text(encoding="utf-8")
    )
    return frontmatter


# -- Bundled extension layout -------------------------------------------------


class TestExtensionLayout:
    def test_extension_yml_has_required_fields(self):
        manifest = _manifest_dict()
        assert manifest["extension"]["id"] == "github"
        assert manifest["extension"]["name"] == "GitHub Integration"
        assert manifest["extension"]["author"] == "spec-kit-core"
        # Install rejects a manifest without a requires block.
        assert manifest["requires"]["speckit_version"]
        commands = {c["name"] for c in manifest["provides"]["commands"]}
        assert commands == {COMMAND_NAME}

    def test_readme_exists(self):
        readme = EXT_DIR / "README.md"
        assert readme.is_file()
        assert "GitHub Integration Extension" in readme.read_text(encoding="utf-8")

    def test_readme_documents_migration_from_core(self):
        text = (EXT_DIR / "README.md").read_text(encoding="utf-8")
        assert "specify extension add github" in text
        assert "/speckit.taskstoissues" in text
        assert COMMAND_NAME in text

    def test_command_file_exists(self):
        assert COMMAND_FILE.is_file()

    @pytest.mark.parametrize("rel_path", sorted(SCRIPT_TWINS.values()))
    def test_script_twin_ships(self, rel_path: str):
        assert (EXT_DIR / rel_path).is_file(), f"Missing script: {rel_path}"


# -- Catalog registration and bundle resolution -------------------------------


class TestCatalogEntry:
    def test_catalog_lists_github_as_bundled(self):
        catalog = json.loads(
            (PROJECT_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8")
        )
        entry = catalog["extensions"]["github"]
        assert entry["bundled"] is True
        assert entry["id"] == "github"
        assert entry["author"] == "spec-kit-core"

    def test_locate_bundled_extension_finds_github(self):
        located = _locate_bundled_extension("github")
        assert located is not None
        assert (located / "extension.yml").is_file()

    def test_pyproject_bundles_the_extension_into_the_wheel(self):
        pyproject = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        force_include = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"][
            "force-include"
        ]
        assert (
            force_include["extensions/github"]
            == "specify_cli/core_pack/extensions/github"
        )


# -- Manifest validation ------------------------------------------------------


class TestManifest:
    def test_manifest_validates(self):
        from specify_cli.extensions import ExtensionManifest

        m = ExtensionManifest(EXT_DIR / "extension.yml")
        assert m.id == "github"
        assert m.version == "1.0.0"
        assert [c["name"] for c in m.commands] == [COMMAND_NAME]

    def test_manifest_command_files_exist(self):
        from specify_cli.extensions import ExtensionManifest

        m = ExtensionManifest(EXT_DIR / "extension.yml")
        for cmd in m.commands:
            assert (EXT_DIR / cmd["file"]).is_file()

    def test_no_alias_claims_the_core_command(self):
        """Stage 1 keeps the core command; nothing here may shadow it.

        Alias names are not pattern-checked and the core-namespace guard
        applies to primary names only, so this is author discipline that a
        test has to hold in place.
        """
        from specify_cli.extensions import ExtensionManifest

        m = ExtensionManifest(EXT_DIR / "extension.yml")
        aliases = [a for cmd in m.commands for a in cmd.get("aliases", []) or []]
        assert aliases == []

    def test_core_command_remains_unchanged(self):
        """Stage 1 is additive: the core command still ships."""
        assert CORE_COMMAND.is_file()


# -- Install / uninstall ------------------------------------------------------


class TestExtensionInstall:
    def test_install_copies_command_and_scripts(self, tmp_path: Path):
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manifest = manager.install_from_directory(
            EXT_DIR, "0.9.0", register_commands=False
        )

        assert manifest.id == "github"
        assert manager.registry.is_installed("github")
        assert {c["name"] for c in manifest.commands} == {COMMAND_NAME}

        installed = tmp_path / ".specify" / "extensions" / "github"
        assert (installed / "commands" / f"{COMMAND_NAME}.md").is_file()
        for rel_path in SCRIPT_TWINS.values():
            assert (installed / rel_path).is_file(), f"Missing script: {rel_path}"

    def test_remove_uninstalls_cleanly(self, tmp_path: Path):
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manager.install_from_directory(EXT_DIR, "0.9.0", register_commands=False)

        assert manager.remove("github") is True
        assert not manager.registry.is_installed("github")
        assert not (tmp_path / ".specify" / "extensions" / "github").exists()


# -- Rendered command artifacts -----------------------------------------------


class TestScriptPathResolution:
    def test_frontmatter_uses_plain_extension_local_spelling(self):
        """No ``../../`` escape hatch back into core scripts."""
        scripts = _command_frontmatter()["scripts"]
        assert set(scripts) == set(SCRIPT_TWINS)
        for variant, rel_path in SCRIPT_TWINS.items():
            assert scripts[variant].startswith(rel_path), scripts[variant]
            assert ".." not in scripts[variant]

    def test_adjusted_paths_resolve_under_the_installed_extension(self):
        from specify_cli.agents import CommandRegistrar

        adjusted = CommandRegistrar()._adjust_script_paths(
            _command_frontmatter(), extension_id="github"
        )["scripts"]

        for variant, rel_path in SCRIPT_TWINS.items():
            assert adjusted[variant].startswith(
                f".specify/extensions/github/{rel_path}"
            ), adjusted[variant]

    @pytest.mark.parametrize("variant,rel_path", sorted(SCRIPT_TWINS.items()))
    def test_rendered_command_points_at_a_script_that_ships(
        self, tmp_path: Path, variant: str, rel_path: str
    ):
        """End to end: install, render, and confirm the path exists on disk.

        A verbatim copy of the core command renders an extension-local path
        for core's ``check-prerequisites``, installs happily, and only fails
        when a user runs it. This pins the working spelling.
        """
        from specify_cli.extensions import CommandRegistrar, ExtensionManager

        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)
        (project / ".specify" / "init-options.json").write_text(
            json.dumps({"ai": "copilot", "script": variant}), encoding="utf-8"
        )
        (project / ".github" / "agents").mkdir(parents=True)

        manager = ExtensionManager(project)
        manifest = manager.install_from_directory(
            EXT_DIR, "0.9.0", register_commands=False
        )
        extension_dir = project / ".specify" / "extensions" / "github"

        CommandRegistrar().register_commands_for_agent(
            "copilot", manifest, extension_dir, project
        )

        rendered = project / ".github" / "agents" / f"{COMMAND_NAME}.agent.md"
        assert rendered.is_file()
        content = rendered.read_text(encoding="utf-8")

        assert "{SCRIPT}" not in content
        expected = f".specify/extensions/github/{rel_path}"
        assert expected in content
        # The rendered path must resolve to a file the extension ships.
        assert (project / expected).is_file()
        # And it must not have been rewritten into the core script tree.
        assert ".specify/scripts/" not in content

    @pytest.mark.parametrize("agent", SUPPORTED_AGENTS)
    def test_every_supported_integration_renders_the_command(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, agent: str
    ):
        """Acceptance criterion: the command works for *every* integration.

        Covers both layouts in one sweep — command-file agents, skills-mode
        agents, and Hermes, which installs to ``~/.hermes/skills`` rather than
        a project-local directory (hence the redirected home).
        """
        from specify_cli.extensions import CommandRegistrar, ExtensionManager

        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("USERPROFILE", str(home))

        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)
        (project / ".specify" / "init-options.json").write_text(
            json.dumps({"ai": agent, "script": "sh"}), encoding="utf-8"
        )

        manager = ExtensionManager(project)
        manifest = manager.install_from_directory(
            EXT_DIR, "0.9.0", register_commands=False
        )
        CommandRegistrar().register_commands_for_agent(
            agent, manifest, project / ".specify" / "extensions" / "github", project
        )

        installed = project / ".specify" / "extensions"
        artifacts = [
            p
            for root in (project, home)
            for p in root.rglob("*")
            if p.is_file()
            and installed not in p.parents
            and "taskstoissues" in p.as_posix().lower()
        ]
        assert artifacts, f"{agent} produced no command artifact"

        expected = f".specify/extensions/github/{SCRIPT_TWINS['sh']}"
        bodies = [p.read_text(encoding="utf-8") for p in artifacts]

        # No artifact may leak an unresolved placeholder...
        for artifact, content in zip(artifacts, bodies):
            assert "{SCRIPT}" not in content, artifact
        # ...and the command body must carry the resolved extension-local path.
        # Some integrations also emit a thin companion file (e.g. Copilot's
        # prompt shim, which only points at the agent), so this is "at least
        # one" rather than "all".
        assert any(expected in content for content in bodies), (
            f"{agent}: no artifact references {expected} "
            f"(wrote {[p.name for p in artifacts]})"
        )

    def test_rendered_skill_points_at_a_script_that_ships(self, tmp_path: Path):
        """Skills-mode layouts resolve ``{SCRIPT}`` the same way."""
        from specify_cli.extensions import CommandRegistrar, ExtensionManager

        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)
        (project / ".specify" / "init-options.json").write_text(
            json.dumps({"ai": "codex", "ai_skills": True, "script": "sh"}),
            encoding="utf-8",
        )
        (project / ".agents" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project)
        manifest = manager.install_from_directory(
            EXT_DIR, "0.9.0", register_commands=False
        )
        extension_dir = project / ".specify" / "extensions" / "github"

        CommandRegistrar().register_commands_for_agent(
            "codex", manifest, extension_dir, project
        )

        skill = (
            project / ".agents" / "skills" / "speckit-github-taskstoissues" / "SKILL.md"
        )
        assert skill.is_file()
        content = skill.read_text(encoding="utf-8")

        assert "{SCRIPT}" not in content
        expected = f".specify/extensions/github/{SCRIPT_TWINS['sh']}"
        assert expected in content
        assert (project / expected).is_file()


# -- Behaviour parity with the core command -----------------------------------


class TestCommandBody:
    def test_preserves_the_hook_contract(self):
        """The hook keys are literal strings read out of extensions.yml."""
        body = COMMAND_FILE.read_text(encoding="utf-8")
        assert "hooks.before_taskstoissues" in body
        assert "hooks.after_taskstoissues" in body

    def test_git_extension_hooks_still_target_those_keys(self):
        """The live consumers of the hook contract keep firing."""
        git_manifest = yaml.safe_load(
            (PROJECT_ROOT / "extensions" / "git" / "extension.yml").read_text(
                encoding="utf-8"
            )
        )
        hooks = git_manifest["hooks"]
        assert "before_taskstoissues" in hooks
        assert "after_taskstoissues" in hooks

    def test_declares_the_github_mcp_tools(self):
        tools = _command_frontmatter()["tools"]
        assert "github/github-mcp-server/list_issues" in tools
        assert "github/github-mcp-server/issue_write" in tools

    def test_preserves_remote_validation(self):
        body = COMMAND_FILE.read_text(encoding="utf-8")
        assert "git config --get remote.origin.url" in body
        assert "ONLY PROCEED TO NEXT STEPS IF THE REMOTE IS A GITHUB URL" in body
        assert (
            "UNDER NO CIRCUMSTANCES EVER CREATE ISSUES IN REPOSITORIES THAT DO NOT "
            "MATCH THE REMOTE URL" in body
        )

    def test_readme_lists_every_dollar_skills_agent(self):
        """The invocation guide must name all `$speckit-` agents, not some.

        Regression: Command Code was omitted, so its users were pointed at a
        syntax their agent does not use.
        """
        from specify_cli._invocation_style import DOLLAR_SKILLS_AGENTS

        readme = (EXT_DIR / "README.md").read_text(encoding="utf-8")
        note = next(
            line for line in readme.splitlines() if "$speckit-github-taskstoissues" in line
        )

        display_names = {
            "codex": "Codex",
            "zcode": "ZCode",
            "command-code": "Command Code",
        }
        # If a new dollar-skills agent appears, this fails until it is named.
        assert set(display_names) == set(DOLLAR_SKILLS_AGENTS), (
            "DOLLAR_SKILLS_AGENTS changed; update the README invocation note "
            f"and this mapping: {sorted(DOLLAR_SKILLS_AGENTS)}"
        )
        for agent, display in display_names.items():
            assert display in note, f"README omits {display} ({agent}): {note}"

    def test_preserves_deduplication_and_pagination(self):
        body = COMMAND_FILE.read_text(encoding="utf-8")
        assert "list_issues" in body
        # Both open and closed issues: the tool returns both when `state` is omitted.
        assert "Do not pass a `state` value" in body
        # Cursor-based pagination, and the early exit that bounds the call count.
        assert "perPage: 100" in body
        assert "`after` parameter" in body
        assert "endCursor" in body
        assert "Stop paginating as soon as every task ID has been matched" in body
        # Four-digit and longer task IDs must still match.
        assert r"\bT\d{3,}\b" in body

    def test_body_differs_from_core_only_in_the_script_invocation(self):
        """Behaviour parity, enforced as a diff rather than as spot checks.

        Everything except the ``scripts:`` frontmatter and the two lines that
        read the new ``TASKS`` value must match the core command verbatim, so
        the two cannot silently drift while both exist.
        """
        import difflib

        core = CORE_COMMAND.read_text(encoding="utf-8").splitlines()
        ext = COMMAND_FILE.read_text(encoding="utf-8").splitlines()
        changed = [
            line
            for line in difflib.unified_diff(core, ext, n=0)
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        ]

        # 3 script lines + 2 outline lines, each as one removal and one addition.
        assert len(changed) == 10, "\n".join(changed)

        markers = (
            "check-prerequisites",
            "check_prerequisites",
            "resolve-tasks",
            "resolve_tasks",
            "AVAILABLE_DOCS",
            "path to **tasks**",
        )
        assert all(
            any(marker in line for marker in markers) for line in changed
        ), "\n".join(changed)

    def test_uses_the_portable_command_reference_token(self):
        """A literal invocation would be correct for exactly one agent."""
        body = COMMAND_FILE.read_text(encoding="utf-8")
        assert "__SPECKIT_COMMAND_CONVERGE__" in body


# -- resolve-tasks script twins -----------------------------------------------

PY_SCRIPT = EXT_DIR / SCRIPT_TWINS["py"]
SH_SCRIPT = EXT_DIR / SCRIPT_TWINS["sh"]


def _make_feature_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    feature = project / "specs" / "001-demo"
    feature.mkdir(parents=True)
    (project / ".specify").mkdir(exist_ok=True)
    (project / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": "specs/001-demo"}), encoding="utf-8"
    )
    (feature / "tasks.md").write_text(
        "- [ ] T001 Create project structure\n", encoding="utf-8"
    )
    (feature / "research.md").write_text("# Research\n", encoding="utf-8")
    return project


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


class TestResolveTasksPython:
    def test_reports_feature_dir_tasks_and_docs(self, tmp_path: Path):
        project = _make_feature_project(tmp_path)
        result = _run([sys.executable, str(PY_SCRIPT), "--json"], project)

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert Path(payload["FEATURE_DIR"]) == project / "specs" / "001-demo"
        assert Path(payload["TASKS"]) == project / "specs" / "001-demo" / "tasks.md"
        assert payload["AVAILABLE_DOCS"] == ["research.md", "tasks.md"]

    def test_errors_when_tasks_md_is_missing(self, tmp_path: Path):
        project = _make_feature_project(tmp_path)
        (project / "specs" / "001-demo" / "tasks.md").unlink()

        result = _run([sys.executable, str(PY_SCRIPT), "--json"], project)

        assert result.returncode == 1
        assert "tasks.md not found" in result.stderr

    def test_text_mode_survives_a_cp1252_stdout(self, tmp_path: Path):
        """Regression: U+2713 is unencodable in cp1252.

        On Windows stdout falls back to the ANSI code page whenever it is not
        a console — a pipe or a redirect, which is exactly how agents invoke
        these scripts — so printing the glyph raised UnicodeEncodeError and
        aborted the report right after ``AVAILABLE_DOCS:``.
        """
        project = _make_feature_project(tmp_path)
        env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
        result = subprocess.run(
            [sys.executable, str(PY_SCRIPT)],
            cwd=project,
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, result.stderr
        assert "UnicodeEncodeError" not in result.stderr
        # The docs section must be complete, not truncated at the first marker.
        assert "AVAILABLE_DOCS:" in result.stdout
        assert "research.md" in result.stdout
        assert "tasks.md" in result.stdout
        # ASCII fallback, matching core and the PowerShell twin.
        assert "[OK] tasks.md" in result.stdout

    def test_text_mode_uses_the_glyph_when_stdout_can_encode_it(
        self, tmp_path: Path
    ):
        project = _make_feature_project(tmp_path)
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            [sys.executable, str(PY_SCRIPT)],
            cwd=project,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )

        assert result.returncode == 0, result.stderr
        assert "✓ tasks.md" in result.stdout

    def test_does_not_write_feature_json(self, tmp_path: Path):
        """Resolution is read-only; it must not dirty the working tree."""
        project = _make_feature_project(tmp_path)
        feature_json = project / ".specify" / "feature.json"
        before = feature_json.read_bytes()

        result = _run([sys.executable, str(PY_SCRIPT), "--json"], project)

        assert result.returncode == 0, result.stderr
        assert feature_json.read_bytes() == before


@requires_bash
class TestResolveTasksBashJsonEscape:
    """``json_escape`` must emit valid JSON, matching core's implementation.

    Regression: the escape table silently lost a level of backslash quoting,
    so backslashes passed through unescaped and ``\\n``/``\\t`` collapsed to
    the bare letters ``n``/``t``. A Windows feature path would have produced
    invalid JSON that the agent then failed to parse.
    """

    CASES = {
        "backslash": "a\\b",
        "windows_path": "C:\\Users\\dev\\specs",
        "quote": 'a"b',
        "newline": "a\nb",
        "tab": "a\tb",
        "carriage_return": "a\rb",
        "control": "a\x01b",
    }

    @staticmethod
    def _escape(script: Path, tmp_path: Path, value: str) -> str:
        """Run the script's own ``json_escape`` over *value*, byte-exactly."""
        import re

        body = re.search(
            r"(json_escape\(\) \{.*?\n\})",
            script.read_text(encoding="utf-8"),
            re.S,
        )
        assert body, f"no json_escape found in {script}"

        # Callers pass a per-script subdirectory so the two harnesses do not
        # collide; pytest only creates tmp_path itself.
        tmp_path.mkdir(parents=True, exist_ok=True)
        payload = tmp_path / "value.txt"
        payload.write_text(value, encoding="utf-8", newline="")
        harness = tmp_path / "harness.sh"
        # Read the raw value from a file so the harness itself needs no quoting.
        harness.write_text(
            body.group(1) + '\nvalue="$(cat "$1")"\njson_escape "$value"\n',
            encoding="utf-8",
            newline="\n",
        )
        return subprocess.run(
            ["bash", str(harness), str(payload)],
            capture_output=True,
            check=True,
        ).stdout.decode("utf-8")

    @pytest.mark.parametrize("name", sorted(CASES))
    def test_escaping_round_trips_through_json(self, tmp_path: Path, name: str):
        value = self.CASES[name]
        escaped = self._escape(SH_SCRIPT, tmp_path, value)

        # The escaped text must be a valid JSON string body that decodes back
        # to exactly what went in.
        assert json.loads(f'"{escaped}"') == value, escaped

    @pytest.mark.parametrize("name", sorted(CASES))
    def test_matches_core_json_escape(self, tmp_path: Path, name: str):
        """Kept in step with core rather than diverging quietly."""
        core_common = PROJECT_ROOT / "scripts" / "bash" / "common.sh"
        value = self.CASES[name]

        ours = self._escape(SH_SCRIPT, tmp_path / "ours", value)
        theirs = self._escape(core_common, tmp_path / "theirs", value)

        assert ours == theirs

    def test_json_output_parses_for_a_path_with_a_backslash(self, tmp_path: Path):
        """End to end: a feature directory containing a backslash.

        POSIX allows a backslash in a filename, so this exercises the real
        emit path rather than the helper in isolation.
        """
        project = _make_feature_project(tmp_path)
        odd = project / "specs" / "we\\ird"
        try:
            odd.mkdir()
        except OSError:
            pytest.skip("filesystem rejects backslash in a path component")
        (odd / "tasks.md").write_text("- [ ] T001 x\n", encoding="utf-8")
        (project / ".specify" / "feature.json").write_text(
            json.dumps({"feature_directory": "specs/we\\ird"}), encoding="utf-8"
        )

        result = _run(["bash", str(SH_SCRIPT), "--json"], project)

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)  # would raise on invalid escaping
        assert payload["FEATURE_DIR"].endswith("we\\ird")


@requires_bash
class TestResolveTasksBash:
    def test_matches_the_python_twin(self, tmp_path: Path):
        project = _make_feature_project(tmp_path)

        bash_result = _run(["bash", str(SH_SCRIPT), "--json"], project)
        py_result = _run([sys.executable, str(PY_SCRIPT), "--json"], project)

        assert bash_result.returncode == 0, bash_result.stderr
        assert py_result.returncode == 0, py_result.stderr

        bash_payload = json.loads(bash_result.stdout)
        py_payload = json.loads(py_result.stdout)
        assert bash_payload["AVAILABLE_DOCS"] == py_payload["AVAILABLE_DOCS"]
        assert Path(bash_payload["FEATURE_DIR"]).name == Path(
            py_payload["FEATURE_DIR"]
        ).name
        assert Path(bash_payload["TASKS"]).name == Path(py_payload["TASKS"]).name

    def test_errors_when_tasks_md_is_missing(self, tmp_path: Path):
        project = _make_feature_project(tmp_path)
        (project / "specs" / "001-demo" / "tasks.md").unlink()

        result = _run(["bash", str(SH_SCRIPT), "--json"], project)

        assert result.returncode == 1
        assert "tasks.md not found" in result.stderr
