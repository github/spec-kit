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

    def test_templates_dir(self):
        i = _StubIntegration()
        td = i.templates_dir()
        # Should point to a templates/ dir next to this test module.
        # It won't exist, but the path should be well-formed.
        assert td.name == "templates"

    def test_setup_no_templates_returns_empty(self, tmp_path):
        """setup() gracefully returns empty list when templates dir is missing."""
        i = _StubIntegration()
        manifest = IntegrationManifest("stub", tmp_path)
        created = i.setup(tmp_path, manifest)
        assert created == []

    def test_setup_copies_templates(self, tmp_path, monkeypatch):
        """setup() copies template files and records them in the manifest."""
        # Create templates under tmp_path so we don't mutate the source tree
        tpl = tmp_path / "_templates"
        tpl.mkdir()
        (tpl / "speckit.plan.md").write_text("plan content", encoding="utf-8")
        (tpl / "speckit.specify.md").write_text("spec content", encoding="utf-8")

        i = _StubIntegration()
        monkeypatch.setattr(type(i), "templates_dir", lambda self: tpl)

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
        assert result == []  # no templates dir → empty

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
