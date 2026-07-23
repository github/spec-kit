"""Tests for KilocodeIntegration."""

from specify_cli.agents import CommandRegistrar
from specify_cli.integrations import get_integration

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestKilocodeIntegration(MarkdownIntegrationTests):
    KEY = "kilocode"
    FOLDER = ".kilo/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".kilo/commands"

    def test_registrar_config_has_legacy_dir(self):
        integration = get_integration(self.KEY)
        assert integration.registrar_config["legacy_dir"] == ".kilocode/workflows"

    def test_legacy_dir_extension_registration(self, tmp_path):
        """Extension commands still register into legacy Kilo projects."""
        legacy_dir = tmp_path / ".kilocode" / "workflows"
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "speckit.specify.md").write_text(
            "# existing", encoding="utf-8"
        )

        src_dir = tmp_path / "_ext_src"
        src_dir.mkdir()
        (src_dir / "myext.md").write_text(
            "---\ndescription: test\n---\n# ext command",
            encoding="utf-8",
        )

        registrar = CommandRegistrar()
        commands = [{"name": "speckit.myext", "file": "myext.md"}]
        results = registrar.register_commands(
            self.KEY,
            commands,
            "test-ext",
            src_dir,
            tmp_path,
        )

        assert results == ["speckit.myext"]
        assert (legacy_dir / "speckit.myext.md").exists()
        assert not (tmp_path / ".kilo" / "commands").exists()

    def test_legacy_dir_extension_unregister(self, tmp_path):
        """Unregister removes commands from legacy Kilo projects."""
        legacy_dir = tmp_path / ".kilocode" / "workflows"
        legacy_dir.mkdir(parents=True)
        cmd_file = legacy_dir / "speckit.myext.md"
        cmd_file.write_text("# ext command", encoding="utf-8")

        registrar = CommandRegistrar()
        registrar.unregister_commands({"kilocode": ["speckit.myext"]}, tmp_path)

        assert not cmd_file.exists()

    def test_unregister_cleans_legacy_when_both_dirs_exist(self, tmp_path):
        """Unregister removes stale legacy files after Kilo path migration."""
        canonical_dir = tmp_path / ".kilo" / "commands"
        canonical_dir.mkdir(parents=True)
        legacy_dir = tmp_path / ".kilocode" / "workflows"
        legacy_dir.mkdir(parents=True)

        canonical_cmd = canonical_dir / "speckit.myext.md"
        canonical_cmd.write_text("# ext command", encoding="utf-8")
        legacy_cmd = legacy_dir / "speckit.myext.md"
        legacy_cmd.write_text("# stale ext command", encoding="utf-8")

        registrar = CommandRegistrar()
        registrar.unregister_commands({"kilocode": ["speckit.myext"]}, tmp_path)

        assert not canonical_cmd.exists()
        assert not legacy_cmd.exists()
