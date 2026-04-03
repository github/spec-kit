"""Tests for ForgeIntegration."""

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest
from specify_cli.integrations.forge import format_forge_command_name


class TestForgeCommandNameFormatter:
    """Test the centralized Forge command name formatter."""

    def test_simple_name_without_prefix(self):
        """Test formatting a simple name without 'speckit.' prefix."""
        assert format_forge_command_name("plan") == "speckit-plan"
        assert format_forge_command_name("tasks") == "speckit-tasks"
        assert format_forge_command_name("specify") == "speckit-specify"

    def test_name_with_speckit_prefix(self):
        """Test formatting a name that already has 'speckit.' prefix."""
        assert format_forge_command_name("speckit.plan") == "speckit-plan"
        assert format_forge_command_name("speckit.tasks") == "speckit-tasks"

    def test_extension_command_name(self):
        """Test formatting extension command names with dots."""
        assert format_forge_command_name("speckit.my-extension.example") == "speckit-my-extension-example"
        assert format_forge_command_name("my-extension.example") == "speckit-my-extension-example"

    def test_complex_nested_name(self):
        """Test formatting deeply nested command names."""
        assert format_forge_command_name("speckit.jira.sync-status") == "speckit-jira-sync-status"
        assert format_forge_command_name("speckit.foo.bar.baz") == "speckit-foo-bar-baz"

    def test_name_with_hyphens_preserved(self):
        """Test that existing hyphens are preserved."""
        assert format_forge_command_name("my-extension") == "speckit-my-extension"
        assert format_forge_command_name("speckit.my-ext.test-cmd") == "speckit-my-ext-test-cmd"

    def test_alias_formatting(self):
        """Test formatting alias names."""
        assert format_forge_command_name("speckit.my-extension.example-short") == "speckit-my-extension-example-short"

    def test_idempotent_already_hyphenated(self):
        """Test that already-hyphenated names are returned unchanged (idempotent)."""
        assert format_forge_command_name("speckit-plan") == "speckit-plan"
        assert format_forge_command_name("speckit-my-extension-example") == "speckit-my-extension-example"
        assert format_forge_command_name("speckit-jira-sync-status") == "speckit-jira-sync-status"


