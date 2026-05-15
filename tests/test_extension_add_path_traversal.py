"""Tests for path traversal guard in `specify extension add --from` (GHSA-67q9-p54f-7cpr).

The extension argument is used to construct a temporary ZIP download path.
Without sanitisation, absolute paths or ``../`` segments in the argument can
escape the intended cache directory, causing arbitrary file writes and deletes.
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()

TRAVERSAL_PAYLOADS = [
    "../pwned",
    "../../etc/passwd",
    "subdir/../../escape",
    "/tmp/evil",
]


@pytest.fixture()
def project_dir(tmp_path, monkeypatch):
    proj = tmp_path / "project"
    proj.mkdir()
    (proj / ".specify").mkdir()
    monkeypatch.chdir(proj)
    return proj


class TestExtensionAddFromPathTraversal:
    """Path traversal payloads in the extension name must not escape the download cache."""

    @pytest.mark.parametrize("bad_name", TRAVERSAL_PAYLOADS)
    def test_traversal_payload_cannot_write_outside_cache(self, project_dir, bad_name):
        """The download zip path must stay inside .specify/extensions/.cache/downloads/."""
        result = runner.invoke(
            app,
            ["extension", "add", bad_name, "--from", "https://example.com/ext.zip"],
        )
        # The command should either reject early (path traversal guard) or
        # the sanitised name means the file would land inside the cache dir.
        # In no case should files appear outside the project tree.
        cache_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
        stray = [
            p
            for p in project_dir.parent.rglob("*")
            if p.is_file() and "url-download.zip" in p.name and not str(p).startswith(str(cache_dir))
        ]
        assert stray == [], f"Traversal payload leaked files: {stray}"

    def test_clean_name_is_unaffected(self, project_dir, monkeypatch):
        """A normal extension name should not trigger the guard."""
        from unittest.mock import patch, MagicMock

        mock_response = MagicMock()
        mock_response.read.return_value = b"PK\x03\x04fake"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("specify_cli.authentication.http.open_url", return_value=mock_response), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip") as mock_install:
            mock_install.return_value = MagicMock(id="my-ext", name="My Ext", version="1.0.0")
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
            )

        # Should reach the install call, not be rejected as traversal
        assert "path traversal" not in (result.output or "").lower()
