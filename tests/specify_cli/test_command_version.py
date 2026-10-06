"""Tests for the ``specify version`` command adapter."""

import json
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()

EXPECTED_FEATURES = {
    "controlled_multi_install_integrations": True,
    "integration_use_command": True,
    "multi_install_safe_registry_metadata": True,
    "integration_upgrade_command": True,
    "self_check_command": True,
    "workflow_catalog": True,
    "bundled_templates": True,
}


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

    def test_version_json_emits_complete_stable_payload(self):
        """specify version --json emits the complete machine-readable result."""
        with (
            patch("specify_cli.get_speckit_version", return_value="1.2.3"),
            patch(
                "specify_cli.command_version.platform.python_version",
                return_value="3.13.1",
            ),
            patch(
                "specify_cli.command_version.platform.system",
                return_value="ExampleOS",
            ),
            patch(
                "specify_cli.command_version.platform.machine",
                return_value="example64",
            ),
            patch(
                "specify_cli.command_version.platform.version",
                return_value="ExampleOS 4.5",
            ),
            patch(
                "specify_cli.command_version._openssl_version",
                return_value="OpenSSL 3.4.0",
            ),
        ):
            result = runner.invoke(app, ["version", "--json"])

        expected = {
            "cli_version": "1.2.3",
            "runtime": {
                "python": "3.13.1",
                "openssl": "OpenSSL 3.4.0",
            },
            "system": {
                "platform": "ExampleOS",
                "architecture": "example64",
                "os_version": "ExampleOS 4.5",
            },
            "features": EXPECTED_FEATURES,
        }
        assert result.exit_code == 0
        assert result.stdout == f"{json.dumps(expected, indent=2)}\n"
        assert result.stderr == ""
        assert json.loads(result.stdout) == expected

    def test_version_features_json_is_exact_alias(self):
        """--features does not filter JSON output or change its bytes."""
        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            canonical = runner.invoke(app, ["version", "--json"])
            compatibility = runner.invoke(app, ["version", "--features", "--json"])

        assert canonical.exit_code == 0
        assert compatibility.exit_code == 0
        assert compatibility.stdout == canonical.stdout
        assert compatibility.stderr == canonical.stderr == ""

    def test_version_json_uses_null_when_openssl_unavailable(self, monkeypatch):
        """Missing ssl is represented as a stable JSON null value."""
        monkeypatch.setitem(sys.modules, "ssl", None)
        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            result = runner.invoke(app, ["version", "--json"])

        assert result.exit_code == 0
        assert result.stderr == ""
        assert json.loads(result.stdout)["runtime"]["openssl"] is None

    def test_version_json_sanitizes_unexpected_failures(self):
        """Unexpected failures emit one safe error object and no traceback."""
        unsafe = (
            "\x1b[31mSECRET_TOKEN=do-not-print /Users/example/private/project\x1b[0m"
        )
        with patch(
            "specify_cli.get_speckit_version",
            side_effect=RuntimeError(unsafe),
        ):
            result = runner.invoke(app, ["version", "--json"])

        expected = {
            "error": {
                "code": "internal_error",
                "message": "Unable to collect version information.",
                "details": {},
            },
        }
        assert result.exit_code == 1
        assert result.stdout == ""
        assert result.stderr == f"{json.dumps(expected, indent=2)}\n"
        assert json.loads(result.stderr) == expected
        assert unsafe not in result.stderr
        assert "\x1b" not in result.stderr
        assert "Traceback" not in result.stderr

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
        """The focused human feature view does not require ssl."""
        monkeypatch.setitem(sys.modules, "ssl", None)
        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            result = runner.invoke(app, ["version", "--features"])

        assert result.exit_code == 0
        assert "Spec Kit CLI: 1.2.3" in result.output
