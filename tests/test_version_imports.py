"""Regression guard: version symbols must remain importable from specify_cli."""
from specify_cli import (
    GITHUB_API_LATEST,
    self_check,
    self_upgrade,
)


def test_version_symbols_importable():
    assert isinstance(GITHUB_API_LATEST, str)
    assert GITHUB_API_LATEST.startswith("https://")
    assert callable(self_check)
    assert callable(self_upgrade)


def test_version_symbols_available_from_star_import():
    namespace = {}
    exec("from specify_cli import *", namespace)

    for symbol in ("GITHUB_API_LATEST", "self_check", "self_upgrade"):
        assert symbol in namespace


def test_version_module_symbols_directly_importable():
    from specify_cli._version import (
        GITHUB_API_LATEST,
        _fetch_latest_release_tag,
        _get_installed_version,
        _is_newer,
        _normalize_tag,
        self_app,
        self_check,
        self_upgrade,
    )
    assert callable(_get_installed_version)
    assert callable(_normalize_tag)
    assert callable(_is_newer)
    assert callable(_fetch_latest_release_tag)
    assert callable(self_check)
    assert callable(self_upgrade)
    assert self_app is not None
