"""Consistency checks for agent configuration across runtime surfaces."""

import re
from pathlib import Path

from specify_cli import AGENT_CONFIG, AI_ASSISTANT_ALIASES, AI_ASSISTANT_HELP
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

    def test_extension_registrar_includes_codex(self):
        """Extension command registrar should include codex targeting .agents/skills."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert "codex" in cfg
        assert cfg["codex"]["dir"] == ".agents/skills"
        assert cfg["codex"]["extension"] == "/SKILL.md"

    def test_runtime_codex_uses_native_skills(self):
        """Codex runtime config should point at .agents/skills."""
        assert AGENT_CONFIG["codex"]["folder"] == ".agents/"
        assert AGENT_CONFIG["codex"]["commands_subdir"] == "skills"

    def test_init_ai_help_includes_roo_and_kiro_alias(self):
        """CLI help text for --ai should stay in sync with agent config and alias guidance."""
        assert "roo" in AI_ASSISTANT_HELP
        for alias, target in AI_ASSISTANT_ALIASES.items():
            assert alias in AI_ASSISTANT_HELP
            assert target in AI_ASSISTANT_HELP

    def test_devcontainer_kiro_installer_uses_pinned_checksum(self):
        """Devcontainer installer should always verify Kiro installer via pinned SHA256."""
        post_create_text = (REPO_ROOT / ".devcontainer" / "post-create.sh").read_text(encoding="utf-8")

        assert 'KIRO_INSTALLER_SHA256="7487a65cf310b7fb59b357c4b5e6e3f3259d383f4394ecedb39acf70f307cffb"' in post_create_text
        assert "sha256sum -c -" in post_create_text
        assert "KIRO_SKIP_KIRO_INSTALLER_VERIFY" not in post_create_text

    def test_agent_context_scripts_use_kiro_cli(self):
        """Agent context scripts should advertise kiro-cli and not legacy q agent key."""
        bash_text = (REPO_ROOT / "scripts" / "bash" / "update-agent-context.sh").read_text(encoding="utf-8")
        pwsh_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        assert "kiro-cli" in bash_text
        assert "kiro-cli" in pwsh_text
        assert "Amazon Q Developer CLI" not in bash_text
        assert "Amazon Q Developer CLI" not in pwsh_text

    # --- Tabnine CLI consistency checks ---

    def test_runtime_config_includes_tabnine(self):
        """AGENT_CONFIG should include tabnine with correct folder and subdir."""
        assert "tabnine" in AGENT_CONFIG
        assert AGENT_CONFIG["tabnine"]["folder"] == ".tabnine/agent/"
        assert AGENT_CONFIG["tabnine"]["commands_subdir"] == "commands"
        assert AGENT_CONFIG["tabnine"]["requires_cli"] is True
        assert AGENT_CONFIG["tabnine"]["install_url"] is not None

    def test_extension_registrar_includes_tabnine(self):
        """CommandRegistrar.AGENT_CONFIGS should include tabnine with correct TOML config."""
        from specify_cli.extensions import CommandRegistrar

        assert "tabnine" in CommandRegistrar.AGENT_CONFIGS
        cfg = CommandRegistrar.AGENT_CONFIGS["tabnine"]
        assert cfg["dir"] == ".tabnine/agent/commands"
        assert cfg["format"] == "toml"
        assert cfg["args"] == "{{args}}"
        assert cfg["extension"] == ".toml"

    def test_agent_context_scripts_include_tabnine(self):
        """Agent context scripts should support tabnine agent type."""
        bash_text = (REPO_ROOT / "scripts" / "bash" / "update-agent-context.sh").read_text(encoding="utf-8")
        pwsh_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        assert "tabnine" in bash_text
        assert "TABNINE_FILE" in bash_text
        assert "tabnine" in pwsh_text
        assert "TABNINE_FILE" in pwsh_text

    def test_ai_help_includes_tabnine(self):
        """CLI help text for --ai should include tabnine."""
        assert "tabnine" in AI_ASSISTANT_HELP

    # --- Kimi Code CLI consistency checks ---

    def test_kimi_in_agent_config(self):
        """AGENT_CONFIG should include kimi with correct folder and commands_subdir."""
        assert "kimi" in AGENT_CONFIG
        assert AGENT_CONFIG["kimi"]["folder"] == ".kimi/"
        assert AGENT_CONFIG["kimi"]["commands_subdir"] == "skills"
        assert AGENT_CONFIG["kimi"]["requires_cli"] is True

    def test_kimi_in_extension_registrar(self):
        """Extension command registrar should include kimi using .kimi/skills and SKILL.md."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert "kimi" in cfg
        kimi_cfg = cfg["kimi"]
        assert kimi_cfg["dir"] == ".kimi/skills"
        assert kimi_cfg["extension"] == "/SKILL.md"

    def test_kimi_in_powershell_validate_set(self):
        """PowerShell update-agent-context script should include 'kimi' in ValidateSet."""
        ps_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        validate_set_match = re.search(r"\[ValidateSet\(([^)]*)\)\]", ps_text)
        assert validate_set_match is not None
        validate_set_values = re.findall(r"'([^']+)'", validate_set_match.group(1))

        assert "kimi" in validate_set_values

    def test_ai_help_includes_kimi(self):
        """CLI help text for --ai should include kimi."""
        assert "kimi" in AI_ASSISTANT_HELP

    # --- Trae IDE consistency checks ---

    def test_trae_in_agent_config(self):
        """AGENT_CONFIG should include trae with correct folder and commands_subdir."""
        assert "trae" in AGENT_CONFIG
        assert AGENT_CONFIG["trae"]["folder"] == ".trae/"
        assert AGENT_CONFIG["trae"]["commands_subdir"] == "skills"
        assert AGENT_CONFIG["trae"]["requires_cli"] is False
        assert AGENT_CONFIG["trae"]["install_url"] is None

    def test_trae_in_extension_registrar(self):
        """Extension command registrar should include trae using .trae/rules and markdown, if present."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert "trae" in cfg
        trae_cfg = cfg["trae"]
        assert trae_cfg["format"] == "markdown"
        assert trae_cfg["args"] == "$ARGUMENTS"
        assert trae_cfg["extension"] == "/SKILL.md"

    def test_trae_in_agent_context_scripts(self):
        """Agent context scripts should support trae agent type."""
        bash_text = (REPO_ROOT / "scripts" / "bash" / "update-agent-context.sh").read_text(encoding="utf-8")
        pwsh_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        assert "trae" in bash_text
        assert "TRAE_FILE" in bash_text
        assert "trae" in pwsh_text
        assert "TRAE_FILE" in pwsh_text

    def test_trae_in_powershell_validate_set(self):
        """PowerShell update-agent-context script should include 'trae' in ValidateSet."""
        ps_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        validate_set_match = re.search(r"\[ValidateSet\(([^)]*)\)\]", ps_text)
        assert validate_set_match is not None
        validate_set_values = re.findall(r"'([^']+)'", validate_set_match.group(1))

        assert "trae" in validate_set_values

    def test_ai_help_includes_trae(self):
        """CLI help text for --ai should include trae."""
        assert "trae" in AI_ASSISTANT_HELP

    # --- Pi Coding Agent consistency checks ---

    def test_pi_in_agent_config(self):
        """AGENT_CONFIG should include pi with correct folder and commands_subdir."""
        assert "pi" in AGENT_CONFIG
        assert AGENT_CONFIG["pi"]["folder"] == ".pi/"
        assert AGENT_CONFIG["pi"]["commands_subdir"] == "prompts"
        assert AGENT_CONFIG["pi"]["requires_cli"] is True
        assert AGENT_CONFIG["pi"]["install_url"] is not None

    def test_pi_in_extension_registrar(self):
        """Extension command registrar should include pi using .pi/prompts."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert "pi" in cfg
        pi_cfg = cfg["pi"]
        assert pi_cfg["dir"] == ".pi/prompts"
        assert pi_cfg["format"] == "markdown"
        assert pi_cfg["args"] == "$ARGUMENTS"
        assert pi_cfg["extension"] == ".md"

    def test_pi_in_powershell_validate_set(self):
        """PowerShell update-agent-context script should include 'pi' in ValidateSet."""
        ps_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        validate_set_match = re.search(r"\[ValidateSet\(([^)]*)\)\]", ps_text)
        assert validate_set_match is not None
        validate_set_values = re.findall(r"'([^']+)'", validate_set_match.group(1))

        assert "pi" in validate_set_values

    def test_agent_context_scripts_include_pi(self):
        """Agent context scripts should support pi agent type."""
        bash_text = (REPO_ROOT / "scripts" / "bash" / "update-agent-context.sh").read_text(encoding="utf-8")
        pwsh_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        assert "pi" in bash_text
        assert "Pi Coding Agent" in bash_text
        assert "pi" in pwsh_text
        assert "Pi Coding Agent" in pwsh_text

    def test_ai_help_includes_pi(self):
        """CLI help text for --ai should include pi."""
        assert "pi" in AI_ASSISTANT_HELP

    # --- iFlow CLI consistency checks ---

    def test_iflow_in_agent_config(self):
        """AGENT_CONFIG should include iflow with correct folder and commands_subdir."""
        assert "iflow" in AGENT_CONFIG
        assert AGENT_CONFIG["iflow"]["folder"] == ".iflow/"
        assert AGENT_CONFIG["iflow"]["commands_subdir"] == "commands"
        assert AGENT_CONFIG["iflow"]["requires_cli"] is True

    def test_iflow_in_extension_registrar(self):
        """Extension command registrar should include iflow targeting .iflow/commands."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert "iflow" in cfg
        assert cfg["iflow"]["dir"] == ".iflow/commands"
        assert cfg["iflow"]["format"] == "markdown"
        assert cfg["iflow"]["args"] == "$ARGUMENTS"

    def test_iflow_in_agent_context_scripts(self):
        """Agent context scripts should support iflow agent type."""
        bash_text = (REPO_ROOT / "scripts" / "bash" / "update-agent-context.sh").read_text(encoding="utf-8")
        pwsh_text = (REPO_ROOT / "scripts" / "powershell" / "update-agent-context.ps1").read_text(encoding="utf-8")

        assert "iflow" in bash_text
        assert "IFLOW_FILE" in bash_text
        assert "iflow" in pwsh_text
        assert "IFLOW_FILE" in pwsh_text

    def test_ai_help_includes_iflow(self):
        """CLI help text for --ai should include iflow."""
        assert "iflow" in AI_ASSISTANT_HELP