class TestForgeIntegration:
    def test_forge_key_and_config(self):
        forge = get_integration("forge")
        assert forge is not None
        assert forge.key == "forge"
        assert forge.config["folder"] == ".forge/"
        assert forge.config["commands_subdir"] == "commands"
        assert forge.config["requires_cli"] is True
        assert forge.registrar_config["args"] == "{{parameters}}"
        assert forge.registrar_config["extension"] == ".md"
        assert forge.context_file == "AGENTS.md"

    def test_command_filename_md(self):
        forge = get_integration("forge")
        assert forge.command_filename("plan") == "speckit.plan.md"

    def test_setup_creates_md_files(self, tmp_path):
        from specify_cli.integrations.forge import ForgeIntegration
        forge = ForgeIntegration()
        m = IntegrationManifest("forge", tmp_path)
        created = forge.setup(tmp_path, m)
        assert len(created) > 0
        # Separate command files from scripts
        command_files = [f for f in created if f.parent == tmp_path / ".forge" / "commands"]
        assert len(command_files) > 0
        for f in command_files:
            assert f.name.endswith(".md")

    def test_setup_installs_update_scripts(self, tmp_path):
        from specify_cli.integrations.forge import ForgeIntegration
        forge = ForgeIntegration()
        m = IntegrationManifest("forge", tmp_path)
        created = forge.setup(tmp_path, m)
        script_files = [f for f in created if "scripts" in f.parts]
        assert len(script_files) > 0
        sh_script = tmp_path / ".specify" / "integrations" / "forge" / "scripts" / "update-context.sh"
        ps_script = tmp_path / ".specify" / "integrations" / "forge" / "scripts" / "update-context.ps1"
        assert sh_script in created
        assert ps_script in created
        assert sh_script.exists()
        assert ps_script.exists()

    def test_all_created_files_tracked_in_manifest(self, tmp_path):
        from specify_cli.integrations.forge import ForgeIntegration
        forge = ForgeIntegration()
        m = IntegrationManifest("forge", tmp_path)
        created = forge.setup(tmp_path, m)
        for f in created:
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"Created file {rel} not tracked in manifest"

    def test_install_uninstall_roundtrip(self, tmp_path):
        from specify_cli.integrations.forge import ForgeIntegration
        forge = ForgeIntegration()
        m = IntegrationManifest("forge", tmp_path)
        created = forge.install(tmp_path, m)
        assert len(created) > 0
        m.save()
        for f in created:
            assert f.exists()
        removed, skipped = forge.uninstall(tmp_path, m)
        assert len(removed) == len(created)
        assert skipped == []

    def test_modified_file_survives_uninstall(self, tmp_path):
        from specify_cli.integrations.forge import ForgeIntegration
        forge = ForgeIntegration()
        m = IntegrationManifest("forge", tmp_path)
        created = forge.install(tmp_path, m)
        m.save()
        # Modify a command file (not a script)
        command_files = [f for f in created if f.parent == tmp_path / ".forge" / "commands"]
        modified_file = command_files[0]
        modified_file.write_text("user modified this", encoding="utf-8")
        removed, skipped = forge.uninstall(tmp_path, m)
        assert modified_file.exists()
        assert modified_file in skipped

    def test_directory_structure(self, tmp_path):
        from specify_cli.integrations.forge import ForgeIntegration
        forge = ForgeIntegration()
        m = IntegrationManifest("forge", tmp_path)
        forge.setup(tmp_path, m)
        commands_dir = tmp_path / ".forge" / "commands"
        assert commands_dir.is_dir()

        # Derive expected command names from the Forge command templates so the test
        # stays in sync if templates are added/removed.
        templates = forge.list_command_templates()
        expected_commands = {t.stem for t in templates}
        assert len(expected_commands) > 0, "No command templates found"

        # Check generated files match templates
        command_files = sorted(commands_dir.glob("speckit.*.md"))
        assert len(command_files) == len(expected_commands)
        actual_commands = {f.name.removeprefix("speckit.").removesuffix(".md") for f in command_files}
        assert actual_commands == expected_commands

    def test_templates_are_processed(self, tmp_path):
        from specify_cli.integrations.forge import ForgeIntegration
        forge = ForgeIntegration()
        m = IntegrationManifest("forge", tmp_path)
        forge.setup(tmp_path, m)
        commands_dir = tmp_path / ".forge" / "commands"
        for cmd_file in commands_dir.glob("speckit.*.md"):
            content = cmd_file.read_text(encoding="utf-8")
            # Check standard replacements
            assert "{SCRIPT}" not in content, f"{cmd_file.name} has unprocessed {{SCRIPT}}"
            assert "__AGENT__" not in content, f"{cmd_file.name} has unprocessed __AGENT__"
            assert "{ARGS}" not in content, f"{cmd_file.name} has unprocessed {{ARGS}}"
            # Check Forge-specific: $ARGUMENTS should be replaced with {{parameters}}
            assert "$ARGUMENTS" not in content, f"{cmd_file.name} has unprocessed $ARGUMENTS"
            # Frontmatter sections should be stripped
            assert "\nscripts:\n" not in content
            assert "\nagent_scripts:\n" not in content

    def test_forge_specific_transformations(self, tmp_path):
        """Test Forge-specific processing: name injection and handoffs stripping."""
        from specify_cli.integrations.forge import ForgeIntegration
        forge = ForgeIntegration()
        m = IntegrationManifest("forge", tmp_path)
        forge.setup(tmp_path, m)
        commands_dir = tmp_path / ".forge" / "commands"

        for cmd_file in commands_dir.glob("speckit.*.md"):
            content = cmd_file.read_text(encoding="utf-8")

            # Check that name field is injected in frontmatter
            assert "\nname: " in content, f"{cmd_file.name} missing injected 'name' field"

            # Check that handoffs frontmatter key is stripped
            assert "\nhandoffs:" not in content, f"{cmd_file.name} has unstripped 'handoffs' key"

    def test_uses_parameters_placeholder(self, tmp_path):
        """Verify Forge replaces $ARGUMENTS with {{parameters}} in generated files."""
        from specify_cli.integrations.forge import ForgeIntegration
        forge = ForgeIntegration()

        # The registrar_config should specify {{parameters}}
        assert forge.registrar_config["args"] == "{{parameters}}"

        # Generate files and verify $ARGUMENTS is replaced with {{parameters}}
        from specify_cli.integrations.manifest import IntegrationManifest
        m = IntegrationManifest("forge", tmp_path)
        forge.setup(tmp_path, m)
        commands_dir = tmp_path / ".forge" / "commands"

        # Check all generated command files
        for cmd_file in commands_dir.glob("speckit.*.md"):
            content = cmd_file.read_text(encoding="utf-8")
            # $ARGUMENTS should be replaced with {{parameters}}
            assert "$ARGUMENTS" not in content, (
                f"{cmd_file.name} still contains $ARGUMENTS - it should be replaced with {{{{parameters}}}}"
            )
            # At least some files should have {{parameters}} (those with user input sections)
            # We'll check the checklist file specifically as it has a User Input section

        # Verify checklist specifically has {{parameters}} in the User Input section
        checklist = commands_dir / "speckit.checklist.md"
        if checklist.exists():
            content = checklist.read_text(encoding="utf-8")
            assert "{{parameters}}" in content, (
                "checklist should contain {{parameters}} in User Input section"
            )

    def test_name_field_uses_hyphenated_format(self, tmp_path):
        """Verify that injected name fields use hyphenated format (speckit-plan, not speckit.plan)."""
        from specify_cli.integrations.forge import ForgeIntegration
        forge = ForgeIntegration()
        m = IntegrationManifest("forge", tmp_path)
        forge.setup(tmp_path, m)
        commands_dir = tmp_path / ".forge" / "commands"

        # Check that name fields use hyphenated format
        for cmd_file in commands_dir.glob("speckit.*.md"):
            content = cmd_file.read_text(encoding="utf-8")
            # Extract the name field from frontmatter
            import re
            name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
            if name_match:
                name_value = name_match.group(1).strip()
                # Name should use hyphens, not dots
                assert "." not in name_value, (
                    f"{cmd_file.name} has name field with dots: {name_value} "
                    f"(should use hyphens for Forge/ZSH compatibility)"
                )
                assert name_value.startswith("speckit-"), (
                    f"{cmd_file.name} name field should start with 'speckit-': {name_value}"
                )


