"""Tests for the ``specify check`` command adapter."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specify_cli import app
from tests.conftest import strip_ansi


runner = CliRunner()


@pytest.mark.parametrize("external", [False, True])
def test_no_cli_requirement_is_not_classified_as_ide(tmp_path, monkeypatch, external):
    from specify_cli.command_check import _check_external_tools
    from specify_cli._console import StepTracker

    if external:
        tracker = StepTracker("Tools")
        tracker.add("generic", "Generic")
        with patch("specify_cli.command_check.shutil.which") as which:
            assert not _check_external_tools(
                tmp_path, "generic", {"requires": {}}, False, tracker,
            )
        which.assert_not_called()
        from rich.console import Console
        console = Console(width=120)
        with console.capture() as capture:
            console.print(tracker.render())
        output = capture.get()
    else:
        monkeypatch.chdir(tmp_path)
        with patch("specify_cli.check_tool", return_value=True) as check_tool:
            result = runner.invoke(app, ["check"])
        assert result.exit_code == 0, result.output
        assert "none" not in [call.args[0] for call in check_tool.call_args_list]
        output = strip_ansi(result.output)
        assert "None (shared scaffolding only) (no CLI required)" in output
    assert "no CLI required" in output
    assert "IDE-based" not in output


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
