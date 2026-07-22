"""Tests for IntegrationOption, IntegrationBase, MarkdownIntegration, and primitives."""

import shlex
import sys
from types import SimpleNamespace

import pytest

from specify_cli.integrations.base import (
    IntegrationBase,
    IntegrationOption,
    MarkdownIntegration,
    SkillsIntegration,
)
from specify_cli.integrations.manifest import IntegrationManifest
from .conftest import StubIntegration


class TestIntegrationOption:
    def test_defaults(self):
        opt = IntegrationOption(name="--flag")
        assert opt.name == "--flag"
        assert opt.is_flag is False
        assert opt.required is False
        assert opt.default is None
        assert opt.help == ""

    def test_flag_option(self):
        opt = IntegrationOption(name="--skills", is_flag=True, default=True, help="Enable skills")
        assert opt.is_flag is True
        assert opt.default is True
        assert opt.help == "Enable skills"

    def test_required_option(self):
        opt = IntegrationOption(name="--commands-dir", required=True, help="Dir path")
        assert opt.required is True

    def test_frozen(self):
        opt = IntegrationOption(name="--x")
        with pytest.raises(AttributeError):
            opt.name = "--y"  # type: ignore[misc]


class TestIntegrationBase:
    def test_key_and_config(self):
        i = StubIntegration()
        assert i.key == "stub"
        assert i.config["name"] == "Stub Agent"
        assert i.registrar_config["format"] == "markdown"

    def test_options_default_empty(self):
        assert StubIntegration.options() == []

    def test_shared_commands_dir(self):
        i = StubIntegration()
        cmd_dir = i.shared_commands_dir()
        assert cmd_dir is not None
        assert cmd_dir.is_dir()

    def test_setup_uses_shared_templates(self, tmp_path):
        i = StubIntegration()
        manifest = IntegrationManifest("stub", tmp_path)
        created = i.setup(tmp_path, manifest)
        assert len(created) > 0
        for f in created:
            assert f.parent == tmp_path / ".stub" / "commands"
            assert f.name.startswith("speckit.")
            assert f.name.endswith(".md")

    def test_setup_copies_templates(self, tmp_path, monkeypatch):
        tpl = tmp_path / "_templates"
        tpl.mkdir()
        (tpl / "plan.md").write_text("plan content", encoding="utf-8")
        (tpl / "specify.md").write_text("spec content", encoding="utf-8")

        i = StubIntegration()
        monkeypatch.setattr(type(i), "list_command_templates", lambda self: sorted(tpl.glob("*.md")))

        project = tmp_path / "project"
        project.mkdir()
        created = i.setup(project, IntegrationManifest("stub", project))
        assert len(created) == 2
        assert (project / ".stub" / "commands" / "speckit.plan.md").exists()
        assert (project / ".stub" / "commands" / "speckit.specify.md").exists()

    def test_install_delegates_to_setup(self, tmp_path):
        i = StubIntegration()
        manifest = IntegrationManifest("stub", tmp_path)
        result = i.install(tmp_path, manifest)
        assert len(result) > 0

    def test_uninstall_delegates_to_teardown(self, tmp_path):
        i = StubIntegration()
        manifest = IntegrationManifest("stub", tmp_path)
        removed, skipped = i.uninstall(tmp_path, manifest)
        assert removed == []
        assert skipped == []


class TestMarkdownIntegration:
    def test_is_subclass_of_base(self):
        assert issubclass(MarkdownIntegration, IntegrationBase)

    def test_stub_is_markdown(self):
        assert isinstance(StubIntegration(), MarkdownIntegration)


