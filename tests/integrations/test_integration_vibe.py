"""Tests for VibeIntegration."""

import yaml

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


class TestVibeIntegration(SkillsIntegrationTests):
    KEY = "vibe"
    FOLDER = ".vibe/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".vibe/skills"
    CONTEXT_FILE = "AGENTS.md"


class TestVibeUserInvocable:
    def test_all_skills_have_user_invocable(self, tmp_path):
        i = get_integration("vibe")
        m = IntegrationManifest("vibe", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert skill_files
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            assert content.startswith("---"), (
                f"{f.parent.name}/SKILL.md is missing the opening frontmatter delimiter '---'"
            )
            parts = content.split("---", 2)
            assert len(parts) >= 3, (
                f"{f.parent.name}/SKILL.md has malformed frontmatter; expected a '--- ... ---' block"
            )
            parsed = yaml.safe_load(parts[1])
            assert parsed.get("user-invocable") is True, (
                f"{f.parent.name}/SKILL.md is missing user-invocable: true in frontmatter"
            )