"""Tests for the ``specify init`` command adapter.

`command_init.py` interpolated the project name, `--integration`/`--script`
values and paths straight into Rich markup f-strings. A name containing a
tag-shaped bracket run was therefore consumed as markup:

* ``specify init "proj [v2]"`` succeeded and created the directory, but the
  Next Steps panel printed ``cd proj`` -- a command that fails when pasted.
* ``specify init "app[/red]x"`` created the directory and then died with
  ``MarkupError``, so the user saw a traceback for a project that had in fact
  been scaffolded.

Every sibling CLI module (extensions, presets, workflows, integrations) already
escapes user-controlled display values; init.py was the outlier.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.command_init import _shell_quote_arg
from tests.conftest import requires_bash

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def test_command_init_importable():
    mod = importlib.import_module("specify_cli.command_init")
    assert hasattr(mod, "register")
    assert callable(mod.register)


def test_transitional_commands_package_removed():
    import specify_cli

    package_root = Path(specify_cli.__file__).parent
    assert not (package_root / "commands" / "__init__.py").exists()
    assert not (package_root / "commands" / "init.py").exists()


def test_init_command_registered():
    callback_names = [
        cmd.callback.__name__ for cmd in app.registered_commands if cmd.callback
    ]
    assert callback_names == ["init", "check", "version", "mcp"]


def test_init_has_win32_guard():
    """init.py must assign _transient from platform check and pass it to Live."""
    import specify_cli

    init_src = Path(specify_cli.__file__).parent / "command_init.py"
    content = init_src.read_text(encoding="utf-8")
    guard = (
        r"_transient\s*=\s*sys\.platform\s*!=\s*['\"]win32['\"].*"
        r"Live\(.*transient\s*=\s*_transient"
    )
    assert re.search(guard, content, re.DOTALL)


def _strip(text: str) -> str:
    return _ANSI.sub("", text or "")


def _init(tmp_path: Path, name: str):
    """Run a fully offline, non-interactive `specify init <name>`."""
    previous = os.getcwd()
    os.chdir(tmp_path)
    try:
        return CliRunner().invoke(
            app,
            [
                "init",
                name,
                "--integration",
                "generic",
                "--integration-options",
                "--commands-dir .agent/commands",
                "--ignore-agent-tools",
                "--offline",
            ],
            catch_exceptions=True,
        )
    finally:
        os.chdir(previous)


@pytest.mark.parametrize("numbering", ["timestamp", "sequential", None])
def test_reinit_preserves_feature_numbering(tmp_path: Path, monkeypatch, numbering):
    result = _init(tmp_path, "proj")
    assert result.exit_code == 0, _strip(result.stdout)
    project = tmp_path / "proj"
    options_path = project / ".specify" / "init-options.json"
    options = json.loads(options_path.read_text(encoding="utf-8"))
    assert options["feature_numbering"] == "sequential"
    if numbering is None:
        options.pop("feature_numbering")
    else:
        options["feature_numbering"] = numbering
    options["custom_setting"] = "keep me"
    options_path.write_text(json.dumps(options), encoding="utf-8")

    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, [
        "init", "--here", "--force", "--integration", "generic",
        "--integration-options", "--commands-dir .agent/commands",
        "--script", "sh", "--non-interactive", "--ignore-agent-tools", "--offline",
    ])
    assert result.exit_code == 0, _strip(result.stdout)
    updated = json.loads(options_path.read_text(encoding="utf-8"))
    assert updated["feature_numbering"] == (numbering or "sequential")
    assert updated["custom_setting"] == "keep me"
    assert updated["here"] is True


@pytest.mark.parametrize("name", ["proj [v2]", "my[bold]app"])
def test_next_steps_cd_shows_the_real_project_name(tmp_path: Path, name: str):
    """The `cd` line must name the directory that was actually created."""
    result = _init(tmp_path, name)
    assert result.exit_code == 0, _strip(result.stdout)
    assert (tmp_path / name).is_dir()

    out = _strip(result.stdout)
    cd_lines = [line for line in out.splitlines() if "cd " in line]
    assert cd_lines, out
    assert f"cd {_shell_quote_arg(name)}" in " ".join(cd_lines), cd_lines


def test_closing_tag_in_project_name_does_not_crash(tmp_path: Path):
    """A name forming a closing tag raised MarkupError *after* the project had
    been created, so init reported failure for work it had completed."""
    name = "app[/red]x"
    result = _init(tmp_path, name)

    assert result.exception is None or not isinstance(
        result.exception, Exception
    ) or "MarkupError" not in type(result.exception).__name__, (
        f"unexpected {type(result.exception).__name__}: {result.exception}"
    )
    assert result.exit_code == 0, _strip(result.stdout)
    assert (tmp_path / name).is_dir()
    assert f"cd {_shell_quote_arg(name)}" in _strip(result.stdout)


def test_invalid_integration_value_is_rendered_literally(tmp_path: Path):
    """An invalid `--integration` value is echoed back; it must not be parsed as
    markup (nor raise) when it contains a bracket run."""
    previous = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = CliRunner().invoke(
            app,
            ["init", "proj", "--integration", "nope[/red]", "--ignore-agent-tools"],
            catch_exceptions=True,
        )
    finally:
        os.chdir(previous)

    assert result.exit_code != 0
    assert "nope[/red]" in _strip(result.stdout)


def _cd_argument(stdout: str) -> str:
    """Return the argument of the printed `cd` command, verbatim.

    The line is rendered inside a Rich panel, so the trailing box-drawing
    border and its padding are stripped before the argument is compared.
    """
    marker = "Go to the project folder: cd "
    for line in _strip(stdout).splitlines():
        if marker in line:
            return line.split(marker, 1)[1].rstrip().rstrip("│").rstrip()
    raise AssertionError(f"no cd line in output:\n{stdout}")


@pytest.mark.parametrize("name", ["proj v2", "my project"])
def test_cd_line_quotes_a_name_containing_whitespace(tmp_path: Path, name: str):
    """Rich-escaping alone left `cd proj v2`, which every shell reads as two
    arguments, so the copy-pasted command did not enter the directory."""
    result = _init(tmp_path, name)
    assert result.exit_code == 0, _strip(result.stdout)
    assert (tmp_path / name).is_dir()

    printed = _cd_argument(result.stdout)
    assert printed != name, "a whitespace-bearing name must be quoted"
    assert name in printed, printed
    assert printed == _shell_quote_arg(name)


def test_ordinary_name_is_not_quoted(tmp_path: Path):
    """The common case must stay byte-identical: no gratuitous quoting."""
    result = _init(tmp_path, "my-project")
    assert result.exit_code == 0, _strip(result.stdout)
    assert _cd_argument(result.stdout) == "my-project"


@requires_bash
@pytest.mark.parametrize("name", ["proj v2", "proj [v2]", "my-project"])
def test_printed_cd_command_actually_changes_directory(tmp_path: Path, name: str):
    """Execute the printed command rather than only inspecting it.

    This is the assertion the string comparisons cannot make: the rendered
    `cd <arg>` is fed to a real shell and must land in the created directory.
    """
    result = _init(tmp_path, name)
    assert result.exit_code == 0, _strip(result.stdout)
    target = tmp_path / name
    assert target.is_dir()

    printed = _cd_argument(result.stdout)
    proc = subprocess.run(
        ["bash", "-c", f"cd {printed} && pwd"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"cd {printed!r} failed: {proc.stderr}"
    assert Path(proc.stdout.strip()).name == name, proc.stdout


def test_shell_quote_arg_is_host_appropriate():
    """The helper follows `_version._render_argv`: list2cmdline on Windows,
    shlex.quote elsewhere. Names needing no quoting round-trip unchanged."""
    assert _shell_quote_arg("my-project") == "my-project"
    quoted = _shell_quote_arg("my project")
    assert quoted != "my project"
    if os.name == "nt":
        assert quoted == '"my project"'
    else:
        assert quoted == "'my project'"


@pytest.mark.parametrize("here", [False, True])
def test_output_free_init_recommends_switching_integrations(tmp_path, monkeypatch, here):
    from specify_cli.integrations.generic import GenericIntegration

    monkeypatch.setattr(GenericIntegration, "list_command_templates", lambda self: [])
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "init", *(["--here"] if here else ["proj"]),
            "--integration", "generic",
            "--integration-options", "--commands-dir .agent/commands",
            "--ignore-agent-tools",
        ],
    )
    assert result.exit_code == 0, result.output
    output = _strip(result.output)
    assert "Next Steps" in output
    if here:
        assert "You're already in the project directory!" in output
    else:
        assert "cd proj" in output
    assert "specify integration switch <key>" in output
    assert "Switch this project to it:" in output
    assert "Add it to this project:" not in output
    assert "specify integration list" in output
    assert "Start using" not in output
    assert "speckit." not in output
    assert "Enhancement Commands" not in output
    assert "Enhancement Skills" not in output
    project = tmp_path if here else tmp_path / "proj"
    assert not (project / ".agent" / "commands").exists()


def test_rendering_init_preserves_command_guidance(tmp_path):
    result = _init(tmp_path, "proj")
    assert result.exit_code == 0, result.output
    output = _strip(result.output)
    assert "Start using slash commands" in output
    for command in ("constitution", "specify", "plan", "tasks", "implement", "converge",
                    "clarify", "analyze", "checklist"):
        assert f"/speckit.{command}" in output
        assert (tmp_path / "proj" / ".agent" / "commands" / f"speckit.{command}.md").is_file()
    assert "Enhancement Commands" in output
    assert "specify integration switch <key>" not in output


def test_rendering_init_preserves_skill_guidance(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app, ["init", "proj", "--integration", "copilot", "--ignore-agent-tools"],
    )
    assert result.exit_code == 0, result.output
    output = _strip(result.output)
    assert "Start using skills" in output
    assert "Enhancement Skills" in output
    assert "specify integration switch <key>" not in output
    for command in ("constitution", "specify", "plan", "tasks", "implement", "converge",
                    "clarify", "analyze", "checklist"):
        assert f"/speckit-{command}" in output
        assert (tmp_path / "proj" / ".github" / "skills" / f"speckit-{command}" / "SKILL.md").is_file()


def test_init_force_syncs_manifest_hash_for_preset_override(tmp_path, monkeypatch):
    """Re-init must record preset bytes and retain setup's other files (#5078)."""
    from specify_cli.integrations.manifest import IntegrationManifest

    monkeypatch.chdir(tmp_path)
    args = ["--integration", "codex", "--script", "sh", "--ignore-agent-tools", "--non-interactive"]
    result = CliRunner().invoke(app, ["init", "proj", *args])
    assert result.exit_code == 0, result.output
    project = tmp_path / "proj"
    preset = tmp_path / "tasks-preset"
    (preset / "commands").mkdir(parents=True)
    (preset / "commands/speckit.tasks.md").write_bytes(
        b"---\ndescription: Tasks override\n---\nPreset tasks body\n"
    )
    (preset / "preset.yml").write_bytes(b"""schema_version: '1.0'
preset: {id: tasks-preset, name: Tasks Preset, version: 1.0.0, description: x}
requires: {speckit_version: '>=0.1.0'}
provides:
  templates:
  - {type: command, name: speckit.tasks, file: commands/speckit.tasks.md}
""")
    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, ["preset", "add", "--dev", str(preset)])
    assert result.exit_code == 0, result.output
    plan_rel = ".agents/skills/speckit-plan/SKILL.md"
    original_plan = (project / plan_rel).read_bytes()
    (project / plan_rel).write_bytes(b"User-edited skill\n")

    result = CliRunner().invoke(app, ["init", "--here", "--force", *args])
    assert result.exit_code == 0, result.output

    manifest = IntegrationManifest.load("codex", project)
    rel = ".agents/skills/speckit-tasks/SKILL.md"
    content = (project / rel).read_bytes()
    assert b"Preset tasks body" in content
    assert manifest.files[rel] == hashlib.sha256(content).hexdigest(), (
        "manifest hash must match the preset-overridden skill (#5078)"
    )
    assert (project / plan_rel).read_bytes() == original_plan, "force re-init still replaces user edits"
    assert manifest.files[plan_rel] == hashlib.sha256(original_plan).hexdigest()
    result = CliRunner().invoke(app, ["integration", "status", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["modified_managed_files"] == 0
    result = CliRunner().invoke(app, ["integration", "upgrade", "codex", "--script", "sh"])
    assert result.exit_code == 0, result.output


def test_init_force_keeps_recovered_markers(tmp_path, monkeypatch):
    """Re-init resync must not re-record files registration left unchanged (#5078)."""
    from specify_cli.integrations import get_integration
    from specify_cli.integrations.manifest import IntegrationManifest

    monkeypatch.chdir(tmp_path)
    args = ["--integration", "codex", "--script", "sh", "--ignore-agent-tools", "--non-interactive"]
    result = CliRunner().invoke(app, ["init", "proj", *args])
    assert result.exit_code == 0, result.output
    project = tmp_path / "proj"
    integration_class = type(get_integration("codex"))
    original_setup = integration_class.setup
    rel = ".agents/skills/speckit-plan/SKILL.md"

    def setup_with_recovered_file(self, project_root, manifest, *args, **kwargs):
        created = original_setup(self, project_root, manifest, *args, **kwargs)
        manifest.record_existing(rel, recovered=True)
        return created

    monkeypatch.setattr(integration_class, "setup", setup_with_recovered_file)
    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, ["init", "--here", "--force", *args])

    assert result.exit_code == 0, result.output
    assert IntegrationManifest.load("codex", project).is_recovered(rel)


def test_init_force_registers_extensions_as_skills_in_skills_mode(tmp_path, monkeypatch):
    """Force re-init into a skills-mode agent must register extensions as skills (#5321).

    The force re-registration reads the saved ai / ai_skills init options to
    decide skill vs command rendering. Before the fix it ran before those
    options were saved, so a skills-mode re-init wrote command files for the
    extension instead of SKILL.md files.
    """
    from specify_cli.extensions import ExtensionManager

    result = _init(tmp_path, "proj")
    assert result.exit_code == 0, _strip(result.stdout)
    project = tmp_path / "proj"

    ext_dir = tmp_path / "test-ext"
    (ext_dir / "commands").mkdir(parents=True)
    (ext_dir / "extension.yml").write_text(
        "schema_version: '1.0'\n"
        "extension:\n"
        "  id: test-ext\n"
        "  name: Test Extension\n"
        "  version: 1.0.0\n"
        "  description: A test extension for skill registration\n"
        "requires:\n"
        "  speckit_version: '>=0.1.0'\n"
        "provides:\n"
        "  commands:\n"
        "    - name: speckit.test-ext.hello\n"
        "      file: commands/hello.md\n"
        "      description: Test hello command\n",
        encoding="utf-8",
    )
    (ext_dir / "commands" / "hello.md").write_text(
        "---\n"
        "description: \"Test hello command\"\n"
        "---\n"
        "\n"
        "# Hello Command\n"
        "\n"
        "Run this to say hello.\n"
        "$ARGUMENTS\n",
        encoding="utf-8",
    )
    ExtensionManager(project).install_from_directory(
        ext_dir, "0.1.0", register_commands=False
    )

    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, [
        "init", "--here", "--force", "--integration", "copilot",
        "--script", "sh", "--non-interactive", "--ignore-agent-tools", "--offline",
    ])
    assert result.exit_code == 0, _strip(result.stdout)

    assert (project / ".github" / "skills" / "speckit-test-ext-hello" / "SKILL.md").is_file()
    assert not (project / ".github" / "agents" / "speckit.test-ext.hello.agent.md").exists()


