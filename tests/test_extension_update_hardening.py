from specify_cli.extensions import ExtensionManager, ExtensionRegistry, ExtensionCatalog
import pytest
import yaml
from typer.testing import CliRunner
from specify_cli import app

runner = CliRunner()

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

    # Force failure in download_extension to trigger rollback
    def mock_download_fail(*args, **kwargs):
        # Corrupt the config BEFORE rollback is triggered
        config_path.write_text(yaml.dump("CORRUPTED"))
        raise Exception("Download failed")

    monkeypatch.setattr(ExtensionCatalog, "get_extension_info", lambda self, ext_id: {"id": "test-ext", "name": "Test Ext", "version": "1.1.0", "download_url": "https://example.com/ext.zip"})
    monkeypatch.setattr(ExtensionCatalog, "download_extension", mock_download_fail)
    monkeypatch.setattr("typer.confirm", lambda _: True)

    result = runner.invoke(app, ["extension", "update", "test-ext"], obj={"project_root": project_dir})

    # Should handle Exception and NOT crash with AttributeError during rollback
    assert result.exit_code == 1
    assert "Download failed" in result.output
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

    # Fail at download (step 5, after the command backup in step 3). Delete the
    # originals first to simulate an install clobbering them, forcing rollback
    # to rely entirely on the backups.
    def mock_download_fail(self, ext_id):
        plan_file.unlink()
        tasks_file.unlink()
        raise Exception("Download failed")

    monkeypatch.setattr(ExtensionCatalog, "download_extension", mock_download_fail)
    monkeypatch.setattr("typer.confirm", lambda _: True)

    result = runner.invoke(app, ["extension", "update", "test-ext"], obj={"project_root": project_dir})

    assert result.exit_code == 1
    # Rollback must restore EACH skill's own content, not a single collided copy.
    assert plan_file.exists() and tasks_file.exists()
    assert plan_file.read_text() == "PLAN CONTENT"
    assert tasks_file.read_text() == "TASKS CONTENT"
