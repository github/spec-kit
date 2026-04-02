"""Tests for ForgeIntegration."""

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest


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
        command_files = sorted(commands_dir.glob("speckit.*.md"))
        assert len(command_files) == 9
        expected_commands = {
            "analyze", "checklist", "clarify", "constitution",
            "implement", "plan", "specify", "tasks", "taskstoissues",
        }
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
            # Note: $ARGUMENTS may appear in template content (examples, instructions)
            # The placeholder that gets replaced is {ARGS}, not $ARGUMENTS
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
        """Verify Forge config specifies {{parameters}} as the args placeholder."""
        from specify_cli.integrations.forge import ForgeIntegration
        forge = ForgeIntegration()
        # The registrar_config should specify {{parameters}}
        assert forge.registrar_config["args"] == "{{parameters}}"
        
        # When process_template is called, it should replace {ARGS} with {{parameters}}
        # Note: $ARGUMENTS in template content is intentional (examples/instructions)
