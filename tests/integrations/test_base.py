"""Tests for IntegrationOption, IntegrationBase, MarkdownIntegration, and primitives."""

import inspect
import shlex
import sys
from types import SimpleNamespace

import pytest

from specify_cli.integrations.base import (
    DISPATCH_SETTINGS,
    DispatchSettingsError,
    IntegrationBase,
    IntegrationOption,
    MarkdownIntegration,
    SkillsIntegration,
    TomlIntegration,
    check_dispatch_settings,
    dispatch_setting_value_error,
    effective_dispatch_settings,
    requested_dispatch_settings,
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

    def test_runtime_config_default_accepts_empty_and_rejects_non_empty(self):
        integration = StubIntegration()

        integration.validate_runtime_config([], {})
        with pytest.raises(ValueError, match="integration_args"):
            integration.validate_runtime_config(["./agent.yaml"], {})
        with pytest.raises(ValueError, match="integration_options.*unknown"):
            integration.validate_runtime_config([], {"unknown": "value"})

    def test_all_builtin_exec_builders_accept_runtime_config(self):
        from specify_cli.integrations import INTEGRATION_REGISTRY

        for key, integration in INTEGRATION_REGISTRY.items():
            parameters = inspect.signature(integration.build_exec_args).parameters
            assert "integration_args" in parameters, key
            assert "integration_options" in parameters, key
            assert "project_root" in parameters, key

    def test_unsupported_exec_builders_reject_runtime_config_directly(self):
        from specify_cli.integrations import INTEGRATION_REGISTRY

        for integration in INTEGRATION_REGISTRY.values():
            if (
                type(integration).validate_runtime_config
                is not IntegrationBase.validate_runtime_config
            ):
                continue
            with pytest.raises(ValueError, match="integration_args"):
                integration.build_exec_args(
                    "prompt", integration_args=["unexpected"]
                )

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

    @pytest.mark.parametrize("force", [False, True])
    def test_teardown_supports_legacy_remove_events(self, tmp_path, force):
        calls = []

        class LegacyIntegration(StubIntegration):
            def remove_events(self, project_root, manifest):
                calls.append((project_root, manifest))

        integration = LegacyIntegration()
        manifest = IntegrationManifest(integration.key, tmp_path)
        generated = manifest.record_file(".stub/commands/speckit.plan.md", "# Plan\n")
        manifest.save()

        removed, skipped = integration.teardown(tmp_path, manifest, force=force)

        assert calls == [(tmp_path, manifest)]
        assert removed == [generated]
        assert skipped == []
        assert not generated.exists()
        assert not manifest.manifest_path.exists()

    @pytest.mark.parametrize("force", [False, True])
    @pytest.mark.parametrize("style", ["keyword", "kwargs"])
    def test_teardown_forwards_supported_force(self, tmp_path, force, style):
        calls = []

        class KeywordIntegration(StubIntegration):
            def remove_events(self, project_root, manifest, *, force=False):
                calls.append(force)

        class KwargsIntegration(StubIntegration):
            def remove_events(self, project_root, manifest, **kwargs):
                calls.append(kwargs["force"])

        integration = KeywordIntegration() if style == "keyword" else KwargsIntegration()
        manifest = IntegrationManifest(integration.key, tmp_path)

        integration.teardown(tmp_path, manifest, force=force)

        assert calls == [force]

    @pytest.mark.parametrize("force", [False, True])
    def test_teardown_does_not_retry_remove_events_type_error(self, tmp_path, force):
        calls = []

        class BrokenIntegration(StubIntegration):
            def remove_events(self, project_root, manifest, *, force=False):
                calls.append(force)
                raise TypeError("adapter cleanup failed")

        integration = BrokenIntegration()
        manifest = IntegrationManifest(integration.key, tmp_path)
        generated = manifest.record_file(".stub/commands/speckit.plan.md", "# Plan\n")

        with pytest.raises(TypeError, match="adapter cleanup failed"):
            integration.teardown(tmp_path, manifest, force=force)

        assert calls == [force]
        assert generated.exists()


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

    @pytest.mark.parametrize(
        ("integration_key", "command_name", "args", "expected"),
        [
            ("stub", "speckit.plan", "", "/speckit.plan"),
            ("stub", "plan", "", "/speckit.plan"),
            ("stub", "plan", "my feature", "/speckit.plan my feature"),
            ("stub", "speckit.git.commit", "", "/speckit.git.commit"),
            ("stub", "git.commit", "", "/speckit.git.commit"),
            ("forge", "speckit.plan", "", "/speckit-plan"),
            ("forge", "plan", "", "/speckit-plan"),
            ("forge", "speckit.git.commit", "fix typo", "/speckit-git-commit fix typo"),
            ("cline", "speckit.plan", "", "/speckit-plan"),
            ("cline", "git.commit", "fix typo", "/speckit-git-commit fix typo"),
            ("codex", "speckit.plan", "", "$speckit-plan"),
            ("codex", "plan", "", "$speckit-plan"),
            ("codex", "speckit.git.commit", "", "$speckit-git-commit"),
            ("codex", "git.commit", "fix typo", "$speckit-git-commit fix typo"),
            ("kimi", "speckit.plan", "", "/skill:speckit-plan"),
            ("kimi", "git.commit", "fix typo", "/skill:speckit-git-commit fix typo"),
        ],
    )
    def test_native_invocation_styles(
        self, integration_key, command_name, args, expected
    ):
        from specify_cli.integrations import get_integration

        integration = (
            StubIntegration()
            if integration_key == "stub"
            else get_integration(integration_key)
        )

        assert integration.build_command_invocation(command_name, args) == expected

    @pytest.mark.parametrize("integration_key", ["codex", "zcode"])
    def test_dollar_skill_post_processing_is_idempotent(self, integration_key):
        from specify_cli.integrations import get_integration

        content = (
            "---\nname: test\n---\n\n"
            "Literal slash invocation: /speckit-plan\n"
            "- For each executable hook, output the following based on its flag:\n"
        )
        integration = get_integration(integration_key)
        once = integration.post_process_skill_content(content)
        twice = integration.post_process_skill_content(once)

        assert twice == once
        assert once.count("replace dots (`.`) with hyphens") == 1
        assert "$speckit-git-commit" in once
        assert "/speckit-plan" in once

    def test_kimi_skill_post_processing_is_idempotent(self):
        """Kimi's post_process_skill_content must be idempotent.

        The hook-command note is injected with the /skill: prefix by the base
        class (via get_invocation_prefix), so the idempotency check matches on
        re-runs without requiring the broad /speckit- -> /skill:speckit- body
        replacement to recognise a duplicate.
        """
        from specify_cli.integrations import get_integration

        content = (
            "---\nname: test\n---\n\n"
            "Literal slash invocation: /speckit-plan\n"
            "- For each executable hook, output the following based on its flag:\n"
        )
        integration = get_integration("kimi")
        once = integration.post_process_skill_content(content)
        twice = integration.post_process_skill_content(once)

        assert twice == once
        assert once.count("replace dots (`.`) with hyphens") == 1
        assert "/skill:speckit-git-commit" in once

    def test_get_invocation_prefix_skill_colon(self):
        """get_invocation_prefix returns '/skill:' for Kimi in skills mode."""
        from specify_cli._invocation_style import get_invocation_prefix

        assert get_invocation_prefix("kimi", True) == "/skill:"
        assert get_invocation_prefix("kimi", False) == "/"
        assert get_invocation_prefix("codex", True) == "$"
        assert get_invocation_prefix("claude", True) == "/"

class TestResolveCommandRefs:
    """Tests for __SPECKIT_COMMAND_<NAME>__ placeholder resolution."""

    @pytest.mark.parametrize(
        ("placeholder", "separator", "prefix", "expected"),
        [
            ("PLAN", ".", "/", "/speckit.plan"),
            ("PLAN", "-", "/", "/speckit-plan"),
            ("PLAN", "-", "$", "$speckit-plan"),
            ("PLAN", "-", "/skill:", "/skill:speckit-plan"),
            ("GIT_COMMIT", ".", "/", "/speckit.git.commit"),
            ("GIT_COMMIT", "-", "/", "/speckit-git-commit"),
            (
                "AGENT-CONTEXT_UPDATE",
                ".",
                "/",
                "/speckit.agent-context.update",
            ),
            (
                "AGENT-CONTEXT_UPDATE",
                "-",
                "/",
                "/speckit-agent-context-update",
            ),
            ("V2_PLAN", ".", "/", "/speckit.v2.plan"),
        ],
    )
    def test_command_reference_rendering(
        self, placeholder, separator, prefix, expected
    ):
        text = f"Run __SPECKIT_COMMAND_{placeholder}__ now."
        result = IntegrationBase.resolve_command_refs(text, separator, prefix)

        assert result == f"Run {expected} now."

    def test_process_template_kimi_uses_skill_colon_prefix(self):
        """process_template must use /skill: prefix for Kimi without relying on
        post_process_skill_content's broad replacement."""
        text = "---\ndescription: test\n---\nRun `__SPECKIT_COMMAND_PLAN__` to plan."
        result = IntegrationBase.process_template(
            text, "kimi", "sh", invoke_separator="-"
        )
        assert "/skill:speckit-plan" in result
        assert "/speckit-plan" not in result

    def test_multiple_placeholders(self):
        text = "__SPECKIT_COMMAND_SPECIFY__ then __SPECKIT_COMMAND_PLAN__ then __SPECKIT_COMMAND_TASKS__"
        result = IntegrationBase.resolve_command_refs(text, ".")
        assert result == "/speckit.specify then /speckit.plan then /speckit.tasks"

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

    def test_leading_hyphen_not_matched(self):
        text = "Run __SPECKIT_COMMAND_-PLAN__ to plan."
        assert IntegrationBase.resolve_command_refs(text, ".") == text

    def test_placeholder_adjacent_to_text(self):
        text = "foo__SPECKIT_COMMAND_PLAN__bar"
        result = IntegrationBase.resolve_command_refs(text, ".")
        assert result == "foo/speckit.planbar"


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


# -- Per-step dispatch settings contract ---------------------------------------

_CLI_CONFIG = {**StubIntegration.config, "requires_cli": True}


class _TranslatingIntegration(StubIntegration):
    """Declares both settings and translates them in its own builder."""

    key = "translating-stub"
    config = _CLI_CONFIG
    supported_dispatch_settings = frozenset(DISPATCH_SETTINGS)

    def build_exec_args(
        self,
        prompt,
        *,
        model=None,
        output_json=True,
        integration_args=None,
        integration_options=None,
        project_root=None,
        reasoning_effort=None,
        context_size=None,
    ):
        args = super().build_exec_args(
            prompt,
            model=model,
            output_json=output_json,
            integration_args=integration_args,
            integration_options=integration_options,
            project_root=project_root,
        )
        if reasoning_effort is not None:
            args.extend(["--effort", reasoning_effort])
        if context_size is not None:
            args.extend(["--context", context_size])
        return args


class _InheritingIntegration(_TranslatingIntegration):
    key = "inheriting-stub"


class _LegacyKwargsOverride(_TranslatingIntegration):
    """Replaces the capable builder without re-declaring support."""

    key = "legacy-kwargs-stub"

    def build_exec_args(self, prompt, **kwargs):
        return ["legacy-kwargs-stub", "-p", prompt]


class _DeclaringFormatBase(StubIntegration):
    """Declares support but inherits a generic format-base builder."""

    key = "declaring-format-stub"
    config = _CLI_CONFIG
    supported_dispatch_settings = frozenset({"reasoning_effort"})


class _StringDeclaration(StubIntegration):
    key = "string-declaration-stub"
    config = _CLI_CONFIG
    supported_dispatch_settings = "reasoning_effort"

    def build_exec_args(self, prompt, **kwargs):
        return ["string-declaration-stub", "-p", prompt]


class _DeclaresWithoutKeyword(StubIntegration):
    key = "no-keyword-stub"
    config = _CLI_CONFIG
    supported_dispatch_settings = frozenset({"reasoning_effort"})

    def build_exec_args(
        self,
        prompt,
        *,
        model=None,
        output_json=True,
        integration_args=None,
        integration_options=None,
        project_root=None,
    ):
        return ["no-keyword-stub", "-p", prompt]


class _ForwardsToSuper(StubIntegration):
    """Declares support but hands the settings to the generic builder."""

    key = "forwarding-stub"
    config = _CLI_CONFIG
    supported_dispatch_settings = frozenset({"reasoning_effort"})

    def build_exec_args(self, prompt, **kwargs):
        return super().build_exec_args(prompt, **kwargs)


class _CommandOwner(StubIntegration):
    """Translates settings only in an overridden dispatch_command."""

    key = "command-owner-stub"
    supported_dispatch_settings = frozenset({"reasoning_effort"})

    def dispatch_command(self, command_name, args="", *, reasoning_effort=None, **kwargs):
        return {"exit_code": 0, "stdout": reasoning_effort or "", "stderr": ""}


class _ValidatingIntegration(_TranslatingIntegration):
    key = "validating-stub"

    def validate_dispatch_setting(self, name, value):
        if value == "rejected":
            raise ValueError(f"{name} value is not accepted by this CLI")
        if value == "unlabeled":
            raise DispatchSettingsError("unlabeled failure")


class _HintingIntegration(StubIntegration):
    key = "hinting-stub"

    def dispatch_setting_hint(self, setting):
        if setting == "context_size":
            return "Choose a long-context model instead."
        return None


class _LegacyStrictBuilder(StubIntegration):
    """A CLI builder whose signature predates dispatch settings."""

    key = "legacy-strict-stub"
    config = _CLI_CONFIG

    def __init__(self):
        self.calls = []

    def build_exec_args(
        self,
        prompt,
        *,
        model=None,
        output_json=True,
        integration_args=None,
        integration_options=None,
        project_root=None,
    ):
        self.calls.append(
            {
                "model": model,
                "output_json": output_json,
                "integration_args": integration_args,
                "integration_options": integration_options,
                "project_root": project_root,
            }
        )
        return ["legacy-strict-stub", "-p", prompt]


class _PlainBase(IntegrationBase):
    key = "plain-stub"
    config = _CLI_CONFIG


class _TomlStub(TomlIntegration):
    key = "toml-stub"
    config = _CLI_CONFIG


class _SkillsStub(SkillsIntegration):
    key = "skills-stub"
    config = _CLI_CONFIG


@pytest.fixture
def scoped_registry():
    """Pin the registry used to list supporting integrations."""
    from specify_cli.integrations.installer import dispatch_registry

    tokens = []

    def pin(*integrations):
        tokens.append(
            dispatch_registry.set({item.key: item for item in integrations})
        )

    yield pin
    for token in reversed(tokens):
        dispatch_registry.reset(token)


def _fake_run(calls):
    def run(args, **kwargs):
        calls.append(list(args))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return run


class TestDispatchSettingsValues:
    def test_settings_are_ordered_and_named(self):
        assert DISPATCH_SETTINGS == ("reasoning_effort", "context_size")

    def test_requested_settings_use_is_not_none_semantics(self):
        assert requested_dispatch_settings() == {}
        assert requested_dispatch_settings(
            context_size="long_context", reasoning_effort="high"
        ) == {"reasoning_effort": "high", "context_size": "long_context"}
        assert list(
            requested_dispatch_settings(context_size="a", reasoning_effort="b")
        ) == ["reasoning_effort", "context_size"]
        assert requested_dispatch_settings(reasoning_effort="") == {
            "reasoning_effort": ""
        }

    @pytest.mark.parametrize(
        "value", ["low", "xhigh", "long_context", "200000", "a.b-c_d", "A" * 64]
    )
    def test_accepts_argv_safe_tokens(self, value):
        assert dispatch_setting_value_error("reasoning_effort", value) is None

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "-x",
            "--yolo",
            "x y",
            "high\n",
            "high\r",
            "a" * 65,
            "a&b",
            "a|b",
            "a;b",
            "a<b",
            "a>b",
            "a^b",
            "a\x00b",
            ".hidden",
            "_x",
        ],
    )
    def test_rejects_unsafe_tokens(self, value):
        message = dispatch_setting_value_error("reasoning_effort", value)
        assert message is not None
        assert "'reasoning_effort' must be 1-64 letters" in message

    @pytest.mark.parametrize("value", [200000, True, None, 1.5, ["high"]])
    def test_non_strings_get_a_quoting_hint(self, value):
        message = dispatch_setting_value_error("context_size", value)
        assert message is not None
        assert f"must be a string, got {type(value).__name__}" in message
        assert "quote YAML values" in message

    @pytest.mark.parametrize("value", [200000, True, 1.5, ["high"]])
    def test_non_string_expression_results_get_expression_advice(self, value):
        message = dispatch_setting_value_error(
            "context_size", value, from_expression=True
        )
        assert message == (
            "'context_size' must be a string, but its expression resolved to "
            f"{type(value).__name__}; make it resolve to a string, for example "
            "by reading an input declared with type: string."
        )

    def test_expression_flag_changes_only_the_non_string_advice(self):
        assert (
            dispatch_setting_value_error("context_size", "200000", from_expression=True)
            is None
        )
        assert dispatch_setting_value_error(
            "reasoning_effort", "-rf", from_expression=True
        ) == dispatch_setting_value_error("reasoning_effort", "-rf")

    @pytest.mark.parametrize(
        "value",
        [
            pytest.param("SECRET-api-key-0123456789 tail", id="leading-secret"),
            pytest.param("SECRET!", id="short-secret"),
            pytest.param("-SECRET", id="leading-dash"),
            pytest.param("\x1b[31m" + "x" * (1024 * 1024) + "\nSECRET", id="huge"),
        ],
    )
    @pytest.mark.parametrize("from_expression", [False, True])
    def test_malformed_values_report_only_type_and_length(
        self, value, from_expression
    ):
        """A value can be captured output, which Spec Kit does not print or log."""
        message = dispatch_setting_value_error(
            "reasoning_effort", value, from_expression=from_expression
        )

        assert message == (
            "'reasoning_effort' must be 1-64 letters, digits, '.', '_', or '-' "
            f"starting with a letter or digit, got a string of length {len(value)}."
        )
        assert "SECRET" not in message


