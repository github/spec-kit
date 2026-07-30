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
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.commands.init import _shell_quote_arg

from tests.conftest import requires_bash

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
    assert f"cd {_shell_quote_arg(name)}" in " ".join(cd_lines), cd_lines


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
    assert f"cd {_shell_quote_arg(name)}" in _strip(result.stdout)


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


def _cd_argument(stdout: str) -> str:
    """Return the argument of the printed `cd` command, verbatim.

    The line is rendered inside a Rich panel, so the trailing box-drawing
    border and its padding are stripped before the argument is compared.
    """
    marker = "Go to the project folder: cd "
    for line in _strip(stdout).splitlines():
        if marker in line:
            return line.split(marker, 1)[1].rstrip().rstrip("│").rstrip()
    raise AssertionError(f"no cd line in output:\n{stdout}")


@pytest.mark.parametrize("name", ["proj v2", "my project"])
def test_cd_line_quotes_a_name_containing_whitespace(tmp_path: Path, name: str):
    """Rich-escaping alone left `cd proj v2`, which every shell reads as two
    arguments, so the copy-pasted command did not enter the directory."""
    result = _init(tmp_path, name)
    assert result.exit_code == 0, _strip(result.stdout)
    assert (tmp_path / name).is_dir()

    printed = _cd_argument(result.stdout)
    assert printed != name, "a whitespace-bearing name must be quoted"
    assert name in printed, printed
    assert printed == _shell_quote_arg(name)


def test_ordinary_name_is_not_quoted(tmp_path: Path):
    """The common case must stay byte-identical: no gratuitous quoting."""
    result = _init(tmp_path, "my-project")
    assert result.exit_code == 0, _strip(result.stdout)
    assert _cd_argument(result.stdout) == "my-project"


@requires_bash
@pytest.mark.parametrize("name", ["proj v2", "proj [v2]", "my-project"])
def test_printed_cd_command_actually_changes_directory(tmp_path: Path, name: str):
    """Execute the printed command rather than only inspecting it.

    This is the assertion the string comparisons cannot make: the rendered
    `cd <arg>` is fed to a real shell and must land in the created directory.
    """
    result = _init(tmp_path, name)
    assert result.exit_code == 0, _strip(result.stdout)
    target = tmp_path / name
    assert target.is_dir()

    printed = _cd_argument(result.stdout)
    proc = subprocess.run(
        ["bash", "-c", f"cd {printed} && pwd"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"cd {printed!r} failed: {proc.stderr}"
    assert Path(proc.stdout.strip()).name == name, proc.stdout


def test_shell_quote_arg_is_host_appropriate():
    """The helper follows `_version._render_argv`: list2cmdline on Windows,
    shlex.quote elsewhere. Names needing no quoting round-trip unchanged."""
    assert _shell_quote_arg("my-project") == "my-project"
    quoted = _shell_quote_arg("my project")
    assert quoted != "my project"
    if os.name == "nt":
        assert quoted == '"my project"'
    else:
        assert quoted == "'my project'"
