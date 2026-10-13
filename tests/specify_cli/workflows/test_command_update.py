"""Command-focused workflow tests."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest



class TestWorkflowCliAlignment:
    """CLI alignment with extension/preset commands (#2342)."""

    WORKFLOW_YAML = """
schema_version: "1.0"
workflow:
  id: "align-wf"
  name: "Align Workflow"
  version: "{version}"
  description: "CLI alignment test workflow"
steps:
  - id: step-one
    type: shell
    run: "echo hello"
"""

    def _write_workflow_dir(self, base, version="1.0.0"):
        d = base / "wf-src"
        d.mkdir(parents=True, exist_ok=True)
        (d / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version=version), encoding="utf-8"
        )
        return d

    def _install_dev(self, runner, app, project_dir):
        src = self._write_workflow_dir(project_dir)
        result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])
        assert result.exit_code == 0, result.output
        return src

    class _FakeResponse:
        def __init__(self, data, url="https://example.com/workflow.yml", headers=None):
            self._data = data
            self._url = url
            self._pos = 0
            self._headers = headers or {}

        def read(self, amt=None):
            if amt is None:
                chunk = self._data[self._pos :]
                self._pos = len(self._data)
                return chunk
            chunk = self._data[self._pos : self._pos + amt]
            self._pos += len(chunk)
            return chunk

        def getheader(self, name, default=None):
            return self._headers.get(name, default)

        def geturl(self):
            return self._url

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def test_update_no_workflows_installed(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "update"])
        assert result.exit_code == 0, result.output
        assert "No workflows installed" in result.output

    def test_update_not_installed_errors(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "update", "ghost"])
        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_update_skips_non_catalog_sources(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)
        result = runner.invoke(app, ["workflow", "update"])
        assert result.exit_code == 0, result.output
        assert "re-add to update" in result.output
        # Every target was skipped — must not claim everything is up to date.
        assert "No workflows were eligible for update" in result.output
        assert "up to date!" not in result.output

    def test_update_skip_message_accurate_for_bundled_source(self, project_dir, monkeypatch):
        """A workflow registered with source "bundled" (e.g. the speckit
        workflow installed by `specify init`) was never installed from a
        local path or URL; the skip message must not claim otherwise."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        registry = WorkflowRegistry(project_dir)
        registry.add(
            "speckit",
            {"name": "Speckit", "version": "1.0.0", "source": "bundled"},
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "update"])
        assert result.exit_code == 0, result.output
        assert "local path or URL" not in result.output
        assert "re-add to update" in result.output

    def test_update_mixed_targets_does_not_claim_all_up_to_date(self, project_dir, monkeypatch):
        """Skipped targets must not be presented as verified up to date."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)  # local source → skipped
        WorkflowRegistry(project_dir).add("catalog-wf", {
            "name": "Catalog Workflow",
            "version": "1.0.0",
            "description": "",
            "source": "catalog",
            "url": "https://example.com/workflow.yml",
        })
        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "version": "1.0.0",
                "url": "https://example.com/workflow.yml",
                "_install_allowed": True,
            },
        )
        result = runner.invoke(app, ["workflow", "update"])
        assert result.exit_code == 0, result.output
        assert "All workflows are up to date!" not in result.output
        assert "All checked workflows are up to date" in result.output
        assert "skipped" in result.output

    def test_update_installs_newer_catalog_version(self, project_dir, monkeypatch):
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        registry = WorkflowRegistry(project_dir)
        registry.add("align-wf", {
            "name": "Align Workflow",
            "version": "1.0.0",
            "description": "CLI alignment test workflow",
            "source": "catalog",
            "catalog_name": "test-catalog",
            "url": "https://example.com/workflow.yml",
        })
        wf_dir = project_dir / ".specify" / "workflows" / "align-wf"
        wf_dir.mkdir(parents=True)
        (wf_dir / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="1.0.0"), encoding="utf-8"
        )

        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "name": "Align Workflow",
                "version": "2.0.0",
                "url": "https://example.com/workflow.yml",
                "_install_allowed": True,
                "_catalog_name": "test-catalog",
            },
        )
        data = self.WORKFLOW_YAML.format(version="2.0.0").encode()
        runner = CliRunner()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(data, url),
        ):
            result = runner.invoke(app, ["workflow", "update"], input="y\n")
        assert result.exit_code == 0, result.output
        assert "1.0.0" in result.output and "2.0.0" in result.output
        meta = WorkflowRegistry(project_dir).get("align-wf")
        assert meta["version"] == "2.0.0"
        assert "2.0.0" in (wf_dir / "workflow.yml").read_text(encoding="utf-8")

    def test_update_downloaded_invalid_yaml_escapes_rich_markup(self, project_dir, monkeypatch):
        """A malformed downloaded workflow can quote the offending line verbatim; escape it before printing."""
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry
        from specify_cli.workflows.engine import WorkflowDefinition

        monkeypatch.chdir(project_dir)
        registry = WorkflowRegistry(project_dir)
        registry.add("align-wf", {
            "name": "Align Workflow",
            "version": "1.0.0",
            "description": "CLI alignment test workflow",
            "source": "catalog",
            "catalog_name": "test-catalog",
            "url": "https://example.com/workflow.yml",
        })
        wf_dir = project_dir / ".specify" / "workflows" / "align-wf"
        wf_dir.mkdir(parents=True)
        (wf_dir / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="1.0.0"), encoding="utf-8"
        )

        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "name": "Align Workflow",
                "version": "2.0.0",
                "url": "https://example.com/workflow.yml",
                "_install_allowed": True,
                "_catalog_name": "test-catalog",
            },
        )
        runner = CliRunner()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(b"", url),
        ), patch.object(
            WorkflowDefinition,
            "from_string",
            side_effect=ValueError('bad snippet: "New [Feature]"'),
        ):
            result = runner.invoke(app, ["workflow", "update"], input="y\n")
        assert 'bad snippet: "New [Feature]"' in result.output
        assert "Failed to update" in result.output
        # The previously installed workflow must survive a failed update.
        assert "1.0.0" in (wf_dir / "workflow.yml").read_text(encoding="utf-8")

    def test_update_malformed_catalog_url_fails_cleanly(self, project_dir, monkeypatch):
        """An unparseable catalog URL (unbalanced IPv6 literal) must not abort the whole update."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        registry = WorkflowRegistry(project_dir)
        registry.add("align-wf", {
            "name": "Align Workflow",
            "version": "1.0.0",
            "description": "CLI alignment test workflow",
            "source": "catalog",
            "catalog_name": "test-catalog",
            "url": "https://[::1/workflow.yml",
        })
        wf_dir = project_dir / ".specify" / "workflows" / "align-wf"
        wf_dir.mkdir(parents=True)
        (wf_dir / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="1.0.0"), encoding="utf-8"
        )

        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "name": "Align Workflow",
                "version": "2.0.0",
                "url": "https://[::1/workflow.yml",
                "_install_allowed": True,
                "_catalog_name": "test-catalog",
            },
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "update"], input="y\n")
        assert "malformed install URL" in result.output
        assert "Failed to update" in result.output
        # The previously installed workflow must survive.
        assert "1.0.0" in (wf_dir / "workflow.yml").read_text(encoding="utf-8")

    def test_update_rejects_version_mismatch_from_stale_url(self, project_dir, monkeypatch):
        """A URL serving a different version than the catalog advertised must fail the update."""
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        WorkflowRegistry(project_dir).add("align-wf", {
            "name": "Align Workflow",
            "version": "1.0.0",
            "description": "CLI alignment test workflow",
            "source": "catalog",
            "catalog_name": "test-catalog",
            "url": "https://example.com/workflow.yml",
        })
        wf_dir = project_dir / ".specify" / "workflows" / "align-wf"
        wf_dir.mkdir(parents=True)
        (wf_dir / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="1.0.0"), encoding="utf-8"
        )

        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "name": "Align Workflow",
                "version": "2.0.0",
                "url": "https://example.com/workflow.yml",
                "_install_allowed": True,
                "_catalog_name": "test-catalog",
            },
        )
        # The URL still serves the old 1.0.0 payload.
        data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
        runner = CliRunner()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(data, url),
        ):
            result = runner.invoke(app, ["workflow", "update"], input="y\n")
        assert "does not match the catalog version" in result.output
        assert "Failed to update" in result.output
        meta = WorkflowRegistry(project_dir).get("align-wf")
        assert meta["version"] == "1.0.0"
        assert "1.0.0" in (wf_dir / "workflow.yml").read_text(encoding="utf-8")

    def test_update_preserves_disabled_state(self, project_dir, monkeypatch):
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        WorkflowRegistry(project_dir).add("align-wf", {
            "name": "Align Workflow",
            "version": "1.0.0",
            "description": "",
            "source": "catalog",
            "url": "https://example.com/workflow.yml",
            "enabled": False,
        })
        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "version": "2.0.0",
                "url": "https://example.com/workflow.yml",
                "_install_allowed": True,
            },
        )
        data = self.WORKFLOW_YAML.format(version="2.0.0").encode()
        runner = CliRunner()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(data, url),
        ):
            result = runner.invoke(app, ["workflow", "update"], input="y\n")
        assert result.exit_code == 0, result.output
        meta = WorkflowRegistry(project_dir).get("align-wf")
        assert meta["version"] == "2.0.0"
        assert meta["enabled"] is False

    @pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
    def test_update_preserves_workflow_file_mode(self, project_dir, monkeypatch):
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        WorkflowRegistry(project_dir).add("align-wf", {
            "name": "Align Workflow",
            "version": "1.0.0",
            "description": "",
            "source": "catalog",
            "url": "https://example.com/workflow.yml",
        })
        workflow_file = (
            project_dir
            / ".specify"
            / "workflows"
            / "align-wf"
            / "workflow.yml"
        )
        workflow_file.parent.mkdir(parents=True)
        workflow_file.write_text(
            self.WORKFLOW_YAML.format(version="1.0.0"), encoding="utf-8"
        )
        workflow_file.chmod(0o640)

        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "version": "2.0.0",
                "url": "https://example.com/workflow.yml",
                "_install_allowed": True,
            },
        )
        data = self.WORKFLOW_YAML.format(version="2.0.0").encode()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None,
            redirect_validator=None: self._FakeResponse(data, url),
        ):
            result = CliRunner().invoke(
                app, ["workflow", "update"], input="y\n"
            )

        assert result.exit_code == 0, result.output
        assert stat.S_IMODE(workflow_file.stat().st_mode) == 0o640

    def test_update_skips_corrupted_registry_entry(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        registry_path = WorkflowRegistry(project_dir).registry_path
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps({"schema_version": "1.0", "workflows": {"broken": "not-a-dict"}}),
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "update"])
        assert result.exit_code == 0, result.output
        assert "corrupted" in result.output

    def test_update_reports_unsafe_registry_id_per_workflow(self, project_dir, monkeypatch):
        """An unsafe workflow id in the registry must fail that one entry, not abort the whole update."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry, WorkflowCatalog

        monkeypatch.chdir(project_dir)
        registry_path = WorkflowRegistry(project_dir).registry_path
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "workflows": {
                        "../evil": {
                            "name": "Bad",
                            "version": "0.0.1",
                            "source": "catalog",
                            "url": "https://example.com/evil.yml",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {"version": "9.9.9", "url": "https://example.com/evil.yml", "_install_allowed": True},
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "update"], input="y\n")
        assert result.exit_code != 0
        assert "Failed to update" in result.output

    def test_update_registry_save_failure_restores_prior_file_without_redundant_write(
        self, project_dir, monkeypatch
    ):
        """A registry.add() save failure during `workflow update` must be
        fully restored by _install_workflow_from_catalog's own atomic
        rollback (rename-based, not a byte-level rewrite). The outer
        workflow_update loop must not perform any redundant write of its
        own onto the destination file -- that write happened only after
        typer.Exit already unwound, could itself fail/truncate the safely
        preserved file, and is provably unnecessary here since the inner
        transaction already restored it via rename."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "name": "Align Workflow",
                "version": "1.0.0",
                "url": "https://example.com/workflow.yml",
                "_install_allowed": True,
                "_catalog_name": "test-catalog",
            },
        )
        source_data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
        runner = CliRunner()
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                    source_data, url
                ),
            )
            result = runner.invoke(app, ["workflow", "add", "align-wf"])
        assert result.exit_code == 0, result.output

        dest_file = project_dir / ".specify" / "workflows" / "align-wf" / "workflow.yml"
        original_data = dest_file.read_bytes()

        new_data = self.WORKFLOW_YAML.format(version="2.0.0").encode()

        def boom_save(self):
            raise OSError("disk full")

        dest_writes: list[bytes] = []
        real_write_bytes = Path.write_bytes
        resolved_dest_file = dest_file.resolve()

        def tracking_write_bytes(self_path, data, *args, **kwargs):
            if self_path.resolve() == resolved_dest_file:
                dest_writes.append(data)
            return real_write_bytes(self_path, data, *args, **kwargs)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                WorkflowCatalog,
                "get_workflow_info",
                lambda self, wid: {
                    "id": wid,
                    "name": "Align Workflow",
                    "version": "2.0.0",
                    "url": "https://example.com/workflow.yml",
                    "_install_allowed": True,
                    "_catalog_name": "test-catalog",
                },
            )
            mp.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                    new_data, url
                ),
            )
            mp.setattr(WorkflowRegistry, "save", boom_save)
            mp.setattr(Path, "write_bytes", tracking_write_bytes)
            result = runner.invoke(app, ["workflow", "update"], input="y\n")

        assert result.exit_code != 0
        assert "Failed to update" in result.output
        # No redundant/second write of the destination file was attempted --
        # the inner atomic commit/rollback (rename-based) is the only thing
        # that ever touches it.
        assert dest_writes == []
        assert dest_file.read_bytes() == original_data
        registry = WorkflowRegistry(project_dir)
        assert registry.is_installed("align-wf")
        assert registry.get("align-wf")["version"] == "1.0.0"

    def test_update_non_json_description_restores_prior_file_and_registry(
        self, project_dir, monkeypatch
    ):
        from unittest.mock import patch

        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        registry = WorkflowRegistry(project_dir)
        registry.add(
            "align-wf",
            {
                "name": "Align Workflow",
                "version": "1.0.0",
                "description": "",
                "source": "catalog",
                "url": "https://example.com/workflow.yml",
            },
        )
        workflow_file = (
            project_dir
            / ".specify"
            / "workflows"
            / "align-wf"
            / "workflow.yml"
        )
        workflow_file.parent.mkdir(parents=True)
        original_data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
        workflow_file.write_bytes(original_data)

        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "name": "Align Workflow",
                "version": "2.0.0",
                "url": "https://example.com/workflow.yml",
                "_install_allowed": True,
                "_catalog_name": "test-catalog",
            },
        )
        invalid_data = self.WORKFLOW_YAML.format(version="2.0.0").replace(
            'description: "CLI alignment test workflow"',
            "description: 2026-01-02",
        ).encode()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None,
            redirect_validator=None: self._FakeResponse(invalid_data, url),
        ):
            result = CliRunner().invoke(
                app, ["workflow", "update", "align-wf"], input="y\n"
            )

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Failed to update workflow registry" in result.output
        assert workflow_file.read_bytes() == original_data
        current = WorkflowRegistry(project_dir).get("align-wf")
        assert current["version"] == "1.0.0"
        leftovers = [
            path.name
            for path in workflow_file.parent.iterdir()
            if path.name != "workflow.yml"
        ]
        assert leftovers == []

    @pytest.mark.parametrize(
        ("replacement_source", "replacement_version"),
        [("local", "1.0.0"), ("catalog", "1.5.0")],
    )
    def test_update_rechecks_registry_after_confirmation(
        self, project_dir, monkeypatch, replacement_source, replacement_version
    ):
        from unittest.mock import patch

        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        registry = WorkflowRegistry(project_dir)
        registry.add(
            "align-wf",
            {
                "name": "Align Workflow",
                "version": "1.0.0",
                "description": "",
                "source": "catalog",
                "url": "https://example.com/workflow.yml",
            },
        )
        workflow_file = (
            project_dir
            / ".specify"
            / "workflows"
            / "align-wf"
            / "workflow.yml"
        )
        workflow_file.parent.mkdir(parents=True)
        workflow_file.write_text(
            self.WORKFLOW_YAML.format(version="1.0.0"), encoding="utf-8"
        )
        replacement_data = self.WORKFLOW_YAML.format(
            version=replacement_version
        ).replace(
            'description: "CLI alignment test workflow"',
            'description: "concurrent replacement"',
        ).encode()

        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "name": "Align Workflow",
                "version": "2.0.0",
                "url": "https://example.com/workflow.yml",
                "_install_allowed": True,
                "_catalog_name": "test-catalog",
            },
        )

        def replace_while_confirming(*args, **kwargs):
            WorkflowRegistry(project_dir).add(
                "align-wf",
                {
                    "name": "Concurrent replacement",
                    "version": replacement_version,
                    "description": "",
                    "source": replacement_source,
                },
            )
            workflow_file.write_bytes(replacement_data)
            return True

        monkeypatch.setattr(_commands.typer, "confirm", replace_while_confirming)
        catalog_data = self.WORKFLOW_YAML.format(version="2.0.0").encode()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None,
            redirect_validator=None: self._FakeResponse(catalog_data, url),
        ):
            result = CliRunner().invoke(app, ["workflow", "update", "align-wf"])

        assert result.exit_code != 0
        assert "changed during update" in result.output
        assert workflow_file.read_bytes() == replacement_data
        current = WorkflowRegistry(project_dir).get("align-wf")
        assert current["source"] == replacement_source
        assert current["version"] == replacement_version

    def test_update_up_to_date_reports_and_exits_zero(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        WorkflowRegistry(project_dir).add("align-wf", {
            "name": "Align Workflow",
            "version": "1.0.0",
            "description": "",
            "source": "catalog",
            "url": "https://example.com/workflow.yml",
        })
        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "version": "1.0.0",
                "url": "https://example.com/workflow.yml",
                "_install_allowed": True,
            },
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "update"])
        assert result.exit_code == 0, result.output
        assert "Up to date" in result.output
        assert "All workflows are up to date!" in result.output

    def test_update_restores_backup_on_failed_download(self, project_dir, monkeypatch):
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        WorkflowRegistry(project_dir).add("align-wf", {
            "name": "Align Workflow",
            "version": "1.0.0",
            "description": "",
            "source": "catalog",
            "url": "https://example.com/workflow.yml",
        })
        wf_dir = project_dir / ".specify" / "workflows" / "align-wf"
        wf_dir.mkdir(parents=True)
        original = self.WORKFLOW_YAML.format(version="1.0.0")
        (wf_dir / "workflow.yml").write_text(original, encoding="utf-8")

        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "version": "2.0.0",
                "url": "https://example.com/workflow.yml",
                "_install_allowed": True,
            },
        )

        def boom(url, timeout=None, extra_headers=None, redirect_validator=None):
            raise OSError("network down")

        runner = CliRunner()
        with patch("specify_cli.authentication.http.open_url", side_effect=boom):
            result = runner.invoke(app, ["workflow", "update"], input="y\n")
        assert result.exit_code != 0
        assert "Failed to update" in result.output
        # Working copy and registry version are untouched
        assert (wf_dir / "workflow.yml").read_text(encoding="utf-8") == original
        assert WorkflowRegistry(project_dir).get("align-wf")["version"] == "1.0.0"
