"""Command-focused workflow tests."""

from __future__ import annotations

import json
import os
import shutil
import stat
import tarfile
import tempfile
import zipfile
from pathlib import Path

import pytest
import typer
import yaml

from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()



class TestWorkflowAddCaseInsensitiveSuffix:
    """`workflow add` must detect a local YAML file case-insensitively, matching
    `workflow run` (_commands.py:workflow_run) and the engine loader
    (engine.py:WorkflowEngine.load_workflow), which both use `.suffix.lower()`.
    Without it, `workflow run Sample.YAML` works but `workflow add Sample.YAML`
    fails — an add/run inconsistency for an uppercase extension."""

    def test_plain_path_accepts_uppercase_extension(self, temp_dir, monkeypatch, sample_workflow_yaml):
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)
        src = temp_dir / "Sample.YAML"
        src.write_text(sample_workflow_yaml, encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(src)])

        # Before the fix: `.suffix in (...)` is case-sensitive, so ".YAML" is not
        # recognized as a local file; the path falls through to catalog lookup
        # and fails. After the fix it installs like the lowercase happy path.
        assert result.exit_code == 0, result.output
        assert "installed" in result.output

    def test_dev_path_accepts_uppercase_extension(self, temp_dir, monkeypatch, sample_workflow_yaml):
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)
        src = temp_dir / "Sample.YAML"
        src.write_text(sample_workflow_yaml, encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", "--dev", str(src)])

        # Before the fix the --dev branch rejects ".YAML" with
        # "--dev source must be a workflow YAML file ...".
        assert result.exit_code == 0, result.output
        assert "installed" in result.output

    def test_lowercase_extension_still_installs(self, temp_dir, monkeypatch, sample_workflow_yaml):
        """Happy path (lowercase .yml) is unchanged by the case-normalization."""
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)
        src = temp_dir / "sample.yml"
        src.write_text(sample_workflow_yaml, encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(src)])

        assert result.exit_code == 0, result.output
        assert "installed" in result.output

    def test_add_installs_workflow_with_custom_step(self, temp_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)
        step_dir = temp_dir / ".specify" / "workflows" / "steps" / "test-add-step"
        step_dir.mkdir(parents=True)
        step_manifest = {
            "schema_version": "1.0",
            "step": {
                "type_key": "test-add-step",
                "name": "Test Add Step",
                "version": "1.0.0",
            },
        }
        (step_dir / "step.yml").write_text(
            yaml.safe_dump(step_manifest, sort_keys=False),
            encoding="utf-8",
        )
        (step_dir / "__init__.py").write_text(
            """
from specify_cli.workflows.base import StepBase, StepResult


class TestAddStep(StepBase):
    type_key = "test-add-step"

    def execute(self, config, context):
        return StepResult()
""",
            encoding="utf-8",
        )

        src = temp_dir / "sample.yml"
        workflow_definition = {
            "schema_version": "1.0",
            "workflow": {
                "id": "test-workflow-with-custom-step",
                "name": "Test Workflow With Custom Step",
                "version": "1.0.0",
            },
            "steps": [
                {"id": "custom-step", "type": "test-add-step"},
            ],
        }
        src.write_text(
            yaml.safe_dump(workflow_definition, sort_keys=False),
            encoding="utf-8",
        )
        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(src)])

        assert result.exit_code == 0, result.output
        installed_workflow = (
            temp_dir
            / ".specify"
            / "workflows"
            / "test-workflow-with-custom-step"
            / "workflow.yml"
        )
        assert installed_workflow.is_file()



class TestWorkflowAddUrlResolution:
    """CLI-level tests for workflow add <url> GitHub release URL resolution."""

    VALID_WORKFLOW_YAML = """
schema_version: "1.0"
workflow:
  id: "test-wf"
  name: "Test Workflow"
  version: "1.0.0"
  description: "A test workflow"
steps:
  - id: step-one
    type: shell
    run: "echo hello"
"""

    def test_workflow_add_from_github_release_url_resolves_and_downloads(self, project_dir):
        """'workflow add <github-release-url>' resolves to API asset URL."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        captured_urls = []

        class FakeResponse:
            def __init__(self, data, url=None):
                self._data = data
                self._pos = 0
                self._url = url or "https://api.github.com/repos/org/repo/releases/assets/42"

            def read(self, size=-1):
                if size < 0:
                    size = len(self._data) - self._pos
                out = self._data[self._pos : self._pos + size]
                self._pos += len(out)
                return out

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
            captured_urls.append(
                (url, extra_headers, timeout, redirect_validator)
            )
            if "releases/tags/" in url:
                return FakeResponse(json.dumps({
                    "assets": [{"name": "workflow.yml", "url": "https://api.github.com/repos/org/repo/releases/assets/42"}]
                }).encode())
            return FakeResponse(self.VALID_WORKFLOW_YAML.encode())

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
            result = runner.invoke(app, [
                "workflow", "add",
                "https://github.com/org/repo/releases/download/v1.0/workflow.yml",
            ])

        assert result.exit_code == 0, result.output
        assert "Test Workflow" in result.output
        # First call resolves the release tag with timeout=30
        tag_calls = [
            (url, headers, timeout, validator)
            for url, headers, timeout, validator in captured_urls
            if "releases/tags/" in url
        ]
        assert len(tag_calls) == 1
        assert tag_calls[0][2] == 30  # timeout matches download timeout
        assert tag_calls[0][3] is not None
        # Second call downloads from the resolved asset URL with octet-stream
        asset_calls = [
            (url, headers, timeout, validator)
            for url, headers, timeout, validator in captured_urls
            if "releases/assets/" in url
        ]
        assert len(asset_calls) >= 1
        assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    def test_workflow_add_from_direct_api_asset_url_passes_through(self, project_dir):
        """'workflow add <api-asset-url>' uses URL directly with octet-stream."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        captured_urls = []

        class FakeResponse:
            def __init__(self, data, url=None):
                self._data = data
                self._pos = 0
                self._url = url or "https://api.github.com/repos/org/repo/releases/assets/42"

            def read(self, size=-1):
                if size < 0:
                    size = len(self._data) - self._pos
                out = self._data[self._pos : self._pos + size]
                self._pos += len(out)
                return out

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
            captured_urls.append((url, extra_headers))
            return FakeResponse(self.VALID_WORKFLOW_YAML.encode())

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
            result = runner.invoke(app, [
                "workflow", "add",
                "https://api.github.com/repos/org/repo/releases/assets/42",
            ])

        assert result.exit_code == 0, result.output
        # Should go directly to the asset URL with Accept header
        assert len(captured_urls) == 1
        assert captured_urls[0][0] == "https://api.github.com/repos/org/repo/releases/assets/42"
        assert captured_urls[0][1] == {"Accept": "application/octet-stream"}

    def test_workflow_add_catalog_based_resolves_github_release_url(self, project_dir):
        """'workflow add <id>' with catalog GitHub release URL resolves via API."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        captured_urls = []

        class FakeResponse:
            def __init__(self, data, url=None):
                self._data = data
                self._pos = 0
                self._url = url or "https://api.github.com/repos/org/repo/releases/assets/55"

            def read(self, size=-1):
                if size < 0:
                    size = len(self._data) - self._pos
                out = self._data[self._pos : self._pos + size]
                self._pos += len(out)
                return out

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
            captured_urls.append((url, extra_headers, redirect_validator))
            if "releases/tags/" in url:
                return FakeResponse(json.dumps({
                    "assets": [{"name": "workflow.yml", "url": "https://api.github.com/repos/org/repo/releases/assets/55"}]
                }).encode())
            # Use workflow YAML with id matching catalog key
            wf_yaml = """
schema_version: "1.0"
workflow:
  id: "my-wf"
  name: "My Workflow"
  version: "1.0.0"
  description: "A catalog workflow"
steps:
  - id: step-one
    type: shell
    run: "echo hello"
"""
            return FakeResponse(wf_yaml.encode())

        fake_catalog_info = {
            "id": "my-wf",
            "name": "My Workflow",
            "version": "1.0.0",
            "url": "https://github.com/org/repo/releases/download/v2.0/workflow.yml",
            "_install_allowed": True,
        }

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url), \
             patch("specify_cli.workflows.catalog.WorkflowCatalog.get_workflow_info", return_value=fake_catalog_info):
            result = runner.invoke(app, ["workflow", "add", "my-wf"])

        assert result.exit_code == 0, result.output
        # Should resolve via releases/tags API
        tag_calls = [
            (url, validator)
            for url, _, validator in captured_urls
            if "releases/tags/" in url
        ]
        assert len(tag_calls) == 1
        assert "releases/tags/v2.0" in tag_calls[0][0]
        assert tag_calls[0][1] is not None
        # Should download from resolved asset URL with octet-stream
        asset_calls = [
            (url, headers)
            for url, headers, _ in captured_urls
            if "releases/assets/" in url
        ]
        assert len(asset_calls) >= 1
        assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    def test_workflow_add_from_ghes_release_url_resolves_via_api_v3(self, project_dir, monkeypatch):
        """'workflow add <ghes-release-url>' resolves via GHES /api/v3 endpoint."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        from specify_cli.authentication import http as _auth_http
        from specify_cli.authentication.config import AuthConfigEntry

        monkeypatch.setattr(_auth_http, "_config_override", [
            AuthConfigEntry(hosts=("ghes.example",), provider="github", auth="bearer", token="t"),
        ])

        captured_urls = []

        class FakeResponse:
            def __init__(self, data, url=None):
                self._data = data
                self._pos = 0
                self._url = url or "https://ghes.example/api/v3/repos/org/repo/releases/assets/42"

            def read(self, size=-1):
                if size < 0:
                    size = len(self._data) - self._pos
                out = self._data[self._pos : self._pos + size]
                self._pos += len(out)
                return out

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
            captured_urls.append((url, extra_headers))
            if "releases/tags/" in url:
                return FakeResponse(json.dumps({
                    "assets": [{"name": "workflow.yml", "url": "https://ghes.example/api/v3/repos/org/repo/releases/assets/42"}]
                }).encode())
            return FakeResponse(self.VALID_WORKFLOW_YAML.encode())

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
            result = runner.invoke(app, [
                "workflow", "add",
                "https://ghes.example/org/repo/releases/download/v1.0/workflow.yml",
            ])

        assert result.exit_code == 0, result.output
        # Tag lookup must use the GHES /api/v3 endpoint
        assert any("ghes.example/api/v3/repos/org/repo/releases/tags/v1.0" in url for url, _ in captured_urls)
        # Asset download must carry Accept: application/octet-stream
        asset_calls = [(url, h) for url, h in captured_urls if "releases/assets/" in url]
        assert len(asset_calls) >= 1
        assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    def test_workflow_add_catalog_based_ghes_release_url_resolves_via_api_v3(self, project_dir, monkeypatch):
        """'workflow add <id>' with a GHES catalog URL resolves via /api/v3."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        from specify_cli.authentication import http as _auth_http
        from specify_cli.authentication.config import AuthConfigEntry

        monkeypatch.setattr(_auth_http, "_config_override", [
            AuthConfigEntry(hosts=("ghes.example",), provider="github", auth="bearer", token="t"),
        ])

        captured_urls = []

        class FakeResponse:
            def __init__(self, data, url=None):
                self._data = data
                self._pos = 0
                self._url = url or "https://ghes.example/api/v3/repos/org/repo/releases/assets/55"

            def read(self, size=-1):
                if size < 0:
                    size = len(self._data) - self._pos
                out = self._data[self._pos : self._pos + size]
                self._pos += len(out)
                return out

            def geturl(self):
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        ghes_wf_yaml = """
schema_version: "1.0"
workflow:
  id: "my-wf"
  name: "My GHES Workflow"
  version: "1.0.0"
  description: "A GHES catalog workflow"