def _create_test_extension(tmp_path: Path) -> Path:
    """Create a minimal extension dir with one hello command."""
    ext_dir = tmp_path / "test-ext"
    (ext_dir / "commands").mkdir(parents=True)
    (ext_dir / "extension.yml").write_text(
        "schema_version: '1.0'\n"
        "extension:\n"
        "  id: test-ext\n"
        "  name: Test Extension\n"
        "  version: 1.0.0\n"
        "  description: A test extension for skill registration\n"
        "requires:\n"
        "  speckit_version: '>=0.1.0'\n"
        "provides:\n"
        "  commands:\n"
        "    - name: speckit.test-ext.hello\n"
        "      file: commands/hello.md\n"
        "      description: Test hello command\n",
        encoding="utf-8",
    )
    (ext_dir / "commands" / "hello.md").write_text(
        "---\n"
        "description: \"Test hello command\"\n"
        "---\n"
        "\n"
        "# Hello Command\n"
        "\n"
        "Run this to say hello.\n"
        "$ARGUMENTS\n",
        encoding="utf-8",
    )
    return ext_dir


def test_init_force_rejects_symlinked_extension_skill_destination(tmp_path, monkeypatch):
    """Force re-init must not write SKILL.md through a symlinked skill dir (#5323).

    With force=True the pre-existing-directory guards in
    ``_register_extension_skills`` are bypassed, so a skill directory that
    is a symlink to a location outside the project would receive the
    generated SKILL.md. The destination must be rejected before any write.
    """
    from specify_cli.extensions import ExtensionManager

    result = _init(tmp_path, "proj")
    assert result.exit_code == 0, _strip(result.stdout)
    project = tmp_path / "proj"

    ext_dir = tmp_path / "test-ext"
    (ext_dir / "commands").mkdir(parents=True)
    (ext_dir / "extension.yml").write_text(
        "schema_version: '1.0'\n"
        "extension:\n"
        "  id: test-ext\n"
        "  name: Test Extension\n"
        "  version: 1.0.0\n"
        "  description: A test extension for skill registration\n"
        "requires:\n"
        "  speckit_version: '>=0.1.0'\n"
        "provides:\n"
        "  commands:\n"
        "    - name: speckit.test-ext.hello\n"
        "      file: commands/hello.md\n"
        "      description: Test hello command\n",
        encoding="utf-8",
    )
    (ext_dir / "commands" / "hello.md").write_text(
        "---\n"
        "description: \"Test hello command\"\n"
        "---\n"
        "\n"
        "# Hello Command\n"
        "\n"
        "Run this to say hello.\n"
        "$ARGUMENTS\n",
        encoding="utf-8",
    )
    ExtensionManager(project).install_from_directory(
        ext_dir, "0.1.0", register_commands=False
    )

    # Plant a symlink where the extension skill would be written, pointing
    # outside the project.
    outside = tmp_path / "outside"
    outside.mkdir()
    skill_subdir = project / ".github" / "skills" / "speckit-test-ext-hello"
    skill_subdir.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(outside, skill_subdir, target_is_directory=True)
    except OSError:
        pytest.skip("Current platform/user cannot create directory symlinks")

    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, [
        "init", "--here", "--force", "--integration", "copilot",
        "--script", "sh", "--non-interactive", "--ignore-agent-tools", "--offline",
    ])
    assert result.exit_code == 0, _strip(result.stdout)

    assert not (outside / "SKILL.md").exists()
    assert skill_subdir.is_symlink()


