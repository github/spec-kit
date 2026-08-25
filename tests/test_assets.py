"""Tests for the shared bundle-path resolvers in `specify_cli._assets`."""

from __future__ import annotations

import specify_cli._assets as assets


class TestLocateCoreAssetDir:
    """`_locate_core_asset_dir` is the single source of truth every core-asset
    consumer (extension command-name discovery, the preset resolver's core
    fallback, and the artifact command's core-baseline enumeration) shares."""

    def test_prefers_wheel_core_pack_over_repo_checkout(self, tmp_path, monkeypatch):
        core_pack = tmp_path / "core_pack"
        (core_pack / "commands").mkdir(parents=True)
        repo_root = tmp_path / "repo"
        (repo_root / "templates" / "commands").mkdir(parents=True)

        monkeypatch.setattr(assets, "_locate_core_pack", lambda: core_pack)
        monkeypatch.setattr(assets, "_repo_root", lambda: repo_root)

        assert assets._locate_core_asset_dir("commands") == core_pack / "commands"

    def test_falls_back_to_repo_checkout_when_no_wheel_bundle(self, tmp_path, monkeypatch):
        repo_root = tmp_path / "repo"
        (repo_root / "templates" / "commands").mkdir(parents=True)
        (repo_root / "templates").mkdir(exist_ok=True)
        (repo_root / "scripts").mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(assets, "_locate_core_pack", lambda: None)
        monkeypatch.setattr(assets, "_repo_root", lambda: repo_root)

        assert assets._locate_core_asset_dir("commands") == repo_root / "templates" / "commands"
        assert assets._locate_core_asset_dir("templates") == repo_root / "templates"
        assert assets._locate_core_asset_dir("scripts") == repo_root / "scripts"

    def test_returns_none_when_directory_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(assets, "_locate_core_pack", lambda: None)
        monkeypatch.setattr(assets, "_repo_root", lambda: tmp_path / "nonexistent")

        assert assets._locate_core_asset_dir("commands") is None

    def test_returns_none_for_unknown_subdir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(assets, "_locate_core_pack", lambda: None)
        monkeypatch.setattr(assets, "_repo_root", lambda: tmp_path)

        assert assets._locate_core_asset_dir("bogus") is None

    def test_falls_back_to_repo_checkout_when_wheel_bundle_missing_subdir(
        self, tmp_path, monkeypatch
    ):
        """A wheel bundle without the requested family subdir must not short-circuit
        the source-checkout fallback, matching the "wheel, then source" pattern
        used by ``_locate_bundled_extension``/``_locate_bundled_workflow``/
        ``_locate_bundled_preset``."""
        core_pack = tmp_path / "core_pack"
        core_pack.mkdir()  # bundle exists but has no "commands/" subdir
        repo_root = tmp_path / "repo"
        (repo_root / "templates" / "commands").mkdir(parents=True)

        monkeypatch.setattr(assets, "_locate_core_pack", lambda: core_pack)
        monkeypatch.setattr(assets, "_repo_root", lambda: repo_root)

        assert (
            assets._locate_core_asset_dir("commands")
            == repo_root / "templates" / "commands"
        )
