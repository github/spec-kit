"""Tests for the update-check helper in specify_cli.__init__.

Covers issue https://github.com/github/spec-kit/issues/1320 — the CLI should
nudge users who are running outdated releases toward an upgrade, without
blocking any command when offline or rate-limited.
"""

import json
import time
import urllib.error
from io import StringIO
from unittest.mock import patch

import pytest

from specify_cli import (
    _check_for_updates,
    _fetch_latest_version,
    _parse_version_tuple,
    _read_update_check_cache,
    _write_update_check_cache,
)


class TestParseVersionTuple:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("v0.6.2", (0, 6, 2)),
            ("0.6.2", (0, 6, 2)),
            ("V1.2.3.4", (1, 2, 3, 4)),
            ("0.6.2.dev0", (0, 6, 2)),
            ("1.0.0-rc.1", (1, 0, 0)),
            ("1.0.0+meta", (1, 0, 0)),
        ],
    )
    def test_parses_common_version_strings(self, raw, expected):
        assert _parse_version_tuple(raw) == expected

    @pytest.mark.parametrize("raw", ["", "abc", "v.", None])
    def test_returns_none_on_unparseable(self, raw):
        assert _parse_version_tuple(raw) is None

    def test_ordering_matches_semver_intuition(self):
        assert _parse_version_tuple("v0.6.2") < _parse_version_tuple("v0.6.3")
        assert _parse_version_tuple("v0.6.2") < _parse_version_tuple("v0.7.0")
        assert _parse_version_tuple("v0.6.2") == _parse_version_tuple("0.6.2")


class TestCache:
    def test_fresh_cache_is_returned(self, tmp_path):
        cache_file = tmp_path / "version_check.json"
        cache_file.write_text(json.dumps({"checked_at": time.time(), "latest": "v0.7.0"}))
        data = _read_update_check_cache(cache_file)
        assert data is not None
        assert data["latest"] == "v0.7.0"

    def test_stale_cache_is_ignored(self, tmp_path):
        cache_file = tmp_path / "version_check.json"
        very_old = time.time() - (48 * 60 * 60)
        cache_file.write_text(json.dumps({"checked_at": very_old, "latest": "v0.5.0"}))
        assert _read_update_check_cache(cache_file) is None

    def test_missing_cache_returns_none(self, tmp_path):
        assert _read_update_check_cache(tmp_path / "missing.json") is None

    def test_corrupt_cache_returns_none(self, tmp_path):
        cache_file = tmp_path / "version_check.json"
        cache_file.write_text("{not json")
        assert _read_update_check_cache(cache_file) is None

    def test_write_round_trips(self, tmp_path):
        cache_file = tmp_path / "nested" / "version_check.json"
        _write_update_check_cache(cache_file, "v0.9.9")
        assert cache_file.exists()
        data = json.loads(cache_file.read_text())
        assert data["latest"] == "v0.9.9"
        assert float(data["checked_at"]) <= time.time()


class TestFetchLatestVersion:
    def test_returns_tag_on_success(self):
        payload = json.dumps({"tag_name": "v0.6.3"}).encode("utf-8")

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return payload

        with patch("urllib.request.urlopen", return_value=FakeResp()):
            assert _fetch_latest_version() == "v0.6.3"

    def test_returns_none_on_network_error(self):
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
            assert _fetch_latest_version() is None

    def test_returns_none_on_malformed_json(self):
        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return b"not json"

        with patch("urllib.request.urlopen", return_value=FakeResp()):
            assert _fetch_latest_version() is None

    def test_returns_none_when_tag_missing(self):
        payload = json.dumps({"name": "unnamed"}).encode("utf-8")

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return payload

        with patch("urllib.request.urlopen", return_value=FakeResp()):
            assert _fetch_latest_version() is None


