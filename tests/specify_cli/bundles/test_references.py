"""Unit tests for the bundle reference checker (T047 / FR-005 / SC-007).

Resolution is offline-first: bundled and installed components resolve without a
network; unknown ids fail online and downgrade to warnings offline.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from specify_cli.bundles.manifest import ComponentRef
from specify_cli.bundles.references import make_reference_checker
from tests.specify_cli.bundles.helpers import bundled_extension_version, make_project


def _ref(kind: str, id_: str, version: str | None = "1.0.0") -> ComponentRef:
    return ComponentRef(kind=kind, id=id_, version=version)


def test_bundled_extension_resolves(tmp_path: Path):
    root = make_project(tmp_path)
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)
    assert check(
        _ref("extensions", "agent-context", bundled_extension_version("agent-context"))
    ) is None
    assert warnings == []


def test_builtin_step_type_resolves(tmp_path: Path):
    """A built-in step type must resolve, like a bundled extension.

    Spec Kit ships 12 step types as built-ins registered in ``STEP_REGISTRY``
    rather than as on-disk asset directories, so there is no
    ``_locate_bundled_step``. The ``steps`` branch of ``_resolved_locally`` only
    asked ``StepRegistry(root).is_installed()``, which tracks *community* step
    types installed under ``.specify/workflows/steps/`` — so every built-in step
    type was reported as an unresolved reference.
    """
    from specify_cli.workflows import BUILTIN_STEP_TYPES

    root = make_project(tmp_path)
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)

    for step_id in ("shell", "gate", "command", "if", "slot"):
        assert step_id in BUILTIN_STEP_TYPES, step_id
        assert check(_ref("steps", step_id, None)) is None, step_id
    assert warnings == []


def test_community_step_is_not_treated_as_bundled(tmp_path: Path):
    """A community step loaded for one project must not resolve for another.

    `load_custom_steps` adds project-installed ids to the process-global
    `STEP_REGISTRY` and never removes them, so checking `STEP_REGISTRY` here
    would accept project A's community step as "bundled" while validating
    project B. `BUILTIN_STEP_TYPES` is snapshotted before any custom step can
    load, which is why the check uses it instead.
    """
    from specify_cli.workflows import (
        BUILTIN_STEP_TYPES,
        STEP_REGISTRY,
        _register_step,
    )
    from specify_cli.workflows.base import StepBase, StepResult, StepStatus

    class _CommunityStep(StepBase):
        type_key = "community-only-step"

        def execute(self, config, context):  # pragma: no cover - never run
            return StepResult(status=StepStatus.COMPLETED)

    # Simulate project A having loaded a community step into the global registry.
    _register_step(_CommunityStep())
    try:
        assert "community-only-step" in STEP_REGISTRY
        assert "community-only-step" not in BUILTIN_STEP_TYPES

        # Project B does not have it installed, so it must NOT resolve locally.
        root = make_project(tmp_path)
        warnings: list[str] = []
        check = make_reference_checker(root, allow_network=True, warnings=warnings)
        problem = check(_ref("steps", "community-only-step"))
        assert problem is not None, "leaked community step resolved as bundled"
        assert "community-only-step" in problem
    finally:
        STEP_REGISTRY.pop("community-only-step", None)


def test_unknown_step_type_still_errors_online(tmp_path: Path):
    """The guard must not make every step id resolve."""
    root = make_project(tmp_path)
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)
    problem = check(_ref("steps", "no-such-step-type"))
    assert problem is not None
    assert "no-such-step-type" in problem


def test_unknown_reference_errors_online(tmp_path: Path):
    root = make_project(tmp_path)
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=True, warnings=warnings)
    problem = check(_ref("presets", "does-not-exist"))
    assert problem is not None
    assert "does-not-exist" in problem


def test_unknown_reference_warns_offline(tmp_path: Path):
    root = make_project(tmp_path)
    warnings: list[str] = []
    check = make_reference_checker(root, allow_network=False, warnings=warnings)
    assert check(_ref("presets", "does-not-exist")) is None
    assert any("does-not-exist" in w for w in warnings)


@pytest.mark.parametrize("allow_network", [False, True])
def test_wrong_bundled_extension_pin_is_definitive(
    tmp_path, monkeypatch, allow_network,
):
    from specify_cli.extensions import ExtensionCatalog

    root = make_project(tmp_path)
    monkeypatch.setattr(
        ExtensionCatalog, "get_extension_info",
        lambda self, _id, version=None: {
            "version": version or "999.0.0",
            "_catalog_name": "trusted",
            "_install_allowed": True,
        },
    )
    warnings = []
    check = make_reference_checker(root, allow_network=allow_network, warnings=warnings)

    problem = check(_ref("extensions", "agent-context", "999.0.0"))
    assert problem is not None and "resolved version is" in problem
    assert warnings == []
    if allow_network:
        assert check(ComponentRef(
            kind="extensions", id="agent-context", version="999.0.0", source="trusted"
        )) is None
        assert warnings == []
    assert check(
        _ref("extensions", "agent-context", bundled_extension_version("agent-context"))
    ) is None


@pytest.mark.parametrize("allow_network", [False, True])
def test_bundled_preset_pin_mismatch_is_definitive(
    tmp_path, monkeypatch, allow_network,
):
    import specify_cli._assets as assets
    from specify_cli.presets import PresetCatalog

    bundled = tmp_path / "preset"
    bundled.mkdir()
    (bundled / "preset.yml").write_text(
        "preset:\n  id: requested\n  version: 1.0.0\n", encoding="utf-8"
    )
    monkeypatch.setattr(assets, "_locate_bundled_preset", lambda _id: bundled)
    monkeypatch.setattr(
        PresetCatalog, "get_pack_info",
        lambda self, _id, version=None: {
            "version": version or "2.0.0",
            "_catalog_name": "trusted",
            "_install_allowed": True,
        },
    )
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=allow_network, warnings=warnings)

    problem = check(_ref("presets", "requested", "2.0.0"))
    assert problem is not None and "resolved version is 1.0.0" in problem
    assert warnings == []
    if allow_network:
        assert check(ComponentRef(
            kind="presets", id="requested", version="2.0.0", source="trusted"
        )) is None
        assert warnings == []
    assert check(_ref("presets", "requested", "1.0.0")) is None


def test_bundled_preset_mismatch_allows_matching_installed_version(
    tmp_path, monkeypatch,
):
    from types import SimpleNamespace

    import specify_cli._assets as assets
    from specify_cli.bundles import primitives

    bundled = tmp_path / "preset"
    bundled.mkdir()
    (bundled / "preset.yml").write_text(
        "preset:\n  id: requested\n  version: 1.0.0\n", encoding="utf-8"
    )
    monkeypatch.setattr(assets, "_locate_bundled_preset", lambda _id: bundled)
    monkeypatch.setattr(
        primitives, "primitive_manager",
        lambda *args, **kwargs: SimpleNamespace(
            is_installed=lambda _component: True,
            installed_version=lambda _component: "2.0.0",
        ),
    )
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=False, warnings=warnings)

    assert check(_ref("presets", "requested", "2.0.0")) is None
    assert warnings == []


@pytest.mark.parametrize("legacy", [False, True])
def test_extension_http_protocol_error_is_unreachable_catalog(
    tmp_path, monkeypatch, legacy,
):
    from http.client import BadStatusLine

    from specify_cli.extensions import (
        CatalogEntry,
        ExtensionCatalog,
        ExtensionCatalogFetchError,
    )

    catalog = ExtensionCatalog(tmp_path)
    entry = CatalogEntry("https://example.com/catalog.json", "trusted", 1, True)
    monkeypatch.setattr(catalog, "get_catalog_url", lambda: entry.url)

    def bad_status(*args, **kwargs):
        raise BadStatusLine("bad response")

    monkeypatch.setattr(catalog, "_open_url", bad_status)
    with pytest.raises(ExtensionCatalogFetchError, match="bad response"):
        if legacy:
            catalog.fetch_catalog(force_refresh=True)
        else:
            catalog._fetch_single_catalog(entry, force_refresh=True)


def test_online_validation_warns_for_extension_http_protocol_error(
    tmp_path, monkeypatch,
):
    from http.client import BadStatusLine

    from specify_cli.extensions import CatalogEntry, ExtensionCatalog

    monkeypatch.setattr(
        ExtensionCatalog, "get_active_catalogs",
        lambda self: [CatalogEntry("https://example.com/catalog.json", "trusted", 1, True)],
    )

    def bad_status(*args, **kwargs):
        raise BadStatusLine("bad response")

    monkeypatch.setattr(ExtensionCatalog, "_open_url", bad_status)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(_ref("extensions", "requested")) is None
    assert len(warnings) == 1 and "unreachable" in warnings[0]


def test_online_validation_checks_winning_exact_release_and_source(tmp_path, monkeypatch):
    import specify_cli._assets as assets
    from specify_cli.workflows.catalog import WorkflowCatalog

    monkeypatch.setattr(assets, "_locate_bundled_workflow", lambda _id: None)
    lookups = []

    def lookup(_self, _id, version=None):
        lookups.append(version)
        if version == "1.0.0":
            return {
                "version": "1.0.0", "_catalog_name": "winning",
                "_install_allowed": True,
            }
        if version is None:
            return {
                "version": "2.0.0", "_catalog_name": "winning",
                "_install_allowed": True,
            }
        return None

    monkeypatch.setattr(WorkflowCatalog, "get_workflow_info", lookup)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)
    requested = ComponentRef(
        kind="workflows", id="catalog-workflow", version="1.0.0", source="winning"
    )

    assert check(requested) is None
    assert lookups == [None, "1.0.0"]
    assert check(ComponentRef(kind="workflows", id=requested.id, version="3.0.0"))
    assert check(ComponentRef(
        kind="workflows", id=requested.id, version="1.0.0", source="lower"
    ))
    assert warnings == []


def test_online_validation_rejects_discovery_only_exact_release(tmp_path, monkeypatch):
    from specify_cli.workflows.catalog import StepCatalog

    monkeypatch.setattr(
        StepCatalog, "get_step_info",
        lambda _self, _id, version=None: {
            "version": version or "2.0.0", "_catalog_name": "winning",
            "_install_allowed": version is None,
        },
    )
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(_ref("steps", "catalog-step", "1.0.0"))
    assert warnings == []


def test_online_validation_reports_invalid_release_metadata(tmp_path, monkeypatch):
    from specify_cli.workflows.catalog import StepCatalog, StepCatalogError

    def invalid_release(_self, _id, version=None):
        raise StepCatalogError("Step release needs a SHA-256 digest.")

    monkeypatch.setattr(StepCatalog, "get_step_info", invalid_release)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert "SHA-256" in check(_ref("steps", "invalid-release"))
    assert warnings == []


def test_online_validation_warns_when_catalogs_are_unreachable(tmp_path, monkeypatch):
    from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowCatalogFetchError

    def unavailable(_self, _id, version=None):
        raise WorkflowCatalogFetchError("All configured catalogs failed to fetch.")

    monkeypatch.setattr(WorkflowCatalog, "get_workflow_info", unavailable)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(_ref("workflows", "unreachable")) is None
    assert len(warnings) == 1
    assert "unreachable" in warnings[0]


@pytest.mark.parametrize("kind", ["extensions", "presets", "workflows", "steps"])
@pytest.mark.parametrize(
    ("unreachable", "has_match"),
    [
        ("high", False),
        ("low", False),
        ("high", True),
        ("low", True),
        (None, False),
    ],
)
def test_online_validation_distinguishes_partial_outage_from_missing_reference(
    tmp_path, monkeypatch, kind, unreachable, has_match,
):
    from specify_cli.extensions import (
        CatalogEntry,
        ExtensionCatalog,
        ExtensionCatalogFetchError,
    )
    from specify_cli.presets import PresetCatalog, PresetCatalogEntry
    from specify_cli.presets._catalog import PresetCatalogFetchError
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        StepCatalogFetchError,
        WorkflowCatalog,
        WorkflowCatalogEntry,
        WorkflowCatalogFetchError,
    )

    catalog, entry_type, fetch_error = {
        "extensions": (ExtensionCatalog, CatalogEntry, ExtensionCatalogFetchError),
        "presets": (PresetCatalog, PresetCatalogEntry, PresetCatalogFetchError),
        "workflows": (WorkflowCatalog, WorkflowCatalogEntry, WorkflowCatalogFetchError),
        "steps": (StepCatalog, StepCatalogEntry, StepCatalogFetchError),
    }[kind]
    sources = [
        entry_type("https://example.com/high.json", "high", 1, True),
        entry_type("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda self: sources)
    visited = []

    def fetch(self, entry, force_refresh=False):
        visited.append(entry.name)
        if entry.name == unreachable:
            raise fetch_error("catalog timed out")
        contents = {"requested": {"version": "1.0.0"}} if has_match else {}
        return {kind: contents}

    monkeypatch.setattr(catalog, "_fetch_single_catalog", fetch)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    problem = check(_ref(kind, "requested"))
    if has_match and unreachable == "high":
        assert problem is None
        assert len(warnings) == 1
        assert "unreachable" in warnings[0]
        assert visited == ["high", "low"]
    elif has_match:
        assert problem is None
        assert warnings == []
        assert visited == ["high", "high"]
    elif unreachable is not None:
        assert problem is None
        assert len(warnings) == 1
        assert "unreachable" in warnings[0]
        assert visited == ["high", "low"]
    else:
        assert problem is not None and "not available" in problem
        assert warnings == []
        assert visited == ["high", "low"]


@pytest.mark.parametrize("kind", ["extensions", "presets"])
def test_online_validation_warns_for_unreachable_component_catalog(
    tmp_path, monkeypatch, kind,
):
    from specify_cli.extensions import ExtensionCatalog, ExtensionCatalogFetchError
    from specify_cli.presets import PresetCatalog
    from specify_cli.presets._catalog import PresetCatalogFetchError

    if kind == "extensions":
        catalog, method, failure = (
            ExtensionCatalog, "get_extension_info",
            ExtensionCatalogFetchError("Failed to fetch any extension catalog"),
        )
    else:
        catalog, method, failure = (
            PresetCatalog, "get_pack_info",
            PresetCatalogFetchError("Failed to fetch preset catalog from https://example.com: timed out"),
        )

    def unavailable(_self, _id, version=None):
        raise failure

    monkeypatch.setattr(catalog, method, unavailable)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(_ref(kind, "unreachable-component")) is None
    assert len(warnings) == 1
    assert "unreachable" in warnings[0]


@pytest.mark.parametrize("kind", ["extensions", "presets"])
def test_online_validation_rejects_malformed_component_release(
    tmp_path, monkeypatch, kind,
):
    from specify_cli.extensions import ExtensionCatalog, ExtensionError
    from specify_cli.presets import PresetCatalog
    from specify_cli.presets._manifest import PresetError

    catalog, method, failure = (
        (ExtensionCatalog, "get_extension_info", ExtensionError("Invalid release digest"))
        if kind == "extensions"
        else (PresetCatalog, "get_pack_info", PresetError("Invalid release digest"))
    )

    def invalid(_self, _id, version=None):
        raise failure

    monkeypatch.setattr(catalog, method, invalid)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert "Invalid release digest" in check(_ref(kind, "invalid-component"))
    assert warnings == []


def test_online_validation_rejects_malformed_extension_catalog(
    tmp_path, monkeypatch,
):
    from specify_cli.extensions import (
        CatalogEntry,
        ExtensionCatalog,
    )

    monkeypatch.setattr(
        ExtensionCatalog, "get_active_catalogs",
        lambda self: [CatalogEntry("https://example.com/catalog.json", "trusted", 1, True)],
    )
    monkeypatch.setattr(
        ExtensionCatalog, "_fetch_single_catalog",
        lambda self, entry, force_refresh=False:
            self._validate_catalog_payload({"extensions": []}, entry.url),
    )
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert "Invalid catalog format" in check(_ref("extensions", "invalid"))
    assert warnings == []


def test_online_validation_rejects_malformed_winning_extension_catalog(
    tmp_path, monkeypatch,
):
    from specify_cli.extensions import CatalogEntry, ExtensionCatalog

    sources = [
        CatalogEntry("https://example.com/high.json", "high", 1, True),
        CatalogEntry("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(ExtensionCatalog, "get_active_catalogs", lambda self: sources)

    def fetch(self, entry, force_refresh=False):
        if entry.name == "high":
            self._validate_catalog_payload({"extensions": []}, entry.url)
        return {
            "schema_version": "1.0",
            "extensions": {"requested": {"version": "1.0.0"}},
        }

    monkeypatch.setattr(ExtensionCatalog, "_fetch_single_catalog", fetch)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert "Invalid catalog format" in check(_ref("extensions", "requested"))
    assert warnings == []


@pytest.mark.parametrize("kind", ["workflows", "steps"])
@pytest.mark.parametrize("payload", [b"{invalid", b"[]"])
def test_online_validation_rejects_malformed_workflow_catalogs(
    tmp_path, monkeypatch, kind, payload,
):
    import io

    from specify_cli.authentication import http
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        WorkflowCatalog,
        WorkflowCatalogEntry,
    )

    catalog, entry = (
        (WorkflowCatalog, WorkflowCatalogEntry)
        if kind == "workflows"
        else (StepCatalog, StepCatalogEntry)
    )
    url = "https://example.com/catalog.json"
    monkeypatch.setattr(
        catalog, "get_active_catalogs",
        lambda self: [entry(url, "trusted", 1, True)],
    )

    class Response(io.BytesIO):
        def geturl(self):
            return url

    monkeypatch.setattr(http, "open_url", lambda *args, **kwargs: Response(payload))
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert "Catalog lookup failed" in check(_ref(kind, "requested"))
    assert warnings == []


@pytest.mark.parametrize("kind", ["workflows", "steps"])
def test_online_validation_warns_for_unreachable_workflow_catalogs(
    tmp_path, monkeypatch, kind,
):
    from urllib.error import URLError

    from specify_cli.authentication import http
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        WorkflowCatalog,
        WorkflowCatalogEntry,
    )

    catalog, entry = (
        (WorkflowCatalog, WorkflowCatalogEntry)
        if kind == "workflows"
        else (StepCatalog, StepCatalogEntry)
    )
    monkeypatch.setattr(
        catalog, "get_active_catalogs",
        lambda self: [
            entry("https://example.com/catalog.json", "trusted", 1, True),
        ],
    )

    def unavailable(*args, **kwargs):
        raise URLError("timed out")

    monkeypatch.setattr(http, "open_url", unavailable)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(_ref(kind, "requested")) is None
    assert len(warnings) == 1
    assert "unreachable" in warnings[0]


@pytest.mark.parametrize("kind", ["workflows", "steps"])
def test_online_validation_rejects_unsafe_catalog_redirect(
    tmp_path, monkeypatch, kind,
):
    from specify_cli.authentication import http
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        WorkflowCatalog,
        WorkflowCatalogEntry,
    )

    catalog, entry = (
        (WorkflowCatalog, WorkflowCatalogEntry)
        if kind == "workflows"
        else (StepCatalog, StepCatalogEntry)
    )
    monkeypatch.setattr(
        catalog, "get_active_catalogs",
        lambda self: [
            entry("https://example.com/catalog.json", "trusted", 1, True),
        ],
    )

    def unsafe_redirect(*args, **kwargs):
        raise http.RedirectPolicyError("unsafe catalog redirect")

    monkeypatch.setattr(http, "open_url", unsafe_redirect)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert "unsafe catalog redirect" in check(_ref(kind, "requested"))
    assert warnings == []


@pytest.mark.parametrize("kind", ["extensions", "presets"])
@pytest.mark.parametrize("redirect", ["validator", "policy"])
def test_online_validation_does_not_skip_unsafe_higher_priority_catalog(
    tmp_path, monkeypatch, kind, redirect,
):
    import io
    import json

    from specify_cli.authentication.http import RedirectPolicyError
    from specify_cli.extensions import CatalogEntry, ExtensionCatalog
    from specify_cli.presets import PresetCatalog, PresetCatalogEntry

    catalog, entry = (
        (ExtensionCatalog, CatalogEntry)
        if kind == "extensions"
        else (PresetCatalog, PresetCatalogEntry)
    )
    sources = [
        entry("https://example.com/high.json", "high", 1, True),
        entry("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda self: sources)

    class Response(io.BytesIO):
        def __init__(self, url, payload):
            super().__init__(payload)
            self.url = url

        def geturl(self):
            return self.url

    def open_url(self, url, **kwargs):
        if url.endswith("high.json"):
            if redirect == "validator":
                kwargs["redirect_validator"](url, "http://evil.test/catalog.json")
                pytest.fail("unsafe redirect was accepted")
            raise RedirectPolicyError("unsafe catalog redirect")
        return Response(
            url,
            json.dumps({
                "schema_version": "1.0",
                kind: {
                    "requested": {
                        "version": "1.0.0",
                        "download_url": "https://example.com/archive.zip",
                        "sha256": "a" * 64,
                    }
                },
            }).encode(),
        )

    monkeypatch.setattr(catalog, "_open_url", open_url)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    problem = check(_ref(kind, "requested"))
    assert problem is not None and (
        "HTTPS" in problem or "unsafe catalog redirect" in problem
    )
    assert warnings == []


@pytest.mark.parametrize("legacy", [False, True])
def test_extension_catalog_invalid_utf8_is_validation_error(
    tmp_path, monkeypatch, legacy,
):
    import io

    from specify_cli.extensions import (
        CatalogEntry,
        ExtensionCatalog,
        ExtensionCatalogValidationError,
    )

    class Response(io.BytesIO):
        def geturl(self):
            return "https://example.com/catalog.json"

    catalog = ExtensionCatalog(tmp_path)
    entry = CatalogEntry("https://example.com/catalog.json", "bad", 1, True)
    monkeypatch.setattr(catalog, "get_catalog_url", lambda: entry.url)
    monkeypatch.setattr(catalog, "_open_url", lambda url, **kwargs: Response(b"\xff"))

    with pytest.raises(ExtensionCatalogValidationError, match="encoding"):
        if legacy:
            catalog.fetch_catalog(force_refresh=True)
        else:
            catalog._fetch_single_catalog(entry, force_refresh=True)


def test_online_validation_does_not_skip_invalid_utf8_extension_catalog(
    tmp_path, monkeypatch,
):
    import io
    import json

    from specify_cli.extensions import CatalogEntry, ExtensionCatalog

    sources = [
        CatalogEntry("https://example.com/high.json", "high", 1, True),
        CatalogEntry("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(ExtensionCatalog, "get_active_catalogs", lambda self: sources)

    class Response(io.BytesIO):
        def __init__(self, url, payload):
            super().__init__(payload)
            self.url = url

        def geturl(self):
            return self.url

    def open_url(self, url, **kwargs):
        payload = (
            b"\xff" if url.endswith("high.json")
            else json.dumps({
                "schema_version": "1.0",
                "extensions": {"requested": {"version": "1.0.0"}},
            }).encode()
        )
        return Response(url, payload)

    monkeypatch.setattr(ExtensionCatalog, "_open_url", open_url)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert "Invalid encoding" in check(_ref("extensions", "requested"))
    assert warnings == []


@pytest.mark.parametrize("kind", ["extensions", "presets"])
@pytest.mark.parametrize("legacy", [False, True])
def test_catalog_redirect_policy_is_validation_error(
    tmp_path, monkeypatch, kind, legacy,
):
    from specify_cli.authentication.http import RedirectPolicyError
    from specify_cli.extensions import (
        CatalogEntry,
        ExtensionCatalog,
        ExtensionCatalogValidationError,
    )
    from specify_cli.presets import (
        PresetCatalog,
        PresetCatalogEntry,
    )
    from specify_cli.presets._catalog import PresetCatalogValidationError

    catalog_type, entry_type, error_type = (
        (ExtensionCatalog, CatalogEntry, ExtensionCatalogValidationError)
        if kind == "extensions"
        else (PresetCatalog, PresetCatalogEntry, PresetCatalogValidationError)
    )
    catalog = catalog_type(tmp_path)
    url = "https://example.com/catalog.json"
    monkeypatch.setattr(catalog, "get_catalog_url", lambda: url)

    def unsafe_redirect(*args, **kwargs):
        raise RedirectPolicyError("unsafe catalog redirect")

    monkeypatch.setattr(catalog, "_open_url", unsafe_redirect)
    with pytest.raises(error_type, match="unsafe catalog redirect"):
        if legacy:
            catalog.fetch_catalog(force_refresh=True)
        else:
            catalog._fetch_single_catalog(
                entry_type(url, "trusted", 1, True), force_refresh=True
            )


@pytest.mark.parametrize("kind", ["workflows", "steps"])
@pytest.mark.parametrize("payload", [b"[]", b"{}", b'{"schema_version":"1.0"}'])
@pytest.mark.parametrize("cached", [False, True])
def test_online_validation_does_not_skip_malformed_higher_priority_catalog(
    tmp_path, monkeypatch, kind, payload, cached,
):
    import io
    import json

    from specify_cli.authentication import http
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        WorkflowCatalog,
        WorkflowCatalogEntry,
    )

    catalog, entry = (
        (WorkflowCatalog, WorkflowCatalogEntry)
        if kind == "workflows"
        else (StepCatalog, StepCatalogEntry)
    )
    sources = [
        entry("https://example.com/high.json", "high", 1, True),
        entry("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda self: sources)
    if cached:
        catalog_instance = catalog(tmp_path)
        cache_file, _ = catalog_instance._get_cache_paths(sources[0].url)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(payload)
        monkeypatch.setattr(
            catalog, "_is_url_cache_valid",
            lambda self, url: url == sources[0].url,
        )

    class Response(io.BytesIO):
        def __init__(self, url, payload):
            super().__init__(payload)
            self.url = url

        def geturl(self):
            return self.url

    def open_url(url, **kwargs):
        response_payload = (
            payload if url.endswith("high.json")
            else json.dumps({
                kind: {"requested": {"version": "1.0.0"}},
            }).encode()
        )
        return Response(url, response_payload)

    monkeypatch.setattr(http, "open_url", open_url)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert "Catalog lookup failed" in check(ComponentRef(kind=kind, id="requested"))
    assert warnings == []


@pytest.mark.parametrize("kind", ["workflows", "steps"])
@pytest.mark.parametrize("empty", [{}, []])
def test_valid_empty_higher_priority_catalog_allows_lower_source(
    tmp_path, monkeypatch, kind, empty,
):
    import io
    import json

    from specify_cli.authentication import http
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        WorkflowCatalog,
        WorkflowCatalogEntry,
    )

    catalog, entry = (
        (WorkflowCatalog, WorkflowCatalogEntry)
        if kind == "workflows"
        else (StepCatalog, StepCatalogEntry)
    )
    sources = [
        entry("https://example.com/high.json", "high", 1, True),
        entry("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda self: sources)

    class Response(io.BytesIO):
        def __init__(self, url, payload):
            super().__init__(payload)
            self.url = url

        def geturl(self):
            return self.url

    def open_url(url, **kwargs):
        entries = empty if url.endswith("high.json") else {
            "requested": {"version": "1.0.0"}
        }
        return Response(url, json.dumps({kind: entries}).encode())

    monkeypatch.setattr(http, "open_url", open_url)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(ComponentRef(kind=kind, id="requested")) is None
    assert warnings == []


@pytest.mark.parametrize("kind", ["workflows", "steps"])
@pytest.mark.parametrize("source", ["network", "fresh-cache", "stale-cache"])
def test_deeply_nested_catalog_is_handled_as_malformed_data(
    tmp_path, monkeypatch, kind, source,
):
    import io
    import json
    from urllib.error import URLError

    from specify_cli.authentication import http
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        StepCatalogFetchError,
        StepCatalogValidationError,
        WorkflowCatalog,
        WorkflowCatalogEntry,
        WorkflowCatalogFetchError,
        WorkflowCatalogValidationError,
    )

    catalog_type, entry_type, validation_error, fetch_error = {
        "workflows": (
            WorkflowCatalog, WorkflowCatalogEntry,
            WorkflowCatalogValidationError, WorkflowCatalogFetchError,
        ),
        "steps": (
            StepCatalog, StepCatalogEntry,
            StepCatalogValidationError, StepCatalogFetchError,
        ),
    }[kind]
    catalog = catalog_type(tmp_path)
    entry = entry_type("https://example.com/catalog.json", "trusted", 1, True)
    nested = (
        b'{"' + kind.encode() + b'":{},"nested":'
        + b"[" * 10000 + b"0" + b"]" * 10000 + b"}"
    )
    valid = {"schema_version": "1.0", kind: {"requested": {"version": "1.0.0"}}}

    class Response(io.BytesIO):
        def geturl(self):
            return entry.url

    if source != "network":
        cache_file, _ = catalog._get_cache_paths(entry.url)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(nested)
        monkeypatch.setattr(
            catalog, "_is_url_cache_valid", lambda _url: source == "fresh-cache"
        )

        def read_nested_cache(*args, **kwargs):
            raise RecursionError("catalog nesting limit exceeded")

        monkeypatch.setattr(json, "load", read_nested_cache)
    else:
        original_loads = json.loads

        def decode_nested_catalog(raw, *args, **kwargs):
            if raw == nested.decode("utf-8"):
                raise RecursionError("catalog nesting limit exceeded")
            return original_loads(raw, *args, **kwargs)

        monkeypatch.setattr(json, "loads", decode_nested_catalog)

    def open_url(*args, **kwargs):
        if source == "stale-cache":
            raise URLError("connection failed")
        payload = nested if source == "network" else json.dumps(valid).encode()
        return Response(payload)

    monkeypatch.setattr(http, "open_url", open_url)
    if source == "network":
        with pytest.raises(validation_error, match="Invalid.*catalog"):
            catalog._fetch_single_catalog(entry, force_refresh=True)
    elif source == "stale-cache":
        with pytest.raises(fetch_error, match="Failed to fetch catalog"):
            catalog._fetch_single_catalog(entry)
    else:
        assert catalog._fetch_single_catalog(entry) == valid


@pytest.mark.parametrize("kind", ["workflows", "steps"])
def test_deep_catalog_does_not_escape_during_cache_write(
    tmp_path, monkeypatch, kind,
):
    import io

    from specify_cli.authentication import http
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        StepCatalogValidationError,
        WorkflowCatalog,
        WorkflowCatalogEntry,
        WorkflowCatalogValidationError,
    )

    catalog_type, entry_type, error_type = {
        "workflows": (
            WorkflowCatalog, WorkflowCatalogEntry, WorkflowCatalogValidationError,
        ),
        "steps": (StepCatalog, StepCatalogEntry, StepCatalogValidationError),
    }[kind]
    catalog = catalog_type(tmp_path)
    entry = entry_type("https://example.com/catalog.json", "trusted", 1, True)
    payload = (
        b'{"' + kind.encode() + b'":{},"nested":'
        + b"[" * 1200 + b"0" + b"]" * 1200 + b"}"
    )

    class Response(io.BytesIO):
        def geturl(self):
            return entry.url

    monkeypatch.setattr(
        http, "open_url", lambda *args, **kwargs: Response(payload)
    )
    with pytest.raises(error_type, match="Invalid.*catalog"):
        catalog._fetch_single_catalog(entry, force_refresh=True)


@pytest.mark.parametrize("kind", ["extensions", "workflows", "steps"])
def test_targeted_lookup_stops_before_lower_priority_catalog(
    tmp_path, monkeypatch, kind,
):
    from specify_cli.extensions import CatalogEntry, ExtensionCatalog
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        WorkflowCatalog,
        WorkflowCatalogEntry,
    )

    catalog, entry, key = {
        "extensions": (ExtensionCatalog, CatalogEntry, "extensions"),
        "workflows": (WorkflowCatalog, WorkflowCatalogEntry, "workflows"),
        "steps": (StepCatalog, StepCatalogEntry, "steps"),
    }[kind]
    sources = [
        entry("https://example.com/high.json", "high", 1, True),
        entry("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda self: sources)

    def fetch(self, source, force_refresh=False):
        if source.name != "high":
            pytest.fail("lower-priority catalog was fetched after finding the ID")
        return {
            "schema_version": "1.0",
            key: {"requested": {"version": "1.0.0"}},
        }

    monkeypatch.setattr(catalog, "_fetch_single_catalog", fetch)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(ComponentRef(kind=kind, id="requested", source="high")) is None
    assert warnings == []


@pytest.mark.parametrize("kind", ["extensions", "presets", "workflows", "steps"])
@pytest.mark.parametrize("duplicate_name", [False, True])
def test_explicit_source_requires_unique_catalog_name(
    tmp_path, monkeypatch, kind, duplicate_name,
):
    from specify_cli.bundles import BundlerError
    from specify_cli.bundles.adapters import DefaultPrimitiveInstaller
    from specify_cli.extensions import ExtensionCatalog
    from specify_cli.presets import PresetCatalog
    from specify_cli.workflows.catalog import (
        StepCatalog,
        WorkflowCatalog,
    )

    catalog_type, lookup, env_key = {
        "extensions": (ExtensionCatalog, "get_extension_info", "SPECKIT_CATALOG_URL"),
        "presets": (PresetCatalog, "get_pack_info", "SPECKIT_PRESET_CATALOG_URL"),
        "workflows": (
            WorkflowCatalog, "get_workflow_info", "SPECKIT_WORKFLOW_CATALOG_URL"
        ),
        "steps": (StepCatalog, "get_step_info", "SPECKIT_STEP_CATALOG_URL"),
    }[kind]
    monkeypatch.delenv(env_key, raising=False)
    config = tmp_path / ".specify" / f"{kind[:-1]}-catalogs.yml"
    config.parent.mkdir()
    config.write_text(
        yaml.safe_dump({"catalogs": [
            {
                "url": "https://example.com/expected.json",
                "name": "trusted",
                "priority": 1,
                "install_allowed": True,
            },
            {
                "url": "https://example.com/other.json",
                "name": "trusted" if duplicate_name else "other",
                "priority": 2,
                "install_allowed": True,
            },
        ]}),
        encoding="utf-8",
    )
    assert [entry.name for entry in catalog_type(tmp_path).get_active_catalogs()] == [
        "trusted",
        "trusted" if duplicate_name else "other",
    ]
    monkeypatch.setattr(
        catalog_type,
        lookup,
        lambda self, component_id, version=None: {
            "id": component_id,
            "version": version or "1.0.0",
            "_catalog_name": "trusted",
            "_install_allowed": True,
        },
    )
    ref = ComponentRef(kind=kind, id="requested", source="trusted")
    warnings: list[str] = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)
    installer = DefaultPrimitiveInstaller()

    if duplicate_name:
        assert "ambiguous" in check(ref).lower()
        with pytest.raises(BundlerError, match="ambiguous"):
            installer.validate_source(tmp_path, ref)
    else:
        assert check(ref) is None
        installer.validate_source(tmp_path, ref)
    assert warnings == []