class TestBasePrimitives:
    def test_shared_commands_dir_returns_path(self):
        i = StubIntegration()
        cmd_dir = i.shared_commands_dir()
        assert cmd_dir is not None
        assert cmd_dir.is_dir()

    def test_shared_templates_dir_returns_path(self):
        i = StubIntegration()
        tpl_dir = i.shared_templates_dir()
        assert tpl_dir is not None
        assert tpl_dir.is_dir()

    def test_list_command_templates_returns_md_files(self):
        i = StubIntegration()
        templates = i.list_command_templates()
        assert len(templates) > 0
        assert all(t.suffix == ".md" for t in templates)

    def test_list_command_templates_keeps_checklist_after_plan(self):
        i = StubIntegration()
        stems = [template.stem for template in i.list_command_templates()]
        assert stems.index("plan") < stems.index("checklist")

    def test_command_filename_default(self):
        i = StubIntegration()
        assert i.command_filename("plan") == "speckit.plan.md"

    def test_commands_dest(self, tmp_path):
        i = StubIntegration()
        dest = i.commands_dest(tmp_path)
        assert dest == tmp_path / ".stub" / "commands"

    def test_commands_dest_no_config_raises(self, tmp_path):
        class NoConfig(MarkdownIntegration):
            key = "noconfig"
        with pytest.raises(ValueError, match="config is not set"):
            NoConfig().commands_dest(tmp_path)

    def test_copy_command_to_directory(self, tmp_path):
        src = tmp_path / "source.md"
        src.write_text("content", encoding="utf-8")
        dest_dir = tmp_path / "output"
        result = IntegrationBase.copy_command_to_directory(src, dest_dir, "speckit.plan.md")
        assert result == dest_dir / "speckit.plan.md"
        assert result.read_text(encoding="utf-8") == "content"

    def test_record_file_in_manifest(self, tmp_path):
        f = tmp_path / "f.txt"
        f.write_text("hello", encoding="utf-8")
        m = IntegrationManifest("test", tmp_path)
        IntegrationBase.record_file_in_manifest(f, tmp_path, m)
        assert "f.txt" in m.files

    def test_write_file_and_record(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        dest = tmp_path / "sub" / "f.txt"
        result = IntegrationBase.write_file_and_record("content", dest, tmp_path, m)
        assert result == dest
        assert dest.read_text(encoding="utf-8") == "content"
        assert "sub/f.txt" in m.files

    def test_setup_copies_shared_templates(self, tmp_path):
        i = StubIntegration()
        m = IntegrationManifest("stub", tmp_path)
        created = i.setup(tmp_path, m)
        assert len(created) > 0
        for f in created:
            assert f.parent.name == "commands"
            assert f.name.startswith("speckit.")
            assert f.name.endswith(".md")


class TestBuildCommandInvocation:
    """Tests for build_command_invocation across integration types."""

    def test_base_core_command_dotted(self):
        i = StubIntegration()
        assert i.build_command_invocation("speckit.plan") == "/speckit.plan"

    def test_base_core_command_bare(self):
        i = StubIntegration()
        assert i.build_command_invocation("plan") == "/speckit.plan"

    def test_base_core_command_with_args(self):
        i = StubIntegration()
        assert i.build_command_invocation("plan", "my feature") == "/speckit.plan my feature"

    def test_base_extension_command(self):
        i = StubIntegration()
        assert i.build_command_invocation("speckit.git.commit") == "/speckit.git.commit"

    def test_base_extension_command_bare(self):
        i = StubIntegration()
        assert i.build_command_invocation("git.commit") == "/speckit.git.commit"

    def test_skills_core_command(self):
        from specify_cli.integrations import get_integration
        i = get_integration("codex")
        assert i.build_command_invocation("speckit.plan") == "/speckit-plan"
        assert i.build_command_invocation("plan") == "/speckit-plan"

    def test_skills_extension_command(self):
        from specify_cli.integrations import get_integration
        i = get_integration("codex")
        assert i.build_command_invocation("speckit.git.commit") == "/speckit-git-commit"
        assert i.build_command_invocation("git.commit") == "/speckit-git-commit"

    def test_skills_extension_command_with_args(self):
        from specify_cli.integrations import get_integration
        i = get_integration("codex")
        assert i.build_command_invocation("speckit.git.commit", "fix typo") == "/speckit-git-commit fix typo"

    def test_forge_core_command_hyphenated(self):
        """Forge installs hyphenated slash-commands (/speckit-<name>), so the
        dispatch invocation must be hyphenated too — not the dotted default it
        would inherit from MarkdownIntegration."""
        from specify_cli.integrations import get_integration
        i = get_integration("forge")
        assert i.build_command_invocation("speckit.plan") == "/speckit-plan"
        assert i.build_command_invocation("plan") == "/speckit-plan"

    def test_forge_extension_command_hyphenated(self):
        from specify_cli.integrations import get_integration
        i = get_integration("forge")
        assert i.build_command_invocation("speckit.git.commit") == "/speckit-git-commit"
        assert (
            i.build_command_invocation("speckit.git.commit", "fix typo")
            == "/speckit-git-commit fix typo"
        )


class TestResolveCommandRefs:
    """Tests for __SPECKIT_COMMAND_<NAME>__ placeholder resolution."""

    def test_dot_separator_core_command(self):
        text = "Run `__SPECKIT_COMMAND_PLAN__` to plan."
        result = IntegrationBase.resolve_command_refs(text, ".")
        assert result == "Run `/speckit.plan` to plan."

    def test_hyphen_separator_core_command(self):
        text = "Run `__SPECKIT_COMMAND_PLAN__` to plan."
        result = IntegrationBase.resolve_command_refs(text, "-")
        assert result == "Run `/speckit-plan` to plan."

    def test_multiple_placeholders(self):
        text = "__SPECKIT_COMMAND_SPECIFY__ then __SPECKIT_COMMAND_PLAN__ then __SPECKIT_COMMAND_TASKS__"
        result = IntegrationBase.resolve_command_refs(text, ".")
        assert result == "/speckit.specify then /speckit.plan then /speckit.tasks"

    def test_extension_command_dot(self):
        text = "Run __SPECKIT_COMMAND_GIT_COMMIT__ to commit."
        result = IntegrationBase.resolve_command_refs(text, ".")
        assert result == "Run /speckit.git.commit to commit."

    def test_extension_command_hyphen(self):
        text = "Run __SPECKIT_COMMAND_GIT_COMMIT__ to commit."
        result = IntegrationBase.resolve_command_refs(text, "-")
        assert result == "Run /speckit-git-commit to commit."

    def test_no_placeholders_unchanged(self):
        text = "No placeholders here."
        assert IntegrationBase.resolve_command_refs(text, ".") == text

    def test_default_separator_is_dot(self):
        text = "__SPECKIT_COMMAND_PLAN__"
        assert IntegrationBase.resolve_command_refs(text) == "/speckit.plan"

    def test_invoke_separator_class_attribute(self):
        assert IntegrationBase.invoke_separator == "."
        assert SkillsIntegration.invoke_separator == "-"

    def test_effective_invoke_separator_default(self):
        """Base classes return invoke_separator regardless of parsed_options."""
        from .conftest import StubIntegration
        stub = StubIntegration()
        assert stub.effective_invoke_separator() == "."
        assert stub.effective_invoke_separator({"skills": True}) == "."

    def test_process_template_resolves_placeholders(self):
        content = "---\ndescription: test\n---\nRun __SPECKIT_COMMAND_PLAN__ now."
        result = IntegrationBase.process_template(
            content, "test-agent", "sh", invoke_separator="."
        )
        assert "/speckit.plan" in result
        assert "__SPECKIT_COMMAND_" not in result

    def test_process_template_skills_separator(self):
        content = "---\ndescription: test\n---\nRun __SPECKIT_COMMAND_PLAN__ now."
        result = IntegrationBase.process_template(
            content, "test-agent", "sh", invoke_separator="-"
        )
        assert "/speckit-plan" in result
        assert "__SPECKIT_COMMAND_" not in result

    def test_unclosed_placeholder_unchanged(self):
        text = "Run __SPECKIT_COMMAND_PLAN to plan."
        assert IntegrationBase.resolve_command_refs(text, ".") == text

    def test_empty_name_not_matched(self):
        text = "Run __SPECKIT_COMMAND___ to plan."
        assert IntegrationBase.resolve_command_refs(text, ".") == text

    def test_lowercase_placeholder_not_matched(self):
        text = "Run __SPECKIT_COMMAND_plan__ to plan."
        assert IntegrationBase.resolve_command_refs(text, ".") == text

    def test_placeholder_adjacent_to_text(self):
        text = "foo__SPECKIT_COMMAND_PLAN__bar"
        result = IntegrationBase.resolve_command_refs(text, ".")
        assert result == "foo/speckit.planbar"

    def test_placeholder_with_digits(self):
        text = "__SPECKIT_COMMAND_V2_PLAN__"
        result = IntegrationBase.resolve_command_refs(text, ".")
        assert result == "/speckit.v2.plan"


class TestResolvePythonInterpreter:
    def test_returns_python_on_path(self, monkeypatch):
        # Positive: when python3 is on PATH it is preferred over python.
        # Pin a POSIX platform so the Windows stub probe (tested separately
        # below) does not reject the fake PATH entries on Windows CI.
        def fake_which(name):
            return f"/usr/bin/{name}" if name in ("python3", "python") else None

        monkeypatch.setattr("specify_cli.integrations.base.sys.platform", "linux")
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which", fake_which
        )
        assert IntegrationBase.resolve_python_interpreter() == "python3"

    def test_falls_back_to_python_when_no_python3(self, monkeypatch):
        def fake_which(name):
            return "/usr/bin/python" if name == "python" else None

        monkeypatch.setattr("specify_cli.integrations.base.sys.platform", "linux")
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which", fake_which
        )
        assert IntegrationBase.resolve_python_interpreter() == "python"

    def test_falls_back_to_sys_executable_when_nothing_found(self, monkeypatch):
        # Negative: nothing on PATH and no venv -> the running interpreter
        # (sys.executable) is used so the command works in this environment.
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which", lambda name: None
        )
        monkeypatch.setattr(
            "specify_cli.integrations.base.sys.executable", "/opt/py/bin/python"
        )
        assert IntegrationBase.resolve_python_interpreter() == "/opt/py/bin/python"

    def test_falls_back_to_python3_when_no_interpreter_at_all(self, monkeypatch):
        # Negative edge: neither PATH nor sys.executable resolves.
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which", lambda name: None
        )
        monkeypatch.setattr(
            "specify_cli.integrations.base.sys.executable", ""
        )
        assert IntegrationBase.resolve_python_interpreter() == "python3"

    def test_prefers_project_venv_posix(self, monkeypatch, tmp_path):
        venv_python = tmp_path / ".venv" / "bin" / "python"
        venv_python.parent.mkdir(parents=True)
        venv_python.write_text("")
        # Even if python3 is on PATH, the project venv wins. The returned
        # path is relative to the project root for portability.
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which",
            lambda name: "/usr/bin/python3",
        )
        result = IntegrationBase.resolve_python_interpreter(tmp_path)
        assert result == ".venv/bin/python"

    def test_prefers_project_venv_windows(self, monkeypatch, tmp_path):
        venv_python = tmp_path / ".venv" / "Scripts" / "python.exe"
        venv_python.parent.mkdir(parents=True)
        venv_python.write_text("")
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which", lambda name: None
        )
        result = IntegrationBase.resolve_python_interpreter(tmp_path)
        assert result == ".venv/Scripts/python.exe"

    def test_ignores_missing_venv(self, monkeypatch, tmp_path):
        # Negative: no venv directory -> PATH resolution is used instead.
        monkeypatch.setattr("specify_cli.integrations.base.sys.platform", "linux")
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which",
            lambda name: "/usr/bin/python3" if name == "python3" else None,
        )
        assert IntegrationBase.resolve_python_interpreter(tmp_path) == "python3"

    def test_windows_skips_store_alias_stub(self, monkeypatch):
        # On Windows, python3 on PATH may be the Microsoft Store App
        # Execution Alias stub: it exists but only prints an installer
        # hint and exits non-zero. Existence is not enough; the
        # interpreter must actually run (mirrors #3304 for the CLI).
        monkeypatch.setattr("specify_cli.integrations.base.sys.platform", "win32")
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which",
            lambda name: f"C:\\WindowsApps\\{name}.exe"
            if name in ("python3", "python")
            else None,
        )
        monkeypatch.setattr(
            IntegrationBase, "_interpreter_runs", staticmethod(lambda path: False)
        )
        monkeypatch.setattr(
            "specify_cli.integrations.base.sys.executable", "C:\\Python\\python.exe"
        )
        result = IntegrationBase.resolve_python_interpreter()
        assert result == "C:\\Python\\python.exe"

    def test_windows_keeps_working_interpreter(self, monkeypatch):
        # Positive: a real python3 on Windows PATH passes the run check.
        monkeypatch.setattr("specify_cli.integrations.base.sys.platform", "win32")
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which",
            lambda name: f"C:\\Python\\{name}.exe" if name == "python3" else None,
        )
        monkeypatch.setattr(
            IntegrationBase, "_interpreter_runs", staticmethod(lambda path: True)
        )
        assert IntegrationBase.resolve_python_interpreter() == "python3"

    def test_windows_stub_python3_falls_through_to_working_python(self, monkeypatch):
        # python3 is the stub but python is a real install: pick python.
        monkeypatch.setattr("specify_cli.integrations.base.sys.platform", "win32")
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which",
            lambda name: f"C:\\somewhere\\{name}.exe"
            if name in ("python3", "python")
            else None,
        )
        monkeypatch.setattr(
            IntegrationBase,
            "_interpreter_runs",
            staticmethod(lambda path: path.endswith("python.exe")),
        )
        assert IntegrationBase.resolve_python_interpreter() == "python"

    def test_posix_does_not_spawn_run_check(self, monkeypatch):
        # Non-Windows platforms have no App Execution Alias; existence
        # on PATH stays sufficient and no subprocess is spawned.
        monkeypatch.setattr("specify_cli.integrations.base.sys.platform", "linux")
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which",
            lambda name: "/usr/bin/python3" if name == "python3" else None,
        )

        def boom(path):
            raise AssertionError("run check must not execute on POSIX")

        monkeypatch.setattr(
            IntegrationBase, "_interpreter_runs", staticmethod(boom)
        )
        assert IntegrationBase.resolve_python_interpreter() == "python3"


