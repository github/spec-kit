"""Tests for the ``specify version`` command adapter."""

import json
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specify_cli import app


runner = CliRunner()


class TestVersionCommand:
    """Test the `specify version` subcommand."""

    def test_version_features_text(self):
        """specify version --features prints local capability flags."""
        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            result = runner.invoke(app, ["version", "--features"])

        assert result.exit_code == 0
        assert "Spec Kit CLI: 1.2.3" in result.output
        assert "Features:" in result.output
        assert "- controlled multi install integrations: yes" in result.output
        assert "- integration use command: yes" in result.output
        assert "- self check command: yes" in result.output

    def test_version_features_json(self):
        """specify version --features --json prints machine-readable capabilities."""
        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            result = runner.invoke(app, ["version", "--features", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload == {
            "version": "1.2.3",
            "features": {
                "controlled_multi_install_integrations": True,
                "integration_use_command": True,
                "multi_install_safe_registry_metadata": True,
                "integration_upgrade_command": True,
                "self_check_command": True,
                "workflow_catalog": True,
                "bundled_templates": True,
            },
        }

    def test_version_json_requires_features(self):
        """specify version --json is rejected until a JSON surface exists."""
        result = runner.invoke(app, ["version", "--json"])

        assert result.exit_code != 0
        assert "--json requires --features" in result.output

    def test_version_reports_openssl_runtime(self):
        """specify version reports the OpenSSL runtime the interpreter loaded.

        Regression test for the triage gap in #4433: HTTPS failures on Windows
        are commonly blamed on a PATH-preceded OpenSSL DLL, but ``specify
        version`` reported no OpenSSL information at all, so a report had no way
        to show which runtime was actually in use.
        """
        ssl = pytest.importorskip("ssl")

        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            result = runner.invoke(app, ["version"])

        assert result.exit_code == 0

        expected = ssl.OPENSSL_VERSION
        assert expected, "test host reports no ssl.OPENSSL_VERSION to assert against"
        assert expected in result.output

    def test_version_skips_openssl_row_when_ssl_unavailable(self, monkeypatch):
        """An interpreter built without the ssl extension skips the OpenSSL row.

        ``sys.modules["ssl"] = None`` makes ``import ssl`` raise ImportError,
        simulating a build without ``_ssl``. The command must still succeed —
        only the OpenSSL row is omitted.
        """
        monkeypatch.setitem(sys.modules, "ssl", None)
        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "OpenSSL" not in result.output

    def test_version_skips_openssl_row_when_version_attr_missing(self, monkeypatch):
        """An ssl module without OPENSSL_VERSION also skips the row.

        The implementation reads ``getattr(ssl, "OPENSSL_VERSION", "")``, so an
        importable ssl that lacks the attribute must omit the row rather than
        raise AttributeError.
        """
        monkeypatch.setitem(sys.modules, "ssl", SimpleNamespace())
        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "OpenSSL" not in result.output

    def test_version_features_never_touches_ssl(self, monkeypatch):
        """--features/--json return early and must not require ssl at all."""
        monkeypatch.setitem(sys.modules, "ssl", None)
        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            result = runner.invoke(app, ["version", "--features", "--json"])

        assert result.exit_code == 0
        assert json.loads(result.output)["version"] == "1.2.3"
