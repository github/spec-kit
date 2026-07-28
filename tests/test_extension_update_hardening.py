from specify_cli.extensions import ExtensionManager, ExtensionRegistry, ExtensionCatalog
from pathlib import Path
import pytest
import shutil
import yaml
from typer.testing import CliRunner
from specify_cli import app

runner = CliRunner()


def _valid_update_manifest(version="1.1.0", command_name="speckit.test-ext.run"):
    """Return a manifest accepted by normal install preflight validation."""
    return {
        "schema_version": "1.0",
        "extension": {
            "id": "test-ext",
            "name": "Test Ext",
            "version": version,
            "description": "Update hardening test extension",
        },
        "requires": {"speckit_version": ">=0"},
        "provides": {
            "commands": [
                {
                    "name": command_name,
                    "file": "commands/run.md",
                }
            ]
        },
    }


def _write_update_zip(zip_path, *, version="1.1.0", manifest=None):
    """Create the minimal archive required by the update preflight."""
    import zipfile

    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "extension.yml",
            yaml.safe_dump(
                manifest
                if manifest is not None
                else _valid_update_manifest(version=version)
            ),
        )


def _stub_available_update(monkeypatch, registry_entry):
    """Stub discovery for one installed extension with an available update."""
    monkeypatch.setattr(
        ExtensionManager,
        "list_installed",
        lambda self: [
            {"id": "test-ext", "name": "Test Ext", "version": "1.0.0"}
        ],
    )
    monkeypatch.setattr(
        ExtensionRegistry, "get", lambda self, ext_id: registry_entry
    )
    monkeypatch.setattr(
        ExtensionCatalog,
        "get_extension_info",
        lambda self, ext_id: {
            "id": "test-ext",
            "name": "Test Ext",
            "version": "1.1.0",
            "download_url": "https://example.com/ext.zip",
        },
    )
    monkeypatch.setattr("typer.confirm", lambda _: True)


def _update_backup_dirs(project_dir):
    """Return per-attempt update backups created for test-ext."""
    backup_root = (
        project_dir / ".specify" / "extensions" / ".backup"
    )
    if not backup_root.is_dir():
        return []
    return list(backup_root.glob("update-*-*"))


@pytest.fixture
def project_dir(tmp_path):
    """Create a mock spec-kit project directory."""
    proj_dir = tmp_path / "project"
    proj_dir.mkdir()
    (proj_dir / ".specify").mkdir()
    # Create required files for a project
    (proj_dir / ".specify" / "config.toml").write_text("ai = 'claude'")
    return proj_dir

def test_extension_update_corrupted_config_root(project_dir, monkeypatch):
    """Regression: extension update must handle corrupted extensions.yml (root is scalar)."""
    # chdir into project_dir so _require_specify_project() succeeds
    monkeypatch.chdir(project_dir)

    # Corrupt extensions.yml
    config_path = project_dir / ".specify" / "extensions.yml"
    config_path.write_text(yaml.dump(123))

    # Mock ExtensionManager to return an installed extension for resolution

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [{"id": "test-ext", "name": "Test Ext", "version": "1.0.0"}])
    monkeypatch.setattr(ExtensionRegistry, "get", lambda self, ext_id: {"version": "1.0.0", "enabled": True})
    monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda self, ext_id: {"id": "test-ext", "name": "Test Ext", "version": "1.1.0", "download_url": "https://example.com/ext.zip"})

    # Mock download_extension to avoid network calls; use tmp_path so the test is hermetic
    # and returns a Path so zip_path.exists() / zip_path.unlink() work without AttributeError
    mock_zip = project_dir / "mock.zip"
    monkeypatch.setattr(ExtensionCatalog, "download_extension", lambda self, ext_id: mock_zip)

    # Mock confirmation to true
    monkeypatch.setattr("typer.confirm", lambda _: True)

    # Run update
    result = runner.invoke(app, ["extension", "update", "test-ext"], obj={"project_root": project_dir})

    # extension_update() catches exceptions internally and exits with code 1 on failure.
    assert result.exit_code == 1
    assert "AttributeError" not in result.output
    assert not isinstance(result.exception, AttributeError)

def test_extension_update_corrupted_hooks_value(project_dir, monkeypatch):
    """Regression: extension update must handle non-dict 'hooks' in extensions.yml."""
    monkeypatch.chdir(project_dir)

    config_path = project_dir / ".specify" / "extensions.yml"
    config_path.write_text(yaml.dump({
        "installed": ["test-ext"],
        "hooks": ["not", "a", "dict"]
    }))

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [{"id": "test-ext", "name": "Test Ext", "version": "1.0.0"}])
    monkeypatch.setattr(ExtensionRegistry, "get", lambda self, ext_id: {"version": "1.0.0", "enabled": True})
    monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda self, ext_id: {"id": "test-ext", "name": "Test Ext", "version": "1.1.0", "download_url": "https://example.com/ext.zip"})
    # Use tmp_path-scoped zip so the test is hermetic and returns a Path for zip_path.exists()
    mock_zip = project_dir / "mock.zip"
    monkeypatch.setattr(ExtensionCatalog, "download_extension", lambda self, ext_id: mock_zip)
    monkeypatch.setattr("typer.confirm", lambda _: True)

    result = runner.invoke(app, ["extension", "update", "test-ext"], obj={"project_root": project_dir})

    # extension_update() catches exceptions internally and exits with code 1 on failure.
    assert result.exit_code == 1
    assert "AttributeError" not in result.output
    assert not isinstance(result.exception, AttributeError)