class TestProcessTemplatePyScriptType:
    CONTENT = (
        "---\n"
        "scripts:\n"
        "  sh: scripts/bash/check-prerequisites.sh --json\n"
        "  ps: scripts/powershell/check-prerequisites.ps1 -Json\n"
        "  py: scripts/python/check-prerequisites.py --json\n"
        "---\n"
        "Run {SCRIPT} now."
    )

    def test_py_prefixes_interpreter(self, monkeypatch):
        # Positive: py script type prefixes a resolved interpreter and the
        # script path is rewritten to the .specify location.
        monkeypatch.setattr("specify_cli.integrations.base.sys.platform", "linux")
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which",
            lambda name: "/usr/bin/python3" if name == "python3" else None,
        )
        result = IntegrationBase.process_template(self.CONTENT, "agent", "py")
        assert "python3 .specify/scripts/python/check-prerequisites.py --json" in result
        # The scripts: frontmatter block is stripped.
        assert "scripts:" not in result

    def test_sh_does_not_prefix_interpreter(self):
        # Negative: non-py script types are never prefixed with an interpreter.
        result = IntegrationBase.process_template(self.CONTENT, "agent", "sh")
        assert ".specify/scripts/bash/check-prerequisites.sh --json" in result
        assert "python" not in result

    def test_body_scripts_example_does_not_override_frontmatter(self):
        content = (
            "---\n"
            "scripts:\n"
            "  sh: scripts/bash/real.sh --json\n"
            "---\n"
            "Run {SCRIPT} now.\n"
            "```yaml\n"
            "scripts:\n"
            "  sh: examples/not-the-command.sh\n"
            "```\n"
        )

        result = IntegrationBase.process_template(content, "agent", "sh")

        assert ".specify/scripts/bash/real.sh --json" in result
        assert "examples/not-the-command.sh" in result

    def test_py_quotes_interpreter_with_spaces(self, monkeypatch):
        # An interpreter path containing whitespace (e.g. Windows
        # ``Program Files``) must be quoted so it isn't split into args.
        interpreter = r"C:\Program Files\Python\python.exe"
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which", lambda name: None
        )
        monkeypatch.setattr(
            "specify_cli.integrations.base.sys.executable",
            interpreter,
        )
        monkeypatch.setattr(
            "specify_cli.integrations.base.os", SimpleNamespace(name="posix")
        )
        result = IntegrationBase.process_template(self.CONTENT, "agent", "py")
        assert (
            f"{shlex.quote(interpreter)} "
            ".specify/scripts/python/check-prerequisites.py --json"
        ) in result

    def test_py_does_not_quote_interpreter_without_spaces(self, monkeypatch):
        # Negative: a whitespace-free interpreter is left unquoted.
        monkeypatch.setattr(
            "specify_cli.integrations.base.shutil.which",
            lambda name: "/usr/bin/python3" if name == "python3" else None,
        )
        result = IntegrationBase.process_template(self.CONTENT, "agent", "py")
        assert '"' not in result.split("check-prerequisites.py")[0]

    def test_py_uses_project_venv(self, monkeypatch, tmp_path):
        venv_python = tmp_path / ".venv" / "bin" / "python"
        venv_python.parent.mkdir(parents=True)
        venv_python.write_text("")
        result = IntegrationBase.process_template(
            self.CONTENT, "agent", "py", project_root=tmp_path
        )
        assert ".venv/bin/python .specify/scripts/python/check-prerequisites.py" in result

    def test_setup_py_falls_back_to_platform_shell(
        self, monkeypatch, tmp_path
    ):
        template = tmp_path / "fallback.md"
        template.write_text(
            "---\n"
            "scripts:\n"
            "  sh: scripts/bash/check-prerequisites.sh --json\n"
            "  ps: scripts/powershell/check-prerequisites.ps1 -Json\n"
            "---\n"
            "Run {SCRIPT} now.\n",
            encoding="utf-8",
        )
        integration = StubIntegration()
        monkeypatch.setattr(
            integration, "list_command_templates", lambda: [template]
        )

        created = integration.setup(
            tmp_path,
            IntegrationManifest("stub", tmp_path),
            script_type="py",
        )

        rendered = created[0].read_text(encoding="utf-8")
        expected = (
            ".specify/scripts/powershell/check-prerequisites.ps1"
            if sys.platform == "win32"
            else ".specify/scripts/bash/check-prerequisites.sh"
        )
        assert "{SCRIPT}" not in rendered
        assert expected in rendered


