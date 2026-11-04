"""Transport-neutral workflow catalog list contract and effect boundaries."""

import errno
import socket
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from specify_cli.file_helper import FileHelper, SymlinkDeniedError
from specify_cli.workflows.catalog import WorkflowCatalog
from specify_cli.workflows.catalog import _operation_list as operation


@pytest.fixture(autouse=True)
def isolated_layers(tmp_path, monkeypatch):
    """Keep the environment and the real user config out of the catalog stack."""
    monkeypatch.delenv("SPECKIT_WORKFLOW_CATALOG_URL", raising=False)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    return home


def _project(tmp_path, config=None):
    root = tmp_path / "project"
    (root / ".specify").mkdir(parents=True)
    if config is not None:
        (root / ".specify" / "workflow-catalogs.yml").write_text(
            config, encoding="utf-8"
        )
    return root


def _list(root, limit=None):
    return operation.list_catalog_sources(
        operation.WorkflowCatalogListRequest(root, limit)
    )


def _tree(root):
    return sorted(str(path.relative_to(root)) for path in root.rglob("*"))


def test_builtin_defaults_when_nothing_is_configured(tmp_path):
    result = _list(_project(tmp_path))
    assert [item.name for item in result.items] == ["default", "community"]
    assert [item.priority for item in result.items] == [1, 2]
    assert [item.install_allowed for item in result.items] == [True, False]
    assert result.truncated is False
    with pytest.raises(FrozenInstanceError):
        result.truncated = True


def test_project_config_is_ordered_and_normalized(tmp_path):
    root = _project(
        tmp_path,
        "catalogs:\n"
        "  - name: second\n"
        "    url: https://second.example/catalog.json\n"
        "    priority: 20\n"
        "  - name: first\n"
        "    url: https://first.example/catalog.json\n"
        "    priority: 10\n"
        "    install_allowed: true\n"
        "    description: First source\n",
    )
    assert _list(root).items == (
        operation.WorkflowCatalogSource(
            "first", "https://first.example/catalog.json", 10, True, "First source"
        ),
        operation.WorkflowCatalogSource(
            "second", "https://second.example/catalog.json", 20, False, None
        ),
    )


def test_operation_keeps_the_configured_url_for_adapters_to_project(tmp_path):
    url = "https://user:token@host.example/catalog.json?key=value"
    root = _project(tmp_path, f"catalogs:\n  - name: private\n    url: {url}\n")
    assert _list(root).items[0].url == url


def test_environment_override_takes_precedence(tmp_path, monkeypatch):
    root = _project(
        tmp_path, "catalogs:\n  - name: project\n    url: https://p.example/c.json\n"
    )
    monkeypatch.setenv("SPECKIT_WORKFLOW_CATALOG_URL", "https://env.example/c.json")
    assert [item.name for item in _list(root).items] == ["env-override"]


def test_user_config_applies_when_project_has_none(tmp_path, isolated_layers):
    (isolated_layers / ".specify").mkdir()
    (isolated_layers / ".specify" / "workflow-catalogs.yml").write_text(
        "catalogs:\n  - name: user\n    url: https://user.example/c.json\n",
        encoding="utf-8",
    )
    assert [item.name for item in _list(_project(tmp_path)).items] == ["user"]


@pytest.mark.parametrize(
    "limit,names,truncated",
    [
        (1, ["default"], True),
        (2, ["default", "community"], False),
        (1000, ["default", "community"], False),
        (None, ["default", "community"], False),
    ],
)
def test_limit_bounds_sources_and_reports_truncation(
    tmp_path, limit, names, truncated
):
    result = _list(_project(tmp_path), limit)
    assert [item.name for item in result.items] == names
    assert result.truncated is truncated


@pytest.mark.parametrize("limit", [0, -1, 1001, True, 1.5, "1"])
def test_invalid_limit_is_rejected(tmp_path, limit):
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(_project(tmp_path), limit)
    assert exc.value.code == "invalid_limit"


def test_relative_project_directory_is_rejected():
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(Path("relative"))
    assert exc.value.code == "invalid_project_directory"


