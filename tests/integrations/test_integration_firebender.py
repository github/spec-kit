"""Tests for FirebenderIntegration."""

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestFirebenderIntegration(MarkdownIntegrationTests):
    KEY = "firebender"
    FOLDER = ".firebender/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".firebender/commands"
    CONTEXT_FILE = ".firebender/rules/specify-rules.mdc"

    # Firebender reads custom slash commands from ``.firebender/commands/*.mdc``,
    # so this integration uses the ``.mdc`` extension instead of the ``.md``
    # default the base mixin assumes. Override the two extension-specific tests.
    def test_registrar_config(self):
        i = get_integration(self.KEY)
        assert i.registrar_config["dir"] == self.REGISTRAR_DIR
        assert i.registrar_config["format"] == "markdown"
        assert i.registrar_config["args"] == "$ARGUMENTS"
        assert i.registrar_config["extension"] == ".mdc"

    def test_setup_creates_files(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        assert len(created) > 0
        cmd_files = [f for f in created if "scripts" not in f.parts]
        for f in cmd_files:
            assert f.exists()
            assert f.name.startswith("speckit.")
            assert f.name.endswith(".mdc")

    def _expected_files(self, script_variant: str) -> list[str]:
        # Firebender emits ``.mdc`` command files, so remap the base mixin's
        # ``.md`` expectations for files under this integration's command dir.
        cmd_dir = get_integration(self.KEY).registrar_config["dir"]
        prefix = cmd_dir + "/"
        return sorted(
            f[:-3] + ".mdc" if f.startswith(prefix) and f.endswith(".md") else f
            for f in super()._expected_files(script_variant)
        )
