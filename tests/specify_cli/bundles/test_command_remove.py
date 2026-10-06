from __future__ import annotations

import io  # noqa: F401
import json  # noqa: F401
from pathlib import Path
from unittest.mock import patch  # noqa: F401

import pytest
import yaml  # noqa: F401
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles.packager import build_bundle  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401
from tests.specify_cli.bundles.helpers import (
    valid_manifest_dict,
)

runner = CliRunner()


def test_remove_reports_clean_error_when_primitive_raises_raw_exception(
    project: Path,
):
    """A raw exception from a primitive installer (e.g. an OSError from an
    unreadable workflow registry surfacing through _WorkflowKindManager's
    fail-closed construction) must not propagate uncaught through
    `specify bundle remove` -- the command only catches BundlerError, so
    without a conversion at the remove_bundle boundary this would exit
    with an unhandled exception and empty/raw output instead of a clean,
    actionable message, and no removal side effects should occur either."""
    from specify_cli.bundles.manifest import BundleManifest
    from specify_cli.bundles.records import load_records
    from specify_cli.bundles.adapters import DefaultPrimitiveInstaller
    from specify_cli.bundles.installer import install_bundle
    from specify_cli.bundles.resolver import resolve_install_plan
    from tests.specify_cli.bundles.helpers import FakeInstaller

    manifest = BundleManifest.from_dict(valid_manifest_dict())
    plan = resolve_install_plan(
        manifest, speckit_version="0.11.2", active_integration="copilot"
    )
    install_bundle(project, plan, FakeInstaller(), manifest=manifest)

    def boom(self, project_root, component):
        raise OSError("workflow registry unreadable")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(DefaultPrimitiveInstaller, "is_installed", boom)
        result = runner.invoke(app, ["bundle", "remove", "demo-bundle"])

    assert result.exit_code != 0
    assert result.output.strip() != ""
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert {r.bundle_id for r in load_records(project)} == {"demo-bundle"}
