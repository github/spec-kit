"""Exact-release preset catalog lookup, downloads, and CLI regressions."""

from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import (
    PresetCatalog,
    PresetCatalogEntry,
    PresetError,
    PresetManager,
    PresetValidationError,
)

CURRENT_URL = "https://example.com/preset-current.zip"
OLD_URL = "https://example.com/preset-old.zip"


def _archive(pack_id: str = "sample", version: str = "1.0.0") -> bytes:
    manifest = {
        "schema_version": "1.0",
        "preset": {
            "id": pack_id,
            "name": "Sample",
            "version": version,
            "description": "Sample preset",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "templates": [
                {
                    "type": "template",
                    "name": "spec-template",
                    "file": "templates/spec-template.md",
                }
            ]
        },
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("preset.yml", yaml.safe_dump(manifest))
        archive.writestr("templates/spec-template.md", "# Sample\n")
    return buffer.getvalue()


def _entry(old_bytes: bytes | None = None) -> dict:
    old_bytes = old_bytes if old_bytes is not None else _archive()
    return {
        "id": "sample",
        "name": "Sample",
        "version": "2.0.0",
        "download_url": CURRENT_URL,
        "sha256": "a" * 64,
        "requires": {"speckit_version": ">=2"},
        "provides": {"templates": 2},
        "releases": {
            "1.0.0": {
                "download_url": OLD_URL,
                "sha256": hashlib.sha256(old_bytes).hexdigest(),
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {"templates": 0},
            }
        },
    }


def _response(data: bytes, url: str) -> MagicMock:
    response = MagicMock()
    response.read.side_effect = io.BytesIO(data).read
    response.geturl.return_value = url
    response.getheader.return_value = "application/zip"
    response.__enter__.return_value = response
    return response


def test_current_and_exact_selection_keep_current_fields(project_dir):
    catalog = PresetCatalog(project_dir)
    entry = _entry()
    with patch.object(catalog, "_get_merged_packs", return_value={"sample": entry}):
        current = catalog.get_pack_info("sample")
        old = catalog.get_pack_info("sample", "1.0")
        assert catalog.get_pack_info("sample", "0.4.12") is None
        assert catalog.get_pack_versions("sample") == ["2.0.0", "1.0.0"]
    assert current["version"] == "2.0.0"
    assert current["download_url"] == CURRENT_URL
    assert old["version"] == "1.0.0"
    assert old["download_url"] == OLD_URL
    assert old["requires"] == {"speckit_version": ">=0.1.0"}
    assert old["provides"] == {"templates": 0}
    assert old["sha256"] != current["sha256"]
    assert "releases" not in old


def test_single_release_entry_remains_compatible(project_dir):
    catalog = PresetCatalog(project_dir)
    entry = {"name": "Legacy", "version": "1.0.0", "download_url": OLD_URL}
    with patch.object(catalog, "_get_merged_packs", return_value={"sample": entry}):
        assert catalog.get_pack_info("sample")["version"] == "1.0.0"
        assert catalog.get_pack_info("sample", "1.0")["version"] == "1.0.0"
        assert catalog.get_pack_info("sample", "2.0") is None
        assert catalog.get_pack_versions("sample") == ["1.0.0"]


@pytest.mark.parametrize(
    "change, error",
    [
        ({"releases": []}, "releases mapping"),
        ({"version": None}, "current version"),
        ({"version": "garbage"}, "current version"),
        (
            {"releases": {"2.0": {"download_url": OLD_URL, "sha256": "f" * 64}}},
            "repeats",
        ),
        (
            {
                "releases": {
                    "1.0": {"download_url": OLD_URL, "sha256": "f" * 64},
                    "1.0.0": {"download_url": OLD_URL, "sha256": "f" * 64},
                }
            },
            "repeats",
        ),
        ({"releases": {"oops": {}}}, "release version"),
        ({"releases": {"1.0": []}}, "must be an object"),
        ({"releases": {"1.0": {"sha256": "f" * 64}}}, "download_url"),
        (
            {
                "releases": {
                    "1.0": {
                        "download_url": "http://evil.test/a.zip",
                        "sha256": "f" * 64,
                    }
                }
            },
            "download_url",
        ),
        (
            {"releases": {"1.0": {"download_url": OLD_URL, "sha256": "broken"}}},
            "SHA-256",
        ),
        (
            {
                "releases": {
                    "1.0": {
                        "download_url": OLD_URL,
                        "sha256": "f" * 64,
                        "version": "1.0",
                    }
                }
            },
            "reserved",
        ),
        (
            {
                "releases": {
                    "1.0": {"download_url": OLD_URL, "sha256": "f" * 64, "requires": []}
                }
            },
            "requires",
        ),
        (
            {
                "releases": {
                    "1.0": {
                        "download_url": OLD_URL,
                        "sha256": "f" * 64,
                        "requires": {"speckit_version": 2},
                    }
                }
            },
            "requires.speckit_version",
        ),
        (
            {
                "releases": {
                    "1.0": {
                        "download_url": OLD_URL,
                        "sha256": "f" * 64,
                        "requires": {"speckit_version": "not a specifier"},
                    }
                }
            },
            "requires.speckit_version",
        ),
        ({"id": "other"}, "inconsistent"),
    ],
)
def test_malformed_history_rejected_even_for_current(project_dir, change, error):
    entry = {**_entry(), **change}
    catalog = PresetCatalog(project_dir)
    with (
        patch.object(catalog, "_get_merged_packs", return_value={"sample": entry}),
        pytest.raises(PresetError, match=error),
    ):
        catalog.get_pack_info("sample")


def test_winning_source_does_not_fall_back_to_lower_release(project_dir):
    catalog = PresetCatalog(project_dir)
    sources = [
        PresetCatalogEntry("https://example.com/high.json", "high", 1, True),
        PresetCatalogEntry("https://example.com/low.json", "low", 2, True),
    ]
    older = {**_entry(), "version": "3.0.0"}
    higher = {"version": "2.0.0", "download_url": CURRENT_URL}

    def fetch(source, _refresh):
        return {"presets": {"sample": higher if source.name == "high" else older}}

    with (
        patch.object(catalog, "get_active_catalogs", return_value=sources),
        patch.object(catalog, "_fetch_single_catalog", side_effect=fetch),
    ):
        assert catalog.get_pack_info("sample")["_catalog_name"] == "high"
        assert catalog.get_pack_info("sample", "1.0.0") is None


def test_discovery_only_winner_does_not_delegate_exact_release(project_dir):
    catalog = PresetCatalog(project_dir)
    sources = [
        PresetCatalogEntry("https://example.com/high.json", "discovery", 1, False),
        PresetCatalogEntry("https://example.com/low.json", "trusted", 2, True),
    ]

    def fetch(_source, _refresh):
        return {"presets": {"sample": _entry()}}

    with (
        patch.object(catalog, "get_active_catalogs", return_value=sources),
        patch.object(catalog, "_fetch_single_catalog", side_effect=fetch),
        patch.object(catalog, "_open_url") as open_url,
    ):
        selected = catalog.get_pack_info("sample", "1.0")
        assert selected["_catalog_name"] == "discovery"
        with pytest.raises(PresetError, match="does not allow installation"):
            catalog.download_pack_info(selected, project_dir)
        open_url.assert_not_called()


def test_historical_release_does_not_inherit_current_requirements(project_dir):
    catalog = PresetCatalog(project_dir)
    entry = _entry()
    del entry["releases"]["1.0.0"]["requires"]
    del entry["releases"]["1.0.0"]["provides"]
    with patch.object(catalog, "_get_merged_packs", return_value={"sample": entry}):
        selected = catalog.get_pack_info("sample", "1.0.0")
    assert "requires" not in selected
    assert "provides" not in selected


def test_selected_download_uses_old_url_and_digest_without_lookup(project_dir):
    old_bytes = _archive()
    catalog = PresetCatalog(project_dir)
    info = {**_entry(old_bytes), "_install_allowed": True, "_catalog_name": "trusted"}
    with patch.object(catalog, "_get_merged_packs", return_value={"sample": info}):
        selected = catalog.get_pack_info("sample", "1.0")
    with (
        patch.object(catalog, "get_pack_info", side_effect=AssertionError("re-lookup")),
        patch.object(
            catalog, "_open_url", return_value=_response(old_bytes, OLD_URL)
        ) as opened,
    ):
        saved = catalog.download_pack_info(selected, target_dir=project_dir)
    assert saved.read_bytes() == old_bytes
    assert opened.call_args.args[0] == OLD_URL


def test_selected_download_rejects_discovery_digest_and_redirect(project_dir):
    old_bytes = _archive()
    selected = {
        "id": "sample",
        "version": "1.0.0",
        "download_url": OLD_URL,
        "sha256": hashlib.sha256(old_bytes).hexdigest(),
        "_install_allowed": False,
        "_catalog_name": "community",
    }
    catalog = PresetCatalog(project_dir)
    with patch.object(catalog, "_open_url") as open_url:
        with pytest.raises(PresetError, match="does not allow installation"):
            catalog.download_pack_info(selected, project_dir)
        open_url.assert_not_called()
    selected["_install_allowed"] = True
    with (
        patch.object(catalog, "_open_url", return_value=_response(b"wrong", OLD_URL)),
        pytest.raises(PresetError, match="[Ii]ntegrity"),
    ):
        catalog.download_pack_info(selected, project_dir)
    with (
        patch.object(
            catalog,
            "_open_url",
            return_value=_response(old_bytes, "http://evil.test/a.zip"),
        ),
        pytest.raises(PresetError, match="disallowed URL"),
    ):
        catalog.download_pack_info(selected, project_dir)
    assert not list(project_dir.glob("sample-*.zip"))


def test_selected_download_rejects_unsafe_intermediate_redirect(project_dir):
    selected = {
        "id": "sample",
        "version": "1.0.0",
        "download_url": OLD_URL,
        "sha256": "f" * 64,
        "_install_allowed": True,
    }
    catalog = PresetCatalog(project_dir)

    def redirect(_url, **kwargs):
        kwargs["redirect_validator"](OLD_URL, "http://evil.test/transit")
        return _response(_archive(), OLD_URL)

    with (
        patch.object(catalog, "_open_url", side_effect=redirect),
        pytest.raises(PresetError, match="disallowed URL"),
    ):
        catalog.download_pack_info(selected, project_dir)
    assert not list(project_dir.glob("sample-*.zip"))


@pytest.mark.parametrize(
    "bad_id,bad_version", [("other", "1.0.0"), ("sample", "2.0.0")]
)
def test_archive_identity_checked_before_install(
    project_dir, tmp_path, bad_id, bad_version
):
    archive_path = tmp_path / "sample.zip"
    archive_path.write_bytes(_archive(bad_id, bad_version))
    manager = PresetManager(project_dir)
    with pytest.raises(PresetValidationError, match="does not match catalog"):
        manager.install_from_zip(
            archive_path, "1.0.0", expected_id="sample", expected_version="1.0.0"
        )
    assert not manager.registry.is_installed(bad_id)


def test_archive_mismatch_does_not_replace_installed_preset(project_dir, tmp_path):
    good_path = tmp_path / "good.zip"
    bad_path = tmp_path / "bad.zip"
    good_path.write_bytes(_archive("sample", "1.0.0"))
    bad_path.write_bytes(_archive("sample", "2.0.0"))
    manager = PresetManager(project_dir)
    manager.install_from_zip(good_path, "1.0.0")
    with pytest.raises(PresetValidationError, match="does not match catalog"):
        manager.install_from_zip(
            bad_path,
            "1.0.0",
            force=True,
            expected_id="sample",
            expected_version="1.0.0",
        )
    assert manager.get_pack("sample").version == "1.0.0"


def test_cli_installs_exact_archive_and_lists_versions(project_dir):
    old_bytes = _archive()
    catalog_entry = _entry(old_bytes)
    urls: list[str] = []

    def open_url(_self, url, **_kwargs):
        urls.append(url)
        return _response(old_bytes, url)

    with (
        patch.object(Path, "cwd", return_value=project_dir),
        patch("specify_cli.get_speckit_version", return_value="1.0.0"),
        patch.object(
            PresetCatalog,
            "_get_merged_packs",
            return_value={
                "sample": {
                    **catalog_entry,
                    "_catalog_name": "trusted",
                    "_install_allowed": True,
                }
            },
        ),
        patch.object(PresetCatalog, "_open_url", open_url),
    ):
        listed = CliRunner().invoke(app, ["preset", "info", "sample", "--versions"])
        installed = CliRunner().invoke(
            app, ["preset", "add", "sample", "--version", "1.0"]
        )

    assert listed.exit_code == 0, listed.output
    assert "2.0.0 (current)" in listed.output and "1.0.0" in listed.output
    assert installed.exit_code == 0, installed.output
    assert urls == [OLD_URL]
    assert PresetManager(project_dir).get_pack("sample").version == "1.0.0"


def test_cli_rejects_missing_release_and_discovery_without_download(project_dir):
    entry = _entry()
    with (
        patch.object(Path, "cwd", return_value=project_dir),
        patch.object(
            PresetCatalog,
            "_get_merged_packs",
            return_value={
                "sample": {
                    **entry,
                    "_catalog_name": "discovery",
                    "_install_allowed": False,
                }
            },
        ),
        patch.object(PresetCatalog, "_open_url") as open_url,
    ):
        info = CliRunner().invoke(app, ["preset", "info", "sample", "--versions"])
        refused = CliRunner().invoke(
            app, ["preset", "add", "sample", "--version", "1.0.0"]
        )
    assert info.exit_code == 0 and "Discovery only" in info.output
    assert refused.exit_code == 1 and "discovery-only" in refused.output
    open_url.assert_not_called()
    with (
        patch.object(Path, "cwd", return_value=project_dir),
        patch.object(
            PresetCatalog,
            "_get_merged_packs",
            return_value={
                "sample": {
                    **entry,
                    "_catalog_name": "trusted",
                    "_install_allowed": True,
                }
            },
        ),
        patch.object(PresetCatalog, "_open_url") as open_url,
    ):
        absent = CliRunner().invoke(
            app, ["preset", "add", "sample", "--version", "9.0"]
        )
    assert absent.exit_code == 1 and "no catalog release" in absent.output
    open_url.assert_not_called()


@pytest.mark.parametrize(
    "args",
    [
        ["preset", "add", "sample", "--from", OLD_URL, "--version", "1.0"],
        ["preset", "add", "sample", "--dev", ".", "--version", "1.0"],
        ["preset", "add", "sample", "--version", ""],
    ],
)
def test_cli_rejects_version_with_non_catalog_source(project_dir, args):
    with patch.object(Path, "cwd", return_value=project_dir):
        result = CliRunner().invoke(app, args)
    assert result.exit_code == 1
    assert "--version requires a catalog" in result.output