class TestEffectiveDispatchSettings:
    @pytest.mark.parametrize("via", ["dispatch_command", "build_exec_args"])
    def test_declaring_builder_owns_its_settings(self, via):
        assert effective_dispatch_settings(
            _TranslatingIntegration(), via=via
        ) == frozenset(DISPATCH_SETTINGS)

    @pytest.mark.parametrize("via", ["dispatch_command", "build_exec_args"])
    def test_subclass_without_override_inherits_support(self, via):
        assert effective_dispatch_settings(
            _InheritingIntegration(), via=via
        ) == frozenset(DISPATCH_SETTINGS)

    @pytest.mark.parametrize(
        "integration",
        [
            _LegacyKwargsOverride(),
            _DeclaringFormatBase(),
            _StringDeclaration(),
            StubIntegration(),
        ],
        ids=["legacy-kwargs-override", "format-base", "string", "undeclared"],
    )
    @pytest.mark.parametrize("via", ["dispatch_command", "build_exec_args"])
    def test_untranslated_declarations_count_as_unsupported(self, integration, via):
        assert effective_dispatch_settings(integration, via=via) == frozenset()

    def test_dispatch_command_owner_supports_only_the_command_path(self):
        integration = _CommandOwner()

        assert effective_dispatch_settings(
            integration, via="dispatch_command"
        ) == frozenset({"reasoning_effort"})
        assert effective_dispatch_settings(
            integration, via="build_exec_args"
        ) == frozenset()

    def test_unknown_dispatch_path_is_a_programming_error(self):
        with pytest.raises(ValueError, match="Unknown dispatch path"):
            effective_dispatch_settings(_TranslatingIntegration(), via="prompt")

    def test_builtin_declarations_are_owned_by_their_receivers(self):
        from specify_cli.integrations import INTEGRATION_REGISTRY

        for key, integration in INTEGRATION_REGISTRY.items():
            for via in ("dispatch_command", "build_exec_args"):
                supported = effective_dispatch_settings(integration, via=via)
                assert supported <= set(DISPATCH_SETTINGS), key
                receiver = (
                    "dispatch_command"
                    if via == "dispatch_command"
                    and "dispatch_command" in vars(type(integration))
                    else "build_exec_args"
                )
                parameters = inspect.signature(
                    getattr(integration, receiver)
                ).parameters
                for name in supported:
                    assert name in parameters, (key, via, name)


