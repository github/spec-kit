"""Consistency checks for agent configuration across runtime surfaces."""

import re
from pathlib import Path

import yaml

from specify_cli import AGENT_CONFIG
from specify_cli.extensions import CommandRegistrar

REPO_ROOT = Path(__file__).resolve().parent.parent

ISSUE_TEMPLATE_AGENT_KEYS = [
    "amp",
    "agy",
    "auggie",
    "claude",
    "cline",
    "codebuddy",
    "codex",
    "cursor-agent",
    "devin",
    "firebender",
    "forge",
    "gemini",
    "copilot",
    "goose",
    "grok",
    "hermes",
    "bob",
    "junie",
    "kilocode",
    "kimi",
    "kiro-cli",
    "lingma",
    "vibe",
    "omp",
    "opencode",
    "pi",
    "qodercli",
    "qwen",
    "rovodev",
    "shai",
    "tabnine",
    "trae",
    "zcode",
    "zed",
]


def _issue_template(path: str) -> dict:
    return yaml.safe_load((REPO_ROOT / path).read_text(encoding="utf-8"))


def _body_item_by_id(template: dict, item_id: str) -> dict:
    for item in template["body"]:
        if item.get("id") == item_id:
            return item
    raise AssertionError(f"Expected issue template body item {item_id!r}")


def _dropdown_options(path: str, item_id: str) -> list[str]:
    item = _body_item_by_id(_issue_template(path), item_id)
    return item["attributes"]["options"]


def _normalized_markdown(text: str) -> str:
    return " ".join(text.split())


def _markdown_value_containing(path: str, marker: str) -> str:
    template = _issue_template(path)
    normalized_marker = _normalized_markdown(marker)
    for item in template["body"]:
        if item.get("type") != "markdown":
            continue
        value = item["attributes"]["value"]
        if normalized_marker in _normalized_markdown(value):
            return value
    raise AssertionError(f"Expected issue template markdown containing {marker!r}")


def _markdown_paragraph_containing(path: str, marker: str) -> str:
    value = _markdown_value_containing(path, marker)
    normalized_marker = _normalized_markdown(marker)
    for paragraph in re.split(r"\n\s*\n", value):
        if normalized_marker in _normalized_markdown(paragraph):
            return paragraph
    raise AssertionError(f"Expected issue template paragraph containing {marker!r}")


def _supported_agent_names_from_agent_request_template() -> list[str]:
    marker = "**Currently supported agents**:"
    paragraph = _markdown_paragraph_containing(
        ".github/ISSUE_TEMPLATE/agent_request.yml",
        marker,
    )
    supported_agents_text = _normalized_markdown(paragraph).split(marker, 1)[1].strip()
    return [agent.strip() for agent in supported_agents_text.split(",")]


