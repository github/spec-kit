"""Tests for the integrations foundation (Stage 1).

Covers:
- IntegrationOption dataclass
- IntegrationBase ABC and MarkdownIntegration base class
- IntegrationManifest — record, hash, save, load, uninstall, modified detection
- INTEGRATION_REGISTRY basics
"""

import hashlib
import json

import pytest

from specify_cli.integrations import (
    INTEGRATION_REGISTRY,
    _register,
    get_integration,
)
from specify_cli.integrations.base import (
    IntegrationBase,
    IntegrationOption,
    MarkdownIntegration,
)
from specify_cli.integrations.manifest import IntegrationManifest, _sha256


# ── helpers ──────────────────────────────────────────────────────────────────


class _StubIntegration(MarkdownIntegration):
    """Minimal concrete integration for testing."""

    key = "stub"
    config = {
        "name": "Stub Agent",
        "folder": ".stub/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".stub/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "STUB.md"


# ═══════════════════════════════════════════════════════════════════════════
# IntegrationOption
# ═══════════════════════════════════════════════════════════════════════════


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


# ═══════════════════════════════════════════════════════════════════════════
# IntegrationBase / MarkdownIntegration
# ═══════════════════════════════════════════════════════════════════════════


class TestIntegrationBase:
    def test_key_and_config(self):
        i = _StubIntegration()
        assert i.key == "stub"
        assert i.config["name"] == "Stub Agent"
        assert i.registrar_config["format"] == "markdown"
        assert i.context_file == "STUB.md"

    def test_options_default_empty(self):
        assert _StubIntegration.options() == []

    def test_shared_commands_dir(self):
        i = _StubIntegration()
        cmd_dir = i.shared_commands_dir()
        # Should find the shared templates/commands/ directory
        assert cmd_dir is not None
        assert cmd_dir.is_dir()

    def test_setup_uses_shared_templates(self, tmp_path):
        """setup() copies shared command templates into the agent's directory."""
        i = _StubIntegration()
        manifest = IntegrationManifest("stub", tmp_path)
        created = i.setup(tmp_path, manifest)
        assert len(created) > 0
        for f in created:
            assert f.parent == tmp_path / ".stub" / "commands"
            assert f.name.startswith("speckit.")
            assert f.name.endswith(".md")

    def test_setup_copies_templates(self, tmp_path, monkeypatch):
        """setup() copies template files and records them in the manifest."""
        # Create custom templates under tmp_path
        tpl = tmp_path / "_templates"
        tpl.mkdir()
        (tpl / "plan.md").write_text("plan content", encoding="utf-8")
        (tpl / "specify.md").write_text("spec content", encoding="utf-8")

        i = _StubIntegration()
        monkeypatch.setattr(type(i), "list_command_templates", lambda self: sorted(tpl.glob("*.md")))

        project = tmp_path / "project"
        project.mkdir()
        created = i.setup(project, IntegrationManifest("stub", project))
        assert len(created) == 2
        assert (project / ".stub" / "commands" / "speckit.plan.md").exists()
        assert (project / ".stub" / "commands" / "speckit.specify.md").exists()

    def test_install_delegates_to_setup(self, tmp_path):
        i = _StubIntegration()
        manifest = IntegrationManifest("stub", tmp_path)
        result = i.install(tmp_path, manifest)
        # Uses shared templates, so should create files
        assert len(result) > 0

    def test_uninstall_delegates_to_teardown(self, tmp_path):
        i = _StubIntegration()
        manifest = IntegrationManifest("stub", tmp_path)
        removed, skipped = i.uninstall(tmp_path, manifest)
        assert removed == []
        assert skipped == []


class TestMarkdownIntegration:
    def test_is_subclass_of_base(self):
        assert issubclass(MarkdownIntegration, IntegrationBase)

    def test_stub_is_markdown(self):
        assert isinstance(_StubIntegration(), MarkdownIntegration)


# ═══════════════════════════════════════════════════════════════════════════
# IntegrationManifest
# ═══════════════════════════════════════════════════════════════════════════


class TestManifestRecordFile:
    def test_record_file_writes_and_hashes(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        content = "hello world"
        abs_path = m.record_file("a/b.txt", content)

        assert abs_path == tmp_path / "a" / "b.txt"
        assert abs_path.read_text(encoding="utf-8") == content
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        assert m.files["a/b.txt"] == expected_hash

    def test_record_file_bytes(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        data = b"\x00\x01\x02"
        abs_path = m.record_file("bin.dat", data)
        assert abs_path.read_bytes() == data
        assert m.files["bin.dat"] == hashlib.sha256(data).hexdigest()

    def test_record_existing(self, tmp_path):
        f = tmp_path / "existing.txt"
        f.write_text("content", encoding="utf-8")
        m = IntegrationManifest("test", tmp_path)
        m.record_existing("existing.txt")
        assert m.files["existing.txt"] == _sha256(f)


class TestManifestPathTraversal:
    def test_record_file_rejects_parent_traversal(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        with pytest.raises(ValueError, match="outside"):
            m.record_file("../escape.txt", "bad")

    def test_record_file_rejects_absolute_path(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        with pytest.raises(ValueError, match="Absolute paths"):
            m.record_file("/tmp/escape.txt", "bad")

    def test_record_existing_rejects_parent_traversal(self, tmp_path):
        # Create a file outside the project root
        escape = tmp_path.parent / "escape.txt"
        escape.write_text("evil", encoding="utf-8")
        try:
            m = IntegrationManifest("test", tmp_path)
            with pytest.raises(ValueError, match="outside"):
                m.record_existing("../escape.txt")
        finally:
            escape.unlink(missing_ok=True)

    def test_uninstall_skips_traversal_paths(self, tmp_path):
        """If a manifest is corrupted with traversal paths, uninstall ignores them."""
        m = IntegrationManifest("test", tmp_path)
        m.record_file("safe.txt", "good")
        # Manually inject a traversal path into the manifest
        m._files["../outside.txt"] = "fakehash"
        m.save()

        removed, skipped = m.uninstall()
        # Only the safe file should have been removed
        assert len(removed) == 1
        assert removed[0].name == "safe.txt"


class TestManifestCheckModified:
    def test_unmodified_file(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "original")
        assert m.check_modified() == []

    def test_modified_file(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "original")
        (tmp_path / "f.txt").write_text("changed", encoding="utf-8")
        assert m.check_modified() == ["f.txt"]

    def test_deleted_file_not_reported(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "original")
        (tmp_path / "f.txt").unlink()
        assert m.check_modified() == []

    def test_symlink_treated_as_modified(self, tmp_path):
        """A tracked file replaced with a symlink is reported as modified."""
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "original")
        target = tmp_path / "target.txt"
        target.write_text("target", encoding="utf-8")
        (tmp_path / "f.txt").unlink()
        (tmp_path / "f.txt").symlink_to(target)
        assert m.check_modified() == ["f.txt"]


class TestManifestUninstall:
    def test_removes_unmodified(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("d/f.txt", "content")
        m.save()

        removed, skipped = m.uninstall()
        assert len(removed) == 1
        assert not (tmp_path / "d" / "f.txt").exists()
        # Parent dir cleaned up because empty
        assert not (tmp_path / "d").exists()
        assert skipped == []

    def test_skips_modified(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "original")
        m.save()
        (tmp_path / "f.txt").write_text("modified", encoding="utf-8")

        removed, skipped = m.uninstall()
        assert removed == []
        assert len(skipped) == 1
        assert (tmp_path / "f.txt").exists()

    def test_force_removes_modified(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "original")
        m.save()
        (tmp_path / "f.txt").write_text("modified", encoding="utf-8")

        removed, skipped = m.uninstall(force=True)
        assert len(removed) == 1
        assert skipped == []
        assert not (tmp_path / "f.txt").exists()

    def test_already_deleted_file(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "content")
        m.save()
        (tmp_path / "f.txt").unlink()

        removed, skipped = m.uninstall()
        assert removed == []
        assert skipped == []

    def test_removes_manifest_file(self, tmp_path):
        m = IntegrationManifest("test", tmp_path, version="1.0")
        m.record_file("f.txt", "content")
        m.save()
        assert m.manifest_path.exists()

        m.uninstall()
        assert not m.manifest_path.exists()

    def test_cleans_empty_parent_dirs(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("a/b/c/f.txt", "content")
        m.save()

        m.uninstall()
        assert not (tmp_path / "a" / "b" / "c").exists()
        assert not (tmp_path / "a" / "b").exists()
        assert not (tmp_path / "a").exists()

    def test_preserves_nonempty_parent_dirs(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("a/b/tracked.txt", "content")
        # Create an untracked sibling
        (tmp_path / "a" / "b" / "other.txt").write_text("keep", encoding="utf-8")
        m.save()

        m.uninstall()
        assert not (tmp_path / "a" / "b" / "tracked.txt").exists()
        assert (tmp_path / "a" / "b" / "other.txt").exists()
        assert (tmp_path / "a" / "b").is_dir()

    def test_symlink_skipped_without_force(self, tmp_path):
        """A tracked file replaced with a symlink is skipped unless force."""
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "original")
        m.save()
        target = tmp_path / "target.txt"
        target.write_text("target", encoding="utf-8")
        (tmp_path / "f.txt").unlink()
        (tmp_path / "f.txt").symlink_to(target)

        removed, skipped = m.uninstall()
        assert removed == []
        assert len(skipped) == 1
        assert (tmp_path / "f.txt").is_symlink()  # still there

    def test_symlink_removed_with_force(self, tmp_path):
        """A tracked file replaced with a symlink is removed with force."""
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "original")
        m.save()
        target = tmp_path / "target.txt"
        target.write_text("target", encoding="utf-8")
        (tmp_path / "f.txt").unlink()
        (tmp_path / "f.txt").symlink_to(target)

        removed, skipped = m.uninstall(force=True)
        assert len(removed) == 1
        assert not (tmp_path / "f.txt").exists()
        assert target.exists()  # target not deleted


class TestManifestPersistence:
    def test_save_and_load_roundtrip(self, tmp_path):
        m = IntegrationManifest("myagent", tmp_path, version="2.0.1")
        m.record_file("dir/file.md", "# Hello")
        m.save()

        loaded = IntegrationManifest.load("myagent", tmp_path)
        assert loaded.key == "myagent"
        assert loaded.version == "2.0.1"
        assert loaded.files == m.files
        assert loaded._installed_at == m._installed_at

    def test_manifest_path(self, tmp_path):
        m = IntegrationManifest("copilot", tmp_path)
        assert m.manifest_path == tmp_path / ".specify" / "integrations" / "copilot.manifest.json"

    def test_load_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            IntegrationManifest.load("nonexistent", tmp_path)

    def test_save_creates_directories(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "content")
        path = m.save()
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["integration"] == "test"
        assert "installed_at" in data
        assert "f.txt" in data["files"]

    def test_save_preserves_installed_at(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "content")
        m.save()
        first_ts = m._installed_at

        # Save again — timestamp should not change
        m.save()
        assert m._installed_at == first_ts


# ═══════════════════════════════════════════════════════════════════════════
# Registry
# ═══════════════════════════════════════════════════════════════════════════


class TestRegistry:
    def test_registry_starts_empty(self):
        # Registry may have been populated by other tests; at minimum
        # it should be a dict.
        assert isinstance(INTEGRATION_REGISTRY, dict)

    def test_register_and_get(self):
        stub = _StubIntegration()
        _register(stub)
        try:
            assert get_integration("stub") is stub
        finally:
            INTEGRATION_REGISTRY.pop("stub", None)

    def test_get_missing_returns_none(self):
        assert get_integration("nonexistent-xyz") is None

    def test_register_empty_key_raises(self):
        class EmptyKey(MarkdownIntegration):
            key = ""
        with pytest.raises(ValueError, match="empty key"):
            _register(EmptyKey())

    def test_register_duplicate_raises(self):
        stub = _StubIntegration()
        _register(stub)
        try:
            with pytest.raises(KeyError, match="already registered"):
                _register(_StubIntegration())
        finally:
            INTEGRATION_REGISTRY.pop("stub", None)


class TestManifestLoadValidation:
    def test_load_non_dict_raises(self, tmp_path):
        path = tmp_path / ".specify" / "integrations" / "bad.manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text('"just a string"', encoding="utf-8")
        with pytest.raises(ValueError, match="JSON object"):
            IntegrationManifest.load("bad", tmp_path)

    def test_load_bad_files_type_raises(self, tmp_path):
        path = tmp_path / ".specify" / "integrations" / "bad.manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"files": ["not", "a", "dict"]}), encoding="utf-8")
        with pytest.raises(ValueError, match="mapping"):
            IntegrationManifest.load("bad", tmp_path)

    def test_load_bad_files_values_raises(self, tmp_path):
        path = tmp_path / ".specify" / "integrations" / "bad.manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"files": {"a.txt": 123}}), encoding="utf-8")
        with pytest.raises(ValueError, match="mapping"):
            IntegrationManifest.load("bad", tmp_path)

    def test_load_invalid_json_raises(self, tmp_path):
        path = tmp_path / ".specify" / "integrations" / "bad.manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ValueError, match="invalid JSON"):
            IntegrationManifest.load("bad", tmp_path)


# ═══════════════════════════════════════════════════════════════════════════
# Base class primitives
# ═══════════════════════════════════════════════════════════════════════════


class TestBasePrimitives:
    def test_shared_commands_dir_returns_path(self):
        i = _StubIntegration()
        cmd_dir = i.shared_commands_dir()
        assert cmd_dir is not None
        assert cmd_dir.is_dir()

    def test_shared_templates_dir_returns_path(self):
        i = _StubIntegration()
        tpl_dir = i.shared_templates_dir()
        assert tpl_dir is not None
        assert tpl_dir.is_dir()

    def test_list_command_templates_returns_md_files(self):
        i = _StubIntegration()
        templates = i.list_command_templates()
        assert len(templates) > 0
        assert all(t.suffix == ".md" for t in templates)

    def test_command_filename_default(self):
        i = _StubIntegration()
        assert i.command_filename("plan") == "speckit.plan.md"

    def test_commands_dest(self, tmp_path):
        i = _StubIntegration()
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
        i = _StubIntegration()
        m = IntegrationManifest("stub", tmp_path)
        created = i.setup(tmp_path, m)
        assert len(created) > 0
        # All files should be in .stub/commands/ with speckit.*.md naming
        for f in created:
            assert f.parent.name == "commands"
            assert f.name.startswith("speckit.")
            assert f.name.endswith(".md")


# ═══════════════════════════════════════════════════════════════════════════
# CopilotIntegration
# ═══════════════════════════════════════════════════════════════════════════


class TestCopilotIntegration:
    def test_copilot_registered(self):
        assert "copilot" in INTEGRATION_REGISTRY

    def test_copilot_key_and_config(self):
        copilot = get_integration("copilot")
        assert copilot is not None
        assert copilot.key == "copilot"
        assert copilot.config["folder"] == ".github/"
        assert copilot.config["commands_subdir"] == "agents"
        assert copilot.registrar_config["extension"] == ".agent.md"
        assert copilot.context_file == ".github/copilot-instructions.md"

    def test_command_filename_agent_md(self):
        copilot = get_integration("copilot")
        assert copilot.command_filename("plan") == "speckit.plan.agent.md"

    def test_setup_creates_agent_md_files(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.setup(tmp_path, m)
        assert len(created) > 0

        agent_files = [f for f in created if f.suffix == ".md" and ".agent." in f.name]
        assert len(agent_files) > 0
        for f in agent_files:
            assert f.parent == tmp_path / ".github" / "agents"
            assert f.name.startswith("speckit.")
            assert f.name.endswith(".agent.md")

    def test_setup_creates_companion_prompts(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.setup(tmp_path, m)

        prompt_files = [f for f in created if f.parent.name == "prompts"]
        assert len(prompt_files) > 0
        for f in prompt_files:
            assert f.parent == tmp_path / ".github" / "prompts"
            assert f.name.endswith(".prompt.md")
            content = f.read_text(encoding="utf-8")
            assert content.startswith("---\nagent: speckit.")
            assert content.endswith("\n---\n")

    def test_agent_and_prompt_counts_match(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.setup(tmp_path, m)

        agents = [f for f in created if ".agent.md" in f.name]
        prompts = [f for f in created if ".prompt.md" in f.name]
        assert len(agents) == len(prompts)

    def test_setup_creates_vscode_settings_new(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.setup(tmp_path, m)

        settings = tmp_path / ".vscode" / "settings.json"
        if copilot._vscode_settings_path():
            assert settings.exists()
            assert settings in created
            # Should be tracked in manifest since it was newly created
            assert any("settings.json" in k for k in m.files)

    def test_setup_merges_existing_vscode_settings(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()

        # Pre-create settings with user content
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir(parents=True)
        existing = {"editor.fontSize": 14, "custom.setting": True}
        (vscode_dir / "settings.json").write_text(
            json.dumps(existing, indent=4), encoding="utf-8"
        )

        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.setup(tmp_path, m)

        settings = tmp_path / ".vscode" / "settings.json"
        if copilot._vscode_settings_path():
            data = json.loads(settings.read_text(encoding="utf-8"))
            # User settings preserved
            assert data["editor.fontSize"] == 14
            assert data["custom.setting"] is True
            # Merged settings should NOT be tracked (existing file)
            assert settings not in created
            assert not any("settings.json" in k for k in m.files)

    def test_all_created_files_tracked_in_manifest(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        created = copilot.setup(tmp_path, m)

        for f in created:
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"Created file {rel} not tracked in manifest"

    def test_install_uninstall_roundtrip(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)

        created = copilot.install(tmp_path, m)
        assert len(created) > 0
        m.save()

        # All created files exist
        for f in created:
            assert f.exists(), f"Missing after install: {f}"

        # Uninstall removes them
        removed, skipped = copilot.uninstall(tmp_path, m)
        assert len(removed) == len(created)
        assert skipped == []
        for f in created:
            assert not f.exists(), f"Still exists after uninstall: {f}"

    def test_modified_file_survives_uninstall(self, tmp_path):
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)

        created = copilot.install(tmp_path, m)
        m.save()

        # Modify one file
        modified_file = created[0]
        modified_file.write_text("user modified this", encoding="utf-8")

        removed, skipped = copilot.uninstall(tmp_path, m)
        assert modified_file.exists()
        assert modified_file in skipped

    def test_directory_structure(self, tmp_path):
        """Verify the complete directory structure matches copilot conventions."""
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        copilot.setup(tmp_path, m)

        # .github/agents/ must exist with .agent.md files
        agents_dir = tmp_path / ".github" / "agents"
        assert agents_dir.is_dir()
        agent_files = sorted(agents_dir.glob("speckit.*.agent.md"))
        assert len(agent_files) == 9  # 9 command templates

        # Expected command names
        expected_commands = {
            "analyze", "checklist", "clarify", "constitution",
            "implement", "plan", "specify", "tasks", "taskstoissues",
        }
        actual_commands = {f.name.removeprefix("speckit.").removesuffix(".agent.md") for f in agent_files}
        assert actual_commands == expected_commands

        # .github/prompts/ must exist with matching .prompt.md files
        prompts_dir = tmp_path / ".github" / "prompts"
        assert prompts_dir.is_dir()
        prompt_files = sorted(prompts_dir.glob("speckit.*.prompt.md"))
        assert len(prompt_files) == 9

        # Each agent file must have a matching prompt file
        for agent_file in agent_files:
            cmd_name = agent_file.name.removesuffix(".agent.md")
            prompt_file = prompts_dir / f"{cmd_name}.prompt.md"
            assert prompt_file.exists(), f"Missing prompt for {cmd_name}"

        # .vscode/settings.json should exist (new project)
        settings = tmp_path / ".vscode" / "settings.json"
        if copilot._vscode_settings_path():
            assert settings.exists()
            data = json.loads(settings.read_text(encoding="utf-8"))
            assert "chat.promptFilesRecommendations" in data

        # Only expected top-level directories
        top_dirs = {d.name for d in tmp_path.iterdir() if d.is_dir()}
        expected = {".github", ".vscode", ".specify"}
        assert top_dirs.issubset(expected)

    def test_templates_are_processed(self, tmp_path):
        """Verify raw placeholders are replaced in generated command files."""
        from specify_cli.integrations.copilot import CopilotIntegration
        copilot = CopilotIntegration()
        m = IntegrationManifest("copilot", tmp_path)
        copilot.setup(tmp_path, m)

        agents_dir = tmp_path / ".github" / "agents"
        for agent_file in agents_dir.glob("speckit.*.agent.md"):
            content = agent_file.read_text(encoding="utf-8")
            # No raw placeholders should remain
            assert "{SCRIPT}" not in content, f"{agent_file.name} has unprocessed {{SCRIPT}}"
            assert "__AGENT__" not in content, f"{agent_file.name} has unprocessed __AGENT__"
            assert "{ARGS}" not in content, f"{agent_file.name} has unprocessed {{ARGS}}"
            # scripts: block should be stripped from frontmatter
            assert "\nscripts:\n" not in content, f"{agent_file.name} has raw scripts: block"
            assert "\nagent_scripts:\n" not in content, f"{agent_file.name} has raw agent_scripts: block"
            # Paths should be rewritten
            assert "scripts/bash/" not in content or ".specify/scripts/bash/" in content


# ═══════════════════════════════════════════════════════════════════════════
# CLI --integration flag (Stage 2b)
# ═══════════════════════════════════════════════════════════════════════════


class TestInitIntegrationFlag:
    """Tests for the --integration flag on specify init."""

    def test_integration_and_ai_mutually_exclusive(self):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        result = runner.invoke(app, [
            "init", "test-project",
            "--ai", "claude",
            "--integration", "copilot",
        ])
        assert result.exit_code != 0
        assert "mutually exclusive" in result.output

    def test_unknown_integration_rejected(self):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        result = runner.invoke(app, [
            "init", "test-project",
            "--integration", "nonexistent",
        ])
        assert result.exit_code != 0
        assert "Unknown integration" in result.output

    def test_integration_copilot_creates_files(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        result = runner.invoke(app, [
            "init", "--here",
            "--integration", "copilot",
            "--script", "sh",
            "--no-git",
        ], catch_exceptions=False, env={"HOME": str(tmp_path)})
        # The init command runs in CWD, which for CliRunner is OS cwd.
        # Use a different approach: create project in a named dir
        project = tmp_path / "int-test"
        project.mkdir()
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "init", "--here",
                "--integration", "copilot",
                "--script", "sh",
                "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, f"init failed: {result.output}"

        # Copilot-specific files
        assert (project / ".github" / "agents" / "speckit.plan.agent.md").exists()
        assert (project / ".github" / "prompts" / "speckit.plan.prompt.md").exists()

        # Shared infrastructure
        assert (project / ".specify" / "scripts" / "bash" / "common.sh").exists()
        assert (project / ".specify" / "templates" / "spec-template.md").exists()

        # integration.json
        integration_json = project / ".specify" / "integration.json"
        assert integration_json.exists()
        data = json.loads(integration_json.read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"

        # init-options.json
        init_opts = project / ".specify" / "init-options.json"
        assert init_opts.exists()
        opts = json.loads(init_opts.read_text(encoding="utf-8"))
        assert opts["integration"] == "copilot"
        assert opts["ai"] == "copilot"

        # Manifest recorded
        manifest = project / ".specify" / "integrations" / "copilot.manifest.json"
        assert manifest.exists()

        # Integration-specific scripts installed
        update_script = project / ".specify" / "integrations" / "copilot" / "scripts" / "update-context.sh"
        assert update_script.exists()

        # integration.json has script paths
        assert "scripts" in data
        assert "update-context" in data["scripts"]

        # Shared infrastructure manifest
        shared_manifest = project / ".specify" / "integrations" / "speckit.manifest.json"
        assert shared_manifest.exists()
        shared_data = json.loads(shared_manifest.read_text(encoding="utf-8"))
        assert shared_data["integration"] == "speckit"
        assert len(shared_data["files"]) > 0

    def test_ai_copilot_auto_promotes(self, tmp_path):
        """--ai copilot should auto-promote to integration path with a nudge."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "promote-test"
        project.mkdir()
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here",
                "--ai", "copilot",
                "--script", "sh",
                "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, f"init failed: {result.output}"
        # Should show the migration nudge
        assert "--integration copilot" in result.output
        # Should still produce copilot files via integration path
        assert (project / ".github" / "agents" / "speckit.plan.agent.md").exists()

    def test_complete_file_inventory(self, tmp_path):
        """Every file produced by --integration copilot is accounted for."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "inventory-test"
        project.mkdir()
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here",
                "--integration", "copilot",
                "--script", "sh",
                "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, f"init failed: {result.output}"

        actual_files = sorted(
            str(p.relative_to(project))
            for p in project.rglob("*") if p.is_file()
        )

        expected_files = sorted([
            # Copilot agent commands (9)
            ".github/agents/speckit.analyze.agent.md",
            ".github/agents/speckit.checklist.agent.md",
            ".github/agents/speckit.clarify.agent.md",
            ".github/agents/speckit.constitution.agent.md",
            ".github/agents/speckit.implement.agent.md",
            ".github/agents/speckit.plan.agent.md",
            ".github/agents/speckit.specify.agent.md",
            ".github/agents/speckit.tasks.agent.md",
            ".github/agents/speckit.taskstoissues.agent.md",
            # Companion prompts (9)
            ".github/prompts/speckit.analyze.prompt.md",
            ".github/prompts/speckit.checklist.prompt.md",
            ".github/prompts/speckit.clarify.prompt.md",
            ".github/prompts/speckit.constitution.prompt.md",
            ".github/prompts/speckit.implement.prompt.md",
            ".github/prompts/speckit.plan.prompt.md",
            ".github/prompts/speckit.specify.prompt.md",
            ".github/prompts/speckit.tasks.prompt.md",
            ".github/prompts/speckit.taskstoissues.prompt.md",
            # VS Code settings
            ".vscode/settings.json",
            # Integration metadata
            ".specify/integration.json",
            ".specify/init-options.json",
            ".specify/integrations/copilot.manifest.json",
            ".specify/integrations/speckit.manifest.json",
            # Integration-specific scripts
            ".specify/integrations/copilot/scripts/update-context.ps1",
            ".specify/integrations/copilot/scripts/update-context.sh",
            # Shared scripts (bash)
            ".specify/scripts/bash/check-prerequisites.sh",
            ".specify/scripts/bash/common.sh",
            ".specify/scripts/bash/create-new-feature.sh",
            ".specify/scripts/bash/setup-plan.sh",
            ".specify/scripts/bash/update-agent-context.sh",
            # Shared templates
            ".specify/templates/agent-file-template.md",
            ".specify/templates/checklist-template.md",
            ".specify/templates/constitution-template.md",
            ".specify/templates/plan-template.md",
            ".specify/templates/spec-template.md",
            ".specify/templates/tasks-template.md",
            # Constitution (copied from template)
            ".specify/memory/constitution.md",
        ])

        assert actual_files == expected_files, (
            f"File inventory mismatch.\n"
            f"Missing: {sorted(set(expected_files) - set(actual_files))}\n"
            f"Extra: {sorted(set(actual_files) - set(expected_files))}"
        )