def test_extension_update_rollback_corrupted_config(project_dir, monkeypatch):
    """Regression: extension update rollback must handle corrupted extensions.yml."""
    monkeypatch.chdir(project_dir)

    config_path = project_dir / ".specify" / "extensions.yml"
    # Write config with hooks: null; get_project_config() normalizes this to {}
    # so the backup captures {} and the restored config will have hooks: {}.
    config_path.write_text(yaml.dump({"installed": ["test-ext"], "hooks": None}))

    # Mock update process to fail after backup
    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [{"id": "test-ext", "name": "Test Ext", "version": "1.0.0"}])
    monkeypatch.setattr(ExtensionRegistry, "get", lambda self, ext_id: {"version": "1.0.0", "enabled": True})

    # Reach the destructive update phase, then fail the install so rollback is
    # both necessary and safe to exercise. Download/preflight failures leave
    # the installation untouched and deliberately skip destructive rollback.
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: None,
    )

    def mock_install_fail(*args, **kwargs):
        config_path.write_text(yaml.dump("CORRUPTED"))
        raise Exception("Install failed")

    monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda self, ext_id: {"id": "test-ext", "name": "Test Ext", "version": "1.1.0", "download_url": "https://example.com/ext.zip"})
    monkeypatch.setattr(ExtensionManager, "install_from_zip", mock_install_fail)
    monkeypatch.setattr("typer.confirm", lambda _: True)

    result = runner.invoke(app, ["extension", "update", "test-ext"], obj={"project_root": project_dir})

    # Should handle Exception and NOT crash with AttributeError during rollback
    assert result.exit_code == 1
    assert "Install failed" in result.output
    assert not isinstance(result.exception, AttributeError)

    # Verify hooks key was preserved (normalized to {} if it was null/corrupted)
    restored_config = yaml.safe_load(config_path.read_text())
    assert isinstance(restored_config, dict)
    assert "hooks" in restored_config
    assert restored_config["hooks"] == {}


def test_extension_update_skills_backup_no_collision(project_dir, monkeypatch):
    """Regression: skills agents name every command file SKILL.md (one per
    command subdirectory). Backup must keep the per-command path so rollback
    restores each skill's own content instead of overwriting them onto a
    single backup path."""
    monkeypatch.chdir(project_dir)

    config_path = project_dir / ".specify" / "extensions.yml"
    config_path.write_text(yaml.dump({"installed": ["test-ext"], "hooks": {}}))

    # Two skill command files with DISTINCT content, mirroring the claude
    # skills layout (.claude/skills/<name>/SKILL.md).
    skills_root = project_dir / ".claude" / "skills"
    plan_file = skills_root / "speckit-plan" / "SKILL.md"
    tasks_file = skills_root / "speckit-tasks" / "SKILL.md"
    plan_file.parent.mkdir(parents=True)
    tasks_file.parent.mkdir(parents=True)
    plan_file.write_text("PLAN CONTENT")
    tasks_file.write_text("TASKS CONTENT")

    monkeypatch.setattr(ExtensionManager, "list_installed", lambda self: [{"id": "test-ext", "name": "Test Ext", "version": "1.0.0"}])
    monkeypatch.setattr(ExtensionRegistry, "get", lambda self, ext_id: {
        "version": "1.0.0",
        "enabled": True,
        "registered_commands": {"claude": ["speckit.plan", "speckit.tasks"]},
    })
    monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda self, ext_id: {"id": "test-ext", "name": "Test Ext", "version": "1.1.0", "download_url": "https://example.com/ext.zip"})

    # Let download and validation succeed, then simulate remove clobbering the
    # originals before install fails. Rollback must rely on the command backups.
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    def mock_remove(self, ext_id, keep_config=False):
        plan_file.unlink()
        tasks_file.unlink()

    def mock_install_fail(*args, **kwargs):
        raise Exception("Install failed")

    monkeypatch.setattr(ExtensionManager, "remove", mock_remove)
    monkeypatch.setattr(ExtensionManager, "install_from_zip", mock_install_fail)
    monkeypatch.setattr("typer.confirm", lambda _: True)

    result = runner.invoke(app, ["extension", "update", "test-ext"], obj={"project_root": project_dir})

    assert result.exit_code == 1
    # Rollback must restore EACH skill's own content, not a single collided copy.
    assert plan_file.exists() and tasks_file.exists()
    assert plan_file.read_text() == "PLAN CONTENT"
    assert tasks_file.read_text() == "TASKS CONTENT"


def test_extension_update_download_failure_never_removes_live_extension(
    project_dir, monkeypatch
):
    """A download error happens before the destructive update boundary."""
    import shutil

    monkeypatch.chdir(project_dir)

    config_path = project_dir / ".specify" / "extensions.yml"
    config_path.write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    live_extension = project_dir / ".specify" / "extensions" / "test-ext"
    live_extension.mkdir(parents=True)
    sentinel = live_extension / "sentinel.txt"
    sentinel.write_text("ORIGINAL")

    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )

    def mock_download_fail(self, ext_id):
        raise Exception("Download failed")

    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        mock_download_fail,
    )

    removed_paths = []
    real_rmtree = shutil.rmtree

    def track_rmtree(path, *args, **kwargs):
        removed_paths.append(Path(path).resolve())
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(shutil, "rmtree", track_rmtree)

    remove_calls = []

    def track_remove(self, ext_id, keep_config=False):
        remove_calls.append((ext_id, keep_config))

    monkeypatch.setattr(ExtensionManager, "remove", track_remove)

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Download failed" in result.output
    assert "Rolling back" not in result.output
    assert remove_calls == []
    assert live_extension.resolve() not in removed_paths
    assert sentinel.read_text() == "ORIGINAL"
    assert _update_backup_dirs(project_dir) == []


def test_extension_update_partial_extension_backup_preserves_live_tree(
    project_dir, monkeypatch
):
    """A partial extension backup must never be restored over the live tree."""
    import shutil

    monkeypatch.chdir(project_dir)

    config_path = project_dir / ".specify" / "extensions.yml"
    config_path.write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    live_extension = project_dir / ".specify" / "extensions" / "test-ext"
    live_extension.mkdir(parents=True)
    first_file = live_extension / "first.txt"
    second_file = live_extension / "second.txt"
    first_file.write_text("FIRST ORIGINAL")
    second_file.write_text("SECOND ORIGINAL")

    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )

    real_copytree = shutil.copytree

    def fail_partial_backup(src, dst, *args, **kwargs):
        src = Path(src)
        dst = Path(dst)
        if src.resolve() == live_extension.resolve():
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(first_file, dst / first_file.name)
            raise OSError("Extension backup failed")
        return real_copytree(src, dst, *args, **kwargs)

    monkeypatch.setattr(shutil, "copytree", fail_partial_backup)

    remove_calls = []

    def track_remove(self, ext_id, keep_config=False):
        remove_calls.append((ext_id, keep_config))

    monkeypatch.setattr(ExtensionManager, "remove", track_remove)

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Extension backup failed" in result.output
    assert "Rolling back" not in result.output
    assert remove_calls == []
    assert first_file.read_text() == "FIRST ORIGINAL"
    assert second_file.read_text() == "SECOND ORIGINAL"
    assert _update_backup_dirs(project_dir) == []


