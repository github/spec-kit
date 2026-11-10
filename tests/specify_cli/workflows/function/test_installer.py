"""Installer: validate, stage, publish and register without importing code."""

from __future__ import annotations

import os
import shutil
import sys
import threading

import pytest

from specify_cli.workflows.function import FunctionRegistry, WorkflowFunctionError
from specify_cli.workflows.function import installer

from .helpers import (
    functions_dir,
    install_dir,
    write_installed,
    write_package,
)


def install(project_dir, source, function_id="text", **kwargs):
    return installer.install_function_package(
        project_dir, function_id, source, source=kwargs.pop("kind", "local"), **kwargs
    )


@pytest.fixture
def source(tmp_path):
    return write_package(tmp_path / "src", "text")


def leftovers(project_dir):
    return [p.name for p in functions_dir(project_dir).iterdir() if p.name.startswith(".speckit")]


class TestInstall:
    def test_installs_files_and_registers_metadata(self, project_dir, source):
        (source / "helpers.py").write_text("X = 1\n")
        (source / "sub").mkdir()
        (source / "sub" / "data.txt").write_text("d")
        write_package(
            source, "text",
            [{"name": "pad", "handler": "trim", "min_args": 1, "max_args": 2,
              "description": "Pad"}],
            name="Text", version="1.0.0", description="Helpers",
        )
        entry = install(project_dir, source)

        target = install_dir(project_dir, "text")
        assert (target / "function.yml").is_file() and (target / "__init__.py").is_file()
        assert (target / "helpers.py").read_text() == "X = 1\n"
        assert (target / "sub" / "data.txt").read_text() == "d"
        assert entry == {
            "name": "Text", "version": "1.0.0", "description": "Helpers", "source": "local",
            "functions": [{"name": "pad", "handler": "trim", "min_args": 1,
                           "max_args": 2, "description": "Pad"}],
        }
        stored = FunctionRegistry(project_dir).get("text")
        assert {k: stored[k] for k in entry} == entry
        assert leftovers(project_dir) == []

    def test_name_defaults_to_id(self, project_dir, source):
        assert install(project_dir, source)["name"] == "text"

    def test_source_directory_is_left_untouched(self, project_dir, source):
        before = sorted(p.name for p in source.iterdir())
        install(project_dir, source)
        assert sorted(p.name for p in source.iterdir()) == before

    def test_never_imports_package_code(self, project_dir, tmp_path):
        marker = tmp_path / "imported"
        write_package(
            tmp_path / "src", "text",
            code=f"open({str(marker)!r}, 'w').close()\ndef trim(v):\n    return v\n",
        )
        install(project_dir, tmp_path / "src")
        installer.validate_function_package(tmp_path / "src", "text")
        assert not marker.exists()
        assert not [n for n in sys.modules if n.startswith("_speckit_workflow_function_")]

    def test_url_source_label(self, project_dir, source):
        assert install(project_dir, source, kind="url")["source"] == "url"

    @pytest.mark.parametrize("kind", ["", "catalog", "LOCAL", None])
    def test_unknown_source_kind_is_rejected(self, project_dir, source, kind):
        with pytest.raises(WorkflowFunctionError, match="'local' or 'url'"):
            install(project_dir, source, kind=kind)
        assert not install_dir(project_dir, "text").exists()

    def test_packages_with_disjoint_exports_coexist(self, project_dir, tmp_path):
        write_package(tmp_path / "a", "alpha", [{"name": "one", "handler": "trim"}])
        write_package(tmp_path / "b", "beta", [{"name": "two", "handler": "trim"}])
        install(project_dir, tmp_path / "a", "alpha")
        install(project_dir, tmp_path / "b", "beta")
        assert sorted(FunctionRegistry(project_dir).list()) == ["alpha", "beta"]


