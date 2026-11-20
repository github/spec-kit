"""Best-effort Python metadata parsing must not disrupt artifact commands."""

from __future__ import annotations

import ast
import json
import warnings
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.artifacts import catalog


COMMANDS = [
    ["artifact", "list", "--json"],
    ["artifact", "info", "script:deploy", "--json"],
    ["artifact", "info", "command:speckit.plan", "--json"],
]


def _write_python_script(project: Path, source: str) -> None:
    templates = project / ".specify" / "templates"
    scripts = templates / "scripts" / "python"
    scripts.mkdir(parents=True)
    commands = templates / "commands"
    commands.mkdir()
    (commands / "deploy.md").write_text(
        "---\nscripts:\n  py: scripts/python/deploy.py\n---\nDeploy.\n",
        encoding="utf-8",
    )
    (project / ".specify" / "init-options.json").write_text(
        json.dumps({"script": "py"}), encoding="utf-8"
    )
    (scripts / "deploy.py").write_text(source, encoding="utf-8")


def _assert_script_description(payload, command, expected):
    if command[1] == "list":
        assert (
            next(row for row in payload if row["id"] == "script:deploy")["description"]
            == expected
        )
    elif command[2] == "script:deploy":
        assert payload["description"] == expected
    else:
        assert payload["id"] == "command:speckit.plan"


@pytest.mark.parametrize(
    "expression",
    ["1+" * 9999 + "1", "+" * 6000 + "1", "def broken(:", "\0"],
    ids=["deep-addition", "deep-unary", "invalid-syntax", "nul-character"],
)
@pytest.mark.parametrize("command", COMMANDS)
def test_parser_failures_use_comment_fallback(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    expression: str,
    command: list[str],
):
    _write_python_script(spec_kit_project, "# Deployment helper\n" + expression + "\n")
    monkeypatch.chdir(spec_kit_project)

    result = CliRunner().invoke(app, command)

    assert result.exit_code == 0, result.exception
    assert result.stderr == ""
    _assert_script_description(json.loads(result.stdout), command, "Deployment helper")


@pytest.mark.parametrize("command", COMMANDS)
def test_metadata_parse_suppresses_warnings_without_changing_filters(
    spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch, command: list[str]
):
    _write_python_script(
        spec_kit_project,
        '# Header\n"""Deployment helper."""\nimport re\nre.compile("\\d+")\n'
        'raise RuntimeError("Inventory must never execute this script")\n',
    )
    monkeypatch.chdir(spec_kit_project)
    with warnings.catch_warnings(record=True) as emitted:
        warnings.simplefilter("always")
        filters = warnings.filters.copy()
        result = CliRunner().invoke(app, command)
        assert warnings.filters == filters

    assert result.exit_code == 0, result.exception
    assert result.stderr == ""
    assert emitted == []
    _assert_script_description(json.loads(result.stdout), command, "Deployment helper.")


@pytest.mark.parametrize("command", COMMANDS)
def test_metadata_does_not_invoke_full_module_parser(
    spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch, command: list[str]
):
    _write_python_script(
        spec_kit_project,
        '# Header\n"""Deployment helper."""\ntype FeatureId = str\n',
    )
    monkeypatch.chdir(spec_kit_project)
    parse = ast.parse
    filters = warnings.filters.copy()

    def reject_module_parse(*args, **kwargs):
        raise AssertionError("Metadata must not parse the full module")

    monkeypatch.setattr(
        catalog,
        "ast",
        SimpleNamespace(parse=reject_module_parse, literal_eval=ast.literal_eval),
    )
    result = CliRunner().invoke(app, command)

    assert ast.parse is parse
    assert warnings.filters == filters
    assert result.exit_code == 0, result.exception
    assert result.stderr == ""
    _assert_script_description(json.loads(result.stdout), command, "Deployment helper.")


@pytest.mark.parametrize("command", COMMANDS)
def test_description_does_not_parse_newer_syntax_after_docstring(
    spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch, command: list[str]
):
    _write_python_script(
        spec_kit_project,
        '# -*- coding: utf-8 -*-\n"""Deployment helper."""\ntype FeatureId = str\n',
    )
    monkeypatch.chdir(spec_kit_project)
    result = CliRunner().invoke(app, command)
    assert result.exit_code == 0, result.exception
    assert result.stderr == ""
    _assert_script_description(json.loads(result.stdout), command, "Deployment helper.")