class TestInstallScriptsPython:
    def _make_integration_with_scripts(self, monkeypatch, tmp_path):
        scripts_src = tmp_path / "bundled_scripts"
        scripts_src.mkdir()
        (scripts_src / "common.py").write_text("print('hi')\n")
        (scripts_src / "common.sh").write_text("echo hi\n")
        (scripts_src / "notes.txt").write_text("not executable\n")
        integration = StubIntegration()
        monkeypatch.setattr(
            integration, "integration_scripts_dir", lambda: scripts_src
        )
        return integration

    def test_copies_all_script_files(self, monkeypatch, tmp_path):
        # Cross-platform: every bundled file is copied into the project.
        integration = self._make_integration_with_scripts(monkeypatch, tmp_path)
        project_root = tmp_path / "proj"
        project_root.mkdir()
        manifest = IntegrationManifest("stub", project_root.resolve())

        created = integration.install_scripts(project_root, manifest)
        names = {p.name for p in created}
        assert {"common.py", "common.sh", "notes.txt"} == names

    @pytest.mark.skipif(
        sys.platform == "win32", reason="chmod exec bit not reliable on Windows"
    )
    def test_marks_py_and_sh_executable(self, monkeypatch, tmp_path):
        integration = self._make_integration_with_scripts(monkeypatch, tmp_path)
        project_root = tmp_path / "proj"
        project_root.mkdir()
        manifest = IntegrationManifest("stub", project_root.resolve())

        integration.install_scripts(project_root, manifest)

        dest = project_root / ".specify" / "integrations" / "stub" / "scripts"
        py_file = dest / "common.py"
        sh_file = dest / "common.sh"
        txt_file = dest / "notes.txt"
        # Positive: .py and .sh are executable.
        assert py_file.stat().st_mode & 0o111
        assert sh_file.stat().st_mode & 0o111
        # Negative: a non-script file is not made executable.
        assert not (txt_file.stat().st_mode & 0o111)