@pytest.mark.parametrize("kind", ["missing", "file", "no-specify", "nul"])
def test_non_project_roots_are_rejected(tmp_path, kind):
    root = tmp_path / "candidate"
    if kind == "file":
        root.write_text("not a directory", encoding="utf-8")
    elif kind == "no-specify":
        root.mkdir()
    elif kind == "nul":
        root = tmp_path / "invalid\x00project"
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(root)
    assert exc.value.code == "not_a_spec_kit_project"


@pytest.mark.parametrize(
    "config",
    [
        "catalogs: [",
        "- not\n- a mapping\n",
        "catalogs: 5\n",
        "catalogs:\n  - name: no-url\n",
        "catalogs:\n  - name: plain\n    url: http://example.com/c.json\n",
        "catalogs:\n  - name: bad\n    url: https://[::1\n",
        "catalogs:\n  - name: p\n    url: https://e.example/c\n    priority: high\n",
    ],
)
def test_malformed_config_fails_closed(tmp_path, config):
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(_project(tmp_path, config))
    assert exc.value.code == "invalid_catalog_config"


def test_undecodable_config_fails_closed(tmp_path):
    root = _project(tmp_path)
    (root / ".specify" / "workflow-catalogs.yml").write_bytes(b"\xff\xfe\xff")
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(root)
    assert exc.value.code == "invalid_catalog_config"


def test_invalid_environment_override_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("SPECKIT_WORKFLOW_CATALOG_URL", "http://example.com/c.json")
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(_project(tmp_path))
    assert exc.value.code == "invalid_catalog_config"


@pytest.mark.parametrize("kind", ["policy", "storage"])
def test_unsafe_project_storage_is_rejected(tmp_path, kind):
    root = _project(tmp_path)
    if kind == "policy":
        path = root / ".specify" / "init-options.json"
        path.write_text('{"allow_symlinks": "yes"}', encoding="utf-8")
    else:
        (root / ".specify" / "workflows").write_text("not a dir", encoding="utf-8")
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(root)
    assert exc.value.code == "unsafe_workflow_storage"


def test_symlinked_project_config_is_not_followed(tmp_path):
    root = _project(tmp_path)
    outside = tmp_path / "outside.yml"
    outside.write_text(
        "catalogs:\n  - name: outside\n    url: https://outside.example/c.json\n",
        encoding="utf-8",
    )
    link = root / ".specify" / "workflow-catalogs.yml"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 1314 or exc.errno in {
            errno.EPERM,
            errno.ENOTSUP,
        }:
            pytest.skip(f"Host cannot create symlinks: {exc}")
        raise
    with pytest.raises(operation.WorkflowCatalogListError) as error:
        _list(root)
    assert error.value.code == "unsafe_workflow_storage"


def test_project_config_read_goes_through_the_file_policy(tmp_path, monkeypatch):
    """Runs without symlink privileges, unlike the real-symlink test above."""
    root = _project(
        tmp_path, "catalogs:\n  - name: project\n    url: https://p.example/c.json\n"
    )

    def deny(self, path, *, encoding="utf-8"):
        raise SymlinkDeniedError(f"Denied: {path}")

    monkeypatch.setattr(FileHelper, "read_text", deny)
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(root)
    assert exc.value.code == "unsafe_workflow_storage"


def test_existing_catalog_callers_keep_their_read_behavior(tmp_path):
    """The read-policy handoff stays opt-in for mutation paths and other callers."""
    root = _project(
        tmp_path, "catalogs:\n  - name: project\n    url: https://p.example/c.json\n"
    )
    configs = WorkflowCatalog(root).get_catalog_configs()
    assert [config["name"] for config in configs] == ["project"]


def test_no_network_access_or_filesystem_writes(tmp_path, monkeypatch):
    root = _project(
        tmp_path, "catalogs:\n  - name: project\n    url: https://p.example/c.json\n"
    )
    before = _tree(tmp_path)

    def refuse(*args, **kwargs):
        raise AssertionError("workflow.catalog.list must not open a socket")

    monkeypatch.setattr(socket, "socket", refuse)
    assert _list(root).items[0].name == "project"
    assert _tree(tmp_path) == before


def test_descriptor_declares_read_only_local_effects():
    descriptor = operation.WORKFLOW_CATALOG_LIST_OPERATION
    assert descriptor.operation_id == "workflow.catalog.list"
    assert descriptor.capabilities == frozenset({"local-read"})
    assert descriptor.network_access == "none"
    assert descriptor.result_type is operation.WorkflowCatalogListResult
