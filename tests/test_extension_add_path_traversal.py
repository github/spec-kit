"""Tests for path traversal guard in `specify extension add --from` (GHSA-67q9-p54f-7cpr).

The extension argument is used to construct a temporary ZIP download path.
Without sanitisation, absolute paths or ``../`` segments in the argument can
escape the intended cache directory, causing arbitrary file writes and deletes.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()

TRAVERSAL_PAYLOADS = [
    "../pwned",
    "../../etc/passwd",
    "subdir/../../escape",
    "..\\pwned",
    "..\\..\\etc\\passwd",
    "/tmp/evil",
]


@pytest.fixture()
def project_dir(tmp_path, monkeypatch):
    proj = tmp_path / "project"
    proj.mkdir()
    (proj / ".specify").mkdir()
    monkeypatch.chdir(proj)
    return proj


def _mock_open_url():
    """Return a mock open_url that yields fake ZIP bytes."""
    mock_response = MagicMock()
    mock_response.read.return_value = b"PK\x03\x04fake"
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestExtensionAddFromPathTraversal:
    """Path traversal payloads in the extension name must not escape the download cache."""

    @pytest.mark.parametrize("bad_name", TRAVERSAL_PAYLOADS)
    def test_traversal_payload_cannot_write_outside_cache(self, project_dir, bad_name):
        """The download zip path must stay inside .specify/extensions/.cache/downloads/."""
        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip", return_value=MagicMock(id="x", name="X", version="1.0.0")):
            result = runner.invoke(
                app,
                ["extension", "add", bad_name, "--from", "https://example.com/ext.zip"],
            )
        cache_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
        cache_resolved = cache_dir.resolve()
        stray = []
        for p in project_dir.parent.rglob("*"):
            if not p.is_file() or ".zip" not in p.name:
                continue
            try:
                p.resolve().relative_to(cache_resolved)
            except ValueError:
                stray.append(p)
        assert stray == [], f"Traversal payload leaked files: {stray}"

    @pytest.mark.parametrize("bad_name", TRAVERSAL_PAYLOADS)
    def test_traversal_payload_cannot_delete_outside_cache(self, project_dir, bad_name):
        """The finally-block cleanup must not delete files outside the cache dir."""
        # Place a sentinel where the pre-fix code would have written/deleted
        sentinel = project_dir.parent / "sentinel.txt"
        sentinel.write_text("must survive")

        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip", return_value=MagicMock(id="x", name="X", version="1.0.0")):
            runner.invoke(
                app,
                ["extension", "add", bad_name, "--from", "https://example.com/ext.zip"],
            )
        assert sentinel.exists(), "Sentinel file was deleted by cleanup — traversal not blocked"

    def test_clean_name_is_unaffected(self, project_dir):
        """A normal extension name should not trigger the guard."""
        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip") as mock_install:
            mock_install.return_value = MagicMock(id="my-ext", name="My Ext", version="1.0.0")
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
            )

        assert result.exit_code == 0, result.output
        mock_install.assert_called_once()
        assert "path traversal" not in (result.output or "").lower()
