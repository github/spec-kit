"""Tests for ``specify integration`` subcommand (list, install, uninstall, switch)."""

import json
import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from tests.conftest import strip_ansi


runner = CliRunner()


def _init_project(tmp_path, integration="copilot"):
    """Helper: init a spec-kit project with the given integration."""
    project = tmp_path / "proj"
    project.mkdir()
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        result = runner.invoke(app, [
            "init", "--here",
            "--integration", integration,
            "--script", "sh",
            "--ignore-agent-tools",
        ], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)
    assert result.exit_code == 0, f"init failed: {result.output}"
    return project


def _run_in_project(project, args):
    """Run a CLI command from inside a generated project."""
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        return runner.invoke(app, args, catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def _write_invalid_manifest(project, key):
    manifest = project / ".specify" / "integrations" / f"{key}.manifest.json"
    manifest.write_bytes(b"\xff\xfe\x00")
    return manifest


def _copy_project_template(tmp_path, template):
    project = tmp_path / "proj"
    shutil.copytree(template, project)
    return project


@pytest.fixture(scope="module")
def status_copilot_template(tmp_path_factory):
    return _init_project(tmp_path_factory.mktemp("status-copilot"), "copilot")


@pytest.fixture(scope="module")
def status_claude_template(tmp_path_factory):
    return _init_project(tmp_path_factory.mktemp("status-claude"), "claude")


@pytest.fixture
def copilot_project(tmp_path, status_copilot_template):
    return _copy_project_template(tmp_path, status_copilot_template)


@pytest.fixture
def claude_project(tmp_path, status_claude_template):
    return _copy_project_template(tmp_path, status_claude_template)


def _integration_list_row_cells(output: str, key: str) -> list[str]:
    plain = strip_ansi(output)
    row = next(line for line in plain.splitlines() if line.startswith(f"│ {key}"))
    return [cell.strip() for cell in row.split("│")[1:-1]]


# ── list ─────────────────────────────────────────────────────────────


class TestIntegrationList:
    def test_list_requires_speckit_project(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a spec-kit project" in result.output

    def test_list_shows_installed(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "copilot" in result.output
        assert "installed" in result.output

    def test_list_shows_available_integrations(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        # Should show multiple integrations
        assert "claude" in result.output
        assert "gemini" in result.output
        assert "zed" in result.output

    def test_list_shows_multi_install_safe_status(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "Multi-install" in result.output
        assert "Safe" in result.output
        assert _integration_list_row_cells(result.output, "claude")[-1] == "yes"
        assert _integration_list_row_cells(result.output, "copilot")[-1] == "no"

    def test_list_rejects_newer_integration_state_schema(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        int_json = project / ".specify" / "integration.json"
        data = json.loads(int_json.read_text(encoding="utf-8"))
        data["integration_state_schema"] = 99
        int_json.write_text(json.dumps(data), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        normalized = " ".join(result.output.split())
        assert "schema 99" in normalized
        assert "only supports schema 1" in normalized


# ── status ───────────────────────────────────────────────────────────


class TestIntegrationStatus:
    def test_status_requires_speckit_project(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["integration", "status"])
        assert result.exit_code != 0
        assert "Not a spec-kit project" in result.output

    def test_status_reports_healthy_project(self, copilot_project):
        result = _run_in_project(copilot_project, ["integration", "status"])

        assert result.exit_code == 0
        assert "Integration status: OK" in result.output
        assert "Default integration: copilot" in result.output
        assert "Installed integrations: copilot" in result.output
        assert "Shared templates target alignment: copilot" in result.output
        assert "Modified managed files: 0" in result.output
        assert "Missing managed files: 0" in result.output

    def test_status_json_reports_healthy_project(self, copilot_project):
        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["status"] == "ok"
        assert payload["default_integration"] == "copilot"
        assert payload["installed_integrations"] == ["copilot"]
        assert payload["recorded_installed_integrations"] == ["copilot"]
        assert payload["manifest_checked_integrations"] == ["copilot", "speckit"]
        assert payload["multi_install_safe"] is True
        assert payload["shared_templates_target_alignment"] == "copilot"
        assert "shared_templates_aligned_to" not in payload
        assert payload["findings"] == []

    def test_status_reports_invalid_integration_json(self, copilot_project):
        (copilot_project / ".specify" / "integration.json").write_text("{", encoding="utf-8")

        result = _run_in_project(copilot_project, ["integration", "status"])

        assert result.exit_code != 0
        assert "integration-state-unreadable" in result.output
        assert "invalid JSON" in result.output
        assert "Detail:" in result.output
        assert "Multi-install safe: unknown" in result.output
        assert "Traceback" not in result.output

    def test_status_json_reports_unknown_multi_install_safety_when_state_unreadable(
        self,
        copilot_project,
    ):
        (copilot_project / ".specify" / "integration.json").write_text("{", encoding="utf-8")

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["status"] == "error"
        assert payload["multi_install_safe"] is None
        assert payload["manifest_checked_integrations"] == []
        assert payload["findings"][0]["code"] == "integration-state-unreadable"
        assert "Detail:" in payload["findings"][0]["message"]

    def test_status_reports_supported_schema_for_newer_integration_state(self, copilot_project):
        state_path = copilot_project / ".specify" / "integration.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["integration_state_schema"] = 99
        state_path.write_text(json.dumps(state), encoding="utf-8")

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["findings"][0]["code"] == "integration-state-unreadable"
        assert "schema 99" in payload["findings"][0]["message"]
        assert "supported schema: 1" in payload["findings"][0]["message"]

    def test_status_reports_missing_integration_json(self, copilot_project):
        (copilot_project / ".specify" / "integration.json").unlink()

        result = _run_in_project(copilot_project, ["integration", "status"])

        assert result.exit_code != 0
        assert "integration-state-missing" in result.output
        assert ".specify/integration.json is missing" in result.output
        assert "Multi-install safe: unknown" in result.output

    def test_status_json_reports_unknown_multi_install_safety_when_state_missing(
        self,
        copilot_project,
    ):
        (copilot_project / ".specify" / "integration.json").unlink()

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["status"] == "error"
        assert payload["multi_install_safe"] is None
        assert payload["manifest_checked_integrations"] == []
        assert payload["findings"][0]["code"] == "integration-state-missing"

    def test_status_json_reports_no_installed_integrations_as_warning(self, copilot_project):
        state_path = copilot_project / ".specify" / "integration.json"
        state_path.write_text(
            json.dumps({
                "version": "test",
                "integration_state_schema": 1,
                "installed_integrations": [],
            }),
            encoding="utf-8",
        )

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["status"] == "warning"
        assert payload["installed_integrations"] == []
        assert payload["multi_install_safe"] is None
        assert payload["manifest_checked_integrations"] == ["speckit"]
        assert payload["findings"][0]["code"] == "no-installed-integrations"
        assert "speckit" in payload["manifests"]
        assert payload["manifests"]["speckit"]["readable"] is True

    def test_status_checks_shared_manifest_when_no_integrations_installed(self, copilot_project):
        state_path = copilot_project / ".specify" / "integration.json"
        state_path.write_text(
            json.dumps({
                "version": "test",
                "integration_state_schema": 1,
                "installed_integrations": [],
            }),
            encoding="utf-8",
        )
        (copilot_project / ".specify" / "integrations" / "speckit.manifest.json").unlink()

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["status"] == "error"
        assert payload["installed_integrations"] == []
        assert payload["manifest_checked_integrations"] == ["speckit"]
        assert payload["unchecked_manifests"] == 1
        assert any(
            item["code"] == "no-installed-integrations"
            for item in payload["findings"]
        )
        assert any(
            item["code"] == "manifest-missing"
            and item["integration"] == "speckit"
            for item in payload["findings"]
        )

    def test_status_json_reports_missing_default_integration_as_error(self, claude_project):
        state_path = claude_project / ".specify" / "integration.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.pop("default_integration", None)
        state.pop("integration", None)
        state["installed_integrations"] = ["claude"]
        state_path.write_text(json.dumps(state), encoding="utf-8")

        result = _run_in_project(claude_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["status"] == "error"
        assert payload["default_integration"] is None
        assert any(
            item["code"] == "default-integration-missing"
            for item in payload["findings"]
        )

    def test_status_ignores_non_list_raw_installed_integrations(self, copilot_project):
        state_path = copilot_project / ".specify" / "integration.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.pop("default_integration", None)
        state.pop("integration", None)
        state["installed_integrations"] = "copilot"
        state_path.write_text(json.dumps(state), encoding="utf-8")

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["status"] == "warning"
        assert payload["installed_integrations"] == []
        assert payload["recorded_installed_integrations"] == []
        assert payload["manifest_checked_integrations"] == ["speckit"]
        assert payload["multi_install_safe"] is None
        assert [item["code"] for item in payload["findings"]] == [
            "installed-integrations-invalid",
            "no-installed-integrations",
        ]

    def test_status_reports_non_list_raw_installed_integrations_with_default(self, copilot_project):
        state_path = copilot_project / ".specify" / "integration.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["default_integration"] = "copilot"
        state["integration"] = "copilot"
        state["installed_integrations"] = "copilot"
        state_path.write_text(json.dumps(state), encoding="utf-8")

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["status"] == "warning"
        assert payload["installed_integrations"] == ["copilot"]
        assert payload["recorded_installed_integrations"] == []
        assert payload["manifest_checked_integrations"] == ["copilot", "speckit"]
        assert payload["multi_install_safe"] is None
        assert [item["code"] for item in payload["findings"]] == [
            "installed-integrations-invalid",
        ]

    def test_status_reports_default_integration_not_installed(self, claude_project):
        state_path = claude_project / ".specify" / "integration.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["default_integration"] = "codex"
        state["integration"] = "codex"
        state["installed_integrations"] = ["claude"]
        state_path.write_text(json.dumps(state), encoding="utf-8")

        result = _run_in_project(claude_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["default_integration"] == "codex"
        assert payload["installed_integrations"] == ["codex", "claude"]
        assert payload["recorded_installed_integrations"] == ["claude"]
        assert payload["manifest_checked_integrations"] == ["claude", "speckit"]
        assert any(
            item["code"] == "default-integration-not-installed"
            and "Default integration 'codex' is not listed" in item["message"]
            for item in payload["findings"]
        )
        assert "codex" not in payload["manifests"]
        assert not any(
            item["code"] == "manifest-missing" and item.get("integration") == "codex"
            for item in payload["findings"]
        )

    def test_status_checks_effective_default_manifest_when_raw_installed_is_empty(self, claude_project):
        state_path = claude_project / ".specify" / "integration.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["installed_integrations"] = []
        state_path.write_text(json.dumps(state), encoding="utf-8")

        result = _run_in_project(claude_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["installed_integrations"] == ["claude"]
        assert payload["recorded_installed_integrations"] == []
        assert payload["manifest_checked_integrations"] == ["claude", "speckit"]
        assert payload["multi_install_safe"] is None
        assert payload["manifests"]["claude"]["readable"] is True
        assert any(
            item["code"] == "default-integration-not-installed"
            for item in payload["findings"]
        )

    def test_status_reports_missing_manifest(self, copilot_project):
        (copilot_project / ".specify" / "integrations" / "copilot.manifest.json").unlink()

        result = _run_in_project(copilot_project, ["integration", "status"])

        assert result.exit_code != 0
        assert "manifest-missing" in result.output
        assert "Manifest for integration 'copilot' is missing" in result.output

    def test_status_reports_unreadable_manifest_in_json_summary(self, copilot_project):
        _write_invalid_manifest(copilot_project, "copilot")

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["unchecked_manifests"] == 1
        assert payload["manifests"]["copilot"]["readable"] is False
        assert payload["manifests"]["copilot"]["missing_files"] == []
        assert payload["manifests"]["copilot"]["modified_files"] == []

    def test_status_reports_modified_managed_files_without_failing(self, copilot_project):
        manifest_path = copilot_project / ".specify" / "integrations" / "copilot.manifest.json"
        tracked_files = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
        first_rel = next(iter(tracked_files))
        (copilot_project / first_rel).write_text("MODIFIED CONTENT\n", encoding="utf-8")

        result = _run_in_project(copilot_project, ["integration", "status"])

        assert result.exit_code == 0
        assert "Integration status: WARNING" in result.output
        assert "managed-files-modified" in result.output
        assert "Modified managed files: 1" in result.output

    def test_status_reports_missing_managed_files(self, copilot_project):
        manifest_path = copilot_project / ".specify" / "integrations" / "copilot.manifest.json"
        tracked_files = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
        first_rel = next(iter(tracked_files))
        (copilot_project / first_rel).unlink()

        result = _run_in_project(copilot_project, ["integration", "status"])

        assert result.exit_code != 0
        assert "managed-files-missing" in result.output
        assert "Missing managed files: 1" in result.output

    def test_status_reports_missing_shared_managed_files(self, copilot_project):
        shared_file = copilot_project / ".specify" / "scripts" / "bash" / "common.sh"
        assert shared_file.exists()
        shared_file.unlink()

        result = _run_in_project(copilot_project, ["integration", "status"])

        assert result.exit_code != 0
        assert "managed-files-missing" in result.output
        assert "shared Spec Kit infrastructure" in result.output
        assert "Missing managed files: 1" in result.output

    def test_status_does_not_use_exists_precheck_for_managed_files(self, tmp_path, monkeypatch):
        from specify_cli.integration_status import _manifest_file_status
        from specify_cli.integrations.manifest import IntegrationManifest

        project = tmp_path / "proj"
        project.mkdir()
        tracked = project / "tracked.md"
        tracked.write_text("content\n", encoding="utf-8")
        manifest = IntegrationManifest("test", project, version="test")
        manifest.record_existing("tracked.md")

        def fail_exists(self):
            raise AssertionError(f"Path.exists() should not be used for {self}")

        monkeypatch.setattr(Path, "exists", fail_exists)

        missing, modified, invalid, valid = _manifest_file_status(
            manifest,
            project.resolve(),
        )

        assert missing == []
        assert modified == []
        assert invalid == []
        assert valid == ["tracked.md"]

    def test_status_does_not_use_exists_precheck_for_manifest_load(self, copilot_project, monkeypatch):
        def fail_exists(self):
            raise AssertionError(f"Path.exists() should not be used for {self}")

        monkeypatch.setattr(Path, "exists", fail_exists)

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["status"] == "ok"
        assert payload["manifests"]["copilot"]["readable"] is True

    def test_status_reports_unresolved_project_root_without_crashing(self, copilot_project, monkeypatch):
        original_resolve = Path.resolve
        failed = {"done": False}

        def fail_first_project_root_resolve(self, *args, **kwargs):
            if self == copilot_project and not failed["done"]:
                failed["done"] = True
                raise RuntimeError("symlink loop")
            return original_resolve(self, *args, **kwargs)

        monkeypatch.setattr(Path, "resolve", fail_first_project_root_resolve)

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["status"] == "warning"
        assert any(item["code"] == "project-root-unresolved" for item in payload["findings"])

    def test_status_loads_manifests_when_project_root_resolution_keeps_failing(
        self,
        copilot_project,
        monkeypatch,
    ):
        original_resolve = Path.resolve

        def fail_project_root_resolve(self, *args, **kwargs):
            if self == copilot_project:
                raise RuntimeError("symlink loop")
            return original_resolve(self, *args, **kwargs)

        monkeypatch.setattr(Path, "resolve", fail_project_root_resolve)

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["status"] == "warning"
        assert payload["manifests"]["copilot"]["readable"] is True
        assert payload["manifests"]["speckit"]["readable"] is True
        assert any(item["code"] == "project-root-unresolved" for item in payload["findings"])

    def test_status_uses_lexical_manifest_paths_when_project_root_resolution_falls_back(self, tmp_path):
        from specify_cli.integration_status import _manifest_file_status
        from specify_cli.integrations.manifest import IntegrationManifest

        real_project = tmp_path / "real-project"
        real_project.mkdir()
        tracked = real_project / "tracked.md"
        tracked.write_text("content\n", encoding="utf-8")
        symlinked_project = tmp_path / "symlinked-project"
        try:
            symlinked_project.symlink_to(real_project, target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"symlinks unavailable: {exc}")

        manifest = IntegrationManifest("test", real_project, version="test")
        manifest.record_existing("tracked.md")
        manifest.project_root = symlinked_project.absolute()

        missing, modified, invalid, valid = _manifest_file_status(
            manifest,
            symlinked_project.absolute(),
            project_root_is_resolved=False,
        )

        assert missing == []
        assert modified == []
        assert invalid == []
        assert valid == ["tracked.md"]

    def test_status_treats_resolve_runtime_error_as_invalid_path(self, tmp_path, monkeypatch):
        from specify_cli.integration_status import _manifest_file_status
        from specify_cli.integrations.manifest import IntegrationManifest

        project = tmp_path / "proj"
        project.mkdir()
        tracked = project / "tracked.md"
        tracked.write_text("content\n", encoding="utf-8")
        manifest = IntegrationManifest("test", project, version="test")
        manifest.record_existing("tracked.md")
        project_root_resolved = project.resolve()
        original_resolve = Path.resolve

        def fail_project_parent_resolve(self, *args, **kwargs):
            if self == project:
                raise RuntimeError("symlink loop")
            return original_resolve(self, *args, **kwargs)

        monkeypatch.setattr(Path, "resolve", fail_project_parent_resolve)

        missing, modified, invalid, valid = _manifest_file_status(
            manifest,
            project_root_resolved,
        )

        assert missing == []
        assert modified == []
        assert invalid == ["tracked.md"]
        assert valid == []

    def test_status_does_not_mask_runtime_errors_from_manifest_load(self, copilot_project, monkeypatch):
        from specify_cli import integration_status as status_module

        def fail_load(key, project_root, **kwargs):
            raise RuntimeError(f"unexpected manifest loader bug for {key}")

        monkeypatch.setattr(status_module.IntegrationManifest, "load", fail_load)

        with pytest.raises(RuntimeError, match="unexpected manifest loader bug"):
            status_module.build_integration_status_report(copilot_project)

    def test_status_treats_dangling_symlink_as_missing(self, copilot_project):
        manifest_path = copilot_project / ".specify" / "integrations" / "copilot.manifest.json"
        tracked_files = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
        first_rel = next(iter(tracked_files))
        target = copilot_project / first_rel
        target.unlink()
        try:
            target.symlink_to(copilot_project / "missing-target")
        except OSError as exc:
            pytest.skip(f"symlinks unavailable: {exc}")

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert first_rel in payload["manifests"]["copilot"]["missing_files"]
        assert first_rel not in payload["manifests"]["copilot"]["modified_files"]

    def test_status_treats_windows_style_dangling_symlink_as_missing(self, tmp_path, monkeypatch):
        from specify_cli.integration_status import _manifest_file_status
        from specify_cli.integrations.manifest import IntegrationManifest

        project = tmp_path / "proj"
        project.mkdir()
        tracked = project / "tracked.md"
        tracked.write_text("content\n", encoding="utf-8")
        regular_stat = tracked.lstat()

        manifest = IntegrationManifest("test", project, version="test")
        manifest.record_existing("tracked.md")

        tracked.unlink()
        try:
            tracked.symlink_to(project / "missing-target")
        except OSError as exc:
            pytest.skip(f"symlinks unavailable: {exc}")

        original_lstat = Path.lstat
        original_is_symlink = Path.is_symlink

        def windows_style_lstat(self):
            if self == tracked:
                return regular_stat
            return original_lstat(self)

        def windows_style_is_symlink(self):
            if self == tracked:
                return True
            return original_is_symlink(self)

        monkeypatch.setattr(Path, "lstat", windows_style_lstat)
        monkeypatch.setattr(Path, "is_symlink", windows_style_is_symlink)

        missing, modified, invalid, valid = _manifest_file_status(
            manifest,
            project.resolve(),
        )

        assert missing == ["tracked.md"]
        assert modified == []
        assert invalid == []
        assert valid == ["tracked.md"]

    def test_strip_extended_length_prefix_normalizes_windows_paths(self):
        from specify_cli.integration_status import _strip_extended_length_prefix

        # Build the prefixed strings explicitly so the test is meaningful on
        # every platform (POSIX won't parse backslash separators, but the
        # helper operates on the string form). Compare Path objects rather than
        # their str() form: on Windows pathlib renders a UNC root with a
        # trailing separator (``\\server\share\``), so an exact string match is
        # brittle, whereas Path equality captures the intended semantics on
        # both POSIX and Windows.
        bs = "\\"
        assert _strip_extended_length_prefix(
            Path(f"{bs}{bs}?{bs}C:{bs}proj")
        ) == Path(f"C:{bs}proj")
        assert _strip_extended_length_prefix(
            Path(f"{bs}{bs}?{bs}UNC{bs}server{bs}share")
        ) == Path(f"{bs}{bs}server{bs}share")
        # Paths without the prefix are returned unchanged.
        assert _strip_extended_length_prefix(Path("relative/path")) == Path("relative/path")

    def test_is_within_project_tolerates_extended_length_prefix(self):
        from specify_cli.integration_status import _is_within_project

        # A readlink result on POSIX never carries the prefix, so an in-project
        # child is contained and an outside path is not. The Windows
        # prefix-stripping branch is exercised by the dangling-symlink tests on
        # Windows CI; here we lock in the cross-platform containment contract.
        root = Path("/tmp/project").resolve()
        assert _is_within_project(root, root / "child")
        assert not _is_within_project(root, Path("/tmp/other").resolve())

    def test_status_reports_unsafe_manifest_paths_without_hashing_them(self, tmp_path, copilot_project):
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("outside project\n", encoding="utf-8")
        link = copilot_project / "outside-link"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"symlinks unavailable: {exc}")

        manifest_path = copilot_project / ".specify" / "integrations" / "copilot.manifest.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_data["files"]["outside-link/secret.txt"] = "wrong"
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["invalid_manifest_paths"] == 1
        assert "outside-link/secret.txt" in payload["manifests"]["copilot"]["invalid_files"]
        assert "outside-link/secret.txt" not in payload["manifests"]["copilot"]["modified_files"]

    def test_status_reports_tracked_symlink_target_escape_as_invalid(self, tmp_path, copilot_project, monkeypatch):
        outside = tmp_path / "outside"
        outside.mkdir()
        outside_file = outside / "secret.txt"
        outside_file.write_text("outside project\n", encoding="utf-8")

        manifest_path = copilot_project / ".specify" / "integrations" / "copilot.manifest.json"
        tracked_files = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
        first_rel = next(iter(tracked_files))
        tracked_path = copilot_project / first_rel
        tracked_path.unlink()
        try:
            tracked_path.symlink_to(outside_file)
        except OSError as exc:
            pytest.skip(f"symlinks unavailable: {exc}")

        original_stat = Path.stat

        def fail_tracked_symlink_stat(self, *args, **kwargs):
            follows_symlinks = kwargs.get("follow_symlinks", True)
            if self == tracked_path and follows_symlinks:
                raise AssertionError("Path.stat() should not follow tracked symlinks")
            return original_stat(self, *args, **kwargs)

        monkeypatch.setattr(Path, "stat", fail_tracked_symlink_stat)

        result = _run_in_project(copilot_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["invalid_manifest_paths"] == 1
        assert first_rel in payload["manifests"]["copilot"]["invalid_files"]
        assert first_rel not in payload["manifests"]["copilot"]["modified_files"]

    def test_status_reports_unsafe_multi_install_combination(self, copilot_project):
        from specify_cli.integrations.manifest import IntegrationManifest

        state_path = copilot_project / ".specify" / "integration.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["installed_integrations"] = ["copilot", "claude"]
        state["default_integration"] = "copilot"
        state["integration"] = "copilot"
        state_path.write_text(json.dumps(state), encoding="utf-8")
        IntegrationManifest("claude", copilot_project, version="test").save()

        result = _run_in_project(copilot_project, ["integration", "status"])

        assert result.exit_code != 0
        assert "unsafe-multi-install" in result.output
        assert "Multi-install safe: no" in result.output
        assert "specify integration switch <key>" in result.output

    def test_status_treats_unknown_multi_install_as_unsafe(self, claude_project):
        from specify_cli.integrations.manifest import IntegrationManifest

        state_path = claude_project / ".specify" / "integration.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["installed_integrations"] = ["claude", "mystery"]
        state["default_integration"] = "claude"
        state["integration"] = "claude"
        state_path.write_text(json.dumps(state), encoding="utf-8")
        IntegrationManifest("mystery", claude_project, version="test").save()

        result = _run_in_project(claude_project, ["integration", "status"])

        assert result.exit_code != 0
        assert "unknown-integration" in result.output
        assert "unsafe-multi-install" in result.output
        assert "remove the stale integration entry" in result.output
        assert "Multi-install safe: no" in result.output

    def test_status_gives_actionable_suggestion_for_unknown_manifest(self, claude_project):
        state_path = claude_project / ".specify" / "integration.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["installed_integrations"] = ["mystery"]
        state["default_integration"] = "mystery"
        state["integration"] = "mystery"
        state_path.write_text(json.dumps(state), encoding="utf-8")

        result = _run_in_project(claude_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        manifest_finding = next(
            item for item in payload["findings"]
            if item["code"] == "manifest-missing" and item["integration"] == "mystery"
        )
        assert "remove the stale integration entry" in manifest_finding["suggestion"]
        assert "integration upgrade mystery" not in manifest_finding["suggestion"]

    def test_status_rejects_unsafe_integration_keys_before_manifest_lookup(self, tmp_path, claude_project):
        state_path = claude_project / ".specify" / "integration.json"
        unsafe_key = "../../../escape"
        state_path.write_text(
            json.dumps({
                "integration": unsafe_key,
                "default_integration": unsafe_key,
                "installed_integrations": [unsafe_key],
            }),
            encoding="utf-8",
        )
        outside_manifest = tmp_path / "escape.manifest.json"
        outside_manifest.write_text(
            json.dumps({"integration": unsafe_key, "files": {}}),
            encoding="utf-8",
        )

        result = _run_in_project(claude_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert unsafe_key not in payload["manifests"]
        assert payload["manifest_checked_integrations"] == ["speckit"]
        assert any(
            item["code"] == "integration-key-invalid"
            and item["integration"] == unsafe_key
            for item in payload["findings"]
        )

    def test_status_rejects_filename_invalid_integration_keys(self, claude_project):
        state_path = claude_project / ".specify" / "integration.json"
        unsafe_key = "bad:key"
        state_path.write_text(
            json.dumps({
                "integration": unsafe_key,
                "default_integration": unsafe_key,
                "installed_integrations": [unsafe_key],
            }),
            encoding="utf-8",
        )

        result = _run_in_project(claude_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert any(
            item["code"] == "integration-key-invalid"
            and item["integration"] == unsafe_key
            for item in payload["findings"]
        )

    def test_status_rejects_windows_reserved_integration_keys(self, claude_project):
        state_path = claude_project / ".specify" / "integration.json"
        unsafe_key = "CON"
        state_path.write_text(
            json.dumps({
                "integration": unsafe_key,
                "default_integration": unsafe_key,
                "installed_integrations": [unsafe_key],
            }),
            encoding="utf-8",
        )

        result = _run_in_project(claude_project, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert any(
            item["code"] == "integration-key-invalid"
            and item["integration"] == unsafe_key
            for item in payload["findings"]
        )

    def test_status_reports_managed_file_collisions(self, claude_project):
        from specify_cli.integrations.manifest import IntegrationManifest

        state_path = claude_project / ".specify" / "integration.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["installed_integrations"] = ["claude", "codex"]
        state["default_integration"] = "claude"
        state["integration"] = "claude"
        state_path.write_text(json.dumps(state), encoding="utf-8")

        claude_manifest = claude_project / ".specify" / "integrations" / "claude.manifest.json"
        tracked_files = json.loads(claude_manifest.read_text(encoding="utf-8"))["files"]
        shared_rel = next(iter(tracked_files))
        codex_manifest = IntegrationManifest("codex", claude_project, version="test")
        codex_manifest.record_existing(shared_rel)
        codex_manifest.save()

        result = _run_in_project(claude_project, ["integration", "status"])

        assert result.exit_code == 0
        assert "managed-file-collision" in result.output
        assert "Integration status: WARNING" in result.output

    def test_status_json_is_not_rich_rendered(self, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        (project / ".specify" / "integration.json").write_text(
            json.dumps({
                "integration": "[red]x[/red]",
                "installed_integrations": ["[red]x[/red]"],
            }),
            encoding="utf-8",
        )
        monkeypatch.chdir(project)

        result = runner.invoke(app, ["integration", "status", "--json"])

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["default_integration"] == "[red]x[/red]"
        assert payload["installed_integrations"] == ["[red]x[/red]"]

    def test_status_text_escapes_rich_markup_from_project_state(self, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        (project / ".specify" / "integration.json").write_text(
            json.dumps({
                "integration": "[red]x[/red]",
                "installed_integrations": ["[red]x[/red]"],
            }),
            encoding="utf-8",
        )
        monkeypatch.chdir(project)

        result = runner.invoke(app, ["integration", "status"])

        assert result.exit_code != 0
        assert "Default integration: [red]x[/red]" in result.output
        assert "Installed integrations: [red]x[/red]" in result.output


# ── install ──────────────────────────────────────────────────────────


class TestIntegrationInstall:
    def test_install_requires_speckit_project(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "install", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a spec-kit project" in result.output

    def test_install_unknown_integration(self, tmp_path):
        project = _init_project(tmp_path)
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "install", "nonexistent"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Unknown integration" in result.output

    def test_install_already_installed(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "install", "copilot"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        plain = strip_ansi(result.output)
        assert "already installed" in plain
        normalized = " ".join(plain.split())
        assert "specify integration upgrade copilot" in normalized
        assert "already the default integration" in normalized
        assert "No files were changed" in normalized
        assert "specify integration uninstall copilot" not in normalized

    def test_install_already_installed_non_default_guides_use(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, ["integration", "install", "codex"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        normalized = " ".join(output.split())
        assert "already installed" in normalized
        assert "specify integration use codex" in normalized
        assert "specify integration upgrade codex" in normalized
        assert "specify integration uninstall codex" not in normalized

    def test_install_different_when_one_exists(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "install", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        plain = strip_ansi(result.output)
        assert "Installed integrations: copilot" in plain
        assert "Default integration: copilot" in plain
        normalized = " ".join(plain.split())
        assert "To replace the default integration" in normalized
        assert "specify integration switch claude" in normalized
        assert "To install 'claude' alongside" in normalized
        assert "retry the same install command with --force" in normalized

    def test_install_multi_safe_integration(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert "installed successfully" in result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"
        assert data["default_integration"] == "claude"
        assert data["integration_state_schema"] == 1
        assert data["installed_integrations"] == ["claude", "codex"]
        assert data["integration_settings"]["claude"]["invoke_separator"] == "-"
        assert data["integration_settings"]["codex"]["invoke_separator"] == "-"

        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (project / ".agents" / "skills" / "speckit-plan" / "SKILL.md").exists()

    def test_install_non_default_refreshes_init_options_version_only(self, tmp_path, monkeypatch):
        project = _init_project(tmp_path, "claude")
        init_options = project / ".specify" / "init-options.json"
        opts = json.loads(init_options.read_text(encoding="utf-8"))
        opts["speckit_version"] = "0.6.1"
        init_options.write_text(json.dumps(opts), encoding="utf-8")

        import specify_cli.integrations._commands as _int_cmds

        monkeypatch.setattr(_int_cmds, "get_speckit_version", lambda: "0.8.11")

        result = _run_in_project(project, [
            "integration", "install", "codex",
            "--script", "sh",
        ])

        assert result.exit_code == 0, result.output
        updated = json.loads(init_options.read_text(encoding="utf-8"))
        assert updated["speckit_version"] == "0.8.11"
        assert updated["integration"] == "claude"
        assert updated["ai"] == "claude"
        assert "context_file" not in updated

    def test_install_additional_preserves_shared_manifest(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        shared_manifest = project / ".specify" / "integrations" / "speckit.manifest.json"
        before = set(json.loads(shared_manifest.read_text(encoding="utf-8"))["files"])
        assert before

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        after = set(json.loads(shared_manifest.read_text(encoding="utf-8"))["files"])
        assert before <= after

    def test_install_multi_safe_migrates_legacy_state(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        int_json = project / ".specify" / "integration.json"
        int_json.write_text(json.dumps({
            "integration": "claude",
            "version": "0.0.0",
        }), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads(int_json.read_text(encoding="utf-8"))
        assert data["integration"] == "claude"
        assert data["default_integration"] == "claude"
        assert data["installed_integrations"] == ["claude", "codex"]

    def test_install_multi_unsafe_requires_force(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        plain = strip_ansi(result.output)
        assert "Installed integrations: copilot" in plain
        assert "multi-install safe" in plain
        normalized = " ".join(plain.split())
        assert "To replace the default integration" in normalized
        assert "specify integration switch claude" in normalized
        assert "To install 'claude' alongside" in normalized
        assert "retry the same install command with --force" in normalized

    def test_install_multi_unsafe_allowed_with_force(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
                "--force",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"
        assert data["installed_integrations"] == ["copilot", "claude"]

    def test_install_into_bare_project(self, tmp_path):
        """Install into a project with .specify/ but no integration."""
        project = tmp_path / "bare"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert "installed successfully" in result.output

        # integration.json written
        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"

        # Manifest created
        assert (project / ".specify" / "integrations" / "claude.manifest.json").exists()

        # Claude uses skills directory (not commands)
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

    def test_install_bare_project_gets_shared_infra(self, tmp_path):
        """Installing into a bare project should create shared scripts and templates."""
        project = tmp_path / "bare"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        # Shared infrastructure should be present
        assert (project / ".specify" / "scripts").is_dir()
        assert (project / ".specify" / "templates").is_dir()
        script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        script_content = script.read_text(encoding="utf-8")
        assert "/speckit-specify" in script_content
        assert "/speckit.specify" not in script_content


# ── uninstall ────────────────────────────────────────────────────────


class TestIntegrationUninstall:
    def test_uninstall_requires_speckit_project(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "uninstall"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a spec-kit project" in result.output

    def test_uninstall_no_integration(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "No integration" in result.output

    def test_uninstall_removes_files(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        # Claude uses skills directory
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (project / ".specify" / "integrations" / "claude.manifest.json").exists()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "uninstalled" in result.output

        # Command files removed
        assert not (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

        # Manifest removed
        assert not (project / ".specify" / "integrations" / "claude.manifest.json").exists()

        # integration.json removed
        assert not (project / ".specify" / "integration.json").exists()

    def test_uninstall_preserves_modified_files(self, tmp_path):
        """Full lifecycle: install → modify → uninstall → modified file kept."""
        project = _init_project(tmp_path, "claude")
        plan_file = project / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
        assert plan_file.exists()

        # Modify a file
        plan_file.write_text("# My custom plan command\n", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "preserved" in result.output
        assert ".claude/skills/speckit-plan/SKILL.md" in result.output

        # Modified file kept
        assert plan_file.exists()
        assert plan_file.read_text(encoding="utf-8") == "# My custom plan command\n"

    def test_uninstall_wrong_key(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_uninstall_invalid_manifest_reports_cli_error(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        _write_invalid_manifest(project, "claude")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "manifest" in result.output
        assert "unreadable" in result.output

    def test_uninstall_non_default_preserves_default(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, [
                "integration", "uninstall", "codex",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert not (project / ".agents" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"
        assert data["installed_integrations"] == ["claude"]

    def test_uninstall_default_refreshes_templates_for_fallback(self, tmp_path):
        project = _init_project(tmp_path, "gemini")
        template = project / ".specify" / "templates" / "plan-template.md"
        script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        assert "/speckit.plan" in template.read_text(encoding="utf-8")
        assert "/speckit.plan" in script.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, ["integration", "uninstall", "gemini"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"
        assert "/speckit-plan" in template.read_text(encoding="utf-8")
        assert "/speckit-plan" in script.read_text(encoding="utf-8")

    def test_uninstall_preserves_shared_infra(self, tmp_path):
        """Shared scripts and templates are not removed by integration uninstall."""
        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "common.sh"
        assert shared_script.exists()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0

        # Shared infrastructure preserved
        assert shared_script.exists()
        assert (project / ".specify" / "templates").is_dir()


class TestIntegrationUse:
    def test_use_installed_integration_sets_default(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, ["integration", "use", "codex"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "codex"
        assert data["default_integration"] == "codex"
        assert data["installed_integrations"] == ["claude", "codex"]

        opts = json.loads((project / ".specify" / "init-options.json").read_text(encoding="utf-8"))
        assert opts["integration"] == "codex"
        assert opts["ai"] == "codex"

    def test_use_requires_installed_integration(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "use", "codex"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_use_refreshes_shared_templates_between_command_styles(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        template = project / ".specify" / "templates" / "plan-template.md"
        script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        assert "/speckit-plan" in template.read_text(encoding="utf-8")
        assert "/speckit-plan" in script.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "gemini",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            use_gemini = runner.invoke(app, ["integration", "use", "gemini"], catch_exceptions=False)
            assert use_gemini.exit_code == 0, use_gemini.output
            assert "/speckit.plan" in template.read_text(encoding="utf-8")
            assert "/speckit.plan" in script.read_text(encoding="utf-8")
            assert "/speckit-plan" not in script.read_text(encoding="utf-8")

            use_claude = runner.invoke(app, ["integration", "use", "claude"], catch_exceptions=False)
            assert use_claude.exit_code == 0, use_claude.output
            assert "/speckit-plan" in template.read_text(encoding="utf-8")
            assert "/speckit-plan" in script.read_text(encoding="utf-8")
            assert "/speckit.plan" not in script.read_text(encoding="utf-8")
        finally:
            os.chdir(old_cwd)

    def test_use_preserves_modified_templates_unless_forced(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        template = project / ".specify" / "templates" / "plan-template.md"
        template.write_text("custom template with /speckit-plan\n", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "gemini",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            use_gemini = runner.invoke(app, ["integration", "use", "gemini"], catch_exceptions=False)
            assert use_gemini.exit_code == 0, use_gemini.output
            normalized = " ".join(use_gemini.output.split())
            assert "specify integration use gemini --force" in normalized
            assert template.read_text(encoding="utf-8") == "custom template with /speckit-plan\n"

            force_use = runner.invoke(app, [
                "integration", "use", "gemini",
                "--force",
            ], catch_exceptions=False)
            assert force_use.exit_code == 0, force_use.output
        finally:
            os.chdir(old_cwd)

        updated = template.read_text(encoding="utf-8")
        assert "/speckit.plan" in updated
        assert "custom template" not in updated

    def test_use_does_not_persist_default_when_shared_infra_refresh_fails(self, tmp_path, monkeypatch):
        project = _init_project(tmp_path, "claude")
        int_json = project / ".specify" / "integration.json"
        init_options = project / ".specify" / "init-options.json"

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            before_state = json.loads(int_json.read_text(encoding="utf-8"))
            before_options = json.loads(init_options.read_text(encoding="utf-8"))
            import specify_cli

            def fail_refresh(*args, **kwargs):
                raise ValueError("refuse refresh")

            monkeypatch.setattr(specify_cli, "_install_shared_infra", fail_refresh)

            result = runner.invoke(app, [
                "integration", "use", "codex",
                "--force",
            ])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        assert "Failed to refresh shared infrastructure" in result.output
        assert json.loads(int_json.read_text(encoding="utf-8")) == before_state
        assert json.loads(init_options.read_text(encoding="utf-8")) == before_options


# ── switch ───────────────────────────────────────────────────────────


class TestIntegrationSwitch:
    def test_switch_requires_speckit_project(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "switch", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a spec-kit project" in result.output

    def test_switch_unknown_target(self, tmp_path):
        project = _init_project(tmp_path)
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "switch", "nonexistent"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Unknown integration" in result.output

    def test_switch_invalid_current_manifest_reports_cli_error(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        _write_invalid_manifest(project, "claude")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "codex",
                "--script", "sh",
            ])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Could not read integration manifest" in result.output

    def test_switch_same_noop(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "switch", "copilot"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "already the default integration" in result.output

    def test_switch_same_force_refreshes_shared_templates(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        template = project / ".specify" / "templates" / "plan-template.md"
        script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        template.write_text("# custom shared template\n", encoding="utf-8")
        script.write_text("# custom shared script\n", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "claude",
                "--force",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert "shared infrastructure refreshed" in result.output
        assert "managed shared infrastructure refreshed" not in result.output
        assert "/speckit-plan" in template.read_text(encoding="utf-8")
        assert "/speckit-plan" in script.read_text(encoding="utf-8")

    def test_switch_installed_target_rejects_integration_options(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, [
                "integration", "switch", "codex",
                "--integration-options", "--bogus",
            ])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "--integration-options cannot be used" in result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["default_integration"] == "claude"

    def test_switch_between_integrations(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        # Verify claude files exist (claude uses skills)
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()
        shared_script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        assert "/speckit-specify" in shared_script.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert "Switched to" in result.output

        # Old claude files removed
        assert not (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

        # New copilot files created
        assert (project / ".github" / "agents" / "speckit.plan.agent.md").exists()
        assert "/speckit.specify" in shared_script.read_text(encoding="utf-8")
        assert "/speckit-specify" not in shared_script.read_text(encoding="utf-8")

        # integration.json updated
        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"

    def test_switch_migrates_extension_commands(self, tmp_path):
        """Switching should migrate extension commands to the new agent directory."""
        project = _init_project(tmp_path, "kimi")

        # Install the bundled git extension
        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        # Verify git extension skills exist for kimi
        kimi_git_feature = project / ".kimi" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert kimi_git_feature.exists(), "Git extension skill should exist for kimi"

        result = _run_in_project(project, [
            "integration", "switch", "opencode",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        # Git extension commands should exist for opencode
        opencode_git_feature = project / ".opencode" / "commands" / "speckit.git.feature.md"
        assert opencode_git_feature.exists(), "Git extension command should exist for opencode"

        # Old kimi extension skills should be removed
        assert not kimi_git_feature.exists(), "Old kimi extension skill should be removed"

        # Extension registry should be updated
        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        registered_commands = registry["extensions"]["git"]["registered_commands"]
        assert "opencode" in registered_commands
        assert "kimi" not in registered_commands

        # Switch to claude
        result = _run_in_project(project, [
            "integration", "switch", "claude",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        # Git extension skills should exist for claude
        claude_git_feature = project / ".claude" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert claude_git_feature.exists(), "Git extension skill should exist for claude"

        # Old opencode extension commands should be removed
        assert not opencode_git_feature.exists(), "Old opencode extension command should be removed"

        # Extension registry should be updated
        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        registered_commands = registry["extensions"]["git"]["registered_commands"]
        assert "claude" in registered_commands
        assert "opencode" not in registered_commands

    def test_switch_migrates_copilot_skills_extension_commands(self, tmp_path):
        """Copilot --skills should receive extension skills, not .agent.md files."""
        project = _init_project(tmp_path, "opencode")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        result = _run_in_project(project, [
            "integration", "switch", "copilot",
            "--script", "sh",
            "--integration-options", "--skills",
        ])
        assert result.exit_code == 0, result.output

        copilot_git_feature = project / ".github" / "skills" / "speckit-git-feature" / "SKILL.md"
        copilot_agent_file = project / ".github" / "agents" / "speckit.git.feature.agent.md"
        assert copilot_git_feature.exists(), "Git extension skill should exist for Copilot skills mode"
        assert not copilot_agent_file.exists(), "Copilot skills mode should not create extension .agent.md files"

        # Verify Copilot skill frontmatter does NOT contain mode: — VS Code Copilot does not support it
        skill_content = copilot_git_feature.read_text(encoding="utf-8")
        assert "mode:" not in skill_content, (
            "Copilot skill frontmatter must not contain unsupported 'mode' field"
        )

        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        git_meta = registry["extensions"]["git"]
        assert "speckit-git-feature" in git_meta["registered_skills"]
        assert "copilot" not in git_meta["registered_commands"]

        result = _run_in_project(project, [
            "integration", "switch", "opencode",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        opencode_git_feature = project / ".opencode" / "commands" / "speckit.git.feature.md"
        assert opencode_git_feature.exists(), "Git extension command should exist for opencode"
        assert not copilot_git_feature.exists(), "Old Copilot extension skill should be removed"

        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        git_meta = registry["extensions"]["git"]
        assert git_meta["registered_skills"] == []
        assert "opencode" in git_meta["registered_commands"]
        assert "copilot" not in git_meta["registered_commands"]

    def test_switch_does_not_register_disabled_extensions(self, tmp_path):
        """Disabled extensions should stay disabled and should not migrate commands."""
        project = _init_project(tmp_path, "opencode")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"
        result = _run_in_project(project, ["extension", "disable", "git"])
        assert result.exit_code == 0, result.output

        opencode_git_feature = project / ".opencode" / "commands" / "speckit.git.feature.md"
        assert opencode_git_feature.exists(), "Disabled extension command remains until integration switch"

        result = _run_in_project(project, [
            "integration", "switch", "claude",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        claude_git_feature = project / ".claude" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert not claude_git_feature.exists(), "Disabled extension should not be registered for new agent"
        assert not opencode_git_feature.exists(), "Old disabled extension command should be removed on switch"

        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        git_meta = registry["extensions"]["git"]
        assert git_meta["enabled"] is False
        assert "claude" not in git_meta["registered_commands"]
        assert "opencode" not in git_meta["registered_commands"]

    def test_switch_refreshes_managed_shared_script_refs(self, tmp_path):
        """Switching refreshes managed shared scripts to the target command style."""
        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "setup-tasks.sh"
        assert shared_script.exists()
        shared_content = shared_script.read_text(encoding="utf-8")
        assert "/speckit-plan" in shared_content

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0

        assert shared_script.exists()
        updated = shared_script.read_text(encoding="utf-8")
        assert "/speckit.plan" in updated
        assert "/speckit-plan" not in updated

    def test_switch_refreshes_stale_managed_shared_infra(self, tmp_path):
        """Regression for #2293: stale managed shared scripts get refreshed on switch."""
        import hashlib

        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "setup-tasks.sh"
        assert "/speckit-plan" in shared_script.read_text(encoding="utf-8")

        # Simulate a stale vendored script: write truncated content as bytes
        # (write_text would translate \n→\r\n on Windows and break the hash)
        # and update the speckit manifest hash so the stale copy is treated
        # as "managed" (installed by spec-kit, not a user customization).
        stale_bytes = b"#!/usr/bin/env bash\n# stale vendored copy\n"
        shared_script.write_bytes(stale_bytes)

        manifest_path = project / ".specify" / "integrations" / "speckit.manifest.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_data["files"][".specify/scripts/bash/setup-tasks.sh"] = (
            hashlib.sha256(stale_bytes).hexdigest()
        )
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0

        # Stale managed file should be replaced by the target integration's rendered version.
        updated = shared_script.read_text(encoding="utf-8")
        assert "# stale vendored copy" not in updated
        assert "/speckit.plan" in updated
        assert "/speckit-plan" not in updated

    def test_switch_preserves_user_customized_shared_infra(self, tmp_path):
        """User customizations (hash divergence from manifest) survive switch without --refresh-shared-infra."""
        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "common.sh"

        # User customization: append bytes but do NOT update manifest hash,
        # so on-disk hash diverges from the recorded one.
        original = shared_script.read_bytes()
        custom_bytes = original + b"\n# user customization\n"
        shared_script.write_bytes(custom_bytes)

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert shared_script.read_bytes() == custom_bytes
        assert "Preserved" in result.output

    def test_switch_refresh_shared_infra_overwrites_customizations(self, tmp_path):
        """--refresh-shared-infra explicitly overwrites user customizations on switch."""
        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "setup-tasks.sh"
        assert "/speckit-plan" in shared_script.read_text(encoding="utf-8")
        rendered_bytes = shared_script.read_bytes()

        # User customization (hash diverges from manifest)
        custom_bytes = rendered_bytes + b"\n# user customization\n"
        shared_script.write_bytes(custom_bytes)

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
                "--refresh-shared-infra",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        # Customization is overwritten with the target integration's rendered version.
        updated = shared_script.read_text(encoding="utf-8")
        assert "# user customization" not in updated
        assert "/speckit.plan" in updated
        assert "/speckit-plan" not in updated

    def test_switch_preserves_recovered_files(self, tmp_path):
        """Regression for #2918: files marked recovered in the manifest are not overwritten.

        When a file already exists on disk before init and is recorded with
        ``recovered=True``, ``integration use``/``switch`` must not treat it as
        managed even when the on-disk hash matches the manifest hash.
        """
        import hashlib

        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "setup-tasks.sh"
        assert shared_script.is_file()

        # Simulate a team-customized file that was recorded as recovered:
        # write custom content, then update the manifest to record its hash
        # with the recovered flag set.
        custom_bytes = b"#!/usr/bin/env bash\n# team custom workflow\nexit 0\n"
        shared_script.write_bytes(custom_bytes)

        manifest_path = project / ".specify" / "integrations" / "speckit.manifest.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        rel = ".specify/scripts/bash/setup-tasks.sh"
        manifest_data["files"][rel] = hashlib.sha256(custom_bytes).hexdigest()
        manifest_data.setdefault("recovered_files", []).append(rel)
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        # Recovered file must NOT be overwritten — team content preserved.
        assert shared_script.read_bytes() == custom_bytes

    def test_switch_skips_symlinked_parent_directory(self, tmp_path):
        """Regression: if .specify/scripts/bash is a symlink, switch must not write through it.

        Copilot follow-up on #2375: leaf-only symlink check let writes escape
        when an *ancestor* directory was symlinked outside the project root.
        """
        import sys
        if sys.platform.startswith("win"):
            import pytest as _pytest
            _pytest.skip("Symlink creation typically requires admin on Windows")

        project = _init_project(tmp_path, "claude")
        bash_dir = project / ".specify" / "scripts" / "bash"
        outside = tmp_path / "outside"
        outside.mkdir()
        for child in bash_dir.iterdir():
            child.rename(outside / child.name)
        bash_dir.rmdir()
        bash_dir.symlink_to(outside, target_is_directory=True)
        sentinel = (outside / "common.sh").read_bytes()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        # Symlinked tree reported, not written through.
        assert "symlink" in result.output.lower()
        # Outside dir contents unchanged.
        assert (outside / "common.sh").read_bytes() == sentinel

    def test_switch_force_alone_does_not_overwrite_shared_customizations(self, tmp_path):
        """--force (uninstall semantics) must NOT overwrite shared-infra customizations.

        Regression: ensures the decoupling of --force and --refresh-shared-infra.
        """
        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "common.sh"
        bundled_bytes = shared_script.read_bytes()

        custom_bytes = bundled_bytes + b"\n# user customization\n"
        shared_script.write_bytes(custom_bytes)

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
                "--force",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        # --force alone preserves the customization
        assert shared_script.read_bytes() == custom_bytes

    def test_switch_from_nothing(self, tmp_path):
        """Switch when no integration is installed should just install the target."""
        project = tmp_path / "bare"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "Switched to" in result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"

    def test_failed_switch_keeps_fallback_metadata_consistent(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, [
                "integration", "switch", "generic",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "codex"
        assert data["installed_integrations"] == ["codex"]

        opts = json.loads((project / ".specify" / "init-options.json").read_text(encoding="utf-8"))
        assert opts["integration"] == "codex"
        assert opts["ai"] == "codex"

        template = project / ".specify" / "templates" / "plan-template.md"
        assert "/speckit-plan" in template.read_text(encoding="utf-8")


class TestIntegrationUpgrade:
    def test_upgrade_invalid_manifest_reports_cli_error(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        _write_invalid_manifest(project, "claude")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "manifest" in result.output
        assert "unreadable" in result.output

    def test_upgrade_refreshes_init_options_speckit_version(self, tmp_path, monkeypatch):
        project = _init_project(tmp_path, "claude")
        init_options = project / ".specify" / "init-options.json"
        opts = json.loads(init_options.read_text(encoding="utf-8"))
        opts["speckit_version"] = "0.6.1"
        init_options.write_text(json.dumps(opts), encoding="utf-8")

        import specify_cli.integrations._commands as _int_cmds

        monkeypatch.setattr(_int_cmds, "get_speckit_version", lambda: "0.8.11")

        result = _run_in_project(project, [
            "integration", "upgrade", "claude",
            "--force",
        ])

        assert result.exit_code == 0, result.output
        updated = json.loads(init_options.read_text(encoding="utf-8"))
        assert updated["speckit_version"] == "0.8.11"

    def test_upgrade_non_default_refreshes_init_options_version_only(self, tmp_path, monkeypatch):
        project = _init_project(tmp_path, "gemini")
        install = _run_in_project(project, [
            "integration", "install", "claude",
            "--script", "sh",
        ])
        assert install.exit_code == 0, install.output

        init_options = project / ".specify" / "init-options.json"
        opts = json.loads(init_options.read_text(encoding="utf-8"))
        opts["speckit_version"] = "0.6.1"
        init_options.write_text(json.dumps(opts), encoding="utf-8")

        import specify_cli.integrations._commands as _int_cmds

        monkeypatch.setattr(_int_cmds, "get_speckit_version", lambda: "0.8.11")

        result = _run_in_project(project, [
            "integration", "upgrade", "claude",
            "--script", "sh",
            "--force",
        ])

        assert result.exit_code == 0, result.output
        updated = json.loads(init_options.read_text(encoding="utf-8"))
        assert updated["speckit_version"] == "0.8.11"
        assert updated["integration"] == "gemini"
        assert updated["ai"] == "gemini"
        assert "context_file" not in updated

    def test_upgrade_does_not_persist_state_when_shared_infra_refresh_fails(self, tmp_path, monkeypatch):
        project = _init_project(tmp_path, "claude")
        int_json = project / ".specify" / "integration.json"
        init_options = project / ".specify" / "init-options.json"
        manifest_path = project / ".specify" / "integrations" / "claude.manifest.json"

        before_state = json.loads(int_json.read_text(encoding="utf-8"))
        before_options = json.loads(init_options.read_text(encoding="utf-8"))
        before_manifest = manifest_path.read_text(encoding="utf-8")

        import specify_cli

        real_install_shared_infra = specify_cli._install_shared_infra
        calls = {"count": 0}

        def fail_refresh(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 2:
                raise ValueError("refuse refresh")
            return real_install_shared_infra(*args, **kwargs)

        monkeypatch.setattr(specify_cli, "_install_shared_infra", fail_refresh)

        result = _run_in_project(project, [
            "integration", "upgrade", "claude",
            "--force",
        ])

        assert result.exit_code != 0
        assert "Failed to refresh shared infrastructure" in result.output
        assert json.loads(int_json.read_text(encoding="utf-8")) == before_state
        assert json.loads(init_options.read_text(encoding="utf-8")) == before_options
        assert manifest_path.read_text(encoding="utf-8") == before_manifest

    def test_upgrade_default_refreshes_shared_script_refs_for_option_separator_change(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        template = project / ".specify" / "templates" / "plan-template.md"
        managed_script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        customized_script = project / ".specify" / "scripts" / "bash" / "setup-tasks.sh"

        assert "/speckit.plan" in template.read_text(encoding="utf-8")
        assert "/speckit.specify" in managed_script.read_text(encoding="utf-8")
        customized_before = customized_script.read_text(encoding="utf-8") + "\n# user customization\n"
        customized_script.write_text(customized_before, encoding="utf-8")

        result = _run_in_project(project, [
            "integration", "upgrade", "copilot",
            "--integration-options", "--skills",
        ])

        assert result.exit_code == 0, result.output
        assert "/speckit-plan" in template.read_text(encoding="utf-8")
        managed_content = managed_script.read_text(encoding="utf-8")
        assert "/speckit-specify" in managed_content
        assert "/speckit.specify" not in managed_content
        assert customized_script.read_text(encoding="utf-8") == customized_before

    def test_upgrade_non_default_keeps_default_template_invocations(self, tmp_path):
        project = _init_project(tmp_path, "gemini")
        template = project / ".specify" / "templates" / "plan-template.md"
        script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        assert "/speckit.plan" in template.read_text(encoding="utf-8")
        assert "/speckit.plan" in script.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, [
                "integration", "upgrade", "claude",
                "--script", "sh",
                "--force",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "gemini"
        assert "/speckit.plan" in template.read_text(encoding="utf-8")
        assert "/speckit.plan" in script.read_text(encoding="utf-8")
        assert "/speckit-plan" not in script.read_text(encoding="utf-8")

    def test_upgrade_migrates_opencode_legacy_dir(self, tmp_path):
        """Upgrade moves OpenCode commands from .opencode/command/ to .opencode/commands/."""
        project = _init_project(tmp_path, "opencode")

        # Simulate a legacy project: rename commands/ back to command/
        canonical = project / ".opencode" / "commands"
        legacy = project / ".opencode" / "command"
        assert canonical.is_dir(), "init should have created .opencode/commands/"
        canonical.rename(legacy)
        assert legacy.is_dir()
        assert not canonical.exists()

        # Patch the manifest to reflect old paths (command/ not commands/)
        manifest_path = project / ".specify" / "integrations" / "opencode.manifest.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        patched_files = {}
        for path, info in manifest_data.get("files", {}).items():
            patched_files[path.replace(".opencode/commands/", ".opencode/command/")] = info
        manifest_data["files"] = patched_files
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        old_commands = sorted(legacy.glob("speckit.*.md"))
        assert len(old_commands) > 0, "Legacy dir should have speckit command files"

        result = _run_in_project(project, [
            "integration", "upgrade", "opencode",
            "--script", "sh",
            "--force",
        ])
        assert result.exit_code == 0, f"upgrade failed: {result.output}"

        # New commands in canonical dir
        assert canonical.is_dir(), ".opencode/commands/ should exist after upgrade"
        new_commands = sorted(canonical.glob("speckit.*.md"))
        assert len(new_commands) > 0, "Commands should exist in .opencode/commands/"

        # Stale files removed from legacy dir (extension-installed commands
        # like agent-context.update may still appear — only check the original
        # core command stems that should have been migrated).
        core_remaining = [
            f for f in legacy.glob("speckit.*.md")
            if "agent-context" not in f.name
        ]
        assert len(core_remaining) == 0, (
            f"Legacy .opencode/command/ should have no core speckit files after upgrade, "
            f"found: {[f.name for f in core_remaining]}"
        )

    def test_upgrade_preserves_existing_vscode_settings(self, tmp_path):
        """Regression: copilot upgrade must not stale-delete .vscode/settings.json.

        On init the file is created and recorded in the manifest. On upgrade,
        setup() merges into the now-existing file and intentionally stops
        tracking it, so without ``stale_cleanup_exclusions()`` the Phase 2
        stale cleanup would delete it (destroying the user's settings).
        """
        project = _init_project(tmp_path, "copilot")
        settings = project / ".vscode" / "settings.json"
        assert settings.is_file(), "init should create .vscode/settings.json"
        before = json.loads(settings.read_text(encoding="utf-8"))
        assert before, "settings.json should contain managed defaults"

        # Simulate a user editing their settings: add a custom key that the
        # integration does not manage.  It must survive the upgrade.
        before["editor.fontSize"] = 17
        settings.write_text(json.dumps(before), encoding="utf-8")

        result = _run_in_project(project, [
            "integration", "upgrade", "copilot",
            "--script", "sh", "--force",
        ])
        assert result.exit_code == 0, result.output

        assert settings.is_file(), ".vscode/settings.json must survive upgrade"
        after = json.loads(settings.read_text(encoding="utf-8"))
        assert after.get("editor.fontSize") == 17, (
            "user-defined settings must be preserved after upgrade"
        )

    def test_upgrade_restores_executable_bit_on_shared_scripts(self, tmp_path):
        """Regression: scripts refreshed by the managed-refresh step stay +x."""
        if os.name == "nt":
            pytest.skip("POSIX execute bits are not meaningful on Windows")
        project = _init_project(tmp_path, "copilot")
        script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        assert script.is_file()
        # Simulate a perms-losing install (e.g. wheel extraction dropping +x).
        script.chmod(0o644)
        assert not (script.stat().st_mode & 0o111)

        result = _run_in_project(project, [
            "integration", "upgrade", "copilot",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        assert script.stat().st_mode & 0o111, (
            "shared .sh scripts must be executable after upgrade"
        )


# ── Full lifecycle ───────────────────────────────────────────────────


class TestIntegrationLifecycle:
    def test_install_modify_uninstall_preserves_modified(self, tmp_path):
        """Full lifecycle: install → modify file → uninstall → verify modified file kept."""
        project = tmp_path / "lifecycle"
        project.mkdir()
        (project / ".specify").mkdir()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)

            # Install
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
            assert result.exit_code == 0
            assert "installed successfully" in result.output

            # Claude uses skills directory
            plan_file = project / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
            assert plan_file.exists()

            # Modify one file
            plan_file.write_text("# user customization\n", encoding="utf-8")

            # Uninstall
            result = runner.invoke(app, ["integration", "uninstall"], catch_exceptions=False)
            assert result.exit_code == 0
            assert "preserved" in result.output

            # Modified file kept
            assert plan_file.exists()
            assert plan_file.read_text(encoding="utf-8") == "# user customization\n"
        finally:
            os.chdir(old_cwd)


# ── Edge-case fixes ─────────────────────────────────────────────────


class TestScriptTypeValidation:
    def test_invalid_script_type_rejected(self, tmp_path):
        """--script with an invalid value should fail with a clear error."""
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "bash",
            ])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Invalid script type" in result.output

    def test_valid_script_types_accepted(self, tmp_path):
        """Both 'sh' and 'ps' should be accepted."""
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0


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


class TestUninstallNoManifestClearsInitOptions:
    def test_init_options_cleared_on_no_manifest_uninstall(self, tmp_path):
        """When no manifest exists, uninstall should still clear init-options.json."""
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()

        # Write integration.json and init-options.json without a manifest
        int_json = project / ".specify" / "integration.json"
        int_json.write_text(json.dumps({"integration": "claude"}), encoding="utf-8")

        opts_json = project / ".specify" / "init-options.json"
        opts_json.write_text(json.dumps({
            "integration": "claude",
            "ai": "claude",
            "ai_skills": True,
            "script": "sh",
        }), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0

        # init-options.json should have integration keys cleared
        opts = json.loads(opts_json.read_text(encoding="utf-8"))
        assert "integration" not in opts
        assert "ai" not in opts
        assert "ai_skills" not in opts
        # Non-integration keys preserved
        assert opts.get("script") == "sh"


class TestSwitchClearsMetadataAfterTeardown:
    def test_metadata_cleared_between_phases(self, tmp_path):
        """After a successful switch, metadata should reference the new integration."""
        project = _init_project(tmp_path, "claude")

        # Verify initial state
        int_json = project / ".specify" / "integration.json"
        assert json.loads(int_json.read_text(encoding="utf-8"))["integration"] == "claude"

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            # Switch to copilot — should succeed and update metadata
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0

        # integration.json should reference copilot, not claude
        data = json.loads(int_json.read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"

        # init-options.json should reference copilot
        opts_json = project / ".specify" / "init-options.json"
        opts = json.loads(opts_json.read_text(encoding="utf-8"))
        assert opts.get("ai") == "copilot"
