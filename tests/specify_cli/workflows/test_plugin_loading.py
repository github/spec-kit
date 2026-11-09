"""Run, resume, add and update load project functions before using expressions."""

from __future__ import annotations

import json
import sys

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows.expressions import BUILTIN_FILTERS, FILTER_TABLE

from tests.specify_cli.workflows.function.helpers import install_dir, write_installed

pytestmark = pytest.mark.usefixtures("reset_custom_functions")

COLLIDING = [{"name": "upper", "handler": "trim"}]


def custom_filters():
    return sorted(set(FILTER_TABLE) - set(BUILTIN_FILTERS))


def python_run(project_dir, name, body, *args):
    """A shell ``run`` executing *body* with this interpreter.

    The shell step runs through the platform shell (``cmd.exe`` on Windows), so
    fixtures avoid POSIX utilities and ``;`` chaining and use double quotes only.
    """
    script = project_dir / name
    script.write_text(body, encoding="utf-8")
    quoted = "".join(f' "{arg}"' for arg in args)
    return f'"{sys.executable}" "{script}"{quoted}'


def workflow_yaml(steps, workflow_id="fn-wf", inputs=None):
    data = {
        "schema_version": "1.0",
        "workflow": {"id": workflow_id, "name": "Fn", "version": "1.0.0"},
        "steps": steps,
    }
    if inputs:
        data["inputs"] = inputs
    return yaml.safe_dump(data)


@pytest.fixture
def cli(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)
    runner = CliRunner()  # stdout and stderr are captured separately
    return lambda *args, **kw: runner.invoke(app, ["workflow", *args], **kw)


@pytest.fixture
def trim_wf(project_dir):
    path = project_dir / "wf.yml"
    path.write_text(
        workflow_yaml(
            [{
                "id": "w", "type": "shell",
                "run": python_run(
                    project_dir, "write_out.py",
                    "import sys\nopen('out.txt', 'w').write(sys.argv[1])\n",
                    "{{ inputs.s | trim }}",
                ),
            }],
            inputs={"s": {"type": "string", "default": "  hi  "}},
        ),
        encoding="utf-8",
    )
    return path


class TestRun:
    def test_functions_are_available_to_the_run(self, cli, project_dir, trim_wf):
        write_installed(project_dir, "text")
        result = cli("run", str(trim_wf), "--json")
        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout)["status"] == "completed"
        assert (project_dir / "out.txt").read_text() == "hi"

    def test_unknown_filter_fails_the_run_without_the_package(self, cli, project_dir, trim_wf):
        result = cli("run", str(trim_wf), "--json")
        assert result.exit_code != 0
        assert not (project_dir / "out.txt").exists()

    def test_collision_text_mode(self, cli, project_dir, trim_wf):
        write_installed(project_dir, "text", COLLIDING)
        result = cli("run", str(trim_wf))
        assert result.exit_code == 1
        assert "collides" in result.output and "'upper'" in result.output
        assert "rename or remove the package" in result.output
        assert not (project_dir / "out.txt").exists()

    def test_collision_json_mode(self, cli, project_dir, trim_wf):
        write_installed(project_dir, "text", COLLIDING)
        result = cli("run", str(trim_wf), "--json")
        assert result.exit_code == 1
        payload = json.loads(result.stdout)
        assert payload["status"] == "failed" and "collides" in payload["error"]
        assert not (project_dir / "out.txt").exists()

    def test_import_time_output_does_not_contaminate_json(self, cli, project_dir, trim_wf):
        write_installed(
            project_dir, "text",
            code="print('IMPORT-TIME-NOISE')\ndef trim(v):\n    return v.strip()\n",
        )
        result = cli("run", str(trim_wf), "--json")
        assert result.exit_code == 0, result.output
        assert "IMPORT-TIME-NOISE" not in result.stdout
        assert json.loads(result.stdout)["status"] == "completed"

    def test_broken_package_does_not_block_the_run(self, cli, project_dir, trim_wf):
        write_installed(project_dir, "text")
        write_installed(project_dir, "broken", [{"name": "x", "handler": "absent"}])
        assert cli("run", str(trim_wf), "--json").exit_code == 0


class TestResume:
    @pytest.fixture
    def failing_wf(self, project_dir):
        calls = project_dir / "calls.txt"
        write_installed(
            project_dir, "count",
            [{"name": "mark", "handler": "mark"}],
            code=(
                "def mark(value):\n"
                f"    with open({str(calls)!r}, 'a') as handle:\n"
                "        handle.write('x')\n"
                "    return value\n"
            ),
        )
        path = project_dir / "wf.yml"
        path.write_text(
            workflow_yaml(
                [
                    {"id": "done", "type": "shell", "run": "echo {{ inputs.s | mark }}"},
                    {
                        "id": "broken", "type": "shell",
                        "run": python_run(
                            project_dir, "fail.py", "raise SystemExit(1)\n", "{{ inputs.s | mark }}"
                        ),
                    },
                ],
                inputs={"s": {"type": "string", "default": "v"}},
            ),
            encoding="utf-8",
        )
        return path, calls

    def start(self, cli, path):
        result = cli("run", str(path), "--json")
        assert result.exit_code != 0, result.output
        return json.loads(result.stdout)["run_id"]

    def test_completed_steps_are_not_replayed_but_the_unfinished_step_is(self, cli, failing_wf):
        path, calls = failing_wf
        run_id = self.start(cli, path)
        assert calls.read_text() == "xx"  # both steps evaluated once
        resumed = cli("resume", run_id, "--json")
        assert resumed.exit_code != 0
        assert calls.read_text() == "xxx"  # only the failed step is re-evaluated

    def test_resume_loads_functions(self, cli, project_dir, failing_wf):
        path, _ = failing_wf
        run_id = self.start(cli, path)
        from specify_cli.workflows.function.loader import _unload_custom_functions

        _unload_custom_functions()
        assert custom_filters() == []
        cli("resume", run_id, "--json")
        assert custom_filters() == ["mark"]

    @pytest.mark.parametrize("json_mode", [False, True])
    def test_resume_collision(self, cli, project_dir, failing_wf, json_mode):
        path, calls = failing_wf
        run_id = self.start(cli, path)
        write_installed(project_dir, "clash", COLLIDING)
        args = ["resume", run_id] + (["--json"] if json_mode else [])
        result = cli(*args)
        assert result.exit_code == 1
        assert calls.read_text() == "xx"
        if json_mode:
            payload = json.loads(result.stdout)
            assert payload["status"] == "failed" and "collides" in payload["error"]
            assert payload["run_id"] == run_id
        else:
            assert "collides" in result.output