class TestReplacement:
    def test_existing_package_requires_force(self, project_dir, source):
        install(project_dir, source)
        with pytest.raises(WorkflowFunctionError, match="already installed. Remove it first with: specify workflow function remove text"):
            install(project_dir, source)

    def test_unregistered_leftover_directory_requires_force(self, project_dir, source):
        write_installed(project_dir, "text")
        FunctionRegistry(project_dir).remove("text")
        with pytest.raises(WorkflowFunctionError, match="Function directory already exists"):
            install(project_dir, source)

    def test_force_replaces_files_and_metadata(self, project_dir, tmp_path, source):
        (source / "old.py").write_text("")
        install(project_dir, source)
        installed_at = FunctionRegistry(project_dir).get("text")["installed_at"]

        new = write_package(
            tmp_path / "new", "text", [{"name": "pad", "handler": "trim"}], version="2.0.0"
        )
        install(project_dir, new, force=True)

        target = install_dir(project_dir, "text")
        assert not (target / "old.py").exists()
        entry = FunctionRegistry(project_dir).get("text")
        assert entry["version"] == "2.0.0" and [f["name"] for f in entry["functions"]] == ["pad"]
        assert entry["installed_at"] == installed_at
        assert leftovers(project_dir) == []

    def test_force_may_keep_the_same_export_names(self, project_dir, source):
        install(project_dir, source)
        install(project_dir, source, force=True)

    def test_force_on_a_fresh_install_succeeds(self, project_dir, source):
        install(project_dir, source, force=True)
        assert FunctionRegistry(project_dir).is_installed("text")


class TestExportCollisions:
    def test_builtin_name(self, project_dir, tmp_path):
        write_package(tmp_path / "s", "text", [{"name": "upper", "handler": "trim"}])
        with pytest.raises(WorkflowFunctionError, match="conflicts with a built-in filter"):
            install(project_dir, tmp_path / "s")
        assert not install_dir(project_dir, "text").exists()
        assert not FunctionRegistry(project_dir).is_installed("text")

    def test_other_package_name(self, project_dir, source, tmp_path):
        install(project_dir, source)
        write_package(tmp_path / "o", "other")
        with pytest.raises(WorkflowFunctionError, match="already provided by package 'text'"):
            install(project_dir, tmp_path / "o", "other")
        assert not install_dir(project_dir, "other").exists()

    def test_duplicate_name_within_one_manifest(self, project_dir, tmp_path):
        write_package(
            tmp_path / "s", "text",
            [{"name": "a", "handler": "trim"}, {"name": "a", "handler": "trim"}],
        )
        with pytest.raises(WorkflowFunctionError, match="more than once"):
            install(project_dir, tmp_path / "s")

    def test_force_cannot_claim_another_packages_export(self, project_dir, source, tmp_path):
        install(project_dir, source)
        write_package(tmp_path / "o", "other", [{"name": "mine", "handler": "trim"}])
        install(project_dir, tmp_path / "o", "other")
        write_package(tmp_path / "o2", "other")  # now claims text's 'trim'
        with pytest.raises(WorkflowFunctionError, match="already provided by package 'text'"):
            install(project_dir, tmp_path / "o2", "other", force=True)
        assert [f["name"] for f in FunctionRegistry(project_dir).get("other")["functions"]] == ["mine"]

    def test_locked_recheck_uses_fresh_registry_state(self, project_dir, source, tmp_path, monkeypatch):
        """A competing install that lands after the preflight is still caught."""
        real = installer._function_install_transaction

        class Racing:
            def __init__(self, root):
                self.inner = real(root)

            def __enter__(self):
                FunctionRegistry(project_dir).add(
                    "rival", {"functions": [{"name": "trim"}]}
                )
                return self.inner.__enter__()

            def __exit__(self, *exc):
                return self.inner.__exit__(*exc)

        monkeypatch.setattr(installer, "_function_install_transaction", Racing)
        with pytest.raises(WorkflowFunctionError, match="already provided by package 'rival'"):
            install(project_dir, source)
        assert not install_dir(project_dir, "text").exists()
        assert not FunctionRegistry(project_dir).is_installed("text")
        assert leftovers(project_dir) == []

    def test_concurrent_installs_claiming_one_name_allow_only_one(self, project_dir, tmp_path):
        sources = {
            package_id: write_package(tmp_path / package_id, package_id)
            for package_id in ("alpha", "beta", "gamma", "delta")
        }
        barrier = threading.Barrier(len(sources))
        results: dict[str, object] = {}

        def worker(package_id):
            barrier.wait()
            try:
                install(project_dir, sources[package_id], package_id)
                results[package_id] = "ok"
            except WorkflowFunctionError as exc:
                results[package_id] = exc

        threads = [threading.Thread(target=worker, args=(i,)) for i in sources]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        winners = [i for i, r in results.items() if r == "ok"]
        assert len(winners) == 1 and len(results) == len(sources)
        assert list(FunctionRegistry(project_dir).list()) == winners
        assert [p.name for p in functions_dir(project_dir).iterdir() if p.is_dir()] == winners
        assert all("already provided" in str(r) for i, r in results.items() if i not in winners)


