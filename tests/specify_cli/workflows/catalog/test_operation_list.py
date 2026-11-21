"""Transport-neutral workflow catalog list contract and effect boundaries."""

import errno
import json
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


def _symlink_or_skip(link, target):
    try:
        link.symlink_to(target)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 1314 or exc.errno in {
            errno.EPERM,
            errno.ENOTSUP,
        }:
            pytest.skip(f"Host cannot create symlinks: {exc}")
        raise


def _allow_symlinks(root, allow):
    (root / ".specify" / "init-options.json").write_text(
        json.dumps({"allow_symlinks": allow}), encoding="utf-8"
    )


def _alias_chain(depth):
    """Anchors that each repeat the previous one nine times."""
    lines = ["a0: &a0 [x, x, x, x, x, x, x, x, x]"]
    for level in range(1, depth):
        aliases = ", ".join([f"*a{level - 1}"] * 9)
        lines.append(f"a{level}: &a{level} [{aliases}]")
    return "\n".join(lines) + "\n"


URL_LINE = "    url: https://e.example/c.json\n"


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


@pytest.mark.parametrize(
    "entry",
    [
        f"  - name: *a6\n{URL_LINE}",
        f"  - name: n\n{URL_LINE}    description: *a6\n",
        "  - name: n\n    url: *a6\n",
        f"  - name: n\n{URL_LINE}    priority: *a6\n",
    ],
    ids=["name", "description", "url", "priority"],
)
def test_nested_aliases_are_rejected_before_text_coercion(tmp_path, entry):
    config = _alias_chain(7) + "catalogs:\n" + entry
    assert len(config) < 1024
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(_project(tmp_path, config), 1)
    assert exc.value.code == "invalid_catalog_config"
    assert "size limit" in str(exc.value.__cause__)


def test_nested_merge_keys_are_rejected_before_construction(tmp_path):
    lines = ["a0: &a0 {k: v}"]
    for level in range(1, 7):
        aliases = ", ".join([f"*a{level - 1}"] * 9)
        lines.append(f"a{level}: &a{level} {{<<: [{aliases}]}}")
    config = "\n".join(lines) + f"\ncatalogs:\n  - name: n\n{URL_LINE}"
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(_project(tmp_path, config))
    assert exc.value.code == "invalid_catalog_config"
    assert "size limit" in str(exc.value.__cause__)


@pytest.mark.parametrize(
    "config",
    [
        f"r: &r [*r]\ncatalogs:\n  - name: *r\n{URL_LINE}",
        "[" * 5000,
    ],
    ids=["recursive-alias", "deep-nesting"],
)
def test_unbounded_yaml_structures_fail_closed(tmp_path, config):
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(_project(tmp_path, config))
    assert exc.value.code == "invalid_catalog_config"


def test_ordinary_aliases_and_merge_keys_still_load(tmp_path):
    root = _project(
        tmp_path,
        "base: &base {install_allowed: true, description: &text Shared text}\n"
        "catalogs:\n"
        "  - {<<: *base, name: one, url: https://one.example/c.json}\n"
        "  - {name: two, url: https://two.example/c.json, description: *text}\n",
    )
    items = _list(root).items
    assert [(item.name, item.install_allowed) for item in items] == [
        ("one", True),
        ("two", False),
    ]
    assert [item.description for item in items] == ["Shared text", "Shared text"]


def test_large_config_without_aliases_is_not_limited(tmp_path):
    description = "x" * (2 * 1024 * 1024)
    root = _project(
        tmp_path,
        f"catalogs:\n  - name: big\n{URL_LINE}    description: {description}\n",
    )
    assert _list(root).items[0].description == description


@pytest.mark.parametrize(
    "config",
    [
        'catalogs:\n  - name: c\n    url: "https://user:s3cret@[::1"\n',
        'catalogs:\n  - name: c\n    url: "https://user:s3cret@e.example/c\n',
        "catalogs:\n  - name: c\n    url: https://e.example/c\n    priority: s3cret\n",
    ],
    ids=["malformed-url", "yaml-parser", "priority"],
)
def test_shared_config_error_message_holds_no_configured_values(tmp_path, config):
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(_project(tmp_path, config))
    assert exc.value.code == "invalid_catalog_config"
    assert "s3cret" not in str(exc.value)
    assert str(tmp_path) not in str(exc.value)
    assert "s3cret" in str(exc.value.__cause__)


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