class TestForgeCommandRegistrar:
    """Test CommandRegistrar's Forge-specific name formatting."""

    def test_registrar_formats_extension_command_names_for_forge(self, tmp_path):
        """Verify CommandRegistrar converts dot notation to hyphens for Forge."""
        from specify_cli.agents import CommandRegistrar
        
        # Create a mock extension command file
        ext_dir = tmp_path / "extension"
        ext_dir.mkdir()
        cmd_dir = ext_dir / "commands"
        cmd_dir.mkdir()
        
        # Create a test command with dot notation name
        cmd_file = cmd_dir / "example.md"
        cmd_file.write_text(
            "---\n"
            "description: Test extension command\n"
            "---\n\n"
            "Test content with $ARGUMENTS\n",
            encoding="utf-8"
        )
        
        # Register with Forge
        registrar = CommandRegistrar()
        commands = [
            {
                "name": "speckit.my-extension.example",
                "file": "commands/example.md"
            }
        ]
        
        registered = registrar.register_commands(
            "forge",
            commands,
            "test-extension",
            ext_dir,
            tmp_path
        )
        
        # Verify registration succeeded
        assert "speckit.my-extension.example" in registered
        
        # Check the generated file has hyphenated name in frontmatter
        forge_cmd = tmp_path / ".forge" / "commands" / "speckit.my-extension.example.md"
        assert forge_cmd.exists()
        
        content = forge_cmd.read_text(encoding="utf-8")
        # Name field should use hyphens, not dots
        assert "name: speckit-my-extension-example" in content
        assert "name: speckit.my-extension.example" not in content

    def test_registrar_formats_alias_names_for_forge(self, tmp_path):
        """Verify CommandRegistrar converts alias names to hyphens for Forge."""
        from specify_cli.agents import CommandRegistrar
        
        # Create a mock extension command file
        ext_dir = tmp_path / "extension"
        ext_dir.mkdir()
        cmd_dir = ext_dir / "commands"
        cmd_dir.mkdir()
        
        cmd_file = cmd_dir / "example.md"
        cmd_file.write_text(
            "---\n"
            "description: Test command with alias\n"
            "---\n\n"
            "Test content\n",
            encoding="utf-8"
        )
        
        # Register with Forge including an alias
        registrar = CommandRegistrar()
        commands = [
            {
                "name": "speckit.my-extension.example",
                "file": "commands/example.md",
                "aliases": ["speckit.my-extension.ex"]
            }
        ]
        
        registrar.register_commands(
            "forge",
            commands,
            "test-extension",
            ext_dir,
            tmp_path
        )
        
        # Check the alias file has hyphenated name in frontmatter
        alias_file = tmp_path / ".forge" / "commands" / "speckit.my-extension.ex.md"
        assert alias_file.exists()
        
        content = alias_file.read_text(encoding="utf-8")
        # Alias name field should also use hyphens
        assert "name: speckit-my-extension-ex" in content
        assert "name: speckit.my-extension.ex" not in content

    def test_registrar_does_not_affect_other_agents(self, tmp_path):
        """Verify other agents still use dot notation (not affected by Forge formatter)."""
        from specify_cli.agents import CommandRegistrar
        
        # Create a mock extension command file
        ext_dir = tmp_path / "extension"
        ext_dir.mkdir()
        cmd_dir = ext_dir / "commands"
        cmd_dir.mkdir()
        
        cmd_file = cmd_dir / "example.md"
        cmd_file.write_text(
            "---\n"
            "description: Test command\n"
            "---\n\n"
            "Test content with $ARGUMENTS\n",
            encoding="utf-8"
        )
        
        # Register with Claude (uses dot notation)
        registrar = CommandRegistrar()
        commands = [
            {
                "name": "speckit.my-extension.example",
                "file": "commands/example.md"
            }
        ]
        
        registrar.register_commands(
            "claude",
            commands,
            "test-extension",
            ext_dir,
            tmp_path
        )
        
        # Claude uses skills format (hyphenated directory names)
        # but doesn't inject frontmatter names
        skill_dir = tmp_path / ".claude" / "skills" / "speckit-my-extension-example"
        assert skill_dir.exists()
        
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        # Claude skills should have hyphenated name in metadata
        assert "name: speckit-my-extension-example" in content
