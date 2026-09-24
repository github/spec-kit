"""Domain-focused tests for the workflow step package installer."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from specify_cli.workflows.step import installer


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


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
def test_validate_package_rejects_symlink_in_excluded_dir(tmp_path):
    pkg = _write_package(tmp_path / "pkg")
    git_dir = pkg / ".git"
    git_dir.mkdir()
    (git_dir / "hook").symlink_to(pkg / "step.yml")
    with pytest.raises(installer.StepInstallError, match="symlink"):
        installer.validate_step_package(pkg, "my-step")


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

    # The excluded entries must not count against the file limit.
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
    assert "2-file limit" in str(exc.value)


def test_byte_limit_boundary(tmp_path, monkeypatch):
    pkg = _write_package(tmp_path / "pkg")
    total = (pkg / "step.yml").stat().st_size + (pkg / "__init__.py").stat().st_size
    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_BYTES", total)
    installer.validate_step_package(pkg, "my-step")

    monkeypatch.setattr(installer, "_MAX_STEP_PACKAGE_BYTES", total - 1)
    with pytest.raises(installer.StepInstallError) as exc:
        installer.validate_step_package(pkg, "my-step")
    assert "total size limit" in str(exc.value)


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
    assert (_steps_dir(project_dir) / "my-step" / "__init__.py").read_text(
        encoding="utf-8"
    ) == "# new\n"


def test_force_removal_failure_warns_reinstall(tmp_path, project_dir, monkeypatch):
    target = _steps_dir(project_dir) / "my-step"
    _write_package(target, init_body="# old\n")
    _register(project_dir, "my-step")
    new_pkg = _write_package(tmp_path / "pkg", init_body="# new\n")

    real_rmtree = installer.shutil.rmtree

    def _rmtree(path, *args, **kwargs):
        if Path(path) == target:
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

    def _replace(src, dst, *args, **kwargs):
        if Path(dst) == target:
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