def test_extension_update_rejects_symlinked_backup_root_without_cleanup(
    project_dir, monkeypatch
):
    """A rejected backup root must never be followed during error cleanup."""
    import os

    if not hasattr(os, "symlink"):
        pytest.skip("symlinks are unavailable")

    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )

    outside = project_dir / "outside-backups"
    outside.mkdir()
    sentinel = outside / "keep.txt"
    sentinel.write_text("KEEP", encoding="utf-8")
    backup_root = (
        project_dir / ".specify" / "extensions" / ".backup"
    )
    backup_root.parent.mkdir(parents=True)
    try:
        os.symlink(outside, backup_root)
    except OSError:
        pytest.skip("Current platform/user cannot create directory symlinks")

    download_calls = []
    remove_calls = []
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: download_calls.append(ext_id),
    )
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "symlinked directory" in result.output
    assert "Rolling back" not in result.output
    assert download_calls == []
    assert remove_calls == []
    assert backup_root.is_symlink()
    assert sentinel.read_text(encoding="utf-8") == "KEEP"


def test_extension_update_partial_command_backup_preserves_live_commands(
    project_dir, monkeypatch
):
    """An incomplete command backup must not make originals look newly added."""
    import shutil

    monkeypatch.chdir(project_dir)

    config_path = project_dir / ".specify" / "extensions.yml"
    config_path.write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    skills_root = project_dir / ".claude" / "skills"
    plan_file = skills_root / "speckit-plan" / "SKILL.md"
    tasks_file = skills_root / "speckit-tasks" / "SKILL.md"
    plan_file.parent.mkdir(parents=True)
    tasks_file.parent.mkdir(parents=True)
    plan_file.write_text("PLAN ORIGINAL")
    tasks_file.write_text("TASKS ORIGINAL")

    registry_entry = {
        "version": "1.0.0",
        "enabled": True,
        "registered_commands": {
            "claude": ["speckit.plan", "speckit.tasks"]
        },
    }
    _stub_available_update(monkeypatch, registry_entry)

    backup_root = (
        project_dir
        / ".specify"
        / "extensions"
        / ".backup"
    )
    real_copy2 = shutil.copy2
    command_backup_count = 0

    def fail_second_command_backup(src, dst, *args, **kwargs):
        nonlocal command_backup_count
        dst = Path(dst)
        try:
            relative_backup = dst.resolve().relative_to(
                backup_root.resolve()
            )
        except ValueError:
            return real_copy2(src, dst, *args, **kwargs)
        if (
            len(relative_backup.parts) < 2
            or not relative_backup.parts[0].startswith("update-")
            or relative_backup.parts[1] != "commands"
        ):
            return real_copy2(src, dst, *args, **kwargs)
        command_backup_count += 1
        if command_backup_count == 2:
            raise OSError("Command backup failed")
        return real_copy2(src, dst, *args, **kwargs)

    monkeypatch.setattr(shutil, "copy2", fail_second_command_backup)

    remove_calls = []

    def track_remove(self, ext_id, keep_config=False):
        remove_calls.append((ext_id, keep_config))

    monkeypatch.setattr(ExtensionManager, "remove", track_remove)

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Command backup failed" in result.output
    assert "Rolling back" not in result.output
    assert command_backup_count == 2
    assert remove_calls == []
    assert plan_file.read_text() == "PLAN ORIGINAL"
    assert tasks_file.read_text() == "TASKS ORIGINAL"
    assert _update_backup_dirs(project_dir) == []


def test_extension_update_rolls_back_partial_remove(project_dir, monkeypatch):
    """A remove failure after its first mutation still restores the backup."""
    monkeypatch.chdir(project_dir)

    config_path = project_dir / ".specify" / "extensions.yml"
    config_path.write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    live_extension = project_dir / ".specify" / "extensions" / "test-ext"
    live_extension.mkdir(parents=True)
    sentinel = live_extension / "sentinel.txt"
    sentinel.write_text("ORIGINAL")

    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    def fail_partial_remove(self, ext_id, keep_config=False):
        sentinel.unlink()
        raise OSError("Remove failed")

    monkeypatch.setattr(ExtensionManager, "remove", fail_partial_remove)

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Remove failed" in result.output
    assert "Rolling back" in result.output
    assert sentinel.read_text() == "ORIGINAL"
    assert _update_backup_dirs(project_dir) == []


def test_extension_update_reports_success_when_backup_cleanup_fails(
    project_dir, monkeypatch
):
    """A retained backup is isolated from the next successful update."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    live_extension = (
        project_dir / ".specify" / "extensions" / "test-ext"
    )
    live_extension.mkdir(parents=True)
    (live_extension / "sentinel.txt").write_text(
        "ORIGINAL", encoding="utf-8"
    )
    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: None,
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: None,
    )

    backup_root = (
        project_dir
        / ".specify"
        / "extensions"
        / ".backup"
    )
    real_rmtree = shutil.rmtree
    failed_cleanup = False

    def fail_backup_cleanup_once(path, *args, **kwargs):
        nonlocal failed_cleanup
        candidate = Path(path)
        if (
            candidate.parent == backup_root
            and candidate.name.startswith("update-")
            and not failed_cleanup
        ):
            failed_cleanup = True
            raise OSError("Backup is locked")
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(shutil, "rmtree", fail_backup_cleanup_once)

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 0, result.output
    assert "Updated to v1.1.0" in result.output
    assert "Could not fully remove update backup" in result.output
    assert "Rolling back" not in result.output
    assert failed_cleanup

    retained_backups = _update_backup_dirs(project_dir)
    assert len(retained_backups) == 1
    stale_config = (
        retained_backups[0] / "config" / "stale-config.yml"
    )
    stale_config.parent.mkdir(parents=True, exist_ok=True)
    stale_config.write_text("stale: true\n", encoding="utf-8")

    # A second attempt receives a distinct backup directory. The retained
    # config from the first completed update must never be resurrected.
    _write_update_zip(mock_zip)
    second_result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert second_result.exit_code == 0, second_result.output
    assert not (live_extension / stale_config.name).exists()
    assert _update_backup_dirs(project_dir) == retained_backups


def test_extension_update_reports_restored_state_when_cleanup_fails(
    project_dir, monkeypatch
):
    """Post-rollback cleanup errors must not contradict restored state."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    live_extension = (
        project_dir / ".specify" / "extensions" / "test-ext"
    )
    live_extension.mkdir(parents=True)
    sentinel = live_extension / "sentinel.txt"
    sentinel.write_text("ORIGINAL", encoding="utf-8")
    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    def fail_partial_remove(self, ext_id, keep_config=False):
        sentinel.unlink()
        raise OSError("Remove failed")

    monkeypatch.setattr(
        ExtensionManager, "remove", fail_partial_remove
    )

    backup_root = (
        project_dir
        / ".specify"
        / "extensions"
        / ".backup"
    )
    real_rmtree = shutil.rmtree
    failed_cleanup = False

    def fail_backup_cleanup_once(path, *args, **kwargs):
        nonlocal failed_cleanup
        candidate = Path(path)
        if (
            candidate.parent == backup_root
            and candidate.name.startswith("update-")
            and not failed_cleanup
        ):
            failed_cleanup = True
            raise OSError("Backup is locked")
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(shutil, "rmtree", fail_backup_cleanup_once)

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Rollback successful" in result.output
    assert "Could not fully remove rollback backup" in result.output
    assert "Rollback failed" not in result.output
    assert sentinel.read_text(encoding="utf-8") == "ORIGINAL"
    assert failed_cleanup


