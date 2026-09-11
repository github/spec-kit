"""Real custom packages under controlled cross-project interleavings."""
from __future__ import annotations

import importlib.util
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest

from specify_cli.workflows import STEP_REGISTRY, load_custom_steps
from specify_cli.workflows.base import StepBase
from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine


@pytest.fixture
def projects(tmp_path):
    import sys

    original_registry = dict(STEP_REGISTRY)
    original_modules = set(sys.modules)
    roots = [tmp_path / "project-a", tmp_path / "project-b"]
    for root in roots:
        package = root / ".specify/workflows/steps/shared"
        package.mkdir(parents=True)
        (package / "step.yml").write_text(
            "step:\n  type_key: shared\n  version: '1.0.0'\n", encoding="utf-8"
        )
        (package / "helper.py").write_text(
            f"PROJECT = {root.name!r}\n", encoding="utf-8"
        )
        (package / "__init__.py").write_text(
            "from specify_cli.workflows.base import StepBase, StepResult\n"
            "class SharedStep(StepBase):\n"
            "    type_key = 'shared'\n"
            f"    project_marker = {root.name!r}\n"
            "    def execute(self, config, context):\n"
            "        from .helper import PROJECT\n"
            "        return StepResult(output={'project': PROJECT})\n",
            encoding="utf-8",
        )
    yield roots
    STEP_REGISTRY.clear()
    STEP_REGISTRY.update(original_registry)
    for name in set(sys.modules) - original_modules:
        if name.startswith("_speckit_custom_step_"):
            sys.modules.pop(name, None)


def definition(steps=None):
    return WorkflowDefinition({
        "schema_version": "1.0",
        "workflow": {"id": "scoped", "name": "Scoped", "version": "1.0.0"},
        "steps": steps or [{"id": "custom", "type": "shared"}],
    })


def test_concurrent_scans_cannot_register_another_projects_class(projects, monkeypatch):
    project_a, project_b = projects
    first_import = Event()
    second_import = Event()
    release_first = Event()
    make_module = importlib.util.module_from_spec

    def pause_first_import(spec):
        module = make_module(spec)
        if spec.origin == str(project_a / ".specify/workflows/steps/shared/__init__.py"):
            first_import.set()
            assert release_first.wait(10)
        elif spec.origin == str(project_b / ".specify/workflows/steps/shared/__init__.py"):
            second_import.set()
        return module

    monkeypatch.setattr(importlib.util, "module_from_spec", pause_first_import)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(WorkflowEngine(project_a).execute, definition())
        try:
            assert first_import.wait(10)
            second = pool.submit(WorkflowEngine(project_b).execute, definition())
            # A serialized importer cannot reach B until A is released.
            if second_import.wait(1):
                second.result(timeout=10)
        finally:
            release_first.set()
        first_state = first.result(timeout=10)
        second_state = second.result(timeout=10)
    assert first_state.step_results["custom"]["output"]["project"] == "project-a"
    assert second_state.step_results["custom"]["output"]["project"] == "project-b"


def test_running_step_retains_its_relative_imports_after_another_project_loads(
    projects, monkeypatch
):
    project_a, project_b = projects
    ready = Event()
    release = Event()
    execute_steps = WorkflowEngine._execute_steps

    def pause_before_execution(self, *args, **kwargs):
        if self.project_root == project_a:
            ready.set()
            assert release.wait(10)
        return execute_steps(self, *args, **kwargs)

    monkeypatch.setattr(WorkflowEngine, "_execute_steps", pause_before_execution)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(WorkflowEngine(project_a).execute, definition())
        try:
            assert ready.wait(10)
            second = WorkflowEngine(project_b).execute(definition())
        finally:
            release.set()
        first_state = first.result(timeout=10)
    assert first_state.step_results["custom"]["output"]["project"] == "project-a"
    assert second.step_results["custom"]["output"]["project"] == "project-b"


def test_validation_retains_registry_for_nested_steps_after_project_switch(
    projects, monkeypatch, tmp_path
):
    project_a, _ = projects
    ready = Event()
    release = Event()
    validate = StepBase.validate

    def pause_first_validation(self, config):
        if self.type_key == "shared" and config["id"] == "first":
            ready.set()
            assert release.wait(10)
        return validate(self, config)

    monkeypatch.setattr(StepBase, "validate", pause_first_validation)
    workflow = definition([
        {"id": "first", "type": "shared"},
        {"id": "branch", "type": "if", "condition": "true",
         "then": [{"id": "second", "type": "shared"}]},
    ])
    with ThreadPoolExecutor(max_workers=1) as pool:
        result = pool.submit(WorkflowEngine(project_a).validate, workflow)
        try:
            assert ready.wait(10)
            load_custom_steps(tmp_path / "empty")
        finally:
            release.set()
        assert result.result(timeout=10) == []


