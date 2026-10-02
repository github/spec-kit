"""Tests for the ``specify check`` command adapter."""

from unittest.mock import patch

from typer.testing import CliRunner

from specify_cli import app
from tests.conftest import strip_ansi


runner = CliRunner()


class TestCheckTip:
    """`specify check` should point users to the existing version check."""

    def test_check_shows_self_check_tip(self):
        with patch("specify_cli.check_tool", return_value=True):
            result = runner.invoke(app, ["check"])

        output = strip_ansi(result.output)
        assert result.exit_code == 0
        assert (
            "Tip: Run 'specify self check' to verify you have the latest CLI version"
            in output
        )

    def test_check_tip_does_not_fetch_latest_release(self):
        with (
            patch("specify_cli.check_tool", return_value=True),
            patch(
                "specify_cli._version._fetch_latest_release_tag",
                side_effect=AssertionError("latest release lookup should not run"),
            ) as fetch_latest,
        ):
            result = runner.invoke(app, ["check"])

        assert result.exit_code == 0
        fetch_latest.assert_not_called()