class TestSharedInstallFlow:
    """The staged flow, copy and replacement are the step installer's mechanics."""

    def test_function_installer_delegates_to_the_shared_module(self):
        import inspect

        from specify_cli.workflows import _package_install

        assert "_package_install" in inspect.getsource(installer)
        assert installer._pi is _package_install

    def test_function_and_step_specs_share_the_same_derived_names(self):
        from specify_cli.workflows.step import installer as step_installer

        function_spec, step_spec = installer._function_spec(), step_installer._step_spec()
        assert function_spec.work_prefix == ".speckit-function-install-"
        assert step_spec.work_prefix == step_installer._WORK_DIR_PREFIX
        assert function_spec.lock_name == ".function-install.lock"
        assert (function_spec.directory, step_spec.directory) == ("functions", "steps")

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_symlink_swapped_in_after_validation_is_not_followed(
        self, project_dir, tmp_path, monkeypatch
    ):
        source = write_package(tmp_path / "s", "text")
        secret = tmp_path / "secret.txt"
        secret.write_text("TOP-SECRET")
        manifest = installer.validate_function_package(source, "text")
        # Simulate the swap: the source validates clean, then gains a symlink.
        calls = []

        def validate_then_swap(path, function_id):
            calls.append(path)
            if len(calls) == 1:
                (source / "leak.txt").symlink_to(secret)
            return manifest

        monkeypatch.setattr(installer, "validate_function_package", validate_then_swap)
        with pytest.raises(WorkflowFunctionError, match="contains symlink"):
            install(project_dir, source)
        assert not install_dir(project_dir, "text").exists()
        assert leftovers(project_dir) == []

    @pytest.mark.parametrize("name", ["__pycache__", ".git", ".DS_Store"])
    def test_excluded_names_are_not_installed_or_counted(self, project_dir, source, monkeypatch, name):
        monkeypatch.setattr(installer, "_MAX_FUNCTION_PACKAGE_FILES", 2)  # the two required files
        if name == ".DS_Store":
            (source / name).write_text("x")
        else:
            (source / name).mkdir()
            (source / name / "x").write_text("x")
        install(project_dir, source)
        assert not (install_dir(project_dir, "text") / name).exists()

    def test_locked_recheck_includes_case_insensitive_ids(self, project_dir, source, monkeypatch):
        real = installer._function_install_transaction

        class Racing:
            def __init__(self, root):
                self.inner = real(root)

            def __enter__(self):
                FunctionRegistry(project_dir).add("TEXT", {"functions": [{"name": "other"}]})
                return self.inner.__enter__()

            def __exit__(self, *exc):
                return self.inner.__exit__(*exc)

        monkeypatch.setattr(installer, "_function_install_transaction", Racing)
        with pytest.raises(WorkflowFunctionError, match="collides case-insensitively"):
            install(project_dir, source)
        assert not install_dir(project_dir, "text").exists()

    def test_staging_directory_is_removed_after_a_failed_install(self, project_dir, source):
        (source / "function.yml").write_text("id: text\nfunctions: []\n")
        with pytest.raises(WorkflowFunctionError):
            install(project_dir, source)
        assert not functions_dir(project_dir).exists() or leftovers(project_dir) == []

    def test_lock_failure_is_reported_as_a_function_error(self, project_dir, source, monkeypatch):
        from specify_cli import shared_infra

        def broken(*args, **kwargs):
            raise OSError("no lock")

        monkeypatch.setattr(shared_infra, "_exclusive_project_lock", broken)
        with pytest.raises(WorkflowFunctionError, match="Failed to acquire the function lock: no lock"):
            install(project_dir, source)
        assert not install_dir(project_dir, "text").exists()