class TestAgentConfigConsistency:
    """Ensure agent configuration stays synchronized across key surfaces."""

    def test_issue_template_agent_lists_match_runtime_integrations(self):
        """GitHub issue templates should list all concrete built-in agents."""
        concrete_agent_keys = set(AGENT_CONFIG) - {"generic"}
        issue_template_agent_keys = set(ISSUE_TEMPLATE_AGENT_KEYS)

        missing_agent_keys = sorted(concrete_agent_keys - issue_template_agent_keys)
        unexpected_agent_keys = sorted(issue_template_agent_keys - concrete_agent_keys)
        duplicate_agent_keys = sorted(
            key
            for key in issue_template_agent_keys
            if ISSUE_TEMPLATE_AGENT_KEYS.count(key) > 1
        )
        assert not missing_agent_keys, (
            "Issue template agent list is missing AGENT_CONFIG keys: "
            f"{missing_agent_keys}"
        )
        assert not unexpected_agent_keys, (
            "Issue template agent list includes unknown AGENT_CONFIG keys: "
            f"{unexpected_agent_keys}"
        )
        assert not duplicate_agent_keys, (
            "Issue template agent list contains duplicate keys: "
            f"{duplicate_agent_keys}"
        )

        issue_template_agent_names = [
            AGENT_CONFIG[key]["name"] for key in ISSUE_TEMPLATE_AGENT_KEYS
        ]
        assert "Generic (bring your own agent)" not in issue_template_agent_names

        bug_options = _dropdown_options(
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            "ai-agent",
        )
        assert bug_options == issue_template_agent_names + ["Not applicable"]

        feature_options = _dropdown_options(
            ".github/ISSUE_TEMPLATE/feature_request.yml",
            "ai-agent",
        )
        assert feature_options == [
            "All agents",
            *issue_template_agent_names,
            "Not applicable",
        ]

        assert (
            _supported_agent_names_from_agent_request_template()
            == issue_template_agent_names
        )

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

    def test_devcontainer_kiro_installer_uses_pinned_checksum(self):
        """Devcontainer installer should always verify Kiro installer via pinned SHA256."""
        post_create_text = (REPO_ROOT / ".devcontainer" / "post-create.sh").read_text(
            encoding="utf-8"
        )

        assert (
            'KIRO_INSTALLER_SHA256="7487a65cf310b7fb59b357c4b5e6e3f3259d383f4394ecedb39acf70f307cffb"'
            in post_create_text
        )
        assert "sha256sum -c -" in post_create_text
        assert "KIRO_SKIP_KIRO_INSTALLER_VERIFY" not in post_create_text

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

    def test_agent_config_includes_tabnine(self):
        """AGENT_CONFIG should include tabnine."""
        assert "tabnine" in AGENT_CONFIG

    # --- Kimi Code CLI consistency checks ---

    def test_kimi_in_agent_config(self):
        """AGENT_CONFIG should include kimi with correct folder and commands_subdir."""
        assert "kimi" in AGENT_CONFIG
        assert AGENT_CONFIG["kimi"]["folder"] == ".kimi-code/"
        assert AGENT_CONFIG["kimi"]["commands_subdir"] == "skills"
        assert AGENT_CONFIG["kimi"]["requires_cli"] is True

    def test_kimi_in_extension_registrar(self):
        """Extension command registrar should include kimi using .kimi-code/skills and SKILL.md."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert "kimi" in cfg
        kimi_cfg = cfg["kimi"]
        assert kimi_cfg["dir"] == ".kimi-code/skills"
        assert kimi_cfg["extension"] == "/SKILL.md"

    def test_agent_config_includes_kimi(self):
        """AGENT_CONFIG should include kimi."""
        assert "kimi" in AGENT_CONFIG

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

    def test_agent_config_includes_trae(self):
        """AGENT_CONFIG should include trae."""
        assert "trae" in AGENT_CONFIG

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

    def test_agent_config_includes_pi(self):
        """AGENT_CONFIG should include pi."""
        assert "pi" in AGENT_CONFIG

    # --- Goose consistency checks ---

    def test_goose_in_agent_config(self):
        """AGENT_CONFIG should include goose with correct folder and commands_subdir."""
        assert "goose" in AGENT_CONFIG
        assert AGENT_CONFIG["goose"]["folder"] == ".goose/"
        assert AGENT_CONFIG["goose"]["commands_subdir"] == "recipes"
        assert AGENT_CONFIG["goose"]["requires_cli"] is True

    def test_goose_in_extension_registrar(self):
        """Extension command registrar should include goose targeting .goose/recipes."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert "goose" in cfg
        assert cfg["goose"]["dir"] == ".goose/recipes"
        assert cfg["goose"]["format"] == "yaml"
        assert cfg["goose"]["args"] == "{{args}}"

    def test_agent_config_includes_goose(self):
        """AGENT_CONFIG should include goose."""
        assert "goose" in AGENT_CONFIG

    # --- invoke_separator propagation checks ---

    def test_skills_agents_have_hyphen_invoke_separator_in_agent_configs(self):
        """Skills-based agents must expose invoke_separator='-' in AGENT_CONFIGS.

        SkillsIntegration sets ``invoke_separator = "-"`` as a class attribute,
        but individual skills integrations (claude, codex, …) do not repeat it in
        their ``registrar_config`` dicts. ``_build_agent_configs()`` must
        propagate the class attribute so that ``register_commands()`` resolves
        ``__SPECKIT_COMMAND_*__`` tokens with the correct hyphen separator.
        """
        cfg = CommandRegistrar.AGENT_CONFIGS
        skills_agents = [
            key for key, c in cfg.items() if c.get("extension") == "/SKILL.md"
        ]
        assert skills_agents, (
            "Expected at least one skills-based agent in AGENT_CONFIGS"
        )
        for agent in skills_agents:
            assert cfg[agent].get("invoke_separator") == "-", (
                f"Skills agent '{agent}' has invoke_separator="
                f"{cfg[agent].get('invoke_separator')!r} in AGENT_CONFIGS; "
                "expected '-' (propagated from SkillsIntegration.invoke_separator)"
            )

    def test_codex_dev_no_symlink_policy_in_agent_config(self):
        """Codex dev installs must expose the no-symlink policy as metadata."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert cfg["codex"].get("dev_no_symlink") is True

    def test_skills_agent_command_token_resolves_with_hyphen(self, tmp_path):
        """__SPECKIT_COMMAND_*__ tokens in extension commands resolve to /speckit-<cmd>
        when registered for a skills-based agent (e.g. claude).

        Regression guard: before the fix, _build_agent_configs() did not
        propagate invoke_separator from the integration class, so
        register_commands() fell back to '.' and emitted /speckit.specify instead
        of /speckit-specify for skills agents.
        """
        import re
        from pathlib import Path

        from specify_cli.agents import CommandRegistrar

        repo_root = Path(__file__).resolve().parent.parent
        ext_dir = repo_root / "extensions" / "git"
        cmd_source = ext_dir / "commands" / "speckit.git.feature.md"
        assert cmd_source.exists(), (
            f"Git extension command source not found at {cmd_source}"
        )
        assert "__SPECKIT_COMMAND_SPECIFY__" in cmd_source.read_text(
            encoding="utf-8"
        ), (
            "Expected __SPECKIT_COMMAND_SPECIFY__ token in speckit.git.feature.md; "
            "check that the file uses the token rather than a hard-coded ref."
        )

        registrar = CommandRegistrar()
        commands = [
            {"name": "speckit.git.feature", "file": "commands/speckit.git.feature.md"}
        ]

        registered = registrar.register_commands(
            "claude",
            commands,
            "git",
            ext_dir,
            tmp_path,
        )

        assert "speckit.git.feature" in registered
        skill_file = (
            tmp_path / ".claude" / "skills" / "speckit-git-feature" / "SKILL.md"
        )
        assert skill_file.exists(), (
            f"Expected Claude skill file not found at {skill_file}"
        )
        content = skill_file.read_text(encoding="utf-8")
        assert "/speckit-specify" in content, (
            "Expected '/speckit-specify' (hyphen) in generated Claude skill for git.feature; "
            "__SPECKIT_COMMAND_SPECIFY__ was not resolved with the correct separator."
        )
        # Negative lookbehind (?<![a-zA-Z0-9_]) excludes file-path occurrences
        # such as 'source: git:commands/speckit.git.feature.md' in frontmatter,
        # where the '/' is a path separator preceded by a word character.
        assert not re.search(r"(?<![a-zA-Z0-9_])/speckit\.[a-z]", content), (
            "Found dot-notation command ref (/speckit.<cmd>) in generated Claude skill. "
            "Skills agents must use hyphen notation."
        )

    # --- RovoDev consistency checks ---

    def test_rovodev_in_agent_config(self):
        """AGENT_CONFIG should include rovodev with skills-based scaffold metadata."""
        assert "rovodev" in AGENT_CONFIG
        assert AGENT_CONFIG["rovodev"]["folder"] == ".rovodev/"
        assert AGENT_CONFIG["rovodev"]["commands_subdir"] == "skills"
        assert AGENT_CONFIG["rovodev"]["requires_cli"] is True

    def test_rovodev_in_extension_registrar(self):
        """CommandRegistrar.AGENT_CONFIGS should include rovodev skill scaffold metadata."""
        cfg = CommandRegistrar.AGENT_CONFIGS

        assert "rovodev" in cfg
        rovodev_cfg = cfg["rovodev"]
        assert rovodev_cfg["dir"] == ".rovodev/skills"
        assert rovodev_cfg["format"] == "markdown"
        assert rovodev_cfg["args"] == "$ARGUMENTS"
        assert rovodev_cfg["extension"] == "/SKILL.md"

    def test_agent_config_includes_rovodev(self):
        """AGENT_CONFIG should include rovodev."""
        assert "rovodev" in AGENT_CONFIG