class TestCheckForUpdates:
    """End-to-end-ish checks on `_check_for_updates` with skip conditions patched off."""

    def _run_and_capture(self, monkeypatch) -> str:
        """Force the skip-guard off so the helper runs, then capture console output."""
        # Guard returns False → helper proceeds.
        monkeypatch.setattr("specify_cli._should_skip_update_check", lambda: False)
        buf = StringIO()
        import specify_cli
        from rich.console import Console
        captured = Console(file=buf, force_terminal=False, width=200)
        monkeypatch.setattr(specify_cli, "console", captured)
        _check_for_updates()
        return buf.getvalue()

    def test_prints_warning_when_newer_release_available(self, monkeypatch, tmp_path):
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.6.2")
        monkeypatch.setattr(
            "specify_cli._update_check_cache_path", lambda: tmp_path / "vc.json"
        )
        monkeypatch.setattr("specify_cli._fetch_latest_version", lambda: "v0.7.0")

        out = self._run_and_capture(monkeypatch)

        assert "new spec-kit version is available" in out
        assert "v0.7.0" in out
        assert "v0.6.2" in out
        assert "uv tool install specify-cli" in out

    def test_no_output_when_up_to_date(self, monkeypatch, tmp_path):
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.7.0")
        monkeypatch.setattr(
            "specify_cli._update_check_cache_path", lambda: tmp_path / "vc.json"
        )
        monkeypatch.setattr("specify_cli._fetch_latest_version", lambda: "v0.7.0")

        out = self._run_and_capture(monkeypatch)

        assert out == ""

    def test_uses_cache_when_fresh(self, monkeypatch, tmp_path):
        cache_file = tmp_path / "vc.json"
        cache_file.write_text(json.dumps({"checked_at": time.time(), "latest": "v0.7.0"}))

        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.6.2")
        monkeypatch.setattr("specify_cli._update_check_cache_path", lambda: cache_file)

        call_counter = {"n": 0}

        def _should_not_be_called() -> str | None:
            call_counter["n"] += 1
            return None

        monkeypatch.setattr("specify_cli._fetch_latest_version", _should_not_be_called)

        out = self._run_and_capture(monkeypatch)

        assert call_counter["n"] == 0
        assert "v0.7.0" in out

    def test_network_failure_is_silent(self, monkeypatch, tmp_path):
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.6.2")
        monkeypatch.setattr(
            "specify_cli._update_check_cache_path", lambda: tmp_path / "vc.json"
        )
        monkeypatch.setattr("specify_cli._fetch_latest_version", lambda: None)

        out = self._run_and_capture(monkeypatch)

        assert out == ""

    def test_opt_in_default_off_short_circuits(self, monkeypatch, tmp_path):
        """Without SPECIFY_ENABLE_UPDATE_CHECK the helper must not hit the network."""
        monkeypatch.delenv("SPECIFY_ENABLE_UPDATE_CHECK", raising=False)

        fetched = {"called": False}

        def _fetch():
            fetched["called"] = True
            return "v99.0.0"

        monkeypatch.setattr("specify_cli._fetch_latest_version", _fetch)
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.0.1")
        monkeypatch.setattr(
            "specify_cli._update_check_cache_path", lambda: tmp_path / "vc.json"
        )

        _check_for_updates()

        assert fetched["called"] is False

    def test_opt_in_env_var_allows_check(self, monkeypatch, tmp_path):
        """With SPECIFY_ENABLE_UPDATE_CHECK=1 and a TTY, the helper proceeds."""
        monkeypatch.setenv("SPECIFY_ENABLE_UPDATE_CHECK", "1")
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)

        fetched = {"called": False}

        def _fetch():
            fetched["called"] = True
            return "v99.0.0"

        monkeypatch.setattr("specify_cli._fetch_latest_version", _fetch)
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.0.1")
        monkeypatch.setattr(
            "specify_cli._update_check_cache_path", lambda: tmp_path / "vc.json"
        )

        _check_for_updates()

        assert fetched["called"] is True

    def test_ci_suppresses_even_when_opted_in(self, monkeypatch, tmp_path):
        """Belt-and-suspenders: CI=1 wins over the opt-in flag.

        Pin isatty()=True so this test fails if the CI guard is removed —
        otherwise pytest's stdout capture makes isatty False and the TTY
        guard alone would suppress the fetch, masking a regression.
        """
        monkeypatch.setenv("SPECIFY_ENABLE_UPDATE_CHECK", "1")
        monkeypatch.setenv("CI", "1")
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)

        fetched = {"called": False}

        def _fetch():
            fetched["called"] = True
            return "v99.0.0"

        monkeypatch.setattr("specify_cli._fetch_latest_version", _fetch)
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.0.1")
        monkeypatch.setattr(
            "specify_cli._update_check_cache_path", lambda: tmp_path / "vc.json"
        )

        _check_for_updates()

        assert fetched["called"] is False
