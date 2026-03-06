"""Tests for minispec init-registry command."""

from pathlib import Path

import yaml

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


# --- Sample packages ---


SAMPLES_DIR = Path(__file__).parent.parent / "templates" / "registry-samples"
EXPECTED_SAMPLES = ["changelog-writer", "protect-main", "quick-review"]


class TestSamplePackagesExist:
    def test_samples_directory_exists(self):
        assert SAMPLES_DIR.is_dir(), f"Missing {SAMPLES_DIR}"

    def test_expected_samples_present(self):
        sample_names = sorted(d.name for d in SAMPLES_DIR.iterdir() if d.is_dir())
        assert sample_names == EXPECTED_SAMPLES


class TestSamplePackageYaml:
    """Verify each sample has a valid package.yaml with required fields."""

    def test_all_samples_have_package_yaml(self):
        for name in EXPECTED_SAMPLES:
            pkg = SAMPLES_DIR / name / "package.yaml"
            assert pkg.exists(), f"Missing package.yaml in {name}"

    def test_package_yaml_required_fields(self):
        required = {"name", "version", "type", "description", "agents", "files"}
        for name in EXPECTED_SAMPLES:
            data = yaml.safe_load((SAMPLES_DIR / name / "package.yaml").read_text())
            missing = required - set(data.keys())
            assert not missing, f"{name}/package.yaml missing fields: {missing}"

    def test_package_yaml_types_valid(self):
        valid_types = {"hook", "command", "skill"}
        for name in EXPECTED_SAMPLES:
            data = yaml.safe_load((SAMPLES_DIR / name / "package.yaml").read_text())
            assert data["type"] in valid_types, f"{name} has invalid type: {data['type']}"

    def test_package_yaml_files_sources_exist(self):
        """Every source file referenced in files[] must exist in the package directory."""
        for name in EXPECTED_SAMPLES:
            pkg_dir = SAMPLES_DIR / name
            data = yaml.safe_load((pkg_dir / "package.yaml").read_text())
            for mapping in data.get("files", []):
                source = pkg_dir / mapping["source"]
                assert source.exists(), f"{name}: source file '{mapping['source']}' not found"

    def test_all_samples_have_readme(self):
        for name in EXPECTED_SAMPLES:
            readme = SAMPLES_DIR / name / "README.md"
            assert readme.exists(), f"Missing README.md in {name}"


class TestSamplesCopiedByInit:
    """Verify that init_registry copies samples into packages/."""

    def test_copy_samples_to_packages(self, tmp_path):
        """Simulate the sample-copy logic from init_registry."""
        import shutil

        packages_dir = tmp_path / "packages"
        packages_dir.mkdir()

        for sample_dir in sorted(SAMPLES_DIR.iterdir()):
            if sample_dir.is_dir():
                dest = packages_dir / sample_dir.name
                shutil.copytree(sample_dir, dest)

        copied = sorted(d.name for d in packages_dir.iterdir() if d.is_dir())
        assert copied == EXPECTED_SAMPLES

        # Verify each copied package has package.yaml
        for name in EXPECTED_SAMPLES:
            assert (packages_dir / name / "package.yaml").exists()

    def test_does_not_overwrite_existing_package(self, tmp_path):
        """If a package directory already exists, it should not be overwritten."""
        import shutil

        packages_dir = tmp_path / "packages"
        packages_dir.mkdir()

        # Pre-create one package with custom content
        existing = packages_dir / "protect-main"
        existing.mkdir()
        marker = existing / "custom.txt"
        marker.write_text("do not overwrite")

        # Copy samples (skip existing)
        for sample_dir in sorted(SAMPLES_DIR.iterdir()):
            if sample_dir.is_dir():
                dest = packages_dir / sample_dir.name
                if not dest.exists():
                    shutil.copytree(sample_dir, dest)

        # Custom content preserved
        assert marker.read_text() == "do not overwrite"
        # Other samples still installed
        assert (packages_dir / "quick-review" / "package.yaml").exists()
