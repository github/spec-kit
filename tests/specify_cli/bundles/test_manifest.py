"""Unit tests for ``specify_cli.bundles.manifest`` bundle references."""
from __future__ import annotations

import pytest

from specify_cli.bundles import BundlerError
from specify_cli.bundles.manifest import (
    SUPPORTED_SCHEMA_VERSIONS,
    BundleManifest,
    BundleRef,
)
from tests.specify_cli.bundles.helpers import (
    reference_manifest_dict,
    valid_manifest_dict,
)


def _manifest(data: dict) -> BundleManifest:
    return BundleManifest.from_dict(data)


def _errors(data: dict) -> list[str]:
    return _manifest(data).structural_errors()


def test_supported_schema_versions_include_reference_schema():
    assert SUPPORTED_SCHEMA_VERSIONS == {"1.0", "1.1"}


def test_bundle_ref_label_pinned_and_unpinned():
    assert BundleRef(id="bugfix", version="1.0.1").label() == "bundle:bugfix@1.0.1"
    assert BundleRef(id="bugfix").label() == "bundle:bugfix@unpinned"


def test_provides_bundles_parsed_in_declaration_order():
    manifest = _manifest(
        reference_manifest_dict(
            [
                {"id": "bugfix", "version": "1.0.1", "source": "default"},
                {"id": "qa-pack", "version": "2.0.0"},
            ]
        )
    )

    assert manifest.bundles == [
        BundleRef(id="bugfix", version="1.0.1", source="default"),
        BundleRef(id="qa-pack", version="2.0.0", source=None),
    ]
    assert manifest.structural_errors() == []


def test_reference_values_are_stripped_and_version_coerced_to_text():
    manifest = _manifest(
        reference_manifest_dict(
            [{"id": " bugfix ", "version": " 1.0.1 ", "source": " default "}]
        )
    )

    assert manifest.bundles == [BundleRef("bugfix", "1.0.1", "default")]


@pytest.mark.parametrize("blank", [None, "", " ", "\t "])
def test_blank_reference_source_and_version_are_unset(blank):
    manifest = _manifest(
        reference_manifest_dict(
            [{"id": "bugfix", "version": blank, "source": blank}]
        )
    )

    assert manifest.bundles == [BundleRef("bugfix", None, None)]


def test_components_stay_own_only_when_bundles_declared():
    manifest = _manifest(
        reference_manifest_dict(
            [{"id": "bugfix", "version": "1.0.1"}],
            extensions=[{"id": "secure-design", "version": "0.5.0"}],
        )
    )

    assert [c.id for c in manifest.components] == ["secure-design"]
    assert manifest.structural_errors() == []


def test_reference_only_bundle_is_valid():
    manifest = _manifest(
        reference_manifest_dict([{"id": "bugfix", "version": "1.0.1"}])
    )

    assert manifest.components == []
    assert manifest.structural_errors() == []


@pytest.mark.parametrize("schema_version", ["1.0", "1.1"])
@pytest.mark.parametrize("declaration", ["absent", "null", "empty"])
def test_absent_empty_or_null_references_accepted_under_supported_schemas(
    schema_version, declaration
):
    data = valid_manifest_dict(schema_version=schema_version)
    if declaration == "null":
        data["provides"]["bundles"] = None
    elif declaration == "empty":
        data["provides"]["bundles"] = []

    manifest = _manifest(data)

    assert manifest.bundles == []
    assert manifest.structural_errors() == []


def test_schema_1_1_without_references_is_valid():
    manifest = _manifest(valid_manifest_dict(schema_version="1.1"))

    assert manifest.bundles == []
    assert manifest.structural_errors() == []


def test_references_with_schema_1_0_rejected():
    errors = _errors(
        reference_manifest_dict(
            [{"id": "bugfix", "version": "1.0.1"}], schema_version="1.0"
        )
    )

    assert errors == ['Bundle references require schema_version "1.1".']


def test_references_with_missing_schema_rejected():
    data = reference_manifest_dict([{"id": "bugfix", "version": "1.0.1"}])
    del data["schema_version"]

    errors = _errors(data)

    assert any('require schema_version "1.1"' in e for e in errors)
    assert any("not supported" in e for e in errors)


def test_unsupported_schema_rejected():
    errors = _errors(valid_manifest_dict(schema_version="2.0"))

    assert any("schema_version '2.0' is not supported" in e for e in errors)


def test_reference_missing_id_rejected():
    errors = _errors(reference_manifest_dict([{"version": "1.0.1"}]))

    assert errors == ["A bundle reference is missing its 'id'."]


@pytest.mark.parametrize("bad_id", ["../evil", "a/b", "Upper", "-lead", "trail-"])
def test_reference_unsafe_id_rejected(bad_id):
    errors = _errors(reference_manifest_dict([{"id": bad_id, "version": "1.0.1"}]))

    assert any(
        f"Bundle reference id '{bad_id}' must be a slug" in e for e in errors
    )


def test_reference_missing_version_rejected():
    errors = _errors(reference_manifest_dict([{"id": "bugfix"}]))

    assert errors == ["bundle reference 'bugfix' must be pinned to a 'version'."]


@pytest.mark.parametrize("bad_version", ["not-semver", ">=1.0.0", "1.0"])
def test_reference_invalid_version_rejected(bad_version):
    errors = _errors(
        reference_manifest_dict([{"id": "bugfix", "version": bad_version}])
    )

    assert errors == [
        f"bundle reference 'bugfix' has invalid version '{bad_version}'."
    ]


def test_reference_version_with_v_prefix_accepted():
    errors = _errors(reference_manifest_dict([{"id": "bugfix", "version": "v1.0.1"}]))

    assert errors == []


def test_duplicate_reference_rejected_even_at_different_versions():
    errors = _errors(
        reference_manifest_dict(
            [
                {"id": "bugfix", "version": "1.0.1"},
                {"id": "bugfix", "version": "1.0.2"},
            ]
        )
    )

    assert any(
        "Duplicate bundle reference 'bugfix'" in e
        and "declare each bundle reference only once" in e
        for e in errors
    )


def test_self_reference_rejected():
    errors = _errors(
        reference_manifest_dict(
            [{"id": "team", "version": "1.0.0"}], bundle_id="team"
        )
    )

    assert errors == [
        "Bundle reference 'team' is invalid: a bundle cannot reference itself."
    ]


def test_reference_to_other_bundle_is_not_self_reference():
    errors = _errors(
        reference_manifest_dict(
            [{"id": "bugfix", "version": "1.0.1"}], bundle_id="team"
        )
    )

    assert errors == []


@pytest.mark.parametrize(
    "bundles", ["bugfix", {"id": "bugfix", "version": "1.0.1"}, 5]
)
def test_non_list_bundles_rejected(bundles):
    with pytest.raises(BundlerError, match=r"provides\.bundles must be a list"):
        _manifest(reference_manifest_dict(bundles))


@pytest.mark.parametrize("entry", ["bugfix", ["bugfix"], 1, None])
def test_non_mapping_bundle_entry_rejected(entry):
    with pytest.raises(BundlerError, match=r"provides\.bundles entry must be a mapping"):
        _manifest(reference_manifest_dict([entry]))
