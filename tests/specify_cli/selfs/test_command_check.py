"""Command tests for ``specify self check``."""

import urllib.error
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specify_cli import app
from tests.conftest import strip_ansi
from tests.http_helpers import (
    mock_urlopen_response,
    route_opener_open_through_urlopen,  # noqa: F401 (autouse fixture)
)

runner = CliRunner()

SENTINEL_GH_TOKEN = "SENTINEL-GH-TOKEN-VALUE"
SENTINEL_GITHUB_TOKEN = "SENTINEL-GITHUB-TOKEN-VALUE"
_RATE_LIMITED_REASON = (
    "rate limited (configure ~/.specify/auth.json with a GitHub token)"
)


def _http_error(code: int, message: str = "error") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="https://api.github.com/repos/github/spec-kit/releases/latest",
        code=code,
        msg=message,
        hdrs={},  # type: ignore[arg-type]
        fp=None,
    )


_FAILURE_CASES = [
    ("offline or timeout", urllib.error.URLError("down")),
    (_RATE_LIMITED_REASON, _http_error(403)),
    ("HTTP 500", _http_error(500)),
]


class TestUserStory1:
    def test_newer_available_prints_update_and_install_command(self):
        with patch("specify_cli._version._get_installed_version", return_value="0.7.4"), patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            return_value=mock_urlopen_response({"tag_name": "v0.9.0"}),
        ):
            result = runner.invoke(app, ["self", "check"])
        output = strip_ansi(result.output)
        assert result.exit_code == 0
        assert "Update available" in output
        assert "0.7.4" in output
        assert "0.9.0" in output
        assert "git+https://github.com/github/spec-kit.git@v0.9.0" in output

    def test_up_to_date_prints_current_only(self):
        with patch("specify_cli._version._get_installed_version", return_value="0.9.0"), patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            return_value=mock_urlopen_response({"tag_name": "v0.9.0"}),
        ):
            result = runner.invoke(app, ["self", "check"])
        output = strip_ansi(result.output)
        assert result.exit_code == 0
        assert "Up to date: 0.9.0" in output
        assert "Update available" not in output
        assert "git+https://" not in output

    def test_dev_build_ahead_of_release_is_up_to_date(self):
        with patch("specify_cli._version._get_installed_version", return_value="0.7.5.dev0"), patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            return_value=mock_urlopen_response({"tag_name": "v0.7.4"}),
        ):
            result = runner.invoke(app, ["self", "check"])
        output = strip_ansi(result.output)
        assert result.exit_code == 0
        assert "Update available" not in output
        assert "Up to date" in output

    def test_unknown_installed_still_prints_latest_and_reinstall(self):
        with patch("specify_cli._version._get_installed_version", return_value="unknown"), patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            return_value=mock_urlopen_response({"tag_name": "v0.7.4"}),
        ):
            result = runner.invoke(app, ["self", "check"])
        output = strip_ansi(result.output)
        assert result.exit_code == 0
        assert "Current version could not be determined" in output
        assert "Latest release: v0.7.4" in output
        assert "0.7.4" in output
        assert "git+https://github.com/github/spec-kit.git@v0.7.4" in output
        assert "specify self upgrade" in output
        assert "pipx install --force git+https://github.com/github/spec-kit.git@v0.7.4" in output

    def test_unknown_installed_uses_placeholder_when_latest_tag_is_invalid(self):
        with patch("specify_cli._version._get_installed_version", return_value="unknown"), patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            return_value=mock_urlopen_response({"tag_name": "v0.9.0;echo unsafe"}),
        ):
            result = runner.invoke(app, ["self", "check"])
        output = strip_ansi(result.output)
        assert result.exit_code == 0
        assert "Latest release: vX.Y.Z" in output
        assert "Could not validate latest release tag from GitHub." in output
        assert "git+https://github.com/github/spec-kit.git@vX.Y.Z" in output
        assert "v0.9.0;echo unsafe" not in output

    def test_unparseable_tag_reports_validation_failure_without_raw_tag(self):
        with patch("specify_cli._version._get_installed_version", return_value="0.7.4"), patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            return_value=mock_urlopen_response({"tag_name": "not-a-version"}),
        ):
            result = runner.invoke(app, ["self", "check"])
        output = strip_ansi(result.output)
        assert result.exit_code == 0
        assert "Update available" not in output
        assert "Up to date" not in output
        assert "Could not validate latest release tag from GitHub." in output
        assert "Latest release: vX.Y.Z" in output
        assert "0.7.4" in output
        assert "not-a-version" not in output
        assert "git+https://github.com/github/spec-kit.git@vX.Y.Z" in output


