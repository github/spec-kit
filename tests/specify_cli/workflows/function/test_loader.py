"""Loader: discovery, import isolation, atomic registration, collisions."""

from __future__ import annotations

import os
import shutil
import sys

import pytest

from specify_cli.workflows.expressions import (
    BUILTIN_FILTERS,
    FILTER_TABLE,
    evaluate_expression,
)
from specify_cli.workflows.base import StepContext
from specify_cli.workflows.function import WorkflowFunctionError, load_workflow_functions
from specify_cli.workflows.function import loader as loader_module

from .helpers import functions_dir, install_dir, trim_export, write_installed

PREFIX = "_speckit_workflow_function_"


def synthetic_modules():
    return [name for name in sys.modules if name.startswith(PREFIX)]


def custom_filters():
    return sorted(set(FILTER_TABLE) - set(BUILTIN_FILTERS))


def run(template, **inputs):
    return evaluate_expression(template, StepContext(inputs=inputs))


class TestLoading:
    def test_no_functions_directory(self, project_dir):
        assert load_workflow_functions(project_dir) == []
        assert custom_filters() == [] and synthetic_modules() == []

    def test_loads_declared_callables_without_a_base_class(self, project_dir):
        write_installed(
            project_dir, "text",
            [trim_export(), {"name": "shout", "handler": "loud", "min_args": 0, "max_args": 1}],
            code=(
                "def trim(v):\n    return v.strip()\n"
                "def loud(v, suffix='!'):\n    return v.upper() + suffix\n"
                "def undeclared(v):\n    return 'never'\n"
            ),
        )
        assert load_workflow_functions(project_dir) == ["trim", "shout"]
        assert custom_filters() == ["shout", "trim"]
        assert run("{{ inputs.s | trim | shout('?') }}", s=" a ") == "A?"

    def test_handlers_may_be_any_callable(self, project_dir):
        write_installed(
            project_dir, "text",
            code="class Trim:\n    def __call__(self, v):\n        return v.strip()\n"
                 "trim = Trim()\n",
        )
        assert load_workflow_functions(project_dir) == ["trim"]
        assert run("{{ inputs.s | trim }}", s=" a ") == "a"

    def test_relative_imports_work(self, project_dir):
        package = write_installed(
            project_dir, "text", code="from .helpers import clean as trim\n"
        )
        (package / "helpers.py").write_text(
            "def clean(v):\n    return v.strip()\n", encoding="utf-8"
        )
        assert load_workflow_functions(project_dir) == ["trim"]
        assert run("{{ inputs.s | trim }}", s=" a ") == "a"

    def test_packages_with_same_internal_module_names_are_isolated(self, project_dir):
        for package_id, name, marker in (("one", "f1", "1"), ("two", "f2", "2")):
            package = write_installed(
                project_dir, package_id,
                [{"name": name, "handler": "f"}],
                code="from .helpers import f\n",
            )
            (package / "helpers.py").write_text(
                f"def f(v):\n    return {marker!r}\n", encoding="utf-8"
            )
        assert sorted(load_workflow_functions(project_dir)) == ["f1", "f2"]
        assert run("{{ inputs.s | f1 }}{{ inputs.s | f2 }}", s="x") == "12"

    def test_modules_use_synthetic_names_and_not_plain_imports(self, project_dir):
        write_installed(project_dir, "text")
        load_workflow_functions(project_dir)
        (name,) = synthetic_modules()
        assert name.startswith(f"{PREFIX}text_")
        assert "text" not in sys.modules

    def test_non_package_entries_are_ignored(self, project_dir):
        write_installed(project_dir, "text")
        (functions_dir(project_dir) / "function-registry.json").write_text("{}")
        (functions_dir(project_dir) / ".cache").mkdir()
        (functions_dir(project_dir) / "stray.txt").write_text("x")
        (functions_dir(project_dir) / "empty").mkdir()
        assert load_workflow_functions(project_dir) == ["trim"]

    def test_reload_for_another_project_replaces_functions_and_modules(self, tmp_path):
        project_a, project_b = tmp_path / "a", tmp_path / "b"
        write_installed(project_a, "text", code="def trim(v):\n    return 'a'\n")
        write_installed(
            project_b, "other", [{"name": "shout", "handler": "shout"}],
            code="def shout(v):\n    return 'b'\n",
        )
        assert load_workflow_functions(project_a) == ["trim"]
        assert run("{{ inputs.s | trim }}", s="") == "a"
        before = synthetic_modules()

        assert load_workflow_functions(project_b) == ["shout"]
        assert custom_filters() == ["shout"]
        assert not set(before) & set(synthetic_modules())
        with pytest.raises(ValueError, match="unknown filter 'trim'"):
            run("{{ inputs.s | trim }}", s="")

    def test_reload_after_removal_forgets_the_package(self, project_dir):
        write_installed(project_dir, "text")
        assert load_workflow_functions(project_dir) == ["trim"]
        shutil.rmtree(install_dir(project_dir, "text"))
        assert load_workflow_functions(project_dir) == []
        assert custom_filters() == [] and synthetic_modules() == []

    def test_reload_picks_up_changed_code(self, project_dir):
        write_installed(project_dir, "text", code="def trim(v):\n    return 'old'\n")
        load_workflow_functions(project_dir)
        write_installed(project_dir, "text", code="def trim(v):\n    return 'changed'\n")
        load_workflow_functions(project_dir)
        assert run("{{ inputs.s | trim }}", s="") == "changed"

    def test_reload_same_project_is_idempotent(self, project_dir):
        write_installed(project_dir, "text")
        assert load_workflow_functions(project_dir) == ["trim"]
        assert load_workflow_functions(project_dir) == ["trim"]
        assert len(synthetic_modules()) == 1