class TestCheckDispatchSettings:
    def test_unsupported_setting_lists_no_supporters(self, scoped_registry):
        integration = _LegacyStrictBuilder()
        scoped_registry(integration)

        with pytest.raises(DispatchSettingsError) as excinfo:
            check_dispatch_settings(
                integration, {"reasoning_effort": "high"}, via="dispatch_command"
            )

        assert excinfo.value.setting == "reasoning_effort"
        message = str(excinfo.value)
        assert "'legacy-strict-stub' does not support per-step 'reasoning_effort'" in message
        assert "No available integration supports it." in message
        assert "Remove the setting from this step" in message

    def test_unsupported_setting_lists_pinned_supporters(self, scoped_registry):
        scoped_registry(
            _LegacyStrictBuilder(), _TranslatingIntegration(), _CommandOwner()
        )

        with pytest.raises(DispatchSettingsError) as excinfo:
            check_dispatch_settings(
                _LegacyStrictBuilder(),
                {"reasoning_effort": "high"},
                via="build_exec_args",
            )

        assert "Integrations that support it: translating-stub." in str(excinfo.value)

    def test_hint_is_appended_to_unsupported_error(self, scoped_registry):
        scoped_registry()

        with pytest.raises(DispatchSettingsError, match="Choose a long-context model"):
            check_dispatch_settings(
                _HintingIntegration(),
                {"context_size": "long_context"},
                via="dispatch_command",
            )

    def test_settings_are_checked_in_declared_order(self, scoped_registry):
        scoped_registry()

        with pytest.raises(DispatchSettingsError) as excinfo:
            check_dispatch_settings(
                StubIntegration(),
                {"context_size": "x y", "reasoning_effort": "x y"},
                via="build_exec_args",
            )

        assert excinfo.value.setting == "reasoning_effort"

    def test_value_errors_are_raised_before_support_errors(self):
        with pytest.raises(DispatchSettingsError, match="must be 1-64") as excinfo:
            check_dispatch_settings(
                StubIntegration(), {"context_size": "-rf"}, via="build_exec_args"
            )

        assert excinfo.value.setting == "context_size"

    @pytest.mark.parametrize(
        "integration",
        [_LegacyKwargsOverride(), _DeclaringFormatBase(), _StringDeclaration()],
        ids=["legacy-kwargs-override", "format-base", "string"],
    )
    def test_untranslated_declarations_fail_instead_of_dropping(
        self, scoped_registry, integration
    ):
        scoped_registry()

        with pytest.raises(DispatchSettingsError, match="does not support") as excinfo:
            check_dispatch_settings(
                integration, {"reasoning_effort": "high"}, via="dispatch_command"
            )

        assert excinfo.value.setting == "reasoning_effort"

    def test_declared_receiver_must_accept_the_keyword(self):
        with pytest.raises(DispatchSettingsError, match="does not accept") as excinfo:
            check_dispatch_settings(
                _DeclaresWithoutKeyword(),
                {"reasoning_effort": "high"},
                via="dispatch_command",
            )

        assert excinfo.value.setting == "reasoning_effort"

    def test_integration_value_errors_are_attributed_to_their_setting(self):
        with pytest.raises(DispatchSettingsError) as excinfo:
            check_dispatch_settings(
                _ValidatingIntegration(),
                {"reasoning_effort": "high", "context_size": "rejected"},
                via="build_exec_args",
            )

        assert excinfo.value.setting == "context_size"
        assert "context_size value is not accepted" in str(excinfo.value)
        assert isinstance(excinfo.value.__cause__, ValueError)

    def test_unlabeled_integration_errors_are_labeled(self):
        with pytest.raises(DispatchSettingsError, match="unlabeled failure") as excinfo:
            check_dispatch_settings(
                _ValidatingIntegration(),
                {"reasoning_effort": "unlabeled"},
                via="build_exec_args",
            )

        assert excinfo.value.setting == "reasoning_effort"

    def test_supported_settings_pass(self):
        check_dispatch_settings(
            _TranslatingIntegration(),
            {"reasoning_effort": "high", "context_size": "long_context"},
            via="build_exec_args",
        )
        check_dispatch_settings(
            _CommandOwner(), {"reasoning_effort": "high"}, via="dispatch_command"
        )

    def test_none_values_are_skipped(self):
        check_dispatch_settings(
            StubIntegration(),
            {"reasoning_effort": None, "context_size": None},
            via="build_exec_args",
        )

    def test_unknown_setting_names_are_programming_errors(self):
        with pytest.raises(ValueError, match="Unknown dispatch settings"):
            check_dispatch_settings(
                _TranslatingIntegration(), {"temperature": "1"}, via="build_exec_args"
            )

    def test_builtins_reject_settings_they_do_not_declare(self, scoped_registry):
        from specify_cli.integrations import INTEGRATION_REGISTRY

        scoped_registry()
        for key, integration in INTEGRATION_REGISTRY.items():
            for via in ("dispatch_command", "build_exec_args"):
                supported = effective_dispatch_settings(integration, via=via)
                for name in DISPATCH_SETTINGS:
                    if name in supported:
                        continue
                    with pytest.raises(DispatchSettingsError) as excinfo:
                        check_dispatch_settings(
                            integration, {name: "high"}, via=via
                        )
                    assert excinfo.value.setting == name, (key, via)


