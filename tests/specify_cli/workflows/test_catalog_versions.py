"""Exact-release lookup and installation for workflow catalogs (#4719)."""

from __future__ import annotations

import hashlib
import io
import zipfile

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows.catalog import (
    WorkflowCatalog,
    WorkflowCatalogEntry,
    WorkflowRegistry,
    WorkflowValidationError,
)

runner = CliRunner()
CURRENT_URL = "https://example.com/current.zip"
OLD_URL = "https://example.com/old.zip"
OLD_YAML_URL = "https://example.com/old.yml"
OLD_WORKFLOW_YAML = b"""schema_version: "1.0"
workflow:
  id: history-wf
  name: History Workflow
  version: 1.0.0
steps:
  - id: first
    type: gate
    message: Continue?
"""


def _archive(version: str, workflow_id: str = "history-wf", requires=None) -> bytes:
    import yaml

    document = {
        "schema_version": "1.0",
        "workflow": {
            "id": workflow_id,
            "name": "History Workflow",
            "version": version,
        },
        "steps": [{"id": "first", "type": "gate", "message": "Continue?"}],
    }
    if requires is not None:
        document["requires"] = requires
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("workflow.yml", yaml.safe_dump(document))
    return output.getvalue()


def _entry() -> dict:
    old = _archive("1.0.0", requires={"integrations": ["copilot"]})
    current = _archive("2.0.0")
    return {
        "id": "history-wf",
        "name": "History Workflow",
        "version": "2.0.0",
        "url": CURRENT_URL,
        "sha256": hashlib.sha256(current).hexdigest(),
        "bundled": True,
        "releases": {
            "1.0.0": {
                "url": OLD_URL,
                "sha256": hashlib.sha256(old).hexdigest(),
                "requires": {"integrations": ["copilot"]},
            }
        },
    }


def _catalog(monkeypatch, project_dir, high, low=None, *, install_allowed=True):
    sources = [
        WorkflowCatalogEntry(
            "https://example.com/high.json", "high", 1, install_allowed
        )
    ]
    if low is not None:
        sources.append(
            WorkflowCatalogEntry("https://example.com/low.json", "low", 2, True)
        )
    monkeypatch.setattr(WorkflowCatalog, "get_active_catalogs", lambda self: sources)
    monkeypatch.setattr(
        WorkflowCatalog,
        "_fetch_single_catalog",
        lambda self, source, force_refresh=False: {
            "workflows": {"history-wf": high if source.name == "high" else low}
        },
    )
    return WorkflowCatalog(project_dir)


class _Response(io.BytesIO):
    def __init__(self, content: bytes, url: str):
        super().__init__(content)
        self.url = url

    def geturl(self):
        return self.url


def test_current_and_historical_metadata(monkeypatch, project_dir):
    entry = _entry()
    catalog = _catalog(monkeypatch, project_dir, entry)
    assert catalog.get_workflow_info("history-wf")["url"] == CURRENT_URL
    assert catalog.get_workflow_info("history-wf", "v2.0")["url"] == CURRENT_URL
    old = catalog.get_workflow_info("history-wf", "1.0.0.0")
    assert old["url"] == OLD_URL
    assert old["version"] == "1.0.0"
    assert old["sha256"] == entry["releases"]["1.0.0"]["sha256"]
    assert old["requires"] == {"integrations": ["copilot"]}
    assert "releases" not in old and "bundled" not in old
    assert old["_catalog_name"] == "high"
    assert catalog.get_workflow_versions("history-wf") == ["2.0.0", "1.0.0"]
    assert catalog.get_workflow_info("history-wf", "invalid") is None
    assert catalog.get_workflow_info("history-wf", "0.0.1") is None


def test_legacy_entry_and_winning_source(monkeypatch, project_dir):
    entry = _entry()
    high = {"id": "history-wf", "version": "2.0.0", "url": CURRENT_URL}
    catalog = _catalog(monkeypatch, project_dir, high, entry)
    assert catalog.get_workflow_info("history-wf", "2.0.0")["url"] == CURRENT_URL
    assert catalog.get_workflow_info("history-wf", "1.0.0") is None
    assert catalog.get_workflow_versions("history-wf") == ["2.0.0"]
    assert catalog.search(query="history-wf")[0]["version"] == "2.0.0"


