from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from tests.specify_cli.bundles.helpers import write_manifest

runner = CliRunner()
REPO_ROOT = Path(__file__).parents[3]


def _make_project(tmp_path: Path, name: str) -> Path:
    project = tmp_path / name
    (project / ".specify").mkdir(parents=True)
    return project


@pytest.mark.parametrize("bundle", [None, "bugfix"])
def test_bundle_init_delegates_without_refresh(project, monkeypatch, bundle):
    from specify_cli.bundles import command_init

    install = Mock()
    monkeypatch.setattr(command_init, "bundle_install", install)

    command_init.bundle_init(bundle, integration=None, offline=True)

    if bundle is None:
        install.assert_not_called()
    else:
        install.assert_called_once_with(
            bundle, integration=None, offline=True, refresh=False,
        )


@pytest.mark.parametrize(
    ("command", "refresh"),
    [("init", False), ("install", False), ("install", True)],
)
def test_bundle_init_preserves_workflow_unless_explicitly_refreshed(
    project, command, refresh,
):
    bundle = REPO_ROOT / "bundles" / "bugfix"
    initial = runner.invoke(app, ["bundle", "init", str(bundle), "--offline"])
    assert initial.exit_code == 0, initial.output
    workflow = project / ".specify/workflows/bugfix/workflow.yml"
    original = workflow.read_bytes()
    edited = original + b"# Local review note: use staging.\r\n"
    workflow.write_bytes(edited)
    registry = project / ".specify/workflows/workflow-registry.json"
    registry_before = registry.read_bytes()
    args = ["bundle", command, str(bundle), "--offline"]
    if refresh:
        args.append("--refresh")

    repeated = runner.invoke(app, args)

    assert repeated.exit_code == 0, repeated.output
    assert workflow.read_bytes() == (original if refresh else edited)
    if not refresh:
        assert registry.read_bytes() == registry_before
        assert "2 already present" in repeated.output
        assert "refreshed" not in repeated.output


def test_bundle_init_rejects_changed_manifest_without_refresh(project):
    bundle = REPO_ROOT / "bundles" / "bugfix"
    initial = runner.invoke(app, ["bundle", "init", str(bundle), "--offline"])
    assert initial.exit_code == 0, initial.output
    records = project / ".specify/bundle-records.json"
    records_before = records.read_bytes()
    workflow = project / ".specify/workflows/bugfix/workflow.yml"
    edited = workflow.read_bytes() + b"# Local review note: use staging.\r\n"
    workflow.write_bytes(edited)
    data = yaml.safe_load((bundle / "bundle.yml").read_text(encoding="utf-8"))
    data["bundle"]["version"] = "999.0.0"
    changed = write_manifest(project / "changed-bundle", data)

    result = runner.invoke(app, ["bundle", "init", str(changed), "--offline"])

    assert result.exit_code == 1, result.output
    assert "--refresh" in result.output
    assert records.read_bytes() == records_before
    assert workflow.read_bytes() == edited


def test_override_symlinked_specify_errors_bundle_init_no_fallback(
    tmp_path, monkeypatch
):
    """A symlinked override .specify must not make bundle init fall back to cwd."""
    web = tmp_path / "web"
    web.mkdir()
    real = tmp_path / "real-specify"
    real.mkdir()
    try:
        (web / ".specify").symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are not available in this environment")

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(web))

    result = runner.invoke(app, ["bundle", "init", "--offline"])
    assert result.exit_code != 0
    assert "symlinked .specify" in result.output
    assert not (elsewhere / ".specify").exists()