class TestDispatchSettingsBuilders:
    @pytest.mark.parametrize(
        "integration",
        [_PlainBase(), StubIntegration(), _TomlStub(), _SkillsStub()],
        ids=["base", "markdown", "toml", "skills"],
    )
    @pytest.mark.parametrize(
        ("settings", "expected"),
        [
            ({"reasoning_effort": "high"}, "reasoning_effort"),
            ({"context_size": "long_context"}, "context_size"),
            (
                {"reasoning_effort": "high", "context_size": "long_context"},
                "reasoning_effort",
            ),
        ],
    )
    def test_generic_builders_reject_untranslated_settings(
        self, integration, settings, expected
    ):
        with pytest.raises(DispatchSettingsError, match="does not translate") as excinfo:
            integration.build_exec_args("prompt", **settings)

        assert excinfo.value.setting == expected

    @pytest.mark.parametrize(
        "integration",
        [_PlainBase(), StubIntegration(), _TomlStub(), _SkillsStub()],
        ids=["base", "markdown", "toml", "skills"],
    )
    def test_generic_builders_are_unchanged_without_settings(self, integration):
        assert integration.build_exec_args(
            "prompt", reasoning_effort=None, context_size=None
        ) == integration.build_exec_args("prompt")

    def test_forwarding_declared_settings_to_super_fails_loudly(self):
        with pytest.raises(DispatchSettingsError, match="does not translate"):
            _ForwardsToSuper().build_exec_args("prompt", reasoning_effort="high")

    def test_command_check_probe_is_unchanged(self, tmp_path):
        from specify_cli.integrations import INTEGRATION_REGISTRY

        for key, integration in INTEGRATION_REGISTRY.items():
            try:
                integration.build_exec_args("test", project_root=tmp_path)
            except DispatchSettingsError:
                pytest.fail(f"{key}: settings-free probe hit the dispatch-settings guard")
            except ValueError:
                # Pre-existing integration requirements (e.g. Docker Agent's
                # agent reference) are unrelated to dispatch settings.
                pass


