"""``specify workflow function list``."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows.function import FunctionRegistry

from .helpers import functions_dir, write_package


@pytest.fixture
def cli(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)
    runner = CliRunner()
    return lambda *args: runner.invoke(app, ["workflow", "function", *args])


def install(cli, tmp_path, function_id, functions, **manifest):
    source = write_package(tmp_path / function_id, function_id, functions, **manifest)
    result = cli("add", function_id, "--dev", str(source))
    assert result.exit_code == 0, result.output


class TestList:
    def test_empty_text_and_json(self, cli):
        text = cli("list")
        assert text.exit_code == 0 and "No workflow functions installed." in text.output
        data = cli("list", "--json")
        assert data.exit_code == 0 and json.loads(data.output) == []

    def test_json_describes_every_package_and_function(self, cli, tmp_path):
        install(
            cli, tmp_path, "text",
            [
                {"name": "trim", "handler": "trim", "description": "Strip"},
                {"name": "pad", "handler": "trim", "min_args": 2, "max_args": 3},
            ],
            name="Text", version="1.0.0", description="Helpers",
        )
        rows = json.loads(cli("list", "--json").output)
        assert rows == [{
            "id": "text", "name": "Text", "version": "1.0.0", "source": "local",
            "description": "Helpers",
            "functions": [
                {"name": "trim", "handler": "trim", "min_args": 0, "max_args": 0,
                 "description": "Strip", "usage": "trim"},
                {"name": "pad", "handler": "trim", "min_args": 2, "max_args": 3,
                 "description": "", "usage": "pad(arg1, arg2, arg3)"},
            ],
        }]

    @pytest.mark.parametrize(
        ("minimum", "maximum", "usage"),
        [
            (0, 0, "f"),
            (0, 1, "f or f('x')"),
            (1, 1, "f('arg1')"),
            (0, 2, "f or f(arg1, arg2)"),
            (2, 2, "f(arg1, arg2)"),
        ],
    )
    def test_usage_for_each_arity(self, cli, tmp_path, minimum, maximum, usage):
        install(cli, tmp_path, "p", [{"name": "f", "handler": "trim", "min_args": minimum, "max_args": maximum}])
        (row,) = json.loads(cli("list", "--json").output)
        assert row["functions"][0]["usage"] == usage

    def test_packages_are_sorted_by_id(self, cli, tmp_path):
        install(cli, tmp_path, "zeta", [{"name": "z", "handler": "trim"}])
        install(cli, tmp_path, "alpha", [{"name": "a", "handler": "trim"}])
        assert [r["id"] for r in json.loads(cli("list", "--json").output)] == ["alpha", "zeta"]

    def test_text_output(self, cli, tmp_path):
        install(
            cli, tmp_path, "text",
            [{"name": "pad", "handler": "trim", "min_args": 1, "max_args": 1, "description": "Pad it"}],
            name="Text helpers", version="1.2.3",
        )
        result = cli("list")
        assert result.exit_code == 0
        assert "Text helpers" in result.output and "(text)" in result.output and "v1.2.3" in result.output
        assert "pad('arg1')" in result.output and "Pad it" in result.output

    def test_json_output_is_only_json(self, cli, tmp_path):
        install(cli, tmp_path, "text", None)
        json.loads(cli("list", "--json").output)

    def test_text_is_rendered_literally(self, cli, tmp_path):
        install(
            cli, tmp_path, "text",
            [{"name": "f", "handler": "trim", "description": "[red]bold[/red] [x]"}],
        )
        assert "[red]bold[/red] [x]" in cli("list").output

    def test_listing_never_imports_package_code(self, cli, tmp_path):
        marker = tmp_path / "imported"
        source = write_package(
            tmp_path / "text", "text",
            code=f"open({str(marker)!r}, 'w').close()\ndef trim(v):\n    return v\n",
        )
        assert cli("add", "text", "--dev", str(source)).exit_code == 0
        assert cli("list").exit_code == 0 and cli("list", "--json").exit_code == 0
        assert not marker.exists()

    def test_listing_does_not_register_filters(self, cli, tmp_path):
        from specify_cli.workflows.expressions import BUILTIN_FILTERS, FILTER_TABLE

        install(cli, tmp_path, "text", None)
        cli("list")
        assert set(FILTER_TABLE) == set(BUILTIN_FILTERS)

    def test_damaged_registry_entries_are_tolerated(self, cli, project_dir):
        registry = FunctionRegistry(project_dir)
        registry.add("odd", {
            "functions": [
                "not-a-mapping",
                {"name": "bad", "min_args": 5, "max_args": 1},
                {"name": "bool", "min_args": True, "max_args": True},
            ],
        })
        registry.data["functions"]["junk"] = "not-a-mapping"
        registry.save()
        result = cli("list", "--json")
        assert result.exit_code == 0
        (row,) = json.loads(result.output)
        assert row["id"] == "odd"
        assert [(f["name"], f["min_args"], f["max_args"]) for f in row["functions"]] == [
            ("bad", 0, 0), ("bool", 0, 0),
        ]

    def test_oversized_stored_bounds_are_listed_without_expanding_usage(self, cli, project_dir):
        registry = FunctionRegistry(project_dir)
        registry.add("big", {
            "functions": [
                {"name": "huge", "min_args": 0, "max_args": 100_000_000},
                {"name": "edge", "min_args": 0, "max_args": 16},
            ],
        })
        result = cli("list", "--json")
        assert result.exit_code == 0
        (row,) = json.loads(result.output)
        assert [(f["name"], f["min_args"], f["max_args"]) for f in row["functions"]] == [
            ("huge", 0, 0), ("edge", 0, 16),
        ]
        assert cli("list").exit_code == 0

    def test_corrupt_registry_lists_nothing(self, cli, project_dir):
        functions_dir(project_dir).mkdir(parents=True)
        (functions_dir(project_dir) / "function-registry.json").write_text("{bad")
        assert json.loads(cli("list", "--json").output) == []