class TestBrokenPackages:
    """A broken package is skipped; healthy packages still load."""

    def healthy(self, project_dir):
        write_installed(project_dir, "good", [{"name": "ok", "handler": "ok"}],
                        code="def ok(v):\n    return 'ok'\n")

    def assert_only_healthy_loaded(self, project_dir):
        assert load_workflow_functions(project_dir) == ["ok"]
        assert custom_filters() == ["ok"]
        assert len(synthetic_modules()) == 1 and "good" in synthetic_modules()[0]

    def test_invalid_manifest(self, project_dir):
        self.healthy(project_dir)
        package = write_installed(project_dir, "bad")
        (package / "function.yml").write_text("id: bad\nfunctions: nope\n")
        self.assert_only_healthy_loaded(project_dir)

    def test_non_string_manifest_key_is_skipped_like_any_invalid_manifest(self, project_dir):
        self.healthy(project_dir)
        package = write_installed(project_dir, "bad")
        (package / "function.yml").write_text(
            "id: bad\n1: x\nb: y\nfunctions: [{name: bad, handler: trim}]\n"
        )
        self.assert_only_healthy_loaded(project_dir)

    def test_oversized_max_args_is_skipped_like_any_invalid_manifest(self, project_dir):
        self.healthy(project_dir)
        write_installed(
            project_dir, "bad", [{"name": "huge", "handler": "trim", "max_args": 10**9}]
        )
        self.assert_only_healthy_loaded(project_dir)

    def test_unreadable_manifest(self, project_dir):
        self.healthy(project_dir)
        package = write_installed(project_dir, "bad")
        (package / "function.yml").write_bytes(b"\xff\xfe\x00")
        self.assert_only_healthy_loaded(project_dir)

    def test_id_must_equal_directory_name(self, project_dir):
        self.healthy(project_dir)
        write_installed(project_dir, "bad", id="other")
        self.assert_only_healthy_loaded(project_dir)

    def test_missing_manifest_or_init(self, project_dir):
        self.healthy(project_dir)
        (write_installed(project_dir, "a") / "function.yml").unlink()
        (write_installed(project_dir, "b") / "__init__.py").unlink()
        self.assert_only_healthy_loaded(project_dir)

    def test_missing_handler(self, project_dir):
        self.healthy(project_dir)
        write_installed(project_dir, "bad", [{"name": "nope", "handler": "absent"}])
        self.assert_only_healthy_loaded(project_dir)

    def test_non_callable_handler(self, project_dir):
        self.healthy(project_dir)
        write_installed(project_dir, "bad", code="trim = 5\n")
        self.assert_only_healthy_loaded(project_dir)

    def test_import_failure_leaves_no_modules(self, project_dir):
        self.healthy(project_dir)
        package = write_installed(project_dir, "bad", code="from .helpers import x\n")
        (package / "helpers.py").write_text("raise RuntimeError('boom')\n")
        self.assert_only_healthy_loaded(project_dir)

    def test_import_failure_after_submodule_import_leaves_no_submodules(self, project_dir):
        self.healthy(project_dir)
        package = write_installed(
            project_dir, "bad", code="from . import helpers\nraise RuntimeError('late')\n"
        )
        (package / "helpers.py").write_text("X = 1\n")
        self.assert_only_healthy_loaded(project_dir)
        assert not [n for n in sys.modules if n.startswith(PREFIX) and "bad" in n]

    def test_syntax_error(self, project_dir):
        self.healthy(project_dir)
        write_installed(project_dir, "bad", code="def trim(:\n")
        self.assert_only_healthy_loaded(project_dir)

    def test_bad_second_handler_registers_nothing_from_that_package(self, project_dir):
        self.healthy(project_dir)
        write_installed(
            project_dir, "bad",
            [{"name": "first", "handler": "first"}, {"name": "second", "handler": "absent"}],
            code="def first(v):\n    return v\n",
        )
        self.assert_only_healthy_loaded(project_dir)

    def test_registration_failure_rolls_back_the_whole_package(self, project_dir, monkeypatch):
        write_installed(project_dir, "a_good", [{"name": "ok", "handler": "ok"}],
                        code="def ok(v):\n    return 'ok'\n")
        write_installed(
            project_dir, "b_bad",
            [{"name": "first", "handler": "f"}, {"name": "second", "handler": "f"}],
            code="def f(v):\n    return v\n",
        )
        write_installed(project_dir, "c_good", [{"name": "ok2", "handler": "ok"}],
                        code="def ok(v):\n    return 'ok2'\n")
        real = loader_module.register_custom_filter

        def flaky(name, *args):
            if name == "second":
                raise RuntimeError("injected")
            real(name, *args)

        monkeypatch.setattr(loader_module, "register_custom_filter", flaky)
        assert load_workflow_functions(project_dir) == ["ok", "ok2"]
        assert custom_filters() == ["ok", "ok2"]
        assert not [n for n in synthetic_modules() if "b_bad" in n]