@pytest.mark.parametrize(
    "history",
    [
        None,
        [],
        {"bad": {"url": OLD_URL, "sha256": "a" * 64}},
        {"\u0661.\u0660.\u0660": {"url": OLD_URL, "sha256": "a" * 64}},
        {"1.0": {"url": OLD_URL, "sha256": "a" * 64}},
        {"v1.0.0": {"url": OLD_URL, "sha256": "a" * 64}},
        {"2.0.0": {"url": OLD_URL, "sha256": "a" * 64}},
        {"2.0.0.0": {"url": OLD_URL, "sha256": "a" * 64}},
        {
            "1.0.0": {"url": OLD_URL, "sha256": "a" * 64},
            "01.0.0": {"url": OLD_URL, "sha256": "b" * 64},
        },
        {"1.0.0": {"sha256": "a" * 64}},
        {"1.0.0": {"url": "http://example.com/old.zip", "sha256": "a" * 64}},
        {"1.0.0": {"url": "https://[::1", "sha256": "a" * 64}},
        {"1.0.0": {"url": OLD_URL}},
        {"1.0.0": {"url": OLD_URL, "sha256": "wrong"}},
        {"1.0.0": {"url": OLD_URL, "sha256": "a" * 64, "id": "other"}},
        {"1.0.0": {"url": OLD_URL, "sha256": "a" * 64, "requires": []}},
        {"1.0.0": None},
    ],
)
def test_malformed_history_rejected(monkeypatch, project_dir, history):
    entry = _entry()
    entry["releases"] = history
    catalog = _catalog(monkeypatch, project_dir, entry)
    with pytest.raises(WorkflowValidationError):
        catalog.get_workflow_info("history-wf", "1.0.0")
    with pytest.raises(WorkflowValidationError):
        catalog.get_workflow_versions("history-wf")


def test_history_without_current_version_rejected(monkeypatch, project_dir):
    entry = _entry()
    entry.pop("version")
    catalog = _catalog(monkeypatch, project_dir, entry)
    with pytest.raises(WorkflowValidationError, match="no current version"):
        catalog.get_workflow_info("history-wf")


@pytest.mark.parametrize(
    "version", ["2.0", "v2.0.0", "2.0.0.0", "\u0662.\u0660.\u0660"]
)
def test_history_with_non_workflow_current_version_rejected(
    monkeypatch, project_dir, version
):
    entry = _entry()
    entry["version"] = version
    catalog = _catalog(monkeypatch, project_dir, entry)
    with pytest.raises(WorkflowValidationError, match="invalid current version"):
        catalog.get_workflow_info("history-wf")


def test_malformed_history_is_reported_by_cli(monkeypatch, project_dir):
    entry = _entry()
    entry["releases"] = {"1.0.0": {"url": OLD_URL}}
    _catalog(monkeypatch, project_dir, entry)
    monkeypatch.chdir(project_dir)
    for args in (
        ["workflow", "info", "history-wf"],
        ["workflow", "info", "history-wf", "--versions"],
        ["workflow", "add", "history-wf", "--version", "1.0.0"],
    ):
        result = runner.invoke(app, args)
        assert result.exit_code == 1
        assert "needs a SHA-256 digest" in result.output
        assert "not found" not in result.output


def test_info_versions_uses_catalog_even_when_installed(monkeypatch, project_dir):
    _catalog(monkeypatch, project_dir, _entry())
    WorkflowRegistry(project_dir).add(
        "history-wf", {"version": "0.5.0", "source": "catalog"}
    )
    monkeypatch.chdir(project_dir)
    result = runner.invoke(app, ["workflow", "info", "history-wf", "--versions"])
    assert result.exit_code == 0, result.output
    assert "2.0.0, 1.0.0" in result.output
    assert "installable" in result.output
    result = runner.invoke(app, ["workflow", "info", "history-wf"])
    assert result.exit_code == 0, result.output
    assert "Version:     2.0.0" in result.output


def test_info_versions_labels_discovery_only_catalog(monkeypatch, project_dir):
    _catalog(monkeypatch, project_dir, _entry(), _entry(), install_allowed=False)
    monkeypatch.chdir(project_dir)
    result = runner.invoke(app, ["workflow", "info", "history-wf", "--versions"])
    assert result.exit_code == 0, result.output
    assert "2.0.0, 1.0.0" in result.output
    assert "discovery-only" in result.output
    assert "not installable" in result.output