def test_extension_update_does_not_rollback_for_locked_download_cleanup(
    project_dir, monkeypatch
):
    """A locked downloaded ZIP is non-fatal after the update commits."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: None,
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: None,
    )

    real_unlink = Path.unlink
    failed_cleanup = False

    def fail_zip_cleanup_once(path, *args, **kwargs):
        nonlocal failed_cleanup
        if path == mock_zip and not failed_cleanup:
            failed_cleanup = True
            raise OSError("Downloaded ZIP is locked")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_zip_cleanup_once)

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 0, result.output
    assert "Updated to v1.1.0" in result.output
    assert "Could not remove downloaded update archive" in result.output
    assert "Rolling back" not in result.output
    assert failed_cleanup


def test_extension_update_preserves_install_error_when_zip_cleanup_fails(
    project_dir, monkeypatch
):
    """ZIP cleanup must not replace the error that caused rollback."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: None,
    )

    def fail_install(*args, **kwargs):
        raise RuntimeError("Original install failure")

    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        fail_install,
    )

    real_unlink = Path.unlink
    failed_cleanup = False

    def fail_zip_cleanup_once(path, *args, **kwargs):
        nonlocal failed_cleanup
        if path == mock_zip and not failed_cleanup:
            failed_cleanup = True
            raise OSError("Downloaded ZIP is locked")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_zip_cleanup_once)

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Original install failure" in result.output
    assert "Failed: Downloaded ZIP is locked" not in result.output
    assert "Could not remove downloaded update archive" in result.output
    assert "Rollback successful" in result.output
    assert failed_cleanup


@pytest.mark.parametrize(
    ("manifest", "expected_error"),
    [
        (
            {
                "extension": {
                    "id": "test-ext",
                    "name": "Test Ext",
                    "version": "1.1.0",
                }
            },
            "Missing required field: schema_version",
        ),
        (
            {
                **_valid_update_manifest(),
                "requires": {"speckit_version": ">=9999"},
            },
            "Extension requires spec-kit >=9999",
        ),
    ],
)
def test_extension_update_validates_full_manifest_before_removal(
    project_dir, monkeypatch, manifest, expected_error
):
    """Malformed or incompatible manifests must fail before remove()."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )

    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip, manifest=manifest)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    remove_calls = []
    install_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: install_calls.append(args),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert expected_error in result.output
    assert "Rolling back" not in result.output
    assert remove_calls == []
    assert install_calls == []


def test_extension_update_rejects_catalog_archive_version_mismatch(
    project_dir, monkeypatch
):
    """The archive version must match the normalized catalog version."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )

    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip, version="1.0.1")
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    remove_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert (
        "Extension version mismatch: expected '1.1.0', got '1.0.1'"
        in result.output
    )
    assert "Updated to v1.1.0" not in result.output
    assert "Rolling back" not in result.output
    assert remove_calls == []


def test_extension_update_rejects_command_conflicts_before_removal(
    project_dir, monkeypatch
):
    """Deterministic install conflicts belong on the safe side of remove()."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )

    mock_zip = project_dir / "mock.zip"
    _write_update_zip(
        mock_zip,
        manifest=_valid_update_manifest(
            command_name="speckit.other.run"
        ),
    )
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    remove_calls = []
    install_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: install_calls.append(args),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    normalized_output = " ".join(result.output.split())
    assert (
        "Command 'speckit.other.run' must use extension namespace 'test-ext'"
        in normalized_output
    )
    assert "Rolling back" not in result.output
    assert remove_calls == []
    assert install_calls == []


def test_extension_update_rejects_alias_parent_traversal_before_removal(
    project_dir, monkeypatch
):
    """Alias '..' segments cannot escape through a symlinked subdirectory."""
    import os

    if not hasattr(os, "symlink"):
        pytest.skip("symlinks are unavailable")

    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )

    commands_dir = project_dir / ".github" / "agents"
    commands_dir.mkdir(parents=True)
    outside_dir = project_dir / "outside" / "subdir"
    outside_dir.mkdir(parents=True)
    outside_target = outside_dir.parent / "victim.agent.md"
    outside_target.write_text("USER CONTENT", encoding="utf-8")
    try:
        os.symlink(outside_dir, commands_dir / "link")
    except OSError:
        pytest.skip("Current platform/user cannot create directory symlinks")

    manifest = _valid_update_manifest()
    manifest["provides"]["commands"][0]["aliases"] = [
        "link/../victim"
    ]
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip, manifest=manifest)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    remove_calls = []
    install_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: install_calls.append(args),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    normalized_output = " ".join(result.output.split())
    assert "Invalid alias 'link/../victim'" in normalized_output
    assert "Rolling back" not in result.output
    assert remove_calls == []
    assert install_calls == []
    assert outside_target.read_text(encoding="utf-8") == "USER CONTENT"


def test_extension_update_accepts_normalized_equivalent_archive_version(
    project_dir, monkeypatch
):
    """Equivalent PEP 440 spellings must not cause a false mismatch."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    registry_entry = {"version": "1.0.0", "enabled": True}
    _stub_available_update(monkeypatch, registry_entry)

    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip, version="v1.1")
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    remove_calls = []
    install_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: install_calls.append(args),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 0, result.output
    assert remove_calls == ["test-ext"]
    assert len(install_calls) == 1
    assert "Updated to v1.1.0" in result.output