def test_failed_cache_deletion_skips_stale_package(projects, monkeypatch):
    import shutil

    project_a, _ = projects
    package = project_a / ".specify/workflows/steps/shared"
    helper = package / "helper.py"
    assert load_custom_steps(project_a) == ["shared"]
    STEP_REGISTRY["shared"].execute({}, None)
    original_stat = helper.stat()
    helper.write_text("PROJECT = 'project-b'\n", encoding="utf-8")
    os.utime(helper, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    remove_tree = shutil.rmtree

    def deny_cache_removal(path, *args, **kwargs):
        if Path(path) == package / "__pycache__":
            if kwargs.get("ignore_errors"):
                return
            raise PermissionError("cache deletion denied")
        return remove_tree(path, *args, **kwargs)

    monkeypatch.setattr(shutil, "rmtree", deny_cache_removal)
    assert load_custom_steps(project_a) == []
    assert "shared" not in STEP_REGISTRY


def test_reloading_keeps_live_packages_and_unloads_released_packages(projects):
    import gc
    import sys

    project_a, project_b = projects
    load_custom_steps(project_a)
    first_step = STEP_REGISTRY["shared"]
    first_module = type(first_step).__module__
    load_custom_steps(project_b)
    assert first_step.execute({}, None).output["project"] == "project-a"
    del first_step
    gc.collect()
    assert first_module not in sys.modules
    assert not any(name.startswith(first_module + ".") for name in sys.modules)


def test_symlinked_cache_is_not_used_when_it_cannot_be_invalidated(projects):
    project_a, _ = projects
    package = project_a / ".specify/workflows/steps/shared"
    assert load_custom_steps(project_a) == ["shared"]
    cache = package / "__pycache__"
    external = project_a.parent / "external-cache"
    cache.rename(external)
    cache.symlink_to(external, target_is_directory=True)
    assert load_custom_steps(project_a) == []
    assert "shared" not in STEP_REGISTRY
    assert external.is_dir()


@pytest.fixture
def external_bytecode_cache(projects, monkeypatch):
    import sys

    project_a, _ = projects
    prefix = project_a.parent / "bytecode"
    monkeypatch.setattr(sys, "pycache_prefix", str(prefix))
    package = project_a / ".specify/workflows/steps/shared"
    assert load_custom_steps(project_a) == ["shared"]
    assert STEP_REGISTRY["shared"].execute({}, None).output["project"] == "project-a"
    for name in ("__init__.py", "helper.py"):
        cache = Path(importlib.util.cache_from_source(str(package / name)))
        assert cache.is_relative_to(prefix)
        assert cache.is_file()
    assert not (package / "__pycache__").exists()
    return project_a, package, prefix


def test_external_caches_are_invalidated_for_package_and_delayed_imports(
    external_bytecode_cache,
):
    project, package, prefix = external_bytecode_cache
    unrelated = prefix / "unrelated.pyc"
    unrelated.write_bytes(b"unrelated cache")
    for name in ("__init__.py", "helper.py"):
        source = package / name
        stat = source.stat()
        original = source.read_text(encoding="utf-8")
        updated = original.replace("project-a", "project-b")
        assert updated != original and len(updated) == len(original)
        source.write_text(updated, encoding="utf-8")
        os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns))

    assert load_custom_steps(project) == ["shared"]
    assert STEP_REGISTRY["shared"].project_marker == "project-b"
    assert STEP_REGISTRY["shared"].execute({}, None).output["project"] == "project-b"
    assert unrelated.read_bytes() == b"unrelated cache"


@pytest.mark.parametrize("source_name", ["__init__.py", "helper.py"])
def test_failed_external_cache_deletion_skips_package(
    external_bytecode_cache, monkeypatch, source_name,
):
    project, package, _ = external_bytecode_cache
    cache = Path(importlib.util.cache_from_source(str(package / source_name)))
    unlink = Path.unlink

    def deny_cache_removal(path, *args, **kwargs):
        if path == cache:
            raise PermissionError("external cache deletion denied")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", deny_cache_removal)
    assert load_custom_steps(project) == []
    assert "shared" not in STEP_REGISTRY
