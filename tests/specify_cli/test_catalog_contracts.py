"""Cross-primitive characterization tests for remote catalog contracts."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from specify_cli.extensions import ExtensionCatalog, ValidationError
from specify_cli.integrations import (
    IntegrationCatalog,
    IntegrationValidationError,
)
from specify_cli.presets import PresetCatalog, PresetValidationError
from specify_cli.workflows.catalog import (
    WorkflowCatalog,
    WorkflowValidationError,
)
from specify_cli.workflows.step.catalog import StepCatalog, StepValidationError


@dataclass(frozen=True)
class RemoteCatalogCase:
    name: str
    catalog_type: type
    config_filename: str
    env_var: str
    error_type: type[Exception]
    empty_project_fails_closed: bool
    whitespace_environment_fails_closed: bool


REMOTE_CATALOGS = (
    RemoteCatalogCase(
        "extension",
        ExtensionCatalog,
        "extension-catalogs.yml",
        "SPECKIT_CATALOG_URL",
        ValidationError,
        True,
        True,
    ),
    RemoteCatalogCase(
        "preset",
        PresetCatalog,
        "preset-catalogs.yml",
        "SPECKIT_PRESET_CATALOG_URL",
        PresetValidationError,
        False,
        True,
    ),
    RemoteCatalogCase(
        "integration",
        IntegrationCatalog,
        "integration-catalogs.yml",
        "SPECKIT_INTEGRATION_CATALOG_URL",
        IntegrationValidationError,
        True,
        False,
    ),
    RemoteCatalogCase(
        "workflow",
        WorkflowCatalog,
        "workflow-catalogs.yml",
        "SPECKIT_WORKFLOW_CATALOG_URL",
        WorkflowValidationError,
        False,
        False,
    ),
    RemoteCatalogCase(
        "workflow-step",
        StepCatalog,
        "step-catalogs.yml",
        "SPECKIT_STEP_CATALOG_URL",
        StepValidationError,
        False,
        False,
    ),
)


def _write_remote_config(root: Path, filename: str, name: str) -> None:
    config_dir = root / ".specify"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / filename).write_text(
        yaml.safe_dump(
            {
                "catalogs": [
                    {
                        "name": name,
                        "url": f"https://{name}.example.com/catalog.json",
                        "priority": 7,
                        "install_allowed": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize("case", REMOTE_CATALOGS, ids=lambda case: case.name)
def test_remote_catalog_default_stack_preserves_install_policy(
    case: RemoteCatalogCase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.delenv(case.env_var, raising=False)

    sources = case.catalog_type(project).get_active_catalogs()

    assert [source.name for source in sources] == ["default", "community"]
    assert [source.install_allowed for source in sources] == [True, False]
    assert [source.priority for source in sources] == [1, 2]


@pytest.mark.parametrize("case", REMOTE_CATALOGS, ids=lambda case: case.name)
def test_remote_catalog_resolution_replaces_lower_source_layers(
    case: RemoteCatalogCase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    _write_remote_config(home, case.config_filename, "user")
    _write_remote_config(project, case.config_filename, "project")
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.delenv(case.env_var, raising=False)
    catalog = case.catalog_type(project)

    project_sources = catalog.get_active_catalogs()

    assert [source.name for source in project_sources] == ["project"]

    monkeypatch.setenv(case.env_var, "https://env.example.com/catalog.json")
    environment_sources = catalog.get_active_catalogs()

    assert len(environment_sources) == 1
    assert environment_sources[0].url == "https://env.example.com/catalog.json"
    assert environment_sources[0].install_allowed is True


@pytest.mark.parametrize("case", REMOTE_CATALOGS, ids=lambda case: case.name)
def test_remote_catalog_whitespace_environment_keeps_historical_semantics(
    case: RemoteCatalogCase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    _write_remote_config(project, case.config_filename, "project")
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setenv(case.env_var, "   ")
    catalog = case.catalog_type(project)

    if case.whitespace_environment_fails_closed:
        with pytest.raises(case.error_type):
            catalog.get_active_catalogs()
    else:
        assert [source.name for source in catalog.get_active_catalogs()] == ["project"]


@pytest.mark.parametrize("case", REMOTE_CATALOGS, ids=lambda case: case.name)
def test_remote_catalog_empty_project_config_keeps_historical_semantics(
    case: RemoteCatalogCase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    home = tmp_path / "home"
    (project / ".specify").mkdir(parents=True)
    home.mkdir()
    _write_remote_config(home, case.config_filename, "user")
    (project / ".specify" / case.config_filename).write_text("", encoding="utf-8")
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.delenv(case.env_var, raising=False)
    catalog = case.catalog_type(project)

    if case.empty_project_fails_closed:
        with pytest.raises(case.error_type):
            catalog.get_active_catalogs()
    else:
        assert [source.name for source in catalog.get_active_catalogs()] == ["user"]


@pytest.mark.parametrize("case", REMOTE_CATALOGS, ids=lambda case: case.name)
def test_remote_catalog_malformed_config_fails_instead_of_falling_back(
    case: RemoteCatalogCase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    home = tmp_path / "home"
    (project / ".specify").mkdir(parents=True)
    home.mkdir()
    _write_remote_config(home, case.config_filename, "user")
    (project / ".specify" / case.config_filename).write_text(
        "catalogs: false\n", encoding="utf-8"
    )
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.delenv(case.env_var, raising=False)

    with pytest.raises(case.error_type):
        case.catalog_type(project).get_active_catalogs()


@pytest.mark.parametrize("case", REMOTE_CATALOGS, ids=lambda case: case.name)
def test_remote_catalog_fractional_priority_is_truncated(
    case: RemoteCatalogCase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    home = tmp_path / "home"
    (project / ".specify").mkdir(parents=True)
    home.mkdir()
    (project / ".specify" / case.config_filename).write_text(
        yaml.safe_dump(
            {
                "catalogs": [
                    {
                        "name": "fractional",
                        "url": "https://fractional.example.com/catalog.json",
                        "priority": 1.9,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.delenv(case.env_var, raising=False)

    sources = case.catalog_type(project).get_active_catalogs()

    assert sources[0].priority == 1


def test_bundle_catalogs_merge_scopes_by_id_and_sort_deterministically(
    tmp_path: Path,
) -> None:
    from specify_cli.bundles.catalogs import Scope, load_source_stack

    project = tmp_path / "project"
    user_config = tmp_path / "user"
    (project / ".specify").mkdir(parents=True)
    user_config.mkdir()
    (user_config / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "catalogs": [
                    {
                        "id": "default",
                        "url": "https://user.example.com/default.json",
                        "priority": 9,
                        "install_policy": "discovery-only",
                    },
                    {
                        "id": "team",
                        "url": "https://user.example.com/team.json",
                        "priority": 5,
                        "install_policy": "discovery-only",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "catalogs": [
                    {
                        "id": "default",
                        "url": "https://project.example.com/default.json",
                        "priority": 1,
                        "install_policy": "install-allowed",
                    },
                    {
                        "id": "team",
                        "url": "https://project.example.com/team.json",
                        "priority": 5,
                        "install_policy": "install-allowed",
                    },
                    {
                        "id": "alpha",
                        "url": "https://project.example.com/alpha.json",
                        "priority": 5,
                        "install_policy": "discovery-only",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    sources = load_source_stack(project, user_config)
    by_id = {source.id: source for source in sources}

    assert [source.id for source in sources] == [
        "default",
        "alpha",
        "team",
        "community",
    ]
    assert by_id["default"].url == "https://project.example.com/default.json"
    assert by_id["default"].scope is Scope.PROJECT
    assert by_id["team"].url == "https://project.example.com/team.json"
    assert by_id["team"].scope is Scope.PROJECT
    assert by_id["community"].scope is Scope.BUILTIN


def test_bundle_catalog_materialization_rejects_fractional_priority() -> None:
    from specify_cli.bundler import BundlerError
    from specify_cli.bundles.catalogs import CatalogSource, Scope

    with pytest.raises(BundlerError, match="non-integer priority"):
        CatalogSource.from_dict(
            {
                "id": "fractional",
                "url": "https://example.com/catalog.json",
                "priority": 1.9,
                "install_policy": "discovery-only",
            },
            Scope.PROJECT,
        )


def test_bundle_config_reader_defers_source_field_validation(tmp_path: Path) -> None:
    from specify_cli.bundles import catalog_config

    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(
            {
                "catalogs": [
                    {
                        "id": "deferred",
                        "url": "ftp://example.com/catalog.json",
                        "priority": True,
                        "install_policy": "not-a-policy",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert catalog_config._read(project) == [
        {
            "id": "deferred",
            "url": "ftp://example.com/catalog.json",
            "priority": True,
            "install_policy": "not-a-policy",
        }
    ]


def test_bundle_catalog_remove_can_delete_invalid_raw_entry(tmp_path: Path) -> None:
    from specify_cli.bundles import catalog_config

    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    config_path = project / ".specify" / "bundle-catalogs.yml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "catalogs": [
                    {
                        "id": "invalid",
                        "url": "ftp://example.com/catalog.json",
                        "priority": True,
                        "install_policy": "not-a-policy",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert catalog_config.remove_source(project, "invalid") == "invalid"
    assert yaml.safe_load(config_path.read_text(encoding="utf-8")) == {
        "schema_version": "1.0",
        "catalogs": [],
    }


def test_bundle_catalog_malformed_project_config_does_not_fall_back(
    tmp_path: Path,
) -> None:
    from specify_cli.bundler import BundlerError
    from specify_cli.bundles.catalogs import load_source_stack

    project = tmp_path / "project"
    user_config = tmp_path / "user"
    (project / ".specify").mkdir(parents=True)
    user_config.mkdir()
    (project / ".specify" / "bundle-catalogs.yml").write_text(
        "catalogs: false\n", encoding="utf-8"
    )

    with pytest.raises(BundlerError, match="'catalogs' must be a list"):
        load_source_stack(project, user_config)


def test_integration_malformed_release_history_falls_through(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from specify_cli.integrations import (
        IntegrationCatalogEntry,
        IntegrationCatalogError,
        _catalog_shape_error,
    )

    high = IntegrationCatalogEntry(
        "https://example.com/high.json", "high", 1, False
    )
    low = IntegrationCatalogEntry(
        "https://example.com/low.json", "low", 2, True
    )
    payloads = {
        "high": {
            "schema_version": "1.0",
            "integrations": {
                "sample": {
                    "id": "sample",
                    "version": "2.0.0",
                    "releases": [],
                }
            },
        },
        "low": {
            "schema_version": "1.0",
            "integrations": {
                "sample": {
                    "id": "sample",
                    "version": "1.0.0",
                }
            },
        },
    }
    catalog = IntegrationCatalog(tmp_path)
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda: [high, low])

    def fetch(source, force_refresh=False):
        payload = payloads[source.name]
        error = _catalog_shape_error(payload)
        if error is not None:
            raise IntegrationCatalogError(error)
        return payload

    monkeypatch.setattr(catalog, "_fetch_single_catalog", fetch)

    result = catalog.get_integration_info("sample")

    assert result is not None
    assert result["version"] == "1.0.0"
    assert result["_catalog_name"] == "low"
    assert result["_install_allowed"] is True


@pytest.mark.parametrize("catalog_kind", ["workflow", "workflow-step"])
def test_workflow_catalogs_use_stale_cache_after_malformed_json(
    catalog_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from specify_cli.authentication import http as auth_http
    from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowCatalogEntry
    from specify_cli.workflows.step.catalog import StepCatalog, StepCatalogEntry

    if catalog_kind == "workflow":
        catalog = WorkflowCatalog(tmp_path)
        entry = WorkflowCatalogEntry(
            "https://example.com/workflows.json", "test", 1, True
        )
        payload = {"schema_version": "1.0", "workflows": {}}
    else:
        catalog = StepCatalog(tmp_path)
        entry = StepCatalogEntry(
            "https://example.com/steps.json", "test", 1, True
        )
        payload = {"schema_version": "1.0", "steps": {}}

    cache_path, _ = catalog._get_cache_paths(entry.url)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload), encoding="utf-8")

    class MalformedResponse(io.BytesIO):
        def geturl(self):
            return entry.url

    monkeypatch.setattr(
        auth_http,
        "open_url",
        lambda *args, **kwargs: MalformedResponse(b"not-json"),
    )

    assert catalog._fetch_single_catalog(entry, force_refresh=True) == payload
