"""Regression coverage for exact bundle releases in catalog entries."""

from __future__ import annotations

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundles.catalog_versions import available_versions, select_release
from specify_cli.bundles.catalogs import CatalogEntry, load_catalog_payload
from specify_cli.bundles.versioning import parse_version
from tests.specify_cli.bundles.helpers import catalog_entry_dict, catalog_payload


def _entry(**overrides) -> CatalogEntry:
    return CatalogEntry.from_dict(catalog_entry_dict("history", **overrides))


def _record(**overrides) -> dict:
    data = {
        "download_url": "https://example.com/history-1.1.0.zip",
        "sha256": "a" * 64,
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {"extensions": 2},
        "verified": True,
    }
    data.update(overrides)
    return data


def test_legacy_entry_keeps_current_behavior_and_load_rejects_history():
    plain_legacy = _entry(version="legacy")
    legacy = _entry(version="legacy", releases={"1.0.0": _record()})
    assert select_release(plain_legacy, "legacy") is plain_legacy
    assert available_versions(plain_legacy) == ["legacy"]
    assert legacy.version == "legacy"

    malformed = _entry(releases=[])
    with pytest.raises(BundlerError, match="invalid releases mapping"):
        load_catalog_payload(catalog_payload({"history": malformed.raw}))
    with pytest.raises(BundlerError, match="invalid current version 'legacy'"):
        load_catalog_payload(catalog_payload({"history": legacy.raw}))


def test_historical_selection_uses_its_own_current_only_fields():
    entry = _entry(
        version="1.2.0",
        releases={
            "1.1.0": _record(
                download_url="https://example.com/history-1.1.0.zip",
                sha256="b" * 64,
            ),
            "1.0.0": {
                "download_url": "https://example.com/history-1.0.0.zip",
                "sha256": "c" * 64,
            },
        },
    )

    selected = select_release(entry, "v1.1.0")

    assert selected is not None
    assert selected.version == "1.1.0"
    assert selected.download_url.endswith("1.1.0.zip")
    assert selected.sha256 == "b" * 64
    assert selected.requires_speckit_version == ">=0.1.0"
    assert selected.provides == {"extensions": 2}
    assert selected.verified is True
    assert selected.raw is not None and "releases" not in selected.raw
    assert available_versions(entry) == ["1.2.0", "1.1.0", "1.0.0"]

    oldest = select_release(entry, "1.0.0")
    assert oldest is not None
    assert oldest.requires_speckit_version == ""
    assert oldest.provides == {}
    assert oldest.verified is False


def test_current_and_equivalent_spelling_select_current_release():
    entry = _entry(version="1.2.0", releases={"1.1.0": _record()})

    assert select_release(entry, None) is entry
    assert select_release(entry, "1.2.0") is entry
    assert select_release(entry, "v1.2.0") is entry
    assert select_release(entry, "not-a-version") is None
    assert select_release(entry, "1.0.0") is None


def _without(field: str) -> dict:
    data = _record()
    del data[field]
    return data


_MALFORMED_HISTORY = [
    ([], "invalid releases mapping"),
    ({"1.1.0": []}, "release '1.1.0' must be an object"),
    ({"1.1.0": _without("download_url")}, "release '1.1.0' needs a download_url"),
    ({"1.1.0": _record(download_url="")}, "release '1.1.0' needs a download_url"),
    (
        {"1.1.0": _record(download_url="file:///tmp/history.zip")},
        "release '1.1.0' has an invalid download_url",
    ),
    (
        {"1.1.0": _record(download_url="http://example.com/history.zip")},
        "release '1.1.0' has an invalid download_url",
    ),
    ({"1.1.0": _without("sha256")}, "release '1.1.0' needs a SHA-256 digest"),
    ({"1.1.0": _record(sha256="bad")}, "release '1.1.0' needs a SHA-256 digest"),
    ({"1.1.0": _record(sha256="a" * 63)}, "release '1.1.0' needs a SHA-256 digest"),
    (
        {"1.1.0": _record(sha256=f"md5:{'a' * 64}")},
        "release '1.1.0' needs a SHA-256 digest",
    ),
    ({"1.1.0": _record(sha256=64)}, "release '1.1.0' needs a SHA-256 digest"),
    ({"1.1.0": _record(requires=[])}, "release '1.1.0' has invalid requires"),
    ({"1.1.0": _record(provides=[])}, "release '1.1.0' has invalid provides"),
    ({"1.1.0": _record(id="history")}, "release '1.1.0' contains reserved fields"),
    ({"1.1.0": _record(version="1.1.0")}, "release '1.1.0' contains reserved fields"),
    ({"1.1.0": _record(releases={})}, "release '1.1.0' contains reserved fields"),
    ({"": _record()}, "invalid release version key"),
    ({"1.1.0\n": _record()}, "invalid release version '1.1.0\n'"),
    ({"1.0": _record()}, "invalid release version '1.0'"),
    ({"1.0.0.post1": _record()}, "invalid release version '1.0.0.post1'"),
    ({"not-a-version": _record()}, "invalid release version 'not-a-version'"),
    # Strict SemVer, but not PEP 440-comparable.
    ({"1.0.0-alpha.beta": _record()}, "invalid release version '1.0.0-alpha.beta'"),
    ({"1.2.0": _record()}, "repeats release version '1.2.0'"),
    ({"v1.2.0": _record()}, "repeats release version 'v1.2.0'"),
    (
        {"1.1.0-rc.1": _record(), "1.1.0-rc1": _record()},
        "repeats release version",
    ),
    ({"1.1.0": _record(tags="invalid")}, "release '1.1.0' has Catalog entry"),
    ({"1.1.0": _record(verified="yes")}, "release '1.1.0' has Catalog entry"),
]


