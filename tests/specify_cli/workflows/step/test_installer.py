"""Domain-focused tests for the workflow step package installer."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from specify_cli.workflows.step import installer
from tests.lock_helpers import watch_lock_attempt


def _write_package(
    package_dir: Path, type_key: str = "my-step", *, init_body: str = "# init\n"
) -> Path:
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "step.yml").write_text(
        f"step:\n  type_key: {type_key}\n  name: My Step\n  version: 0.1.0\n",
        encoding="utf-8",
    )
    (package_dir / "__init__.py").write_text(init_body, encoding="utf-8")
    return package_dir


def _steps_dir(project_dir: Path) -> Path:
    return project_dir / ".specify" / "workflows" / "steps"


def _register(project_dir: Path, step_id: str, **overrides) -> None:
    from specify_cli.workflows.step.catalog import StepRegistry

    entry = {
        "name": "My Step",
        "version": "0.1.0",
        "type_key": step_id,
        "source": "catalog",
        "catalog_name": "default",
    }
    entry.update(overrides)
    StepRegistry(project_dir).add(step_id, entry)


def _registry_entry(project_dir: Path, step_id: str) -> dict:
    path = _steps_dir(project_dir) / "step-registry.json"
    return json.loads(path.read_text(encoding="utf-8"))["steps"][step_id]


# ---------------------------------------------------------------------------
# Step id validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("step_id", ["my-step", "my_step", "step2", "a.b", "Step"])
def test_validate_step_id_accepts_normal(step_id):
    installer.validate_step_id(step_id)


@pytest.mark.parametrize(
    "step_id",
    [
        "",
        "   ",
        " padded",
        "padded ",
        "a/b",
        "a\\b",
        ".",
        "..",
        ".hidden",
        ".cache",
        "step-registry.json",
        "con",
        "nul",
        "com1",
        "a:b",
        "a*b",
        "a<b",
        "trail.",
        "trail ",
        "tab\there",
    ],
)
def test_validate_step_id_rejects_unsafe(step_id):
    with pytest.raises(installer.StepInstallError):
        installer.validate_step_id(step_id)


# ---------------------------------------------------------------------------
# Base directory resolution
# ---------------------------------------------------------------------------


def test_resolve_steps_base_dir_ok(project_dir):
    expected = (project_dir / ".specify" / "workflows" / "steps").resolve()
    assert installer.resolve_steps_base_dir(project_dir) == expected


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
@pytest.mark.parametrize("component", [[".specify"], [".specify", "workflows"], [".specify", "workflows", "steps"]])
def test_resolve_steps_base_dir_rejects_symlinked_component(tmp_path, component):
    root = tmp_path / "proj"
    root.mkdir()
    target = tmp_path / "outside"
    target.mkdir()

    link_parent = root
    for part in component[:-1]:
        link_parent = link_parent / part
        link_parent.mkdir(parents=True, exist_ok=True)
    (link_parent / component[-1]).symlink_to(target, target_is_directory=True)

    with pytest.raises(installer.StepInstallError, match="symlink"):
        installer.resolve_steps_base_dir(root)


def test_resolve_steps_base_dir_rejects_non_directory(tmp_path):
    root = tmp_path / "proj"
    (root / ".specify").mkdir(parents=True)
    (root / ".specify" / "workflows").write_text("not a dir", encoding="utf-8")

    with pytest.raises(installer.StepInstallError, match="not a directory"):
        installer.resolve_steps_base_dir(root)


# ---------------------------------------------------------------------------
# Package shape and metadata
# ---------------------------------------------------------------------------


def test_validate_package_returns_step_metadata(tmp_path):
    pkg = _write_package(tmp_path / "pkg")
    meta = installer.validate_step_package(pkg, "my-step")
    assert meta["type_key"] == "my-step"


@pytest.mark.parametrize("missing", ["step.yml", "__init__.py"])
def test_validate_package_requires_root_files(tmp_path, missing):
    pkg = _write_package(tmp_path / "pkg")
    (pkg / missing).unlink()
    with pytest.raises(installer.StepInstallError, match="missing required file"):
        installer.validate_step_package(pkg, "my-step")


def test_validate_package_rejects_nested_required_files(tmp_path):
    pkg = tmp_path / "pkg"
    nested = _write_package(pkg / "nested")
    assert (nested / "step.yml").is_file()
    with pytest.raises(installer.StepInstallError, match="missing required file"):
        installer.validate_step_package(pkg, "my-step")


@pytest.mark.parametrize("body", [b"[]", b"false", b"0", b"''", b"null", b"~", b"NULL"])
def test_validate_package_rejects_non_mapping_step_yml(tmp_path, body):
    pkg = _write_package(tmp_path / "pkg")
    (pkg / "step.yml").write_bytes(body)
    with pytest.raises(installer.StepInstallError, match="must be a YAML mapping"):
        installer.validate_step_package(pkg, "my-step")


def test_validate_package_rejects_non_mapping_step_field(tmp_path):
    pkg = _write_package(tmp_path / "pkg")
    (pkg / "step.yml").write_text("step: []\n", encoding="utf-8")
    with pytest.raises(installer.StepInstallError, match="'step' field must be a mapping"):
        installer.validate_step_package(pkg, "my-step")


@pytest.mark.parametrize("yaml_body", ["step:\n  name: x\n", "step:\n  type_key: ''\n"])
def test_validate_package_requires_type_key(tmp_path, yaml_body):
    pkg = _write_package(tmp_path / "pkg")
    (pkg / "step.yml").write_text(yaml_body, encoding="utf-8")
    with pytest.raises(installer.StepInstallError, match="type_key"):
        installer.validate_step_package(pkg, "my-step")


def test_validate_package_rejects_type_key_mismatch(tmp_path):
    pkg = _write_package(tmp_path / "pkg", type_key="other-step")
    with pytest.raises(installer.StepInstallError, match="does not match"):
        installer.validate_step_package(pkg, "my-step")


def test_validate_package_rejects_symlinked_root(tmp_path):
    pkg = _write_package(tmp_path / "pkg")
    link = tmp_path / "link"
    link.symlink_to(pkg, target_is_directory=True)
    with pytest.raises(installer.StepInstallError, match="symlinked package"):
        installer.validate_step_package(link, "my-step")


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
def test_validate_package_rejects_descendant_symlink(tmp_path):
    pkg = _write_package(tmp_path / "pkg")
    (pkg / "helper.py").symlink_to(pkg / "step.yml")
    with pytest.raises(installer.StepInstallError, match="symlink"):
        installer.validate_step_package(pkg, "my-step")


class _ScandirSpy:
    """Delegating ``os.scandir`` wrapper that records reads beneath *root*."""

    def __init__(self, root: Path, real=os.scandir):
        self.root = root
        self.real = real
        self.scanned: list[Path] = []
        self.entries_read: dict[Path, int] = {}

    def __call__(self, path=".", *args, **kwargs):
        iterator = self.real(path, *args, **kwargs)
        if not isinstance(path, (str, os.PathLike)):
            return iterator
        directory = Path(path)
        if directory != self.root and self.root not in directory.parents:
            return iterator
        self.scanned.append(directory)
        self.entries_read[directory] = 0
        spy = self

        class _Counting:
            def __iter__(self):
                for entry in iterator:
                    spy.entries_read[directory] += 1
                    yield entry

            def __enter__(self):
                return self

            def __exit__(self, *exc_info):
                iterator.close()

            def close(self):
                iterator.close()

        return _Counting()


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
def test_excluded_dirs_are_pruned_not_inspected(tmp_path, project_dir, monkeypatch):
    """Excluded subtrees are never entered, so their contents cannot fail
    validation or reach the installed package."""
    pkg = _write_package(tmp_path / "pkg")
    git_dir = pkg / ".git"
    git_dir.mkdir()
    (git_dir / "hook").symlink_to(pkg / "step.yml")
    deep = git_dir
    for _ in range(installer._MAX_STEP_PACKAGE_DEPTH + 2):
        deep = deep / "objects"
    deep.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (pkg / "__pycache__").symlink_to(outside, target_is_directory=True)

    spy = _ScandirSpy(pkg)
    monkeypatch.setattr(os, "scandir", spy)
    installer.install_step_package(project_dir, "my-step", pkg, source="local")

    assert not any(
        path == git_dir or git_dir in path.parents for path in spy.scanned
    )
    step_dir = _steps_dir(project_dir) / "my-step"
    assert (step_dir / "step.yml").is_file()
    assert not (step_dir / ".git").exists()
    assert not (step_dir / "__pycache__").exists()


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
def test_symlink_named_like_excluded_file_is_still_not_copied(tmp_path, project_dir):
    pkg = _write_package(tmp_path / "pkg")
    (pkg / ".DS_Store").symlink_to(pkg / "step.yml")
    installer.install_step_package(project_dir, "my-step", pkg, source="local")
    assert not (_steps_dir(project_dir) / "my-step" / ".DS_Store").exists()


def test_validation_stops_reading_oversized_directory(tmp_path, monkeypatch):
    """The entry ceiling bounds how many directory entries are read."""
    pkg = _write_package(tmp_path / "pkg")
    for index in range(50):
        (pkg / f"extra-{index:02}.py").write_text("x", encoding="utf-8")
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_FILES", 3)

    spy = _ScandirSpy(pkg)
    monkeypatch.setattr(os, "scandir", spy)
    with pytest.raises(installer.StepInstallError, match="3-entry limit"):
        installer.validate_step_package(pkg, "my-step")

    assert spy.entries_read[pkg] <= 4


def test_validation_budget_spans_directories(tmp_path, monkeypatch):
    """Entries already discovered elsewhere shrink the budget for later
    directories, so many moderately sized directories cannot evade it."""
    pkg = _write_package(tmp_path / "pkg")
    for name in ("a", "b", "c"):
        sub = pkg / name
        sub.mkdir()
        for index in range(20):
            (sub / f"f{index:02}.py").write_text("x", encoding="utf-8")
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_FILES", 10)

    spy = _ScandirSpy(pkg)
    monkeypatch.setattr(os, "scandir", spy)
    with pytest.raises(installer.StepInstallError, match="10-entry limit"):
        installer.validate_step_package(pkg, "my-step")

    assert sum(spy.entries_read.values()) <= 11


def test_copy_stops_reading_oversized_directory(tmp_path, monkeypatch):
    pkg = _write_package(tmp_path / "pkg")
    for index in range(50):
        (pkg / f"extra-{index:02}.py").write_text("x", encoding="utf-8")
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_FILES", 3)

    spy = _ScandirSpy(pkg)
    monkeypatch.setattr(os, "scandir", spy)
    with pytest.raises(installer.StepInstallError, match="3-entry limit"):
        installer._copy_package_tree(pkg, tmp_path / "staged")

    assert spy.entries_read[pkg] <= 4
    assert not any((tmp_path / "staged").iterdir())


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="mkfifo is unavailable")
def test_validate_package_rejects_special_file(tmp_path):
    pkg = _write_package(tmp_path / "pkg")
    os.mkfifo(pkg / "pipe")
    with pytest.raises(installer.StepInstallError, match="unsupported file"):
        installer.validate_step_package(pkg, "my-step")


def test_excludes_are_not_copied(tmp_path, project_dir, monkeypatch):
    pkg = _write_package(tmp_path / "pkg")
    (pkg / ".git").mkdir()
    (pkg / ".git" / "config").write_text("x", encoding="utf-8")
    (pkg / "__pycache__").mkdir()
    (pkg / "__pycache__" / "helper.pyc").write_text("x", encoding="utf-8")
    (pkg / ".DS_Store").write_text("x", encoding="utf-8")

    # The excluded entries must not count against the entry limit.
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_FILES", 2)
    installer.install_step_package(project_dir, "my-step", pkg, source="local")

    step_dir = _steps_dir(project_dir) / "my-step"
    assert not (step_dir / ".git").exists()
    assert not (step_dir / "__pycache__").exists()
    assert not (step_dir / ".DS_Store").exists()


def test_file_limit_boundary(tmp_path, monkeypatch):
    pkg = _write_package(tmp_path / "pkg")
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_FILES", 2)
    installer.validate_step_package(pkg, "my-step")

    (pkg / "extra.py").write_text("x", encoding="utf-8")
    with pytest.raises(installer.StepInstallError) as exc:
        installer.validate_step_package(pkg, "my-step")
    assert "2-entry limit" in str(exc.value)


def _nest_dirs(root: Path, depth: int) -> Path:
    current = root
    for _ in range(depth):
        current = current / "d"
    current.mkdir(parents=True)
    (current / "leaf.py").write_text("x", encoding="utf-8")
    return current


def test_directories_count_toward_file_limit(tmp_path, monkeypatch):
    pkg = _write_package(tmp_path / "pkg")
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_FILES", 3)
    (pkg / "empty-a").mkdir()
    installer.validate_step_package(pkg, "my-step")

    (pkg / "empty-b").mkdir()
    with pytest.raises(installer.StepInstallError) as exc:
        installer.validate_step_package(pkg, "my-step")
    assert "3-entry limit" in str(exc.value)


def test_depth_limit_boundary(tmp_path, monkeypatch):
    pkg = _write_package(tmp_path / "pkg")
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_DEPTH", 4)
    deepest = _nest_dirs(pkg, 4)
    installer.validate_step_package(pkg, "my-step")

    (deepest / "d").mkdir()
    with pytest.raises(installer.StepInstallError, match="4-level directory depth"):
        installer.validate_step_package(pkg, "my-step")


def test_default_depth_limit_rejects_deep_tree_without_recursion_error(tmp_path):
    pkg = _write_package(tmp_path / "pkg")
    _nest_dirs(pkg, installer._MAX_STEP_PACKAGE_DEPTH)
    installer.validate_step_package(pkg, "my-step")

    _nest_dirs(tmp_path / "deep", installer._MAX_STEP_PACKAGE_DEPTH + 1)
    deep = _write_package(tmp_path / "deep")
    with pytest.raises(installer.StepInstallError, match="directory depth limit"):
        installer.validate_step_package(deep, "my-step")


def test_copy_enforces_depth_limit_if_source_deepens_after_validation(
    tmp_path, monkeypatch
):
    pkg = _write_package(tmp_path / "pkg")
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_DEPTH", 4)
    deepest = _nest_dirs(pkg, 4)
    installer._copy_package_tree(pkg, tmp_path / "ok")
    assert (tmp_path / "ok" / "d" / "d" / "d" / "d" / "leaf.py").is_file()

    (deepest / "d").mkdir()
    with pytest.raises(installer.StepInstallError, match="4-level directory depth"):
        installer._copy_package_tree(pkg, tmp_path / "too-deep")


def test_copy_enforces_entry_limit_if_source_grows_after_validation(
    tmp_path, monkeypatch
):
    pkg = _write_package(tmp_path / "pkg")
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_FILES", 3)
    (pkg / "empty-a").mkdir()
    installer._copy_package_tree(pkg, tmp_path / "ok")

    (pkg / "empty-b").mkdir()
    with pytest.raises(installer.StepInstallError, match="3-entry limit"):
        installer._copy_package_tree(pkg, tmp_path / "too-many")


def test_byte_limit_boundary(tmp_path, monkeypatch):
    pkg = _write_package(tmp_path / "pkg")
    total = (pkg / "step.yml").stat().st_size + (pkg / "__init__.py").stat().st_size
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_BYTES", total)
    installer.validate_step_package(pkg, "my-step")

    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_BYTES", total - 1)
    with pytest.raises(installer.StepInstallError) as exc:
        installer.validate_step_package(pkg, "my-step")
    assert "total size limit" in str(exc.value)


def test_copy_enforces_byte_limit_if_source_grows_after_validation(
    tmp_path, project_dir, monkeypatch
):
    pkg = _write_package(tmp_path / "pkg", init_body="# init\n")
    original_bytes = sum(path.stat().st_size for path in pkg.iterdir())
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_BYTES", original_bytes)
    real_copy = installer._copy_regular_file
    grew_source = False
    copied_bytes: list[int] = []

    def _grow_then_copy(source, target, expected_mode, remaining_bytes):
        nonlocal grew_source
        if not grew_source:
            with open(source, "ab") as source_file:
                source_file.write(b"x")
            grew_source = True
        copied = real_copy(source, target, expected_mode, remaining_bytes)
        copied_bytes.append(copied)
        return copied

    monkeypatch.setattr(installer, "_copy_regular_file", _grow_then_copy)

    with pytest.raises(installer.StepInstallError, match="while staging"):
        installer.install_step_package(project_dir, "my-step", pkg, source="local")

    assert sum(copied_bytes) <= original_bytes
    assert not (_steps_dir(project_dir) / "my-step").exists()


def test_copy_accepts_exact_byte_limit(tmp_path, project_dir, monkeypatch):
    pkg = _write_package(tmp_path / "pkg", init_body="# init\n")
    total_bytes = sum(path.stat().st_size for path in pkg.iterdir())
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_BYTES", total_bytes)

    installer.install_step_package(project_dir, "my-step", pkg, source="local")

    installed = _steps_dir(project_dir) / "my-step"
    assert sum(path.stat().st_size for path in installed.iterdir()) == total_bytes


# ---------------------------------------------------------------------------
# Archive root resolution
# ---------------------------------------------------------------------------


def test_resolve_package_root_at_root(tmp_path):
    root = _write_package(tmp_path / "pkg")
    assert installer.resolve_package_root(root) == root


def test_resolve_package_root_single_nested_dir(tmp_path):
    root = tmp_path / "pkg"
    inner = _write_package(root / "inner")
    assert installer.resolve_package_root(root) == inner


def test_resolve_package_root_rejects_unrelated_siblings(tmp_path):
    root = tmp_path / "pkg"
    _write_package(root / "inner")
    (root / "README.md").write_text("x", encoding="utf-8")
    with pytest.raises(installer.StepInstallError, match="exactly one top-level"):
        installer.resolve_package_root(root)


def test_resolve_package_root_rejects_nested_dir_without_manifest(tmp_path):
    root = tmp_path / "pkg"
    (root / "inner").mkdir(parents=True)
    (root / "inner" / "helper.py").write_text("x", encoding="utf-8")
    with pytest.raises(installer.StepInstallError):
        installer.resolve_package_root(root)


# ---------------------------------------------------------------------------
# Destination guards
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
def test_rejects_symlinked_destination(tmp_path, project_dir):
    pkg = _write_package(tmp_path / "pkg")
    steps = _steps_dir(project_dir)
    steps.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (steps / "my-step").symlink_to(outside, target_is_directory=True)

    with pytest.raises(installer.StepInstallError, match="symlinked path"):
        installer.install_step_package(project_dir, "my-step", pkg, source="local")


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
def test_rejects_dangling_symlinked_destination(tmp_path, project_dir):
    pkg = _write_package(tmp_path / "pkg")
    steps = _steps_dir(project_dir)
    steps.mkdir(parents=True, exist_ok=True)
    (steps / "my-step").symlink_to(steps / "does-not-exist", target_is_directory=True)

    with pytest.raises(installer.StepInstallError, match="symlinked path"):
        installer.install_step_package(project_dir, "my-step", pkg, source="local")


def test_rejects_non_directory_destination(tmp_path, project_dir):
    pkg = _write_package(tmp_path / "pkg")
    steps = _steps_dir(project_dir)
    steps.mkdir(parents=True, exist_ok=True)
    (steps / "my-step").write_text("not a dir", encoding="utf-8")

    with pytest.raises(installer.StepInstallError, match="not a directory"):
        installer.install_step_package(project_dir, "my-step", pkg, source="local")


def test_rejects_source_equal_to_destination(project_dir):
    steps = _steps_dir(project_dir)
    pkg = _write_package(steps / "my-step")

    with pytest.raises(installer.StepInstallError, match="install destination"):
        installer.install_step_package(project_dir, "my-step", pkg, source="local")


def test_duplicate_install_rejected_without_force(tmp_path, project_dir):
    pkg = _write_package(tmp_path / "pkg")
    installer.install_step_package(project_dir, "my-step", pkg, source="local")

    with pytest.raises(installer.StepInstallError, match="already installed"):
        installer.install_step_package(project_dir, "my-step", pkg, source="local")


def test_force_rejects_casefolded_registered_id_collision(tmp_path, project_dir):
    from specify_cli.workflows.step.catalog import StepRegistry

    old_dir = _write_package(
        _steps_dir(project_dir) / "Foo", type_key="Foo", init_body="# old\n"
    )
    _register(project_dir, "Foo")
    replacement = _write_package(tmp_path / "replacement", type_key="foo")

    with pytest.raises(installer.StepInstallError, match="case-insensitively"):
        installer.install_step_package(
            project_dir, "foo", replacement, source="local", force=True
        )

    assert (old_dir / "__init__.py").read_text(encoding="utf-8") == "# old\n"
    assert set(StepRegistry(project_dir).list()) == {"Foo"}


def test_force_rejects_casefolded_orphan_directory_collision(
    tmp_path, project_dir, monkeypatch
):
    from pathlib import Path

    old_dir = _write_package(
        _steps_dir(project_dir) / "Foo", type_key="Foo", init_body="# old\n"
    )
    replacement = _write_package(tmp_path / "replacement", type_key="foo")
    destination = _steps_dir(project_dir) / "foo"
    real_exists = Path.exists
    real_samefile = Path.samefile

    # Simulate a case-insensitive filesystem while running on Linux: both
    # spellings resolve to the same destination even though they differ.
    monkeypatch.setattr(
        Path,
        "exists",
        lambda self: True if self == destination else real_exists(self),
    )
    real_is_dir = Path.is_dir
    monkeypatch.setattr(
        Path,
        "is_dir",
        lambda self: True if self == destination else real_is_dir(self),
    )
    monkeypatch.setattr(
        Path,
        "samefile",
        lambda self, other: (
            True
            if self == old_dir and other == destination
            else real_samefile(self, other)
        ),
    )

    with pytest.raises(installer.StepInstallError, match="case-insensitively"):
        installer.install_step_package(
            project_dir, "foo", replacement, source="local", force=True
        )

    assert (old_dir / "__init__.py").read_text(encoding="utf-8") == "# old\n"


def test_force_allows_exact_id_with_registered_package(tmp_path, project_dir):
    from specify_cli.workflows.step.catalog import StepRegistry

    pkg = _write_package(
        _steps_dir(project_dir) / "Foo", type_key="Foo", init_body="# old\n"
    )
    _register(project_dir, "Foo")
    replacement = _write_package(
        tmp_path / "replacement", type_key="Foo", init_body="# replacement\n"
    )

    installer.install_step_package(
        project_dir, "Foo", replacement, source="local", force=True
    )

    assert (pkg / "__init__.py").read_text(encoding="utf-8") == "# replacement\n"
    assert set(StepRegistry(project_dir).list()) == {"Foo"}


@pytest.mark.parametrize("force", [False, True])
def test_casefold_collision_guard_runs_for_force_and_regular_install(
    tmp_path, project_dir, monkeypatch, force
):
    class _Registry:
        def list(self):
            return {"Foo": {}}

        def is_installed(self, step_id):
            return step_id == "foo"

    steps_dir = _steps_dir(project_dir)
    steps_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(installer, "resolve_steps_base_dir", lambda _root: steps_dir)
    monkeypatch.setattr(installer, "_resolve_step_dir", lambda _base, _id: steps_dir / "foo")
    monkeypatch.setattr(installer, "_reject_unsafe_destination", lambda _path: None)
    monkeypatch.setattr(installer, "_reject_builtin_collision", lambda _step_id: None)
    monkeypatch.setattr(
        "specify_cli.workflows.step.catalog.StepRegistry",
        lambda _root: _Registry(),
    )
    pkg = _write_package(tmp_path / f"pkg-{force}", type_key="foo")

    with pytest.raises(installer.StepInstallError, match="case-insensitively"):
        installer.install_step_package(
            project_dir, "foo", pkg, source="local", force=force
        )


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def test_local_and_url_provenance_shapes(tmp_path, project_dir):
    local_pkg = _write_package(tmp_path / "local-pkg", type_key="local-step")
    installer.install_step_package(project_dir, "local-step", local_pkg, source="local")

    url_pkg = _write_package(tmp_path / "url-pkg", type_key="url-step")
    installer.install_step_package(project_dir, "url-step", url_pkg, source="url")

    local_entry = _registry_entry(project_dir, "local-step")
    assert local_entry["source"] == "local"
    assert "catalog_name" not in local_entry
    assert str(local_pkg) not in json.dumps(local_entry)

    url_entry = _registry_entry(project_dir, "url-step")
    assert url_entry["source"] == "url"
    assert "catalog_name" not in url_entry


def test_catalog_provenance_shape(tmp_path, project_dir):
    pkg = _write_package(tmp_path / "pkg", type_key="cat-step")
    installer.install_step_package(
        project_dir,
        "cat-step",
        pkg,
        source="catalog",
        catalog_name="default",
        catalog_metadata={
            "name": "Catalog Name",
            "version": "2.0.0",
            "description": "desc",
            "author": "author",
        },
    )

    entry = _registry_entry(project_dir, "cat-step")
    assert entry["source"] == "catalog"
    assert entry["catalog_name"] == "default"
    assert entry["name"] == "Catalog Name"
    assert entry["version"] == "2.0.0"
    assert entry["description"] == "desc"
    assert entry["author"] == "author"


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "2026-09-24"),
        ("version", "2026-09-24"),
        ("description", "2026-09-24"),
        ("author", "2026-09-24"),
    ],
)
def test_rejects_non_string_persisted_metadata_before_publication(
    tmp_path, project_dir, field, value
):
    pkg = _write_package(tmp_path / "pkg")
    (pkg / "step.yml").write_text(
        f"step:\n  type_key: my-step\n  {field}: {value}\n", encoding="utf-8"
    )

    with pytest.raises(installer.StepInstallError, match="must be a string"):
        installer.install_step_package(project_dir, "my-step", pkg, source="local")

    assert not (_steps_dir(project_dir) / "my-step").exists()


def test_rejects_unknown_source_before_creating_steps_dir(tmp_path, project_dir):
    pkg = _write_package(tmp_path / "pkg")

    with pytest.raises(installer.StepInstallError, match="source"):
        installer.install_step_package(project_dir, "my-step", pkg, source="unknown")

    assert not _steps_dir(project_dir).exists()


# ---------------------------------------------------------------------------
# Failure handling
# ---------------------------------------------------------------------------


def test_poisoned_init_is_not_imported(tmp_path, project_dir):
    pkg = _write_package(
        tmp_path / "pkg", init_body="raise RuntimeError('must not import')\n"
    )
    entry = installer.install_step_package(project_dir, "my-step", pkg, source="local")
    assert entry["type_key"] == "my-step"


def test_fresh_install_registry_failure_removes_directory(
    tmp_path, project_dir, monkeypatch
):
    from specify_cli.workflows.step.catalog import StepRegistry, StepValidationError

    pkg = _write_package(tmp_path / "pkg")

    def _boom(self, step_id, metadata):
        raise StepValidationError("disk full")

    monkeypatch.setattr(StepRegistry, "add", _boom)

    with pytest.raises(installer.StepInstallError):
        installer.install_step_package(project_dir, "my-step", pkg, source="local")

    assert not (_steps_dir(project_dir) / "my-step").exists()


def test_staging_validation_failure_preserves_old_install(
    tmp_path, project_dir, monkeypatch
):
    old_dir = _write_package(_steps_dir(project_dir) / "my-step", init_body="# old\n")
    assert old_dir.is_dir()
    _register(project_dir, "my-step")

    new_pkg = _write_package(tmp_path / "pkg", init_body="# new\n")

    real_validate = installer.validate_step_package
    calls = {"count": 0}

    def _validate(package_dir, step_id):
        calls["count"] += 1
        if calls["count"] >= 2:
            raise installer.StepInstallError("staged copy invalid")
        return real_validate(package_dir, step_id)

    monkeypatch.setattr(installer, "validate_step_package", _validate)

    with pytest.raises(installer.StepInstallError):
        installer.install_step_package(
            project_dir, "my-step", new_pkg, source="local", force=True
        )

    assert (_steps_dir(project_dir) / "my-step" / "__init__.py").read_text(
        encoding="utf-8"
    ) == "# old\n"


def test_uses_metadata_from_staged_copy(tmp_path, project_dir, monkeypatch):
    pkg = _write_package(tmp_path / "pkg")
    original_copy = installer._copy_package_tree

    def _copy_then_change(source, target):
        original_copy(source, target)
        (target / "step.yml").write_text(
            "step:\n  type_key: my-step\n  name: Staged Name\n", encoding="utf-8"
        )

    monkeypatch.setattr(installer, "_copy_package_tree", _copy_then_change)
    entry = installer.install_step_package(project_dir, "my-step", pkg, source="local")

    assert entry["name"] == "Staged Name"


def test_force_registry_failure_warns_reinstall(
    tmp_path, project_dir, monkeypatch
):
    from specify_cli.workflows.step.catalog import StepRegistry, StepValidationError

    _write_package(_steps_dir(project_dir) / "my-step", init_body="# old\n")
    _register(project_dir, "my-step")
    new_pkg = _write_package(tmp_path / "pkg", init_body="# new\n")

    def _boom(self, step_id, metadata):
        raise StepValidationError("disk full")

    monkeypatch.setattr(StepRegistry, "add", _boom)

    with pytest.raises(installer.StepInstallError) as exc:
        installer.install_step_package(
            project_dir, "my-step", new_pkg, source="local", force=True
        )
    assert "reinstall" in str(exc.value).lower()
    # The previous install stays registered even though its metadata was not
    # updated, so the message must not claim it is unregistered.
    assert "not registered" not in str(exc.value).lower()
    assert StepRegistry(project_dir).is_installed("my-step")
    assert (_steps_dir(project_dir) / "my-step" / "__init__.py").read_text(
        encoding="utf-8"
    ) == "# new\n"


def test_staging_cleanup_failure_warns_after_success(
    tmp_path, project_dir, monkeypatch
):
    pkg = _write_package(tmp_path / "pkg")
    real_rmtree = installer.shutil.rmtree
    residual_dirs: list[Path] = []

    def _rmtree(path, *args, **kwargs):
        path = Path(path)
        if path.name.startswith(installer._WORK_DIR_PREFIX):
            residual_dirs.append(path)
            raise OSError("cleanup blocked")
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(installer.shutil, "rmtree", _rmtree)
    try:
        with pytest.warns(
            UserWarning, match="Could not remove step staging directory"
        ):
            installer.install_step_package(project_dir, "my-step", pkg, source="local")
        assert (_steps_dir(project_dir) / "my-step").is_dir()
        assert len(residual_dirs) == 1 and residual_dirs[0].is_dir()
    finally:
        for residual_dir in residual_dirs:
            if residual_dir.exists():
                real_rmtree(residual_dir)


def test_staging_cleanup_failure_preserves_primary_error(
    tmp_path, project_dir, monkeypatch
):
    pkg = _write_package(tmp_path / "pkg")
    real_validate = installer.validate_step_package
    real_rmtree = installer.shutil.rmtree
    residual_dirs: list[Path] = []
    calls = 0

    def _validate(package_dir, step_id):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise installer.StepInstallError("primary staged validation failure")
        return real_validate(package_dir, step_id)

    def _rmtree(path, *args, **kwargs):
        path = Path(path)
        if path.name.startswith(installer._WORK_DIR_PREFIX):
            residual_dirs.append(path)
            raise OSError("cleanup blocked")
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(installer, "validate_step_package", _validate)
    monkeypatch.setattr(installer.shutil, "rmtree", _rmtree)
    try:
        with pytest.raises(
            installer.StepInstallError, match="primary staged validation failure"
        ) as exc:
            installer.install_step_package(
                project_dir, "my-step", pkg, source="local"
            )
        assert len(residual_dirs) == 1 and residual_dirs[0].is_dir()
        assert str(residual_dirs[0]) in exc.value.__notes__[0]
    finally:
        for residual_dir in residual_dirs:
            if residual_dir.exists():
                real_rmtree(residual_dir)


def test_force_removal_failure_warns_reinstall(tmp_path, project_dir, monkeypatch):
    target = _steps_dir(project_dir) / "my-step"
    _write_package(target, init_body="# old\n")
    _register(project_dir, "my-step")
    new_pkg = _write_package(tmp_path / "pkg", init_body="# new\n")

    real_rmtree = installer.shutil.rmtree
    # The installer operates on resolved paths (e.g. /private/var on macOS).
    resolved_target = target.resolve()

    def _rmtree(path, *args, **kwargs):
        if Path(path).resolve() == resolved_target:
            raise OSError("cannot remove")
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(installer.shutil, "rmtree", _rmtree)

    with pytest.raises(installer.StepInstallError) as exc:
        installer.install_step_package(
            project_dir, "my-step", new_pkg, source="local", force=True
        )
    assert "reinstall" in str(exc.value).lower()
    assert (target / "__init__.py").read_text(encoding="utf-8") == "# old\n"


def test_force_publication_failure_warns_reinstall(tmp_path, project_dir, monkeypatch):
    target = _steps_dir(project_dir) / "my-step"
    _write_package(target, init_body="# old\n")
    _register(project_dir, "my-step")
    new_pkg = _write_package(tmp_path / "pkg", init_body="# new\n")

    real_replace = installer.os.replace
    resolved_target = target.resolve()

    def _replace(src, dst, *args, **kwargs):
        if Path(dst).resolve() == resolved_target:
            raise OSError("rename failed")
        return real_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(installer.os, "replace", _replace)

    with pytest.raises(installer.StepInstallError) as exc:
        installer.install_step_package(
            project_dir, "my-step", new_pkg, source="local", force=True
        )
    assert "reinstall" in str(exc.value).lower()


def test_force_replaces_orphaned_directory(tmp_path, project_dir):
    orphan = _write_package(_steps_dir(project_dir) / "my-step", init_body="# old\n")
    assert orphan.is_dir()

    new_pkg = _write_package(tmp_path / "pkg", init_body="# new\n")
    installer.install_step_package(
        project_dir, "my-step", new_pkg, source="local", force=True
    )

    assert (_steps_dir(project_dir) / "my-step" / "__init__.py").read_text(
        encoding="utf-8"
    ) == "# new\n"


def test_no_backup_artifacts_after_force(tmp_path, project_dir):
    _write_package(_steps_dir(project_dir) / "my-step", init_body="# old\n")
    _register(project_dir, "my-step")
    new_pkg = _write_package(tmp_path / "pkg", init_body="# new\n")

    installer.install_step_package(
        project_dir, "my-step", new_pkg, source="local", force=True
    )

    names = sorted(path.name for path in _steps_dir(project_dir).iterdir())
    assert names == ["my-step", "step-registry.json"]


def _install_race_setup(tmp_path, project_dir, monkeypatch, *, force_b):
    """Drive two concurrent installs against the install lock.

    Installer A is paused inside the locked critical section while installer B
    is guaranteed to be blocked on the platform lock (its lock attempt has
    been observed). The caller resumes A via the returned ``release_a`` event,
    then joins both threads and inspects ``outcomes``.
    """
    import threading

    pkg_a = _write_package(tmp_path / "pkg-a", init_body="# a\n")
    pkg_b = _write_package(tmp_path / "pkg-b", init_body="# b\n")

    class Race:
        a_inside = threading.Event()
        release_a = threading.Event()
        b_attempted_lock: threading.Event
        b_inside_replace = threading.Event()
        outcomes: dict[str, Exception | None] = {}
        thread_a = None
        thread_b = None

    race = Race()
    real_replace = installer._replace_install

    def _replace(step_dir, staged_dir, registry, step_id, entry, *, force):
        if threading.current_thread().name == "installer-a":
            race.a_inside.set()
            if not race.release_a.wait(10):
                raise AssertionError("installer A was never released")
        else:
            race.b_inside_replace.set()
        return real_replace(
            step_dir, staged_dir, registry, step_id, entry, force=force
        )

    monkeypatch.setattr(installer, "_replace_install", _replace)
    race.b_attempted_lock = watch_lock_attempt(monkeypatch, "installer-b")

    def _install(label, pkg, force):
        try:
            installer.install_step_package(
                project_dir, "my-step", pkg, source="local", force=force
            )
        except Exception as exc:  # noqa: BLE001 - recorded for assertions
            race.outcomes[label] = exc
        else:
            race.outcomes[label] = None

    race.thread_a = threading.Thread(
        target=_install, args=("a", pkg_a, False), name="installer-a", daemon=True
    )
    race.thread_b = threading.Thread(
        target=_install, args=("b", pkg_b, force_b), name="installer-b", daemon=True
    )

    race.thread_a.start()
    assert race.a_inside.wait(10), "installer A never reached the critical section"
    race.thread_b.start()
    assert race.b_attempted_lock.wait(10), "installer B never attempted the lock"
    return race


def _finish_race(race):
    race.release_a.set()
    race.thread_a.join(timeout=10)
    race.thread_b.join(timeout=10)
    assert not race.thread_a.is_alive()
    assert not race.thread_b.is_alive()


def test_install_lock_blocks_concurrent_duplicate(tmp_path, project_dir, monkeypatch):
    """A second install of the same id waits for the lock and sees A's commit.

    B can never enter the swap while A holds it; once A commits, B reloads the
    registry inside the lock and fails as a duplicate instead of overwriting.
    """
    race = _install_race_setup(tmp_path, project_dir, monkeypatch, force_b=False)
    # A holds the lock, so B cannot have reached the directory swap.
    assert not race.b_inside_replace.is_set()

    _finish_race(race)

    assert race.outcomes["a"] is None
    assert isinstance(race.outcomes["b"], installer.StepInstallError)
    assert "already installed" in str(race.outcomes["b"])
    # B never swapped, so A's install is intact.
    assert not race.b_inside_replace.is_set()
    assert (_steps_dir(project_dir) / "my-step" / "__init__.py").read_text(
        encoding="utf-8"
    ) == "# a\n"
    assert _registry_entry(project_dir, "my-step")["source"] == "local"


def test_install_lock_serializes_force_replace(tmp_path, project_dir, monkeypatch):
    """A forced install swaps only after the lock is released by the first."""
    race = _install_race_setup(tmp_path, project_dir, monkeypatch, force_b=True)
    # B is blocked on the lock and has not swapped A's package yet.
    assert not race.b_inside_replace.is_set()

    _finish_race(race)

    assert race.outcomes["a"] is None
    assert race.outcomes["b"] is None
    # B reached the swap only after A committed, and its package won.
    assert race.b_inside_replace.is_set()
    assert (_steps_dir(project_dir) / "my-step" / "__init__.py").read_text(
        encoding="utf-8"
    ) == "# b\n"
    assert _registry_entry(project_dir, "my-step")["type_key"] == "my-step"


def test_loader_does_not_discover_staging_package(project_dir):
    from specify_cli.workflows import load_custom_steps

    staging = _steps_dir(project_dir) / ".speckit-step-install-abc" / "staged"
    _write_package(staging, type_key="staged-only-step")

    loaded = load_custom_steps(project_dir)
    assert "staged-only-step" not in loaded


def test_builtin_collision_uses_immutable_snapshot(tmp_path, project_dir, monkeypatch):
    from specify_cli.workflows import BUILTIN_STEP_TYPES, STEP_REGISTRY

    monkeypatch.delitem(STEP_REGISTRY, "shell", raising=False)
    assert "shell" in BUILTIN_STEP_TYPES

    pkg = _write_package(tmp_path / "pkg", type_key="shell")
    with pytest.raises(installer.StepInstallError, match="built-in"):
        installer.install_step_package(project_dir, "shell", pkg, source="local")


def test_check_installable_exposes_duplicate_before_install(tmp_path, project_dir):
    pkg = _write_package(tmp_path / "pkg")
    installer.check_installable(project_dir, "my-step")
    installer.install_step_package(project_dir, "my-step", pkg, source="local")

    with pytest.raises(installer.StepInstallError, match="already installed"):
        installer.check_installable(project_dir, "my-step")
    # force permits the preflight.
    installer.check_installable(project_dir, "my-step", force=True)


def _tree(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_all_sources_share_tree_and_metadata(tmp_path):
    pkg = _write_package(tmp_path / "pkg", type_key="parity-step")
    expected_tree = _tree(pkg)

    entries: dict[str, dict] = {}
    trees: dict[str, dict] = {}
    for source in ("catalog", "local", "url"):
        project = tmp_path / f"proj-{source}"
        project.mkdir()
        entries[source] = installer.install_step_package(
            project,
            "parity-step",
            pkg,
            source=source,
            catalog_name="default" if source == "catalog" else "",
            catalog_metadata={"name": "Parity"} if source == "catalog" else None,
        )
        trees[source] = _tree(_steps_dir(project) / "parity-step")

    assert trees["catalog"] == trees["local"] == trees["url"] == expected_tree

    for source, entry in entries.items():
        assert entry["source"] == source
        assert entry["type_key"] == "parity-step"
        if source == "catalog":
            assert entry["catalog_name"] == "default"
        else:
            assert "catalog_name" not in entry


def test_all_sources_share_identity_rejection(tmp_path):
    pkg = _write_package(tmp_path / "pkg", type_key="wrong-step")
    for index, source in enumerate(("catalog", "local", "url")):
        project = tmp_path / f"proj-{index}"
        project.mkdir()
        with pytest.raises(installer.StepInstallError, match="does not match"):
            installer.install_step_package(
                project, "parity-step", pkg, source=source
            )