class TestOnDiskClaims:
    """Names claimed by package directories count even without a registry entry."""

    def hand_copy(self, project_dir, package_id="alpha", name="trim", **kwargs):
        return write_installed(
            project_dir, package_id, [{"name": name, "handler": "trim"}], **kwargs
        )

    def test_unregistered_package_blocks_a_clashing_install(self, project_dir, source):
        self.hand_copy(project_dir)
        with pytest.raises(WorkflowFunctionError) as info:
            install(project_dir, source)
        assert "'trim' is already provided by package 'alpha'" in str(info.value)
        assert "found on disk, not in the registry" in str(info.value)
        assert not install_dir(project_dir, "text").exists()
        assert not FunctionRegistry(project_dir).is_installed("text")

    def test_registry_claim_is_reported_without_the_disk_note(self, project_dir, source, tmp_path):
        other = write_package(tmp_path / "o", "alpha")
        install(project_dir, other, "alpha")
        with pytest.raises(WorkflowFunctionError) as info:
            install(project_dir, source)
        assert "already provided by package 'alpha'" in str(info.value)
        assert "found on disk" not in str(info.value)

    def test_lost_registry_does_not_hide_installed_packages(self, project_dir, source, tmp_path):
        install(project_dir, write_package(tmp_path / "o", "alpha"), "alpha")
        (functions_dir(project_dir) / "function-registry.json").unlink()
        with pytest.raises(WorkflowFunctionError, match="found on disk"):
            install(project_dir, source)

    def test_disjoint_unregistered_package_does_not_block(self, project_dir, source):
        self.hand_copy(project_dir, name="other")
        install(project_dir, source)

    @pytest.mark.parametrize("breakage", ["invalid-manifest", "missing-init", "id-mismatch", "unreadable"])
    def test_packages_the_loader_would_skip_claim_nothing(self, project_dir, source, breakage):
        package = self.hand_copy(project_dir)
        if breakage == "invalid-manifest":
            (package / "function.yml").write_text("id: alpha\nfunctions: nope\n")
        elif breakage == "missing-init":
            (package / "__init__.py").unlink()
        elif breakage == "id-mismatch":
            write_package(package, "other", [{"name": "trim", "handler": "trim"}])
        else:
            (package / "function.yml").write_bytes(b"\xff\xfe")
        install(project_dir, source)

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_symlinked_package_claims_nothing(self, project_dir, source, tmp_path):
        real = write_package(tmp_path / "elsewhere", "alpha")
        functions_dir(project_dir).mkdir(parents=True)
        install_dir(project_dir, "alpha").symlink_to(real, target_is_directory=True)
        install(project_dir, source)

    def test_non_package_entries_are_ignored(self, project_dir, source):
        base = functions_dir(project_dir)
        (base / ".cache").mkdir(parents=True)
        (base / "stray.txt").write_text("x")
        (base / "empty").mkdir()
        install(project_dir, source)

    def test_force_does_not_conflict_with_the_package_being_replaced(self, project_dir, source):
        install(project_dir, source)
        FunctionRegistry(project_dir).remove("text")  # now on disk only
        install(project_dir, source, force=True)

    def test_force_still_cannot_claim_a_unregistered_neighbours_name(self, project_dir, source):
        install(project_dir, source)
        self.hand_copy(project_dir, "alpha", name="shout")
        replacement = write_package(
            source.parent / "new", "text", [{"name": "shout", "handler": "trim"}]
        )
        with pytest.raises(WorkflowFunctionError, match="package 'alpha'"):
            install(project_dir, replacement, force=True)
        assert [f["name"] for f in FunctionRegistry(project_dir).get("text")["functions"]] == ["trim"]

    def test_locked_recheck_sees_a_package_copied_in_after_the_preflight(
        self, project_dir, source, monkeypatch
    ):
        real = installer._function_install_transaction
        hand_copy = self.hand_copy

        class Racing:
            def __init__(self, root):
                self.inner = real(root)

            def __enter__(self):
                hand_copy(project_dir)
                return self.inner.__enter__()

            def __exit__(self, *exc):
                return self.inner.__exit__(*exc)

        monkeypatch.setattr(installer, "_function_install_transaction", Racing)
        with pytest.raises(WorkflowFunctionError, match="found on disk"):
            install(project_dir, source)
        assert not install_dir(project_dir, "text").exists()

    def test_cli_reports_the_disk_claim(self, project_dir, source, monkeypatch):
        from typer.testing import CliRunner

        from specify_cli import app

        self.hand_copy(project_dir)
        monkeypatch.chdir(project_dir)
        result = CliRunner().invoke(app, ["workflow", "function", "add", "text", "--dev", str(source)])
        assert result.exit_code == 1
        assert "found on disk, not in the registry" in " ".join(result.output.split())