def test_extension_update_rejects_noncanonical_root_manifest_alias(
    project_dir, monkeypatch
):
    """Root aliases must not select different manifests across filesystems."""
    import zipfile

    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )

    injected_manifest = _valid_update_manifest()
    injected_manifest["extension"]["id"] = "injected"
    mock_zip = project_dir / "mock.zip"
    with zipfile.ZipFile(mock_zip, "w") as archive:
        archive.writestr(
            "EXTENSION.YML",
            yaml.safe_dump(injected_manifest),
        )
        archive.writestr(
            "repo/extension.yml",
            yaml.safe_dump(_valid_update_manifest()),
        )
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    remove_calls = []
    install_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: install_calls.append(args),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "canonical 'extension.yml' casing" in result.output
    assert "Rolling back" not in result.output
    assert remove_calls == []
    assert install_calls == []


def test_extension_update_rejects_multiple_nested_archive_roots_before_removal(
    project_dir, monkeypatch
):
    """Nested manifests must match install_from_zip's one-directory layout."""
    import zipfile

    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )

    mock_zip = project_dir / "mock.zip"
    with zipfile.ZipFile(mock_zip, "w") as archive:
        archive.writestr(
            "repo/extension.yml",
            yaml.safe_dump(_valid_update_manifest()),
        )
        archive.writestr("other/content.txt", "SECOND ROOT")
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    remove_calls = []
    install_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: install_calls.append(args),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    normalized_output = " ".join(result.output.split())
    assert (
        "must contain exactly one top-level directory"
        in normalized_output
    )
    assert "Rolling back" not in result.output
    assert remove_calls == []
    assert install_calls == []


def test_extension_update_accepts_root_file_beside_nested_manifest(
    project_dir, monkeypatch
):
    """Root files do not create another directory during ZIP extraction."""
    import zipfile

    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    _stub_available_update(
        monkeypatch, {"version": "1.0.0", "enabled": True}
    )

    mock_zip = project_dir / "mock.zip"
    with zipfile.ZipFile(mock_zip, "w") as archive:
        archive.writestr(
            "repo/extension.yml",
            yaml.safe_dump(_valid_update_manifest()),
        )
        archive.writestr("README.md", "ROOT FILE")
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    remove_calls = []
    install_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: install_calls.append(args),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 0, result.output
    assert remove_calls == ["test-ext"]
    assert len(install_calls) == 1


def test_extension_update_rolls_back_commands_written_before_registry_add(
    project_dir, monkeypatch
):
    """Rollback uses preflight paths when a failed install has no new registry."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    agents_dir = project_dir / ".github" / "agents"
    prompts_dir = project_dir / ".github" / "prompts"
    agents_dir.mkdir(parents=True)
    prompts_dir.mkdir(parents=True)

    registry_entry = {
        "version": "1.0.0",
        "enabled": True,
        "registered_commands": {},
    }
    _stub_available_update(monkeypatch, registry_entry)

    command_name = "speckit.test-ext.new"
    alias_names = [
        "speckit.test-ext.group-a/shared",
        "speckit.test-ext.group-b/shared",
    ]
    new_nested_alias = "speckit.test-ext/new-group/deep"
    manifest = _valid_update_manifest(command_name=command_name)
    manifest["provides"]["commands"][0]["aliases"] = [
        *alias_names,
        new_nested_alias,
    ]
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip, manifest=manifest)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    new_command = agents_dir / f"{command_name}.agent.md"
    new_prompt = prompts_dir / f"{command_name}.prompt.md"
    new_nested_command = (
        agents_dir / f"{new_nested_alias}.agent.md"
    )
    new_nested_prompt = (
        prompts_dir / f"{new_nested_alias}.prompt.md"
    )
    existing_aliases = [
        agents_dir / f"{alias_name}.agent.md"
        for alias_name in alias_names
    ]
    existing_alias_prompts = [
        prompts_dir / f"{alias_name}.prompt.md"
        for alias_name in alias_names
    ]
    for index, alias_file in enumerate(existing_aliases):
        alias_file.parent.mkdir(parents=True, exist_ok=True)
        alias_file.write_text(f"USER COMMAND {index}", encoding="utf-8")
    for index, prompt_file in enumerate(existing_alias_prompts):
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(f"USER PROMPT {index}", encoding="utf-8")

    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: None,
    )

    def fail_before_registry_add(*args, **kwargs):
        new_command.write_text("NEW COMMAND", encoding="utf-8")
        new_prompt.write_text("NEW PROMPT", encoding="utf-8")
        new_nested_command.parent.mkdir(parents=True)
        new_nested_prompt.parent.mkdir(parents=True)
        new_nested_command.write_text(
            "NEW NESTED COMMAND", encoding="utf-8"
        )
        new_nested_prompt.write_text(
            "NEW NESTED PROMPT", encoding="utf-8"
        )
        for alias_file in existing_aliases:
            alias_file.write_text("OVERWRITTEN COMMAND", encoding="utf-8")
        for prompt_file in existing_alias_prompts:
            prompt_file.write_text("OVERWRITTEN PROMPT", encoding="utf-8")
        raise RuntimeError("Hook registration failed before registry add")

    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        fail_before_registry_add,
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Hook registration failed before registry add" in result.output
    assert "Rollback successful" in result.output
    assert not new_command.exists()
    assert not new_prompt.exists()
    assert not new_nested_command.exists()
    assert not new_nested_prompt.exists()
    assert not (agents_dir / "speckit.test-ext").exists()
    assert not (prompts_dir / "speckit.test-ext").exists()
    for index, alias_file in enumerate(existing_aliases):
        assert (
            alias_file.read_text(encoding="utf-8")
            == f"USER COMMAND {index}"
        )
    for index, prompt_file in enumerate(existing_alias_prompts):
        assert (
            prompt_file.read_text(encoding="utf-8")
            == f"USER PROMPT {index}"
        )


def test_extension_update_restores_canonical_and_legacy_commands(
    project_dir, monkeypatch
):
    """Rollback restores every command location cleaned by unregister."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    canonical_dir = project_dir / ".opencode" / "commands"
    legacy_dir = project_dir / ".opencode" / "command"
    canonical_dir.mkdir(parents=True)
    legacy_dir.mkdir(parents=True)

    old_command = "speckit.test-ext.old"
    canonical_file = canonical_dir / f"{old_command}.md"
    legacy_file = legacy_dir / f"{old_command}.md"
    canonical_file.write_text("CANONICAL USER COMMAND", encoding="utf-8")
    legacy_file.write_text("LEGACY USER COMMAND", encoding="utf-8")
    _stub_available_update(
        monkeypatch,
        {
            "version": "1.0.0",
            "enabled": True,
            "registered_commands": {"opencode": [old_command]},
        },
    )

    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    def remove_both_command_copies(
        self, ext_id, keep_config=False
    ):
        canonical_file.unlink()
        legacy_file.unlink()

    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        remove_both_command_copies,
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("Install failed after legacy cleanup")
        ),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Rollback successful" in result.output
    assert (
        canonical_file.read_text(encoding="utf-8")
        == "CANONICAL USER COMMAND"
    )
    assert (
        legacy_file.read_text(encoding="utf-8")
        == "LEGACY USER COMMAND"
    )


