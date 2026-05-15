import json
import shutil
from pathlib import Path

from specify_cli.agent_projection import (
    AGENT_GOVERNANCE_MEMORY,
    PROJECTION_MARKER_START,
    ensure_agent_governance_from_template,
    refresh_agent_projection,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def _copy_template(project: Path, name: str) -> None:
    dest = project / ".specify" / "templates" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / "templates" / name, dest)


def test_ensure_agent_governance_from_template(tmp_path):
    _copy_template(tmp_path, "agent-governance-template.md")

    result = ensure_agent_governance_from_template(tmp_path)

    assert result == tmp_path / AGENT_GOVERNANCE_MEMORY
    content = result.read_text(encoding="utf-8")
    assert "# Repository Agent Governance" in content
    assert "## Authority Order" in content
    assert "Agent code writes are allowed only while executing the generated Spec Kit implement command" in content
    assert "/speckit.implement" in content
    assert "/speckit-implement" in content
    assert "Bug fixes, refactors, and small code changes are not exceptions" in content
    assert content.index("2. This repository agent governance file") < content.index(
        "3. User-authored repository instructions preserved outside generated projection markers"
    )


def test_refresh_agent_projection_creates_repo_and_agent_adapters(tmp_path):
    _copy_template(tmp_path, "agent-governance-template.md")
    (tmp_path / ".specify" / "integration.json").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".specify" / "integration.json").write_text(
        json.dumps(
            {
                "integration": "gemini",
                "default_integration": "gemini",
                "installed_integrations": ["gemini", "copilot"],
                "integration_settings": {},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / ".gemini" / "commands" / "speckit-test" / "SKILL.md").parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    (tmp_path / ".gemini" / "commands" / "speckit-test" / "SKILL.md").write_text(
        "# Test Skill\n",
        encoding="utf-8",
    )
    (tmp_path / ".mcp.json").write_text("{}", encoding="utf-8")

    result = refresh_agent_projection(tmp_path)

    assert result.memory_path == tmp_path / AGENT_GOVERNANCE_MEMORY
    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / "GEMINI.md").exists()
    assert (tmp_path / ".github" / "copilot-instructions.md").exists()
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert PROJECTION_MARKER_START in agents
    assert "Default integration: `gemini`" in agents
    assert "Feature work SSOT: `specs/<feature>/`" in agents
    assert "Agent code writes are allowed only while executing the generated Spec Kit implement command" in agents
    assert "verify the active change has `spec.md`, `plan.md`, and `tasks.md`" in agents
    assert "Architecture SSOT: artifacts produced by `/speckit.arch`" not in agents
    assert "Scenario semantics: `/speckit.arch` scenario view" not in agents
    assert "Business semantics SSOT: `.specify/memory/uc.md`" not in agents
    assert "`.gemini/commands/speckit-test/SKILL.md`" in agents
    assert "`.mcp.json`" in agents


def test_refresh_agent_projection_preserves_user_content(tmp_path):
    _copy_template(tmp_path, "agent-governance-template.md")
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Custom Rules\n\nKeep this.\n", encoding="utf-8")

    refresh_agent_projection(tmp_path)

    content = agents.read_text(encoding="utf-8")
    assert "# Custom Rules" in content
    assert "Keep this." in content
    assert PROJECTION_MARKER_START in content


def test_refresh_agent_projection_projects_governance_memory_rules(tmp_path):
    _copy_template(tmp_path, "agent-governance-template.md")
    memory = ensure_agent_governance_from_template(tmp_path)
    assert memory is not None
    content = memory.read_text(encoding="utf-8")
    memory.write_text(
        content + "\n## Repository-Specific Rules\n\n- Always report MCP writes before execution.\n",
        encoding="utf-8",
    )

    refresh_agent_projection(tmp_path)

    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Repository Agent Governance" in agents
    assert "## Repository-Specific Rules" in agents
    assert "- Always report MCP writes before execution." in agents
    assert "Sync Impact Report" not in agents
