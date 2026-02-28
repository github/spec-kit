"""Consistency checks for agent configuration across runtime and packaging scripts."""

import re
from pathlib import Path

from specify_cli import AGENT_CONFIG, AI_ASSISTANT_HELP
from specify_cli.extensions import CommandRegistrar


REPO_ROOT = Path(__file__).resolve().parent.parent


class TestAgentConfigConsistency:
    """Ensure kiro-cli migration stays synchronized across key surfaces."""

    def test_runtime_config_uses_kiro_cli_and_removes_q(self):
        """AGENT_CONFIG should include kiro-cli and exclude legacy q."""
        assert "kiro-cli" in AGENT_CONFIG
        assert AGENT_CONFIG["kiro-cli"]["folder"] == ".kiro/"
        assert AGENT_CONFIG["kiro-cli"]["commands_subdir"] == "prompts"
        assert "q" not in AGENT_CONFIG

    def test_extension_registrar_uses_kiro_cli_and_removes_q(self):
        """Extension command registrar should target .kiro/prompts."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert "kiro-cli" in cfg
        assert cfg["kiro-cli"]["dir"] == ".kiro/prompts"
        assert "q" not in cfg

    def test_release_agent_lists_include_kiro_cli_and_exclude_q(self):
        """Bash and PowerShell release scripts should agree on agent key set for Kiro."""
        sh_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.sh").read_text(encoding="utf-8")
        ps_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.ps1").read_text(encoding="utf-8")

        sh_match = re.search(r"ALL_AGENTS=\(([^)]*)\)", sh_text)
        assert sh_match is not None
        sh_agents = sh_match.group(1).split()

        ps_match = re.search(r"\$AllAgents = @\(([^)]*)\)", ps_text)
        assert ps_match is not None
        ps_agents = re.findall(r"'([^']+)'", ps_match.group(1))

        assert "kiro-cli" in sh_agents
        assert "kiro-cli" in ps_agents
        assert "shai" in sh_agents
        assert "shai" in ps_agents
        assert "agy" in sh_agents
        assert "agy" in ps_agents
        assert "q" not in sh_agents
        assert "q" not in ps_agents

    def test_release_ps_switch_has_shai_and_agy_generation(self):
        """PowerShell release builder must generate files for shai and agy agents."""
        ps_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.ps1").read_text(encoding="utf-8")

        assert re.search(r"'shai'\s*\{.*?\.shai/commands", ps_text, re.S) is not None
        assert re.search(r"'agy'\s*\{.*?\.agent/workflows", ps_text, re.S) is not None

    def test_init_ai_help_includes_roo_and_kiro_alias(self):
        """CLI help text for --ai should stay in sync with agent config and alias guidance."""
        assert "roo" in AI_ASSISTANT_HELP
        assert "Use 'kiro' as an alias for 'kiro-cli'." in AI_ASSISTANT_HELP

    def test_devcontainer_kiro_installer_uses_pinned_checksum(self):
        """Devcontainer installer should always verify Kiro installer via pinned SHA256."""
        post_create_text = (REPO_ROOT / ".devcontainer" / "post-create.sh").read_text(encoding="utf-8")

        assert 'KIRO_INSTALLER_SHA256="7487a65cf310b7fb59b357c4b5e6e3f3259d383f4394ecedb39acf70f307cffb"' in post_create_text
        assert "sha256sum -c -" in post_create_text
        assert "KIRO_SKIP_KIRO_INSTALLER_VERIFY" not in post_create_text

    def test_release_output_targets_kiro_prompt_dir(self):
        """Packaging and release scripts should no longer emit amazonq artifacts."""
        sh_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.sh").read_text(encoding="utf-8")
        ps_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-release-packages.ps1").read_text(encoding="utf-8")
        gh_release_text = (REPO_ROOT / ".github" / "workflows" / "scripts" / "create-github-release.sh").read_text(encoding="utf-8")

        assert ".kiro/prompts" in sh_text
        assert ".kiro/prompts" in ps_text
        assert ".amazonq/prompts" not in sh_text
        assert ".amazonq/prompts" not in ps_text

        assert "spec-kit-template-kiro-cli-sh-" in gh_release_text
        assert "spec-kit-template-kiro-cli-ps-" in gh_release_text
        assert "spec-kit-template-q-sh-" not in gh_release_text
        assert "spec-kit-template-q-ps-" not in gh_release_text

    def test_agent_context_scripts_use_kiro_cli(self):
        """Agent context scripts should advertise kiro-cli and not legacy q agent key."""
        bash_text = (REPO_ROOT / "scripts" / "bash" / "update-agent-context.sh").read_text(encoding="utf-8")
        pwsh_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        assert "kiro-cli" in bash_text
        assert "kiro-cli" in pwsh_text
        assert "Amazon Q Developer CLI" not in bash_text
        assert "Amazon Q Developer CLI" not in pwsh_text
