from __future__ import annotations

import io  # noqa: F401
import json  # noqa: F401
from pathlib import Path
from unittest.mock import patch  # noqa: F401

import yaml  # noqa: F401
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles.packager import build_bundle  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401

runner = CliRunner()


def test_catalog_remove_builtin_is_refused(project: Path):
    result = runner.invoke(app, ["bundle", "catalog", "remove", "default"])
    assert result.exit_code == 1
    assert "built-in" in result.output
