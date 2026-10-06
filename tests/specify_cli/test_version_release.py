"""Tests for release lookup and version comparison behavior.

Network isolation contract (SC-004 / FR-014): every test that exercises
`_fetch_latest_release_tag()` MUST mock the outbound urllib path so no real call
reaches api.github.com. Production always uses an isolated `build_opener`; this
module's autouse fixture routes its `open()` back through the locally mocked
`urlopen`.
"""

import urllib.error
import importlib.metadata
from unittest.mock import MagicMock, patch

import pytest
from specify_cli._download_security import read_response_limited as _real_read_response_limited
from specify_cli._version import (
    _fetch_latest_release_tag,
    _get_installed_version,
    _is_newer,
    _normalize_tag,
)
from tests.http_helpers import (
    mock_urlopen_response,
    route_opener_open_through_urlopen,  # noqa: F401 (autouse fixture)
)

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


class TestIsNewer:
    def test_latest_strictly_greater_returns_true(self):
        assert _is_newer("0.8.0", "0.7.4") is True

    def test_equal_versions_returns_false(self):
        assert _is_newer("0.7.4", "0.7.4") is False

    def test_current_greater_than_latest_returns_false(self):
        assert _is_newer("0.7.0", "0.7.4") is False

    def test_dev_build_ahead_of_release_returns_false(self):
        assert _is_newer("0.7.4", "0.7.5.dev0") is False

    def test_invalid_version_returns_false(self):
        assert _is_newer("not-a-version", "0.7.4") is False

    def test_local_version_containing_unknown_is_not_treated_as_sentinel(self):
        assert _is_newer("1.2.4", "1.2.3+unknown") is True


class TestInstalledVersion:
    def test_invalid_metadata_error_returns_unknown(self):
        invalid_metadata_error = getattr(importlib.metadata, "InvalidMetadataError", None)
        if invalid_metadata_error is None:
            # Python versions without InvalidMetadataError: simulate with a
            # custom exception to verify the guarded except path works.
            class _FakeInvalidMetadataError(Exception):
                pass
            invalid_metadata_error = _FakeInvalidMetadataError
            # Patch the attribute onto importlib.metadata so the production
            # getattr() finds it during this test.
            with patch.object(importlib.metadata, "InvalidMetadataError", invalid_metadata_error, create=True):
                with patch(
                    "importlib.metadata.version",
                    side_effect=invalid_metadata_error("bad metadata"),
                ):
                    assert _get_installed_version() == "unknown"
        else:
            with patch(
                "importlib.metadata.version",
                side_effect=invalid_metadata_error("bad metadata"),
            ):
                assert _get_installed_version() == "unknown"


class TestNormalizeTag:
    def test_strips_single_leading_v(self):
        assert _normalize_tag("v0.7.4") == "0.7.4"

    def test_idempotent_when_no_leading_v(self):
        assert _normalize_tag("0.7.4") == "0.7.4"

    def test_strips_exactly_one_v(self):
        assert _normalize_tag("vv0.7.4") == "v0.7.4"

    def test_empty_string_passthrough(self):
        assert _normalize_tag("") == ""


class TestFailureCategorization:
    def test_urlerror_maps_to_offline(self):
        with patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            side_effect=urllib.error.URLError("no route to host"),
        ):
            tag, reason = _fetch_latest_release_tag()
        assert tag is None
        assert reason == "offline or timeout"

    def test_timeout_maps_to_offline(self):
        with patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            side_effect=TimeoutError(),
        ):
            tag, reason = _fetch_latest_release_tag()
        assert tag is None
        assert reason == "offline or timeout"

    def test_403_maps_to_rate_limited(self):
        with patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            side_effect=_http_error(403, "rate limited"),
        ):
            tag, reason = _fetch_latest_release_tag()
        assert tag is None
        assert reason == _RATE_LIMITED_REASON

    @pytest.mark.parametrize("code", [404, 500, 502])
    def test_other_http_uses_code_string(self, code):
        with patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            side_effect=_http_error(code, "oops"),
        ):
            tag, reason = _fetch_latest_release_tag()
        assert tag is None
        assert reason == f"HTTP {code}"

    def test_generic_exception_propagates(self):
        # Per research D-006, no catch-all exists; RuntimeError MUST bubble.
        with patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            side_effect=RuntimeError("boom"),
        ):
            with pytest.raises(RuntimeError):
                _fetch_latest_release_tag()


