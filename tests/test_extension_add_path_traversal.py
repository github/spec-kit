"""Tests for path traversal guard in `specify extension add --from` (GHSA-67q9-p54f-7cpr).

The extension argument is used to construct a temporary ZIP download path.
Without sanitisation, absolute paths or ``../`` segments in the argument can
escape the intended cache directory, causing arbitrary file writes and deletes.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import os

import pytest
from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()


def _require_symlinks(tmp_path) -> None:
    """Skip the calling test when symlink creation is not permitted.

    On Windows, symlink creation requires elevated privileges or developer
    mode and may raise ``OSError`` (``EPERM``/``EACCES``/``WinError 1314``).
    The shared-infra test suite uses the same pattern.
    """
    probe_target = tmp_path / "_symlink_probe_target"
    probe_target.mkdir(exist_ok=True)
    probe_link = tmp_path / "_symlink_probe_link"
    try:
        probe_link.symlink_to(probe_target, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation not supported in this environment: {exc}")
    finally:
        if probe_link.exists() or probe_link.is_symlink():
            try:
                probe_link.unlink()
            except OSError:
                pass

def _is_absolute_like(payload: str) -> bool:
    """Detect payloads that may be treated as an absolute path on any supported OS.

    Used to skip the delete-side regression test for those payloads, since
    constructing a sentinel relative to ``cache_dir`` for an absolute-like
    payload would land outside the pytest sandbox (especially on Windows
    where ``Path('C:\\\\...')`` and ``\\\\\\\\server\\\\share`` are roots).
    The write-side test still covers containment for these cases.
    """
    if payload.startswith(("/", "\\")):
        return True
    # Drive letter forms: C:\..., C:/...
    if len(payload) >= 2 and payload[1] == ":" and payload[0].isalpha():
        return True
    return False


TRAVERSAL_PAYLOADS = [
    "../pwned",
    "../../etc/passwd",
    "subdir/../../escape",
    "..\\pwned",
    "..\\..\\etc\\passwd",
    "/tmp/evil",
    # Deep relative traversal long enough to escape from
    # `.specify/extensions/.cache/downloads` (4 segments) all the way out
    # of project_root and beyond.
    "../../../../../etc/shadow",
    # Windows absolute path forms. The CI matrix runs these tests on
    # windows-latest, so the sanitiser must reject drive-letter and UNC
    # roots in addition to POSIX absolute paths.
    "C:\\tmp\\evil",
    "C:/tmp/evil",
    "\\\\server\\share\\evil",
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

    @pytest.mark.parametrize("bad_name", [p for p in TRAVERSAL_PAYLOADS if not _is_absolute_like(p)])
    def test_traversal_payload_cannot_delete_outside_cache(self, project_dir, bad_name):
        """The finally-block cleanup must not delete files outside the cache dir.

        Absolute-like payloads (POSIX absolute, Windows drive letter, UNC) are
        excluded here to avoid writing sentinels outside the pytest sandbox;
        the write-side test above already proves the production guard contains
        absolute payloads.
        """
        # Place a sentinel at the path the pre-fix code would have constructed
        cache_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
        cache_dir.mkdir(parents=True, exist_ok=True)
        pre_fix_path = cache_dir / f"{bad_name}-url-download.zip"
        pre_fix_path.parent.mkdir(parents=True, exist_ok=True)
        pre_fix_path.write_text("sentinel")

        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip", return_value=MagicMock(id="x", name="X", version="1.0.0")):
            result = runner.invoke(
                app,
                ["extension", "add", bad_name, "--from", "https://example.com/ext.zip"],
            )
        # The command must succeed: a non-zero exit would mean the install
        # failed before reaching cleanup, which would leave the sentinel
        # untouched for the wrong reason and mask any cleanup-side regression.
        assert result.exit_code == 0, result.output
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
        _require_symlinks(tmp_path)
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
    """The download write must not follow a symlink swapped in after validation.

    These tests rely on POSIX ``O_NOFOLLOW`` + ``dir_fd``-relative open and on
    the runner being able to create symlinks. Skipped on platforms where either
    is unavailable (notably Windows without elevated privileges).
    """

    def test_swapped_zip_path_symlink_is_refused(self, tmp_path, monkeypatch):
        """If zip_path is replaced by a symlink between validation and write, refuse."""
        if not getattr(os, "O_NOFOLLOW", 0) or os.open not in os.supports_dir_fd:
            pytest.skip("Requires POSIX O_NOFOLLOW + dir_fd support")
        _require_symlinks(tmp_path)
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        target = outside / "stolen.bin"
        monkeypatch.chdir(project_dir)

        from specify_cli import _safe_open_download_zip as _orig_safe_open

        def swap_then_open(project_root, download_dir, zip_filename):
            # Race: pre-stage a symlink at the leaf inside the validated cache.
            leaf = download_dir / zip_filename
            try:
                leaf.symlink_to(target)
            except (OSError, NotImplementedError):
                pytest.skip("Cannot create symlink for leaf-swap race")
            return _orig_safe_open(project_root, download_dir, zip_filename)

        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip") as mock_install, \
             patch("specify_cli._safe_open_download_zip", side_effect=swap_then_open):
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
            )

        assert result.exit_code != 0
        mock_install.assert_not_called()
        # The write must not have followed the symlink to `outside`.
        assert not target.exists(), "write followed swapped leaf symlink"

    def test_swapped_ancestor_symlink_is_refused(self, tmp_path, monkeypatch):
        """If a *cache ancestor* is replaced by a symlink between validation and write, refuse.

        Covers the case `O_NOFOLLOW` alone misses: it only protects the final
        component, but the per-ancestor walk in ``_safe_open_download_zip``
        (using ``dir_fd`` + ``O_NOFOLLOW`` on each component) catches this.
        """
        if not getattr(os, "O_NOFOLLOW", 0) or os.open not in os.supports_dir_fd:
            pytest.skip("Requires POSIX O_NOFOLLOW + dir_fd support")
        _require_symlinks(tmp_path)
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        monkeypatch.chdir(project_dir)

        # Pre-create the cache ancestors so the production validation walk
        # passes (the swap happens *after* validation, before the write).
        cache_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
        cache_dir.mkdir(parents=True)
        ancestor_to_swap = project_dir / ".specify" / "extensions" / ".cache"

        from specify_cli import _safe_open_download_zip as _orig_safe_open

        def swap_then_open(project_root, download_dir, zip_filename):
            # Race: replace `.cache` with a symlink to `outside` after the
            # caller's per-ancestor validation finished.
            import shutil
            shutil.rmtree(ancestor_to_swap)
            try:
                ancestor_to_swap.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                pytest.skip("Cannot create symlink for ancestor-swap race")
            return _orig_safe_open(project_root, download_dir, zip_filename)

        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip") as mock_install, \
             patch("specify_cli._safe_open_download_zip", side_effect=swap_then_open):
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
            )

        assert result.exit_code != 0
        # Clean CLI error from the OSError handler, not a raw traceback.
        assert "could not safely create download file" in (result.output or "").lower() \
            or "failed to write download cache" in (result.output or "").lower()
        mock_install.assert_not_called()
        # No download leaked through the swapped ancestor symlink.
        assert list(outside.iterdir()) == []


class TestExtensionAddFromCacheAncestorIsFile:
    """A non-directory file at a cache-ancestor path must be refused with a clean error."""

    def test_file_at_extensions_path_is_rejected_cleanly(self, tmp_path, monkeypatch):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        # Place a regular file where `.specify/extensions/` would be created.
        (project_dir / ".specify" / "extensions").write_text("i am a file")
        monkeypatch.chdir(project_dir)

        with patch("specify_cli.authentication.http.open_url", return_value=_mock_open_url()), \
             patch("specify_cli.extensions.ExtensionManager.install_from_zip") as mock_install:
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
            )

        assert result.exit_code != 0
        assert "not a directory" in (result.output or "").lower()
        mock_install.assert_not_called()