class TestUserStory2:
    @pytest.mark.parametrize("expected_reason, side_effect", _FAILURE_CASES)
    def test_failure_prints_installed_plus_one_line_reason(
        self, expected_reason, side_effect
    ):
        with patch("specify_cli._version._get_installed_version", return_value="0.7.4"), patch(
            "specify_cli.authentication.http.urllib.request.urlopen", side_effect=side_effect
        ):
            result = runner.invoke(app, ["self", "check"])
        output = strip_ansi(result.output)
        assert "Installed: 0.7.4" in output
        if expected_reason == _RATE_LIMITED_REASON:
            assert "Could not check latest release: rate limited" in output
            assert "~/.specify/auth.json" in output
        else:
            assert f"Could not check latest release: {expected_reason}" in output

    @pytest.mark.parametrize("_expected_reason, side_effect", _FAILURE_CASES)
    def test_failure_exits_zero(self, _expected_reason, side_effect):
        with patch("specify_cli._version._get_installed_version", return_value="0.7.4"), patch(
            "specify_cli.authentication.http.urllib.request.urlopen", side_effect=side_effect
        ):
            result = runner.invoke(app, ["self", "check"])
        assert result.exit_code == 0

    @pytest.mark.parametrize("_expected_reason, side_effect", _FAILURE_CASES)
    def test_failure_output_contains_no_traceback_no_url(
        self, _expected_reason, side_effect
    ):
        with patch("specify_cli._version._get_installed_version", return_value="0.7.4"), patch(
            "specify_cli.authentication.http.urllib.request.urlopen", side_effect=side_effect
        ):
            result = runner.invoke(app, ["self", "check"])
        combined = strip_ansi((result.output or "") + (result.stderr or ""))
        assert "Traceback" not in combined
        assert "https://api.github.com" not in combined


class TestUserStory3:
    @pytest.mark.parametrize("_reason, side_effect", _FAILURE_CASES)
    def test_gh_token_never_appears_in_failure_output(
        self, _reason, side_effect, monkeypatch
    ):
        monkeypatch.setenv("GH_TOKEN", SENTINEL_GH_TOKEN)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with patch("specify_cli._version._get_installed_version", return_value="0.7.4"), patch(
            "specify_cli.authentication.http.urllib.request.urlopen", side_effect=side_effect
        ):
            result = runner.invoke(app, ["self", "check"])
        combined = strip_ansi((result.output or "") + (result.stderr or ""))
        assert SENTINEL_GH_TOKEN not in combined

    @pytest.mark.parametrize("_reason, side_effect", _FAILURE_CASES)
    def test_github_token_never_appears_in_failure_output(
        self, _reason, side_effect, monkeypatch
    ):
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.setenv("GITHUB_TOKEN", SENTINEL_GITHUB_TOKEN)
        with patch("specify_cli._version._get_installed_version", return_value="0.7.4"), patch(
            "specify_cli.authentication.http.urllib.request.urlopen", side_effect=side_effect
        ):
            result = runner.invoke(app, ["self", "check"])
        combined = strip_ansi((result.output or "") + (result.stderr or ""))
        assert SENTINEL_GITHUB_TOKEN not in combined