class TestBoundedRead:
    """Regression test for the read_response_limited hardening.

    A future refactor could silently revert `_fetch_latest_release_tag` to
    `resp.read()` (the unbounded form) — this test pins the contract that
    the response body is read through ``read_response_limited`` with a
    bounded ``max_bytes``.
    """

    def test_response_body_is_bounded(self):
        recorded: dict[str, int | str] = {}

        def _spy(response, *, max_bytes: int, label: str, **kwargs):
            # max_bytes and label are keyword-only with no defaults: if the
            # caller forgets to pass either, the call raises TypeError here
            # (instead of recording a misleading None).
            recorded["max_bytes"] = max_bytes
            recorded["label"] = label
            # Forward to the real implementation so the function under test
            # still gets a parseable body.
            return _real_read_response_limited(
                response, max_bytes=max_bytes, label=label, **kwargs
            )

        with patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            return_value=mock_urlopen_response({"tag_name": "v9.9.9"}),
        ), patch("specify_cli._version.read_response_limited", side_effect=_spy):
            tag, reason = _fetch_latest_release_tag()

        assert tag == "v9.9.9"
        assert reason is None
        # The cap (1 MiB) is a deliberate ceiling for the GitHub release
        # JSON — keep it explicit so a future refactor that drops the
        # `max_bytes=` argument fails this test instead of regressing
        # silently to the default.
        assert recorded["max_bytes"] == 1024 * 1024
        assert recorded["label"] == "GitHub latest release"


def _capture_request_via_urlopen():
    captured = {}

    def _side_effect(req, *args, **kwargs):
        captured["request"] = req
        return mock_urlopen_response({"tag_name": "v0.7.4"})

    return captured, _side_effect


def _capture_request_via_auth_opener():
    captured = {}

    def _side_effect(req, *args, **kwargs):
        captured["request"] = req
        return mock_urlopen_response({"tag_name": "v0.7.4"})

    opener = MagicMock()
    opener.open.side_effect = _side_effect
    return captured, opener


def _inject_github_config(monkeypatch, token_env="GH_TOKEN"):
    from tests.specify_cli.authentication.helpers import inject_github_config
    inject_github_config(monkeypatch, token_env)


class TestUserStory3:
    def test_gh_token_attached_as_bearer_header(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", SENTINEL_GH_TOKEN)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        _inject_github_config(monkeypatch, token_env="GH_TOKEN")
        captured, opener = _capture_request_via_auth_opener()
        with patch(
            "specify_cli.authentication.http.urllib.request.build_opener",
            return_value=opener,
        ):
            _fetch_latest_release_tag()
        req = captured["request"]
        assert req.get_header("Authorization") == f"Bearer {SENTINEL_GH_TOKEN}"

    def test_github_token_used_when_gh_token_unset(self, monkeypatch):
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.setenv("GITHUB_TOKEN", SENTINEL_GITHUB_TOKEN)
        _inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        captured, opener = _capture_request_via_auth_opener()
        with patch(
            "specify_cli.authentication.http.urllib.request.build_opener",
            return_value=opener,
        ):
            _fetch_latest_release_tag()
        req = captured["request"]
        assert req.get_header("Authorization") == f"Bearer {SENTINEL_GITHUB_TOKEN}"

    def test_no_authorization_header_when_both_unset(self, monkeypatch):
        monkeypatch.delenv("GH_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        captured, side_effect = _capture_request_via_urlopen()
        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=side_effect):
            _fetch_latest_release_tag()
        req = captured["request"]
        assert req.get_header("Authorization") is None

    def test_empty_string_gh_token_treated_as_unset(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        _inject_github_config(monkeypatch, token_env="GH_TOKEN")
        captured, side_effect = _capture_request_via_urlopen()
        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=side_effect):
            _fetch_latest_release_tag()
        req = captured["request"]
        assert req.get_header("Authorization") is None

    def test_whitespace_only_gh_token_treated_as_unset(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "   ")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        _inject_github_config(monkeypatch, token_env="GH_TOKEN")
        captured, side_effect = _capture_request_via_urlopen()
        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=side_effect):
            _fetch_latest_release_tag()
        req = captured["request"]
        assert req.get_header("Authorization") is None

    def test_whitespace_only_gh_token_falls_back_to_github_token(self, monkeypatch):
        monkeypatch.setenv("GH_TOKEN", "   ")
        monkeypatch.setenv("GITHUB_TOKEN", SENTINEL_GITHUB_TOKEN)
        _inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        captured, opener = _capture_request_via_auth_opener()
        with patch(
            "specify_cli.authentication.http.urllib.request.build_opener",
            return_value=opener,
        ):
            _fetch_latest_release_tag()
        req = captured["request"]
        assert req.get_header("Authorization") == f"Bearer {SENTINEL_GITHUB_TOKEN}"
