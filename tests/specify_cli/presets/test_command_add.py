from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import ANY, MagicMock

import pytest
import yaml

from specify_cli._console import console
from specify_cli.presets import (
    PresetCatalog,
    PresetCompatibilityError,
    PresetError,
    PresetManager,
    PresetValidationError,
)
from specify_cli.presets._commands import _warn_unmet_extension_dependencies
from tests.conftest import strip_ansi


class TestPresetAddDependencyWarnings:
    """Test find_unmet_extension_dependencies (issue #4231)."""

    def test_version_warning_does_not_promise_update_satisfies_constraint(self):
        """Version remediation must handle constraints update cannot guarantee."""
        manager = MagicMock()
        manager.find_unmet_extension_dependencies.return_value = [
            {
                "id": "speckit-inventory",
                "reason": "version",
                "installed": "3.0.0",
                "version": "<2",
            }
        ]

        with console.capture() as capture:
            _warn_unmet_extension_dependencies(manager, MagicMock())

        output = " ".join(strip_ansi(capture.get()).split())
        assert "Needs: a release of speckit-inventory satisfying <2" in output
        assert "specify extension update" not in output

    def test_missing_and_stale_warnings_mention_discovery_only_catalogs(self):
        """`extension add <id>` is rejected for discovery-only entries, so say so."""
        manager = MagicMock()
        manager.find_unmet_extension_dependencies.return_value = [
            {
                "id": "speckit-inventory",
                "reason": "missing",
                "installed": None,
                "version": None,
            }
        ]

        with console.capture() as capture:
            _warn_unmet_extension_dependencies(manager, MagicMock())

        output = strip_ansi(capture.get())
        assert "discovery-only catalog" in output
        assert "--from <archive-url>" in output
        assert "Install with: specify extension add speckit-inventory" in output

    @pytest.mark.parametrize(
        "reason, extra",
        [
            ("missing", {"installed": None, "version": None}),
            ("stale", {"installed": "0.1.0", "version": None}),
            ("disabled", {"installed": "0.1.0", "version": None}),
            ("version", {"installed": "0.1.0", "version": ">=9.0.0"}),
        ],
    )
    def test_leading_hyphen_id_is_not_emitted_into_a_command(self, reason, extra):
        """A leading-hyphen id satisfies `^[a-z0-9-]+$` but breaks the command.

        Typer would read it as an option rather than the positional extension
        argument, so the advertised fix would fail. Every remedy substitutes
        the placeholder `_command_safe_id` returns. The id here is deliberately
        not a real flag, so a match cannot be confused with `--force` appearing
        legitimately in the stale remedy.
        """
        manager = MagicMock()
        manager.find_unmet_extension_dependencies.return_value = [
            {"id": "--not-a-real-flag", "reason": reason, **extra}
        ]

        with console.capture() as capture:
            _warn_unmet_extension_dependencies(manager, MagicMock())

        output = " ".join(strip_ansi(capture.get()).split())
        # Isolate the remedy: the description line legitimately shows the raw
        # id, escaped for display; only the copyable command must not carry it.
        label = next(
            lbl
            for lbl in ("Install with:", "Reinstall with:", "Enable with:", "Needs:")
            if lbl in output
        )
        remedy = output.split(label, 1)[1].split("The preset is installed.")[0]
        assert "--not-a-real-flag" not in remedy
        assert "<extension-id>" in remedy

    def test_version_only_warning_omits_the_discovery_only_note(self):
        """The note is about installing by id, which a version mismatch does not do."""
        manager = MagicMock()
        manager.find_unmet_extension_dependencies.return_value = [
            {
                "id": "speckit-inventory",
                "reason": "version",
                "installed": "0.1.0",
                "version": ">=9.0.0",
            }
        ]

        with console.capture() as capture:
            _warn_unmet_extension_dependencies(manager, MagicMock())

        assert "discovery-only" not in strip_ansi(capture.get())

    def test_corrupt_warning_suggests_forced_reinstall(self):
        """The corrupt remedy must use --force, since the id is still registered."""
        manager = MagicMock()
        manager.find_unmet_extension_dependencies.return_value = [
            {
                "id": "speckit-inventory",
                "reason": "corrupt",
                "installed": None,
                "version": None,
            }
        ]

        with console.capture() as capture:
            _warn_unmet_extension_dependencies(manager, MagicMock())

        output = strip_ansi(capture.get())
        assert "unreadable registry entry" in output
        assert (
            "Reinstall with: specify extension add speckit-inventory --force" in output
        )

    def test_version_only_footer_does_not_claim_the_feature_is_inert(self):
        """A version mismatch still invokes the extension, so wording differs."""
        manager = MagicMock()
        manager.find_unmet_extension_dependencies.return_value = [
            {
                "id": "speckit-inventory",
                "reason": "version",
                "installed": "0.1.0",
                "version": ">=9.0.0",
            }
        ]

        with console.capture() as capture:
            _warn_unmet_extension_dependencies(manager, MagicMock())

        output = " ".join(strip_ansi(capture.get()).split())
        assert "may not behave as the preset expects" in output
        assert "does nothing" not in output
        assert "safe to use" not in output

    def test_unavailable_footer_states_the_feature_is_inert(self):
        """An unavailable extension genuinely contributes nothing."""
        manager = MagicMock()
        manager.find_unmet_extension_dependencies.return_value = [
            {
                "id": "speckit-inventory",
                "reason": "missing",
                "installed": None,
                "version": None,
            }
        ]

        with console.capture() as capture:
            _warn_unmet_extension_dependencies(manager, MagicMock())

        output = " ".join(strip_ansi(capture.get()).split())
        assert "does nothing" in output
        assert "may not behave as the preset expects" not in output

    def test_stale_warning_suggests_a_forced_reinstall(self):
        """The stale remedy must restore the files, not re-add a registered id."""
        manager = MagicMock()
        manager.find_unmet_extension_dependencies.return_value = [
            {
                "id": "speckit-inventory",
                "reason": "stale",
                "installed": "0.1.0",
                "version": None,
            }
        ]

        with console.capture() as capture:
            _warn_unmet_extension_dependencies(manager, MagicMock())

        output = strip_ansi(capture.get())
        assert "its files are missing" in output
        assert "specify extension add speckit-inventory --force" in output


