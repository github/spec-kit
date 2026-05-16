"""Tests for the update-check helper in specify_cli.__init__.

Covers issue https://github.com/github/spec-kit/issues/1320 — the CLI should
nudge users who are running outdated releases toward an upgrade, without
blocking any command when offline or rate-limited.
"""

import json
import time
from io import StringIO

import pytest

from specify_cli._version import (
    _check_for_updates,
    _read_update_check_cache,
    _write_update_check_cache,
)



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

    def test_write_round_trips_negative_entry(self, tmp_path):
        cache_file = tmp_path / "nested" / "version_check.json"
        _write_update_check_cache(cache_file, None)
        assert cache_file.exists()
        data = json.loads(cache_file.read_text())
        assert data["latest"] is None
        assert float(data["checked_at"]) <= time.time()



class TestCheckForUpdates:
    """End-to-end-ish checks on `_check_for_updates` with skip conditions patched off."""

    def _run_and_capture(self, monkeypatch) -> str:
        """Force the skip-guard off so the helper runs, then capture console output."""
        # Guard returns False → helper proceeds.
        monkeypatch.setattr("specify_cli._version._should_skip_update_check", lambda: False)
        buf = StringIO()
        import specify_cli._version
        from rich.console import Console
        captured = Console(file=buf, force_terminal=False, width=200)
        monkeypatch.setattr(specify_cli._version, "console", captured)
        _check_for_updates()
        return buf.getvalue()

    def test_prints_warning_when_newer_release_available(self, monkeypatch, tmp_path):
        monkeypatch.setattr("specify_cli._version._get_installed_version", lambda: "0.6.2")
        monkeypatch.setattr(
            "specify_cli._version._update_check_cache_path", lambda: tmp_path / "vc.json"
        )
        monkeypatch.setattr("specify_cli._version._fetch_latest_release_tag", lambda: ("v0.7.0", None))

        out = self._run_and_capture(monkeypatch)

        assert "new spec-kit version is available" in out
        assert "v0.7.0" in out
        assert "v0.6.2" in out
        assert "uv tool install specify-cli" in out

    def test_no_output_when_up_to_date(self, monkeypatch, tmp_path):
        monkeypatch.setattr("specify_cli._version._get_installed_version", lambda: "0.7.0")
        monkeypatch.setattr(
            "specify_cli._version._update_check_cache_path", lambda: tmp_path / "vc.json"
        )
        monkeypatch.setattr("specify_cli._version._fetch_latest_release_tag", lambda: ("v0.7.0", None))

        out = self._run_and_capture(monkeypatch)

        assert out == ""

    def test_uses_cache_when_fresh(self, monkeypatch, tmp_path):
        cache_file = tmp_path / "vc.json"
        cache_file.write_text(json.dumps({"checked_at": time.time(), "latest": "v0.7.0"}))

        monkeypatch.setattr("specify_cli._version._get_installed_version", lambda: "0.6.2")
        monkeypatch.setattr("specify_cli._version._update_check_cache_path", lambda: cache_file)

        call_counter = {"n": 0}

        def _should_not_be_called() -> tuple[str | None, str | None]:
            call_counter["n"] += 1
            return (None, None)

        monkeypatch.setattr("specify_cli._version._fetch_latest_release_tag", _should_not_be_called)

        out = self._run_and_capture(monkeypatch)

        assert call_counter["n"] == 0
        assert "v0.7.0" in out

    def test_network_failure_is_silent(self, monkeypatch, tmp_path):
        monkeypatch.setattr("specify_cli._version._get_installed_version", lambda: "0.6.2")
        monkeypatch.setattr(
            "specify_cli._version._update_check_cache_path", lambda: tmp_path / "vc.json"
        )
        monkeypatch.setattr("specify_cli._version._fetch_latest_release_tag", lambda: (None, "offline or timeout"))

        out = self._run_and_capture(monkeypatch)

        assert out == ""

    def test_network_failure_writes_negative_cache(self, monkeypatch, tmp_path):
        cache_file = tmp_path / "vc.json"
        monkeypatch.setattr("specify_cli._version._get_installed_version", lambda: "0.6.2")
        monkeypatch.setattr("specify_cli._version._update_check_cache_path", lambda: cache_file)
        monkeypatch.setattr("specify_cli._version._fetch_latest_release_tag", lambda: (None, "offline or timeout"))

        self._run_and_capture(monkeypatch)

        assert cache_file.exists()
        data = json.loads(cache_file.read_text())
        assert data["latest"] is None
        assert time.time() - float(data["checked_at"]) < 5

    def test_negative_cache_skips_fetch_within_ttl(self, monkeypatch, tmp_path):
        cache_file = tmp_path / "vc.json"
        cache_file.write_text(json.dumps({"checked_at": time.time(), "latest": None}))

        monkeypatch.setattr("specify_cli._version._get_installed_version", lambda: "0.6.2")
        monkeypatch.setattr("specify_cli._version._update_check_cache_path", lambda: cache_file)

        call_counter = {"n": 0}

        def _should_not_be_called() -> tuple[str | None, str | None]:
            call_counter["n"] += 1
            return (None, None)

        monkeypatch.setattr("specify_cli._version._fetch_latest_release_tag", _should_not_be_called)

        out = self._run_and_capture(monkeypatch)

        assert call_counter["n"] == 0
        assert out == ""

    def test_opt_in_default_off_short_circuits(self, monkeypatch, tmp_path):
        """Without SPECIFY_ENABLE_UPDATE_CHECK the helper must not hit the network."""
        monkeypatch.delenv("SPECIFY_ENABLE_UPDATE_CHECK", raising=False)

        fetched = {"called": False}

        def _fetch():
            fetched["called"] = True
            return ("v99.0.0", None)

        monkeypatch.setattr("specify_cli._version._fetch_latest_release_tag", _fetch)
        monkeypatch.setattr("specify_cli._version._get_installed_version", lambda: "0.0.1")
        monkeypatch.setattr(
            "specify_cli._version._update_check_cache_path", lambda: tmp_path / "vc.json"
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
            return ("v99.0.0", None)

        monkeypatch.setattr("specify_cli._version._fetch_latest_release_tag", _fetch)
        monkeypatch.setattr("specify_cli._version._get_installed_version", lambda: "0.0.1")
        monkeypatch.setattr(
            "specify_cli._version._update_check_cache_path", lambda: tmp_path / "vc.json"
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
            return ("v99.0.0", None)

        monkeypatch.setattr("specify_cli._version._fetch_latest_release_tag", _fetch)
        monkeypatch.setattr("specify_cli._version._get_installed_version", lambda: "0.0.1")
        monkeypatch.setattr(
            "specify_cli._version._update_check_cache_path", lambda: tmp_path / "vc.json"
        )

        _check_for_updates()

        assert fetched["called"] is False
