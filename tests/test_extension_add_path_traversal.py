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
    def test_traversal_payload_writes_inside_cache(self, project_dir, bad_name):
        """The zip_path passed to install_from_zip must resolve inside the cache dir."""
        cache_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip", return_value=MagicMock(id="x", name="X", version="1.0.0")) as mock_install:
            result = runner.invoke(
                app,
                ["extension", "add", bad_name, "--from", "https://example.com/ext.zip"],
            )
        assert result.exit_code == 0, result.output
        mock_install.assert_called_once()
        zip_arg = mock_install.call_args[0][0]  # positional arg: zip_path
        zip_arg.resolve().relative_to(cache_dir.resolve())  # raises ValueError if outside

    @pytest.mark.parametrize("bad_name", [p for p in TRAVERSAL_PAYLOADS if not p.startswith(("/", "\\"))])
    def test_traversal_payload_cannot_delete_outside_cache(self, project_dir, bad_name):
        """The finally-block cleanup must not delete files outside the cache dir.

        Absolute-path payloads are excluded here to avoid writing sentinels
        outside the pytest sandbox (e.g. ``/tmp``); the write-side test above
        already proves the production guard contains absolute payloads.
        """
        # Place a sentinel at the path the pre-fix code would have constructed
        cache_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
        cache_dir.mkdir(parents=True, exist_ok=True)
        pre_fix_path = cache_dir / f"{bad_name}-url-download.zip"
        pre_fix_path.parent.mkdir(parents=True, exist_ok=True)
        pre_fix_path.write_text("sentinel")

        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip", return_value=MagicMock(id="x", name="X", version="1.0.0")):
            runner.invoke(
                app,
                ["extension", "add", bad_name, "--from", "https://example.com/ext.zip"],
            )
        assert pre_fix_path.exists(), f"Sentinel deleted by cleanup: {pre_fix_path}"
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


class TestExtensionAddFromSymlinkedCache:
    """A symlinked download-cache ancestor must be rejected before any write."""

    @pytest.mark.parametrize(
        "ancestor_parts",
        [
            (".specify",),
            (".specify", "extensions"),
            (".specify", "extensions", ".cache"),
            (".specify", "extensions", ".cache", "downloads"),
        ],
    )
    def test_symlinked_ancestor_is_refused(self, tmp_path, monkeypatch, ancestor_parts):
        """Symlinking any cache ancestor outside the project must abort the command."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        monkeypatch.chdir(project_dir)

        # Build the parent of the symlinked component using real directories.
        parent = project_dir
        for part in ancestor_parts[:-1]:
            parent = parent / part
            parent.mkdir()

        # Replace the final ancestor component with a symlink pointing outside the project.
        symlink_path = parent / ancestor_parts[-1]
        symlink_path.symlink_to(outside, target_is_directory=True)

        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip") as mock_install:
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
            )

        assert result.exit_code != 0
        assert "symlinked download cache" in (result.output or "").lower()
        mock_install.assert_not_called()
        # No download was written through the symlink
        assert list(outside.iterdir()) == []


class TestExtensionAddFromAncestorEscape:
    """A non-symlink ancestor whose ``.resolve()`` lands outside the project must be refused.

    Simulates the Windows junction / mount-point case using a manually-pre-resolved
    directory swap: we cannot create real junctions on POSIX, but we can patch the
    ``.resolve()`` of an existing ancestor to land outside the project root. The
    production guard must reject it before any download happens.
    """

    def test_ancestor_resolves_outside_project_is_refused(self, tmp_path, monkeypatch):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        monkeypatch.chdir(project_dir)

        # Pre-create the cache ancestors as real directories so the per-component
        # walk reaches the resolve()/relative_to() check on each existing one.
        cache_root = project_dir / ".specify" / "extensions" / ".cache"
        cache_root.mkdir(parents=True)

        real_resolve = Path.resolve

        def fake_resolve(self, *a, **kw):
            # Pretend the .cache ancestor resolves outside the project.
            if self == cache_root:
                return real_resolve(outside, *a, **kw)
            return real_resolve(self, *a, **kw)

        with patch.object(Path, "resolve", fake_resolve), \
             patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip") as mock_install:
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
            )

        assert result.exit_code != 0
        assert "escapes project root" in (result.output or "").lower()
        mock_install.assert_not_called()
        assert list(outside.iterdir()) == []


class TestExtensionAddFromTOCTOUWrite:
    """The download write must not follow a symlink swapped in after validation."""

    def test_swapped_zip_path_symlink_is_refused(self, project_dir):
        """If zip_path is replaced by a symlink between validation and write, refuse."""
        cache_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
        outside = project_dir.parent / "outside"
        outside.mkdir(exist_ok=True)
        target = outside / "stolen.bin"

        # Patch os.open to simulate the TOCTOU window: just before the real
        # os.open runs, replace the target path with a symlink pointing outside.
        # With O_NOFOLLOW the os.open call must raise instead of writing through.
        import os as _os
        real_open = _os.open

        def racing_open(path, flags, mode=0o777):
            try:
                p = Path(path)
                if p.parent == cache_dir and not p.exists():
                    p.symlink_to(target)
            except OSError:
                pass
            return real_open(path, flags, mode)

        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip") as mock_install, \
             patch("os.open", side_effect=racing_open):
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
            )

        # Either O_NOFOLLOW (POSIX) or O_EXCL (all platforms) must reject the
        # swapped symlink. The command must fail and nothing must be written
        # through the symlink to `outside`.
        assert result.exit_code != 0
        mock_install.assert_not_called()
        assert not target.exists(), "write followed swapped symlink"
