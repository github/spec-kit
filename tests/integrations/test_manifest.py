"""Tests for IntegrationManifest — record, hash, save, load, uninstall, modified detection."""

import hashlib
import json
import sys

import pytest

from specify_cli.integrations.manifest import IntegrationManifest, _sha256


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


class TestManifestRecordExistingErrors:
    """Error-case coverage for ``record_existing`` symlink + non-file guards.

    Added in #2483 — Copilot review flagged these as un-tested regressions
    after the ``is_symlink``/``is_file`` guards were introduced.
    """

    def test_rejects_symlink_target(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("target content", encoding="utf-8")
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        m = IntegrationManifest("test", tmp_path)
        with pytest.raises(ValueError, match="symlinked"):
            m.record_existing("link.txt")

    def test_rejects_dangling_symlink(self, tmp_path):
        # A symlink pointing nowhere should still be rejected before the
        # ``is_file()`` check (which would itself be False on a dangler).
        link = tmp_path / "dangler.txt"
        link.symlink_to(tmp_path / "no-such-target.txt")
        m = IntegrationManifest("test", tmp_path)
        with pytest.raises(ValueError, match="symlinked"):
            m.record_existing("dangler.txt")

    def test_rejects_directory_path(self, tmp_path):
        (tmp_path / "a_dir").mkdir()
        m = IntegrationManifest("test", tmp_path)
        with pytest.raises(ValueError, match="not a regular file"):
            m.record_existing("a_dir")

    def test_rejects_missing_path(self, tmp_path):
        # ``is_file()`` is False for non-existent paths too; the same error
        # surface keeps callers from having to distinguish "missing" from
        # "wrong kind" — both mean "cannot hash this".
        m = IntegrationManifest("test", tmp_path)
        with pytest.raises(ValueError, match="not a regular file"):
            m.record_existing("never-existed.txt")

    def test_lexical_prevalidation_for_absolute_path(self, tmp_path):
        # ``record_existing`` must reject absolute paths via the lexical
        # pre-check, NOT via the filesystem-touching ``is_symlink()`` call.
        # Verified by passing an absolute path that points to a directory
        # outside the project root — the canonical "Absolute paths" error
        # must surface before any stat on the absolute path.
        m = IntegrationManifest("test", tmp_path)
        abs_path = "C:\\tmp\\escape.txt" if sys.platform == "win32" else "/tmp/escape.txt"
        with pytest.raises(ValueError, match="Absolute paths"):
            m.record_existing(abs_path)


class TestManifestPathTraversal:
    def test_record_file_rejects_parent_traversal(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        with pytest.raises(ValueError, match="outside"):
            m.record_file("../escape.txt", "bad")

    def test_record_file_rejects_absolute_path(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        abs_path = "C:\\tmp\\escape.txt" if sys.platform == "win32" else "/tmp/escape.txt"
        with pytest.raises(ValueError, match="Absolute paths"):
            m.record_file(abs_path, "bad")

    def test_record_existing_rejects_parent_traversal(self, tmp_path):
        escape = tmp_path.parent / "escape.txt"
        escape.write_text("evil", encoding="utf-8")
        try:
            m = IntegrationManifest("test", tmp_path)
            with pytest.raises(ValueError, match="outside"):
                m.record_existing("../escape.txt")
        finally:
            escape.unlink(missing_ok=True)

    def test_uninstall_skips_traversal_paths(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("safe.txt", "good")
        m._files["../outside.txt"] = "fakehash"
        m.save()
        removed, skipped = m.uninstall()
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
        assert not (tmp_path / "a").exists()

    def test_preserves_nonempty_parent_dirs(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("a/b/tracked.txt", "content")
        (tmp_path / "a" / "b" / "other.txt").write_text("keep", encoding="utf-8")
        m.save()
        m.uninstall()
        assert not (tmp_path / "a" / "b" / "tracked.txt").exists()
        assert (tmp_path / "a" / "b" / "other.txt").exists()

    def test_symlink_skipped_without_force(self, tmp_path):
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

    def test_symlink_removed_with_force(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "original")
        m.save()
        target = tmp_path / "target.txt"
        target.write_text("target", encoding="utf-8")
        (tmp_path / "f.txt").unlink()
        (tmp_path / "f.txt").symlink_to(target)
        removed, skipped = m.uninstall(force=True)
        assert len(removed) == 1
        assert target.exists()


class TestManifestPersistence:
    def test_save_and_load_roundtrip(self, tmp_path):
        m = IntegrationManifest("myagent", tmp_path, version="2.0.1")
        m.record_file("dir/file.md", "# Hello")
        m.save()
        loaded = IntegrationManifest.load("myagent", tmp_path)
        assert loaded.key == "myagent"
        assert loaded.version == "2.0.1"
        assert loaded.files == m.files

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

    def test_save_preserves_installed_at(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "content")
        m.save()
        first_ts = m._installed_at
        m.save()
        assert m._installed_at == first_ts


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


class TestManifestRecoveredFiles:
    """Coverage for the ``recovered_files`` channel added in #2483.

    When ``shared_infra`` skips an existing file (because the user already has
    it on disk) it now records the file with ``recovered=True``. The path
    appears in ``manifest.recovered_files`` and ``is_recovered(path)`` returns
    True. ``refresh_managed`` (out of scope for this PR) consults this list
    before treating the recorded hash as a managed baseline, defending against
    silent overwrite of user customizations after manifest loss.
    """

    def test_record_existing_default_is_not_recovered(self, tmp_path):
        (tmp_path / "f.txt").write_text("x", encoding="utf-8")
        m = IntegrationManifest("test", tmp_path)
        m.record_existing("f.txt")
        assert m.is_recovered("f.txt") is False
        assert m.recovered_files == set()

    def test_record_existing_with_recovered_flag(self, tmp_path):
        (tmp_path / "f.txt").write_text("x", encoding="utf-8")
        m = IntegrationManifest("test", tmp_path)
        m.record_existing("f.txt", recovered=True)
        assert m.is_recovered("f.txt") is True
        assert m.recovered_files == {"f.txt"}
        # File still hashed normally so check_modified/uninstall keep working
        assert m.files["f.txt"] == _sha256(tmp_path / "f.txt")

    def test_recovered_files_round_trips_through_save_load(self, tmp_path):
        (tmp_path / "a.txt").write_text("aaa", encoding="utf-8")
        (tmp_path / "b.txt").write_text("bbb", encoding="utf-8")
        m = IntegrationManifest("test", tmp_path, version="9.9")
        m.record_existing("a.txt", recovered=True)
        m.record_existing("b.txt")  # not recovered
        m.save()
        loaded = IntegrationManifest.load("test", tmp_path)
        assert loaded.is_recovered("a.txt") is True
        assert loaded.is_recovered("b.txt") is False
        assert loaded.recovered_files == {"a.txt"}

    def test_save_omits_empty_recovered_files(self, tmp_path):
        m = IntegrationManifest("test", tmp_path)
        m.record_file("f.txt", "x")
        path = m.save()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "recovered_files" not in data

    def test_load_rejects_non_list_recovered_files(self, tmp_path):
        path = tmp_path / ".specify" / "integrations" / "bad.manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps({"files": {}, "recovered_files": "not-a-list"}),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="recovered_files"):
            IntegrationManifest.load("bad", tmp_path)


class TestRecordExistingNewGuards:
    """Coverage for the two new guards added by Copilot's 2026-05-18 review."""

    def test_rejects_symlinked_ancestor(self, tmp_path):
        real_dir = tmp_path / "real_dir"
        real_dir.mkdir()
        (real_dir / "file.txt").write_text("payload", encoding="utf-8")
        (tmp_path / "linked_dir").symlink_to(real_dir, target_is_directory=True)
        m = IntegrationManifest("test", tmp_path)
        with pytest.raises(ValueError, match="symlinked"):
            m.record_existing("linked_dir/file.txt")

    def test_rejects_inside_root_dotdot_with_explicit_message(self, tmp_path):
        # ``dir/../file.txt`` normalizes inside root, so the old "escapes
        # project root" message was misleading. The new message names the
        # actual reason: canonicalization.
        (tmp_path / "dir").mkdir()
        (tmp_path / "file.txt").write_text("x", encoding="utf-8")
        m = IntegrationManifest("test", tmp_path)
        with pytest.raises(ValueError, match=r"canonical|'\.\.' segments"):
            m.record_existing("dir/../file.txt")