class TestPresetAdd:
    """Tests for _locate_bundled_preset discovery function."""

    def test_bundled_preset_add_via_cli(self, project_dir):
        """Test that 'specify preset add lean' installs the bundled preset."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch("specify_cli.get_speckit_version", return_value="0.6.0"),
        ):
            result = runner.invoke(app, ["preset", "add", "lean"])

        assert result.exit_code == 0, result.output
        assert "Lean Workflow" in result.output
        assert "installed" in result.output.lower()

    def test_preset_add_catalog_forwards_catalog_name(self, project_dir, monkeypatch):
        """Catalog installs pass resolved provenance into the manager boundary."""
        from specify_cli.presets._commands import preset_add

        captured = {}

        def fake_install_from_zip(
            self, _archive, _version, priority=10, *, catalog_name=None
        ):
            captured.update(priority=priority, catalog_name=catalog_name)
            return SimpleNamespace(name="Catalog Preset", version="1.0.0")

        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "1.0.0")
        monkeypatch.setattr(
            PresetCatalog,
            "get_pack_info",
            lambda _self, _id: {
                "name": "Catalog Preset",
                "_install_allowed": True,
                "_catalog_name": "preset-catalog",
            },
        )
        archive = project_dir / "preset.zip"
        archive.write_bytes(b"archive")
        monkeypatch.setattr(PresetCatalog, "download_pack", lambda _self, _id: archive)
        monkeypatch.setattr(PresetManager, "install_from_zip", fake_install_from_zip)

        preset_add(preset_id="catalog-preset", from_url=None, dev=None, priority=7)

        assert captured == {"priority": 7, "catalog_name": "preset-catalog"}

    def test_preset_add_uses_legacy_dependency_warning_seam(
        self, project_dir, pack_dir, monkeypatch
    ):
        """The extracted handler must honor patches at the legacy helper path."""
        from specify_cli.presets import _commands as preset_commands

        manifest = SimpleNamespace(name="Test Preset", version="1.0.0")
        warning = MagicMock()
        monkeypatch.setattr(
            "specify_cli._require_specify_project", lambda: project_dir
        )
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "1.0.0")
        monkeypatch.setattr(
            PresetManager,
            "install_from_directory",
            lambda _self, _path, _version, _priority: manifest,
        )
        monkeypatch.setattr(
            preset_commands,
            "_warn_unmet_extension_dependencies",
            warning,
        )

        preset_commands.preset_add(
            preset_id=None,
            from_url=None,
            dev=str(pack_dir),
            priority=10,
        )

        warning.assert_called_once_with(ANY, manifest)

    def test_preset_add_from_url_rejects_insecure_redirect(
        self, project_dir, monkeypatch
    ):
        """URL installs reject redirects from HTTPS to non-loopback HTTP."""
        import typer

        from specify_cli.presets._commands import preset_add

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return "http://example.com/preset.zip"

        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.6.0")

        def fake_open_url(
            url, timeout=None, extra_headers=None, redirect_validator=None
        ):
            assert redirect_validator is not None
            redirect_validator(url, "http://example.com/preset.zip")
            return FakeResponse(b"zip")

        monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)

        installed = False

        def fake_install_from_zip(self, zip_path, speckit_version, priority=10):
            nonlocal installed
            installed = True

        monkeypatch.setattr(PresetManager, "install_from_zip", fake_install_from_zip)

        with pytest.raises(typer.Exit) as exc_info:
            preset_add(
                preset_id=None,
                from_url="https://example.com/preset.zip",
                dev=None,
                priority=10,
            )

        assert exc_info.value.exit_code == 1
        assert installed is False

    def test_preset_add_from_url_rejects_hostless_https_url(self, project_dir):
        """URL installs reject HTTPS URLs without a hostname before downloading."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch("specify_cli.authentication.http.open_url") as open_url,
        ):
            result = runner.invoke(
                app, ["preset", "add", "--from", "https:///preset.zip"]
            )

        assert result.exit_code == 1
        output = strip_ansi(result.output)
        assert "URL must use HTTPS with a hostname" in output
        assert "got https://" not in output
        open_url.assert_not_called()

    def test_preset_add_from_malformed_ipv6_url_exits_cleanly(self, project_dir):
        """A malformed IPv6 URL must produce a clean error, not a ValueError traceback."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch("specify_cli.authentication.http.open_url") as open_url,
        ):
            result = runner.invoke(
                app,
                ["preset", "add", "--from", "https://[::1/preset.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert result.exception is None or isinstance(result.exception, SystemExit)
        output = strip_ansi(result.output)
        assert "Invalid URL" in output
        open_url.assert_not_called()

    def test_preset_add_from_bracketed_non_ip_url_exits_cleanly(self, project_dir):
        """A bracketed-but-invalid IPv6 host in --from must exit cleanly.

        "https://[not-an-ip]/preset.zip" is a malformed authority that raises
        ValueError during URL validation; the try/except guard around parsing
        and the .hostname read must turn that into a clean "Invalid URL" message.
        """
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch("specify_cli.authentication.http.open_url") as open_url,
        ):
            result = runner.invoke(
                app,
                ["preset", "add", "--from", "https://[not-an-ip]/preset.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert result.exception is None or isinstance(result.exception, SystemExit)
        output = strip_ansi(result.output)
        assert "Invalid URL" in output
        open_url.assert_not_called()

    def test_preset_add_from_url_out_of_range_port_exits_cleanly(self, project_dir):
        """An out-of-range port raises ValueError lazily on .port access.

        The up-front guard reads ``_parsed.port`` (urllib validates the port
        range/syntax there) inside its try/except, so "https://example.com:99999/
        preset.zip" must produce a clean "Invalid URL" message rather than
        leaking a raw ValueError traceback past the CLI.
        """
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch("specify_cli.authentication.http.open_url") as open_url,
        ):
            result = runner.invoke(
                app,
                ["preset", "add", "--from", "https://example.com:99999/preset.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert "Invalid URL" in strip_ansi(result.output)
        open_url.assert_not_called()

    def test_preset_add_bracketed_host_download_url_exits_cleanly(self, project_dir):
        """A catalog download_url with a bracketed non-IP host must render cleanly.

        ``download_pack`` raises ``PresetError`` whose message embeds the raw URL
        (e.g. ``https://[not-an-ip]/x``). The ``preset_add`` handler must escape
        that message before printing so Rich does not interpret ``[not-an-ip]``
        as a markup tag and crash while rendering the error.
        """
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        bad_url = "https://[not-an-ip]/x"
        catalog_data = {
            "test-pack": {
                "name": "Test Pack",
                "version": "1.0.0",
                "download_url": bad_url,
            }
        }

        runner = CliRunner()
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(PresetCatalog, "_get_merged_packs", return_value=catalog_data),
        ):
            result = runner.invoke(
                app,
                ["preset", "add", "test-pack"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert result.exception is None or isinstance(result.exception, SystemExit)
        output = strip_ansi(result.output)
        assert "Error:" in output
        # The malformed URL surfaces verbatim rather than crashing the renderer.
        assert bad_url in output

    @pytest.mark.parametrize(
        ("exc_type", "label"),
        [
            (PresetCompatibilityError, "Compatibility Error"),
            (PresetValidationError, "Validation Error"),
            (PresetError, "Error"),
        ],
    )
    def test_preset_add_exception_handlers_escape_markup(
        self, project_dir, exc_type, label
    ):
        """Preset install exceptions can include catalog-controlled values.

        The message must be escaped so Rich does not treat bracketed content as
        markup and raise while rendering the error.
        """
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        dev_dir = project_dir / "dev-pack"
        dev_dir.mkdir()

        runner = CliRunner()
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch.object(
                PresetManager,
                "install_from_directory",
                side_effect=exc_type("bad [red]preset[/red]"),
            ),
        ):
            result = runner.invoke(
                app,
                ["preset", "add", "--dev", str(dev_dir)],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert result.exception is None or isinstance(result.exception, SystemExit)
        assert f"{label}:" in result.output
        assert "bad [red]preset[/red]" in result.output

    def test_preset_add_from_url_redirect_error_describes_disallowed_url(
        self, project_dir, monkeypatch, capsys
    ):
        """Redirect rejection message covers hostless HTTPS, not only non-HTTPS URLs."""
        import typer

        from specify_cli.presets._commands import preset_add

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return "https:///preset.zip"

        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.6.0")
        monkeypatch.setattr(
            "specify_cli.authentication.http.open_url",
            lambda url, timeout=None, extra_headers=None, redirect_validator=None: (
                FakeResponse(b"zip")
            ),
        )
        monkeypatch.setattr(
            PresetManager, "install_from_zip", lambda *args, **kwargs: None
        )

        with pytest.raises(typer.Exit) as exc_info:
            preset_add(
                preset_id=None,
                from_url="https://example.com/preset.zip",
                dev=None,
                priority=10,
            )

        assert exc_info.value.exit_code == 1
        output = strip_ansi(capsys.readouterr().out)
        assert "redirected to a disallowed URL" in output
        assert "must use HTTPS with a hostname" in output

    def test_preset_add_from_url_reads_in_bounded_chunks(
        self, project_dir, monkeypatch
    ):
        """URL installs read the response in bounded chunks."""
        from specify_cli.presets._commands import preset_add

        class FakeResponse(io.BytesIO):
            def __init__(self, data):
                super().__init__(data)
                self.read_sizes = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return "https://example.com/preset.zip"

            def read(self, size=-1):
                assert size not in (-1, None)
                self.read_sizes.append(size)
                return super().read(size)

        response = FakeResponse(b"PK\x05\x06" + b"\x00" * 18)
        installed = {}

        def fake_install_from_zip(self, zip_path, speckit_version, priority=10):
            installed["zip_bytes"] = Path(zip_path).read_bytes()
            installed["speckit_version"] = speckit_version
            installed["priority"] = priority
            return SimpleNamespace(name="Test Preset", version="1.0.0")

        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.6.0")
        monkeypatch.setattr(
            "specify_cli.authentication.http.open_url",
            lambda url, timeout=None, extra_headers=None, redirect_validator=None: (
                response
            ),
        )
        monkeypatch.setattr(PresetManager, "install_from_zip", fake_install_from_zip)

        preset_add(
            preset_id=None,
            from_url="https://example.com/preset.zip",
            dev=None,
            priority=7,
        )

        assert response.read_sizes
        assert installed == {
            "zip_bytes": b"PK\x05\x06" + b"\x00" * 18,
            "speckit_version": "0.6.0",
            "priority": 7,
        }

    def test_preset_add_from_url_rejects_oversized_download(
        self, project_dir, monkeypatch, capsys
    ):
        """An oversized direct download fails before preset installation."""
        import typer

        from specify_cli._download_security import (
            read_response_limited as real_read_response_limited,
        )
        from specify_cli.presets import _commands as preset_commands

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return "https://example.com/preset.zip"

        def read_with_tiny_limit(response, **kwargs):
            kwargs.pop("max_bytes", None)
            return real_read_response_limited(response, max_bytes=4, **kwargs)

        installed = False

        def fake_install_from_zip(*_args, **_kwargs):
            nonlocal installed
            installed = True

        monkeypatch.setattr(
            preset_commands,
            "read_response_limited",
            read_with_tiny_limit,
        )
        monkeypatch.setattr(
            "specify_cli._require_specify_project",
            lambda: project_dir,
        )
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.6.0")
        monkeypatch.setattr(
            "specify_cli.authentication.http.open_url",
            lambda *_args, **_kwargs: FakeResponse(b"12345"),
        )
        monkeypatch.setattr(PresetManager, "install_from_zip", fake_install_from_zip)

        with pytest.raises(typer.Exit) as exc_info:
            preset_commands.preset_add(
                preset_id=None,
                from_url="https://example.com/preset.zip",
                dev=None,
                priority=10,
            )

        assert exc_info.value.exit_code == 1
        output = " ".join(strip_ansi(capsys.readouterr().out).split())
        assert "exceeds maximum size of 4 bytes" in output
        assert installed is False

    def test_bundled_preset_missing_locally_cli_error(self, project_dir):
        """CLI shows clear error when bundled preset cannot be found locally."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()
        # Patch _locate_bundled_preset to return None (simulating missing files)
        # and mock the catalog to return a bundled entry for "lean"
        fake_pack_info = {
            "id": "lean",
            "name": "Lean Workflow",
            "version": "1.0.0",
            "bundled": True,
            "_install_allowed": True,
        }
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch("specify_cli._locate_bundled_preset", return_value=None),
            patch("specify_cli.presets.PresetCatalog") as MockCatalog,
        ):
            MockCatalog.return_value.get_pack_info.return_value = fake_pack_info
            result = runner.invoke(app, ["preset", "add", "lean"])

        # Should fail with a helpful error explaining this is a bundled preset
        # and suggesting how to recover.
        assert result.exit_code == 1
        output = strip_ansi(result.output).lower()
        assert "bundled" in output, result.output
        assert "reinstall" in output, result.output


