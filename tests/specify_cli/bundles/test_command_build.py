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
from tests.specify_cli.bundles.helpers import (
    valid_manifest_dict,
)

runner = CliRunner()


def test_build_produces_artifact(project: Path):
    (project / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    (project / "README.md").write_text("# Demo", encoding="utf-8")
    result = runner.invoke(app, ["bundle", "build", "--output", str(project / "dist")])
    assert result.exit_code == 0, result.output
    artifacts = list((project / "dist").glob("*.zip"))
    assert len(artifacts) == 1


def test_build_escapes_markup_in_output_path(project: Path):
    """The build success line echoes a caller-supplied ``--output`` path.

    Brackets are legal in a directory name on both POSIX and Windows, so the
    artifact is built and *then* misreported: ``[bold]`` is consumed as a style
    tag, and the success line names a path that does not exist on disk.

    A closing tag (``[/red]``) would raise MarkupError outright, but ``/`` is a
    path separator on Windows, so this uses the silent-swallow form to keep the
    fixture portable.
    """
    (project / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    (project / "README.md").write_text("# Demo", encoding="utf-8")
    out_dir = project / "dist[bold]out"

    result = runner.invoke(app, ["bundle", "build", "--output", str(out_dir)])

    assert result.exit_code == 0, repr(result.exception)
    assert list(out_dir.glob("*.zip")), "the artifact should still be built"
    # Join across Rich's wrap points: the success line prints an absolute path,
    # so the console folds it mid-token whenever the temp directory is long
    # enough, which is a property of the runner's path, not of the escaping.
    assert "dist[bold]out" in "".join(strip_ansi(result.output).split()), (
        "the reported path must match the directory actually written"
    )
