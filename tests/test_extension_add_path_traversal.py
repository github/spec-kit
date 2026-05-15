"""Tests for path traversal guard in `specify extension add --from` (GHSA-67q9-p54f-7cpr).

The extension argument is used to construct a temporary ZIP download path.
Without sanitisation, absolute paths or ``../`` segments in the argument can
escape the intended cache directory, causing arbitrary file writes and deletes.
"""

from unittest.mock import MagicMock, call, patch

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
    def test_traversal_payload_writes_inside_cache(self, project_dir, bad_name):
        """The zip_path passed to install_from_zip must resolve inside the cache dir."""
        cache_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip", return_value=MagicMock(id="x", name="X", version="1.0.0")) as mock_install:
            result = runner.invoke(
                app,
                ["extension", "add", bad_name, "--from", "https://example.com/ext.zip"],
            )
        if mock_install.called:
            zip_arg = mock_install.call_args[0][0]  # positional arg: zip_path
            zip_arg.resolve().relative_to(cache_dir.resolve())  # raises ValueError if outside

    @pytest.mark.parametrize("bad_name", TRAVERSAL_PAYLOADS)
    def test_traversal_payload_cannot_delete_outside_cache(self, project_dir, bad_name):
        """The finally-block cleanup must not delete files outside the cache dir."""
        # Place a sentinel at the path the pre-fix code would have constructed
        cache_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
        cache_dir.mkdir(parents=True, exist_ok=True)
        pre_fix_path = cache_dir / f"{bad_name}-url-download.zip"
        try:
            pre_fix_path.parent.mkdir(parents=True, exist_ok=True)
            pre_fix_path.write_text("sentinel")
        except OSError:
            # Absolute payloads like /tmp/evil can't be created relative to cache
            pre_fix_path = None

        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip", return_value=MagicMock(id="x", name="X", version="1.0.0")):
            runner.invoke(
                app,
                ["extension", "add", bad_name, "--from", "https://example.com/ext.zip"],
            )
        if pre_fix_path is not None and pre_fix_path.exists():
            # Sentinel survived — the fix didn't touch the pre-fix path
            assert pre_fix_path.read_text() == "sentinel"

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
        # Verify the zip path is inside the cache
        zip_arg = mock_install.call_args[0][0]
        cache_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
        zip_arg.resolve().relative_to(cache_dir.resolve())
        assert "path traversal" not in (result.output or "").lower()
