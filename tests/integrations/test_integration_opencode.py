"""Tests for OpencodeIntegration."""

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest
from specify_cli.integrations.opencode import _migrate_legacy_command_dir

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestOpencodeIntegration(MarkdownIntegrationTests):
    KEY = "opencode"
    FOLDER = ".opencode/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".opencode/commands"
    CONTEXT_FILE = "AGENTS.md"

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


class TestOpencodeCommandMigration:
    """Test legacy .opencode/command → .opencode/commands migration."""

    def test_removes_legacy_command_dir(self, tmp_path):
        """Legacy file is removed when byte-identical to counterpart."""
        legacy = tmp_path / ".opencode" / "command"
        legacy.mkdir(parents=True)
        (legacy / "speckit.specify.md").write_text("identical content")
        new_dir = tmp_path / ".opencode" / "commands"
        new_dir.mkdir(parents=True)
        (new_dir / "speckit.specify.md").write_text("identical content")

        removed = _migrate_legacy_command_dir(tmp_path)

        assert removed == 1
        assert not legacy.exists()

    def test_preserves_user_customized_legacy_command(self, tmp_path):
        """Legacy file with different content (user-customized) is preserved."""
        legacy = tmp_path / ".opencode" / "command"
        legacy.mkdir(parents=True)
        (legacy / "speckit.specify.md").write_text("my customization")
        new_dir = tmp_path / ".opencode" / "commands"
        new_dir.mkdir(parents=True)
        (new_dir / "speckit.specify.md").write_text("canonical content")

        removed = _migrate_legacy_command_dir(tmp_path)

        assert removed == 0  # nothing was removed or moved
        assert (legacy / "speckit.specify.md").exists()  # user file preserved
        assert legacy.exists()  # dir not removed (still has content)

    def test_no_op_when_no_legacy_dir(self, tmp_path):
        removed = _migrate_legacy_command_dir(tmp_path)
        assert removed == 0

    def test_moves_user_owned_files_to_new_dir(self, tmp_path):
        """Files without a counterpart in the new dir are moved, not deleted."""
        legacy = tmp_path / ".opencode" / "command"
        legacy.mkdir(parents=True)
        (legacy / "my-custom-command.md").write_text("user content")
        new_dir = tmp_path / ".opencode" / "commands"
        new_dir.mkdir(parents=True)

        removed = _migrate_legacy_command_dir(tmp_path)

        assert removed == 1
        assert not (legacy / "my-custom-command.md").exists()
        assert (new_dir / "my-custom-command.md").read_text() == "user content"

    def test_handles_symlink_without_following(self, tmp_path):
        """A symlink at the legacy path is unlinked, not traversed via rmtree."""
        target = tmp_path / "real_dir"
        target.mkdir()
        (legacy_parent := tmp_path / ".opencode").mkdir(parents=True)
        legacy = legacy_parent / "command"
        legacy.symlink_to(target)

        removed = _migrate_legacy_command_dir(tmp_path)

        assert removed == 1
        assert not legacy.exists()
        assert target.is_dir()  # target is untouched

    def test_setup_removes_legacy_dir(self, tmp_path):
        """setup() preserves user-customized files and moves files without counterparts."""
        legacy = tmp_path / ".opencode" / "command"
        legacy.mkdir(parents=True)
        (legacy / "speckit.specify.md").write_text("old content")
        (legacy / "my-custom.md").write_text("user content")

        i = get_integration("opencode")
        m = IntegrationManifest("opencode", tmp_path)
        i.setup(tmp_path, m)

        assert (tmp_path / ".opencode" / "commands").is_dir()
        # User-customized speckit.specify.md is preserved in legacy dir
        assert (legacy / "speckit.specify.md").exists()
        assert legacy.exists()  # dir still exists because it has the customized file
        # my-custom.md has no counterpart, so it was moved to new dir
        assert not (legacy / "my-custom.md").exists()
        assert (tmp_path / ".opencode" / "commands" / "my-custom.md").read_text() == "user content"
