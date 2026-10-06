"""Unit tests for the bundle reference checker (T047 / FR-005 / SC-007).

Resolution is offline-first: bundled and installed components resolve without a
network; unknown ids fail online and downgrade to warnings offline.
"""
from __future__ import annotations

from pathlib import Path

import pytest

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


def test_wrong_bundled_pin_does_not_resolve_locally(tmp_path):
    root = make_project(tmp_path)
    warnings = []
    check = make_reference_checker(root, allow_network=False, warnings=warnings)

    assert check(_ref("extensions", "agent-context", "999.0.0")) is None
    assert any("agent-context" in message for message in warnings)


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
def test_online_validation_does_not_skip_malformed_higher_priority_catalog(
    tmp_path, monkeypatch, kind,
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
        payload = (
            b"[]" if url.endswith("high.json")
            else json.dumps({
                kind: {"requested": {"version": "1.0.0"}},
            }).encode()
        )
        return Response(url, payload)

    monkeypatch.setattr(http, "open_url", open_url)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert "Catalog lookup failed" in check(ComponentRef(kind=kind, id="requested"))
    assert warnings == []


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
