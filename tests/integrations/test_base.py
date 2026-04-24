"""Tests for IntegrationOption, IntegrationBase, MarkdownIntegration, and primitives."""

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
        assert i.context_file == "STUB.md"

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