steps:
  - id: step-one
    type: shell
    run: "echo hello"
"""

        def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
            captured_urls.append((url, extra_headers))
            if "releases/tags/" in url:
                return FakeResponse(json.dumps({
                    "assets": [{"name": "workflow.yml", "url": "https://ghes.example/api/v3/repos/org/repo/releases/assets/55"}]
                }).encode())
            return FakeResponse(ghes_wf_yaml.encode())

        fake_catalog_info = {
            "id": "my-wf",
            "name": "My GHES Workflow",
            "version": "1.0.0",
            "url": "https://ghes.example/org/repo/releases/download/v2.0/workflow.yml",
            "_install_allowed": True,
        }

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url), \
             patch("specify_cli.workflows.catalog.WorkflowCatalog.get_workflow_info", return_value=fake_catalog_info):
            result = runner.invoke(app, ["workflow", "add", "my-wf"])

        assert result.exit_code == 0, result.output
        # Tag lookup must use GHES /api/v3
        tag_calls = [url for url, _ in captured_urls if "releases/tags/" in url]
        assert len(tag_calls) == 1
        assert "ghes.example/api/v3/repos/org/repo/releases/tags/v2.0" in tag_calls[0]
        # Asset download must carry Accept: application/octet-stream
        asset_calls = [(url, h) for url, h in captured_urls if "releases/assets/" in url]
        assert len(asset_calls) >= 1
        assert asset_calls[0][1] == {"Accept": "application/octet-stream"}



class TestWorkflowAddNonStringScalars:
    """`workflow add` reports clean errors for non-string YAML scalars (#3420)."""

    @pytest.mark.parametrize(
        ("field_yaml", "expected"),
        [
            ('id: 123\n  name: "Probe"\n  version: "1.0.0"', "workflow.id"),
            ('id: "probe"\n  name: "Probe"\n  version: 1.0', "workflow.version"),
        ],
    )
    def test_add_reports_validation_error_not_traceback(
        self, project_dir, monkeypatch, field_yaml, expected
    ):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        wf = project_dir / "workflow.yml"
        wf.write_text(
            "schema_version: \"1.0\"\n"
            f"workflow:\n  {field_yaml}\n"
            "steps:\n  - id: s1\n    type: shell\n    run: \"echo hi\"\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "add", str(wf)])
        assert result.exit_code == 1
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert expected in result.output

    def test_add_non_string_step_id_reports_validation_error(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        wf = project_dir / "workflow.yml"
        wf.write_text(
            "workflow:\n  id: \"probe\"\n  name: \"Probe\"\n  version: \"1.0.0\"\n"
            "steps:\n  - id: 123\n    type: shell\n    run: \"echo hi\"\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "add", str(wf)])
        assert result.exit_code == 1
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Step ID" in result.output



class TestWorkflowAddSymlinkGuard:
    def test_add_malformed_ipv6_url_exits_cleanly(self, temp_dir, monkeypatch):
        """A malformed IPv6 URL must produce a clean error, not a ValueError traceback."""
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify").mkdir(exist_ok=True)
        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(
            app,
            ["workflow", "add", "https://[::1/wf.yaml"],
            catch_exceptions=True,
        )

        assert result.exit_code == 1
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Invalid URL" in result.output

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_add_refuses_symlinked_specify(self, temp_dir, monkeypatch):
        """workflow add must refuse a symlinked .specify (writes could escape root)."""
        from typer.testing import CliRunner
        from specify_cli import app

        outside = temp_dir.parent / "outside-specify-target"
        (outside / "workflows").mkdir(parents=True, exist_ok=True)
        (temp_dir / ".specify").symlink_to(outside, target_is_directory=True)

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", "anything.yml"])

        assert result.exit_code != 0
        assert "symlinked .specify" in result.output

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_add_refuses_symlinked_workflows_dir(self, temp_dir, monkeypatch):
        """workflow add must refuse a symlinked .specify/workflows directory."""
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify").mkdir()
        outside = temp_dir.parent / "outside-workflows-target"
        outside.mkdir(parents=True, exist_ok=True)
        (temp_dir / ".specify" / "workflows").symlink_to(outside, target_is_directory=True)

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", "anything.yml"])

        assert result.exit_code != 0
        assert "symlinked .specify/workflows" in result.output

    def test_add_escapes_rich_markup_in_validation_errors(self, temp_dir, monkeypatch):
        """User-controlled YAML values in validation errors must not be parsed as Rich markup."""
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)
        src = temp_dir / "incoming.yml"
        src.write_text(
            """
schema_version: "1.0"
workflow:
  id: "markup-wf"
  name: "Markup"
  version: "[bold]bad[/bold]"

steps:
  - id: step-one
    command: speckit.specify
""",
            encoding="utf-8",
        )

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(src)])

        assert result.exit_code != 0
        assert "[bold]bad[/bold]" in result.output

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_add_refuses_symlinked_id_dir(self, temp_dir, monkeypatch, sample_workflow_yaml):
        """A symlinked <id> install dir must not let a copy escape the project root."""
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)
        outside = temp_dir.parent / "outside-id-target"
        outside.mkdir(parents=True, exist_ok=True)
        # <id> from the YAML below is "test-workflow"; plant it as a symlink.
        (temp_dir / ".specify" / "workflows" / "test-workflow").symlink_to(
            outside, target_is_directory=True
        )
        src = temp_dir / "incoming.yml"
        src.write_text(sample_workflow_yaml, encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(src)])

        assert result.exit_code != 0
        # No write-through: the symlink target stays empty.
        assert not (outside / "workflow.yml").exists()

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_add_refuses_symlinked_workflow_yml_leaf(self, temp_dir, monkeypatch, sample_workflow_yaml):
        """A symlinked <id>/workflow.yml must not let copy2 write through the link."""
        from typer.testing import CliRunner
        from specify_cli import app

        id_dir = temp_dir / ".specify" / "workflows" / "test-workflow"
        id_dir.mkdir(parents=True)
        outside_file = temp_dir.parent / "outside-leaf-target.yml"
        outside_file.write_text("original\n", encoding="utf-8")
        (id_dir / "workflow.yml").symlink_to(outside_file)
        src = temp_dir / "incoming.yml"
        src.write_text(sample_workflow_yaml, encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(src)])

        assert result.exit_code != 0
        # Rich may wrap the message; assert on the unbroken path fragment.
        assert "test-workflow/workflow.yml" in result.output
        assert "symlinked" in result.output
        # The link target content is untouched.
        assert outside_file.read_text(encoding="utf-8") == "original\n"

    def test_add_refuses_non_directory_id(self, temp_dir, monkeypatch, sample_workflow_yaml):
        """An <id> path that already exists as a file must fail cleanly, not crash."""
        from typer.testing import CliRunner
        from specify_cli import app

        wf_dir = temp_dir / ".specify" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "test-workflow").write_text("not a dir", encoding="utf-8")
        src = temp_dir / "incoming.yml"
        src.write_text(sample_workflow_yaml, encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(src)])

        assert result.exit_code != 0
        assert "exists but is not a directory" in result.output
        assert result.exception is None or isinstance(result.exception, SystemExit)

    def test_add_refuses_workflow_yml_as_directory(self, temp_dir, monkeypatch, sample_workflow_yaml):
        """A pre-existing <id>/workflow.yml *directory* must fail cleanly, not crash."""
        from typer.testing import CliRunner
        from specify_cli import app

        id_dir = temp_dir / ".specify" / "workflows" / "test-workflow"
        id_dir.mkdir(parents=True)
        # Plant workflow.yml as a directory so a later write/copy2 would raise
        # IsADirectoryError without the explicit non-file guard.
        (id_dir / "workflow.yml").mkdir()
        src = temp_dir / "incoming.yml"
        src.write_text(sample_workflow_yaml, encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(src)])

        assert result.exit_code != 0
        assert "test-workflow/workflow.yml" in result.output
        assert "is not a file" in result.output
        # Clean exit, not an unhandled IsADirectoryError traceback.
        assert result.exception is None or isinstance(result.exception, SystemExit)

    def test_safe_workflow_id_dir_escapes_markup_in_invalid_id(self, temp_dir, capsys):
        """A traversal <id> carrying Rich markup must be escaped, not interpreted."""
        from specify_cli.workflows._commands import _safe_workflow_id_dir

        workflows_dir = temp_dir / ".specify" / "workflows"
        workflows_dir.mkdir(parents=True)
        # Traversal (so the "Invalid workflow ID" branch fires) plus markup.
        with pytest.raises(typer.Exit):
            _safe_workflow_id_dir(workflows_dir, "../[red]evil[/red]")

        out = capsys.readouterr().out
        # Literal bracketed text survives; Rich did not consume it as a tag.
        assert "[red]evil[/red]" in out

    def test_add_rejects_reserved_overlay_storage_id(self, temp_dir, monkeypatch):
        """workflow add must not install into the overlay storage directory."""
        from typer.testing import CliRunner
        from specify_cli import app

        (temp_dir / ".specify" / "workflows").mkdir(parents=True)
        overlay_file = temp_dir / "incoming.yml"
        overlay_file.write_text(
            """
schema_version: "1.0"
workflow:
  id: "overlays"
  name: "Bad Workflow"
  version: "1.0.0"
steps:
  - id: step-one
    command: speckit.specify
""".strip()
            + "\n",
            encoding="utf-8",
        )

        monkeypatch.chdir(temp_dir)
        result = CliRunner().invoke(app, ["workflow", "add", str(overlay_file)])

        assert result.exit_code != 0
        assert "Invalid workflow ID" in result.output
        assert not (temp_dir / ".specify" / "workflows" / "overlays" / "workflow.yml").exists()

    @pytest.mark.parametrize(
        "workflow_id",
        [
            "overlays",
            "runs",
            "steps",
            "nested/workflow",
            "nested\\workflow",
            "bad id",
            " bad-id",
            "bad-id ",
            "a" * 201,
        ],
    )
    def test_safe_workflow_id_dir_rejects_reserved_or_non_segment_ids(
        self, temp_dir, workflow_id, capsys
    ):
        """Install IDs must not collide with workflow internals or create nested paths."""
        from specify_cli.workflows._commands import _safe_workflow_id_dir

        workflows_dir = temp_dir / ".specify" / "workflows"
        workflows_dir.mkdir(parents=True)

        with pytest.raises(typer.Exit):
            _safe_workflow_id_dir(workflows_dir, workflow_id)

        assert "Invalid workflow ID" in capsys.readouterr().out
        assert not (workflows_dir / workflow_id).exists()



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

    def _archive_workflow_dir(self, source_dir, archive_path, nested=False):
        prefix = Path("align-wf-v1") if nested else Path()
        if archive_path.name.lower().endswith(".zip"):
            with zipfile.ZipFile(archive_path, "w") as archive:
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file():
                        archive.write(
                            file_path,
                            prefix / file_path.relative_to(source_dir),
                        )
        else:
            with tarfile.open(archive_path, "w:gz") as archive:
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file():
                        archive.add(
                            file_path,
                            arcname=prefix / file_path.relative_to(source_dir),
                        )

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

    def test_add_dev_directory_installs(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        self._install_dev(runner, app, project_dir)
        assert WorkflowRegistry(project_dir).is_installed("align-wf")

    def test_add_local_directory_preserves_package_files(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        source = self._write_workflow_dir(project_dir)
        (source / "scripts").mkdir()
        (source / "scripts" / "helper.sh").write_text("echo helper\n")

        result = CliRunner().invoke(app, ["workflow", "add", str(source)])

        assert result.exit_code == 0, result.output
        installed = project_dir / ".specify" / "workflows" / "align-wf"
        assert (installed / "scripts" / "helper.sh").read_text() == "echo helper\n"

    @pytest.mark.parametrize("suffix", [".zip", ".tar.gz", ".tgz"])
    @pytest.mark.parametrize("nested", [False, True])
    def test_add_local_archive_preserves_package_files(
        self, project_dir, monkeypatch, suffix, nested
    ):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        source = self._write_workflow_dir(project_dir)
        (source / "assets").mkdir()
        (source / "assets" / "message.txt").write_text("hello\n")
        archive_path = project_dir / f"align-wf{suffix}"
        self._archive_workflow_dir(source, archive_path, nested=nested)

        result = CliRunner().invoke(app, ["workflow", "add", str(archive_path)])

        assert result.exit_code == 0, result.output
        installed = project_dir / ".specify" / "workflows" / "align-wf"
        assert (installed / "assets" / "message.txt").read_text() == "hello\n"

    def test_add_dev_yaml_file_installs(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        src = self._write_workflow_dir(project_dir)
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "add", str(src / "workflow.yml"), "--dev"])
        assert result.exit_code == 0, result.output
        assert WorkflowRegistry(project_dir).is_installed("align-wf")

    def test_add_dev_missing_path_errors(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "add", str(project_dir / "missing"), "--dev"])
        assert result.exit_code != 0
        assert "--dev" in result.output

    def test_add_dev_dir_without_workflow_yml_errors(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        empty = project_dir / "empty-src"
        empty.mkdir()
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "add", str(empty), "--dev"])
        assert result.exit_code != 0
        assert "No workflow.yml found" in result.output

    def test_add_local_dir_without_workflow_yml_errors(self, project_dir, monkeypatch):
        """Same as the --dev case, but for the plain local-path fallback (no --dev)."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        empty = project_dir / "empty-src-[bracket]"
        empty.mkdir()
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "add", str(empty)])
        assert result.exit_code != 0
        assert "No workflow.yml found" in result.output
        assert "[bracket]" in result.output

    def test_add_local_dir_with_workflow_yml_directory_errors_cleanly(self, project_dir, monkeypatch):
        """Same as the --dev case, but for the plain local-path fallback (no --dev):
        a directory named workflow.yml must not reach open() and leak IsADirectoryError."""
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        src_dir = project_dir / "local-wf"
        (src_dir / "workflow.yml").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "add", str(src_dir)])
        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "No workflow.yml found" in result.output

    def test_add_yaml_parse_error_escapes_rich_markup(self, project_dir, monkeypatch):
        """A YAML syntax error can quote the offending line verbatim; brackets in it must not be Rich markup."""
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.engine import WorkflowDefinition

        monkeypatch.chdir(project_dir)
        bad = project_dir / "bad.yml"
        bad.write_text("workflow:\n  id: wf\n", encoding="utf-8")
        runner = CliRunner()
        with patch.object(
            WorkflowDefinition,
            "from_string",
            side_effect=ValueError('bad snippet: "New [Feature]"'),
        ):
            result = runner.invoke(app, ["workflow", "add", str(bad)])
        assert result.exit_code != 0
        assert 'bad snippet: "New [Feature]"' in result.output

    @pytest.mark.parametrize("mode", ["dev", "local", "from"])
    def test_reinstall_preserves_disabled_state(
        self, project_dir, monkeypatch, mode
    ):
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        src = self._install_dev(runner, app, project_dir)
        result = runner.invoke(app, ["workflow", "disable", "align-wf"])
        assert result.exit_code == 0, result.output

        if mode == "dev":
            result = runner.invoke(
                app, ["workflow", "add", str(src), "--dev"]
            )
        elif mode == "local":
            result = runner.invoke(app, ["workflow", "add", str(src)])
        else:
            data = self.WORKFLOW_YAML.format(version="2.0.0").encode()
            with patch(
                "specify_cli.authentication.http.open_url",
                side_effect=lambda url, timeout=None, extra_headers=None,
                redirect_validator=None: self._FakeResponse(data, url),
            ):
                result = runner.invoke(
                    app,
                    [
                        "workflow", "add", "align-wf",
                        "--from", "https://example.com/workflow.yml",
                    ],
                    input="y\n",
                )

        assert result.exit_code == 0, result.output
        assert WorkflowRegistry(project_dir).get("align-wf")["enabled"] is False

    def test_add_from_url_rejects_oversized_content_length(self, project_dir, monkeypatch):
        """A --from download must not trust an advertised Content-Length
        alone by reading the whole body first -- it must reject a response
        that declares a size over the workflow YAML limit before reading
        the (potentially huge) body into memory at all."""
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands as wf_commands

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(wf_commands, "_MAX_WORKFLOW_YAML_BYTES", 100)
        small_body = b"id: align-wf\n"  # small actual body; Content-Length lies
        runner = CliRunner()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                small_body, url, headers={"Content-Length": "1000"}
            ),
        ):
            result = runner.invoke(
                app,
                ["workflow", "add", "align-wf", "--from", "https://example.com/workflow.yml"],
                input="y\n",
            )
        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "exceedingthe100-byteworkflowsizelimit" in "".join(result.output.split())

    def test_add_from_url_requires_default_deny_confirmation(
        self, project_dir, monkeypatch
    ):
        from unittest.mock import patch

        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=AssertionError("download should not start"),
        ):
            result = CliRunner().invoke(
                app,
                [
                    "workflow",
                    "add",
                    "align-wf",
                    "--from",
                    "https://example.com/workflow.yml",
                ],
                input="n\n",
            )

        assert result.exit_code == 0, result.output
        assert "Untrusted Source" in result.output
        assert "Cancelled" in result.output

    def test_add_from_url_rejects_oversized_streamed_body_without_content_length(
        self, project_dir, monkeypatch
    ):
        """A chunked/no-Content-Length response must still be capped by
        actually counting streamed bytes -- a malicious or misbehaving
        server cannot bypass the limit merely by omitting or lying about
        Content-Length."""
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands as wf_commands

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(wf_commands, "_MAX_WORKFLOW_YAML_BYTES", 100)
        oversized_body = b"x" * 500  # no Content-Length header at all
        runner = CliRunner()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                oversized_body, url
            ),
        ):
            result = runner.invoke(
                app,
                ["workflow", "add", "align-wf", "--from", "https://example.com/workflow.yml"],
                input="y\n",
            )
        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "exceedsthe100-byteworkflowsizelimit" in "".join(result.output.split())

    def test_add_from_url_oversized_streamed_body_leaves_no_temp_file(
        self, project_dir, monkeypatch, tmp_path
    ):
        """A rejected --from download (oversized streamed body, no
        Content-Length) must not leave the 0-byte NamedTemporaryFile behind:
        the file is created on disk as soon as it is opened (delete=False),
        before any bytes are written, so a failure inside the size-limit
        check must still clean it up rather than merely erroring out."""
        import tempfile as tempfile_mod
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands as wf_commands

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(wf_commands, "_MAX_WORKFLOW_YAML_BYTES", 100)
        scratch_tmp = tmp_path / "scratch-tmp"
        scratch_tmp.mkdir()
        monkeypatch.setattr(tempfile_mod, "tempdir", str(scratch_tmp))
        oversized_body = b"x" * 500  # no Content-Length header at all
        runner = CliRunner()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                oversized_body, url
            ),
        ):
            result = runner.invoke(
                app,
                ["workflow", "add", "align-wf", "--from", "https://example.com/workflow.yml"],
                input="y\n",
            )
        assert result.exit_code != 0
        assert "exceedsthe100-byteworkflowsizelimit" in "".join(result.output.split())
        leaked = list(scratch_tmp.glob("*.yml"))
        assert leaked == [], f"leaked temp files: {leaked}"

    def test_add_from_url_interrupt_during_read_leaves_no_temp_file(
        self, project_dir, monkeypatch, tmp_path
    ):
        """A KeyboardInterrupt while streaming the response body must still
        unlink the already-created (delete=False) temp file. Unlike a
        download ``ValueError``, ``KeyboardInterrupt`` is a ``BaseException``
        and is not caught by ``except Exception`` -- only a ``BaseException``
        handler around the temp-file lifetime can clean it up."""
        import tempfile as tempfile_mod
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands as wf_commands

        monkeypatch.chdir(project_dir)
        scratch_tmp = tmp_path / "scratch-tmp"
        scratch_tmp.mkdir()
        monkeypatch.setattr(tempfile_mod, "tempdir", str(scratch_tmp))

        def _boom(*args, **kwargs):
            raise KeyboardInterrupt()

        monkeypatch.setattr(wf_commands, "_read_response_within_limit", _boom)
        body = b"id: align-wf\n"
        runner = CliRunner()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                body, url
            ),
        ):
            result = runner.invoke(
                app,
                ["workflow", "add", "align-wf", "--from", "https://example.com/workflow.yml"],
                input="y\n",
            )
        assert result.exit_code != 0
        leaked = list(scratch_tmp.glob("*.yml"))
        assert leaked == [], f"leaked temp files: {leaked}"

    def test_add_from_url_oversized_content_length_leaves_no_temp_file(
        self, project_dir, monkeypatch, tmp_path
    ):
        """Same guarantee for the fail-fast Content-Length rejection path:
        it must not even leave a 0-byte temp file behind."""
        import tempfile as tempfile_mod
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands as wf_commands

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(wf_commands, "_MAX_WORKFLOW_YAML_BYTES", 100)
        scratch_tmp = tmp_path / "scratch-tmp"
        scratch_tmp.mkdir()
        monkeypatch.setattr(tempfile_mod, "tempdir", str(scratch_tmp))
        small_body = b"id: align-wf\n"  # small actual body; Content-Length lies
        runner = CliRunner()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                small_body, url, headers={"Content-Length": "1000"}
            ),
        ):
            result = runner.invoke(
                app,
                ["workflow", "add", "align-wf", "--from", "https://example.com/workflow.yml"],
                input="y\n",
            )
        assert result.exit_code != 0
        assert "exceedingthe100-byteworkflowsizelimit" in "".join(result.output.split())
        leaked = list(scratch_tmp.glob("*.yml"))
        assert leaked == [], f"leaked temp files: {leaked}"

    def test_add_from_url_download_failure_cleanup_error_preserves_original_error(
        self, project_dir, monkeypatch, tmp_path
    ):
        """The --from download-failure branch's `tmp_path.unlink(missing_ok=
        True)` can itself raise (e.g. read-only tempdir) before the clean
        "Failed to download workflow" message is ever printed, replacing it
        with a raw unhandled OSError. A cleanup failure there must be
        guarded exactly like the later post-install finally cleanup: warn
        about the cleanup failure, then still preserve/report the original
        download error via a clean typer.Exit, never a raw traceback."""
        import tempfile as tempfile_mod
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands as wf_commands
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(wf_commands, "_MAX_WORKFLOW_YAML_BYTES", 100)
        scratch_tmp = tmp_path / "scratch-tmp"
        scratch_tmp.mkdir()
        monkeypatch.setattr(tempfile_mod, "tempdir", str(scratch_tmp))
        oversized_body = b"x" * 500  # no Content-Length header at all
        runner = CliRunner()

        real_unlink = Path.unlink

        def unlink_boom(self_path, *args, **kwargs):
            if self_path.suffix == ".yml" and self_path.parent == scratch_tmp:
                raise OSError("cleanup denied")
            return real_unlink(self_path, *args, **kwargs)

        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                oversized_body, url
            ),
        ), pytest.MonkeyPatch.context() as mp:
            mp.setattr(Path, "unlink", unlink_boom)
            result = runner.invoke(
                app,
                ["workflow", "add", "align-wf", "--from", "https://example.com/workflow.yml"],
                input="y\n",
            )

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        # Original download error remains present. Normalize whitespace so the
        # assertion is robust to Rich line-wrapping at narrow terminal widths.
        normalized_output = "".join(result.output.split())
        assert "exceedsthe100-byteworkflowsizelimit" in normalized_output
        # Cleanup failure is reported too, not silently swallowed / crashing.
        assert "cleanupdenied" in normalized_output
        assert "Warning" in result.output
        assert not WorkflowRegistry(project_dir).is_installed("align-wf")

    def test_add_from_url_installs(self, project_dir, monkeypatch):
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
        runner = CliRunner()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(data, url),
        ):
            result = runner.invoke(
                app,
                ["workflow", "add", "align-wf", "--from", "https://example.com/workflow.yml"],
                input="y\n",
            )
        assert result.exit_code == 0, result.output
        assert WorkflowRegistry(project_dir).is_installed("align-wf")

    @pytest.mark.parametrize("suffix", [".zip", ".tar.gz", ".tgz"])
    def test_add_from_url_installs_complete_archive_package(
        self, project_dir, monkeypatch, suffix
    ):
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        source = self._write_workflow_dir(project_dir)
        (source / "assets").mkdir()
        (source / "assets" / "remote.txt").write_text("remote\n")
        archive_path = project_dir / f"remote{suffix}"
        self._archive_workflow_dir(source, archive_path)
        data = archive_path.read_bytes()
        url = f"https://example.com/align-wf{suffix}"

        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda *_args, **_kwargs: self._FakeResponse(data, url),
        ):
            result = CliRunner().invoke(
                app,
                ["workflow", "add", "align-wf", "--from", url],
                input="y\n",
            )

        assert result.exit_code == 0, result.output
        installed = project_dir / ".specify" / "workflows" / "align-wf"
        assert (installed / "assets" / "remote.txt").read_text() == "remote\n"

    @pytest.mark.parametrize("suffix", [".zip", ".tar.gz", ".tgz"])
    def test_add_from_suffixless_url_sniffs_archive(
        self, project_dir, monkeypatch, suffix
    ):
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        source = self._write_workflow_dir(project_dir)
        (source / "assets").mkdir()
        (source / "assets" / "sniffed.txt").write_text("sniffed\n")
        archive_path = project_dir / f"remote{suffix}"
        self._archive_workflow_dir(source, archive_path)
        data = archive_path.read_bytes()
        url = "https://example.com/assets/12345"

        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda *_args, **_kwargs: self._FakeResponse(
                data,
                url,
                {"Content-Type": "application/octet-stream"},
            ),
        ):
            result = CliRunner().invoke(
                app,
                ["workflow", "add", "align-wf", "--from", url],
                input="y\n",
            )

        assert result.exit_code == 0, result.output
        installed = project_dir / ".specify" / "workflows" / "align-wf"
        assert (installed / "assets" / "sniffed.txt").read_text() == "sniffed\n"

    @pytest.mark.parametrize("suffix", [".zip", ".tar.gz", ".tgz"])
    def test_add_catalog_installs_complete_archive_package_and_sha(
        self, project_dir, monkeypatch, suffix
    ):
        import hashlib
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog

        monkeypatch.chdir(project_dir)
        source = self._write_workflow_dir(project_dir)
        (source / "assets").mkdir()
        (source / "assets" / "catalog.txt").write_text("catalog\n")
        archive_path = project_dir / f"catalog{suffix}"
        self._archive_workflow_dir(source, archive_path, nested=True)
        data = archive_path.read_bytes()
        url = f"https://example.com/align-wf{suffix}"
        info = {
            "id": "align-wf",
            "name": "Align Workflow",
            "version": "1.0.0",
            "url": url,
            "sha256": hashlib.sha256(data).hexdigest(),
            "_install_allowed": True,
            "_catalog_name": "test",
        }

        with patch.object(
            WorkflowCatalog,
            "get_workflow_info",
            return_value=info,
        ), patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda *_args, **_kwargs: self._FakeResponse(data, url),
        ):
            result = CliRunner().invoke(app, ["workflow", "add", "align-wf"])

        assert result.exit_code == 0, result.output
        installed = project_dir / ".specify" / "workflows" / "align-wf"
        assert (installed / "assets" / "catalog.txt").read_text() == "catalog\n"

    @pytest.mark.parametrize("suffix", [".zip", ".tar.gz", ".tgz"])
    def test_add_catalog_sniffs_suffixless_archive(
        self, project_dir, monkeypatch, suffix
    ):
        import hashlib
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog

        monkeypatch.chdir(project_dir)
        source = self._write_workflow_dir(project_dir)
        (source / "assets").mkdir()
        (source / "assets" / "sniffed.txt").write_text("catalog sniffed\n")
        archive_path = project_dir / f"catalog{suffix}"
        self._archive_workflow_dir(source, archive_path, nested=True)
        data = archive_path.read_bytes()
        url = "https://example.com/assets/67890"
        info = {
            "id": "align-wf",
            "name": "Align Workflow",
            "version": "1.0.0",
            "url": url,
            "sha256": hashlib.sha256(data).hexdigest(),
            "_install_allowed": True,
            "_catalog_name": "test",
        }

        with patch.object(
            WorkflowCatalog,
            "get_workflow_info",
            return_value=info,
        ), patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda *_args, **_kwargs: self._FakeResponse(
                data,
                url,
                {"Content-Type": "application/octet-stream"},
            ),
        ):
            result = CliRunner().invoke(app, ["workflow", "add", "align-wf"])

        assert result.exit_code == 0, result.output
        installed = project_dir / ".specify" / "workflows" / "align-wf"
        assert (
            installed / "assets" / "sniffed.txt"
        ).read_text() == "catalog sniffed\n"

    def test_package_registry_failure_restores_before_failed_cleanup(
        self, project_dir, monkeypatch
    ):
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        source = self._write_workflow_dir(project_dir, version="1.0.0")
        (source / "assets").mkdir()
        (source / "assets" / "version.txt").write_text("old\n")
        runner = CliRunner()
        first = runner.invoke(app, ["workflow", "add", str(source)])
        assert first.exit_code == 0, first.output

        (source / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="2.0.0"),
            encoding="utf-8",
        )
        (source / "assets" / "version.txt").write_text("new\n")
        real_rmtree = shutil.rmtree

        def fail_failed_package_cleanup(path, *args, **kwargs):
            if ".failed-" in Path(path).name:
                raise OSError("cleanup denied")
            return real_rmtree(path, *args, **kwargs)

        with patch.object(
            WorkflowRegistry,
            "add",
            side_effect=OSError("registry save failed"),
        ), patch(
            "shutil.rmtree",
            side_effect=fail_failed_package_cleanup,
        ):
            result = runner.invoke(app, ["workflow", "add", str(source)])

        assert result.exit_code == 1, result.output
        installed = project_dir / ".specify" / "workflows" / "align-wf"
        assert "1.0.0" in (installed / "workflow.yml").read_text()
        assert (installed / "assets" / "version.txt").read_text() == "old\n"
        assert "registry save failed" in result.output
        assert "cleanup denied" in result.output

    def test_add_from_url_temp_cleanup_failure_after_success_still_exits_zero(
        self, project_dir, monkeypatch
    ):
        """An OSError while deleting the --from download's temp file after
        _validate_and_install_local() has already committed the file and
        registry entry must not surface as an unhandled failure for an
        install that already succeeded -- it must be a warning, exit 0."""
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
        runner = CliRunner()


        real_unlink = Path.unlink

        def unlink_boom(self_path, *args, **kwargs):
            if self_path.suffix == ".yml" and self_path.parent == Path(tempfile.gettempdir()):
                raise OSError("permission denied")
            return real_unlink(self_path, *args, **kwargs)

        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(data, url),
        ), pytest.MonkeyPatch.context() as mp:
            mp.setattr(Path, "unlink", unlink_boom)
            result = runner.invoke(
                app,
                ["workflow", "add", "align-wf", "--from", "https://example.com/workflow.yml"],
                input="y\n",
            )

        assert result.exit_code == 0, result.output
        assert "Warning" in result.output
        assert "permissiondenied" in "".join(result.output.split())
        assert WorkflowRegistry(project_dir).is_installed("align-wf")

    def test_add_from_url_id_mismatch_errors(self, project_dir, monkeypatch):
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
        runner = CliRunner()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(data, url),
        ):
            result = runner.invoke(
                app,
                ["workflow", "add", "other-id", "--from", "https://example.com/workflow.yml"],
                input="y\n",
            )
        assert result.exit_code != 0
        assert "does not match" in result.output
        assert not WorkflowRegistry(project_dir).is_installed("align-wf")

    def test_add_from_empty_url_rejected_not_catalog_fallback(self, project_dir, monkeypatch):
        """--from "" must fail URL validation, not silently install from the catalog."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "add", "align-wf", "--from", ""])
        assert result.exit_code != 0
        assert "HTTPS" in result.output
        assert not WorkflowRegistry(project_dir).is_installed("align-wf")

    def test_add_from_url_non_https_redirect_escapes_rich_markup(self, project_dir, monkeypatch):
        """A redirect to a non-HTTPS IPv6 literal (legally bracketed) must not be parsed as Rich markup."""
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        redirected_url = "http://[2001:db8::1]/workflow.yml"
        runner = CliRunner()
        with patch(
            "specify_cli.authentication.http.open_url",
            side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(b"", redirected_url),
        ):
            result = runner.invoke(
                app,
                ["workflow", "add", "align-wf", "--from", "https://example.com/workflow.yml"],
                input="y\n",
            )
        assert result.exit_code != 0
        assert redirected_url in result.output

    def test_add_from_rejects_invalid_source_id_without_fetch(self, project_dir, monkeypatch):
        """--from with a non-workflow-id source (URL, path, uppercase) fails before any network fetch."""
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        calls: list[str] = []

        def _fake_open(url, timeout=None, extra_headers=None, redirect_validator=None):
            calls.append(url)
            raise AssertionError(f"network fetch attempted: {url}")

        runner = CliRunner()
        with patch("specify_cli.authentication.http.open_url", side_effect=_fake_open):
            for bad_source in ("https://x/y.yml", "./local.yml", "BadCase"):
                result = runner.invoke(
                    app,
                    ["workflow", "add", bad_source, "--from", "https://example.com/workflow.yml"],
                )
                assert result.exit_code != 0
                assert "Invalid workflow ID" in result.output
        assert calls == []

    def test_add_dev_dir_with_workflow_yml_directory_errors_cleanly(self, project_dir, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        dev_dir = project_dir / "dev-wf"
        (dev_dir / "workflow.yml").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "add", "--dev", str(dev_dir)])
        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "No workflow.yml found" in result.output

    @pytest.mark.parametrize("mode", ["dev", "local", "from_url"])
    def test_add_save_failure_leaves_no_orphan_directory(self, project_dir, monkeypatch, mode):
        """A registry.add() save failure during a fresh install must not leave
        an orphaned workflow directory on disk, and must fail with a clean
        escaped message instead of a raw OSError traceback. Shared by --dev,
        the plain local-path fallback, and --from since all three funnel
        through _validate_and_install_local's single install choke point."""
        import contextlib
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()

        def boom(self):
            raise OSError("disk full")

        if mode == "from_url":
            data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
            args = ["workflow", "add", "align-wf", "--from", "https://example.com/workflow.yml"]
            url_patch = patch(
                "specify_cli.authentication.http.open_url",
                side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(data, url),
            )
        else:
            src = self._write_workflow_dir(project_dir)
            args = ["workflow", "add", str(src)] + (["--dev"] if mode == "dev" else [])
            url_patch = contextlib.nullcontext()

        with url_patch, pytest.MonkeyPatch.context() as mp:
            mp.setattr(WorkflowRegistry, "save", boom)
            result = runner.invoke(
                app, args, input="y\n" if mode == "from_url" else None
            )

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert result.output.strip() != ""
        dest_dir = project_dir / ".specify" / "workflows" / "align-wf"
        assert not dest_dir.exists()
        assert not WorkflowRegistry(project_dir).is_installed("align-wf")

    @pytest.mark.parametrize("mode", ["dev", "catalog"])
    def test_add_non_json_description_rolls_back_transaction(
        self, project_dir, monkeypatch, mode
    ):
        import contextlib
        from unittest.mock import patch

        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        data = self.WORKFLOW_YAML.format(version="1.0.0").replace(
            'description: "CLI alignment test workflow"',
            "description: 2026-01-02",
        ).encode()

        if mode == "dev":
            source = project_dir / "dated-description"
            source.mkdir()
            (source / "workflow.yml").write_bytes(data)
            args = ["workflow", "add", str(source), "--dev"]
            download = contextlib.nullcontext()
        else:
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
            args = ["workflow", "add", "align-wf"]
            download = patch(
                "specify_cli.authentication.http.open_url",
                side_effect=lambda url, timeout=None, extra_headers=None,
                redirect_validator=None: self._FakeResponse(data, url),
            )

        with download:
            result = CliRunner().invoke(app, args)

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Failed to update workflow registry" in result.output
        dest_dir = project_dir / ".specify" / "workflows" / "align-wf"
        assert not dest_dir.exists()
        assert not WorkflowRegistry(project_dir).is_installed("align-wf")

    @pytest.mark.parametrize("mode", ["dev", "local", "from_url"])
    def test_add_fresh_install_mkstemp_failure_leaves_no_orphan_directory(
        self, project_dir, monkeypatch, mode
    ):
        """_stage_workflow_file() does mkdir(dest_dir) then mkstemp() inside
        it. For a fresh install (no prior directory), if mkdir succeeds but
        mkstemp then fails (disk full/EMFILE/quota), the freshly-created
        empty dest_dir must not be left orphaned -- it must be removed, and
        the original mkstemp error must still be reported cleanly."""
        import contextlib
        from unittest.mock import patch
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()

        def boom(*args, **kwargs):
            raise OSError("disk full")

        if mode == "from_url":
            data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
            args = ["workflow", "add", "align-wf", "--from", "https://example.com/workflow.yml"]
            url_patch = patch(
                "specify_cli.authentication.http.open_url",
                side_effect=lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(data, url),
            )
        else:
            src = self._write_workflow_dir(project_dir)
            args = ["workflow", "add", str(src)] + (["--dev"] if mode == "dev" else [])
            url_patch = contextlib.nullcontext()

        with url_patch, pytest.MonkeyPatch.context() as mp:
            mp.setattr("tempfile.mkstemp", boom)
            result = runner.invoke(
                app, args, input="y\n" if mode == "from_url" else None
            )

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert result.output.strip() != ""
        dest_dir = project_dir / ".specify" / "workflows" / "align-wf"
        assert not dest_dir.exists(), "fresh-install dest_dir left orphaned after mkstemp failure"
        assert not WorkflowRegistry(project_dir).is_installed("align-wf")

    def test_add_reinstall_mkstemp_failure_preserves_preexisting_directory(
        self, project_dir, monkeypatch
    ):
        """A pre-existing (reinstall) dest_dir must never be removed by the
        mkstemp-failure cleanup -- only a directory _stage_workflow_file
        itself just created."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        src = self._install_dev(runner, app, project_dir)
        installed_yaml = project_dir / ".specify" / "workflows" / "align-wf" / "workflow.yml"
        original_bytes = installed_yaml.read_bytes()
        original_registry_entry = WorkflowRegistry(project_dir).get("align-wf")

        (src / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="2.0.0"), encoding="utf-8"
        )

        def boom(*args, **kwargs):
            raise OSError("disk full")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("tempfile.mkstemp", boom)
            result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert result.output.strip() != ""
        assert installed_yaml.parent.is_dir()
        assert installed_yaml.read_bytes() == original_bytes
        assert WorkflowRegistry(project_dir).get("align-wf") == original_registry_entry

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    @pytest.mark.parametrize("mode", ["dev", "catalog"])
    def test_stage_write_rejects_swapped_symlink(
        self, project_dir, monkeypatch, mode
    ):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands
        from specify_cli.workflows.catalog import WorkflowCatalog

        monkeypatch.chdir(project_dir)
        victim = project_dir / "victim.txt"
        victim.write_text("untouched", encoding="utf-8")

        real_stage = _commands._stage_workflow_file

        def raced_stage(*args, **kwargs):
            staged = real_stage(*args, **kwargs)
            staged_path = getattr(staged, "path", staged)
            staged_path.unlink()
            staged_path.symlink_to(victim)
            return staged

        monkeypatch.setattr(_commands, "_stage_workflow_file", raced_stage)

        if mode == "dev":
            source = self._write_workflow_dir(project_dir)
            args = ["workflow", "add", str(source), "--dev"]
        else:
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
            data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
            monkeypatch.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None,
                redirect_validator=None: self._FakeResponse(data, url),
            )
            args = ["workflow", "add", "align-wf"]

        result = CliRunner().invoke(app, args)

        assert result.exit_code != 0
        assert victim.read_text(encoding="utf-8") == "untouched"

    def test_local_install_writes_the_same_bytes_it_validates(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        source = self._write_workflow_dir(project_dir)
        source_file = source / "workflow.yml"
        validated_content = source_file.read_text(encoding="utf-8")
        replacement_content = self.WORKFLOW_YAML.format(version="9.9.9")

        real_stage = _commands._stage_workflow_file

        def replace_source_after_validation(*args, **kwargs):
            staged = real_stage(*args, **kwargs)
            source_file.write_text(replacement_content, encoding="utf-8")
            return staged

        monkeypatch.setattr(
            _commands,
            "_stage_workflow_file",
            replace_source_after_validation,
        )

        result = CliRunner().invoke(
            app, ["workflow", "add", str(source), "--dev"]
        )

        assert result.exit_code == 0, result.output
        installed_file = (
            project_dir
            / ".specify"
            / "workflows"
            / "align-wf"
            / "workflow.yml"
        )
        assert installed_file.read_text(encoding="utf-8") == validated_content
        assert WorkflowRegistry(project_dir).get("align-wf")["version"] == "1.0.0"

    def test_add_fresh_install_staged_discard_cleanup_failure_reports_warning(
        self, project_dir, monkeypatch
    ):
        """A genuine fresh-directory rmdir failure must be reported while
        the original copy failure remains the primary error."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        src = self._write_workflow_dir(project_dir)

        def copy_boom(self, data):
            raise OSError("disk full")

        real_rmdir = Path.rmdir

        def rmdir_boom(path):
            if path.name == "align-wf":
                raise OSError("cleanup denied")
            return real_rmdir(path)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(_commands._StagedWorkflowFile, "write_bytes", copy_boom)
            mp.setattr(Path, "rmdir", rmdir_boom)
            result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        # Original install error remains present and primary.
        assert "disk full" in result.output
        # Cleanup failure is now reported, not silently swallowed.
        assert "cleanup denied" in result.output
        assert "Warning" in result.output
        assert not WorkflowRegistry(project_dir).is_installed("align-wf")

    def test_add_fresh_install_registry_rollback_cleanup_failure_reports_warning(
        self, project_dir, monkeypatch
    ):
        """A fresh-install rollback directory-removal failure must be
        reported while the registry-update error remains primary."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        src = self._write_workflow_dir(project_dir)

        def save_boom(self):
            raise OSError("registry disk full")

        real_rmdir = Path.rmdir

        def rmdir_boom(path):
            if path.name == "align-wf":
                raise OSError("cleanup denied")
            return real_rmdir(path)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(WorkflowRegistry, "save", save_boom)
            mp.setattr(Path, "rmdir", rmdir_boom)
            result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        # Original registry-update error remains present and primary.
        assert "registry disk full" in result.output
        # Cleanup failure is now reported, not silently swallowed.
        assert "cleanup denied" in result.output
        assert "Warning" in result.output

    def test_add_dev_reinstall_copy_failure_leaves_prior_file_untouched(
        self, project_dir, monkeypatch
    ):
        """A staged descriptor-copy failure cannot touch the prior installed
        workflow or leave a staging file behind."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        src = self._install_dev(runner, app, project_dir)
        installed_yaml = project_dir / ".specify" / "workflows" / "align-wf" / "workflow.yml"
        original_bytes = installed_yaml.read_bytes()
        original_registry_entry = WorkflowRegistry(project_dir).get("align-wf")

        # Point --dev at a new version of the same workflow to trigger a
        # reinstall (overwrite) rather than a fresh install.
        (src / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="2.0.0"), encoding="utf-8"
        )

        def boom(staged, data):
            # Simulate a truncating partial write followed by an OSError on
            # the reserved staging inode, mirroring disk exhaustion.
            os.ftruncate(staged.fd, 0)
            raise OSError("disk full")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(_commands._StagedWorkflowFile, "write_bytes", boom)
            result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert result.output.strip() != ""
        assert installed_yaml.read_bytes() == original_bytes
        assert WorkflowRegistry(project_dir).get("align-wf") == original_registry_entry
        # No orphaned staging file left behind in the workflow directory.
        leftovers = [p.name for p in installed_yaml.parent.iterdir() if p.name != "workflow.yml"]
        assert leftovers == []

    def test_add_dev_successful_reinstall_leaves_no_backup_file(
        self, project_dir, monkeypatch
    ):
        """Once registry.add() succeeds, the unique rollback backup must be
        discarded rather than left as a permanent orphan sibling."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        src = self._install_dev(runner, app, project_dir)
        workflow_dir = project_dir / ".specify" / "workflows" / "align-wf"

        # Reinstall (overwrite) with a new version -- a successful reinstall,
        # not a failure path.
        (src / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="2.0.0"), encoding="utf-8"
        )
        result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])

        assert result.exit_code == 0, result.output
        registry = WorkflowRegistry(project_dir)
        assert registry.is_installed("align-wf")
        assert registry.get("align-wf")["version"] == "2.0.0"
        assert (workflow_dir / "workflow.yml").read_text(encoding="utf-8") == (
            self.WORKFLOW_YAML.format(version="2.0.0")
        )
        leftovers = [p.name for p in workflow_dir.iterdir() if p.name != "workflow.yml"]
        assert leftovers == [], f"orphan sibling(s) left behind: {leftovers}"

    def test_add_dev_successful_reinstall_backup_cleanup_failure_still_succeeds(
        self, project_dir, monkeypatch
    ):
        """A failure to clean up the now-unneeded backup file after a
        successful registry.add() must not turn the already-successful
        install into a reported failure: it must be a warning (exit 0),
        consistent with workflow_remove's post-commit cleanup semantics."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        src = self._install_dev(runner, app, project_dir)

        (src / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="2.0.0"), encoding="utf-8"
        )

        real_unlink = Path.unlink

        def unlink_boom(self_path, *args, **kwargs):
            if self_path.name.endswith(".bak"):
                raise OSError("permission denied")
            return real_unlink(self_path, *args, **kwargs)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(Path, "unlink", unlink_boom)
            result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])

        assert result.exit_code == 0, result.output
        assert "Warning" in result.output
        assert "permissiondenied" in "".join(result.output.split())
        registry = WorkflowRegistry(project_dir)
        assert registry.is_installed("align-wf")
        assert registry.get("align-wf")["version"] == "2.0.0"

    def test_add_dev_reinstall_restore_failure_reports_warning_and_original_error(
        self, project_dir, monkeypatch
    ):
        """The prior file is now restored via an atomic rename (not a
        content rewrite) when registry.add() fails on a reinstall. If that
        restore rename itself also fails (e.g. a transient FS issue), it
        must not silently claim success or crash with a raw traceback: it
        must report a clear warning about the restore failure in addition
        to the original clean registry error."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        src = self._install_dev(runner, app, project_dir)

        (src / "workflow.yml").write_text(
            self.WORKFLOW_YAML.format(version="2.0.0"), encoding="utf-8"
        )

        def save_boom(self):
            raise OSError("disk full")

        real_replace = os.replace
        calls = {"n": 0}

        def replace_boom(src_path, dst_path):
            # The commit swap for a reinstall makes exactly two os.replace
            # calls (backup-aside, then staged-into-dest); let both succeed
            # and only fail the third call -- the post-registry-failure
            # restore-back rename.
            calls["n"] += 1
            if calls["n"] <= 2:
                return real_replace(src_path, dst_path)
            raise OSError("permission denied")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(WorkflowRegistry, "save", save_boom)
            mp.setattr(os, "replace", replace_boom)
            result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])


        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        output_compact = "".join(result.output.split())
        assert "Warning" in result.output
        assert "diskfull" in output_compact
        assert "permissiondenied" in output_compact

    def test_add_dev_fresh_install_into_preexisting_empty_dir_cleans_new_file(
        self, project_dir, monkeypatch
    ):
        """When the destination directory already exists but has no
        workflow.yml (e.g. an empty dir left over from elsewhere), a later
        registry.add() failure must remove the newly copied file -- the
        rollback previously did nothing in this case (existed_before=True
        with no backup bytes), leaving the new file behind -- while leaving
        the pre-existing directory itself intact."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowRegistry

        monkeypatch.chdir(project_dir)
        runner = CliRunner()
        src = self._write_workflow_dir(project_dir)
        dest_dir = project_dir / ".specify" / "workflows" / "align-wf"
        dest_dir.mkdir(parents=True)  # pre-existing, but empty: no workflow.yml

        def boom(self, *args, **kwargs):
            raise OSError("disk full")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(WorkflowRegistry, "add", boom)
            result = runner.invoke(app, ["workflow", "add", str(src), "--dev"])

        assert result.exit_code != 0
        assert result.output.strip() != ""
        assert dest_dir.is_dir()
        assert not (dest_dir / "workflow.yml").exists()

    def test_add_catalog_save_failure_leaves_no_orphan_directory(self, project_dir, monkeypatch):
        """Same guarantee as the local-install paths, but for a fresh catalog
        install: a registry.add() failure must clean up the freshly-downloaded
        directory and fail with a clean escaped message."""
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
        data = self.WORKFLOW_YAML.format(version="1.0.0").encode()

        def boom(self):
            raise OSError("disk full")

        runner = CliRunner()
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(data, url),
            )
            mp.setattr(WorkflowRegistry, "save", boom)
            result = runner.invoke(app, ["workflow", "add", "align-wf"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert result.output.strip() != ""
        dest_dir = project_dir / ".specify" / "workflows" / "align-wf"
        assert not dest_dir.exists()
        assert not WorkflowRegistry(project_dir).is_installed("align-wf")

    def test_add_catalog_fresh_install_mkstemp_failure_leaves_no_orphan_directory(
        self, project_dir, monkeypatch
    ):
        """Same guarantee as the local-install fresh-install case, but for a
        fresh catalog install: if _stage_workflow_file's mkdir succeeds but
        its mkstemp then fails, the freshly-created empty directory must not
        be left orphaned."""
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
        data = self.WORKFLOW_YAML.format(version="1.0.0").encode()

        def boom(*args, **kwargs):
            raise OSError("disk full")

        runner = CliRunner()
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(data, url),
            )
            mp.setattr("tempfile.mkstemp", boom)
            result = runner.invoke(app, ["workflow", "add", "align-wf"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert result.output.strip() != ""
        dest_dir = project_dir / ".specify" / "workflows" / "align-wf"
        assert not dest_dir.exists(), "fresh-install dest_dir left orphaned after mkstemp failure"
        assert not WorkflowRegistry(project_dir).is_installed("align-wf")

    def test_add_catalog_rejects_oversized_content_length(self, project_dir, monkeypatch):
        """Catalog installs must share the same size cap as --from: a
        response that declares an oversized Content-Length is rejected
        before its body is read into memory, and no orphan directory or
        registry mutation is left behind."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands as wf_commands
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(wf_commands, "_MAX_WORKFLOW_YAML_BYTES", 100)
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
        small_body = b"id: align-wf\n"  # actual body is small; header lies
        runner = CliRunner()
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                    small_body, url, headers={"Content-Length": "1000"}
                ),
            )
            result = runner.invoke(app, ["workflow", "add", "align-wf"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "exceedingthe100-byteworkflowsizelimit" in "".join(result.output.split())
        dest_dir = project_dir / ".specify" / "workflows" / "align-wf"
        assert not dest_dir.exists()
        assert not WorkflowRegistry(project_dir).is_installed("align-wf")

    def test_add_catalog_rejects_oversized_streamed_body_without_content_length(
        self, project_dir, monkeypatch
    ):
        """Catalog installs must also cap actual streamed bytes when
        Content-Length is absent or understated, leaving no orphan
        directory or registry mutation behind."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands as wf_commands
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(wf_commands, "_MAX_WORKFLOW_YAML_BYTES", 100)
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
        oversized_body = b"x" * 500  # no Content-Length header at all
        runner = CliRunner()
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                    oversized_body, url
                ),
            )
            result = runner.invoke(app, ["workflow", "add", "align-wf"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "exceedsthe100-byteworkflowsizelimit" in "".join(result.output.split())
        dest_dir = project_dir / ".specify" / "workflows" / "align-wf"
        assert not dest_dir.exists()
        assert not WorkflowRegistry(project_dir).is_installed("align-wf")

    def test_add_catalog_reinstall_save_failure_restores_prior_file(self, project_dir, monkeypatch):
        """Re-adding an already-installed catalog workflow downloads the new
        version over the existing install directory. If registry.add() then
        fails to save, the prior working workflow.yml must be restored
        byte-for-byte (not left overwritten with the new download, and not
        deleted like a fresh install) and the registry must remain valid and
        still point at the original version -- the update path's caller has
        an outer backup/restore for this, but plain `workflow add` does not,
        so _install_workflow_from_catalog must handle it itself."""
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

        def boom(self):
            raise OSError("disk full")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                    new_data, url
                ),
            )
            mp.setattr(WorkflowRegistry, "save", boom)
            result = runner.invoke(app, ["workflow", "add", "align-wf"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert result.output.strip() != ""
        # The prior working install must survive untouched, byte-for-byte.
        assert dest_file.read_bytes() == original_data
        registry = WorkflowRegistry(project_dir)
        assert registry.is_installed("align-wf")
        assert registry.get("align-wf")["version"] == "1.0.0"

    def test_add_catalog_successful_reinstall_leaves_no_backup_file(
        self, project_dir, monkeypatch
    ):
        """Same orphan-backup gap as the local-install path: a successful
        catalog reinstall must not leave its unique backup behind once
        registry.add() durably succeeds."""
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
        original_data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
        runner = CliRunner()
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                    original_data, url
                ),
            )
            result = runner.invoke(app, ["workflow", "add", "align-wf"])
        assert result.exit_code == 0, result.output

        new_data = self.WORKFLOW_YAML.format(version="2.0.0").encode()
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                    new_data, url
                ),
            )
            result = runner.invoke(app, ["workflow", "add", "align-wf"])

        assert result.exit_code == 0, result.output
        workflow_dir = project_dir / ".specify" / "workflows" / "align-wf"
        registry = WorkflowRegistry(project_dir)
        assert registry.is_installed("align-wf")
        assert registry.get("align-wf")["version"] == "2.0.0"
        assert (workflow_dir / "workflow.yml").read_bytes() == new_data
        leftovers = [p.name for p in workflow_dir.iterdir() if p.name != "workflow.yml"]
        assert leftovers == [], f"orphan sibling(s) left behind: {leftovers}"

    @pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
    def test_add_catalog_fresh_install_uses_project_file_mode(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog

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
        data = self.WORKFLOW_YAML.format(version="1.0.0").encode()

        previous_umask = os.umask(0o022)
        try:
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(
                    "specify_cli.authentication.http.open_url",
                    lambda url, timeout=None, extra_headers=None,
                    redirect_validator=None: self._FakeResponse(data, url),
                )
                result = CliRunner().invoke(
                    app, ["workflow", "add", "align-wf"]
                )
        finally:
            os.umask(previous_umask)

        assert result.exit_code == 0, result.output
        workflow_file = (
            project_dir
            / ".specify"
            / "workflows"
            / "align-wf"
            / "workflow.yml"
        )
        assert stat.S_IMODE(workflow_file.stat().st_mode) == 0o644

    def test_concurrent_catalog_reinstalls_keep_file_and_registry_aligned(
        self, project_dir, monkeypatch
    ):
        import threading
        from specify_cli.workflows import _commands
        from specify_cli.workflows.catalog import WorkflowCatalog, WorkflowRegistry
        from specify_cli.workflows.engine import WorkflowDefinition

        workflows_dir = project_dir / ".specify" / "workflows"
        workflow_file = workflows_dir / "align-wf" / "workflow.yml"
        workflow_file.parent.mkdir(parents=True)
        workflow_file.write_text(
            self.WORKFLOW_YAML.format(version="1.0.0"), encoding="utf-8"
        )
        WorkflowRegistry(project_dir).add(
            "align-wf",
            {
                "name": "Align Workflow",
                "version": "1.0.0",
                "source": "catalog",
            },
        )

        versions = {"install-a": "2.0.0", "install-b": "3.0.0"}
        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "name": "Align Workflow",
                "version": versions[threading.current_thread().name],
                "url": (
                    "https://example.com/"
                    f"{versions[threading.current_thread().name]}.yml"
                ),
                "_install_allowed": True,
                "_catalog_name": "test-catalog",
            },
        )
        monkeypatch.setattr(
            "specify_cli.authentication.http.open_url",
            lambda url, timeout=None, extra_headers=None,
            redirect_validator=None: self._FakeResponse(
                self.WORKFLOW_YAML.format(
                    version=url.rsplit("/", 1)[-1].removesuffix(".yml")
                ).encode(),
                url,
            ),
        )

        a_committed = threading.Event()
        b_committed = threading.Event()
        a_saving = threading.Event()
        b_saved = threading.Event()
        real_commit = _commands._commit_workflow_file
        real_save = WorkflowRegistry.save

        def coordinated_commit(*args, **kwargs):
            backup = real_commit(*args, **kwargs)
            if threading.current_thread().name == "install-a":
                a_committed.set()
                b_committed.wait(0.5)
            else:
                b_committed.set()
            return backup

        def coordinated_save(registry):
            if threading.current_thread().name == "install-a":
                a_saving.set()
                b_saved.wait(0.5)
                return real_save(registry)
            assert a_saving.wait(2)
            real_save(registry)
            b_saved.set()

        monkeypatch.setattr(
            _commands, "_commit_workflow_file", coordinated_commit
        )
        monkeypatch.setattr(WorkflowRegistry, "save", coordinated_save)

        errors = []

        def install():
            try:
                _commands._install_workflow_from_catalog(
                    project_dir,
                    workflows_dir,
                    "align-wf",
                )
            except BaseException as exc:
                errors.append(exc)

        first = threading.Thread(target=install, name="install-a")
        second = threading.Thread(target=install, name="install-b")
        first.start()
        assert a_committed.wait(2)
        second.start()
        first.join(5)
        second.join(5)

        assert not first.is_alive()
        assert not second.is_alive()
        assert errors == []
        file_version = WorkflowDefinition.from_yaml(workflow_file).version
        registry_version = WorkflowRegistry(project_dir).get("align-wf")[
            "version"
        ]
        assert file_version == registry_version

    def test_precommit_discard_preserves_concurrent_install(self, project_dir):
        from specify_cli.workflows import _commands

        workflow_dir = (
            project_dir / ".specify" / "workflows" / "concurrent-wf"
        )
        workflow_dir.mkdir(parents=True)
        staged_file = workflow_dir / ".workflow.yml.staged.tmp"
        staged_file.write_text("staged", encoding="utf-8")
        committed_file = workflow_dir / "workflow.yml"
        committed_file.write_text("committed", encoding="utf-8")

        _commands._discard_staged_workflow_file(
            staged_file, workflow_dir, existed_before=False
        )

        assert committed_file.read_text(encoding="utf-8") == "committed"
        assert not staged_file.exists()

    def test_fresh_install_rollback_preserves_concurrent_staged_file(
        self, project_dir
    ):
        """A second installer stages before taking the transaction lock, so
        the first installer's rollback must not recursively remove siblings."""
        from specify_cli.workflows import _commands

        workflow_dir = (
            project_dir / ".specify" / "workflows" / "concurrent-wf"
        )
        workflow_dir.mkdir(parents=True)
        committed_file = workflow_dir / "workflow.yml"
        committed_file.write_text("failed install", encoding="utf-8")
        concurrent_stage = workflow_dir / ".workflow.yml.concurrent.tmp"
        concurrent_stage.write_text("next install", encoding="utf-8")

        _commands._rollback_committed_workflow_file(
            committed_file,
            workflow_dir,
            existed_before=False,
            backup_file=None,
        )

        assert not committed_file.exists()
        assert concurrent_stage.read_text(encoding="utf-8") == "next install"

    def test_add_dev_registry_reopen_exit_discards_staged_file(
        self, project_dir, monkeypatch
    ):
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows import _commands

        monkeypatch.chdir(project_dir)
        source_dir = self._write_workflow_dir(project_dir)
        real_open_registry = _commands._open_workflow_registry
        calls = 0

        def fail_transaction_reopen(root):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise typer.Exit(1)
            return real_open_registry(root)

        monkeypatch.setattr(
            _commands, "_open_workflow_registry", fail_transaction_reopen
        )
        result = CliRunner().invoke(
            app, ["workflow", "add", str(source_dir), "--dev"]
        )

        assert result.exit_code != 0
        assert not (
            project_dir / ".specify" / "workflows" / "align-wf"
        ).exists()

    def test_add_catalog_registry_reopen_exit_discards_staged_file(
        self, project_dir, monkeypatch
    ):
        from specify_cli.workflows import _commands
        from specify_cli.workflows.catalog import WorkflowCatalog

        workflows_dir = project_dir / ".specify" / "workflows"
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
        data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
        monkeypatch.setattr(
            "specify_cli.authentication.http.open_url",
            lambda url, timeout=None, extra_headers=None,
            redirect_validator=None: self._FakeResponse(data, url),
        )
        monkeypatch.setattr(
            _commands,
            "_open_workflow_registry",
            lambda _root: (_ for _ in ()).throw(typer.Exit(1)),
        )

        with pytest.raises(typer.Exit):
            _commands._install_workflow_from_catalog(
                project_dir,
                workflows_dir,
                "align-wf",
            )

        assert not (workflows_dir / "align-wf").exists()

    def test_add_catalog_reinstall_restore_failure_reports_warning_and_original_error(
        self, project_dir, monkeypatch
    ):
        """Same restore-rename boundary as the local-install path: the
        prior file is restored via an atomic rename (not a content rewrite)
        when registry.add() fails on a reinstall. If that restore rename
        itself also fails, it must report a clear warning in addition to
        the original clean registry error, never crash or silently claim
        success."""
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
        original_data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
        runner = CliRunner()
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                    original_data, url
                ),
            )
            result = runner.invoke(app, ["workflow", "add", "align-wf"])
        assert result.exit_code == 0, result.output

        new_data = self.WORKFLOW_YAML.format(version="2.0.0").encode()

        def save_boom(self):
            raise OSError("disk full")

        real_replace = os.replace
        calls = {"n": 0}

        def replace_boom(src_path, dst_path):
            # The commit swap for a reinstall makes exactly two os.replace
            # calls (backup-aside, then staged-into-dest); let both succeed
            # and only fail the third call -- the post-registry-failure
            # restore-back rename.
            calls["n"] += 1
            if calls["n"] <= 2:
                return real_replace(src_path, dst_path)
            raise OSError("permission denied")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(
                    new_data, url
                ),
            )
            mp.setattr(WorkflowRegistry, "save", save_boom)
            mp.setattr(os, "replace", replace_boom)
            result = runner.invoke(app, ["workflow", "add", "align-wf"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        output_compact = "".join(result.output.split())
        assert "Warning" in result.output
        assert "diskfull" in output_compact
        assert "permissiondenied" in output_compact

    def test_add_catalog_fresh_install_into_preexisting_empty_dir_cleans_new_file(
        self, project_dir, monkeypatch
    ):
        """Same rollback orphan gap as the local-install path, but for a
        fresh catalog install: a pre-existing empty destination directory
        (no workflow.yml) sets existed_before=True with no backup bytes, so
        the rollback previously did nothing on a later failure -- leaving
        the freshly downloaded workflow.yml behind. It must be removed,
        leaving the pre-existing directory itself intact."""
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
        dest_dir = project_dir / ".specify" / "workflows" / "align-wf"
        dest_dir.mkdir(parents=True)  # pre-existing, but empty: no workflow.yml
        data = self.WORKFLOW_YAML.format(version="1.0.0").encode()

        def boom(self):
            raise OSError("disk full")

        runner = CliRunner()
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "specify_cli.authentication.http.open_url",
                lambda url, timeout=None, extra_headers=None, redirect_validator=None: self._FakeResponse(data, url),
            )
            mp.setattr(WorkflowRegistry, "save", boom)
            result = runner.invoke(app, ["workflow", "add", "align-wf"])

        assert result.exit_code != 0
        assert result.output.strip() != ""
        assert dest_dir.is_dir()
        assert not (dest_dir / "workflow.yml").exists()

    @pytest.mark.parametrize(
        "mode", ["redirect_rejected", "download_exception", "invalid_yaml", "id_mismatch"]
    )
    def test_add_catalog_reinstall_early_failure_restores_prior_file(
        self, project_dir, monkeypatch, mode
    ):
        """Every _install_workflow_from_catalog failure branch that runs after
        the mkdir/download step -- not just the registry.add() OSError case
        -- must route through the same existed-before/backup-aware cleanup:
        on a reinstall, a redirect rejection, a download exception, invalid
        YAML, or a workflow-id mismatch must restore the prior working
        workflow.yml rather than deleting the whole directory. One shared
        root cause (the cleanup helper), so parametrized over trigger point."""
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

        if mode == "redirect_rejected":
            def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
                return self._FakeResponse(b"irrelevant", "http://evil.example.com/workflow.yml")
        elif mode == "download_exception":
            def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
                raise OSError("network down")
        elif mode == "invalid_yaml":
            def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
                return self._FakeResponse(b": : not valid yaml: [", url)
        else:  # id_mismatch
            mismatched_yaml = self.WORKFLOW_YAML.format(version="2.0.0").replace(
                'id: "align-wf"', 'id: "different-workflow"'
            )

            def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
                return self._FakeResponse(mismatched_yaml.encode(), url)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("specify_cli.authentication.http.open_url", fake_open_url)
            result = runner.invoke(app, ["workflow", "add", "align-wf"])

        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert result.output.strip() != ""
        assert dest_file.read_bytes() == original_data
        registry = WorkflowRegistry(project_dir)
        assert registry.is_installed("align-wf")
        assert registry.get("align-wf")["version"] == "1.0.0"

    def test_download_redirect_validator_rejects_http_before_follow(self):
        import urllib.error

        from specify_cli.workflows._commands import _reject_insecure_download_redirect

        with pytest.raises(urllib.error.URLError):
            _reject_insecure_download_redirect(
                "https://example.com/wf.yml", "http://evil.example.com/wf.yml"
            )
        with pytest.raises(urllib.error.URLError):
            _reject_insecure_download_redirect(
                "https://example.com/wf.yml", "http://localhost:8000/wf.yml"
            )
        with pytest.raises(urllib.error.URLError):
            _reject_insecure_download_redirect(
                "https://example.com/wf.yml", "https://127.0.0.2/wf.yml"
            )
        # Allowed: HTTPS anywhere, or loopback HTTP that stays on loopback HTTP.
        _reject_insecure_download_redirect(
            "https://example.com/wf.yml", "https://cdn.example.com/wf.yml"
        )
        _reject_insecure_download_redirect(
            "http://localhost:7000/wf.yml", "http://localhost:8000/wf.yml"
        )
        _reject_insecure_download_redirect(
            "http://127.0.0.1/source.yml", "http://127.0.0.1/wf.yml"
        )
        _reject_insecure_download_redirect(
            "http://127.0.0.2/source.yml", "http://127.255.255.254/wf.yml"
        )

    def test_add_from_url_passes_redirect_validator(self, project_dir, monkeypatch):
        from unittest.mock import patch

        from typer.testing import CliRunner
        from specify_cli import app

        monkeypatch.chdir(project_dir)
        data = self.WORKFLOW_YAML.format(version="1.0.0").encode()
        seen: dict[str, object] = {}

        def fake_open(url, timeout=None, extra_headers=None, redirect_validator=None):
            seen["validator"] = redirect_validator
            return self._FakeResponse(data, url)

        runner = CliRunner()
        with patch("specify_cli.authentication.http.open_url", side_effect=fake_open):
            result = runner.invoke(
                app,
                ["workflow", "add", "align-wf", "--from", "https://example.com/workflow.yml"],
                input="y\n",
            )
        assert result.exit_code == 0, result.output
        from specify_cli.workflows._commands import _reject_insecure_download_redirect

        assert seen["validator"] is _reject_insecure_download_redirect

    def test_add_non_string_catalog_url_fails_cleanly(self, project_dir, monkeypatch):
        """A truthy non-string catalog URL must hit the clean error path, not AttributeError."""
        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.workflows.catalog import WorkflowCatalog

        monkeypatch.chdir(project_dir)
        monkeypatch.setattr(
            WorkflowCatalog,
            "get_workflow_info",
            lambda self, wid: {
                "id": wid,
                "name": "Align Workflow",
                "version": "1.0.0",
                "url": 123,
                "_install_allowed": True,
                "_catalog_name": "test-catalog",
            },
        )
        runner = CliRunner()
        result = runner.invoke(app, ["workflow", "add", "align-wf"])
        assert result.exit_code != 0
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "malformed install URL" in result.output

    def test_commit_failure_reports_unrestored_backup_location(
        self, tmp_path, monkeypatch
    ):
        from specify_cli.workflows import _commands

        dest_dir = tmp_path / "align-wf"
        dest_dir.mkdir()
        dest_file = dest_dir / "workflow.yml"
        staged_file = dest_dir / ".workflow.yml.staged"
        dest_file.write_text("original", encoding="utf-8")
        staged_file.write_text("replacement", encoding="utf-8")

        real_replace = os.replace
        calls = 0
        backup_file = None

        def fail_commit_and_restore(src, dst):
            nonlocal backup_file, calls
            calls += 1
            if calls == 1:
                backup_file = Path(dst)
                return real_replace(src, dst)
            if calls == 2:
                raise OSError("commit denied")
            raise OSError("restore denied")

        monkeypatch.setattr(os, "replace", fail_commit_and_restore)
        with pytest.raises(OSError) as exc_info:
            _commands._commit_workflow_file(
                staged_file, dest_file, existed_before=True
            )

        message = str(exc_info.value)
        assert "commit denied" in message
        assert "restore denied" in message
        assert backup_file is not None
        assert str(backup_file) in message
        assert not dest_file.exists()
        assert backup_file.read_text(encoding="utf-8") == "original"

    def test_commit_keyboard_interrupt_restores_prior_file(
        self, tmp_path, monkeypatch
    ):
        from specify_cli.workflows import _commands

        dest_dir = tmp_path / "align-wf"
        dest_dir.mkdir()
        dest_file = dest_dir / "workflow.yml"
        staged_file = dest_dir / ".workflow.yml.staged"
        dest_file.write_text("original", encoding="utf-8")
        staged_file.write_text("replacement", encoding="utf-8")

        real_replace = os.replace
        calls = 0

        def interrupt_commit(src, dst):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt
            return real_replace(src, dst)

        monkeypatch.setattr(os, "replace", interrupt_commit)
        with pytest.raises(KeyboardInterrupt):
            _commands._commit_workflow_file(
                staged_file, dest_file, existed_before=True
            )

        assert dest_file.read_text(encoding="utf-8") == "original"
        assert staged_file.read_text(encoding="utf-8") == "replacement"
        assert list(dest_dir.glob("*.bak")) == []

    def test_commit_interrupt_after_first_rename_restores_prior_file(
        self, tmp_path, monkeypatch
    ):
        from specify_cli.workflows import _commands

        dest_dir = tmp_path / "align-wf"
        dest_dir.mkdir()
        dest_file = dest_dir / "workflow.yml"
        staged_file = dest_dir / ".workflow.yml.staged"
        dest_file.write_text("original", encoding="utf-8")
        staged_file.write_text("replacement", encoding="utf-8")

        real_replace = os.replace
        calls = 0

        def interrupt_after_replace(src, dst):
            nonlocal calls
            calls += 1
            result = real_replace(src, dst)
            if calls == 1:
                raise KeyboardInterrupt
            return result

        monkeypatch.setattr(os, "replace", interrupt_after_replace)
        with pytest.raises(KeyboardInterrupt):
            _commands._commit_workflow_file(
                staged_file, dest_file, existed_before=True
            )

        assert dest_file.read_text(encoding="utf-8") == "original"
        assert staged_file.read_text(encoding="utf-8") == "replacement"
        assert list(dest_dir.glob("*.bak")) == []

    def test_commit_uses_unique_backup_without_overwriting_existing_sibling(
        self, tmp_path
    ):
        from specify_cli.workflows import _commands

        dest_dir = tmp_path / "align-wf"
        dest_dir.mkdir()
        dest_file = dest_dir / "workflow.yml"
        staged_file = dest_dir / ".workflow.yml.staged"
        fixed_backup = dest_dir / "workflow.yml.bak"
        dest_file.write_text("original", encoding="utf-8")
        staged_file.write_text("replacement", encoding="utf-8")
        fixed_backup.write_text("diagnostic copy", encoding="utf-8")

        backup_file = _commands._commit_workflow_file(
            staged_file, dest_file, existed_before=True
        )

        assert backup_file is not None
        assert backup_file != fixed_backup
        assert backup_file.read_text(encoding="utf-8") == "original"
        assert fixed_backup.read_text(encoding="utf-8") == "diagnostic copy"
        assert dest_file.read_text(encoding="utf-8") == "replacement"


class TestOverlayCli:
    """CLI-level tests for ``specify workflow overlay *``."""

    def test_workflow_add_does_not_copy_overlays(self, project_dir, monkeypatch, tmp_path):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        source_dir = tmp_path / "source-wf"
        source_dir.mkdir()
        (source_dir / "workflow.yml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
                    "steps": [{"id": "a", "type": "command", "command": "echo"}],
                }
            ),
            encoding="utf-8",
        )
        overlays_dir = source_dir / "overlays"
        overlays_dir.mkdir()
        (overlays_dir / "ov1.yml").write_text(
            yaml.safe_dump(
                {
                    "id": "ov1",
                    "extends": "wf",
                    "priority": 10,
                    "edits": [
                        {
                            "operation": "insert_after",
                            "anchor": "a",
                            "step": {"id": "new", "type": "command", "command": "echo"},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(app, ["workflow", "add", str(source_dir)])
        assert result.exit_code == 0, result.output
        # Overlays in the source directory should NOT be copied — workflow add
        # only installs the workflow.yml, not sibling overlays.
        installed_overlay = (
            project_dir / ".specify" / "workflows" / "wf" / "overlays" / "ov1.yml"
        )
        assert not installed_overlay.exists()
