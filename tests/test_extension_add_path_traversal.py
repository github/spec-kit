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
    if not getattr(os, "O_NOFOLLOW", 0) or os.open not in os.supports_dir_fd:
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


def test_safe_unlink_refuses_swapped_cache_ancestor(
    project_dir: Path, tmp_path: Path
) -> None:
    _require_secure_dir_fd()
    if os.unlink not in os.supports_dir_fd:
        pytest.skip("requires unlink dir_fd support")

    download_dir = _commands._validate_safe_cache_dir(project_dir)
    zip_filename = "extension-url-download-cleanup.zip"
    zip_path = download_dir / zip_filename
    zip_path.write_bytes(b"download")

    cache_root = project_dir / ".specify" / "extensions" / ".cache"
    original_cache = project_dir / ".specify" / "extensions" / ".cache-original"
    cache_root.rename(original_cache)
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_sentinel = outside / zip_filename
    outside_sentinel.write_bytes(b"sentinel")
    _symlink_directory(cache_root, outside)

    _commands._safe_unlink_download_zip(
        project_dir, download_dir, zip_filename
    )

    assert outside_sentinel.read_bytes() == b"sentinel"
    assert (original_cache / "downloads" / zip_filename).read_bytes() == b"download"


def test_safe_open_fails_closed_without_atomic_platform_support(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    download_dir = _commands._validate_safe_cache_dir(project_dir)
    monkeypatch.setattr(os, "supports_dir_fd", set())

    with pytest.raises(NotImplementedError, match=r"--dev.*catalog"):
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
    assert "catalog" in result.output
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
    ):
        captured["path"] = zip_path
        captured["bytes"] = zip_path.read_bytes()
        captured["mode"] = zip_path.stat().st_mode & 0o777
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
    zip_path = captured["path"]
    assert isinstance(zip_path, Path)
    assert zip_path.parent == (
        project_dir / ".specify" / "extensions" / ".cache" / "downloads"
    )
    assert zip_path.name.startswith("extension-url-download-")
    assert not zip_path.exists()