def test_exact_add_uses_historical_url_digest_and_requirements(
    monkeypatch, project_dir
):
    from specify_cli.authentication import http

    _catalog(monkeypatch, project_dir, _entry())
    requested = []

    def open_url(url, **kwargs):
        requested.append(url)
        return _Response(_archive("1.0.0", requires={"integrations": ["copilot"]}), url)

    monkeypatch.setattr(http, "open_url", open_url)
    monkeypatch.chdir(project_dir)
    result = runner.invoke(app, ["workflow", "add", "history-wf", "--version", "v1.0"])
    assert result.exit_code == 0, result.output
    assert requested == [OLD_URL]
    assert WorkflowRegistry(project_dir).get("history-wf")["version"] == "1.0.0"


def test_exact_yaml_release_verifies_digest_and_version(monkeypatch, project_dir):
    from specify_cli.authentication import http

    entry = _entry()
    entry["releases"]["1.0.0"] = {
        "url": OLD_YAML_URL,
        "sha256": hashlib.sha256(OLD_WORKFLOW_YAML).hexdigest(),
    }
    _catalog(monkeypatch, project_dir, entry)
    monkeypatch.setattr(
        http,
        "open_url",
        lambda url, **kw: _Response(OLD_WORKFLOW_YAML, url),
    )
    monkeypatch.chdir(project_dir)
    result = runner.invoke(app, ["workflow", "add", "history-wf", "--version", "1.0"])
    assert result.exit_code == 0, result.output
    assert WorkflowRegistry(project_dir).get("history-wf")["version"] == "1.0.0"


def test_exact_yaml_release_rejects_mismatched_requirements(monkeypatch, project_dir):
    from specify_cli.authentication import http

    entry = _entry()
    entry["releases"]["1.0.0"] = {
        "url": OLD_YAML_URL,
        "sha256": hashlib.sha256(OLD_WORKFLOW_YAML).hexdigest(),
        "requires": {"integrations": ["copilot"]},
    }
    _catalog(monkeypatch, project_dir, entry)
    requested = []

    def open_url(url, **kwargs):
        requested.append(url)
        return _Response(OLD_WORKFLOW_YAML, url)

    monkeypatch.setattr(http, "open_url", open_url)
    monkeypatch.chdir(project_dir)
    result = runner.invoke(app, ["workflow", "add", "history-wf", "--version", "1.0.0"])

    assert result.exit_code == 1
    assert "requirements do not match" in " ".join(result.output.split())
    assert requested == [OLD_YAML_URL]
    assert WorkflowRegistry(project_dir).get("history-wf") is None
    assert not (
        project_dir / ".specify" / "workflows" / "history-wf" / "workflow.yml"
    ).exists()


@pytest.mark.parametrize("source_type", ["archive", "yaml"])
def test_exact_release_rejects_differently_spelled_artifact_version(
    monkeypatch, project_dir, source_type
):
    from specify_cli.authentication import http

    if source_type == "archive":
        download = _archive("01.0.0")
        url = OLD_URL
    else:
        download = b"""schema_version: "1.0"
workflow:
  id: history-wf
  name: History Workflow
  version: "01.0.0"
steps:
  - id: first
    type: gate
    message: Continue?
"""
        url = "https://example.com/old.yml"
    entry = _entry()
    entry["releases"]["1.0.0"] = {
        "url": url,
        "sha256": hashlib.sha256(download).hexdigest(),
    }
    _catalog(monkeypatch, project_dir, entry)
    monkeypatch.setattr(
        http, "open_url", lambda requested, **kw: _Response(download, requested)
    )
    monkeypatch.chdir(project_dir)

    result = runner.invoke(app, ["workflow", "add", "history-wf", "--version", "v1.0"])

    assert result.exit_code == 1
    assert "does not match the catalog version" in result.output
    assert WorkflowRegistry(project_dir).get("history-wf") is None