def test_extension_update_removes_new_active_skills_root_on_rollback(
    project_dir, monkeypatch
):
    """Rollback removes an active skills hierarchy created by registration."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    (project_dir / ".specify" / "init-options.json").write_text(
        '{"ai":"claude","ai_skills":true}',
        encoding="utf-8",
    )
    _stub_available_update(
        monkeypatch,
        {
            "version": "1.0.0",
            "enabled": True,
            "registered_commands": {},
        },
    )

    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: None,
    )

    new_skill = (
        project_dir
        / ".claude"
        / "skills"
        / "speckit-test-ext-run"
    )

    def fail_after_creating_skill(*args, **kwargs):
        new_skill.mkdir(parents=True)
        (new_skill / "SKILL.md").write_text(
            "GENERATED SKILL", encoding="utf-8"
        )
        raise RuntimeError("Hook registration failed after skill creation")

    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        fail_after_creating_skill,
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Rollback successful" in result.output
    assert not (project_dir / ".claude").exists()


def test_extension_update_removes_new_hermes_marker_on_rollback(
    project_dir, monkeypatch, tmp_path
):
    """Rollback removes Hermes' local marker as well as global skill output."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    (project_dir / ".specify" / "init-options.json").write_text(
        '{"ai":"hermes","ai_skills":true}',
        encoding="utf-8",
    )
    _stub_available_update(
        monkeypatch,
        {
            "version": "1.0.0",
            "enabled": True,
            "registered_commands": {},
        },
    )

    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: None,
    )

    local_marker = project_dir / ".hermes" / "skills"
    global_skill = (
        fake_home
        / ".hermes"
        / "skills"
        / "speckit-test-ext-run"
    )

    def fail_after_creating_hermes_skill(*args, **kwargs):
        local_marker.mkdir(parents=True)
        global_skill.mkdir(parents=True)
        (global_skill / "SKILL.md").write_text(
            "GENERATED SKILL", encoding="utf-8"
        )
        raise RuntimeError("Hook registration failed after Hermes skill")

    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        fail_after_creating_hermes_skill,
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Rollback successful" in result.output
    assert not (project_dir / ".hermes").exists()
    assert not (fake_home / ".hermes" / "skills").exists()


def test_extension_update_restores_command_symlinks(
    project_dir, monkeypatch
):
    """Rollback preserves valid and dangling command symlinks byte-for-byte."""
    import os

    if not hasattr(os, "symlink"):
        pytest.skip("symlinks are unavailable")

    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    agents_dir = project_dir / ".github" / "agents"
    prompts_dir = project_dir / ".github" / "prompts"
    agents_dir.mkdir(parents=True)
    _stub_available_update(
        monkeypatch,
        {
            "version": "1.0.0",
            "enabled": True,
            "registered_commands": {},
        },
    )

    alias_names = [
        "speckit.test-ext.valid-link",
        "speckit.test-ext.dangling-link",
    ]
    manifest = _valid_update_manifest()
    manifest["provides"]["commands"][0]["aliases"] = alias_names
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(mock_zip, manifest=manifest)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    targets_dir = project_dir / "user-targets"
    targets_dir.mkdir()
    command_targets = [
        targets_dir / "command-valid.md",
        targets_dir / "command-dangling.md",
    ]
    command_targets[0].write_text(
        "USER COMMAND TARGET", encoding="utf-8"
    )

    alias_files = [
        agents_dir / f"{alias_name}.agent.md"
        for alias_name in alias_names
    ]
    generated_prompt = (
        prompts_dir / "speckit.test-ext.run.prompt.md"
    )
    command_link_texts = []
    try:
        for alias_file, target in zip(alias_files, command_targets):
            link_text = os.path.relpath(target, alias_file.parent)
            os.symlink(link_text, alias_file)
            command_link_texts.append(link_text)
    except OSError:
        pytest.skip("Current platform/user cannot create file symlinks")

    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: None,
    )

    def fail_before_registry_add(*args, **kwargs):
        # Normal command rendering replaces command symlinks.
        for alias_file in alias_files:
            alias_file.unlink()
            alias_file.write_text("GENERATED COMMAND", encoding="utf-8")
        generated_prompt.parent.mkdir(parents=True)
        generated_prompt.write_text(
            "GENERATED PROMPT", encoding="utf-8"
        )
        raise RuntimeError("Hook registration failed after symlink writes")

    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        fail_before_registry_add,
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Rollback successful" in result.output
    for alias_file, link_text in zip(
        alias_files, command_link_texts
    ):
        assert alias_file.is_symlink()
        assert os.readlink(alias_file) == link_text
    assert (
        command_targets[0].read_text(encoding="utf-8")
        == "USER COMMAND TARGET"
    )
    assert not command_targets[1].exists()
    assert not prompts_dir.exists()