def test_relative_project_root_still_registers_extension_skills(tmp_path, monkeypatch):
    """Extension skills must register when the project root is relative (#5323).

    With ExtensionManager(Path(".")), the skills directory is relative
    while _extension_skill_trusted_root() returns an absolute root, so
    the trusted-root validation rejected every normal destination and
    the handler silently skipped the skill. Relative roots must be
    normalized before validation.
    """
    from specify_cli.extensions import ExtensionManager

    result = _init(tmp_path, "proj")
    assert result.exit_code == 0, _strip(result.stdout)
    project = tmp_path / "proj"

    ext_dir = _create_test_extension(tmp_path)

    # Switch the saved options to copilot (skills mode) first, mirroring
    # the #5321 force re-init path; no extension is installed yet.
    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, [
        "init", "--here", "--force", "--integration", "copilot",
        "--script", "sh", "--non-interactive", "--ignore-agent-tools", "--offline",
    ])
    assert result.exit_code == 0, _strip(result.stdout)

    manager = ExtensionManager(Path("."))
    manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

    assert (project / ".github" / "skills" / "speckit-test-ext-hello" / "SKILL.md").is_file()


def test_init_force_does_not_modify_hard_linked_skill_file(tmp_path, monkeypatch):
    """Force re-init must not write SKILL.md in place through a hard link (#5323).

    A hard-linked SKILL.md shares its inode with other paths, so writing
    it in place would change every linked copy. Forced registration must
    replace the file without modifying the shared data.
    """
    from specify_cli.extensions import ExtensionManager

    result = _init(tmp_path, "proj")
    assert result.exit_code == 0, _strip(result.stdout)
    project = tmp_path / "proj"

    ext_dir = _create_test_extension(tmp_path)

    # Switch the saved options to copilot (skills mode) first, mirroring
    # the #5321 force re-init path, so installation registers the skill
    # under .github/skills.
    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, [
        "init", "--here", "--force", "--integration", "copilot",
        "--script", "sh", "--non-interactive", "--ignore-agent-tools", "--offline",
    ])
    assert result.exit_code == 0, _strip(result.stdout)

    ExtensionManager(project).install_from_directory(
        ext_dir, "0.1.0", register_commands=False
    )

    # Pre-create the skill file with known content and hard-link it
    # outside the project.
    skill_file = project / ".github" / "skills" / "speckit-test-ext-hello" / "SKILL.md"
    assert skill_file.is_file()
    old_content = "---\nold: content\n---\n\n# Old Skill\n"
    skill_file.write_text(old_content, encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_link = outside / "SKILL.md"
    try:
        os.link(skill_file, outside_link)
    except OSError:
        pytest.skip("Current platform/user cannot create hard links")

    result = CliRunner().invoke(app, [
        "init", "--here", "--force", "--integration", "copilot",
        "--script", "sh", "--non-interactive", "--ignore-agent-tools", "--offline",
    ])
    assert result.exit_code == 0, _strip(result.stdout)

    # The linked copy outside the project must be untouched...
    assert outside_link.read_text(encoding="utf-8") == old_content
    # ...while the project's skill was regenerated.
    assert skill_file.read_text(encoding="utf-8") != old_content
    assert skill_file.is_file() and not skill_file.is_symlink()


def test_init_force_skips_hard_linked_skill_when_detach_fails(tmp_path, monkeypatch):
    """Force re-init must skip a hard-linked SKILL.md it cannot detach (#5323).

    If dropping the hard link raises OSError (for example, the file lives
    in a non-writable directory), writing in place would modify every
    linked copy, so the skill must be skipped instead of written. The
    init itself still succeeds.
    """
    from specify_cli.extensions import ExtensionManager

    result = _init(tmp_path, "proj")
    assert result.exit_code == 0, _strip(result.stdout)
    project = tmp_path / "proj"

    ext_dir = _create_test_extension(tmp_path)

    # Switch the saved options to copilot (skills mode) first, mirroring
    # the #5321 force re-init path, so installation registers the skill
    # under .github/skills.
    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, [
        "init", "--here", "--force", "--integration", "copilot",
        "--script", "sh", "--non-interactive", "--ignore-agent-tools", "--offline",
    ])
    assert result.exit_code == 0, _strip(result.stdout)

    ExtensionManager(project).install_from_directory(
        ext_dir, "0.1.0", register_commands=False
    )

    # Pre-create the skill file with known content and hard-link it
    # outside the project.
    skill_file = project / ".github" / "skills" / "speckit-test-ext-hello" / "SKILL.md"
    assert skill_file.is_file()
    old_content = "---\nold: content\n---\n\n# Old Skill\n"
    skill_file.write_text(old_content, encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_link = outside / "SKILL.md"
    try:
        os.link(skill_file, outside_link)
    except OSError:
        pytest.skip("Current platform/user cannot create hard links")

    # Make only this skill's detach fail, mirroring an unlink denied by
    # the directory permissions; every other unlink still works.
    import specify_cli.integrations._file_changes as file_changes

    real_unlink = file_changes.unlink

    def _fail_skill_detach(path, *, missing_ok=False):
        if os.fspath(path) == os.fspath(skill_file):
            raise OSError("cannot unlink hard-linked skill file")
        return real_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(file_changes, "unlink", _fail_skill_detach)

    result = CliRunner().invoke(app, [
        "init", "--here", "--force", "--integration", "copilot",
        "--script", "sh", "--non-interactive", "--ignore-agent-tools", "--offline",
    ])
    assert result.exit_code == 0, _strip(result.stdout)

    # The linked copy outside the project must be untouched...
    assert outside_link.read_text(encoding="utf-8") == old_content
    # ...and the project's skill must be left as it was, not overwritten
    # in place through the surviving hard link.
    assert skill_file.read_text(encoding="utf-8") == old_content
    assert skill_file.stat().st_nlink > 1
