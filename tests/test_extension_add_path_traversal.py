"""Security tests for the extension URL download cache."""

from __future__ import annotations

import io
import os
import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import typer
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import ExtensionCatalog, ExtensionManager
from specify_cli.extensions import _commands


_MINIMAL_ZIP_BYTES = b"PK\x05\x06" + b"\x00" * 18
runner = CliRunner()


def _require_secure_dir_fd() -> None:
    if (
        not getattr(os, "O_NOFOLLOW", 0)
        or os.open not in os.supports_dir_fd
        or os.mkdir not in os.supports_dir_fd
    ):
        pytest.skip("requires dir_fd and O_NOFOLLOW support")


def _symlink_directory(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"directory symlinks are unavailable: {exc}")


@pytest.fixture
def project_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    (project / ".specify").mkdir()
    monkeypatch.chdir(project)
    return project


@pytest.mark.parametrize(
    "ancestor_parts",
    [
        ("extensions",),
        ("extensions", ".cache"),
        ("extensions", ".cache", "downloads"),
    ],
)
def test_symlinked_cache_ancestor_is_refused(
    project_dir: Path, tmp_path: Path, ancestor_parts: tuple[str, ...]
) -> None:
    _require_secure_dir_fd()
    outside = tmp_path / "outside"
    outside.mkdir()

    parent = project_dir / ".specify"
    for part in ancestor_parts[:-1]:
        parent = parent / part
        parent.mkdir()
    _symlink_directory(parent / ancestor_parts[-1], outside)

    with pytest.raises(typer.Exit):
        _commands._validate_safe_cache_dir(project_dir)

    assert list(outside.iterdir()) == []