def test_extension_update_rejects_symlinked_copilot_prompt_before_removal(
    project_dir, monkeypatch
):
    """Prompt links are rejected before rendering can write through them."""
    import os

    if not hasattr(os, "symlink"):
        pytest.skip("symlinks are unavailable")

    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "init-options.json").write_text(
        '{"ai":"copilot","ai_skills":false}',
        encoding="utf-8",
    )
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    agents_dir = project_dir / ".github" / "agents"
    prompts_dir = project_dir / ".github" / "prompts"
    agents_dir.mkdir(parents=True)
    prompts_dir.mkdir(parents=True)
    _stub_available_update(
        monkeypatch,
        {
            "version": "1.0.0",
            "enabled": True,
            "registered_commands": {},
        },
    )

    command_name = "speckit.test-ext.linked-prompt"
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(
        mock_zip,
        manifest=_valid_update_manifest(command_name=command_name),
    )
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    target = project_dir / "user-prompt.md"
    target.write_text("USER PROMPT", encoding="utf-8")
    prompt_file = prompts_dir / f"{command_name}.prompt.md"
    link_text = os.path.relpath(target, prompt_file.parent)
    try:
        os.symlink(link_text, prompt_file)
    except OSError:
        pytest.skip("Current platform/user cannot create file symlinks")

    remove_calls = []
    install_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: install_calls.append(args),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Cannot safely update symlinked Copilot prompt artifact" in result.output
    assert "Rolling back" not in result.output
    assert remove_calls == []
    assert install_calls == []
    assert prompt_file.is_symlink()
    assert os.readlink(prompt_file) == link_text
    assert target.read_text(encoding="utf-8") == "USER PROMPT"


@pytest.mark.parametrize(
    ("active_agent", "ai_skills"),
    [("gemini", False), ("copilot", True)],
)
def test_extension_update_ignores_inactive_copilot_artifacts(
    project_dir, monkeypatch, active_agent, ai_skills
):
    """Preflight must inspect only outputs the active install can render."""
    import json
    import os

    if not hasattr(os, "link") or not hasattr(os, "symlink"):
        pytest.skip("links are unavailable")

    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "init-options.json").write_text(
        json.dumps({"ai": active_agent, "ai_skills": ai_skills}),
        encoding="utf-8",
    )
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    if active_agent == "gemini":
        (project_dir / ".gemini" / "commands").mkdir(parents=True)

    agents_dir = project_dir / ".github" / "agents"
    prompts_dir = project_dir / ".github" / "prompts"
    agents_dir.mkdir(parents=True)
    prompts_dir.mkdir(parents=True)
    _stub_available_update(
        monkeypatch,
        {
            "version": "1.0.0",
            "enabled": True,
            "registered_commands": {},
        },
    )

    command_name = "speckit.test-ext.inactive-copilot"
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(
        mock_zip,
        manifest=_valid_update_manifest(command_name=command_name),
    )
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    command_target = project_dir / "user-command.md"
    command_target.write_text("USER COMMAND", encoding="utf-8")
    command_file = agents_dir / f"{command_name}.agent.md"
    prompt_target = project_dir / "user-prompt.md"
    prompt_target.write_text("USER PROMPT", encoding="utf-8")
    prompt_file = prompts_dir / f"{command_name}.prompt.md"
    try:
        os.link(command_target, command_file)
        os.symlink(
            os.path.relpath(prompt_target, prompt_file.parent),
            prompt_file,
        )
    except OSError:
        pytest.skip("Current filesystem cannot create test links")

    remove_calls = []
    install_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: install_calls.append(args),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 0, result.output
    assert remove_calls == ["test-ext"]
    assert len(install_calls) == 1
    assert command_file.read_text(encoding="utf-8") == "USER COMMAND"
    assert prompt_file.is_symlink()
    assert prompt_target.read_text(encoding="utf-8") == "USER PROMPT"


@pytest.mark.parametrize("broken_active_marker", [False, True])
def test_extension_update_ignores_unreachable_global_hermes_target(
    project_dir, tmp_path, monkeypatch, broken_active_marker
):
    """Preflight skips Hermes when its project marker cannot be detected."""
    import os

    if not hasattr(os, "link"):
        pytest.skip("hard links are unavailable")

    monkeypatch.chdir(project_dir)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    if broken_active_marker:
        (project_dir / ".specify" / "init-options.json").write_text(
            '{"ai":"hermes","ai_skills":true}',
            encoding="utf-8",
        )
        (project_dir / ".hermes").write_text(
            "marker parent is not a directory",
            encoding="utf-8",
        )
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    _stub_available_update(
        monkeypatch,
        {
            "version": "1.0.0",
            "enabled": True,
            "registered_commands": {},
        },
    )

    command_name = "speckit.test-ext.unmarked-hermes"
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(
        mock_zip,
        manifest=_valid_update_manifest(command_name=command_name),
    )
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    from specify_cli.agents import CommandRegistrar

    registrar = CommandRegistrar()
    agent_config = registrar.AGENT_CONFIGS["hermes"]
    commands_dir = registrar._resolve_agent_dir(
        "hermes", agent_config, project_dir
    )
    output_name = registrar._compute_output_name(
        "hermes", command_name, agent_config
    )
    artifact = commands_dir / f"{output_name}{agent_config['extension']}"
    artifact.parent.mkdir(parents=True)
    user_target = project_dir / "user-hermes-skill.md"
    user_target.write_text("USER HERMES SKILL", encoding="utf-8")
    try:
        os.link(user_target, artifact)
    except OSError:
        pytest.skip("Current filesystem cannot create hard links")

    remove_calls = []
    install_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: install_calls.append(args),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 0, result.output
    assert remove_calls == ["test-ext"]
    assert len(install_calls) == 1
    assert artifact.read_text(encoding="utf-8") == "USER HERMES SKILL"
    assert not (project_dir / ".hermes" / "skills").exists()