class TestPackageValidation:
    @pytest.mark.parametrize("missing", ["function.yml", "__init__.py"])
    def test_required_root_files(self, project_dir, source, missing):
        (source / missing).unlink()
        with pytest.raises(WorkflowFunctionError, match=f"missing required file '{missing}'"):
            install(project_dir, source)

    def test_missing_source_directory(self, project_dir, tmp_path):
        with pytest.raises(WorkflowFunctionError, match="not found"):
            install(project_dir, tmp_path / "nope")

    def test_manifest_id_must_match(self, project_dir, source):
        with pytest.raises(WorkflowFunctionError, match="does not match"):
            install(project_dir, source, "other")

    def test_invalid_manifest(self, project_dir, source):
        (source / "function.yml").write_text("id: text\nfunctions: []\n")
        with pytest.raises(WorkflowFunctionError, match="non-empty list"):
            install(project_dir, source)

    @pytest.mark.parametrize("bad", [".cache", "function-registry.json", "../x", "a/b", ".hidden", ""])
    def test_invalid_and_reserved_ids(self, project_dir, source, bad):
        with pytest.raises(WorkflowFunctionError, match="function id"):
            install(project_dir, source, bad)

    def test_unreadable_manifest(self, project_dir, source):
        (source / "function.yml").write_bytes(b"\xff\xfe")
        with pytest.raises(WorkflowFunctionError, match="Invalid function.yml"):
            install(project_dir, source)

    def test_entry_count_limit(self, project_dir, source, monkeypatch):
        monkeypatch.setattr(installer, "_MAX_FUNCTION_PACKAGE_FILES", 3)
        for index in range(3):
            (source / f"f{index}.py").write_text("")
        with pytest.raises(WorkflowFunctionError, match="too many entries"):
            install(project_dir, source)
        assert not install_dir(project_dir, "text").exists()

    def test_size_limit(self, project_dir, source, monkeypatch):
        monkeypatch.setattr(installer, "_MAX_FUNCTION_PACKAGE_BYTES", 100)
        (source / "big.bin").write_bytes(b"x" * 200)
        with pytest.raises(WorkflowFunctionError, match="total size limit"):
            install(project_dir, source)

    def test_depth_limit(self, project_dir, source, monkeypatch):
        monkeypatch.setattr(installer, "_MAX_FUNCTION_PACKAGE_DEPTH", 2)
        (source / "a" / "b" / "c").mkdir(parents=True)
        with pytest.raises(WorkflowFunctionError, match="directory depth limit"):
            install(project_dir, source)

    def test_limits_allow_a_package_at_the_boundary(self, project_dir, source, monkeypatch):
        monkeypatch.setattr(installer, "_MAX_FUNCTION_PACKAGE_DEPTH", 2)
        (source / "a" / "b").mkdir(parents=True)
        install(project_dir, source)


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
class TestSymlinks:
    def test_symlinked_source_directory(self, project_dir, source, tmp_path):
        link = tmp_path / "link"
        link.symlink_to(source, target_is_directory=True)
        with pytest.raises(WorkflowFunctionError, match="symlinked package directory"):
            install(project_dir, link)

    @pytest.mark.parametrize("name", ["function.yml", "__init__.py"])
    def test_symlinked_required_file(self, project_dir, source, tmp_path, name):
        real = tmp_path / "real"
        shutil.move(source / name, real)
        (source / name).symlink_to(real)
        with pytest.raises(WorkflowFunctionError, match="must be a regular file, not a symlink"):
            install(project_dir, source)

    def test_symlinked_nested_file_or_directory(self, project_dir, source, tmp_path):
        outside = tmp_path / "outside.txt"
        outside.write_text("secret")
        (source / "link.txt").symlink_to(outside)
        with pytest.raises(WorkflowFunctionError, match="contains symlink"):
            install(project_dir, source)
        (source / "link.txt").unlink()
        (source / "dir").symlink_to(tmp_path, target_is_directory=True)
        with pytest.raises(WorkflowFunctionError, match="contains symlink"):
            install(project_dir, source)
        assert not install_dir(project_dir, "text").exists()

    @pytest.mark.parametrize("link", [".specify/workflows/functions"])
    def test_symlinked_functions_directory(self, project_dir, source, tmp_path, link):
        outside = tmp_path / "outside"
        outside.mkdir()
        (project_dir / link).symlink_to(outside, target_is_directory=True)
        with pytest.raises(WorkflowFunctionError, match="symlinked function directory"):
            install(project_dir, source)
        assert list(outside.iterdir()) == []

    def test_symlinked_destination(self, project_dir, source, tmp_path):
        functions_dir(project_dir).mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        install_dir(project_dir, "text").symlink_to(outside, target_is_directory=True)
        with pytest.raises(WorkflowFunctionError, match="through a symlinked path"):
            install(project_dir, source, force=True)
        assert list(outside.iterdir()) == []

    def test_functions_path_that_is_a_file(self, project_dir, source):
        functions_dir(project_dir).write_text("x")
        with pytest.raises(WorkflowFunctionError, match="not a directory"):
            install(project_dir, source)