class TestAddAndUpdate:
    @pytest.fixture
    def workflow_dir(self, tmp_path):
        directory = tmp_path / "wf-src"
        directory.mkdir()
        (directory / "workflow.yml").write_text(
            workflow_yaml([{"id": "a", "type": "shell", "run": "echo hi"}], workflow_id="added"),
            encoding="utf-8",
        )
        return directory

    def test_add_loads_functions(self, cli, project_dir, workflow_dir):
        write_installed(project_dir, "text")
        result = cli("add", str(workflow_dir), "--dev")
        assert result.exit_code == 0, result.output
        assert custom_filters() == ["trim"]

    def test_add_collision(self, cli, project_dir, workflow_dir):
        write_installed(project_dir, "text", COLLIDING)
        result = cli("add", str(workflow_dir), "--dev")
        assert result.exit_code == 1 and "collides" in result.output
        assert not (project_dir / ".specify" / "workflows" / "added").exists()

    def test_update_loads_functions(self, cli, project_dir):
        write_installed(project_dir, "text")
        cli("update")
        assert custom_filters() == ["trim"]

    def test_update_collision(self, cli, project_dir):
        write_installed(project_dir, "text", COLLIDING)
        result = cli("update")
        assert result.exit_code == 1 and "collides" in result.output


class TestLoadingBoundaries:
    def test_function_commands_do_not_import_packages(self, cli, project_dir):
        marker = project_dir / "imported"
        write_installed(
            project_dir, "text",
            code=f"open({str(marker)!r}, 'w').close()\ndef trim(v):\n    return v\n",
        )
        for args in (("function", "list"), ("function", "list", "--json"), ("list",)):
            cli(*args)
        assert not marker.exists()

    def test_removing_a_package_removes_its_filter_on_next_load(self, cli, project_dir, trim_wf):
        write_installed(project_dir, "text")
        assert cli("run", str(trim_wf), "--json").exit_code == 0
        assert cli("function", "remove", "text").exit_code == 0
        assert not install_dir(project_dir, "text").exists()
        (project_dir / "out.txt").unlink()
        assert cli("run", str(trim_wf), "--json").exit_code != 0


class TestLoadFailures:
    """An OSError while loading plugins is rendered, never a raw traceback."""

    @pytest.fixture(params=["functions", "steps"])
    def failing_loader(self, request, monkeypatch):
        def boom(root):
            raise OSError("permission denied")

        if request.param == "functions":
            from specify_cli.workflows import function

            monkeypatch.setattr(function, "load_workflow_functions", boom)
        else:
            from specify_cli import workflows

            monkeypatch.setattr(workflows, "load_custom_steps", boom)
        return request.param

    @pytest.fixture
    def wf(self, project_dir):
        path = project_dir / "wf.yml"
        path.write_text(workflow_yaml([{"id": "a", "type": "shell", "run": "echo hi"}]), encoding="utf-8")
        return path

    @pytest.mark.parametrize("command", ["run", "resume"])
    def test_json_mode_reports_a_failed_payload(self, cli, wf, failing_loader, command):
        args = ["run", str(wf), "--json"] if command == "run" else ["resume", "some-run", "--json"]
        result = cli(*args)
        assert result.exit_code == 1
        assert isinstance(result.exception, SystemExit)
        payload = json.loads(result.stdout)
        assert payload["status"] == "failed" and "permission denied" in payload["error"]
        assert payload["run_id"] == ("some-run" if command == "resume" else None)

    @pytest.mark.parametrize("command", ["run", "resume", "add", "update"])
    def test_text_mode_prints_the_error(self, cli, project_dir, wf, failing_loader, command):
        args = {
            "run": ["run", str(wf)],
            "resume": ["resume", "some-run"],
            "add": ["add", str(wf)],
            "update": ["update"],
        }[command]
        result = cli(*args)
        assert result.exit_code == 1
        assert isinstance(result.exception, SystemExit)
        assert "Error: permission denied" in " ".join(result.output.split())
        assert not (project_dir / ".specify" / "workflows" / "fn-wf").exists()

    def test_a_healthy_load_is_unaffected(self, cli, wf):
        assert cli("run", str(wf), "--json").exit_code == 0
