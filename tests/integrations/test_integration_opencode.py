"""Tests for OpencodeIntegration."""

import json
import os
import shutil
import stat
import subprocess
import warnings
from unittest.mock import patch

import pytest

from specify_cli.agents import CommandRegistrar
from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_markdown import MarkdownIntegrationTests

_OPT_IN = {"configure_ignore_file": True}
_PRIVATE_RULES = (
    ".specify/**/local-config.yml",
    ".specify/**/*-config.local.yml",
    ".specify/workflows/runs/",
)
_PRIVATE = "\n".join(_PRIVATE_RULES)
_PRIVATE_CRLF = "\r\n".join(_PRIVATE_RULES)
_RULES = f"!.specify/\n!.specify/**\n{_PRIVATE}\n".encode()
_AS_ROOT = getattr(os, "geteuid", lambda: -1)() == 0


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
        assert ignore.read_bytes() == _RULES
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
            "empty": (b"", _RULES),
            "lf-non-ascii-no-final-newline": (
                "café keep".encode(),
                f"café keep\n!.specify/\n!.specify/**\n{_PRIVATE}\n".encode(),
            ),
            "crlf-non-ascii-no-final-newline": (
                "café\r\nkeep".encode(),
                f"café\r\nkeep\r\n!.specify/\r\n!.specify/**\r\n{_PRIVATE_CRLF}\r\n".encode(),
            ),
            "dir-rule-only": (b"!.specify/\n", _RULES),
            "contents-rule-only": (
                b"!.specify/**\n", f"!.specify/**\n!.specify/\n{_PRIVATE}\n".encode()
            ),
            "both-rules": (
                "café\r\n!.specify/\r\n!.specify/**\r\n".encode(),
                f"café\r\n!.specify/\r\n!.specify/**\r\n{_PRIVATE_CRLF}\r\n".encode(),
            ),
            "all-rules": (_RULES, _RULES),
            "private-rule-before-exceptions": (
                f"{_PRIVATE}\n!.specify/\n!.specify/**\n".encode(),
                f"{_PRIVATE}\n!.specify/\n!.specify/**\n{_PRIVATE}\n".encode(),
            ),
            "negation-after-private-rules": (
                _RULES + b"!.specify/extensions/jira/local-config.yml\n",
                _RULES + b"!.specify/extensions/jira/local-config.yml\n"
                + _PRIVATE.encode() + b"\n",
            ),
            "broader-exclusions": (
                b"*\n.*\n.specify/**\n",
                b"*\n.*\n.specify/**\n" + _RULES,
            ),
            "bare-cr-comment": (
                b"# user comment\r!.specify/\n!.specify/**\n",
                b"# user comment\r!.specify/\n!.specify/**\n!.specify/\n"
                + _PRIVATE.encode() + b"\n",
            ),
            "unicode-separator-comment": (
                "!.specify/\n!.specify/**\n# note\u2028.specify/memory\n".encode(),
                f"!.specify/\n!.specify/**\n# note\u2028.specify/memory\n{_PRIVATE}\n".encode(),
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
        restored = b"!.specify/\n!.specify/**\n.specify/**\n!.specify/**\n" + _PRIVATE.encode() + b"\n"
        (tmp_path / ".ignore").write_bytes(restored)
        integration.setup(tmp_path, IntegrationManifest(self.KEY, tmp_path), parsed_options=_OPT_IN)
        assert (tmp_path / ".ignore").read_bytes() == restored
        kept = (
            b"!.specify/\n!.specify/**\n.specify/memory\n!.specify/memory/\n!.specify/memory/**\n"
            + _PRIVATE.encode() + b"\n"
        )
        reinclude = tmp_path / "reinclude"
        reinclude.mkdir()
        (reinclude / ".ignore").write_bytes(kept)
        integration.setup(reinclude, IntegrationManifest(self.KEY, reinclude), parsed_options=_OPT_IN)
        assert (reinclude / ".ignore").read_bytes() == kept

    def test_configure_ignore_file_keeps_local_extension_config_hidden(self, tmp_path):
        """Private extension overrides stay excluded and may be excluded again."""
        import pathspec

        integration = get_integration(self.KEY)
        local = tmp_path / ".specify" / "extensions" / "jira" / "local-config.yml"
        local.parent.mkdir(parents=True)
        local.write_text("api_token: x\n", encoding="utf-8")
        (local.parent / "jira-config.yml").write_text("project: x\n", encoding="utf-8")
        ignore = tmp_path / ".ignore"
        ignore.write_bytes(b"!.specify/\n!.specify/**\n.specify/extensions/jira/local-config.yml\n")
        integration.setup(tmp_path, IntegrationManifest(self.KEY, tmp_path), parsed_options=_OPT_IN)
        spec = pathspec.GitIgnoreSpec.from_lines(ignore.read_text(encoding="utf-8").splitlines())
        assert spec.match_file(".specify/extensions/jira/local-config.yml")
        assert spec.match_file(".specify/extensions/other/local-config.yml")
        assert spec.match_file(".specify/extensions/.backup/jira/local-config.yml")
        assert spec.match_file(".specify/extensions/jira/jira-config.local.yml")
        # pathspec ranks a file match above a directory rule, so check the
        # directory the way ripgrep walks it.
        from specify_cli.integrations.opencode import _spec_hides

        assert _spec_hides(spec, ".specify/workflows/runs/run-1/state.json")
        assert not spec.match_file(".specify/extensions/jira/jira-config.yml")
        assert not spec.match_file(".specify/memory/constitution.md")

    @pytest.mark.skipif(shutil.which("rg") is None, reason="ripgrep not installed")
    def test_configure_ignore_file_private_rules_on_native_ripgrep(self, tmp_path):
        """Pin what real ripgrep does with the written .ignore.

        A plain listing omits private configs. A positive ``--glob`` that
        matches them overrides ignore files, which is why the docs do not
        claim the glob tool hides them.
        """
        integration = get_integration(self.KEY)
        constitution = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution.parent.mkdir(parents=True)
        constitution.write_text("# Constitution\n", encoding="utf-8")
        ext = tmp_path / ".specify" / "extensions" / "jira"
        ext.mkdir(parents=True)
        (ext / "jira-config.yml").write_text("project: x\n", encoding="utf-8")
        (ext / "local-config.yml").write_text("placeholder: x\n", encoding="utf-8")
        (ext / "jira-config.local.yml").write_text("placeholder: x\n", encoding="utf-8")
        run = tmp_path / ".specify" / "workflows" / "runs" / "run-1"
        run.mkdir(parents=True)
        for name in ("state.json", "inputs.json", "log.jsonl"):
            (run / name).write_text('{"stdout": "captured"}\n', encoding="utf-8")
        integration.setup(tmp_path, IntegrationManifest(self.KEY, tmp_path), parsed_options=_OPT_IN)

        def rg_files(*args):
            out = subprocess.run(
                ["rg", "--files", "--no-config", *args],
                cwd=tmp_path, capture_output=True, text=True, check=False,
            )
            assert out.returncode in (0, 1), out.stderr
            return {line.removeprefix("./").replace("\\", "/") for line in out.stdout.splitlines()}

        private = {
            ".specify/extensions/jira/local-config.yml",
            ".specify/extensions/jira/jira-config.local.yml",
            ".specify/workflows/runs/run-1/state.json",
            ".specify/workflows/runs/run-1/inputs.json",
            ".specify/workflows/runs/run-1/log.jsonl",
        }
        plain = rg_files()
        assert ".specify/memory/constitution.md" in plain
        assert ".specify/extensions/jira/jira-config.yml" in plain
        assert not plain & private
        globbed = rg_files("--glob", ".specify/**/*")
        assert ".specify/memory/constitution.md" in globbed
        assert private <= globbed

    def test_configure_ignore_file_allows_excluding_extension_backups(self, tmp_path):
        """A user exclusion of removal backups is not treated as hiding Spec Kit files."""
        integration = get_integration(self.KEY)
        backup = tmp_path / ".specify" / "extensions" / ".backup" / "jira"
        backup.mkdir(parents=True)
        (backup / "jira-config.yml").write_text("project: x\n", encoding="utf-8")
        ignore = tmp_path / ".ignore"
        original = _RULES + b".specify/extensions/.backup/\n"
        ignore.write_bytes(original)
        integration.setup(tmp_path, IntegrationManifest(self.KEY, tmp_path), parsed_options=_OPT_IN)
        assert ignore.read_bytes() == original

    @pytest.mark.parametrize(
        "exclusion",
        [b".specify/workflows/runs/*/state.json\n", b".specify/workflows/runs/**\n"],
    )
    def test_configure_ignore_file_allows_excluding_workflow_run_state(self, tmp_path, exclusion):
        """Existing run state with captured output does not block a user exclusion."""
        integration = get_integration(self.KEY)
        run = tmp_path / ".specify" / "workflows" / "runs" / "run-1"
        run.mkdir(parents=True)
        (run / "state.json").write_text(
            '{"step_results": {"s1": {"stdout": "captured", "stderr": ""}}}\n',
            encoding="utf-8",
        )
        (run / "log.jsonl").write_text('{"event": "step"}\n', encoding="utf-8")
        ignore = tmp_path / ".ignore"
        original = _RULES + exclusion
        ignore.write_bytes(original)
        integration.setup(tmp_path, IntegrationManifest(self.KEY, tmp_path), parsed_options=_OPT_IN)
        assert ignore.read_bytes() == original

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
        assert ignore.read_bytes() == b"keep me\n" + _RULES
        result = _run_in_project(project, ["integration", "upgrade", "opencode", "--force"])
        assert result.exit_code == 0, result.output
        assert ignore.read_bytes() == b"keep me\n" + _RULES

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

    @pytest.mark.skipif(_AS_ROOT, reason="Root bypasses file permission checks")
    def test_configure_ignore_file_rejects_unreadable_and_readonly_ignore(self, tmp_path):
        integration = get_integration(self.KEY)
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

    @pytest.mark.skipif(_AS_ROOT, reason="Root bypasses directory permission checks")
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

    def test_configure_ignore_file_skips_malformed_glob_lines(self, tmp_path):
        """pathspec raises re.error for a reversed range; the line is skipped."""
        original = b"[z-a].txt\n"
        (tmp_path / ".ignore").write_bytes(original)
        get_integration(self.KEY).setup(
            tmp_path, IntegrationManifest(self.KEY, tmp_path), parsed_options=_OPT_IN
        )
        assert (tmp_path / ".ignore").read_bytes() == original + _RULES

    @pytest.mark.skipif(os.name == "nt", reason="POSIX O_NOFOLLOW read path")
    def test_configure_ignore_file_refuses_link_swapped_in_before_read(self, tmp_path):
        from specify_cli.file_helper import FileHelper

        outside = tmp_path / "outside-secret"
        outside.write_bytes(b"secret\n")
        root = tmp_path / "project"
        root.mkdir()
        ignore = root / ".ignore"
        ignore.write_bytes(b"user\n")
        real_require = FileHelper._require_file

        def swap(path):
            real_require(path)
            if path.name == ".ignore" and not path.is_symlink():
                path.unlink()
                path.symlink_to(outside)

        with (
            patch.object(FileHelper, "_require_file", staticmethod(swap)),
            pytest.raises(ValueError, match="symlinked"),
        ):
            get_integration(self.KEY).setup(
                root, IntegrationManifest(self.KEY, root), parsed_options=_OPT_IN
            )
        assert ignore.is_symlink()
        assert outside.read_bytes() == b"secret\n"
        assert not (root / ".opencode").exists()

    def test_configure_ignore_file_aborts_when_ignore_changes_before_write(self, tmp_path):
        from specify_cli.integrations import opencode

        ignore = tmp_path / ".ignore"
        ignore.write_bytes(b"user\n")
        real_reject = opencode._reject_hidden_specify_paths
        calls = []

        def reject_then_edit(*args, **kwargs):
            real_reject(*args, **kwargs)
            calls.append(None)
            if len(calls) == 2:
                ignore.write_bytes(b"concurrent edit\n")

        with (
            patch.object(opencode, "_reject_hidden_specify_paths", reject_then_edit),
            pytest.raises(ValueError, match="changed while"),
        ):
            get_integration(self.KEY).setup(
                tmp_path, IntegrationManifest(self.KEY, tmp_path), parsed_options=_OPT_IN
            )
        assert ignore.read_bytes() == b"concurrent edit\n"

    def test_configure_ignore_file_rejects_nested_specify_ignore_files(self, tmp_path):
        for name in (".ignore", ".rgignore"):
            root = tmp_path / name.lstrip(".")
            memory = root / ".specify" / "memory"
            memory.mkdir(parents=True)
            (memory / "constitution.md").write_text("x\n")
            nested = root / ".specify" / name
            nested.write_bytes(b"memory/\n")
            with pytest.raises(ValueError, match=rf"\{name}.*constitution\.md"):
                get_integration(self.KEY).setup(
                    root, IntegrationManifest(self.KEY, root), parsed_options=_OPT_IN
                )
            assert not (root / ".ignore").exists()
            assert nested.read_bytes() == b"memory/\n"

    @pytest.mark.parametrize(
        ("ignore_file", "content"),
        [
            (".rgignore", b".specify/\n"),
            (".rgignore", b"*.md\n"),
            (".specify/memory/.ignore", b"*.md\n"),
            (".specify/memory/.rgignore", b"constitution.md\n"),
        ],
    )
    def test_configure_ignore_file_rejects_overriding_ignore_files(
        self, tmp_path, ignore_file, content
    ):
        """A root .rgignore or a deeper ignore file outranks the root .ignore."""
        constitution = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution.parent.mkdir(parents=True)
        constitution.write_text("x\n")
        blocker = tmp_path / ignore_file
        blocker.write_bytes(content)
        if shutil.which("rg") is not None:
            # Pin the precedence on real ripgrep with the rules setup would write.
            (tmp_path / ".ignore").write_bytes(_RULES)
            out = subprocess.run(
                ["rg", "--files", "--no-config"],
                cwd=tmp_path, capture_output=True, text=True, check=False,
            )
            assert ".specify/memory/constitution.md" not in out.stdout.replace("\\", "/")
            (tmp_path / ".ignore").unlink()
        with pytest.raises(ValueError, match=rf"{ignore_file.split('/')[-1]}.*hides"):
            get_integration(self.KEY).setup(
                tmp_path, IntegrationManifest(self.KEY, tmp_path), parsed_options=_OPT_IN
            )
        assert not (tmp_path / ".ignore").exists()
        assert blocker.read_bytes() == content

    def test_configure_ignore_file_allows_reincluding_ignore_files(self, tmp_path):
        """Nearer re-includes win, so they do not block setup."""
        constitution = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution.parent.mkdir(parents=True)
        constitution.write_text("x\n")
        (tmp_path / ".rgignore").write_bytes(b"*.md\n")
        (tmp_path / ".specify" / ".rgignore").write_bytes(b"!*.md\n")
        (tmp_path / ".specify" / "memory" / ".ignore").write_bytes(b"*.md\n!constitution.md\n")
        get_integration(self.KEY).setup(
            tmp_path, IntegrationManifest(self.KEY, tmp_path), parsed_options=_OPT_IN
        )
        assert (tmp_path / ".ignore").read_bytes() == _RULES
        if shutil.which("rg") is not None:
            out = subprocess.run(
                ["rg", "--files", "--no-config"],
                cwd=tmp_path, capture_output=True, text=True, check=False,
            )
            assert ".specify/memory/constitution.md" in out.stdout.replace("\\", "/")

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
        assert (sh_root / ".ignore").read_bytes() == rules + _PRIVATE.encode() + b"\n"

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