def test_cache_ancestor_resolving_outside_project_is_refused(
    project_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _require_secure_dir_fd()
    cache_root = project_dir / ".specify" / "extensions" / ".cache"
    cache_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    real_resolve = Path.resolve

    def fake_resolve(self: Path, *args, **kwargs) -> Path:
        if self == cache_root:
            return real_resolve(outside, *args, **kwargs)
        return real_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", fake_resolve)

    with pytest.raises(typer.Exit):
        _commands._validate_safe_cache_dir(project_dir)

    assert list(outside.iterdir()) == []


def test_safe_open_refuses_exclusive_leaf_collision(project_dir: Path) -> None:
    _require_secure_dir_fd()
    download_dir = _commands._validate_safe_cache_dir(project_dir)
    zip_filename = "extension-url-download-collision.zip"
    collision = download_dir / zip_filename
    collision.write_bytes(b"sentinel")

    with pytest.raises(OSError):
        _commands._safe_open_download_zip(
            project_dir, download_dir, zip_filename
        )

    assert collision.read_bytes() == b"sentinel"


def test_safe_open_refuses_swapped_cache_ancestor(
    project_dir: Path, tmp_path: Path
) -> None:
    _require_secure_dir_fd()
    download_dir = _commands._validate_safe_cache_dir(project_dir)
    cache_root = project_dir / ".specify" / "extensions" / ".cache"
    outside = tmp_path / "outside"
    outside.mkdir()

    shutil.rmtree(cache_root)
    _symlink_directory(cache_root, outside)

    with pytest.raises(OSError):
        _commands._safe_open_download_zip(
            project_dir,
            download_dir,
            "extension-url-download-swapped.zip",
        )

    assert list(outside.iterdir()) == []


def test_safe_open_refuses_symlinked_project_root(
    project_dir: Path, tmp_path: Path
) -> None:
    _require_secure_dir_fd()
    project_link = tmp_path / "project-link"
    _symlink_directory(project_link, project_dir)
    download_dir = project_link / ".specify" / "extensions" / ".cache" / "downloads"

    with pytest.raises(OSError):
        _commands._safe_open_download_zip(
            project_link,
            download_dir,
            "extension-url-download-project-link.zip",
        )


def test_safe_open_fails_closed_without_atomic_platform_support(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Build the cache dir directly: on a platform without dir_fd support the
    # validator itself fails closed, so we must exercise the leaf-open gate
    # in isolation rather than going through _validate_safe_cache_dir().
    download_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(os, "supports_dir_fd", set())

    with pytest.raises(NotImplementedError, match=r"--dev"):
        _commands._safe_open_download_zip(
            project_dir,
            download_dir,
            "extension-url-download-unsupported.zip",
        )


def test_url_install_surfaces_fail_closed_platform_error(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(typer, "confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(os, "supports_dir_fd", set())
    monkeypatch.setattr(
        ExtensionCatalog,
        "_open_url",
        lambda *args, **kwargs: io.BytesIO(_MINIMAL_ZIP_BYTES),
    )
    install_spy = MagicMock()
    monkeypatch.setattr(ExtensionManager, "install_from_zip", install_spy)

    result = runner.invoke(
        app,
        [
            "extension",
            "add",
            "test-ext",
            "--from",
            "https://example.com/test-ext.zip",
        ],
    )

    assert result.exit_code == 1
    assert "--dev" in result.output
    assert "install from a catalog instead" not in result.output
    install_spy.assert_not_called()


def test_url_install_writes_and_cleans_up_secure_download(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _require_secure_dir_fd()
    captured: dict[str, object] = {}

    class FakeResponse(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_install(
        self,
        zip_path: Path,
        speckit_version: str,
        priority: int = 10,
        force: bool = False,
        *,
        archive_file=None,
    ):
        captured["path"] = zip_path
        captured["mode"] = os.fstat(archive_file.fileno()).st_mode & 0o777
        captured["exists_during_install"] = zip_path.exists()
        captured["bytes"] = archive_file.read()
        archive_file.seek(0)
        return SimpleNamespace(
            id="test-ext",
            name="Test Extension",
            version="1.0.0",
            description="",
            warnings=[],
            commands=[],
        )

    monkeypatch.setattr(typer, "confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        ExtensionCatalog,
        "_open_url",
        lambda *args, **kwargs: FakeResponse(_MINIMAL_ZIP_BYTES),
    )
    monkeypatch.setattr(ExtensionManager, "install_from_zip", fake_install)
    monkeypatch.setattr(_commands, "_refresh_events_and_warn", lambda root: None)
    monkeypatch.setattr(_commands, "load_init_options", lambda root: {})

    result = runner.invoke(
        app,
        [
            "extension",
            "add",
            "test-ext",
            "--from",
            "https://example.com/test-ext.zip",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured["bytes"] == _MINIMAL_ZIP_BYTES
    assert captured["mode"] == 0o600
    # The archive is an anonymous inode: it is never visible on disk, even
    # while installation consumes the open descriptor.
    assert captured["exists_during_install"] is False
    zip_path = captured["path"]
    assert isinstance(zip_path, Path)
    assert zip_path.parent == (
        project_dir / ".specify" / "extensions" / ".cache" / "downloads"
    )
    assert zip_path.name.startswith("extension-url-download-")
    assert not zip_path.exists()


def test_url_install_open_error_surfaces_as_controlled_exit(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An ``OSError`` from the hardened create (e.g. an exclusive-leaf
    collision or a swapped ancestor) must fail closed as ``typer.Exit(1)``
    rather than escaping as an unhandled traceback, and installation must
    not run."""
    download_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"

    monkeypatch.setattr(typer, "confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        ExtensionCatalog,
        "_open_url",
        lambda *args, **kwargs: io.BytesIO(_MINIMAL_ZIP_BYTES),
    )
    monkeypatch.setattr(
        _commands, "_validate_safe_cache_dir", lambda root: download_dir
    )
    download_dir.mkdir(parents=True, exist_ok=True)

    def _raise_collision(project_root, dir_, zip_filename):
        raise FileExistsError("leaf already exists")

    monkeypatch.setattr(_commands, "_safe_open_download_zip", _raise_collision)
    install_spy = MagicMock()
    monkeypatch.setattr(ExtensionManager, "install_from_zip", install_spy)

    result = runner.invoke(
        app,
        [
            "extension",
            "add",
            "test-ext",
            "--from",
            "https://example.com/test-ext.zip",
        ],
    )

    assert result.exit_code == 1
    assert "Could not safely create download file" in result.output
    install_spy.assert_not_called()