class TestPresetAddFromUrlResolution:
    """CLI-level tests for preset add --from <url> GitHub release resolution."""

    def test_preset_add_from_github_release_url_resolves_and_downloads(
        self, project_dir
    ):
        """'preset add --from <github-release-url>' resolves to API asset URL."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        manifest_content = yaml.dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": "my-preset",
                    "name": "My Preset",
                    "version": "1.0.0",
                    "description": "Test preset",
                    "author": "Test",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "templates": [
                        {
                            "type": "template",
                            "name": "t",
                            "file": "templates/t.md",
                            "description": "t",
                        }
                    ]
                },
            }
        )
        zip_buf = __import__("io").BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", manifest_content)
        zip_bytes = zip_buf.getvalue()

        captured_urls = []

        def fake_open_url(
            url, timeout=None, extra_headers=None, redirect_validator=None
        ):
            captured_urls.append((url, extra_headers))
            if "releases/tags/" in url:
                return io.BytesIO(
                    json.dumps(
                        {
                            "assets": [
                                {
                                    "name": "preset.zip",
                                    "url": "https://api.github.com/repos/org/repo/releases/assets/42",
                                }
                            ]
                        }
                    ).encode()
                )
            return io.BytesIO(zip_bytes)

        runner = CliRunner()
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch("specify_cli.get_speckit_version", return_value="1.0.0"),
            patch(
                "specify_cli.authentication.http.open_url", side_effect=fake_open_url
            ),
        ):
            result = runner.invoke(
                app,
                [
                    "preset",
                    "add",
                    "--from",
                    "https://github.com/org/repo/releases/download/v1.0/preset.zip",
                ],
            )

        assert result.exit_code == 0, result.output
        assert "My Preset" in result.output
        # First call should resolve the release tag
        assert any("releases/tags/v1.0" in url for url, _ in captured_urls)
        # Second call should download from the resolved asset URL with octet-stream
        asset_calls = [
            (url, h) for url, h in captured_urls if "releases/assets/" in url
        ]
        assert len(asset_calls) >= 1
        assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    def test_preset_add_from_direct_api_asset_url_passes_through(self, project_dir):
        """'preset add --from <api-asset-url>' uses URL directly with octet-stream."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        manifest_content = yaml.dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": "my-preset",
                    "name": "My Preset",
                    "version": "1.0.0",
                    "description": "Test preset",
                    "author": "Test",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "templates": [
                        {
                            "type": "template",
                            "name": "t",
                            "file": "templates/t.md",
                            "description": "t",
                        }
                    ]
                },
            }
        )
        zip_buf = __import__("io").BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", manifest_content)
        zip_bytes = zip_buf.getvalue()

        captured_urls = []

        def fake_open_url(
            url, timeout=None, extra_headers=None, redirect_validator=None
        ):
            captured_urls.append((url, extra_headers))
            return io.BytesIO(zip_bytes)

        runner = CliRunner()
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch("specify_cli.get_speckit_version", return_value="1.0.0"),
            patch(
                "specify_cli.authentication.http.open_url", side_effect=fake_open_url
            ),
        ):
            result = runner.invoke(
                app,
                [
                    "preset",
                    "add",
                    "--from",
                    "https://api.github.com/repos/org/repo/releases/assets/42",
                ],
            )

        assert result.exit_code == 0, result.output
        # Should go directly to the asset URL with Accept header
        assert len(captured_urls) == 1
        assert (
            captured_urls[0][0]
            == "https://api.github.com/repos/org/repo/releases/assets/42"
        )
        assert captured_urls[0][1] == {"Accept": "application/octet-stream"}

    def test_preset_add_from_ghes_release_url_resolves_via_api_v3(
        self, project_dir, monkeypatch
    ):
        """'preset add --from <ghes-release-url>' resolves via GHES /api/v3 endpoint."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.authentication import http as _auth_http
        from specify_cli.authentication.config import AuthConfigEntry

        monkeypatch.setattr(
            _auth_http,
            "_config_override",
            [
                AuthConfigEntry(
                    hosts=("ghes.example",), provider="github", auth="bearer", token="t"
                ),
            ],
        )

        manifest_content = yaml.dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": "my-preset",
                    "name": "My Preset",
                    "version": "1.0.0",
                    "description": "Test preset",
                    "author": "Test",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "templates": [
                        {
                            "type": "template",
                            "name": "t",
                            "file": "templates/t.md",
                            "description": "t",
                        }
                    ]
                },
            }
        )
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", manifest_content)
        zip_bytes = zip_buf.getvalue()

        captured_urls = []

        def fake_open_url(
            url, timeout=None, extra_headers=None, redirect_validator=None
        ):
            captured_urls.append((url, extra_headers))
            if "releases/tags/" in url:
                return io.BytesIO(
                    json.dumps(
                        {
                            "assets": [
                                {
                                    "name": "preset.zip",
                                    "url": "https://ghes.example/api/v3/repos/org/repo/releases/assets/42",
                                }
                            ]
                        }
                    ).encode()
                )
            return io.BytesIO(zip_bytes)

        runner = CliRunner()
        with (
            patch.object(Path, "cwd", return_value=project_dir),
            patch("specify_cli.get_speckit_version", return_value="1.0.0"),
            patch(
                "specify_cli.authentication.http.open_url", side_effect=fake_open_url
            ),
        ):
            result = runner.invoke(
                app,
                [
                    "preset",
                    "add",
                    "--from",
                    "https://ghes.example/org/repo/releases/download/v1.0/preset.zip",
                ],
            )

        assert result.exit_code == 0, result.output
        # The tag-lookup call must use the GHES /api/v3 endpoint
        assert any(
            "ghes.example/api/v3/repos/org/repo/releases/tags/v1.0" in url
            for url, _ in captured_urls
        )
        # The asset download call must carry Accept: application/octet-stream
        asset_calls = [
            (url, h) for url, h in captured_urls if "releases/assets/" in url
        ]
        assert len(asset_calls) >= 1
        assert asset_calls[0][1] == {"Accept": "application/octet-stream"}
