"""Workflow and step catalog cache confinement regressions."""

from __future__ import annotations

import io
import json
import os
import subprocess
import time
from urllib.error import URLError

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows import _catalog_cache
from specify_cli.workflows.catalog import (
    WorkflowCatalog,
    WorkflowCatalogEntry,
    WorkflowCatalogError,
)
from specify_cli.workflows.step.catalog import (
    StepCatalog,
    StepCatalogEntry,
    StepCatalogError,
)

URL = "https://example.com/catalog.json"
SENTINEL = "isolated target must remain unchanged\n"


@pytest.fixture(params=["workflow", "step"])
def catalog_kind(request):
    if request.param == "workflow":
        return (
            WorkflowCatalog,
            WorkflowCatalogEntry,
            "workflows",
            "workflow-catalogs.yml",
            ["workflow", "search"],
        )
    return (
        StepCatalog,
        StepCatalogEntry,
        "steps",
        "step-catalogs.yml",
        ["workflow", "step", "search"],
    )


@pytest.fixture
def fetch(monkeypatch, catalog_kind):
    payload = {catalog_kind[2]: {}}
    calls = []

    class Response(io.BytesIO):
        def geturl(self):
            return URL

    def open_url(*args, **kwargs):
        calls.append(args[0])
        return Response(json.dumps(payload).encode())

    monkeypatch.setattr("specify_cli.authentication.http.open_url", open_url)
    return payload, calls


def symlink(link, target, *, directory=False):
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")


def junction(link, target):
    import _winapi

    _winapi.CreateJunction(str(target), str(link))


@pytest.mark.parametrize("leaf", ["data", "metadata"])
@pytest.mark.parametrize("dangling", [False, True])
def test_cache_leaf_cannot_redirect_write(
    tmp_path, catalog_kind, fetch, leaf, dangling
):
    catalog_cls, entry_cls, *_ = catalog_kind
    root = tmp_path / "project"
    root.mkdir()
    catalog = catalog_cls(root)
    paths = catalog._get_cache_paths(URL)
    paths[0].parent.mkdir(parents=True)
    victim = tmp_path / "victim"
    if not dangling:
        victim.write_text(SENTINEL)
    symlink(paths[leaf == "metadata"], victim)

    assert catalog._fetch_single_catalog(entry_cls(URL, "test", 1, False)) == fetch[0]
    if dangling:
        assert not victim.exists()
    else:
        assert victim.read_text() == SENTINEL


@pytest.mark.skipif(os.name == "nt", reason="Git symlink checkout is POSIX-specific")
@pytest.mark.parametrize("leaf", ["data", "metadata"])
def test_committed_symlink_clone_search_preserves_target(
    tmp_path, catalog_kind, fetch, monkeypatch, leaf
):
    catalog_cls, _, _, config_name, command = catalog_kind
    source = tmp_path / "source"
    source.mkdir()
    victim = tmp_path / "victim"
    victim.write_text(SENTINEL)
    paths = catalog_cls(source)._get_cache_paths(URL)
    paths[0].parent.mkdir(parents=True)
    link = paths[leaf == "metadata"]
    symlink(link, victim)
    (source / ".specify" / config_name).write_text(
        yaml.safe_dump(
            {
                "catalogs": [
                    {
                        "url": URL,
                        "name": "test",
                        "priority": 1,
                        "install_allowed": False,
                    }
                ],
            }
        )
    )

    def git(*args):
        return subprocess.run(
            ["git", *args], check=True, capture_output=True, text=True
        )

    git("init", "-q", str(source))
    git("-C", str(source), "add", ".")
    git(
        "-C",
        str(source),
        "-c",
        "user.name=Cache Test",
        "-c",
        "user.email=cache@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-qm",
        "Isolated cache fixture",
    )
    clone = tmp_path / "clone"
    git("clone", "-q", "--no-local", str(source), str(clone))
    assert (clone / link.relative_to(source)).is_symlink()
    monkeypatch.delenv("SPECKIT_WORKFLOW_CATALOG_URL", raising=False)
    monkeypatch.delenv("SPECKIT_STEP_CATALOG_URL", raising=False)
    monkeypatch.chdir(clone)

    result = CliRunner().invoke(app, command)

    assert result.exit_code == 0, result.output
    assert fetch[1] == [URL]
    assert victim.read_text() == SENTINEL


