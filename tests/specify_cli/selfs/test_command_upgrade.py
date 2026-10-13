"""Command tests for ``specify self upgrade``."""

from unittest.mock import patch

import pytest

from specify_cli import app
from tests.specify_cli.self_upgrade_helpers import runner, strip_ansi


class TestTagValidation:
    """--tag option parsing and command help."""

    def test_valid_stable_tag(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.7.6"],
            )
        assert result.exit_code == 0

    def test_valid_dev_suffix_tag(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.8.0.dev0"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.8.0.dev0" in strip_ansi(result.output)

    def test_valid_rc_tag(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v1.0.0-rc1"],
            )
        assert result.exit_code == 0

    def test_valid_beta_dot_tag_uses_pep440_equivalent_for_noop(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="1.0.0b1"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--tag", "v1.0.0-beta.1"],
            )
        assert result.exit_code == 0
        assert "Already on requested release: v1.0.0-beta.1" in strip_ansi(
            result.output
        )

    def test_valid_build_metadata_tag(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.8.0+build.42"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.8.0+build.42" in strip_ansi(result.output)

    def test_uppercase_v_prefix_is_folded_to_lowercase(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "V0.7.6"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.7.6" in strip_ansi(result.output)

    def test_valid_prerelease_with_build_metadata_tag(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v1.0.0-rc1+build.42"],
            )
        assert result.exit_code == 0
        assert "Target version: v1.0.0-rc1+build.42" in strip_ansi(result.output)

    @pytest.mark.parametrize(
        "bad_tag",
        [
            "latest",
            "0.7.5",
            "main",
            "v7",
            "",
            "v1.2.3abc",
            "v1.2.3...",
            "v1.2.3++",
            "v\uff11.2.3",
            "v1.\u0662.3",
        ],
    )
    def test_invalid_tags_rejected(self, bad_tag, uv_tool_argv0, clean_environ):
        result = runner.invoke(app, ["self", "upgrade", "--tag", bad_tag])
        assert result.exit_code == 1
        output = strip_ansi(result.output)
        assert "Invalid --tag" in output or "expected vMAJOR.MINOR.PATCH" in output

    def test_rejection_message_keeps_the_suffix_token(
        self, uv_tool_argv0, clean_environ
    ):
        result = runner.invoke(app, ["self", "upgrade", "--tag", "latest"])
        assert result.exit_code == 1
        assert "expected vMAJOR.MINOR.PATCH[suffix]" in strip_ansi(result.output)

    def test_tag_option_help_keeps_the_suffix_token(self):
        result = runner.invoke(app, ["self", "upgrade", "--help"])
        assert result.exit_code == 0
        assert "[suffix]" in strip_ansi(result.output)