class TestDispatchCommandSettings:
    def test_unset_settings_reach_legacy_builders_unchanged(
        self, monkeypatch, tmp_path
    ):
        calls = []
        monkeypatch.setattr("subprocess.run", _fake_run(calls))
        integration = _LegacyStrictBuilder()

        result = integration.dispatch_command(
            "speckit.plan", "add auth", project_root=tmp_path
        )

        assert result["exit_code"] == 0
        assert integration.calls == [
            {
                "model": None,
                "output_json": False,
                "integration_args": None,
                "integration_options": None,
                "project_root": tmp_path,
            }
        ]
        assert calls[0][1:] == ["-p", "/speckit.plan add auth"]

    def test_only_requested_settings_are_forwarded(self, monkeypatch, tmp_path):
        calls = []
        monkeypatch.setattr("subprocess.run", _fake_run(calls))

        _TranslatingIntegration().dispatch_command(
            "speckit.plan", project_root=tmp_path, reasoning_effort="high"
        )

        assert calls[0][-2:] == ["--effort", "high"]
        assert "--context" not in calls[0]

    def test_unsupported_settings_fail_before_building_or_running(
        self, monkeypatch, scoped_registry, tmp_path
    ):
        calls = []
        monkeypatch.setattr("subprocess.run", _fake_run(calls))
        integration = _LegacyStrictBuilder()
        scoped_registry(integration)

        with pytest.raises(DispatchSettingsError, match="does not support"):
            integration.dispatch_command(
                "speckit.plan", project_root=tmp_path, context_size="long_context"
            )

        assert integration.calls == []
        assert calls == []

    def test_forwarding_to_super_fails_before_running(self, monkeypatch, tmp_path):
        calls = []
        monkeypatch.setattr("subprocess.run", _fake_run(calls))

        with pytest.raises(DispatchSettingsError, match="does not translate"):
            _ForwardsToSuper().dispatch_command(
                "speckit.plan", project_root=tmp_path, reasoning_effort="high"
            )

        assert calls == []

    def test_empty_string_is_validated_not_ignored(self, tmp_path):
        with pytest.raises(DispatchSettingsError, match="must be 1-64"):
            _TranslatingIntegration().dispatch_command(
                "speckit.plan", project_root=tmp_path, reasoning_effort=""
            )
