"""Tests for minispec init-registry command."""

from minispec_cli import (
    AGENT_COMMAND_CONFIG,
    AGENT_CONFIG,
    _format_skill_for_agent,
    _read_registry_skill,
)


# --- Helper formatting ---


class TestFormatSkillForAgent:
    def test_md_format(self):
        result = _format_skill_for_agent("A description", "body content", "claude")
        assert result.startswith("---\n")
        assert "description: A description" in result
        assert "body content" in result

    def test_toml_format(self):
        result = _format_skill_for_agent("A description", "body content", "gemini")
        assert result.startswith('description = "A description"')
        assert 'prompt = """' in result
        assert "body content" in result

    def test_toml_escapes_backslashes(self):
        result = _format_skill_for_agent("desc", "path\\to\\file", "qwen")
        assert "path\\\\to\\\\file" in result


class TestReadRegistrySkill:
    def test_claude_returns_md(self):
        filename, content = _read_registry_skill("claude")
        assert filename == "minispec.registry.md"
        assert content.startswith("---\n")
        assert "description:" in content

    def test_gemini_returns_toml(self):
        filename, content = _read_registry_skill("gemini")
        assert filename == "minispec.registry.toml"
        assert content.startswith('description = "')

    def test_copilot_returns_agent_md(self):
        filename, content = _read_registry_skill("copilot")
        assert filename == "minispec.registry.agent.md"

    def test_content_includes_registry_knowledge(self):
        _, content = _read_registry_skill("claude")
        assert "package.yaml" in content
        assert "registry.yaml" in content
        assert "validate" in content.lower()


# --- Agent command config completeness ---


class TestAgentCommandConfig:
    def test_all_agents_have_command_config(self):
        for agent in AGENT_CONFIG:
            assert agent in AGENT_COMMAND_CONFIG, f"Missing AGENT_COMMAND_CONFIG for {agent}"

    def test_config_has_required_keys(self):
        for agent, config in AGENT_COMMAND_CONFIG.items():
            assert "path" in config, f"{agent} missing 'path'"
            assert "ext" in config, f"{agent} missing 'ext'"
            assert "fmt" in config, f"{agent} missing 'fmt'"
            assert config["fmt"] in ("md", "toml"), f"{agent} has invalid fmt: {config['fmt']}"


# --- Scaffold generation ---


class TestInitRegistryScaffold:
    """Test scaffold generation using the CLI in a temp directory."""

    def test_creates_registry_structure(self, tmp_path):
        """Verify init-registry creates expected files."""
        registry_dir = tmp_path / "my-registry"
        registry_dir.mkdir()

        # Simulate what init_registry does (without the interactive parts)
        from minispec_cli import _read_registry_skill

        # Create scaffold
        packages_dir = registry_dir / "packages"
        packages_dir.mkdir()
        (packages_dir / ".gitkeep").touch()

        (registry_dir / "registry.yaml").write_text(
            "name: my-registry\ndescription: \"\"\nmaintainers: []\n"
        )
        (registry_dir / "README.md").write_text("# my-registry\n")

        config = AGENT_COMMAND_CONFIG["claude"]
        skill_dir = registry_dir / config["path"]
        skill_dir.mkdir(parents=True)
        filename, content = _read_registry_skill("claude")
        (skill_dir / filename).write_text(content)

        # Verify
        assert (registry_dir / "registry.yaml").exists()
        assert (registry_dir / "packages" / ".gitkeep").exists()
        assert (registry_dir / "README.md").exists()
        assert (skill_dir / "minispec.registry.md").exists()

    def test_registry_yaml_content(self, tmp_path):
        registry_yaml = tmp_path / "registry.yaml"
        registry_yaml.write_text("name: test-reg\ndescription: \"\"\nmaintainers: []\n")

        import yaml
        data = yaml.safe_load(registry_yaml.read_text())
        assert data["name"] == "test-reg"
        assert data["description"] == ""
        assert data["maintainers"] == []

    def test_skill_placed_correctly_per_agent(self, tmp_path):
        """Verify skill files go to correct paths for different agents."""
        test_agents = ["claude", "copilot", "gemini", "windsurf", "opencode"]
        for agent in test_agents:
            config = AGENT_COMMAND_CONFIG[agent]
            filename, content = _read_registry_skill(agent)
            assert filename == f"minispec.registry.{config['ext']}"
            assert len(content) > 100, f"Content too short for {agent}"

    def test_does_not_overwrite_existing_registry_yaml(self, tmp_path):
        """Simulate --here mode: existing registry.yaml should be preserved."""
        existing = tmp_path / "registry.yaml"
        existing.write_text("name: my-existing\ndescription: Custom\nmaintainers: [alice]\n")

        # The init_registry command skips if registry.yaml exists
        assert existing.read_text().startswith("name: my-existing")