class TestDestinationSafety:
    def test_source_inside_the_destination_is_rejected(self, project_dir):
        inside = write_installed(project_dir, "text")
        with pytest.raises(WorkflowFunctionError, match="resolves to the install destination"):
            install(project_dir, inside, force=True)
        assert (inside / "function.yml").is_file()

    def test_source_containing_the_destination_is_rejected(self, tmp_path):
        project = tmp_path / "src"
        write_package(project, "text")
        (project / ".specify" / "workflows").mkdir(parents=True)
        with pytest.raises(WorkflowFunctionError, match="resolves to the install destination"):
            install(project, project)

    def test_case_insensitive_id_collisions(self, project_dir, source, tmp_path):
        install(project_dir, source)
        write_package(tmp_path / "t", "Text", [{"name": "other", "handler": "trim"}])
        with pytest.raises(WorkflowFunctionError, match="collides case-insensitively"):
            install(project_dir, tmp_path / "t", "Text")

    def test_registry_failure_removes_the_published_package(self, project_dir, source, monkeypatch):
        def fail(self, function_id, metadata):
            raise OSError("disk full")

        monkeypatch.setattr(FunctionRegistry, "add", fail)
        with pytest.raises(WorkflowFunctionError, match="disk full"):
            install(project_dir, source)
        assert not install_dir(project_dir, "text").exists()
        assert leftovers(project_dir) == []


class TestResolvePackageRoot:
    def test_root_with_manifest(self, tmp_path):
        write_package(tmp_path, "text")
        assert installer.resolve_package_root(tmp_path) == tmp_path

    def test_single_top_level_directory(self, tmp_path):
        write_package(tmp_path / "pkg", "text")
        assert installer.resolve_package_root(tmp_path) == tmp_path / "pkg"

    @pytest.mark.parametrize("layout", ["empty", "two-dirs", "nested-no-manifest", "file-only"])
    def test_ambiguous_or_missing_manifest(self, tmp_path, layout):
        if layout == "two-dirs":
            write_package(tmp_path / "a", "a")
            write_package(tmp_path / "b", "b")
        elif layout == "nested-no-manifest":
            (tmp_path / "pkg").mkdir()
        elif layout == "file-only":
            (tmp_path / "x.txt").write_text("")
        with pytest.raises(WorkflowFunctionError, match="function.yml at its root"):
            installer.resolve_package_root(tmp_path)

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_symlinked_manifest_or_directory_is_not_a_package(self, tmp_path):
        real = write_package(tmp_path / "real", "text")
        root = tmp_path / "root"
        root.mkdir()
        (root / "pkg").symlink_to(real, target_is_directory=True)
        with pytest.raises(WorkflowFunctionError):
            installer.resolve_package_root(root)
