"""Tests for mirrored integration CLI behavior in test_registration.py."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401
import shutil  # noqa: F401
from pathlib import Path  # noqa: F401

import pytest  # noqa: F401

from specify_cli import app  # noqa: F401
from specify_cli.integrations import _commands
from specify_cli.integrations.catalog import catalog_app
from tests.conftest import strip_ansi  # noqa: F401
from tests.specify_cli.integrations._catalog_helpers import (
    IntegrationCatalogCliTestBase,
)
from tests.specify_cli.integrations._helpers import (
    _copy_project_template,  # noqa: F401
    _init_project,  # noqa: F401
    _integration_list_row_cells,  # noqa: F401
    _move_kilocode_install_to_legacy_layout,  # noqa: F401
    _run_in_project,  # noqa: F401
    _write_invalid_manifest,  # noqa: F401
    runner,  # noqa: F401
)


def test_integration_commands_registered_once_in_stable_order():
    assert [command.name for command in _commands.integration_app.registered_commands] == [
        "install",
        "uninstall",
        "switch",
        "upgrade",
        "list",
        "status",
        "use",
        "search",
        "info",
        "scaffold",
    ]
    assert [group.name for group in _commands.integration_app.registered_groups] == [
        "catalog"
    ]


def test_catalog_commands_registered_once_in_stable_order():
    assert [command.name for command in catalog_app.registered_commands] == [
        "list",
        "add",
        "remove",
    ]
    assert _commands.integration_catalog_app is catalog_app


def test_catalog_package_preserves_domain_import_compatibility():
    from specify_cli.integrations import IntegrationCatalog
    from specify_cli.integrations.catalog import (
        IntegrationCatalog as CompatibilityIntegrationCatalog,
    )

    assert CompatibilityIntegrationCatalog is IntegrationCatalog


def test_version_lookup_remains_late_bound_through_commands_module(monkeypatch):
    from specify_cli.integrations._helpers import _get_speckit_version

    monkeypatch.setattr(_commands, "get_speckit_version", lambda: "9.8.7-test")

    assert _get_speckit_version() == "9.8.7-test"


@pytest.mark.parametrize("corrupt_manifest", [False, True])
@pytest.mark.parametrize("nested", [False, True])
def test_failed_managed_registration_preserves_error_and_baseline(tmp_path, corrupt_manifest, nested):
    from types import SimpleNamespace

    from specify_cli.integrations._file_changes import registration_changes, write_text
    from specify_cli.integrations._registration import managed_registration
    from specify_cli.integrations.manifest import IntegrationManifest

    relative = ".claude/skills/speckit-plan/SKILL.md"
    manifest = IntegrationManifest("claude", tmp_path)
    output = manifest.record_file(relative, b"original")
    manifest.save()
    before = manifest.manifest_path.read_bytes()
    if corrupt_manifest:
        (manifest.manifest_path.parent / "broken.manifest.json").write_text("invalid JSON")
    failure = RuntimeError("registration failed after writing one output")
    owner = SimpleNamespace(project_root=tmp_path)

    @managed_registration
    def write_output(self):
        write_text(output, "partial output")

    @managed_registration
    def fail_registration(self):
        if nested:
            write_output(self)
        else:
            write_text(output, "partial output")
        raise failure

    assert registration_changes.get() is None
    with pytest.raises(RuntimeError) as caught:
        fail_registration(owner)
    assert caught.value is failure
    assert manifest.manifest_path.read_bytes() == before
    assert IntegrationManifest.load("claude", tmp_path).check_modified() == [relative]
    assert registration_changes.get() is None


def test_successful_nested_managed_registration_refreshes_only_written_outputs(tmp_path):
    from types import SimpleNamespace

    from specify_cli.integrations._file_changes import registration_changes, write_text
    from specify_cli.integrations._registration import managed_registration
    from specify_cli.integrations.manifest import IntegrationManifest

    manifest = IntegrationManifest("claude", tmp_path)
    output = manifest.record_file(".claude/skills/speckit-plan/SKILL.md", b"original")
    untouched = ".claude/skills/speckit-tasks/SKILL.md"
    user_file = manifest.record_file(untouched, b"original")
    manifest.save()
    before = manifest.manifest_path.read_bytes()
    user_file.write_text("user customization")
    result = object()

    @managed_registration
    def write_output(self):
        write_text(output, "managed output")
        return result

    @managed_registration
    def register(self):
        returned = write_output(self)
        assert manifest.manifest_path.read_bytes() == before
        return returned

    assert register(SimpleNamespace(project_root=tmp_path)) is result
    assert IntegrationManifest.load("claude", tmp_path).check_modified() == [untouched]
    assert registration_changes.get() is None


class TestParseIntegrationOptionsEqualsForm:
    def test_equals_form_parsed(self):
        """--commands-dir=./x should be parsed the same as --commands-dir ./x."""
        from specify_cli.integrations._commands import _parse_integration_options
        from specify_cli.integrations import get_integration

        integration = get_integration("generic")
        assert integration is not None

        result_space = _parse_integration_options(integration, "--commands-dir ./mydir")
        result_equals = _parse_integration_options(integration, "--commands-dir=./mydir")
        assert result_space is not None
        assert result_equals is not None
        assert result_space["commands_dir"] == "./mydir"
        assert result_equals["commands_dir"] == "./mydir"

    def test_unbalanced_quote_exits_cleanly(self, capsys):
        """An unbalanced quote must exit(1) with a message, not a raw ValueError.

        shlex.split() raises ValueError("No closing quotation") on an unbalanced
        quote; the parser must translate that into the same clean typer.Exit(1)
        UX as unknown-option / missing-value, rather than letting the traceback
        escape (issue #3457).
        """
        import typer

        from specify_cli.integrations._commands import _parse_integration_options
        from specify_cli.integrations import get_integration

        integration = get_integration("generic")
        assert integration is not None

        with pytest.raises(typer.Exit) as excinfo:
            _parse_integration_options(integration, '--commands-dir "foo')
        assert excinfo.value.exit_code == 1
        assert "Error: Could not parse integration options: No closing quotation." in capsys.readouterr().out

    def test_bad_option_token_with_rich_markup_exits_cleanly(self):
        """A bad option token carrying Rich markup must exit cleanly, not crash.

        The token is user-controlled and gets interpolated into console.print.
        A value like '[/red]foo' parses fine through shlex but is an unexpected
        value / unknown option — and an unbalanced Rich tag would raise
        rich.errors.MarkupError inside console.print, leaking a traceback
        instead of the intended typer.Exit(1). The token must be escaped."""
        import typer

        from specify_cli.integrations._commands import _parse_integration_options
        from specify_cli.integrations import get_integration

        integration = get_integration("generic")
        assert integration is not None

        # Unexpected value token carrying markup.
        with pytest.raises(typer.Exit):
            _parse_integration_options(integration, "[/red]foo")

        # Unknown option token carrying markup.
        with pytest.raises(typer.Exit):
            _parse_integration_options(integration, "--[/red]bad")


@pytest.mark.parametrize(
    "args",
    [
        ["init", "--help"],
        ["integration", "install", "--help"],
        ["integration", "switch", "--help"],
        ["integration", "upgrade", "--help"],
    ],
)
def test_script_help_includes_python_variant(args):
    result = runner.invoke(app, args)

    assert result.exit_code == 0
    assert "sh, ps, or py" in " ".join(strip_ansi(result.output).split())


class TestIntegrationProjectGuards(IntegrationCatalogCliTestBase):
    def test_primary_integration_commands_require_specify_project(self, tmp_path):
        project = tmp_path / "bare"
        project.mkdir()
        commands = [
            ["integration", "list"],
            ["integration", "install", "codex"],
            ["integration", "use", "codex"],
            ["integration", "uninstall"],
            ["integration", "switch", "codex"],
            ["integration", "upgrade"],
        ]

        for command in commands:
            result = self._invoke(command, project)
            failure_context = (
                f"command={command!r}, exit_code={result.exit_code}, output={result.output!r}"
            )
            assert result.exit_code == 1, failure_context
            assert "Not a Spec Kit project" in result.output, failure_context

    def test_integration_commands_require_specify_directory(self, tmp_path):
        project = tmp_path / "bad"
        project.mkdir()
        (project / ".specify").write_text("not a directory")

        commands = [
            ["integration", "list"],
            ["integration", "use", "codex"],
        ]

        for command in commands:
            result = self._invoke(command, project)
            assert result.exit_code == 1, result.output
            assert "Not a Spec Kit project" in result.output