@pytest.mark.parametrize("ancestor", [".specify", "workflows", "steps", ".cache"])
def test_symlinked_cache_ancestor_cannot_redirect_write(
    tmp_path, catalog_kind, fetch, ancestor
):
    catalog_cls, entry_cls, *_ = catalog_kind
    if catalog_cls is WorkflowCatalog and ancestor == "steps":
        pytest.skip("Workflow caches have no steps ancestor")
    root = tmp_path / "project"
    root.mkdir()
    catalog = catalog_cls(root)
    rel = catalog.cache_dir.relative_to(root)
    index = rel.parts.index(ancestor)
    parent = root.joinpath(*rel.parts[:index])
    parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    symlink(parent / ancestor, outside, directory=True)

    assert catalog._fetch_single_catalog(entry_cls(URL, "test", 1, False)) == fetch[0]
    assert list(outside.iterdir()) == []


def test_regular_cache_fresh_refresh_and_stale_fallback(
    tmp_path, catalog_kind, fetch, monkeypatch
):
    catalog_cls, entry_cls, *_ = catalog_kind
    catalog = catalog_cls(tmp_path)
    entry = entry_cls(URL, "test", 1, False)
    data, metadata = catalog._get_cache_paths(URL)

    assert catalog._fetch_single_catalog(entry) == fetch[0]
    assert json.loads(data.read_text()) == fetch[0]
    assert json.loads(metadata.read_text())["url"] == URL
    assert catalog._is_url_cache_valid(URL)
    assert catalog._fetch_single_catalog(entry) == fetch[0]
    assert fetch[1] == [URL]
    assert catalog._fetch_single_catalog(entry, force_refresh=True) == fetch[0]
    assert fetch[1] == [URL, URL]
    metadata.write_text(json.dumps({"fetched_at": time.time() - 7200}))

    def unavailable(*args, **kwargs):
        raise URLError("isolated offline test")

    monkeypatch.setattr("specify_cli.authentication.http.open_url", unavailable)
    assert catalog._fetch_single_catalog(entry) == fetch[0]


@pytest.mark.parametrize("leaf", ["data", "metadata"])
@pytest.mark.parametrize("fresh", [False, True])
def test_symlinked_cache_is_not_read(
    tmp_path, catalog_kind, fetch, monkeypatch, leaf, fresh
):
    catalog_cls, entry_cls, field, *_ = catalog_kind
    catalog = catalog_cls(tmp_path)
    data, metadata = catalog._get_cache_paths(URL)
    data.parent.mkdir(parents=True)
    poisoned = {field: {"outside": {"name": "Outside"}}}
    timestamp = time.time() if fresh else 0
    data.write_text(json.dumps(poisoned))
    metadata.write_text(json.dumps({"fetched_at": timestamp}))
    target = tmp_path / "outside.json"
    path = (data, metadata)[leaf == "metadata"]
    target.write_bytes(path.read_bytes())
    path.unlink()
    symlink(path, target)

    if fresh:
        assert (
            catalog._fetch_single_catalog(entry_cls(URL, "test", 1, False)) == fetch[0]
        )
        assert fetch[1] == [URL]
    else:

        def unavailable(*args, **kwargs):
            raise URLError("isolated offline test")

        monkeypatch.setattr("specify_cli.authentication.http.open_url", unavailable)
        if leaf == "data":
            with pytest.raises(
                (WorkflowCatalogError, StepCatalogError),
                match="Failed to fetch catalog",
            ):
                catalog._fetch_single_catalog(entry_cls(URL, "test", 1, False))
        else:
            # An unsafe metadata leaf cannot make the cache fresh, but a safe
            # data leaf remains usable as the ordinary stale/offline fallback.
            assert (
                catalog._fetch_single_catalog(entry_cls(URL, "test", 1, False))
                == poisoned
            )


@pytest.mark.parametrize("leaf", ["data", "metadata"])
def test_cache_replacement_preserves_hardlink_target(
    tmp_path, catalog_kind, fetch, leaf
):
    catalog_cls, entry_cls, *_ = catalog_kind
    catalog = catalog_cls(tmp_path)
    paths = catalog._get_cache_paths(URL)
    paths[0].parent.mkdir(parents=True)
    victim = tmp_path / "victim"
    victim.write_text(SENTINEL)
    os.link(victim, paths[leaf == "metadata"])

    assert catalog._fetch_single_catalog(entry_cls(URL, "test", 1, False)) == fetch[0]
    assert victim.read_text() == SENTINEL
    assert json.loads(paths[leaf == "metadata"].read_text())


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor swap regression")
@pytest.mark.parametrize("leaf", ["data", "metadata"])
def test_leaf_swap_at_commit_cannot_redirect_write(
    tmp_path, catalog_kind, monkeypatch, leaf
):
    catalog_cls, *_ = catalog_kind
    path = catalog_cls(tmp_path)._get_cache_paths(URL)[leaf == "metadata"]
    victim = tmp_path / "victim"
    victim.write_text(SENTINEL)
    replace = os.replace

    def swap_then_replace(source, destination, **kwargs):
        symlink(path, victim)
        return replace(source, destination, **kwargs)

    monkeypatch.setattr(os, "replace", swap_then_replace)
    _catalog_cache.write_cache_json(tmp_path, path, {"safe": True})

    assert victim.read_text() == SENTINEL
    assert not path.is_symlink()
    assert json.loads(path.read_text()) == {"safe": True}


@pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor swap regression")
@pytest.mark.parametrize("ancestor", [".specify", "workflows", "steps", ".cache"])
@pytest.mark.parametrize("leaf", ["data", "metadata"])
def test_ancestor_swap_at_commit_cannot_redirect_write(
    tmp_path,
    catalog_kind,
    monkeypatch,
    ancestor,
    leaf,
):
    catalog_cls, *_ = catalog_kind
    if catalog_cls is WorkflowCatalog and ancestor == "steps":
        pytest.skip("Workflow caches have no steps ancestor")
    root = tmp_path / "project"
    root.mkdir()
    path = catalog_cls(root)._get_cache_paths(URL)[leaf == "metadata"]
    parts = path.parent.relative_to(root).parts
    index = parts.index(ancestor)
    swapped = root.joinpath(*parts[: index + 1])
    retained = swapped.with_name(f"{swapped.name}-retained")
    outside = tmp_path / "outside"
    outside.mkdir()
    replace = os.replace

    def swap_then_replace(source, destination, **kwargs):
        swapped.rename(retained)
        symlink(swapped, outside, directory=True)
        return replace(source, destination, **kwargs)

    monkeypatch.setattr(os, "replace", swap_then_replace)
    _catalog_cache.write_cache_json(root, path, {"safe": True})

    assert list(outside.iterdir()) == []
    retained_leaf = retained.joinpath(*parts[index + 1 :], path.name)
    assert json.loads(retained_leaf.read_text()) == {"safe": True}
    assert not list(retained_leaf.parent.glob("*.tmp"))