@pytest.mark.parametrize("kind", ["policy", "storage", "specify-file"])
def test_unsafe_project_storage_is_rejected(tmp_path, kind):
    root = _project(tmp_path)
    if kind == "policy":
        path = root / ".specify" / "init-options.json"
        path.write_text('{"allow_symlinks": "yes"}', encoding="utf-8")
    elif kind == "storage":
        (root / ".specify" / "workflows").write_text("not a dir", encoding="utf-8")
    else:
        (root / ".specify").rmdir()
        (root / ".specify").write_text("not a dir", encoding="utf-8")
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
    _symlink_or_skip(root / ".specify" / "workflow-catalogs.yml", outside)
    with pytest.raises(operation.WorkflowCatalogListError) as error:
        _list(root)
    assert error.value.code == "unsafe_workflow_storage"


def test_contained_config_symlink_requires_the_project_opt_in(tmp_path):
    root = _project(tmp_path)
    target = root / "shared-catalogs.yml"
    target.write_text(
        "catalogs:\n  - name: contained\n    url: https://c.example/c.json\n",
        encoding="utf-8",
    )
    _symlink_or_skip(root / ".specify" / "workflow-catalogs.yml", target)

    with pytest.raises(operation.WorkflowCatalogListError) as error:
        _list(root)
    assert error.value.code == "unsafe_workflow_storage"

    _allow_symlinks(root, True)
    assert [item.name for item in _list(root).items] == ["contained"]


def test_config_symlink_leaving_the_project_is_denied_even_with_the_opt_in(tmp_path):
    root = _project(tmp_path)
    _allow_symlinks(root, True)
    outside = tmp_path / "outside.yml"
    outside.write_text(
        "catalogs:\n  - name: outside\n    url: https://outside.example/c.json\n",
        encoding="utf-8",
    )
    _symlink_or_skip(root / ".specify" / "workflow-catalogs.yml", outside)
    with pytest.raises(operation.WorkflowCatalogListError) as error:
        _list(root)
    assert error.value.code == "unsafe_workflow_storage"


def test_dangling_specify_symlink_is_unsafe_storage(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    _symlink_or_skip(root / ".specify", tmp_path / "missing")
    with pytest.raises(operation.WorkflowCatalogListError) as error:
        _list(root)
    assert error.value.code == "unsafe_workflow_storage"


@pytest.mark.parametrize("allow", [True, False])
def test_project_config_read_goes_through_the_file_policy(tmp_path, monkeypatch, allow):
    """Runs without symlink privileges, unlike the real-symlink tests above."""
    root = _project(
        tmp_path, "catalogs:\n  - name: project\n    url: https://p.example/c.json\n"
    )
    _allow_symlinks(root, allow)
    read_text = FileHelper.read_text
    denied = []

    def deny_catalog_config(self, path, *, encoding="utf-8"):
        if Path(path).name != "workflow-catalogs.yml":
            return read_text(self, path, encoding=encoding)
        denied.append(self.allow_symlinks)
        raise SymlinkDeniedError(f"Denied: {path}")

    monkeypatch.setattr(FileHelper, "read_text", deny_catalog_config)
    with pytest.raises(operation.WorkflowCatalogListError) as exc:
        _list(root)
    assert exc.value.code == "unsafe_workflow_storage"
    assert denied == [allow]


def test_existing_catalog_callers_keep_their_read_behavior(tmp_path, monkeypatch):
    """The read-policy handoff stays opt-in for mutation paths and other callers."""
    root = _project(
        tmp_path, "catalogs:\n  - name: project\n    url: https://p.example/c.json\n"
    )

    def refuse(*args, **kwargs):
        raise AssertionError("Default catalog reads must not use FileHelper")

    monkeypatch.setattr(FileHelper, "read_bytes", refuse)
    monkeypatch.setattr(FileHelper, "read_text", refuse)
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
    assert descriptor.warning_types == ()
