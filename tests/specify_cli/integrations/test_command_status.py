"""Tests for mirrored integration CLI behavior in test_command_status.py."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401
import shutil  # noqa: F401
from pathlib import Path  # noqa: F401

import pytest  # noqa: F401

from specify_cli import app  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401
from tests.specify_cli.integrations._helpers import (
    _copy_project_template,  # noqa: F401
    _init_project,  # noqa: F401
    _integration_list_row_cells,  # noqa: F401
    _move_kilocode_install_to_legacy_layout,  # noqa: F401
    _run_in_project,  # noqa: F401
    _write_invalid_manifest,  # noqa: F401
    runner,  # noqa: F401
)

class TestIntegrationStatus:
    def test_status_requires_speckit_project(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["integration", "status"])
        assert result.exit_code != 0
        assert "Not a Spec Kit project" in result.output

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