@pytest.mark.parametrize("artifact_kind", ["command", "prompt"])
def test_extension_update_rejects_hard_linked_artifacts_before_removal(
    project_dir, monkeypatch, artifact_kind
):
    """Rendering must not mutate another name for a shared inode."""
    import os

    if not hasattr(os, "link"):
        pytest.skip("hard links are unavailable")

    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "init-options.json").write_text(
        '{"ai":"copilot","ai_skills":false}',
        encoding="utf-8",
    )
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )
    agents_dir = project_dir / ".github" / "agents"
    prompts_dir = project_dir / ".github" / "prompts"
    agents_dir.mkdir(parents=True)
    prompts_dir.mkdir(parents=True)
    _stub_available_update(
        monkeypatch,
        {
            "version": "1.0.0",
            "enabled": True,
            "registered_commands": {},
        },
    )

    command_name = "speckit.test-ext.hard-link"
    mock_zip = project_dir / "mock.zip"
    _write_update_zip(
        mock_zip,
        manifest=_valid_update_manifest(command_name=command_name),
    )
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    user_target = project_dir / "user-artifact.md"
    user_target.write_text("USER CONTENT", encoding="utf-8")
    if artifact_kind == "command":
        artifact = agents_dir / f"{command_name}.agent.md"
    else:
        artifact = prompts_dir / f"{command_name}.prompt.md"
    try:
        os.link(user_target, artifact)
    except OSError:
        pytest.skip("Current filesystem cannot create hard links")
    original_stat = user_target.stat()

    remove_calls = []
    install_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )
    monkeypatch.setattr(
        ExtensionManager,
        "install_from_zip",
        lambda *args, **kwargs: install_calls.append(args),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Cannot safely update hard-linked generated artifact" in result.output
    assert "Rolling back" not in result.output
    assert remove_calls == []
    assert install_calls == []
    assert artifact.read_text(encoding="utf-8") == "USER CONTENT"
    assert user_target.read_text(encoding="utf-8") == "USER CONTENT"
    assert artifact.stat().st_ino == original_stat.st_ino
    assert artifact.stat().st_dev == original_stat.st_dev


def _write_owned_extension_skill(skill_dir, extension_id, body):
    """Write a SKILL.md whose metadata identifies its owning extension."""
    skill_dir.mkdir(parents=True, exist_ok=True)
    frontmatter = yaml.safe_dump(
        {
            "name": skill_dir.name,
            "description": "Extension update rollback test",
            "metadata": {"source": f"extension:{extension_id}"},
        },
        sort_keys=False,
    )
    (skill_dir / "SKILL.md").write_text(
        f"---\n{frontmatter}---\n\n{body}\n",
        encoding="utf-8",
    )


def test_extension_update_rolls_back_registered_skill_artifacts(
    project_dir, monkeypatch
):
    """Rollback restores old registered skills and removes newly created ones."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "init-options.json").write_text(
        '{"ai":"claude","ai_skills":true}',
        encoding="utf-8",
    )
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )

    skills_root = project_dir / ".claude" / "skills"
    old_skill = skills_root / "speckit-test-ext-old"
    new_skill = skills_root / "speckit-test-ext-new"
    _write_owned_extension_skill(old_skill, "test-ext", "OLD SKILL")
    (old_skill / "support.txt").write_text("OLD SUPPORT", encoding="utf-8")

    registry_entry = {
        "version": "1.0.0",
        "enabled": True,
        "registered_skills": [old_skill.name],
    }
    _stub_available_update(monkeypatch, registry_entry)

    mock_zip = project_dir / "mock.zip"
    _write_update_zip(
        mock_zip,
        manifest=_valid_update_manifest(
            command_name="speckit.test-ext.new"
        ),
    )
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension",
        lambda self, ext_id: mock_zip,
    )

    def mock_remove(self, ext_id, keep_config=False):
        shutil.rmtree(old_skill)

    def mock_install_fail(*args, **kwargs):
        # Simulate a write failure before ownership frontmatter is complete.
        # The normal unregistrar must preserve unverifiable directories, so
        # rollback relies on the absent-before-update snapshot to remove this.
        new_skill.mkdir(parents=True)
        (new_skill / "SKILL.md").write_text("---\n", encoding="utf-8")
        raise RuntimeError("Install failed during skill registration")

    monkeypatch.setattr(ExtensionManager, "remove", mock_remove)
    monkeypatch.setattr(
        ExtensionManager, "install_from_zip", mock_install_fail
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Rollback successful" in result.output
    assert (old_skill / "SKILL.md").exists()
    assert "OLD SKILL" in (old_skill / "SKILL.md").read_text(encoding="utf-8")
    assert (old_skill / "support.txt").read_text(encoding="utf-8") == "OLD SUPPORT"
    assert not new_skill.exists()


def test_extension_update_partial_skill_backup_preserves_live_skills(
    project_dir, monkeypatch
):
    """An incomplete skill backup must abort before remove() touches live data."""
    monkeypatch.chdir(project_dir)
    (project_dir / ".specify" / "init-options.json").write_text(
        '{"ai":"claude","ai_skills":true}',
        encoding="utf-8",
    )
    (project_dir / ".specify" / "extensions.yml").write_text(
        yaml.safe_dump({"installed": ["test-ext"], "hooks": {}})
    )

    first_skill = (
        project_dir / ".claude" / "skills" / "speckit-test-ext-old"
    )
    second_skill = (
        project_dir / ".claude" / "skills" / "speckit-test-ext-second"
    )
    _write_owned_extension_skill(first_skill, "test-ext", "FIRST SKILL")
    _write_owned_extension_skill(second_skill, "test-ext", "SECOND SKILL")
    first_support = first_skill / "support.txt"
    second_support = second_skill / "support.txt"
    first_support.write_text("FIRST SUPPORT", encoding="utf-8")
    second_support.write_text("SECOND SUPPORT", encoding="utf-8")

    registry_entry = {
        "version": "1.0.0",
        "enabled": True,
        "registered_skills": [first_skill.name, second_skill.name],
    }
    _stub_available_update(monkeypatch, registry_entry)

    real_copytree = shutil.copytree
    skill_backup_count = 0

    def fail_partial_skill_backup(src, dst, *args, **kwargs):
        nonlocal skill_backup_count
        source = Path(src).resolve()
        if source in {first_skill.resolve(), second_skill.resolve()}:
            skill_backup_count += 1
            if skill_backup_count == 2:
                Path(dst).mkdir(parents=True, exist_ok=True)
                shutil.copy2(
                    Path(src) / "SKILL.md",
                    Path(dst) / "SKILL.md",
                )
                raise OSError("Skill backup failed")
        return real_copytree(src, dst, *args, **kwargs)

    monkeypatch.setattr(shutil, "copytree", fail_partial_skill_backup)
    remove_calls = []
    monkeypatch.setattr(
        ExtensionManager,
        "remove",
        lambda self, ext_id, keep_config=False: remove_calls.append(ext_id),
    )

    result = runner.invoke(
        app,
        ["extension", "update", "test-ext"],
        obj={"project_root": project_dir},
    )

    assert result.exit_code == 1
    assert "Skill backup failed" in result.output
    assert "Rolling back" not in result.output
    assert remove_calls == []
    assert skill_backup_count == 2
    assert (first_skill / "SKILL.md").exists()
    assert (second_skill / "SKILL.md").exists()
    assert first_support.read_text(encoding="utf-8") == "FIRST SUPPORT"
    assert second_support.read_text(encoding="utf-8") == "SECOND SUPPORT"
    assert _update_backup_dirs(project_dir) == []
