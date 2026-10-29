"""Tests for OpencodeIntegration."""

import json
import os
import stat
import warnings
from unittest.mock import patch

import pytest

from specify_cli.agents import CommandRegistrar
from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_markdown import MarkdownIntegrationTests

_OPT_IN = {"configure_ignore_file": True}


class TestOpencodeIntegration(MarkdownIntegrationTests):
    KEY = "opencode"
    FOLDER = ".opencode/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".opencode/commands"

    def test_multi_install_safe(self):
        assert get_integration(self.KEY).multi_install_safe is True

    def test_build_exec_args_uses_run_command_dispatch(self):
        integration = get_integration(self.KEY)

        args = integration.build_exec_args(
            "/speckit.specify build a login page",
            output_json=False,
        )

        assert args == [
            "opencode",
            "run",
            "--command",
            "speckit.specify",
            "build a login page",
        ]
        assert "-p" not in args
        assert "--output-format" not in args

    def test_build_exec_args_maps_model_and_json_flags(self):
        integration = get_integration(self.KEY)

        args = integration.build_exec_args(
            "/speckit.plan add OAuth",
            model="anthropic/claude-sonnet-4",
            output_json=True,
        )

        assert args == [
            "opencode",
            "run",
            "--command",
            "speckit.plan",
            "-m",
            "anthropic/claude-sonnet-4",
            "--format",
            "json",
            "add OAuth",
        ]

    def test_build_exec_args_keeps_plain_prompt_dispatch(self):
        integration = get_integration(self.KEY)

        args = integration.build_exec_args("explain this repository", output_json=False)

        assert args == ["opencode", "run", "explain this repository"]

    def test_registrar_config_has_legacy_dir(self):
        integration = get_integration(self.KEY)
        assert integration.registrar_config["legacy_dir"] == ".opencode/command"

    def test_legacy_dir_extension_registration(self, tmp_path):
        """Extensions register in legacy .opencode/command/ with a warning."""
        # Seed a legacy project with only .opencode/command/
        legacy_dir = tmp_path / ".opencode" / "command"
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "speckit.specify.md").write_text("# existing", encoding="utf-8")

        # Create a source command file for the registrar
        src_dir = tmp_path / "_ext_src"
        src_dir.mkdir()
        (src_dir / "myext.md").write_text(
            "---\ndescription: test\n---\n# ext command", encoding="utf-8",
        )

        registrar = CommandRegistrar()
        commands = [{"name": "speckit.myext", "file": "myext.md"}]

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = registrar.register_commands_for_all_agents(
                commands, "test-ext", src_dir, tmp_path,
            )

        # Should have registered in the legacy directory
        assert "opencode" in results
        assert (legacy_dir / "speckit.myext.md").exists()
        # Canonical directory should NOT have been created
        assert not (tmp_path / ".opencode" / "commands").exists()
        # Should have emitted a deprecation warning
        opencode_warnings = [
            w for w in caught
            if "legacy" in str(w.message) and "opencode" in str(w.message)
        ]
        assert len(opencode_warnings) == 1, (
            f"Expected exactly 1 legacy-dir warning, got {len(opencode_warnings)}"
        )
        assert "specify integration upgrade" in str(opencode_warnings[0].message)

    def test_legacy_dir_unregister(self, tmp_path):
        """Unregister finds commands in legacy .opencode/command/ dir."""
        legacy_dir = tmp_path / ".opencode" / "command"
        legacy_dir.mkdir(parents=True)
        cmd_file = legacy_dir / "speckit.myext.md"
        cmd_file.write_text("# ext command", encoding="utf-8")

        registrar = CommandRegistrar()

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            registrar.unregister_commands(
                {"opencode": ["speckit.myext"]}, tmp_path,
            )

        assert not cmd_file.exists()

    def test_unregister_cleans_legacy_when_both_dirs_exist(self, tmp_path):
        """Unregister removes files from legacy dir even when canonical exists."""
        # Set up both canonical and legacy dirs
        canonical_dir = tmp_path / ".opencode" / "commands"
        canonical_dir.mkdir(parents=True)
        legacy_dir = tmp_path / ".opencode" / "command"
        legacy_dir.mkdir(parents=True)

        # Place a command file in the legacy dir (orphaned after upgrade)
        legacy_cmd = legacy_dir / "speckit.myext.md"
        legacy_cmd.write_text("# orphaned ext command", encoding="utf-8")
        # Place the same command in the canonical dir (current)
        canonical_cmd = canonical_dir / "speckit.myext.md"
        canonical_cmd.write_text("# ext command", encoding="utf-8")

        registrar = CommandRegistrar()

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            registrar.unregister_commands(
                {"opencode": ["speckit.myext"]}, tmp_path,
            )

        # Both files should be removed
        assert not canonical_cmd.exists(), (
            "Command file in canonical dir should be removed"
        )
        assert not legacy_cmd.exists(), (
            "Orphaned command file in legacy dir should also be removed"
        )

    def test_canonical_dir_preferred_over_legacy(self, tmp_path):
        """When both dirs exist, canonical .opencode/commands/ is used."""
        legacy_dir = tmp_path / ".opencode" / "command"
        legacy_dir.mkdir(parents=True)
        canonical_dir = tmp_path / ".opencode" / "commands"
        canonical_dir.mkdir(parents=True)
        (canonical_dir / "speckit.specify.md").write_text("# cmd", encoding="utf-8")

        # Create a source command file for the registrar
        src_dir = tmp_path / "_ext_src"
        src_dir.mkdir()
        (src_dir / "myext.md").write_text(
            "---\ndescription: test\n---\n# ext command", encoding="utf-8",
        )

        registrar = CommandRegistrar()
        commands = [{"name": "speckit.myext", "file": "myext.md"}]

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = registrar.register_commands_for_all_agents(
                commands, "test-ext", src_dir, tmp_path,
            )

        # Should register in canonical dir, not legacy
        assert "opencode" in results
        assert (canonical_dir / "speckit.myext.md").exists()
        assert not (legacy_dir / "speckit.myext.md").exists()
        # No legacy warning when canonical dir exists
        opencode_warnings = [
            w for w in caught
            if "legacy" in str(w.message) and "opencode" in str(w.message)
        ]
        assert len(opencode_warnings) == 0

    def test_setup_writes_to_canonical_dir(self, tmp_path):
        """New installs always write to .opencode/commands/ (plural)."""
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest)

        canonical = tmp_path / ".opencode" / "commands"
        legacy = tmp_path / ".opencode" / "command"
        assert canonical.is_dir()
        assert not legacy.exists()
        assert any(canonical.glob("speckit.*.md"))

    def test_configure_ignore_file_opt_in_records_partial_and_renders_commands(self, tmp_path):
        """Opt-in appends both rules, renders commands, and records partial ownership."""
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        created = integration.setup(tmp_path, manifest, parsed_options=_OPT_IN)

        ignore = tmp_path / ".ignore"
        assert ignore.read_bytes() == b"!.specify/\n!.specify/**\n"
        assert any(path.resolve() == ignore.resolve() for path in created)
        assert manifest.ownership_modes[".ignore"] == "partial"
        assert ".ignore" in manifest.files

        canonical = tmp_path / ".opencode" / "commands"
        command_files = list(canonical.glob("speckit.*.md"))
        assert command_files
        plan = canonical / integration.command_filename("plan")
        text = plan.read_text(encoding="utf-8")
        assert "{SCRIPT}" not in text
        assert "__AGENT__" not in text

    def test_configure_ignore_file_preserves_prefix_and_repeats_cleanly(self, tmp_path):
        """Existing bytes stay a prefix; missing rules are appended once."""
        integration = get_integration(self.KEY)
        cases = {
            "empty": (b"", b"!.specify/\n!.specify/**\n"),
            "lf-non-ascii-no-final-newline": (
                "café keep".encode(),
                "café keep\n!.specify/\n!.specify/**\n".encode(),
            ),
            "crlf-non-ascii-no-final-newline": (
                "café\r\nkeep".encode(),
                "café\r\nkeep\r\n!.specify/\r\n!.specify/**\r\n".encode(),
            ),
            "dir-rule-only": (b"!.specify/\n", b"!.specify/\n!.specify/**\n"),
            "contents-rule-only": (b"!.specify/**\n", b"!.specify/**\n!.specify/\n"),
            "both-rules": (
                "café\r\n!.specify/\r\n!.specify/**\r\n".encode(),
                "café\r\n!.specify/\r\n!.specify/**\r\n".encode(),
            ),
            "broader-exclusions": (
                b"*\n.*\n.specify/**\n",
                b"*\n.*\n.specify/**\n!.specify/\n!.specify/**\n",
            ),
            "bare-cr-comment": (
                b"# user comment\r!.specify/\n!.specify/**\n",
                b"# user comment\r!.specify/\n!.specify/**\n!.specify/\n",
            ),
            "unicode-separator-comment": (
                "!.specify/\n!.specify/**\n# note\u2028.specify/memory\n".encode(),
                "!.specify/\n!.specify/**\n# note\u2028.specify/memory\n".encode(),
            ),
        }
        for name, (original, expected) in cases.items():
            root = tmp_path / name
            root.mkdir()
            ignore = root / ".ignore"
            ignore.write_bytes(original)
            ignore.chmod(0o640)
            before_mode = stat.S_IMODE(ignore.stat().st_mode)
            manifest = IntegrationManifest(self.KEY, root)
            integration.setup(root, manifest, parsed_options=_OPT_IN)
            assert ignore.read_bytes() == expected
            assert ignore.read_bytes().startswith(original)
            assert stat.S_IMODE(ignore.stat().st_mode) == before_mode
            assert manifest.ownership_modes[".ignore"] == "partial"
            integration.setup(
                root, IntegrationManifest(self.KEY, root), parsed_options=_OPT_IN
            )
            assert ignore.read_bytes() == expected
            assert stat.S_IMODE(ignore.stat().st_mode) == before_mode

    def test_configure_ignore_file_rejects_non_utf8_and_overrides(self, tmp_path):
        integration = get_integration(self.KEY)
        for index, (original, match) in enumerate((
            (b"# caf\xe9\n", "Convert it to UTF-8"),
            (b"!.specify/\n!.specify/**\n.specify/**\n", "later exclusion"),
            (b"!.specify/\n!.specify/**\n/.specify/templates/**\n", "later exclusion"),
            (b"!.specify/\n!.specify/**\n.specify/memory/custom.md\n", "custom.md"),
            (b"!.specify/\n!.specify/**\n.specify/templates/plan-template.md\n", "plan-template.md"),
            (b"!.specify/\n!.specify/**\n.specify/memory\n!.specify/memory/*.md\n", "constitution.md"),
            (b"!.specify/**\n*.md\n", "constitution.md"),
            (
                b"!.specify/\n!.specify/**\n.specify/memory/constitution.md\n!.specify/\n",
                "constitution.md",
            ),
        )):
            root = tmp_path / str(index)
            (root / ".specify" / "memory").mkdir(parents=True)
            (root / ".specify" / "memory" / "custom.md").write_text("x\n")
            (root / ".ignore").write_bytes(original)
            with pytest.raises(ValueError, match=match):
                integration.setup(root, IntegrationManifest(self.KEY, root), parsed_options=_OPT_IN)
            assert (root / ".ignore").read_bytes() == original and not (root / ".opencode").exists()
        restored = b"!.specify/\n!.specify/**\n.specify/**\n!.specify/**\n"
        (tmp_path / ".ignore").write_bytes(restored)
        integration.setup(tmp_path, IntegrationManifest(self.KEY, tmp_path), parsed_options=_OPT_IN)
        assert (tmp_path / ".ignore").read_bytes() == restored
        kept = b"!.specify/\n!.specify/**\n.specify/memory\n!.specify/memory/\n!.specify/memory/**\n"
        reinclude = tmp_path / "reinclude"
        reinclude.mkdir()
        (reinclude / ".ignore").write_bytes(kept)
        integration.setup(reinclude, IntegrationManifest(self.KEY, reinclude), parsed_options=_OPT_IN)
        assert (reinclude / ".ignore").read_bytes() == kept

    def test_without_flag_and_other_integrations_leave_ignore_untouched(self, tmp_path):
        plain = tmp_path / "plain"
        plain.mkdir()
        get_integration(self.KEY).setup(plain, IntegrationManifest(self.KEY, plain))
        assert not (plain / ".ignore").exists()

        other_root = tmp_path / "other"
        other_root.mkdir()
        (other_root / ".ignore").write_bytes(b"user\n")
        get_integration("gemini").setup(
            other_root, IntegrationManifest("gemini", other_root)
        )
        assert (other_root / ".ignore").read_bytes() == b"user\n"

    def test_flag_parses_with_events_and_persists_across_upgrade(self, tmp_path):
        from specify_cli.integrations._helpers import _parse_integration_options
        from tests.specify_cli.integrations._helpers import _init_project, _run_in_project

        integration = get_integration(self.KEY)
        parsed = _parse_integration_options(
            integration, "--configure-ignore-file --events false"
        )
        assert parsed == {"configure_ignore_file": True, "events": "false"}
        names = [option.name for option in integration.options()]
        assert "--events" in names
        assert "--configure-ignore-file" in names

        project = _init_project(
            tmp_path, "opencode", "--configure-ignore-file --events false"
        )
        ignore = project / ".ignore"
        state = json.loads(
            (project / ".specify" / "integration.json").read_text(encoding="utf-8")
        )
        settings = state["integration_settings"]["opencode"]
        assert settings["parsed_options"] == {
            "configure_ignore_file": True,
            "events": "false",
        }

        ignore.write_bytes(b"keep me\n")
        result = _run_in_project(project, ["integration", "upgrade", "opencode", "--force"])
        assert result.exit_code == 0, result.output
        assert ignore.read_bytes() == b"keep me\n!.specify/\n!.specify/**\n"
        result = _run_in_project(project, ["integration", "upgrade", "opencode", "--force"])
        assert result.exit_code == 0, result.output
        assert ignore.read_bytes() == b"keep me\n!.specify/\n!.specify/**\n"

    def test_uninstall_preserves_partial_ignore_even_when_forced(self, tmp_path):
        integration = get_integration(self.KEY)
        for force in (False, True):
            root = tmp_path / f"force-{force}"
            root.mkdir()
            manifest = IntegrationManifest(self.KEY, root)
            integration.setup(root, manifest, parsed_options=_OPT_IN)
            ignore = root / ".ignore"
            expected = ignore.read_bytes() + b"user-rule\n"
            ignore.write_bytes(expected)
            removed, skipped = integration.teardown(root, manifest, force=force)
            assert ignore.read_bytes() == expected
            assert ignore.resolve() not in {path.resolve() for path in removed}
            assert ignore.resolve() in {path.resolve() for path in skipped}

    def test_configure_ignore_file_rejects_unsafe_destinations(self, tmp_path):
        integration = get_integration(self.KEY)
        outside = tmp_path / "outside-secret"
        outside.write_bytes(b"secret\n")

        linked = tmp_path / "linked"
        linked.mkdir()
        integration.setup(linked, IntegrationManifest(self.KEY, linked))
        plan = linked / ".opencode" / "commands" / integration.command_filename("plan")
        plan.write_bytes(b"custom-command\n")
        link = linked / ".ignore"
        link.symlink_to(outside)
        with pytest.raises(ValueError, match="symlinked"):
            integration.setup(linked, IntegrationManifest(self.KEY, linked), parsed_options=_OPT_IN)
        assert plan.read_bytes() == b"custom-command\n"
        assert link.is_symlink()
        assert outside.read_bytes() == b"secret\n"

        directory = tmp_path / "directory"
        directory.mkdir()
        ignore_dir = directory / ".ignore"
        ignore_dir.mkdir()
        (ignore_dir / "user.txt").write_text("keep", encoding="utf-8")
        with pytest.raises(ValueError, match="not a regular file"):
            integration.setup(
                directory, IntegrationManifest(self.KEY, directory), parsed_options=_OPT_IN
            )
        assert not (directory / ".opencode").exists()
        assert (ignore_dir / "user.txt").read_text(encoding="utf-8") == "keep"

        unreadable = tmp_path / "unreadable"
        unreadable.mkdir()
        blocked = unreadable / ".ignore"
        blocked.write_bytes(b"user\n")
        blocked.chmod(0)
        try:
            with pytest.raises(OSError):
                integration.setup(
                    unreadable,
                    IntegrationManifest(self.KEY, unreadable),
                    parsed_options=_OPT_IN,
                )
        finally:
            blocked.chmod(0o644)
        assert blocked.read_bytes() == b"user\n"
        assert not (unreadable / ".opencode").exists()

        readonly = tmp_path / "readonly"
        readonly.mkdir()
        frozen = readonly / ".ignore"
        frozen.write_bytes(b"user\n")
        frozen.chmod(0o444)
        try:
            with pytest.raises(OSError):
                integration.setup(
                    readonly, IntegrationManifest(self.KEY, readonly), parsed_options=_OPT_IN
                )
        finally:
            frozen.chmod(0o644)
        assert frozen.read_bytes() == b"user\n"
        assert not (readonly / ".opencode").exists()

        failing = tmp_path / "write-fail"
        failing.mkdir()
        target = failing / ".ignore"
        original = b"user-rule-keep-this-prefix-intact\n"
        target.write_bytes(original)
        real_fdopen = os.fdopen

        def fdopen_fail(fd, mode="r", *args, **kwargs):
            stream = real_fdopen(fd, mode, *args, **kwargs)
            if mode != "wb":
                return stream
            raw_write = stream.write

            class _Stream:
                def write(self, data):
                    payload = bytes(data)
                    if b"!.specify/" in payload:
                        raw_write(payload[:8])
                        raise OSError("disk full")
                    return raw_write(data)

                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    stream.close()
                    return False

            return _Stream()

        with patch("os.fdopen", fdopen_fail):
            with pytest.raises(OSError, match="disk full"):
                integration.setup(
                    failing, IntegrationManifest(self.KEY, failing), parsed_options=_OPT_IN
                )
        assert target.read_bytes() == original
        assert (failing / ".opencode" / "commands").is_dir()
        assert list(failing.glob("..ignore.*")) == []

    @pytest.mark.skipif(
        os.name == "nt",
        reason="Windows reports directories writable regardless of mode bits",
    )
    def test_configure_ignore_file_rejects_writable_ignore_in_readonly_root(self, tmp_path):
        integration = get_integration(self.KEY)
        root = tmp_path / "readonly-root"
        root.mkdir()
        integration.setup(root, IntegrationManifest(self.KEY, root))
        plan = root / ".opencode" / "commands" / integration.command_filename("plan")
        plan.write_bytes(b"custom-command\n")
        ignore = root / ".ignore"
        ignore.write_bytes(b"user\n")
        ignore.chmod(0o644)
        root.chmod(0o555)
        try:
            assert os.access(ignore, os.W_OK)
            assert not os.access(root, os.W_OK)
            with pytest.raises(PermissionError, match="Cannot update .ignore"):
                integration.setup(
                    root, IntegrationManifest(self.KEY, root), parsed_options=_OPT_IN
                )
        finally:
            root.chmod(0o755)
        assert ignore.read_bytes() == b"user\n"
        assert plan.read_bytes() == b"custom-command\n"

    def test_upgrade_rolls_back_existing_ignore_when_a_later_step_fails(self, tmp_path):
        from specify_cli.integrations import installer
        from tests.specify_cli.integrations._helpers import _init_project, _run_in_project

        project = _init_project(tmp_path, "opencode")
        ignore = project / ".ignore"
        original = "café rule\r\n".encode()
        ignore.write_bytes(original)
        # Built-in upgrades open the file journal when an external package
        # record is present. The sentinel starts that transaction without
        # loading another adapter.
        with (
            patch.object(installer, "read_records", return_value={"sample": {"id": "sample"}}),
            patch.object(installer, "load_installed_integrations", return_value=[]),
            patch(
                "specify_cli.integrations.command_upgrade._write_integration_json",
                side_effect=OSError("later failure"),
            ),
        ):
            result = _run_in_project(
                project,
                [
                    "integration",
                    "upgrade",
                    "opencode",
                    "--force",
                    "--integration-options",
                    "--configure-ignore-file",
                ],
            )
        assert result.exit_code != 0
        assert "later failure" in result.output
        assert ignore.read_bytes() == original

    def test_forced_upgrade_rejects_bad_ignore_before_shared_writes(self, tmp_path):
        from tests.specify_cli.integrations._helpers import _init_project, _run_in_project

        project = _init_project(tmp_path, "opencode")
        template = project / ".specify" / "templates" / "plan-template.md"
        script = project / ".specify" / "scripts" / "bash" / "common.sh"
        template.write_text("custom template\n", encoding="utf-8")
        script.write_text("# custom script\n", encoding="utf-8")
        outside = tmp_path / "outside-ignore"
        outside.write_bytes(b"secret\n")
        ignore = project / ".ignore"
        for setup_ignore, match in (
            (lambda: ignore.symlink_to(outside), "symlinked"),
            (lambda: ignore.write_bytes(b"!.specify/\n!.specify/**\n.specify/**\n"), "later exclusion"),
        ):
            setup_ignore()
            result = _run_in_project(
                project,
                [
                    "integration",
                    "upgrade",
                    "opencode",
                    "--force",
                    "--integration-options",
                    "--configure-ignore-file",
                ],
            )
            assert result.exit_code != 0
            assert match in " ".join(result.output.split())
            assert template.read_text(encoding="utf-8") == "custom template\n"
            assert script.read_text(encoding="utf-8") == "# custom script\n"
            assert outside.read_bytes() == b"secret\n"
            ignore.unlink()

    def test_ignore_check_skips_script_variants_setup_does_not_install(self, tmp_path):
        integration = get_integration(self.KEY)
        rules = b"!.specify/\n!.specify/**\n.specify/scripts/powershell/check-prerequisites.ps1\n"
        sh_root = tmp_path / "sh"
        sh_root.mkdir()
        (sh_root / ".ignore").write_bytes(rules)
        integration.setup(
            sh_root, IntegrationManifest(self.KEY, sh_root),
            parsed_options=_OPT_IN, script_type="sh",
        )
        assert (sh_root / ".ignore").read_bytes() == rules

        for name, script_type, present in (("ps", "ps", False), ("sh-present", "sh", True)):
            root = tmp_path / name
            root.mkdir()
            (root / ".ignore").write_bytes(rules)
            if present:
                installed = root / ".specify" / "scripts" / "powershell"
                installed.mkdir(parents=True)
                (installed / "check-prerequisites.ps1").write_text("x\n")
            with pytest.raises(ValueError, match="check-prerequisites.ps1"):
                integration.setup(
                    root, IntegrationManifest(self.KEY, root),
                    parsed_options=_OPT_IN, script_type=script_type,
                )
            assert (root / ".ignore").read_bytes() == rules
