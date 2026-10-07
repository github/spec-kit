"""Unit tests for the bundle reference checker (T047 / FR-005 / SC-007).

Resolution is offline-first: bundled and installed components resolve without a
network; unknown ids fail online and downgrade to warnings offline.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from urllib.error import URLError

import pytest
import yaml

from specify_cli.bundles.manifest import ComponentRef
from specify_cli.bundles.references import make_reference_checker
from tests.specify_cli.bundles.helpers import bundled_extension_version, make_project


def _ref(kind: str, id_: str, version: str | None = "1.0.0") -> ComponentRef:
    return ComponentRef(kind=kind, id=id_, version=version)


def _mock_catalog(monkeypatch, catalog_type, kind, component_id, record, *, name="trusted"):
    source = SimpleNamespace(
        name=name, url="https://example.com/catalog.json", install_allowed=True
    )
    monkeypatch.setattr(catalog_type, "get_active_catalogs", lambda self: [source])
    monkeypatch.setattr(
        catalog_type,
        "_fetch_single_catalog",
        lambda self, entry, force_refresh=False: {
            "schema_version": "1.0", kind: {component_id: record}
        },
    )


def _installable_current(kind: str) -> dict:
    if kind == "extensions":
        return {
            "version": "1.0.0",
            "download_url": "https://example.com/release.zip",
            "sha256": "a" * 64,
        }
    return {
        "version": "1.0.0",
        "url": f"https://example.com/{'workflow.yml' if kind == 'workflows' else 'step.yml'}",
        "sha256": (
            "a" * 64 if kind == "workflows"
            else {"step.yml": "a" * 64, "__init__.py": "b" * 64}
        ),
    }


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


def test_unknown_step_type_still_errors_online(tmp_path: Path, monkeypatch):
    """The guard must not make every step id resolve."""
    from specify_cli.workflows.catalog import StepCatalog

    _mock_catalog(monkeypatch, StepCatalog, "steps", "other-step", {"version": "1.0.0"})
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
    _mock_catalog(
        monkeypatch, ExtensionCatalog, "extensions",
        "agent-context", {
            "version": "999.0.0",
            "download_url": "https://example.com/release.zip",
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
    _mock_catalog(
        monkeypatch, PresetCatalog, "presets", "requested", {"version": "2.0.0"}
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


@pytest.mark.parametrize("kind", ["extensions", "presets"])
def test_bundle_http_protocol_error_is_unreachable_catalog(
    tmp_path, monkeypatch, kind,
):
    from http.client import BadStatusLine

    from specify_cli.extensions import ExtensionCatalog
    from specify_cli.presets import PresetCatalog

    catalog_type = ExtensionCatalog if kind == "extensions" else PresetCatalog
    _mock_catalog(monkeypatch, catalog_type, kind, "requested", {})

    def bad_status(self, source, force_refresh=False):
        raise BadStatusLine("bad response")

    monkeypatch.setattr(catalog_type, "_fetch_single_catalog", bad_status)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)
    assert check(_ref(kind, "requested")) is None
    assert len(warnings) == 1 and "unreachable" in warnings[0]


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
    fetches = []
    _mock_catalog(
        monkeypatch, WorkflowCatalog, "workflows", "catalog-workflow",
        {
            "version": "2.0.0",
            "releases": {
                "1.0.0": {
                    "url": "https://example.com/old.yml",
                    "sha256": "a" * 64,
                }
            },
        },
        name="winning",
    )
    original_fetch = WorkflowCatalog._fetch_single_catalog

    def fetch(self, source, force_refresh=False):
        fetches.append(source.name)
        return original_fetch(self, source, force_refresh)

    monkeypatch.setattr(WorkflowCatalog, "_fetch_single_catalog", fetch)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)
    requested = ComponentRef(
        kind="workflows", id="catalog-workflow", version="1.0.0", source="winning"
    )

    assert check(requested) is None
    assert fetches == ["winning"]
    assert check(ComponentRef(kind="workflows", id=requested.id, version="3.0.0"))
    assert check(ComponentRef(
        kind="workflows", id=requested.id, version="1.0.0", source="lower"
    ))
    assert warnings == []


def test_online_validation_rejects_discovery_only_exact_release(tmp_path, monkeypatch):
    from specify_cli.workflows.catalog import StepCatalog, StepCatalogEntry

    source = StepCatalogEntry("https://example.com/catalog.json", "winning", 1, False)
    monkeypatch.setattr(StepCatalog, "get_active_catalogs", lambda self: [source])
    monkeypatch.setattr(
        StepCatalog, "_fetch_single_catalog",
        lambda self, entry, force_refresh=False: {
            "steps": {"catalog-step": {"version": "2.0.0"}}
        },
    )
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(_ref("steps", "catalog-step", "1.0.0"))
    assert warnings == []


def test_online_validation_reports_invalid_release_metadata(tmp_path, monkeypatch):
    from specify_cli.workflows.catalog import StepCatalog

    _mock_catalog(
        monkeypatch, StepCatalog, "steps", "invalid-release",
        {
            "version": "2.0.0",
            "releases": {
                "1.0.0": {"step_yml_url": "https://example.com/step.yml"}
            },
        },
    )
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert "SHA-256" in check(_ref("steps", "invalid-release"))
    assert warnings == []


@pytest.mark.parametrize(
    ("kind", "field", "bad_value", "message"),
    [
        ("workflows", "url", None, "install URL"),
        ("workflows", "url", 42, "install URL"),
        ("workflows", "url", "http://example.com/workflow.yml", "install URL"),
        ("workflows", "sha256", "not-a-digest", "SHA-256"),
        ("steps", "url", None, "step.yml URL"),
        ("steps", "url", 42, "step.yml URL"),
        ("steps", "url", "http://example.com/step.yml", "step.yml URL"),
        ("steps", "url", "https://example.com/other.yml", "__init__.py URL"),
        ("steps", "init_url", "http://example.com/__init__.py", "__init__.py URL"),
        ("steps", "sha256", {"step.yml": "a" * 64}, "SHA-256"),
        ("steps", "extra_files", {"helper.py": "http://example.com/helper.py"}, "extra file URL"),
    ],
)
def test_online_validation_rejects_malformed_pinned_current_release(
    tmp_path, monkeypatch, kind, field, bad_value, message,
):
    from specify_cli.workflows.catalog import StepCatalog, WorkflowCatalog

    catalog = WorkflowCatalog if kind == "workflows" else StepCatalog
    record = _installable_current(kind)
    record[field] = bad_value
    if field == "extra_files":
        record["sha256"]["helper.py"] = "c" * 64
    _mock_catalog(monkeypatch, catalog, kind, "requested", record)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    problem = check(_ref(kind, "requested"))
    assert problem is not None and message in problem
    assert warnings == []


@pytest.mark.parametrize("kind", ["workflows", "steps"])
def test_online_validation_accepts_installable_pinned_current_release(
    tmp_path, monkeypatch, kind,
):
    from specify_cli.workflows.catalog import StepCatalog, WorkflowCatalog

    catalog = WorkflowCatalog if kind == "workflows" else StepCatalog
    record = _installable_current(kind)
    _mock_catalog(monkeypatch, catalog, kind, "requested", record)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(_ref(kind, "requested")) is None
    assert warnings == []


def test_online_validation_warns_when_catalogs_are_unreachable(tmp_path, monkeypatch):
    from specify_cli.workflows.catalog import WorkflowCatalog

    _mock_catalog(monkeypatch, WorkflowCatalog, "workflows", "unreachable", {})

    def unavailable(self, source, force_refresh=False):
        raise URLError("timed out")

    monkeypatch.setattr(WorkflowCatalog, "_fetch_single_catalog", unavailable)
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
    from specify_cli.extensions import CatalogEntry, ExtensionCatalog
    from specify_cli.presets import PresetCatalog, PresetCatalogEntry
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        WorkflowCatalog,
        WorkflowCatalogEntry,
    )

    catalog, entry_type = {
        "extensions": (ExtensionCatalog, CatalogEntry),
        "presets": (PresetCatalog, PresetCatalogEntry),
        "workflows": (WorkflowCatalog, WorkflowCatalogEntry),
        "steps": (StepCatalog, StepCatalogEntry),
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
            raise URLError("catalog timed out")
        contents = {"requested": _installable_current(kind)} if has_match else {}
        return {kind: contents}

    monkeypatch.setattr(catalog, "_fetch_single_catalog", fetch)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    problem = check(_ref(kind, "requested"))
    if unreachable == "high":
        assert problem is None
        assert len(warnings) == 1
        assert "unreachable" in warnings[0]
        assert visited == ["high"]
    elif has_match and unreachable == "low":
        assert problem is None
        assert warnings == []
        assert visited == ["high"]
    elif unreachable is not None:
        assert problem is None
        assert len(warnings) == 1
        assert "unreachable" in warnings[0]
        assert visited == ["high", "low"]
    elif has_match:
        assert problem is None
        assert warnings == []
        assert visited == ["high"]
    else:
        assert problem is not None and "not available" in problem
        assert warnings == []
        assert visited == ["high", "low"]


@pytest.mark.parametrize("kind", ["extensions", "presets"])
def test_online_validation_warns_for_unreachable_component_catalog(
    tmp_path, monkeypatch, kind,
):
    from specify_cli.extensions import ExtensionCatalog
    from specify_cli.presets import PresetCatalog

    catalog = ExtensionCatalog if kind == "extensions" else PresetCatalog
    _mock_catalog(monkeypatch, catalog, kind, "unreachable-component", {})

    def unavailable(self, source, force_refresh=False):
        raise URLError("timed out")

    monkeypatch.setattr(catalog, "_fetch_single_catalog", unavailable)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(_ref(kind, "unreachable-component")) is None
    assert len(warnings) == 1
    assert "unreachable" in warnings[0]


@pytest.mark.parametrize("kind", ["extensions", "presets"])
def test_online_validation_rejects_malformed_component_release(
    tmp_path, monkeypatch, kind,
):
    from specify_cli.extensions import ExtensionCatalog
    from specify_cli.presets import PresetCatalog

    catalog = ExtensionCatalog if kind == "extensions" else PresetCatalog
    _mock_catalog(
        monkeypatch, catalog, kind, "invalid-component",
        {
            "version": "2.0.0",
            "releases": {
                "1.0.0": {"download_url": "https://example.com/release.zip"}
            },
        },
    )
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert "SHA-256" in check(_ref(kind, "invalid-component"))
    assert warnings == []


@pytest.mark.parametrize("historical", [False, True])
@pytest.mark.parametrize(
    "url",
    ["http://example.com/release.zip", "https://[::1", "https:///release.zip", 42],
)
def test_online_validation_rejects_invalid_pinned_extension_url(
    tmp_path, monkeypatch, historical, url,
):
    from specify_cli.extensions import ExtensionCatalog

    record = {"download_url": url, "sha256": "a" * 64}
    current = {"version": "2.0.0", **record}
    if historical:
        current["releases"] = {"1.0.0": record}
    _mock_catalog(
        monkeypatch, ExtensionCatalog, "extensions", "invalid-extension", current
    )
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    problem = check(_ref(
        "extensions", "invalid-extension", "1.0.0" if historical else "2.0.0"
    ))
    assert problem is not None and ("URL" in problem or "download_url" in problem)
    assert warnings == []


@pytest.mark.parametrize("historical", [False, True])
def test_online_validation_accepts_safe_pinned_extension_url(
    tmp_path, monkeypatch, historical,
):
    from specify_cli.extensions import ExtensionCatalog

    record = {"download_url": "https://example.com/release.zip", "sha256": "a" * 64}
    current = {"version": "2.0.0", **record}
    if historical:
        current["releases"] = {"1.0.0": record}
    _mock_catalog(monkeypatch, ExtensionCatalog, "extensions", "valid-extension", current)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(_ref(
        "extensions", "valid-extension", "1.0.0" if historical else "2.0.0"
    )) is None
    assert warnings == []


@pytest.mark.parametrize("kind", ["extensions", "presets"])
def test_online_validation_accepts_unversioned_legacy_component(
    tmp_path, monkeypatch, kind,
):
    from specify_cli.extensions import ExtensionCatalog
    from specify_cli.presets import PresetCatalog

    catalog = ExtensionCatalog if kind == "extensions" else PresetCatalog
    _mock_catalog(monkeypatch, catalog, kind, "legacy-component", {})
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    assert check(_ref(kind, "legacy-component", "1.0.0")) is None
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


@pytest.mark.parametrize("kind", ["extensions", "presets"])
def test_bundle_invalid_utf8_catalog_is_validation_error(
    tmp_path, monkeypatch, kind,
):
    import io

    from specify_cli.extensions import ExtensionCatalog
    from specify_cli.presets import PresetCatalog

    class Response(io.BytesIO):
        def geturl(self):
            return "https://example.com/catalog.json"

    catalog_type = ExtensionCatalog if kind == "extensions" else PresetCatalog
    original_fetch = catalog_type._fetch_single_catalog
    _mock_catalog(monkeypatch, catalog_type, kind, "requested", {})
    monkeypatch.setattr(catalog_type, "_open_url", lambda self, url, **kw: Response(b"\xff"))
    monkeypatch.setattr(catalog_type, "_fetch_single_catalog", original_fetch)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)
    assert "decode" in check(_ref(kind, "requested"))
    assert warnings == []


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

    assert "decode" in check(_ref("extensions", "requested"))
    assert warnings == []


@pytest.mark.parametrize("kind", ["extensions", "presets"])
@pytest.mark.parametrize("status", [404, 503])
def test_bundle_catalog_http_errors_preserve_failure_type(
    tmp_path, monkeypatch, kind, status,
):
    from urllib.error import HTTPError

    from specify_cli.extensions import ExtensionCatalog
    from specify_cli.presets import PresetCatalog

    catalog_type = ExtensionCatalog if kind == "extensions" else PresetCatalog
    _mock_catalog(monkeypatch, catalog_type, kind, "requested", {})

    def failed(self, source, force_refresh=False):
        raise HTTPError(source.url, status, "catalog failure", {}, None)

    monkeypatch.setattr(catalog_type, "_fetch_single_catalog", failed)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)
    problem = check(_ref(kind, "requested"))
    if status == 503:
        assert problem is None
        assert len(warnings) == 1 and "unreachable" in warnings[0]
    else:
        assert problem is not None and "404" in problem
        assert warnings == []


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
def test_bundle_catalog_handles_recursion_without_fallback(
    tmp_path, monkeypatch, kind, source,
):
    from specify_cli.workflows.catalog import (
        StepCatalog,
        WorkflowCatalog,
    )

    catalog_type = WorkflowCatalog if kind == "workflows" else StepCatalog
    _mock_catalog(monkeypatch, catalog_type, kind, "requested", _installable_current(kind))

    def fetch(self, entry, force_refresh=False):
        if source == "fresh-cache":
            return {kind: {"requested": _installable_current(kind)}}
        if source == "stale-cache":
            raise URLError("connection failed")
        raise RecursionError("catalog nesting limit exceeded")

    monkeypatch.setattr(catalog_type, "_fetch_single_catalog", fetch)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)
    problem = check(_ref(kind, "requested"))
    if source == "network":
        assert problem is not None and "nesting limit exceeded" in problem
        assert warnings == []
    elif source == "stale-cache":
        assert problem is None
        assert len(warnings) == 1 and "unreachable" in warnings[0]
    else:
        assert problem is None
        assert warnings == []


@pytest.mark.parametrize("kind", ["workflows", "steps"])
def test_bundle_catalog_handles_cache_write_recursion(tmp_path, monkeypatch, kind):
    from specify_cli.workflows.catalog import StepCatalog, WorkflowCatalog

    catalog_type = WorkflowCatalog if kind == "workflows" else StepCatalog
    _mock_catalog(monkeypatch, catalog_type, kind, "requested", {"version": "1.0.0"})

    def fetch(self, entry, force_refresh=False):
        raise RecursionError("cache write nesting limit exceeded")

    monkeypatch.setattr(catalog_type, "_fetch_single_catalog", fetch)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)
    assert "cache write nesting limit exceeded" in check(_ref(kind, "requested"))
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


@pytest.mark.parametrize("kind", ["extensions", "presets", "workflows", "steps"])
@pytest.mark.parametrize("malformed", [None, 42, "invalid", True])
def test_bundle_rejects_malformed_higher_source_before_lower_match(
    tmp_path, monkeypatch, kind, malformed,
):
    from specify_cli.extensions import CatalogEntry, ExtensionCatalog
    from specify_cli.presets import PresetCatalog, PresetCatalogEntry
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        WorkflowCatalog,
        WorkflowCatalogEntry,
    )

    catalog, entry_type = {
        "extensions": (ExtensionCatalog, CatalogEntry),
        "presets": (PresetCatalog, PresetCatalogEntry),
        "workflows": (WorkflowCatalog, WorkflowCatalogEntry),
        "steps": (StepCatalog, StepCatalogEntry),
    }[kind]
    sources = [
        entry_type("https://example.com/high.json", "high", 1, True),
        entry_type("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda self: sources)
    fetched = []

    def fetch(self, source, force_refresh=False):
        fetched.append(source.name)
        if source.name == "high":
            return {"schema_version": "1.0", kind: malformed}
        return {"schema_version": "1.0", kind: {"requested": {"version": "1.0.0"}}}

    monkeypatch.setattr(catalog, "_fetch_single_catalog", fetch)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)

    problem = check(_ref(kind, "requested"))
    assert problem is not None and "malformed" in problem
    assert fetched == ["high"]
    assert warnings == []


@pytest.mark.parametrize("kind", ["workflows", "steps"])
@pytest.mark.parametrize("duplicate_id", ["requested", "other"])
def test_bundle_rejects_duplicate_list_ids_before_lower_source(
    tmp_path, monkeypatch, kind, duplicate_id,
):
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        WorkflowCatalog,
        WorkflowCatalogEntry,
    )

    catalog, entry_type = (
        (WorkflowCatalog, WorkflowCatalogEntry)
        if kind == "workflows" else (StepCatalog, StepCatalogEntry)
    )
    sources = [
        entry_type("https://example.com/high.json", "high", 1, True),
        entry_type("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda self: sources)
    visited = []

    def fetch(self, source, force_refresh=False):
        visited.append(source.name)
        if source.name == "low":
            pytest.fail("duplicate IDs in the higher source were ignored")
        return {kind: [
            {"id": "requested", "version": "1.0.0"},
            {"id": duplicate_id, "version": "2.0.0"},
            {"id": duplicate_id, "version": "3.0.0"},
        ]}

    monkeypatch.setattr(catalog, "_fetch_single_catalog", fetch)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)
    assert f"Duplicate {kind[:-1]} ID '{duplicate_id}'" in check(_ref(kind, "requested"))
    assert visited == ["high"]
    assert warnings == []


@pytest.mark.parametrize("kind", ["workflows", "steps"])
@pytest.mark.parametrize("invalid_id", [{"bad": "id"}, ["bad"], 42, True, None, ""])
def test_bundle_rejects_invalid_list_ids(
    tmp_path, monkeypatch, kind, invalid_id,
):
    from specify_cli.workflows.catalog import StepCatalog, WorkflowCatalog

    catalog = WorkflowCatalog if kind == "workflows" else StepCatalog
    _mock_catalog(monkeypatch, catalog, kind, "requested", {})
    monkeypatch.setattr(
        catalog, "_fetch_single_catalog",
        lambda self, source, force_refresh=False: {
            kind: [
                {"id": "requested", "version": "1.0.0"},
                {"id": invalid_id, "version": "2.0.0"},
            ]
        },
    )
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)
    assert f"Invalid {kind[:-1]} ID" in check(_ref(kind, "requested"))
    assert warnings == []


@pytest.mark.parametrize("kind", ["workflows", "steps"])
def test_bundle_accepts_list_id_from_first_source(tmp_path, monkeypatch, kind):
    from specify_cli.workflows.catalog import (
        StepCatalog,
        StepCatalogEntry,
        WorkflowCatalog,
        WorkflowCatalogEntry,
    )

    catalog, entry_type = (
        (WorkflowCatalog, WorkflowCatalogEntry)
        if kind == "workflows" else (StepCatalog, StepCatalogEntry)
    )
    sources = [
        entry_type("https://example.com/high.json", "high", 1, True),
        entry_type("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda self: sources)
    visited = []

    def fetch(self, source, force_refresh=False):
        visited.append(source.name)
        return {kind: [{"id": "requested", "version": source.name}]}

    monkeypatch.setattr(catalog, "_fetch_single_catalog", fetch)
    warnings = []
    check = make_reference_checker(tmp_path, allow_network=True, warnings=warnings)
    assert check(ComponentRef(kind=kind, id="requested")) is None
    assert visited == ["high"]
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

    catalog_type, env_key = {
        "extensions": (ExtensionCatalog, "SPECKIT_CATALOG_URL"),
        "presets": (PresetCatalog, "SPECKIT_PRESET_CATALOG_URL"),
        "workflows": (
            WorkflowCatalog, "SPECKIT_WORKFLOW_CATALOG_URL"
        ),
        "steps": (StepCatalog, "SPECKIT_STEP_CATALOG_URL"),
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
        "_fetch_single_catalog",
        lambda self, source, force_refresh=False: {
            "schema_version": "1.0",
            kind: {"requested": {"version": "1.0.0"}},
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
