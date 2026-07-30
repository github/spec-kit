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


class TestGooseCliDispatch:
    """`goose` must produce argv for non-interactive dispatch.

    `YamlIntegration` never overrode `build_exec_args()`, so Goose inherited the
    `IntegrationBase` no-op returning `None`. Callers read `None` as "CLI
    unavailable", so a workflow command/prompt step targeting Goose reported
    "CLI not found or not installed" even with `goose` on PATH — the Goose item
    in issue #2416. `goose run` supports `-t/--text`, `--recipe`,
    `--params KEY=VALUE`, `--model` and `--output-format`.
    """

    def test_build_exec_args_is_not_none(self):
        integration = get_integration("goose")
        assert integration.build_exec_args("/speckit.specify") is not None

    def test_slash_command_maps_to_recipe(self):
        integration = get_integration("goose")
        args = integration.build_exec_args("/speckit.specify", output_json=False)
        assert args[1] == "run"
        assert "--recipe" in args
        assert args[args.index("--recipe") + 1] == ".goose/recipes/speckit.specify.yaml"
        # No trailing args -> no --params
        assert "--params" not in args

    def test_slash_command_arguments_map_to_params(self):
        integration = get_integration("goose")
        args = integration.build_exec_args("/speckit.specify add auth", output_json=False)
        assert args[args.index("--params") + 1] == "args=add auth"

    def test_dotted_extension_command_maps_to_recipe(self):
        integration = get_integration("goose")
        args = integration.build_exec_args("/speckit.git.commit msg", output_json=False)
        assert args[args.index("--recipe") + 1] == (
            ".goose/recipes/speckit.git.commit.yaml"
        )

    def test_free_form_prompt_uses_text_flag(self):
        """goose has no `-p`; free-form text goes to `-t/--text`."""
        integration = get_integration("goose")
        args = integration.build_exec_args("just do it", output_json=False)
        assert args[-2:] == ["-t", "just do it"]
        assert "--recipe" not in args

    def test_non_speckit_slash_prompt_is_not_treated_as_a_recipe(self):
        """`/help` is a goose session command, not a Spec Kit recipe.

        `PromptStep` passes arbitrary `prompt:` strings to `build_exec_args`,
        and the recipe branch synthesizes a *file path*, so slash text outside
        the `speckit.` namespace must not become
        `--recipe .goose/recipes/speckit.help.yaml` — `setup()` only ever
        writes `command_filename(stem)` = `speckit.<name>.yaml`.
        """
        integration = get_integration("goose")
        args = integration.build_exec_args("/help", output_json=False)
        assert "--recipe" not in args
        assert "--params" not in args
        assert args[-2:] == ["-t", "/help"]

    def test_non_speckit_slash_prompt_is_not_promoted_to_a_recipe(self):
        """`/plan` is goose's own command and must not run speckit.plan.

        `command_filename()` re-adds the `speckit.` prefix, so the old
        unconditional call silently promoted the free-form goose command
        `/plan` into a real Spec Kit recipe run. Dispatch always spells
        commands `/speckit.plan` (`IntegrationBase.build_command_invocation`),
        so no reachable recipe is lost.
        """
        integration = get_integration("goose")
        args = integration.build_exec_args("/plan the sprint", output_json=False)
        assert "--recipe" not in args
        assert args[-2:] == ["-t", "/plan the sprint"]

    def test_bare_speckit_prefix_falls_through_to_text(self):
        """`/speckit.` alone has no stem and must not yield `speckit..yaml`."""
        integration = get_integration("goose")
        args = integration.build_exec_args("/speckit.", output_json=False)
        assert "--recipe" not in args
        assert args[-2:] == ["-t", "/speckit."]

    def test_model_and_output_format_flags(self):
        integration = get_integration("goose")
        args = integration.build_exec_args("hi", model="gpt-4o", output_json=True)
        assert args[args.index("--model") + 1] == "gpt-4o"
        assert args[args.index("--output-format") + 1] == "json"

    def test_recipe_target_matches_what_setup_writes(self, tmp_path):
        """Anti-drift: the dispatched `--recipe` path must be the file `setup()`
        actually installed, so the two cannot diverge."""
        integration = get_integration("goose")
        manifest = IntegrationManifest("goose", tmp_path)
        created = integration.setup(tmp_path, manifest, script_type="sh")
        assert created

        args = integration.build_exec_args("/speckit.specify hello")
        recipe = args[args.index("--recipe") + 1]
        assert (tmp_path / recipe).is_file(), f"{recipe} was not installed by setup()"
