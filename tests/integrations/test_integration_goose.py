"""Tests for GooseIntegration."""

import yaml
from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_yaml import YamlIntegrationTests


class TestGooseIntegration(YamlIntegrationTests):
    KEY = "goose"
    FOLDER = ".goose/"
    COMMANDS_SUBDIR = "recipes"
    REGISTRAR_DIR = ".goose/recipes"

    def test_setup_declares_args_parameter_for_args_prompt(self, tmp_path):
        # “If a generated Goose recipe uses {{args}} in its prompt, it
        # must declare a corresponding args parameter.”

        integration = get_integration("goose")
        assert integration is not None

        manifest = IntegrationManifest("goose", tmp_path)
        created = integration.setup(tmp_path, manifest, script_type="sh")

        recipe_files = [path for path in created if path.suffix == ".yaml"]
        assert recipe_files

        for recipe_file in recipe_files:
            data = yaml.safe_load(recipe_file.read_text(encoding="utf-8"))

            if "{{args}}" not in data["prompt"]:
                continue

            assert any(
                param.get("key") == "args"
                for param in data.get("parameters", [])
            ), f"{recipe_file} uses {{{{args}}}} but does not declare args"


class TestGooseCommandPlaceholderResolution:
    """register_commands must resolve skill placeholders for the yaml branch.

    The yaml (Goose recipe) branch previously skipped
    resolve_skill_placeholders / _convert_argument_placeholder that the
    markdown and toml branches apply, so extension/preset command bodies
    kept literal {SCRIPT} / __AGENT__ / repo-relative paths.
    """

    def test_register_commands_resolves_placeholders_in_recipe(self, tmp_path):
        from specify_cli.agents import CommandRegistrar

        ext_dir = tmp_path / "extension"
        cmd_dir = ext_dir / "commands"
        cmd_dir.mkdir(parents=True)
        cmd_file = cmd_dir / "example.md"
        cmd_file.write_text(
            "---\n"
            "description: Placeholder command\n"
            "scripts:\n"
            "  sh: scripts/bash/do.sh\n"
            "  ps: scripts/powershell/do.ps1\n"
            "---\n\n"
            "Run {SCRIPT} for agent __AGENT__ with $ARGUMENTS.\n",
            encoding="utf-8",
        )

        registrar = CommandRegistrar()
        commands = [{"name": "speckit.example", "file": "commands/example.md"}]
        registrar.register_commands("goose", commands, "test-ext", ext_dir, tmp_path)

        recipe = tmp_path / ".goose" / "recipes" / "speckit.example.yaml"
        assert recipe.exists(), "goose recipe should be generated"
        # Parse the recipe and assert the prompt actually got the correct
        # replacements — not merely that the literal tokens are absent (which
        # a wrong-but-token-free output could also satisfy).
        data = yaml.safe_load(recipe.read_text(encoding="utf-8"))
        prompt = data["prompt"]
        assert ".specify/scripts/" in prompt  # {SCRIPT} -> resolved script path
        assert "agent goose" in prompt  # __AGENT__ -> agent name
        assert "{{args}}" in prompt  # $ARGUMENTS -> goose args token
        # And the raw placeholders must not survive.
        assert "{SCRIPT}" not in prompt
        assert "__AGENT__" not in prompt
        assert "$ARGUMENTS" not in prompt
