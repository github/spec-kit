from specify_cli.extensions import ExtensionManager, ExtensionRegistry, ExtensionCatalog
from pathlib import Path
import pytest
import yaml
from typer.testing import CliRunner
from specify_cli import app

runner = CliRunner()


def _write_update_zip(zip_path):
    """Create the minimal archive required by the update preflight."""
    import zipfile

    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "extension.yml",
            yaml.safe_dump(
                {
                    "extension": {
                        "id": "test-ext",
                        "name": "Test Ext",
                        "version": "1.1.0",
                    }
                }
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
    assert not (
        project_dir
        / ".specify"
        / "extensions"
        / ".backup"
        / "test-ext-update"
    ).exists()


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

    backup_extension = (
        project_dir
        / ".specify"
        / "extensions"
        / ".backup"
        / "test-ext-update"
        / "extension"
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
    assert not backup_extension.parent.exists()


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

    backup_commands = (
        project_dir
        / ".specify"
        / "extensions"
        / ".backup"
        / "test-ext-update"
        / "commands"
    )
    real_copy2 = shutil.copy2
    command_backup_count = 0

    def fail_second_command_backup(src, dst, *args, **kwargs):
        nonlocal command_backup_count
        dst = Path(dst)
        try:
            dst.resolve().relative_to(backup_commands.resolve())
        except ValueError:
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
    assert not backup_commands.parent.exists()


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
    assert not (
        project_dir
        / ".specify"
        / "extensions"
        / ".backup"
        / "test-ext-update"
    ).exists()
