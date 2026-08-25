"""Tests for the shared bundle-path resolvers in `specify_cli._assets`."""

from __future__ import annotations

import specify_cli._assets as assets


class TestLocateSharedAssetDir:
    """Tests for the shared wheel-then-source asset directory lookup."""

    def test_prefers_wheel_core_pack_over_repo_checkout(self, tmp_path, monkeypatch):
        package_dir = tmp_path / "site-packages" / "specify_cli"
        core_pack = package_dir / "core_pack"
        (core_pack / "commands").mkdir(parents=True)
        repo_root = tmp_path / "repo"
        (repo_root / "templates" / "commands").mkdir(parents=True)

        monkeypatch.setattr(assets, "__file__", str(package_dir / "_assets.py"))
        monkeypatch.setattr(assets, "_repo_root", lambda: repo_root)

        assert assets._locate_shared_asset_dir("commands") == core_pack / "commands"

    def test_falls_back_to_repo_checkout_when_no_wheel_bundle(self, tmp_path, monkeypatch):
        package_dir = tmp_path / "site-packages" / "specify_cli"
        repo_root = tmp_path / "repo"
        (repo_root / "templates" / "commands").mkdir(parents=True)
        (repo_root / "templates").mkdir(exist_ok=True)
        (repo_root / "scripts").mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(assets, "__file__", str(package_dir / "_assets.py"))
        monkeypatch.setattr(assets, "_repo_root", lambda: repo_root)

        assert (
            assets._locate_shared_asset_dir("commands")
            == repo_root / "templates" / "commands"
        )
        assert assets._locate_shared_asset_dir("templates") == repo_root / "templates"
        assert assets._locate_shared_asset_dir("scripts") == repo_root / "scripts"

    def test_returns_none_when_directory_missing(self, tmp_path, monkeypatch):
        package_dir = tmp_path / "site-packages" / "specify_cli"
        monkeypatch.setattr(assets, "__file__", str(package_dir / "_assets.py"))
        monkeypatch.setattr(assets, "_repo_root", lambda: tmp_path / "nonexistent")

        assert assets._locate_shared_asset_dir("commands") is None

    def test_falls_back_to_repo_checkout_when_wheel_bundle_missing_subdir(
        self, tmp_path, monkeypatch
    ):
        """A wheel bundle without the requested family subdir must not short-circuit
        the source-checkout fallback, matching the "wheel, then source" pattern
        used by ``_locate_bundled_extension``/``_locate_bundled_workflow``/
        ``_locate_bundled_preset``."""
        package_dir = tmp_path / "site-packages" / "specify_cli"
        core_pack = package_dir / "core_pack"
        core_pack.mkdir(parents=True)  # bundle exists but has no "commands/" subdir
        repo_root = tmp_path / "repo"
        (repo_root / "templates" / "commands").mkdir(parents=True)

        monkeypatch.setattr(assets, "__file__", str(package_dir / "_assets.py"))
        monkeypatch.setattr(assets, "_repo_root", lambda: repo_root)

        assert (
            assets._locate_shared_asset_dir("commands")
            == repo_root / "templates" / "commands"
        )