class TestCollisions:
    """Collisions are fatal and detected before any package code runs."""

    def marker_code(self, project_dir, name):
        marker = project_dir / f"{name}.imported"
        return marker, f"open({str(marker)!r}, 'w').close()\ndef trim(v):\n    return v\n"

    def assert_clean(self):
        assert custom_filters() == [] and synthetic_modules() == []

    def test_package_shadowing_a_builtin(self, project_dir):
        marker, code = self.marker_code(project_dir, "shadow")
        write_installed(project_dir, "text", [{"name": "upper", "handler": "trim"}], code=code)
        with pytest.raises(WorkflowFunctionError) as info:
            load_workflow_functions(project_dir)
        message = str(info.value)
        assert "'upper'" in message and "built-in filters" in message
        assert "package 'text'" in message and "rename or remove" in message
        assert not marker.exists()
        self.assert_clean()
        assert FILTER_TABLE["upper"] is BUILTIN_FILTERS["upper"]

    def test_two_packages_providing_the_same_name(self, project_dir):
        marker_a, code_a = self.marker_code(project_dir, "a")
        marker_b, code_b = self.marker_code(project_dir, "b")
        write_installed(project_dir, "alpha", code=code_a)
        write_installed(project_dir, "beta", code=code_b)
        with pytest.raises(WorkflowFunctionError) as info:
            load_workflow_functions(project_dir)
        message = str(info.value)
        assert "'trim'" in message and "package 'alpha'" in message and "package 'beta'" in message
        assert not marker_a.exists() and not marker_b.exists()
        self.assert_clean()

    def test_every_builtin_shadow_in_one_package_is_reported(self, project_dir):
        marker, code = self.marker_code(project_dir, "multi")
        write_installed(
            project_dir, "text",
            [{"name": "upper", "handler": "trim"}, {"name": "lower", "handler": "trim"},
             {"name": "fine", "handler": "trim"}],
            code=code,
        )
        with pytest.raises(WorkflowFunctionError) as info:
            load_workflow_functions(project_dir)
        message = str(info.value)
        assert message == (
            "Workflow functions collide: 'upper' between built-in filters and package "
            "'text'; 'lower' between built-in filters and package 'text'; "
            "rename or remove the packages."
        )
        assert "'fine'" not in message and not marker.exists()
        self.assert_clean()

    def test_every_cross_package_clash_is_reported(self, project_dir):
        write_installed(
            project_dir, "alpha",
            [{"name": "trim", "handler": "trim"}, {"name": "pad", "handler": "trim"}],
        )
        write_installed(
            project_dir, "beta",
            [{"name": "pad", "handler": "trim"}, {"name": "trim", "handler": "trim"}],
        )
        with pytest.raises(WorkflowFunctionError) as info:
            load_workflow_functions(project_dir)
        message = str(info.value)
        assert "'pad' between package 'alpha' and package 'beta'" in message
        assert "'trim' between package 'alpha' and package 'beta'" in message
        self.assert_clean()

    def test_mixed_builtin_and_cross_package_clashes_are_reported_together(self, project_dir):
        write_installed(project_dir, "alpha")
        write_installed(
            project_dir, "beta",
            [{"name": "trim", "handler": "trim"}, {"name": "length", "handler": "trim"}],
        )
        with pytest.raises(WorkflowFunctionError) as info:
            load_workflow_functions(project_dir)
        message = str(info.value)
        assert "'trim' between package 'alpha' and package 'beta'" in message
        assert "'length' between built-in filters and package 'beta'" in message

    def test_three_packages_claiming_one_name_report_both_later_packages(self, project_dir):
        for package_id in ("alpha", "beta", "gamma"):
            write_installed(project_dir, package_id)
        with pytest.raises(WorkflowFunctionError) as info:
            load_workflow_functions(project_dir)
        message = str(info.value)
        assert "between package 'alpha' and package 'beta'" in message
        assert "between package 'alpha' and package 'gamma'" in message

    def test_message_order_is_deterministic(self, project_dir):
        write_installed(project_dir, "zeta", [{"name": "upper", "handler": "trim"}])
        write_installed(project_dir, "alpha", [{"name": "lower", "handler": "trim"}])
        messages = set()
        for _ in range(3):
            with pytest.raises(WorkflowFunctionError) as info:
                load_workflow_functions(project_dir)
            messages.add(str(info.value))
        (message,) = messages
        assert message.index("package 'alpha'") < message.index("package 'zeta'")

    def test_single_collision_keeps_the_singular_message(self, project_dir):
        write_installed(project_dir, "text", [{"name": "upper", "handler": "trim"}])
        with pytest.raises(WorkflowFunctionError) as info:
            load_workflow_functions(project_dir)
        assert str(info.value) == (
            "Workflow function 'upper' collides between built-in filters and package "
            "'text'; rename or remove the package."
        )

    def test_collision_wins_over_unrelated_broken_packages(self, project_dir):
        write_installed(project_dir, "alpha")
        write_installed(project_dir, "beta")
        write_installed(project_dir, "gamma", [{"name": "x", "handler": "absent"}])
        with pytest.raises(WorkflowFunctionError, match="collides"):
            load_workflow_functions(project_dir)

    def test_previous_project_state_is_cleared_when_the_next_load_collides(self, tmp_path):
        good, bad = tmp_path / "good", tmp_path / "bad"
        write_installed(good, "text")
        write_installed(bad, "text", [{"name": "upper", "handler": "trim"}])
        load_workflow_functions(good)
        with pytest.raises(WorkflowFunctionError):
            load_workflow_functions(bad)
        self.assert_clean()

    def test_invalid_manifest_does_not_claim_names(self, project_dir):
        write_installed(project_dir, "alpha")
        package = write_installed(project_dir, "beta")
        (package / "function.yml").write_text("id: beta\nfunctions: [bad")
        assert load_workflow_functions(project_dir) == ["trim"]