@pytest.mark.parametrize(
    ("download", "entry_change", "error"),
    [
        (_archive("3.0.0"), None, "does not match the catalog version"),
        (
            _archive("1.0.0", "wrong-wf"),
            None,
            "does not match the requested workflow ID",
        ),
        (_archive("1.0.0"), None, "requirements do not match"),
        (
            _archive("1.0.0", requires={"integrations": ["copilot"]}),
            "bad-digest",
            "Integrity check failed",
        ),
    ],
    ids=["version", "id", "requirements", "digest"],
)
def test_exact_add_rejects_inconsistent_archive(
    monkeypatch, project_dir, download, entry_change, error
):
    from specify_cli.authentication import http
    from specify_cli.workflows import _commands as workflow_cli

    monkeypatch.setattr(workflow_cli.console, "width", 68)
    entry = _entry()
    if entry_change == "bad-digest":
        entry["releases"]["1.0.0"]["sha256"] = "0" * 64
    else:
        entry["releases"]["1.0.0"]["sha256"] = hashlib.sha256(download).hexdigest()
    _catalog(monkeypatch, project_dir, entry)
    monkeypatch.setattr(http, "open_url", lambda url, **kw: _Response(download, url))
    monkeypatch.chdir(project_dir)
    result = runner.invoke(app, ["workflow", "add", "history-wf", "--version", "1.0.0"])
    assert result.exit_code == 1
    assert error in " ".join(result.output.split())
    assert WorkflowRegistry(project_dir).get("history-wf") is None
    assert not (
        project_dir / ".specify" / "workflows" / "history-wf" / "workflow.yml"
    ).exists()


def test_no_fallthrough_for_missing_or_discovery_release(monkeypatch, project_dir):
    high = _entry()
    high["releases"] = {}
    _catalog(monkeypatch, project_dir, high, _entry())
    monkeypatch.chdir(project_dir)
    missing = runner.invoke(
        app, ["workflow", "add", "history-wf", "--version", "1.0.0"]
    )
    assert missing.exit_code == 1
    assert "not found in the winning catalog" in missing.output
    _catalog(monkeypatch, project_dir, _entry(), _entry(), install_allowed=False)
    discovery = runner.invoke(
        app, ["workflow", "add", "history-wf", "--version", "1.0.0"]
    )
    assert discovery.exit_code == 1
    assert "discovery-only" in discovery.output


def test_unqualified_add_still_uses_current_and_invalid_version_scope(
    monkeypatch, project_dir
):
    from specify_cli.authentication import http

    _catalog(monkeypatch, project_dir, _entry())
    requested = []

    def open_url(url, **kw):
        requested.append(url)
        return _Response(_archive("2.0.0"), url)

    monkeypatch.setattr(http, "open_url", open_url)
    monkeypatch.chdir(project_dir)
    result = runner.invoke(app, ["workflow", "add", "history-wf"])
    assert result.exit_code == 0, result.output
    assert requested == [CURRENT_URL]
    assert WorkflowRegistry(project_dir).get("history-wf")["version"] == "2.0.0"
    invalid = runner.invoke(
        app,
        ["workflow", "add", "history-wf", "--from", OLD_URL, "--version", "1.0.0"],
    )
    assert invalid.exit_code == 1
    assert "--version requires a workflow ID" in invalid.output
    assert requested == [CURRENT_URL]


@pytest.mark.parametrize(
    "source_type", ["direct-url", "local-file", "local-dir", "dev"]
)
def test_exact_add_rejects_non_catalog_sources(monkeypatch, project_dir, source_type):
    from specify_cli.authentication import http

    source = "history-wf"
    options = []
    if source_type == "direct-url":
        source = OLD_YAML_URL
    elif source_type in ("local-file", "local-dir"):
        path = project_dir / "local-workflow"
        if source_type == "local-dir":
            path.mkdir()
            (path / "workflow.yml").write_bytes(OLD_WORKFLOW_YAML)
        else:
            path = path.with_suffix(".yml")
            path.write_bytes(OLD_WORKFLOW_YAML)
        source = str(path)
    else:
        options = ["--dev"]

    requested = []
    monkeypatch.setattr(http, "open_url", lambda url, **kwargs: requested.append(url))
    monkeypatch.chdir(project_dir)
    result = runner.invoke(
        app, ["workflow", "add", source, *options, "--version", "1.0.0"]
    )

    assert result.exit_code == 1
    assert "--version requires a workflow ID from a catalog" in result.output
    assert requested == []
    assert WorkflowRegistry(project_dir).get("history-wf") is None
    assert not (
        project_dir / ".specify" / "workflows" / "history-wf" / "workflow.yml"
    ).exists()
