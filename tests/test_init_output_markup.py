"""`specify init` must render user-supplied values literally, not as Rich markup.

`commands/init.py` interpolated the project name, `--integration`/`--script`
values and paths straight into Rich markup f-strings. A name containing a
tag-shaped bracket run was therefore consumed as markup:

* ``specify init "proj [v2]"`` succeeded and created the directory, but the
  Next Steps panel printed ``cd proj`` -- a command that fails when pasted.
* ``specify init "app[/red]x"`` created the directory and then died with
  ``MarkupError``, so the user saw a traceback for a project that had in fact
  been scaffolded.

Every sibling CLI module (extensions, presets, workflows, integrations) already
escapes user-controlled display values; init.py was the outlier.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _strip(text: str) -> str:
    return _ANSI.sub("", text or "")


def _init(tmp_path: Path, name: str):
    """Run a fully offline, non-interactive `specify init <name>`."""
    previous = os.getcwd()
    os.chdir(tmp_path)
    try:
        return CliRunner().invoke(
            app,
            [
                "init",
                name,
                "--integration",
                "generic",
                "--integration-options",
                "--commands-dir .agent/commands",
                "--ignore-agent-tools",
                "--offline",
            ],
            catch_exceptions=True,
        )
    finally:
        os.chdir(previous)


@pytest.mark.parametrize("name", ["proj [v2]", "my[bold]app"])
def test_next_steps_cd_shows_the_real_project_name(tmp_path: Path, name: str):
    """The `cd` line must name the directory that was actually created."""
    result = _init(tmp_path, name)
    assert result.exit_code == 0, _strip(result.stdout)
    assert (tmp_path / name).is_dir()

    out = _strip(result.stdout)
    cd_lines = [line for line in out.splitlines() if "cd " in line]
    assert cd_lines, out
    assert f"cd {name}" in " ".join(cd_lines), cd_lines


def test_closing_tag_in_project_name_does_not_crash(tmp_path: Path):
    """A name forming a closing tag raised MarkupError *after* the project had
    been created, so init reported failure for work it had completed."""
    name = "app[/red]x"
    result = _init(tmp_path, name)

    assert result.exception is None or not isinstance(
        result.exception, Exception
    ) or "MarkupError" not in type(result.exception).__name__, (
        f"unexpected {type(result.exception).__name__}: {result.exception}"
    )
    assert result.exit_code == 0, _strip(result.stdout)
    assert (tmp_path / name).is_dir()
    assert f"cd {name}" in _strip(result.stdout)


def test_invalid_integration_value_is_rendered_literally(tmp_path: Path):
    """An invalid `--integration` value is echoed back; it must not be parsed as
    markup (nor raise) when it contains a bracket run."""
    previous = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = CliRunner().invoke(
            app,
            ["init", "proj", "--integration", "nope[/red]", "--ignore-agent-tools"],
            catch_exceptions=True,
        )
    finally:
        os.chdir(previous)

    assert result.exit_code != 0
    assert "nope[/red]" in _strip(result.stdout)
