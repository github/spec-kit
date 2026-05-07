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
    CONTEXT_FILE = "AGENTS.md"

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
