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
from specify_cli.commands.init import (
    _install_extension_during_init,
    _shell_quote_arg,
)

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


def test_install_extension_during_init_reports_malformed_url_cleanly(tmp_path: Path):
    """A malformed extension URL must raise a clean ValueError, not leak the
    raw urllib message.

    An unterminated/invalid bracketed IPv6 authority (e.g.
    "https://[not-an-ip]/x.zip") makes ``urlparse()`` itself raise
    ``ValueError`` (this became eager in Python 3.14; it was previously lazy,
    raised only on ``.hostname`` access). ``_install_extension_during_init``
    parsed the spec unguarded, so `specify init --extension <bad-url>` showed
    "failed: 'not-an-ip' does not appear to be an IPv4 or IPv6 address"
    instead of an actionable message. Every sibling URL entry point
    (extensions/__init__.py, presets/__init__.py, workflows/catalog.py,
    extensions/_commands.py) already guards this exact case.
    """
    (tmp_path / ".specify").mkdir()
    with pytest.raises(ValueError, match="Malformed extension URL"):
        _install_extension_during_init(
            tmp_path, "https://[not-an-ip]/ext.zip", "1.0.0"
        )


def test_install_extension_during_init_lazy_hostname_valueerror_reported_cleanly(
    tmp_path: Path, monkeypatch
):
    """Synthetic defensive coverage for Python 3.11-3.13's lazy validation.

    On those interpreters ``urlparse()`` itself succeeds for a malformed
    bracketed authority; the ``ValueError`` only fires when ``.hostname`` is
    read. This monkeypatches ``urlparse`` to return an object whose
    ``.hostname`` raises lazily, exercising that path on any interpreter so
    the guard isn't only proven on whichever Python happens to raise eagerly.
    """
    import urllib.parse

    real_urlparse = urllib.parse.urlparse

    class _LazyHostnameRaiser:
        def __init__(self, parsed):
            self._parsed = parsed

        @property
        def hostname(self):
            raise ValueError("simulated lazy IPv6 hostname failure")

        def __getattr__(self, name):
            return getattr(self._parsed, name)

    def _fake_urlparse(url, *args, **kwargs):
        return _LazyHostnameRaiser(real_urlparse(url, *args, **kwargs))

    monkeypatch.setattr(urllib.parse, "urlparse", _fake_urlparse)

    (tmp_path / ".specify").mkdir()
    with pytest.raises(ValueError, match="Malformed extension URL"):
        _install_extension_during_init(
            tmp_path, "https://example.com/ext.zip", "1.0.0"
        )


@pytest.mark.skipif(os.name != "nt", reason="drive-letter/URL-scheme collision is Windows-only")
def test_install_extension_during_init_bracketed_windows_path_not_misreported_as_url(
    tmp_path: Path,
):
    """A bracketed absolute Windows path must be handled as a local path,
    not misclassified as a malformed URL.

    ``urlparse("C://[my-ext]")`` parses with scheme ``"c"`` (a bare drive
    letter looks like a URL scheme to urlparse) and a netloc of ``"[my-ext]"``
    (the doubled slash right after the drive letter is what triggers netloc
    capture); on Python 3.14, ``urlparse()`` itself eagerly raises
    ``ValueError`` for that bracketed authority. If URL parsing ran before
    the local-path check, a real extension directory spec'd this way would
    be misreported as "Malformed extension URL" instead of being looked up
    on disk. The path doesn't need to exist for this: what matters is which
    branch handles it -- local-path failure ("Directory not found") proves
    it was never treated as a URL.
    """
    drive = tmp_path.drive or "C:"
    spec = f"{drive}//[nonexistent-bracketed-ext]"

    with pytest.raises(ValueError, match="Directory not found") as excinfo:
        _install_extension_during_init(tmp_path, spec, "1.0.0")

    assert "Malformed extension URL" not in str(excinfo.value)