@pytest.mark.parametrize("lookup", ["available_versions", "select_release"])
@pytest.mark.parametrize("releases, message", _MALFORMED_HISTORY)
def test_malformed_history_is_rechecked_for_directly_constructed_entries(
    releases, message, lookup
):
    entry = _entry(releases=releases)

    with pytest.raises(BundlerError, match=f"Bundle 'history'.*{message}"):
        if lookup == "available_versions":
            available_versions(entry)
        else:
            select_release(entry, "1.2.0")


@pytest.mark.parametrize("releases, message", _MALFORMED_HISTORY)
def test_malformed_history_is_rejected_when_catalog_loads(releases, message):
    entry = _entry(releases=releases)

    with pytest.raises(BundlerError, match=f"Bundle 'history'.*{message}"):
        load_catalog_payload(catalog_payload({"history": entry.raw}))


@pytest.mark.parametrize(
    "current, message",
    [
        ("", "no current version"),
        ("1.2", "invalid current version '1.2'"),
        # Strict SemVer, but not PEP 440-comparable.
        ("1.2.0-alpha.beta", "invalid current version '1.2.0-alpha.beta'"),
    ],
)
def test_history_requires_valid_current_semver(current, message):
    entry = _entry(version=current, releases={"1.1.0": _record()})

    with pytest.raises(BundlerError, match=message):
        available_versions(entry)
    with pytest.raises(BundlerError, match=message):
        select_release(entry, None)
    with pytest.raises(BundlerError, match=message):
        load_catalog_payload(catalog_payload({"history": entry.raw}))


@pytest.mark.parametrize(
    "digest",
    [
        "a" * 64,
        "A" * 64,
        f"sha256:{'a' * 64}",
        f"SHA256:{'A' * 64}",
        f" SHA256: {'A' * 64} ",
        f"\tsha256:{'a' * 64}\n",
    ],
)
def test_history_accepts_digest_spellings_the_downloader_accepts(digest):
    entry = _entry(releases={"1.1.0": _record(sha256=digest)})

    assert available_versions(entry) == ["1.2.0", "1.1.0"]
    selected = select_release(entry, "1.1.0")
    assert selected is not None
    assert selected.sha256 == digest.strip()


def test_history_accepts_semver_spellings_as_keys():
    valid = _entry(releases={"v1.1.0": _record(), "1.0.0-rc.1": _record()})

    assert available_versions(valid) == ["1.2.0", "v1.1.0", "1.0.0-rc.1"]
    selected = select_release(valid, "1.1.0")
    assert selected is not None
    assert selected.version == "v1.1.0"


def test_historical_record_overrides_inherited_fields():
    entry = _entry(
        author="Current Author",
        repository="https://example.com/history",
        releases={"1.1.0": _record(author="Old Author")},
    )

    selected = select_release(entry, "1.1.0")

    assert selected is not None
    assert selected.author == "Old Author"
    assert selected.repository == "https://example.com/history"
    assert selected.name == entry.name


@pytest.mark.parametrize(
    "version",
    [
        "v1.1.0",
        "1.0.0-rc.1",
        "1.0.0-rc1",
        "1.0.0-alpha.1",
        "1.0.0-RC.1",
        "1.0.0-beta",
        "1.0.0+b.1",
    ],
)
def test_release_parser_agrees_with_bundle_version_parser(version):
    from packaging.version import InvalidVersion, Version

    try:
        packaging_version = Version(version)
    except InvalidVersion:
        with pytest.raises(BundlerError):
            parse_version(version)
    else:
        assert packaging_version == parse_version(version)


@pytest.mark.parametrize("entry_id", [None, "different"])
def test_entry_id_errors_precede_history_validation(entry_id):
    entry = catalog_entry_dict("history", releases=[])
    if entry_id is None:
        del entry["id"]
        expected = "missing its 'id'"
    else:
        entry["id"] = entry_id
        expected = "id mismatch"

    with pytest.raises(BundlerError, match=expected):
        load_catalog_payload(catalog_payload({"history": entry}))
