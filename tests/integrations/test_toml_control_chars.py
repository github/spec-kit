"""
Regression tests for control characters in the TOML renderers (issue #3340).

TOML forbids raw control characters (U+0000-U+001F except tab and newline,
plus U+007F) in every string form, and a bare CR outside a CRLF pair. Both
renderers previously emitted them verbatim, producing files that parsers
reject.
"""

import tomllib

import pytest

from specify_cli.agents import CommandRegistrar
from specify_cli.integrations.base import TomlIntegration, toml_escape_basic

CTRL_SAMPLES = [
    pytest.param("ab\x07cd", id="bell"),
    pytest.param("ab\x00cd", id="nul"),
    pytest.param("ab\x1bcd", id="escape"),
    pytest.param("ab\x7fcd", id="del"),
    pytest.param("ab\rcd", id="bare-cr"),
    pytest.param("line1\nbad\x07line\n", id="multiline-with-bell"),
    pytest.param('has """ and \x07', id="delimiters-and-ctrl"),
    pytest.param("C:\\Users\\x \x1b", id="backslash-and-ctrl"),
]


class TestTomlEscapeBasic:
    @pytest.mark.parametrize("value", CTRL_SAMPLES)
    def test_round_trips_as_basic_string(self, value: str):
        parsed = tomllib.loads(f'v = "{toml_escape_basic(value)}"')
        assert parsed["v"] == value

    def test_plain_strings_unchanged(self):
        assert toml_escape_basic("plain text") == "plain text"


class TestRenderTomlString:
    @pytest.mark.parametrize("value", CTRL_SAMPLES)
    def test_round_trips(self, value: str):
        rendered = TomlIntegration._render_toml_string(value)
        parsed = tomllib.loads(f"prompt = {rendered}")
        assert parsed["prompt"] == value

    def test_issue_repro(self):
        # Verbatim repro from #3340.
        rendered = TomlIntegration._render_toml_string("a\x07b")
        assert tomllib.loads(f"prompt = {rendered}")["prompt"] == "a\x07b"

    def test_clean_single_line_output_unchanged(self):
        assert TomlIntegration._render_toml_string("simple value") == '"simple value"'

    def test_clean_multiline_still_uses_multiline_form(self):
        rendered = TomlIntegration._render_toml_string("line1\nline2")
        assert rendered.startswith('"""')
        assert tomllib.loads(f"prompt = {rendered}")["prompt"] == "line1\nline2"

    def test_crlf_pairs_stay_in_multiline_form(self):
        # CRLF pairs are legal raw in multiline strings; the parser
        # normalizes them to LF per the TOML newline rules.
        value = "line1\r\nline2\r\n"
        rendered = TomlIntegration._render_toml_string(value)
        assert rendered.startswith('"""')
        parsed = tomllib.loads(f"prompt = {rendered}")["prompt"]
        assert parsed == "line1\nline2\n"

    def test_tab_stays_raw(self):
        assert TomlIntegration._render_toml_string("a\tb") == '"a\tb"'


class TestRenderTomlCommand:
    @pytest.fixture()
    def registrar(self):
        return CommandRegistrar()

    @pytest.mark.parametrize("value", CTRL_SAMPLES)
    def test_body_round_trips(self, registrar, value: str):
        content = registrar.render_toml_command({}, value, "ext")
        assert tomllib.loads(content)["prompt"] == value

    @pytest.mark.parametrize("value", CTRL_SAMPLES)
    def test_description_round_trips(self, registrar, value: str):
        content = registrar.render_toml_command({"description": value}, "body", "ext")
        parsed = tomllib.loads(content)
        assert parsed["description"] == value
        # The multiline prompt form appends a trailing newline by design.
        assert parsed["prompt"] == "body\n"

    def test_clean_body_still_uses_multiline_form(self, registrar):
        content = registrar.render_toml_command({}, "line1\nline2", "ext")
        assert 'prompt = """' in content
        assert tomllib.loads(content)["prompt"] == "line1\nline2\n"
