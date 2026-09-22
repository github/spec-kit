"""Tests for ``specify extension add``.

Mirrors ``specify_cli.extensions.command_add``.
"""

from __future__ import annotations

import io
import json
import os
import stat
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import (
    CompatibilityError,
    ExtensionCatalog,
    ExtensionError,
    ExtensionManager,
    ExtensionRegistry,
    ValidationError,
)
from tests.conftest import strip_ansi
from tests.specify_cli.extensions._helpers import (
    MINIMAL_ZIP_BYTES as _MINIMAL_ZIP_BYTES,
    can_create_symlink,
    open_test_download_zip as _open_test_download_zip,
    validate_safe_cache_dir as _validate_safe_cache_dir_test_stand_in,
)


class TestExtensionAddCLI:
    """CLI tests for ``specify extension add``."""

    def test_add_dev_links_copilot_agent_when_supported(
        self, extension_dir, project_dir, temp_dir
    ):
        """extension add --dev should link generated agent files when possible."""
        from specify_cli import app

        (project_dir / ".github" / "agents").mkdir(parents=True)

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", str(extension_dir), "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output

        agent_file = (
            project_dir
            / ".github"
            / "agents"
            / "speckit.test-ext.hello.agent.md"
        )
        assert agent_file.exists()
        if can_create_symlink(temp_dir):
            assert agent_file.is_symlink()
            assert ".specify-dev" in agent_file.resolve().parts
        else:
            assert not agent_file.is_symlink()

    @pytest.mark.skipif(
        os.name == "nt", reason="POSIX execute bits are not meaningful on Windows"
    )
    def test_add_makes_shipped_scripts_executable(self, extension_dir, project_dir):
        """extension add must restore execute bits on bundled POSIX scripts.

        Archives are unpacked with zipfile.extractall and --dev installs copy the
        tree; neither restores a stripped Unix mode, so a shipped *.sh can land
        non-executable and a documented `.specify/extensions/<id>/scripts/...`
        invocation then fails with "Permission denied". init / migrate /
        integration-install already call ensure_executable_scripts(); this guards
        that `extension add` does too.
        """

        scripts_dir = extension_dir / "scripts"
        scripts_dir.mkdir()
        script = scripts_dir / "gate.sh"
        script.write_text("#!/usr/bin/env bash\necho hi\n")
        script.chmod(0o644)  # non-executable, as an unpacked/copied script may be
        assert not os.access(script, os.X_OK)

        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", str(extension_dir), "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        installed = (
            project_dir / ".specify" / "extensions" / "test-ext" / "scripts" / "gate.sh"
        )
        assert installed.exists(), result.output
        assert os.access(installed, os.X_OK), (
            f"installed script not executable: mode="
            f"{stat.S_IMODE(installed.stat().st_mode):o}"
        )

    def test_add_dev_writes_codex_skills_as_files(self, extension_dir, project_dir):
        """Codex dev skills should be written as files so Codex can load them."""
        from specify_cli import app

        init_options = project_dir / ".specify" / "init-options.json"
        init_options.write_text(
            json.dumps({"ai": "codex", "ai_skills": True}), encoding="utf-8"
        )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", str(extension_dir), "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output

        skill_file = (
            project_dir
            / ".agents"
            / "skills"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        )
        assert skill_file.exists()
        assert not skill_file.is_symlink()

        content = skill_file.read_text(encoding="utf-8")
        assert "name: speckit-test-ext-hello" in content
        assert "metadata:" in content
        assert "source: test-ext:commands/hello.md" in content

    def test_add_dev_replaces_existing_codex_skill_symlink(
        self, extension_dir, project_dir, temp_dir
    ):
        """Codex dev installs should migrate expected dev symlinks to files."""
        if not can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        from specify_cli import app

        init_options = project_dir / ".specify" / "init-options.json"
        init_options.write_text(
            json.dumps({"ai": "codex", "ai_skills": True}), encoding="utf-8"
        )

        skill_file = (
            project_dir
            / ".agents"
            / "skills"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        )
        skill_file.parent.mkdir(parents=True)
        cache_file = (
            extension_dir
            / ".specify-dev"
            / "extension-skills"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        )
        cache_file.parent.mkdir(parents=True)
        cache_file.write_text("old linked content", encoding="utf-8")
        os.symlink(os.path.relpath(cache_file, skill_file.parent), skill_file)

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", str(extension_dir), "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert skill_file.exists()
        assert not skill_file.is_symlink()
        content = skill_file.read_text(encoding="utf-8")
        assert "name: speckit-test-ext-hello" in content
        assert "source: test-ext:commands/hello.md" in content
        assert cache_file.read_text(encoding="utf-8") == "old linked content"

    def test_add_dev_falls_back_to_copy_when_windows_symlinks_unavailable(
        self, extension_dir, project_dir, monkeypatch
    ):
        """extension add --dev should work when Windows cannot create symlinks."""
        from specify_cli import app

        (project_dir / ".github" / "agents").mkdir(parents=True)

        def raise_windows_symlink_error(target, link):
            raise OSError("A required privilege is not held by the client")

        monkeypatch.setattr(
            "specify_cli.agents.os.symlink", raise_windows_symlink_error
        )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", str(extension_dir), "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output

        agent_file = (
            project_dir
            / ".github"
            / "agents"
            / "speckit.test-ext.hello.agent.md"
        )
        assert agent_file.exists()
        assert not agent_file.is_symlink()
        assert "Extension: test-ext" in agent_file.read_text(encoding="utf-8")
        assert (
            project_dir
            / ".specify"
            / "extensions"
            / "test-ext"
            / ".specify-dev"
            / "agent-commands"
            / "copilot"
            / "speckit.test-ext.hello.agent.md"
        ).exists()

    def test_add_by_display_name_uses_resolved_id_for_download(self, tmp_path):
        """extension add by display name should use resolved ID for download_extension()."""
        from specify_cli import app

        runner = CliRunner()

        # Create project structure
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".specify" / "extensions").mkdir(parents=True)

        # Mock catalog that returns extension by display name
        mock_catalog = MagicMock()
        mock_catalog.get_extension_info.return_value = None  # ID lookup fails
        mock_catalog.search.return_value = [
            {
                "id": "acme-jira-integration",
                "name": "Jira Integration",
                "version": "1.0.0",
                "description": "Jira integration extension",
                "_install_allowed": True,
            }
        ]

        # Track what ID was passed to download_extension
        download_called_with = []
        def mock_download(extension_id):
            download_called_with.append(extension_id)
            # Return a path that will fail install (we just want to verify the ID)
            raise ExtensionError("Mock download - checking ID was resolved")

        mock_catalog.download_extension.side_effect = mock_download

        with patch("specify_cli.extensions.ExtensionCatalog", return_value=mock_catalog), \
             patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", "Jira Integration"],
                catch_exceptions=True,
            )

        assert result.exit_code != 0, (
            f"Expected non-zero exit code since mock download raises, got {result.exit_code}"
        )

        # Verify download_extension was called with the resolved ID, not the display name
        assert len(download_called_with) == 1
        assert download_called_with[0] == "acme-jira-integration", (
            f"Expected download_extension to be called with resolved ID 'acme-jira-integration', "
            f"but was called with '{download_called_with[0]}'"
        )

    def test_catalog_add_forwards_catalog_name(self, tmp_path):
        """The extension catalog branch passes resolved provenance to the manager."""
        from typer.testing import CliRunner
        from specify_cli import app

        project_dir = tmp_path / "project"
        (project_dir / ".specify").mkdir(parents=True)
        archive = tmp_path / "extension.zip"
        archive.write_bytes(b"archive")
        captured = {}

        def fake_install_from_zip(self, _archive, _version, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                id="catalog-extension",
                name="Catalog Extension",
                version="1.0.0",
                description="catalog extension",
                warnings=[],
                commands=[],
            )

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "catalog-extension",
                 "name": "Catalog Extension",
                 "version": "1.0.0",
                 "_install_allowed": True,
                 "_catalog_name": "extension-catalog",
             }), \
             patch.object(ExtensionCatalog, "download_extension", return_value=archive), \
             patch.object(ExtensionManager, "install_from_zip", fake_install_from_zip), \
             patch("specify_cli.extensions._commands._refresh_events_and_warn"):
            result = CliRunner().invoke(app, ["extension", "add", "catalog-extension"])

        assert result.exit_code == 0, result.output
        assert captured["catalog_name"] == "extension-catalog"

    def test_add_discovery_only_error_suggests_resolved_id(self, tmp_path):
        """The not-installable error must suggest a copy-pasteable command using
        the resolved catalog ID, not a display name that may contain spaces."""
        from specify_cli import app

        runner = CliRunner()

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".specify" / "extensions").mkdir(parents=True)

        mock_catalog = MagicMock()
        mock_catalog.get_extension_info.return_value = None  # ID lookup fails
        mock_catalog.search.return_value = [
            {
                "id": "acme-jira-integration",
                "name": "Jira Integration",
                "version": "1.0.0",
                "description": "Jira integration extension",
                "_install_allowed": False,
                "_catalog_name": "community",
            }
        ]

        with patch("specify_cli.extensions.ExtensionCatalog", return_value=mock_catalog), \
             patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", "Jira Integration"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        output = " ".join(result.output.split())
        # Suggested command uses the resolved ID and stays a single token.
        assert "add acme-jira-integration --from" in output
        # It must not emit the space-containing display name as the command target.
        assert "add Jira Integration --from" not in output

    def test_add_discovery_only_error_neutralizes_unsafe_id(self, tmp_path):
        """A catalog-controlled ID with shell metacharacters must never be
        interpolated into the suggested command; it is replaced by a literal
        placeholder so copying the command can't execute injected shell text."""
        from specify_cli import app

        runner = CliRunner()

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".specify" / "extensions").mkdir(parents=True)

        malicious_id = "foo; rm -rf ~"
        mock_catalog = MagicMock()
        mock_catalog.get_extension_info.return_value = {
            "id": malicious_id,
            "name": "Evil Ext",
            "version": "1.0.0",
            "description": "malicious",
            "_install_allowed": False,
            "_catalog_name": "community",
        }
        mock_catalog.search.return_value = []

        with patch("specify_cli.extensions.ExtensionCatalog", return_value=mock_catalog), \
             patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", malicious_id],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        output = " ".join(result.output.split())
        # The runnable command uses a literal placeholder, never the raw ID.
        assert "add <extension-id> --from" in output
        # The malicious ID is never rendered as the target of an install command.
        assert f"add {malicious_id} --from" not in output
        assert "add foo; rm" not in output

    def test_command_safe_id_rejects_leading_hyphen(self):
        """An ID like ``--force`` matches the manifest character rule but Typer
        would parse it as an option, not the positional extension argument, so
        the helper must fall back to the placeholder."""
        from specify_cli.extensions._commands import _command_safe_id

        assert _command_safe_id("--force") == "<extension-id>"
        assert _command_safe_id("-x") == "<extension-id>"
        # A normal slug is still returned verbatim.
        assert _command_safe_id("acme-thing") == "acme-thing"

    def test_add_bundled_extension_not_found_gives_clear_error(self, tmp_path):
        """extension add should give a clear error when a bundled extension is not found locally."""
        from specify_cli import app

        runner = CliRunner()

        # Create project structure
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".specify" / "extensions").mkdir(parents=True)

        # Mock catalog that returns a bundled extension without download_url
        mock_catalog = MagicMock()
        mock_catalog.get_extension_info.return_value = {
            "id": "git",
            "name": "Git Branching Workflow",
            "version": "1.0.0",
            "description": "Git branching extension",
            "bundled": True,
            "_install_allowed": True,
        }
        mock_catalog.search.return_value = []

        with patch("specify_cli.extensions.ExtensionCatalog", return_value=mock_catalog), \
             patch("specify_cli._locate_bundled_extension", return_value=None), \
             patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", "git"],
                catch_exceptions=True,
            )

        assert result.exit_code != 0
        assert "bundled with spec-kit" in result.output
        assert "reinstall" in result.output.lower()

    def test_add_from_url_prompts_before_spinner(self, tmp_path):
        """Confirm prompt for --from <url> must fire before the console.status spinner.

        Regression test for #2783: typer.confirm() inside console.status()
        was overwritten by the Rich spinner, making the command appear hung.
        """
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        call_order: list[str] = []

        original_status = MagicMock()

        def record_status(*args, **kwargs):
            call_order.append("spinner")
            return original_status

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.console.status", side_effect=record_status), \
             patch("typer.confirm", side_effect=lambda *a, **kw: (call_order.append("confirm"), False)[-1]):
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
                catch_exceptions=True,
            )

        assert "confirm" in call_order, "confirm prompt was never called"
        # The confirm must fire BEFORE the spinner is entered
        if "spinner" in call_order:
            assert call_order.index("confirm") < call_order.index("spinner"), \
                f"confirm must precede spinner, got: {call_order}"
        assert result.exit_code == 0  # user declined → clean exit

    def test_add_from_malformed_ipv6_url_exits_cleanly(self, tmp_path):
        """A malformed IPv6 URL must produce a clean error, not a ValueError traceback."""
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://[::1/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert result.exception is None or isinstance(result.exception, SystemExit)
        plain = strip_ansi(result.output)
        assert "Invalid URL" in plain

    @pytest.mark.parametrize(
        "url",
        [
            "https:///ext.zip",
            "https://example.com:99999/ext.zip",
        ],
    )
    def test_add_from_invalid_url_exits_before_prompt(self, tmp_path, url):
        """Hostless URLs and invalid ports fail before prompting or downloading."""
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm") as confirm, \
             patch("specify_cli.authentication.http.open_url") as open_url:
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", url],
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert "Invalid URL" in strip_ansi(result.output)
        confirm.assert_not_called()
        open_url.assert_not_called()

    def test_add_from_bracketed_non_ip_url_exits_cleanly(self, tmp_path):
        """A bracketed-but-invalid IPv6 host must produce a clean error, not a
        ValueError traceback. "https://[not-an-ip]/ext.zip" is a malformed
        authority that raises ValueError during URL validation; the try/except
        guard around parsing and the .hostname read must turn that into a clean
        "Invalid URL" message.
        """
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://[not-an-ip]/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert result.exception is None or isinstance(result.exception, SystemExit)
        plain = strip_ansi(result.output)
        assert "Invalid URL" in plain

    def test_add_from_url_lazy_hostname_valueerror_exits_cleanly(self, tmp_path, monkeypatch):
        """Synthetic defensive coverage: monkeypatch urlparse() to return an
        object whose .hostname raises ValueError lazily. This does not reproduce
        any specific CPython behavior -- it just exercises the case where the
        ValueError surfaces on the .hostname read rather than at parse time, so a
        raw ValueError would leak if .hostname were read outside the try/except.
        """
        import urllib.parse
        from specify_cli import app

        real_urlparse = urllib.parse.urlparse

        class _LazyHostnameRaiser:
            def __init__(self, parsed):
                self._parsed = parsed

            @property
            def hostname(self):
                raise ValueError("simulated lazy IPv6 hostname failure")

            def __getattr__(self, name):
                return getattr(self._parsed, name)

        def _fake_urlparse(url, *args, **kwargs):
            return _LazyHostnameRaiser(real_urlparse(url, *args, **kwargs))

        monkeypatch.setattr(urllib.parse, "urlparse", _fake_urlparse)

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Invalid URL" in strip_ansi(result.output)

    def test_add_status_escapes_extension_markup(self, tmp_path):
        """User-controlled extension names must not be parsed as Rich markup."""
        from rich.markup import escape as escape_markup
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        status_messages: list[str] = []

        def record_status(message, *args, **kwargs):
            status_messages.append(message)
            return MagicMock()

        extension_name = "[red]bad[/red]"
        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.console.status", side_effect=record_status):
            result = runner.invoke(
                app,
                ["extension", "add", extension_name, "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert status_messages == [
            f"[cyan]Installing extension: {escape_markup(extension_name)}[/cyan]"
        ]

    def test_add_post_install_hint_escapes_manifest_id_markup(self, tmp_path):
        """Extension IDs printed in Rich-rendered hints must stay literal."""
        from types import SimpleNamespace
        from typer.testing import CliRunner
        from specify_cli import app

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        manifest_id = "[red]bad[/red]"

        def fake_install_from_zip(
            self_obj,
            zip_path,
            speckit_version,
            priority=10,
            force=False,
            *,
            archive_file=None,
        ):
            return SimpleNamespace(
                id=manifest_id,
                name="Bad Extension",
                version="1.0.0",
                description="Test extension",
                warnings=[],
                commands=[],
                hooks=[],
            )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=True), \
             patch("specify_cli.extensions._commands._validate_safe_cache_dir", side_effect=_validate_safe_cache_dir_test_stand_in), \
             patch("specify_cli.authentication.http.open_url", return_value=FakeResponse(_MINIMAL_ZIP_BYTES)), \
             patch("specify_cli.extensions._commands._safe_open_download_zip", side_effect=_open_test_download_zip), \
             patch.object(ExtensionManager, "install_from_zip", fake_install_from_zip), \
             patch.object(ExtensionRegistry, "get", return_value={}):
            result = runner.invoke(
                app,
                ["extension", "add", "bad", "--from", "https://example.com/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert ".specify/extensions/[red]bad[/red]/" in result.output

    def test_add_from_url_cancel_exits_cleanly(self, tmp_path):
        """Declining the --from <url> confirmation should exit with code 0."""
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=False):
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://example.com/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0
        assert "Cancelled" in result.output

    def test_add_from_url_escapes_download_exception_markup(self, tmp_path):
        """Download errors can include user-controlled URL text."""
        import urllib.error
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=True), \
             patch("specify_cli.extensions._commands._validate_safe_cache_dir", side_effect=_validate_safe_cache_dir_test_stand_in), \
             patch(
                 "specify_cli.authentication.http.open_url",
                 side_effect=urllib.error.URLError("bad [red]download[/red]"),
             ):
            result = runner.invoke(
                app,
                [
                    "extension",
                    "add",
                    "my-ext",
                    "--from",
                    "https://example.com/[red]ext[/red].zip",
                ],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "https://example.com/[red]ext[/red].zip" in result.output
        assert "bad [red]download[/red]" in result.output

    def test_add_from_url_rejects_non_zip_login_page(self, tmp_path):
        """An HTML login page (unauthenticated fetch) must fail clearly, not BadZipFile."""
        from typer.testing import CliRunner
        from specify_cli import app

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=True), \
             patch("specify_cli.extensions._commands._validate_safe_cache_dir", side_effect=_validate_safe_cache_dir_test_stand_in), \
             patch(
                 "specify_cli.authentication.http.open_url",
                 return_value=FakeResponse(b"<!DOCTYPE html><html>Sign in</html>"),
             ), \
             patch.object(ExtensionManager, "install_from_zip") as install:
            result = runner.invoke(
                app,
                ["extension", "add", "my-ext", "--from", "https://raw.ghe.example/o/r/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "did not return a ZIP archive" in result.output
        install.assert_not_called()

    def test_add_from_url_rejects_oversized_download_before_install(
        self, tmp_path, monkeypatch
    ):
        """The direct URL path must use the same bounded reader as catalogs."""

        from typer.testing import CliRunner
        from specify_cli import app
        from specify_cli.extensions import _commands as extension_commands

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def reject_oversized(*_args, **_kwargs):
            raise ExtensionError("extension URL download exceeds maximum size")

        monkeypatch.setattr(
            extension_commands,
            "read_response_limited",
            reject_oversized,
            raising=False,
        )

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=True), \
             patch("specify_cli.extensions._commands._validate_safe_cache_dir", side_effect=_validate_safe_cache_dir_test_stand_in), \
             patch(
                 "specify_cli.authentication.http.open_url",
                 return_value=FakeResponse(_MINIMAL_ZIP_BYTES),
             ), \
             patch.object(ExtensionManager, "install_from_zip") as install:
            result = runner.invoke(
                app,
                [
                    "extension",
                    "add",
                    "my-ext",
                    "--from",
                    "https://example.com/ext.zip",
                ],
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert "exceeds maximum size" in result.output
        install.assert_not_called()

    def test_add_from_url_resolves_ghes_release_asset(self, tmp_path):
        """A GHES release-download URL resolves to /api/v3 with octet-stream Accept."""
        from types import SimpleNamespace
        from typer.testing import CliRunner
        from specify_cli import app
        import json

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        seen = {}

        def fake_open_url(url, timeout=10, extra_headers=None, redirect_validator=None):
            if "/releases/tags/" in url:
                body = json.dumps({
                    "assets": [{
                        "name": "ext.zip",
                        "url": "https://ghes.example/api/v3/repos/org/repo/releases/assets/42",
                    }]
                }).encode()
                return FakeResponse(body)
            seen["url"] = url
            seen["headers"] = extra_headers
            return FakeResponse(_MINIMAL_ZIP_BYTES)

        def fake_install(
            self_obj,
            zip_path,
            speckit_version,
            priority=10,
            force=False,
            *,
            archive_file=None,
        ):
            return SimpleNamespace(
                id="x", name="X", version="1.0.0", description="", warnings=[], commands=[], hooks=[]
            )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=True), \
             patch("specify_cli.extensions._commands._validate_safe_cache_dir", side_effect=_validate_safe_cache_dir_test_stand_in), \
             patch("specify_cli.authentication.http.github_provider_hosts", return_value=("ghes.example",)), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url), \
             patch("specify_cli.extensions._commands._safe_open_download_zip", side_effect=_open_test_download_zip), \
             patch.object(ExtensionManager, "install_from_zip", fake_install):
            result = runner.invoke(
                app,
                ["extension", "add", "x", "--from",
                 "https://ghes.example/org/repo/releases/download/v1.0/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert "/api/v3/repos/org/repo/releases/assets/" in seen["url"]
        assert seen["headers"] == {"Accept": "application/octet-stream"}

    @pytest.mark.parametrize(
        ("exc_type", "label"),
        [
            (ValidationError, "Validation Error"),
            (CompatibilityError, "Compatibility Error"),
            (ExtensionError, "Error"),
        ],
    )
    def test_add_exception_handlers_escape_markup(self, tmp_path, exc_type, label):
        """Extension install exceptions can include manifest-controlled values."""
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        ext_dir = tmp_path / "ext"
        ext_dir.mkdir()
        (ext_dir / "extension.yml").write_text("extension:\n  id: test\n", encoding="utf-8")

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(
                 ExtensionManager,
                 "install_from_directory",
                 side_effect=exc_type("bad [red]extension[/red]"),
             ):
            result = runner.invoke(
                app,
                ["extension", "add", str(ext_dir), "--dev"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert f"{label}:" in result.output
        assert "bad [red]extension[/red]" in result.output

    def test_add_from_url_uses_cache_tempfile_for_untrusted_extension_name(self, tmp_path):
        """The extension argument must not control the downloaded ZIP path."""
        from types import SimpleNamespace
        from typer.testing import CliRunner
        from specify_cli import app

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        downloads_dir = project_dir / ".specify" / "extensions" / ".cache" / "downloads"
        installed = {}

        def fake_install_from_zip(
            self_obj,
            zip_path,
            speckit_version,
            priority=10,
            force=False,
            *,
            archive_file=None,
        ):
            captured_path = Path(zip_path)
            installed["zip_path"] = captured_path
            installed["zip_bytes"] = archive_file.read()
            archive_file.seek(0)
            return SimpleNamespace(
                id="escape",
                name="Escape Test",
                version="1.0.0",
                description="Test extension",
                warnings=[],
                commands=[],
                hooks=[],
            )

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("typer.confirm", return_value=True), \
             patch("specify_cli.extensions._commands._validate_safe_cache_dir", side_effect=_validate_safe_cache_dir_test_stand_in), \
             patch("specify_cli.authentication.http.open_url", return_value=FakeResponse(_MINIMAL_ZIP_BYTES)), \
             patch("specify_cli.extensions._commands._safe_open_download_zip", side_effect=_open_test_download_zip), \
             patch.object(ExtensionManager, "install_from_zip", fake_install_from_zip):
            result = runner.invoke(
                app,
                ["extension", "add", "../outside", "--from", "https://example.com/ext.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0
        assert installed["zip_bytes"] == _MINIMAL_ZIP_BYTES
        assert installed["zip_path"].resolve().is_relative_to(downloads_dir.resolve())
        assert installed["zip_path"].name.startswith("extension-url-download-")
        assert not installed["zip_path"].exists()


class TestExtensionAddPriorityCLI:
    """Priority option coverage for ``extension add``."""

    def test_add_with_priority_option(self, extension_dir, project_dir):
        """Test extension add command with --priority option."""
        from specify_cli import app

        runner = CliRunner()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, [
                "extension", "add", str(extension_dir), "--dev", "--priority", "3"
            ])

        assert result.exit_code == 0, result.output

        manager = ExtensionManager(project_dir)
        metadata = manager.registry.get("test-ext")
        assert metadata["priority"] == 3


class TestClineExtensionHyphenation:
    """Test that Cline integration uses hyphenated commands and frontmatter references."""

    def _setup_mock_extension(self, tmp_path, ai_name):
        import json

        # 1. Setup mock project
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        init_options = project_dir / ".specify" / "init-options.json"
        init_options.write_text(json.dumps({"ai": ai_name}), encoding="utf-8")

        if ai_name == "cline":
            commands_dest_dir = project_dir / ".clinerules" / "workflows"
        else:
            commands_dest_dir = project_dir / ".agents" / "commands"
        commands_dest_dir.mkdir(parents=True, exist_ok=True)

        # 2. Setup mock extension directory
        ext_dir = tmp_path / "mock-ext"
        ext_dir.mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "mock-ext",
                "name": "Mock Extension",
                "version": "1.0.0",
                "description": f"Mock extension for {ai_name} tests",
                "author": "Tester",
                "repository": "https://github.com/test/mock-ext",
                "license": "MIT",
            },
            "requires": {
                "speckit_version": ">=0.1.0",
            },
            "provides": {
                "commands": [
                    {
                        "name": "speckit.mock-ext.hello",
                        "file": "commands/hello.md",
                        "description": "Test hello command",
                        "aliases": ["speckit.mock-ext.greet"]
                    }
                ]
            }
        }

        with open(ext_dir / "extension.yml", "w", encoding="utf-8") as f:
            yaml.dump(manifest_data, f)

        commands_dir = ext_dir / "commands"
        commands_dir.mkdir()

        # Command file with dotted speckit references in frontmatter and body
        cmd_content = """---
description: "Test hello command"
agent: speckit.tasks
handoffs:
  - agent: speckit.iterate.start
    message: "Hand off to start"
---

# Test Hello Command

Please refer to speckit.mock-ext.greet for instructions.
$ARGUMENTS
"""
        (commands_dir / "hello.md").write_text(cmd_content, encoding="utf-8")

        return project_dir, ext_dir, commands_dest_dir

    def test_cline_extension_hyphenation(self, tmp_path):
        from specify_cli import app
        from specify_cli.agents import CommandRegistrar

        project_dir, ext_dir, cline_workflows_dir = self._setup_mock_extension(tmp_path, "cline")

        # 3. Run specify extension add
        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["extension", "add", str(ext_dir), "--dev"], catch_exceptions=False
            )

        # Verify CLI printed hyphenated commands
        # Note: We assert that the primary command 'speckit-mock-ext-hello' is printed,
        # but we do not assert that the alias 'speckit-mock-ext-greet' is printed in the console
        # because manifest.commands only lists primary commands.
        assert "speckit-mock-ext-hello" in result.output
        assert "speckit.mock-ext.hello" not in result.output

        # Verify on-disk command names are hyphenated
        hello_file = cline_workflows_dir / "speckit-mock-ext-hello.md"
        greet_file = cline_workflows_dir / "speckit-mock-ext-greet.md"

        assert hello_file.exists()
        assert greet_file.exists()

        # Verify frontmatter in the generated files is recursively hyphenated
        hello_text = hello_file.read_text(encoding="utf-8")
        hello_fm, hello_body = CommandRegistrar.parse_frontmatter(hello_text)
        assert hello_fm["agent"] == "speckit-tasks"
        assert hello_fm["handoffs"][0]["agent"] == "speckit-iterate-start"

        # Verify body references are hyphenated for Cline
        assert "speckit-mock-ext-greet" in hello_body
        assert "speckit.mock-ext.greet" not in hello_body

    def test_non_cline_extension_no_hyphenation(self, tmp_path):
        from specify_cli import app
        from specify_cli.agents import CommandRegistrar

        project_dir, ext_dir, agents_commands_dir = self._setup_mock_extension(tmp_path, "amp")

        # 3. Run specify extension add
        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["extension", "add", str(ext_dir), "--dev"], catch_exceptions=False
            )

        # Verify CLI printed dotted commands
        # Note: We assert that the primary command 'speckit.mock-ext.hello' is printed,
        # but we do not assert that the alias 'speckit.mock-ext.greet' is printed in the console
        # because manifest.commands only lists primary commands.
        assert "speckit.mock-ext.hello" in result.output
        assert "speckit-mock-ext-hello" not in result.output

        # Verify on-disk command names are dotted
        hello_file = agents_commands_dir / "speckit.mock-ext.hello.md"
        greet_file = agents_commands_dir / "speckit.mock-ext.greet.md"

        assert hello_file.exists()
        assert greet_file.exists()

        # Verify frontmatter references are still dotted
        hello_text = hello_file.read_text(encoding="utf-8")
        hello_fm, hello_body = CommandRegistrar.parse_frontmatter(hello_text)
        assert hello_fm["agent"] == "speckit.tasks"
        assert hello_fm["handoffs"][0]["agent"] == "speckit.iterate.start"

        # Verify body references are still dotted for non-Cline
        assert "speckit.mock-ext.greet" in hello_body
        assert "speckit-mock-ext-greet" not in hello_body


class TestExtensionForceCLI:
    """CLI tests for `specify extension add --dev --force`."""

    def _create_minimal_extension(self, base_dir: str | Path, ext_id: str = "test-ext") -> Path:
        """Create a minimal extension directory with manifest."""

        ext_dir = Path(base_dir) / ext_id
        ext_dir.mkdir(parents=True, exist_ok=True)
        (ext_dir / "commands").mkdir()

        manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": ext_id,
                "name": "Test Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": f"speckit.{ext_id}.hello",
                        "file": "commands/hello.md",
                        "description": "Test command",
                    }
                ]
            },
        }

        (ext_dir / "extension.yml").write_text(yaml.dump(manifest))
        (ext_dir / "commands" / "hello.md").write_text(
            "---\ndescription: Test\n---\n\nHello $ARGUMENTS\n"
        )
        return ext_dir

    def test_add_dev_force_reinstall(self, tmp_path):
        """extension add --dev --force should reinstall without error."""
        from specify_cli import app

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        ext_src = self._create_minimal_extension(tmp_path)

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            # First install
            result1 = runner.invoke(
                app, ["extension", "add", str(ext_src), "--dev"], catch_exceptions=False
            )
            assert result1.exit_code == 0, strip_ansi(result1.output)
            assert "installed" in strip_ansi(result1.output)

            # Force reinstall
            result2 = runner.invoke(
                app, ["extension", "add", str(ext_src), "--dev", "--force"], catch_exceptions=False
            )
            assert result2.exit_code == 0, strip_ansi(result2.output)
            assert "installed" in strip_ansi(result2.output)


def test_forge_extension_install_listing_hyphenates_command_names(
    extension_dir, project_dir
):
    """The post-install 'Provided commands' listing must show hyphenated
    /speckit-<name> command names for a Forge project (Forge registers
    hyphenated names), mirroring the existing Cline handling."""
    import json
    import os



    init_options = project_dir / ".specify" / "init-options.json"
    init_options.write_text(json.dumps({"ai": "forge", "script": "sh"}))

    old_cwd = os.getcwd()
    try:
        os.chdir(project_dir)
        result = CliRunner().invoke(
            app, ["extension", "add", str(extension_dir), "--dev"]
        )
    finally:
        os.chdir(old_cwd)

    assert result.exit_code == 0, result.output
    # Forge registers hyphenated command names, so the summary must match.
    assert "speckit-test-ext-hello" in result.output
    assert "speckit.test-ext.hello" not in result.output