def test_overlapping_metadata_requests_preserve_warning_filters():
    import subprocess
    import sys
    import textwrap

    source = textwrap.dedent("""\
        import ast
        import warnings
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event, Lock
        from types import SimpleNamespace
        from specify_cli.artifacts import catalog

        first_entered, second_entered, first_finished = Event(), Event(), Event()
        lock = Lock()
        calls = 0
        def gated(function):
            def run(source):
                global calls
                with lock:
                    position = calls
                    calls += 1
                if position == 0:
                    first_entered.set()
                    assert second_entered.wait(5)
                elif position == 1:
                    second_entered.set()
                    assert first_finished.wait(5)
                return function(source)
            return run
        catalog.ast = SimpleNamespace(parse=gated(ast.parse),
            literal_eval=gated(ast.literal_eval), get_docstring=ast.get_docstring)
        before = warnings.filters.copy()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(catalog._extract_script_description,
                '\\"\\"\\"Deployment helper.\\"\\"\\"', is_python=True)
            assert first_entered.wait(5)
            second = pool.submit(catalog._extract_script_description,
                '\\"\\"\\"Deployment helper.\\"\\"\\"', is_python=True)
            try:
                assert first.result(timeout=10) == 'Deployment helper.'
            finally:
                first_finished.set()
            assert second.result(timeout=10) == 'Deployment helper.'
        assert warnings.filters == before, 'metadata requests leaked process warning filters'
    """)
    result = subprocess.run(
        [sys.executable, "-c", source], capture_output=True, text=True, timeout=20
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("statement", "expected"),
    [
        ('"""Deployment helper."""', "Deployment helper."),
        ("'''Deployment helper.'''", "Deployment helper."),
        ('"Deployment " "helper."', "Deployment helper."),
        ('(("Deployment "\n# joining comment\nr"helper."))', "Deployment helper."),
        ('u"Deployment " R"helper."', "Deployment helper."),
        ('"Deployment " \\\n"helper."', "Deployment helper."),
        ('"""\n    Deployment helper.\n    Details.\n"""', "Deployment helper."),
        ('"Deployment helper."; type FeatureId = str', "Deployment helper."),
        (r'r"Path \d+\new"', r"Path \d+\new"),
        (r'"Path \d+"', r"Path \d+"),
        (r'"Deploy\thelper."', "Deploy  helper."),
        (r'"Escaped \\d"', r"Escaped \d"),
        (r'"Octal \400 \7777"', "Octal " + chr(0o400) + " " + chr(0o777) + "7"),
        (r'"Unicode \u0041 \U00000042 \N{LATIN CAPITAL LETTER C}"', "Unicode A B C"),
        ('"Line\\\ncontinued."', "Linecontinued."),
        ('b"Not a docstring"', "Deployment header"),
        ('f"Not a docstring"', "Deployment header"),
        ('rf"Not a docstring"', "Deployment header"),
        ('("Not a docstring",)', "Deployment header"),
        ('("Not a docstring") "extra"', "Deployment header"),
        ('"Not a docstring" ("argument")', "Deployment header"),
        ('(("Not a docstring") "extra")', "Deployment header"),
        ('("Not a docstring" + "extra")', "Deployment header"),
        ('(() "Not a docstring")', "Deployment header"),
        (r'"Malformed \x4"', "Deployment header"),
        (r'"Malformed \u12"', "Deployment header"),
        (r'"Malformed \U00110000"', "Deployment header"),
        (r'"Malformed \N{UNKNOWN UNICODE NAME}"', "Deployment header"),
        ('"""Unterminated', "Deployment header"),
        ('("   ")', "Deployment header"),
    ],
)
@pytest.mark.parametrize("command", COMMANDS[:2])
def test_leading_string_semantics_without_compiler_warnings(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    statement: str,
    expected: str,
    command: list[str],
):
    _write_python_script(
        spec_kit_project,
        "# Deployment header\n"
        + statement
        + '\ntype FeatureId = str\nraise RuntimeError("must not execute")\n',
    )
    monkeypatch.chdir(spec_kit_project)
    with warnings.catch_warnings(record=True) as emitted:
        warnings.simplefilter("always")
        filters = warnings.filters.copy()
        result = CliRunner().invoke(app, command)
        assert warnings.filters == filters
    assert result.exit_code == 0, result.exception
    assert result.stderr == ""
    assert emitted == []
    _assert_script_description(json.loads(result.stdout), command, expected)


@pytest.mark.parametrize("command", COMMANDS[:2])
def test_python_string_expression_is_not_a_docstring(
    spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch, command: list[str]
):
    _write_python_script(spec_kit_project, '"""Not a docstring""" + "suffix"\n')
    monkeypatch.chdir(spec_kit_project)
    result = CliRunner().invoke(app, command)
    assert result.exit_code == 0, result.exception
    assert result.stderr == ""
    _assert_script_description(json.loads(result.stdout), command, "")