@pytest.mark.skipif(os.name == "nt", reason="POSIX no-follow open regression")
def test_directory_swap_before_open_is_refused(tmp_path, catalog_kind, monkeypatch):
    catalog_cls, *_ = catalog_kind
    catalog = catalog_cls(tmp_path)
    catalog.cache_dir.mkdir(parents=True)
    path = catalog._get_cache_paths(URL)[0]
    outside = tmp_path / "outside"
    outside.mkdir()
    original_open = os.open

    def swap_then_open(name, flags, *args, **kwargs):
        if name == ".cache":
            catalog.cache_dir.rename(catalog.cache_dir.with_name("retained"))
            symlink(catalog.cache_dir, outside, directory=True)
        return original_open(name, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", swap_then_open)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {swap_then_open})
    with pytest.raises(OSError):
        _catalog_cache.write_cache_json(tmp_path, path, {"safe": True})
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("leaf", ["data", "metadata"])
def test_failed_replace_preserves_existing_cache_and_logs(
    tmp_path,
    catalog_kind,
    fetch,
    monkeypatch,
    caplog,
    leaf,
):
    catalog_cls, entry_cls, *_ = catalog_kind
    catalog = catalog_cls(tmp_path)
    path = catalog._get_cache_paths(URL)[leaf == "metadata"]
    path.parent.mkdir(parents=True)
    path.write_text(SENTINEL)
    original_replace = os.replace

    def fail_replace(source, destination, **kwargs):
        if str(destination).endswith(path.name):
            raise PermissionError("isolated replace failure")
        return original_replace(source, destination, **kwargs)

    monkeypatch.setattr(os, "replace", fail_replace)
    assert (
        catalog._fetch_single_catalog(entry_cls(URL, "test", 1, False), True)
        == fetch[0]
    )
    assert path.read_text() == SENTINEL
    assert "Could not safely cache" in caplog.text
    assert "isolated replace failure" in caplog.text
    assert not list(path.parent.glob("*.tmp"))


def test_serialization_failure_preserves_existing_cache(tmp_path, catalog_kind):
    catalog_cls, *_ = catalog_kind
    path = catalog_cls(tmp_path)._get_cache_paths(URL)[0]
    path.parent.mkdir(parents=True)
    path.write_text(SENTINEL)

    with pytest.raises(TypeError):
        _catalog_cache.write_cache_json(tmp_path, path, {"invalid": object()})

    assert path.read_text() == SENTINEL
    assert not list(path.parent.glob("*.tmp"))


@pytest.mark.skipif(os.name != "nt", reason="Windows resolved-root cache regression")
def test_path_io_uses_pinned_directory_not_original_alias(tmp_path, catalog_kind):
    catalog_cls, *_ = catalog_kind
    root = tmp_path / "project"
    root.mkdir()
    alias = tmp_path / "original-alias"
    junction(alias, root)
    path = catalog_cls(alias)._get_cache_paths(URL)[0]
    _catalog_cache.write_cache_json(alias, path, {"safe": True})

    with _catalog_cache._cache_directory(alias, path.parent, create=False) as pinned:
        assert pinned == path.parent.resolve()
        assert pinned != path.parent
    assert _catalog_cache.read_cache_json(alias, path) == {"safe": True}
    assert json.loads(catalog_cls(root)._get_cache_paths(URL)[0].read_text()) == {
        "safe": True
    }


@pytest.mark.skipif(os.name != "nt", reason="Windows handle pinning regression")
@pytest.mark.parametrize("ancestor", [".specify", "workflows", "steps", ".cache"])
def test_windows_directory_handle_prevents_swap(tmp_path, catalog_kind, ancestor):
    catalog_cls, *_ = catalog_kind
    if catalog_cls is WorkflowCatalog and ancestor == "steps":
        pytest.skip("Workflow caches have no steps ancestor")
    catalog = catalog_cls(tmp_path)
    catalog.cache_dir.mkdir(parents=True)
    parts = catalog.cache_dir.relative_to(tmp_path).parts
    path = tmp_path.joinpath(*parts[: parts.index(ancestor) + 1])
    with (
        _catalog_cache._cache_directory(tmp_path, catalog.cache_dir, create=False),
        pytest.raises(OSError),
    ):
        path.rename(path.with_name("swapped"))

    path.rename(path.with_name("swapped"))


@pytest.mark.skipif(os.name != "nt", reason="Windows native file handle regression")
@pytest.mark.parametrize(
    ("kind", "directory", "allowed"),
    [
        ("directory", True, True),
        ("file", False, True),
        ("junction", True, False),
        ("symlink", False, False),
        ("file", True, False),
        ("directory", False, False),
    ],
)
def test_windows_handle_rejects_reparse_points_and_wrong_types(
    tmp_path,
    kind,
    directory,
    allowed,
):
    path = tmp_path / "path"
    if kind == "directory":
        path.mkdir()
    elif kind == "file":
        path.write_text(SENTINEL)
    elif kind == "junction":
        target = tmp_path / "target"
        target.mkdir()
        junction(path, target)
    else:
        target = tmp_path / "target"
        target.write_text(SENTINEL)
        symlink(path, target)

    if allowed:
        with _catalog_cache._windows_handle(path, directory=directory) as handle:
            assert handle is not None
            with pytest.raises(OSError):
                path.rename(path.with_name("renamed"))
        path.rename(path.with_name("renamed"))
    else:
        with (
            pytest.raises(OSError),
            _catalog_cache._windows_handle(
                path,
                directory=directory,
            ),
        ):
            pytest.fail("An unsafe Windows path was accepted")
        path.rename(path.with_name("renamed"))


@pytest.mark.skipif(os.name != "nt", reason="Windows native junction cache regression")
@pytest.mark.parametrize("ancestor", [".specify", "workflows", "steps", ".cache"])
def test_windows_junction_ancestor_cannot_redirect_write(
    tmp_path,
    catalog_kind,
    fetch,
    caplog,
    ancestor,
):
    catalog_cls, entry_cls, *_ = catalog_kind
    if catalog_cls is WorkflowCatalog and ancestor == "steps":
        pytest.skip("Workflow caches have no steps ancestor")
    root = tmp_path / "project"
    root.mkdir()
    catalog = catalog_cls(root)
    parts = catalog.cache_dir.relative_to(root).parts
    index = parts.index(ancestor)
    parent = root.joinpath(*parts[:index])
    parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    junction(parent / ancestor, outside)

    assert catalog._fetch_single_catalog(entry_cls(URL, "test", 1, False)) == fetch[0]
    assert list(outside.iterdir()) == []
    assert "Could not safely cache" in caplog.text


@pytest.mark.skipif(os.name == "nt", reason="POSIX capability refusal regression")
def test_unsupported_safe_io_continues_discovery_with_warning(
    tmp_path,
    catalog_kind,
    fetch,
    monkeypatch,
    caplog,
):
    catalog_cls, entry_cls, *_ = catalog_kind
    catalog = catalog_cls(tmp_path)
    monkeypatch.setattr(os, "supports_dir_fd", set())

    assert catalog._fetch_single_catalog(entry_cls(URL, "test", 1, False)) == fetch[0]
    assert not catalog.cache_dir.exists()
    assert "Safe catalog cache I/O is unsupported" in caplog.text