class TestFilesystemSafety:
    pytestmark = pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")

    @pytest.mark.parametrize("link", [".specify", ".specify/workflows", ".specify/workflows/functions"])
    def test_symlinked_parent_is_refused(self, project_dir, tmp_path, link):
        outside = tmp_path / "outside"
        write_installed(outside, "text")
        target = project_dir / link
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        if link.endswith("functions"):
            outside_dir = outside / ".specify" / "workflows" / "functions"
        else:
            outside_dir = outside / ".specify" if link == ".specify" else outside / ".specify" / "workflows"
        target.symlink_to(outside_dir, target_is_directory=True)
        with pytest.raises(WorkflowFunctionError, match="symlinked"):
            load_workflow_functions(project_dir)
        assert custom_filters() == [] and synthetic_modules() == []

    def test_symlinked_package_directory_is_skipped(self, project_dir, tmp_path):
        real = write_installed(tmp_path / "elsewhere", "text")
        (functions_dir(project_dir)).mkdir(parents=True, exist_ok=True)
        install_dir(project_dir, "text").symlink_to(real, target_is_directory=True)
        assert load_workflow_functions(project_dir) == []

    @pytest.mark.parametrize("name", ["function.yml", "__init__.py"])
    def test_symlinked_package_files_are_skipped(self, project_dir, tmp_path, name):
        package = write_installed(project_dir, "text")
        real = tmp_path / "real"
        shutil.move(package / name, real)
        (package / name).symlink_to(real)
        assert load_workflow_functions(project_dir) == []

    def test_functions_path_that_is_a_file_is_an_error(self, project_dir):
        functions_dir(project_dir).write_text("not a directory")
        with pytest.raises(WorkflowFunctionError, match="not a directory"):
            load_workflow_functions(project_dir)
