"""Exact-release lookup for workflow step catalogs."""

from __future__ import annotations

import hashlib
import io

import pytest

from specify_cli.workflows.step.catalog import (
    StepCatalog,
    StepCatalogEntry,
    StepCatalogError,
)
from specify_cli.workflows.step.catalog._versions import available_versions


def _digests(*extra: str) -> dict[str, str]:
    return {
        name: hashlib.sha256(name.encode()).hexdigest()
        for name in ("step.yml", "__init__.py", *extra)
    }


def _entry() -> dict:
    return {
        "id": "deploy",
        "name": "Deploy",
        "version": "2.0",
        "url": "https://example.com/current/step.yml",
        "init_url": "https://example.com/current/__init__.py",
        "sha256": _digests(),
        "requires": {"current": True},
        "releases": {
            "1.0": {
                "step_yml_url": "https://example.com/old/step.yml",
                "init_url": "https://example.com/old/__init__.py",
                "extra_files": {"helper.py": "https://example.com/old/helper.py"},
                "sha256": _digests("helper.py"),
                "requires": {"old": True},
            },
        },
    }


def test_current_and_exact_release_keep_separate_metadata(project_dir, monkeypatch):
    catalog = StepCatalog(project_dir)
    monkeypatch.setattr(catalog, "_get_merged_steps", lambda *, step_id=None: {"deploy": _entry()})

    current = catalog.get_step_info("deploy")
    old = catalog.get_step_info("deploy", version="v1.0")

    assert current["url"] == "https://example.com/current/step.yml"
    assert current["version"] == "2.0"
    assert current["releases"]["1.0"]["extra_files"]
    assert old["version"] == "1.0"
    assert old["step_yml_url"] == "https://example.com/old/step.yml"
    assert old["sha256"] == _digests("helper.py")
    assert old["requires"] == {"old": True}
    assert "url" not in old and "releases" not in old
    assert catalog.get_step_info("deploy", version="2.0")["url"] == current["url"]
    assert catalog.get_step_info("deploy", version="9.0") is None
    assert available_versions(current, "deploy") == ["2.0", "1.0"]


def test_legacy_current_and_exact_spelling(project_dir, monkeypatch):
    catalog = StepCatalog(project_dir)
    legacy = {
        "id": "deploy",
        "version": "release-1",
        "url": "https://example.com/step.yml",
    }
    monkeypatch.setattr(catalog, "_get_merged_steps", lambda *, step_id=None: {"deploy": legacy})
    assert catalog.get_step_info("deploy") is legacy
    assert catalog.get_step_info("deploy", version="release-1") is legacy
    assert catalog.get_step_info("deploy", version="release-2") is None


def test_winning_source_never_falls_back_for_missing_release(project_dir, monkeypatch):
    catalog = StepCatalog(project_dir)
    sources = [
        StepCatalogEntry("https://example.com/high", "discovery", 1, False),
        StepCatalogEntry("https://example.com/low", "installable", 2, True),
    ]
    high = {key: value for key, value in _entry().items() if key != "releases"}
    low = _entry()
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda: sources)
    monkeypatch.setattr(
        catalog,
        "_fetch_single_catalog",
        lambda source, force_refresh=False: {
            "steps": {"deploy": high if source.name == "discovery" else low}
        },
    )
    assert catalog.get_step_info("deploy")["_install_allowed"] is False
    assert catalog.get_step_info("deploy", version="1.0") is None


def test_list_catalog_rejects_duplicate_step_ids(project_dir, monkeypatch):
    catalog = StepCatalog(project_dir)
    source = StepCatalogEntry("https://example.com/steps.json", "test", 1, True)
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda: [source])
    monkeypatch.setattr(
        catalog,
        "_fetch_single_catalog",
        lambda *_args, **_kwargs: {
            "steps": [
                {"id": "deploy", "version": "1.0"},
                {"id": "deploy", "version": "2.0"},
            ]
        },
    )
    with pytest.raises(StepCatalogError, match="Duplicate step ID 'deploy'"):
        catalog.get_step_info("deploy")


@pytest.mark.parametrize("cached", [True, False])
def test_duplicate_json_release_key_is_not_silently_overwritten(
    project_dir, monkeypatch, cached
):
    from specify_cli.authentication import http as auth_http

    catalog = StepCatalog(project_dir)
    source = StepCatalogEntry("https://example.com/steps.json", "test", 1, True)
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda: [source])
    payload = b'{"steps":{"deploy":{"version":"2.0","releases":{"1.0":{},"1.0":{}}}}}'
    if cached:
        cache_file, _ = catalog._get_cache_paths(source.url)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(payload)
        monkeypatch.setattr(catalog, "_is_url_cache_valid", lambda _url: True)
    else:

        class Response(io.BytesIO):
            def geturl(self):
                return source.url

            def getheader(self, _name):
                return None

        monkeypatch.setattr(
            auth_http, "open_url", lambda *_args, **_kwargs: Response(payload)
        )
    with pytest.raises(StepCatalogError, match="Duplicate field '1.0'"):
        catalog.get_step_info("deploy", version="1.0")


@pytest.mark.parametrize(
    ("change", "error"),
    [
        ({"releases": []}, "releases mapping"),
        ({"version": None}, "current version"),
        ({"version": "not valid"}, "current version"),
        ({"id": "another"}, "mismatched catalog ID"),
        ({"releases": {"v2.0": _entry()["releases"]["1.0"]}}, "repeats release"),
        (
            {
                "releases": {
                    "1.0": _entry()["releases"]["1.0"],
                    "v1.0": _entry()["releases"]["1.0"],
                }
            },
            "repeats release",
        ),
        ({"releases": {"bogus": {}}}, "invalid release version"),
        ({"releases": {"1.0": []}}, "must be an object"),
        ({"releases": {"1.0": {"id": "deploy"}}}, "reserved fields"),
        ({"releases": {"1.0": {"url": "https://example.com/step.yml"}}}, "SHA-256"),
        (
            {
                "releases": {
                    "1.0": {
                        **_entry()["releases"]["1.0"],
                        "extra_files": {"./step.yml": "https://example.com/alias"},
                    }
                }
            },
            "invalid extra_files",
        ),
        (
            {
                "releases": {
                    "1.0": {
                        **_entry()["releases"]["1.0"],
                        "sha256": {"step.yml": "bad"},
                    }
                }
            },
            "SHA-256",
        ),
        (
            {"releases": {"1.0": {**_entry()["releases"]["1.0"], "requires": []}}},
            "invalid requires",
        ),
        (
            {"releases": {"1.0": {**_entry()["releases"]["1.0"], "step_yml_url": 12}}},
            "step.yml URL",
        ),
        (
            {
                "releases": {
                    "1.0": {
                        **_entry()["releases"]["1.0"],
                        "init_url": None,
                        "step_yml_url": "https://example.com/old/manifest",
                    }
                }
            },
            "__init__.py URL",
        ),
    ],
)
def test_bad_history_rejected_not_ignored(project_dir, monkeypatch, change, error):
    catalog = StepCatalog(project_dir)
    entry = {**_entry(), **change}
    monkeypatch.setattr(catalog, "_get_merged_steps", lambda *, step_id=None: {"deploy": entry})
    with pytest.raises(StepCatalogError, match=error):
        catalog.get_step_info("deploy")
