"""Tests for issues raised in PR #2103 code review.

Covers six bugs found by Copilot inline review:
  Issue 1 — Copilot execution:isolated never gets mode:agent injected; behavior/agents keys leak
  Issue 2 — Non-dict behavior in source file bypasses manifest-level agent-deployment skip
  Issue 3 — SkillsIntegration.setup() ignores agents: escape-hatch overrides
  Issue 4 — _behavior_overridable clobbers explicit source frontmatter (model, context, etc.)
  Issue 5 — extensions.py _register_extension_skills reads source file twice per iteration
    Issue 6 — Extension skill rendering drops merged behavior/source frontmatter in output
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from specify_cli.extensions import CommandRegistrar


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ext_dir(base: Path, ext_id: str, commands: list[dict]) -> Path:
    """Create a minimal installed extension directory."""
    import yaml

    ext_dir = base / ext_id
    ext_dir.mkdir(parents=True)

    manifest_data = {
        "schema_version": "1.0",
        "extension": {
            "id": ext_id,
            "name": ext_id,
            "version": "1.0.0",
            "description": "Test extension",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {"commands": [c for c in commands]},
    }
    (ext_dir / "extension.yml").write_text(yaml.dump(manifest_data))
    (ext_dir / "commands").mkdir()
    return ext_dir


def _make_project(base: Path, ai: str = "codex", ai_skills: bool = False) -> Path:
    """Create a minimal spec-kit project directory."""
    proj = base / "project"
    proj.mkdir()
    (proj / ".specify").mkdir()

    init_opts: dict = {"ai": ai}
    if ai_skills:
        init_opts["ai_skills"] = True
    (proj / ".specify" / "init-options.json").write_text(json.dumps(init_opts))

    return proj


def _parse_frontmatter(text: str) -> dict:
    import yaml

    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


# ---------------------------------------------------------------------------
# Issue 1 — Copilot execution:isolated does not produce mode:agent
# ---------------------------------------------------------------------------

class TestCopilotExecutionIsolated:
    """Issue 1: behavior.execution=isolated must inject mode:agent for Copilot."""

    @pytest.fixture
    def tmp(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def _copilot_ext(self, tmp: Path, body_frontmatter: str) -> tuple[Path, Path]:
        ext_dir = _make_ext_dir(tmp, "ext-cop", [
            {"name": "speckit.ext-cop.cmd", "file": "commands/cmd.md"}
        ])
        (ext_dir / "commands" / "cmd.md").write_text(
            f"{body_frontmatter}\n\nCommand body."
        )
        proj = tmp / "proj"
        proj.mkdir()
        (proj / ".github" / "agents").mkdir(parents=True)
        return ext_dir, proj

    def test_execution_isolated_produces_mode_agent(self, tmp):
        """execution:isolated must inject mode:agent into Copilot .agent.md."""
        fm = "---\ndescription: Test cmd\nbehavior:\n  execution: isolated\n---"
        ext_dir, proj = self._copilot_ext(tmp, fm)

        from specify_cli.extensions import ExtensionManifest
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("copilot", manifest, ext_dir, proj)

        agent_file = proj / ".github" / "agents" / "speckit.ext-cop.cmd.agent.md"
        assert agent_file.exists(), "agent file not created"
        content = agent_file.read_text()
        parsed = _parse_frontmatter(content)
        assert parsed.get("mode") == "agent", (
            f"expected mode:agent in frontmatter, got: {parsed}"
        )

    def test_execution_isolated_strips_behavior_key(self, tmp):
        """behavior: key must not appear in generated Copilot .agent.md."""
        fm = "---\ndescription: Test cmd\nbehavior:\n  execution: isolated\n---"
        ext_dir, proj = self._copilot_ext(tmp, fm)

        from specify_cli.extensions import ExtensionManifest
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("copilot", manifest, ext_dir, proj)

        content = (proj / ".github" / "agents" / "speckit.ext-cop.cmd.agent.md").read_text()
        parsed = _parse_frontmatter(content)
        assert "behavior" not in parsed, f"behavior: key leaked into output: {parsed}"

    def test_execution_isolated_strips_agents_key(self, tmp):
        """agents: key must not appear in generated Copilot .agent.md."""
        fm = (
            "---\ndescription: Test cmd\n"
            "behavior:\n  execution: isolated\n"
            "agents:\n  copilot:\n    handoffs: []\n---"
        )
        ext_dir, proj = self._copilot_ext(tmp, fm)

        from specify_cli.extensions import ExtensionManifest
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("copilot", manifest, ext_dir, proj)

        content = (proj / ".github" / "agents" / "speckit.ext-cop.cmd.agent.md").read_text()
        parsed = _parse_frontmatter(content)
        assert "agents" not in parsed, f"agents: key leaked into output: {parsed}"

    def test_execution_agent_still_works(self, tmp):
        """Regression: execution:agent must still produce mode:agent."""
        fm = "---\ndescription: Test cmd\nbehavior:\n  execution: agent\n---"
        ext_dir, proj = self._copilot_ext(tmp, fm)

        from specify_cli.extensions import ExtensionManifest
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("copilot", manifest, ext_dir, proj)

        agent_file = proj / ".github" / "agents" / "speckit.ext-cop.cmd.agent.md"
        assert agent_file.exists()
        parsed = _parse_frontmatter(agent_file.read_text())
        assert parsed.get("mode") == "agent"

    def test_no_behavior_dict_uses_raw_frontmatter(self, tmp):
        """No behavior → output frontmatter identical to source (minus behavior/agents)."""
        fm = "---\ndescription: Plain cmd\nmodel: claude-opus-4-6\n---"
        ext_dir, proj = self._copilot_ext(tmp, fm)

        from specify_cli.extensions import ExtensionManifest
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("copilot", manifest, ext_dir, proj)

        agent_file = proj / ".github" / "agents" / "speckit.ext-cop.cmd.agent.md"
        assert agent_file.exists()
        parsed = _parse_frontmatter(agent_file.read_text())
        assert "mode" not in parsed, "mode injected without behavior dict"

    def test_agents_override_applied_for_isolated(self, tmp):
        """agents: escape-hatch overrides must be applied for execution:isolated."""
        fm = (
            "---\ndescription: Test cmd\n"
            "behavior:\n  execution: isolated\n"
            "agents:\n  copilot:\n    priority: 5\n---"
        )
        ext_dir, proj = self._copilot_ext(tmp, fm)

        from specify_cli.extensions import ExtensionManifest
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("copilot", manifest, ext_dir, proj)

        agent_file = proj / ".github" / "agents" / "speckit.ext-cop.cmd.agent.md"
        content = agent_file.read_text()
        parsed = _parse_frontmatter(content)
        assert parsed.get("mode") == "agent"
        assert parsed.get("priority") == 5, f"agents: override not applied: {parsed}"

    def test_behavior_command_execution_no_mode_injected(self, tmp):
        """execution:command must NOT inject mode into Copilot output."""
        fm = "---\ndescription: Test cmd\nbehavior:\n  execution: command\n---"
        ext_dir, proj = self._copilot_ext(tmp, fm)

        from specify_cli.extensions import ExtensionManifest
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("copilot", manifest, ext_dir, proj)

        agent_file = proj / ".github" / "agents" / "speckit.ext-cop.cmd.agent.md"
        assert agent_file.exists()
        parsed = _parse_frontmatter(agent_file.read_text())
        assert "mode" not in parsed, f"mode injected for execution:command: {parsed}"


# ---------------------------------------------------------------------------
# Issue 2 — Non-dict behavior in source file bypasses agent-deployment skip
# ---------------------------------------------------------------------------

class TestExtensionSkillNonDictBehaviorMerge:
    """Issue 2: non-dict/empty behavior in source file must not block manifest merge."""

    @pytest.fixture
    def tmp(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def _setup(self, tmp: Path, source_behavior_yaml: str, manifest_behavior: dict | None = None) -> tuple[Path, Path]:
        """Create ext + project with ai=codex+ai_skills, command has given behavior in source."""
        cmd_manifest_entry: dict = {"name": "speckit.ext2.cmd", "file": "commands/cmd.md"}
        if manifest_behavior is not None:
            cmd_manifest_entry["behavior"] = manifest_behavior

        ext_dir = _make_ext_dir(tmp, "ext2", [cmd_manifest_entry])

        cmd_content = f"---\ndescription: Test\n{source_behavior_yaml}---\n\nBody"
        (ext_dir / "commands" / "cmd.md").write_text(cmd_content)

        proj = _make_project(tmp, ai="codex", ai_skills=True)
        skills_dir = proj / ".agents" / "skills"
        skills_dir.mkdir(parents=True)
        return ext_dir, proj

    def test_string_behavior_in_source_allows_manifest_agent_skip(self, tmp):
        """Source behavior: 'string' + manifest execution:agent → command skipped (not written as skill)."""
        ext_dir, proj = self._setup(
            tmp,
            source_behavior_yaml="behavior: invalid-string\n",
            manifest_behavior={"execution": "agent"},
        )

        from specify_cli.extensions import ExtensionManifest, ExtensionManager
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        mgr = ExtensionManager(proj)
        skills = mgr._register_extension_skills(manifest, ext_dir)

        skill_file = proj / ".agents" / "skills" / "speckit-ext2-cmd" / "SKILL.md"
        assert not skill_file.exists(), (
            "skill was written for a command that should be deployed as an agent definition"
        )
        assert skills == [], f"expected empty skills list, got: {skills}"

    def test_null_behavior_in_source_allows_manifest_agent_skip(self, tmp):
        """Source behavior: null + manifest execution:agent → command skipped."""
        ext_dir, proj = self._setup(
            tmp,
            source_behavior_yaml="behavior: null\n",
            manifest_behavior={"execution": "agent"},
        )

        from specify_cli.extensions import ExtensionManifest, ExtensionManager
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        mgr = ExtensionManager(proj)
        skills = mgr._register_extension_skills(manifest, ext_dir)

        skill_file = proj / ".agents" / "skills" / "speckit-ext2-cmd" / "SKILL.md"
        assert not skill_file.exists()

    def test_empty_dict_behavior_in_source_allows_manifest_agent_skip(self, tmp):
        """Source behavior: {} + manifest execution:agent → command skipped."""
        ext_dir, proj = self._setup(
            tmp,
            source_behavior_yaml="behavior: {}\n",
            manifest_behavior={"execution": "agent"},
        )

        from specify_cli.extensions import ExtensionManifest, ExtensionManager
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        mgr = ExtensionManager(proj)
        skills = mgr._register_extension_skills(manifest, ext_dir)

        skill_file = proj / ".agents" / "skills" / "speckit-ext2-cmd" / "SKILL.md"
        assert not skill_file.exists()

    def test_list_behavior_in_source_allows_manifest_agent_skip(self, tmp):
        """Source behavior: [list] + manifest execution:agent → command skipped."""
        ext_dir, proj = self._setup(
            tmp,
            source_behavior_yaml="behavior:\n  - item1\n  - item2\n",
            manifest_behavior={"execution": "agent"},
        )

        from specify_cli.extensions import ExtensionManifest, ExtensionManager
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        mgr = ExtensionManager(proj)
        skills = mgr._register_extension_skills(manifest, ext_dir)

        skill_file = proj / ".agents" / "skills" / "speckit-ext2-cmd" / "SKILL.md"
        assert not skill_file.exists()

    def test_valid_behavior_in_source_blocks_manifest_merge(self, tmp):
        """Source has valid behavior dict → manifest behavior not merged (source wins)."""
        ext_dir, proj = self._setup(
            tmp,
            source_behavior_yaml="behavior:\n  execution: isolated\n",
            manifest_behavior={"execution": "agent"},
        )

        from specify_cli.extensions import ExtensionManifest, ExtensionManager
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        mgr = ExtensionManager(proj)
        skills = mgr._register_extension_skills(manifest, ext_dir)

        # execution:isolated → NOT agent-type → skill IS written
        skill_file = proj / ".agents" / "skills" / "speckit-ext2-cmd" / "SKILL.md"
        assert skill_file.exists(), "skill should be written when source behavior is not execution:agent"

    def test_no_behavior_no_manifest_behavior_writes_skill(self, tmp):
        """No behavior anywhere → normal skill is written."""
        ext_dir, proj = self._setup(tmp, source_behavior_yaml="")

        from specify_cli.extensions import ExtensionManifest, ExtensionManager
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        mgr = ExtensionManager(proj)
        mgr._register_extension_skills(manifest, ext_dir)

        skill_file = proj / ".agents" / "skills" / "speckit-ext2-cmd" / "SKILL.md"
        assert skill_file.exists()


class TestExtensionSkillFrontmatterPropagation:
    """Issue 6: extension skill rendering must preserve merged source frontmatter."""

    @pytest.fixture
    def tmp(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_manifest_behavior_is_applied_to_skill_frontmatter(self, tmp):
        """Manifest-level behavior must affect generated SKILL.md frontmatter."""
        ext_dir = _make_ext_dir(tmp, "ext3", [{
            "name": "speckit.ext3.cmd",
            "file": "commands/cmd.md",
            "behavior": {"invocation": "automatic"},
        }])
        (ext_dir / "commands" / "cmd.md").write_text(
            "---\n"
            "description: Test\n"
            "---\n\n"
            "Body"
        )

        proj = _make_project(tmp, ai="claude", ai_skills=True)
        (proj / ".claude" / "skills").mkdir(parents=True)

        from specify_cli.extensions import ExtensionManifest, ExtensionManager

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        mgr = ExtensionManager(proj)
        created = mgr._register_extension_skills(manifest, ext_dir)
        assert created == ["speckit-ext3-cmd"]

        skill_file = proj / ".claude" / "skills" / "speckit-ext3-cmd" / "SKILL.md"
        parsed = _parse_frontmatter(skill_file.read_text())
        assert parsed.get("disable-model-invocation") is False, parsed

    def test_source_frontmatter_passthrough_is_preserved(self, tmp):
        """Passthrough keys like model must be preserved in generated SKILL.md."""
        ext_dir = _make_ext_dir(tmp, "ext4", [{
            "name": "speckit.ext4.cmd",
            "file": "commands/cmd.md",
        }])
        (ext_dir / "commands" / "cmd.md").write_text(
            "---\n"
            "description: Test\n"
            "model: claude-opus-4-6\n"
            "---\n\n"
            "Body"
        )

        proj = _make_project(tmp, ai="claude", ai_skills=True)
        (proj / ".claude" / "skills").mkdir(parents=True)

        from specify_cli.extensions import ExtensionManifest, ExtensionManager

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        mgr = ExtensionManager(proj)
        mgr._register_extension_skills(manifest, ext_dir)

        skill_file = proj / ".claude" / "skills" / "speckit-ext4-cmd" / "SKILL.md"
        parsed = _parse_frontmatter(skill_file.read_text())
        assert parsed.get("model") == "claude-opus-4-6", parsed


# ---------------------------------------------------------------------------
# Issue 3 — SkillsIntegration.setup() ignores agents: override
# ---------------------------------------------------------------------------

class TestSkillsIntegrationAgentsOverride:
    """Issue 3: agents: escape-hatch in template frontmatter must reach translate_behavior."""

    @pytest.fixture
    def tmp(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def _find_skill_files(self, tmp_path: Path) -> list[Path]:
        return list(tmp_path.rglob("SKILL.md"))

    def test_agents_override_applied_in_skills_integration(self, tmp):
        """agents: {<key>: {...}} escape-hatch must appear in generated SKILL.md."""
        from specify_cli.integrations import get_integration
        from specify_cli.integrations.manifest import IntegrationManifest

        templates_dir = (
            Path(__file__).resolve().parent.parent / "templates" / "commands"
        )
        if not templates_dir.is_dir():
            pytest.skip("templates/commands not available")

        # Patch one template to include behavior + agents override
        src_template = next(iter(templates_dir.glob("*.md")), None)
        if src_template is None:
            pytest.skip("no template files found")

        original = src_template.read_text()
        patched = (
            "---\n"
            "description: Test patched template\n"
            "behavior:\n"
            "  invocation: automatic\n"
            "agents:\n"
            "  codex:\n"
            "    effort: max\n"
            "---\n" + original.split("---", 2)[-1] if "---" in original else original
        )

        patched_dir = tmp / "patched_templates"
        patched_dir.mkdir()
        (patched_dir / src_template.name).write_text(patched)

        integration = get_integration("codex")
        if integration is None:
            pytest.skip("codex integration not registered")

        m = IntegrationManifest("codex", tmp)

        with patch.object(type(integration), "list_command_templates", return_value=list(patched_dir.glob("*.md"))):
            created = integration.setup(tmp, m)

        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert len(skill_files) > 0, "no SKILL.md files created"

        for sf in skill_files:
            content = sf.read_text()
            parsed = _parse_frontmatter(content)
            # The agents: override for codex sets effort: max
            assert parsed.get("effort") == "max", (
                f"agents: override not applied; got frontmatter: {parsed}"
            )

    def test_agents_override_without_behavior_is_applied(self, tmp):
        """agents-only template frontmatter must still apply for the target agent."""
        from specify_cli.integrations import get_integration
        from specify_cli.integrations.manifest import IntegrationManifest

        templates_dir = (
            Path(__file__).resolve().parent.parent / "templates" / "commands"
        )
        if not templates_dir.is_dir():
            pytest.skip("templates/commands not available")

        src_template = next(iter(templates_dir.glob("*.md")), None)
        if src_template is None:
            pytest.skip("no template files found")

        original = src_template.read_text()
        patched = (
            "---\n"
            "description: Test patched template\n"
            "agents:\n"
            "  codex:\n"
            "    effort: max\n"
            "---\n" + original.split("---", 2)[-1] if "---" in original else original
        )

        patched_dir = tmp / "patched_templates_agents_only"
        patched_dir.mkdir()
        (patched_dir / src_template.name).write_text(patched)

        integration = get_integration("codex")
        if integration is None:
            pytest.skip("codex integration not registered")

        m = IntegrationManifest("codex", tmp)
        with patch.object(type(integration), "list_command_templates", return_value=list(patched_dir.glob("*.md"))):
            created = integration.setup(tmp, m)

        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert skill_files, "no SKILL.md files created"
        for sf in skill_files:
            parsed = _parse_frontmatter(sf.read_text())
            assert parsed.get("effort") == "max", parsed

    def test_agents_override_for_other_agent_not_applied(self, tmp):
        """agents: override for a different agent must not bleed into codex output."""
        from specify_cli.integrations import get_integration
        from specify_cli.integrations.manifest import IntegrationManifest

        templates_dir = (
            Path(__file__).resolve().parent.parent / "templates" / "commands"
        )
        if not templates_dir.is_dir():
            pytest.skip("templates/commands not available")

        src_template = next(iter(templates_dir.glob("*.md")), None)
        if src_template is None:
            pytest.skip("no template files found")

        patched = (
            "---\n"
            "description: Test patched template\n"
            "behavior:\n"
            "  invocation: automatic\n"
            "agents:\n"
            "  claude:\n"
            "    effort: max\n"  # override for claude, NOT codex
            "---\n" + src_template.read_text().split("---", 2)[-1]
            if "---" in src_template.read_text()
            else src_template.read_text()
        )

        patched_dir = tmp / "patched_templates2"
        patched_dir.mkdir()
        (patched_dir / src_template.name).write_text(patched)

        integration = get_integration("codex")
        if integration is None:
            pytest.skip("codex integration not registered")

        m = IntegrationManifest("codex", tmp)

        with patch.object(type(integration), "list_command_templates", return_value=list(patched_dir.glob("*.md"))):
            created = integration.setup(tmp, m)

        skill_files = [f for f in created if f.name == "SKILL.md"]
        for sf in skill_files:
            parsed = _parse_frontmatter(sf.read_text())
            assert parsed.get("effort") != "max", (
                f"claude-only agents: override bled into codex output: {parsed}"
            )

    def test_empty_agents_override_does_not_crash(self, tmp):
        """agents: {} in template frontmatter must not raise."""
        from specify_cli.integrations import get_integration
        from specify_cli.integrations.manifest import IntegrationManifest

        templates_dir = (
            Path(__file__).resolve().parent.parent / "templates" / "commands"
        )
        if not templates_dir.is_dir():
            pytest.skip("templates/commands not available")

        src_template = next(iter(templates_dir.glob("*.md")), None)
        if src_template is None:
            pytest.skip("no template files found")

        original_text = src_template.read_text()
        patched = (
            "---\ndescription: Test template\nbehavior:\n  invocation: automatic\nagents: {}\n---\n"
            + original_text.split("---", 2)[-1] if "---" in original_text else original_text
        )

        patched_dir = tmp / "patched_templates3"
        patched_dir.mkdir()
        (patched_dir / src_template.name).write_text(patched)

        integration = get_integration("codex")
        if integration is None:
            pytest.skip("codex integration not registered")

        m = IntegrationManifest("codex", tmp)

        with patch.object(type(integration), "list_command_templates", return_value=list(patched_dir.glob("*.md"))):
            created = integration.setup(tmp, m)  # must not raise

        assert len(created) > 0

    def test_agents_override_non_scalar_yaml_remains_valid(self, tmp):
        """Non-scalar override values must be emitted as valid YAML frontmatter."""
        from specify_cli.integrations import get_integration
        from specify_cli.integrations.manifest import IntegrationManifest

        templates_dir = (
            Path(__file__).resolve().parent.parent / "templates" / "commands"
        )
        if not templates_dir.is_dir():
            pytest.skip("templates/commands not available")

        src_template = next(iter(templates_dir.glob("*.md")), None)
        if src_template is None:
            pytest.skip("no template files found")

        original_text = src_template.read_text()
        patched = (
            "---\n"
            "description: Test template\n"
            "agents:\n"
            "  claude:\n"
            "    handoffs:\n"
            "      - label: Generate plan\n"
            "        agent: speckit.plan\n"
            "        send: true\n"
            "---\n"
            + original_text.split("---", 2)[-1]
            if "---" in original_text
            else original_text
        )

        patched_dir = tmp / "patched_templates4"
        patched_dir.mkdir()
        (patched_dir / src_template.name).write_text(patched)

        integration = get_integration("claude")
        if integration is None:
            pytest.skip("claude integration not registered")

        m = IntegrationManifest("claude", tmp)
        with patch.object(type(integration), "list_command_templates", return_value=list(patched_dir.glob("*.md"))):
            created = integration.setup(tmp, m)

        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert skill_files, "no SKILL.md files created"
        for sf in skill_files:
            parsed = _parse_frontmatter(sf.read_text())
            handoffs = parsed.get("handoffs")
            assert isinstance(handoffs, list), parsed
            assert handoffs[0].get("agent") == "speckit.plan", parsed


# ---------------------------------------------------------------------------
# Issue 4 — _behavior_overridable clobbers explicit source frontmatter
# ---------------------------------------------------------------------------

class TestBehaviorOverridableScope:
    """Issue 4: source frontmatter values for model/context/effort/agent/allowed-tools must win."""

    def _make_registrar_and_source_dir(self, tmp: Path):
        from specify_cli.agents import CommandRegistrar as AgentsRegistrar

        src_dir = tmp / "ext-src"
        src_dir.mkdir()
        (src_dir / "extension.yml").write_text("id: test-ext\n")
        return AgentsRegistrar(), src_dir

    @pytest.fixture
    def tmp(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_source_model_wins_over_behavior_capability(self, tmp):
        """Explicit model in source frontmatter must not be clobbered by behavior.capability."""
        registrar, src_dir = self._make_registrar_and_source_dir(tmp)

        frontmatter = {
            "description": "test",
            "model": "claude-opus-4-6",       # explicit — must survive
            "behavior": {"capability": "fast"},  # would inject claude-haiku-4-5-20251001
        }
        output = registrar.render_skill_command(
            "claude", "speckit-test", frontmatter, "Body", "test-ext",
            "commands/test.md", tmp, source_dir=src_dir,
        )
        parsed = _parse_frontmatter(output)
        assert parsed.get("model") == "claude-opus-4-6", (
            f"source model was clobbered by behavior.capability; got: {parsed.get('model')}"
        )

    def test_source_effort_wins_over_behavior_effort(self, tmp):
        """Explicit effort in source frontmatter must not be clobbered by behavior.effort."""
        registrar, src_dir = self._make_registrar_and_source_dir(tmp)

        frontmatter = {
            "description": "test",
            "effort": "max",             # explicit — must survive
            "behavior": {"effort": "low"},  # would inject low
        }
        output = registrar.render_skill_command(
            "claude", "speckit-test", frontmatter, "Body", "test-ext",
            "commands/test.md", tmp, source_dir=src_dir,
        )
        parsed = _parse_frontmatter(output)
        assert parsed.get("effort") == "max", (
            f"source effort was clobbered by behavior.effort; got: {parsed.get('effort')}"
        )

    def test_source_context_wins_over_behavior_execution(self, tmp):
        """Explicit context in source frontmatter must not be clobbered by behavior.execution."""
        registrar, src_dir = self._make_registrar_and_source_dir(tmp)

        frontmatter = {
            "description": "test",
            "context": "fork",              # explicit — must survive
            "behavior": {"execution": "command"},  # would produce no injection, but guards
        }
        output = registrar.render_skill_command(
            "claude", "speckit-test", frontmatter, "Body", "test-ext",
            "commands/test.md", tmp, source_dir=src_dir,
        )
        parsed = _parse_frontmatter(output)
        assert parsed.get("context") == "fork", (
            f"source context was clobbered; got: {parsed.get('context')}"
        )

    def test_source_allowed_tools_wins_over_behavior_tools(self, tmp):
        """Explicit allowed-tools in source must not be clobbered by behavior.tools."""
        registrar, src_dir = self._make_registrar_and_source_dir(tmp)

        frontmatter = {
            "description": "test",
            "allowed-tools": "Bash",          # explicit — must survive
            "behavior": {"tools": "read-only"},  # would inject Read Grep Glob
        }
        output = registrar.render_skill_command(
            "claude", "speckit-test", frontmatter, "Body", "test-ext",
            "commands/test.md", tmp, source_dir=src_dir,
        )
        parsed = _parse_frontmatter(output)
        assert parsed.get("allowed-tools") == "Bash", (
            f"source allowed-tools was clobbered; got: {parsed.get('allowed-tools')}"
        )

    def test_behavior_disable_model_invocation_can_override_default(self, tmp):
        """behavior.invocation:automatic must be able to set disable-model-invocation:false."""
        registrar, src_dir = self._make_registrar_and_source_dir(tmp)

        # Source has no explicit disable-model-invocation; behavior says automatic.
        # build_skill_frontmatter injects default True, behavior should override to False.
        frontmatter = {
            "description": "test",
            "behavior": {"invocation": "automatic"},
        }
        output = registrar.render_skill_command(
            "claude", "speckit-test", frontmatter, "Body", "test-ext",
            "commands/test.md", tmp, source_dir=src_dir,
        )
        parsed = _parse_frontmatter(output)
        assert parsed.get("disable-model-invocation") is False, (
            f"behavior.invocation:automatic did not override default; got: {parsed}"
        )

    def test_behavior_user_invocable_can_override_default(self, tmp):
        """behavior.visibility:model must be able to set user-invocable:false."""
        registrar, src_dir = self._make_registrar_and_source_dir(tmp)

        frontmatter = {
            "description": "test",
            "behavior": {"visibility": "model"},
        }
        output = registrar.render_skill_command(
            "claude", "speckit-test", frontmatter, "Body", "test-ext",
            "commands/test.md", tmp, source_dir=src_dir,
        )
        parsed = _parse_frontmatter(output)
        assert parsed.get("user-invocable") is False, (
            f"behavior.visibility:model did not override default; got: {parsed}"
        )

    def test_source_model_wins_even_when_behavior_capability_also_set(self, tmp):
        """Full regression: source model is preserved when both source and behavior specify model."""
        registrar, src_dir = self._make_registrar_and_source_dir(tmp)

        frontmatter = {
            "description": "test",
            "model": "claude-opus-4-6",
            "behavior": {
                "capability": "fast",      # would inject haiku
                "invocation": "automatic", # must still work
            },
        }
        output = registrar.render_skill_command(
            "claude", "speckit-test", frontmatter, "Body", "test-ext",
            "commands/test.md", tmp, source_dir=src_dir,
        )
        parsed = _parse_frontmatter(output)
        assert parsed.get("model") == "claude-opus-4-6"
        assert parsed.get("disable-model-invocation") is False


# ---------------------------------------------------------------------------
# Issue 5 — extensions.py reads source file twice; import inside loop
# ---------------------------------------------------------------------------

class TestExtensionSkillSingleRead:
    """Issue 5: _register_extension_skills must read each source file exactly once."""

    @pytest.fixture
    def tmp(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_source_file_read_at_most_once(self, tmp):
        """Each source command file must be read at most once per registration pass."""
        ext_dir = _make_ext_dir(tmp, "ext5", [
            {"name": "speckit.ext5.cmd", "file": "commands/cmd.md"}
        ])
        cmd_file = ext_dir / "commands" / "cmd.md"
        cmd_file.write_text("---\ndescription: Test\n---\n\nBody")

        proj = _make_project(tmp, ai="codex", ai_skills=True)
        (proj / ".agents" / "skills").mkdir(parents=True)

        from specify_cli.extensions import ExtensionManifest, ExtensionManager
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        mgr = ExtensionManager(proj)

        read_calls: list[Path] = []
        original_read_text = Path.read_text

        def counting_read_text(self_path, *args, **kwargs):
            if self_path == cmd_file:
                read_calls.append(self_path)
            return original_read_text(self_path, *args, **kwargs)

        with patch.object(Path, "read_text", counting_read_text):
            mgr._register_extension_skills(manifest, ext_dir)

        assert len(read_calls) <= 1, (
            f"source file read {len(read_calls)} times, expected at most 1"
        )

    def test_get_deployment_type_imported_at_module_scope(self):
        """get_deployment_type must be importable directly from specify_cli.behavior."""
        from specify_cli.behavior import get_deployment_type
        assert callable(get_deployment_type)

    def test_double_read_fix_preserves_correct_behavior(self, tmp):
        """After fix, agent-deployment skip still works (no regression from read refactor)."""
        ext_dir = _make_ext_dir(tmp, "ext5b", [
            {
                "name": "speckit.ext5b.cmd",
                "file": "commands/cmd.md",
                "behavior": {"execution": "agent"},
            }
        ])
        cmd_file = ext_dir / "commands" / "cmd.md"
        cmd_file.write_text("---\ndescription: Agent command\n---\n\nBody")

        proj = _make_project(tmp, ai="codex", ai_skills=True)
        (proj / ".agents" / "skills").mkdir(parents=True)

        from specify_cli.extensions import ExtensionManifest, ExtensionManager
        manifest = ExtensionManifest(ext_dir / "extension.yml")
        mgr = ExtensionManager(proj)
        skills = mgr._register_extension_skills(manifest, ext_dir)

        skill_file = proj / ".agents" / "skills" / "speckit-ext5b-cmd" / "SKILL.md"
        assert not skill_file.exists(), "agent-type command should not produce a SKILL.md"
        assert skills == []
