"""Filesystem regressions for selector/provider lifecycle mutations."""

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app, save_init_options
from specify_cli.extensions import ExtensionManager
from specify_cli.presets import PresetManager
from specify_cli.extensions._commands import _refresh_presets_and_warn


COMMAND = "speckit.provider.collect"
ALIAS = "speckit.provider.quick"


def project(tmp_path, monkeypatch, agent="gemini", skills=False):
    root = tmp_path / "project"
    (root / ".specify").mkdir(parents=True)
    (root / ".gemini" / "commands").mkdir(parents=True)
    (root / ".github" / "agents").mkdir(parents=True)
    save_init_options(root, {"ai": agent, "ai_skills": skills, "script": "sh"})
    monkeypatch.chdir(root)
    return root


def preset(tmp_path, identifier, name, body, aliases=False, strategy=None):
    source = tmp_path / identifier
    (source / "commands").mkdir(parents=True)
    (source / "commands" / "body.md").write_text(
        f"---\ndescription: Lifecycle test\n---\n{body}\n"
    )
    declaration = {"type": "command", "name": name, "file": "commands/body.md"}
    if aliases:
        declaration["aliases"] = [ALIAS]
    if strategy is not None:
        declaration["strategy"] = strategy
    (source / "preset.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": identifier,
                    "name": identifier,
                    "version": "1.0.0",
                    "description": "Test",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {"templates": [declaration]},
            }
        )
    )
    return source


def second_provider_extension(
    tmp_path, extension_id="secondary", declared=None, body="SECOND BODY"
):
    """Extension that layers on ``COMMAND`` through a conventional command file.

    Primary extension command names are namespace-validated
    (``speckit.<extension-id>.<command>``), so a second extension can only
    contribute a parallel resolution layer for the same concrete command
    through the documented ``commands/<full-command-name>.md`` conventional
    lookup — which is exactly the two-provider stack the lifecycle tests need.
    """
    declared = declared or f"speckit.{extension_id}.collect"
    source = tmp_path / f"{extension_id}-source"
    (source / "commands").mkdir(parents=True)
    (source / "commands" / "body.md").write_text(
        f"---\ndescription: {extension_id}\n---\n{body}\n"
    )
    (source / "commands" / f"{COMMAND}.md").write_text(
        f"---\ndescription: {extension_id}\n---\n{body}\n"
    )
    (source / "extension.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "extension": {
                    "id": extension_id,
                    "name": extension_id,
                    "version": "1.0.0",
                    "description": "Test",
                    "author": "Test",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "commands": [
                        {
                            "name": declared,
                            "file": "commands/body.md",
                            "description": "Test",
                        }
                    ]
                },
            }
        )
    )
    return source


def extension(tmp_path):
    source = tmp_path / "extension-source"
    (source / "commands").mkdir(parents=True)
    (source / "commands" / "body.md").write_text(
        "---\ndescription: Provider\n---\nEXTENSION BODY\n"
    )
    (source / "extension.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "extension": {
                    "id": "provider",
                    "name": "Provider",
                    "version": "1.0.0",
                    "description": "Test",
                    "author": "Test",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "commands": [
                        {
                            "name": COMMAND,
                            "file": "commands/body.md",
                            "description": "Test",
                        }
                    ]
                },
            }
        )
    )
    return source


@pytest.mark.parametrize("mutation", ["remove", "disable"])
@pytest.mark.parametrize(
    "agent,skills", [("gemini", False), ("copilot", True), ("claude", True)]
)
def test_extension_mutation_retires_historical_selector_outputs(
    tmp_path, monkeypatch, mutation, agent, skills
):
    root = project(tmp_path, monkeypatch, agent, skills)
    ExtensionManager(root).install_from_directory(extension(tmp_path), "0.1.5")
    manager = PresetManager(root)
    manager.install_from_directory(
        preset(
            tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY", True
        ),
        "0.1.5",
    )
    command = root / ".gemini/commands" / f"{COMMAND}.toml"
    skill_dir = root / (".github/skills" if agent == "copilot" else ".claude/skills")
    skill = skill_dir / "speckit-provider-collect/SKILL.md"
    output = command if agent == "gemini" else skill
    assert "SELECTOR BODY" in output.read_text()
    result = CliRunner().invoke(
        app,
        ["extension", mutation, "provider"]
        + (["--force"] if mutation == "remove" else []),
    )
    assert result.exit_code == 0, result.output
    assert not output.exists()
    assert not (root / ".gemini/commands" / f"{ALIAS}.toml").exists()
    metadata = PresetManager(root).registry.get("selector")
    assert metadata.get("registered_commands", {}) == {}
    assert metadata.get("registered_skills", {}) == {}
    _refresh_presets_and_warn(root)
    _refresh_presets_and_warn(root)
    assert not output.exists()


@pytest.mark.parametrize("skills", [False, True])
def test_preset_disable_sole_provider_cleans_historical_agents_and_aliases(
    tmp_path, monkeypatch, skills
):
    root = project(tmp_path, monkeypatch)
    manager = PresetManager(root)
    manager.install_from_directory(
        preset(tmp_path, "provider", COMMAND, "PROVIDER BODY", True), "0.1.5"
    )
    save_init_options(root, {"ai": "copilot", "ai_skills": skills, "script": "sh"})
    manager.register_enabled_presets_for_agent("copilot")
    gemini = root / ".gemini/commands" / f"{COMMAND}.toml"
    copilot = root / (
        ".github/skills/speckit-provider-collect/SKILL.md"
        if skills
        else f".github/agents/{COMMAND}.agent.md"
    )
    assert gemini.exists()
    assert copilot.exists()
    result = CliRunner().invoke(app, ["preset", "disable", "provider"])
    assert result.exit_code == 0, result.output
    assert not gemini.exists()
    assert not copilot.exists()
    assert not (gemini.parent / f"{ALIAS}.toml").exists()
    metadata = PresetManager(root).registry.get("provider")
    assert metadata["registered_commands"] == {}
    assert metadata["registered_skills"] == {}
    _refresh_presets_and_warn(root)
    assert not copilot.exists()


def test_extension_removal_rewrites_surviving_fallback(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    ext = ExtensionManager(root)
    ext.install_from_directory(extension(tmp_path), "0.1.5")
    manager = PresetManager(root)
    manager.install_from_directory(
        preset(tmp_path, "fallback", COMMAND, "FALLBACK BODY"), "0.1.5", priority=20
    )
    manager.install_from_directory(
        preset(tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY"),
        "0.1.5",
        priority=5,
    )
    output = root / ".gemini/commands" / f"{COMMAND}.toml"
    assert "SELECTOR BODY" in output.read_text()
    result = CliRunner().invoke(app, ["extension", "remove", "provider", "--force"])
    assert result.exit_code == 0, result.output
    assert (
        "SELECTOR BODY" in output.read_text()
    )  # lower exact preset keeps selector eligible
    result = CliRunner().invoke(app, ["preset", "disable", "selector"])
    assert result.exit_code == 0, result.output
    assert "FALLBACK BODY" in output.read_text()


@pytest.mark.parametrize(
    "strategy,selector_body",
    [
        ("append", "SELECTOR BODY"),
        ("prepend", "SELECTOR BODY"),
        ("wrap", "WRAPPER START\n{CORE_TEMPLATE}\nWRAPPER END"),
    ],
)
def test_extension_removal_recomposes_selector_composition(
    tmp_path, monkeypatch, strategy, selector_body
):
    """Removing one of two extension providers must recompose the selector output.

    The selector preset composes over the higher-precedence extension provider.
    Removing that provider must switch the composition base to the surviving
    provider and drop the removed provider's fragment entirely — not merely
    refresh the registry.
    """
    root = project(tmp_path, monkeypatch)
    extension_manager = ExtensionManager(root)
    extension_manager.install_from_directory(extension(tmp_path), "0.1.5", priority=10)
    extension_manager.install_from_directory(
        second_provider_extension(tmp_path), "0.1.5", priority=20
    )
    manager = PresetManager(root)
    manager.install_from_directory(
        preset(
            tmp_path,
            "selector",
            r"regex:speckit\.provider\..*",
            selector_body,
            strategy=strategy,
        ),
        "0.1.5",
        priority=5,
    )

    output = root / ".gemini" / "commands" / f"{COMMAND}.toml"
    text = output.read_text()
    assert "EXTENSION BODY" in text
    assert "SECOND BODY" not in text

    result = CliRunner().invoke(app, ["extension", "remove", "provider", "--force"])
    assert result.exit_code == 0, result.output

    text = output.read_text()
    assert "SECOND BODY" in text
    assert "EXTENSION BODY" not in text
    if strategy == "wrap":
        assert "WRAPPER START" in text and "WRAPPER END" in text
    else:
        assert "SELECTOR BODY" in text

    # Ownership stays with the preset that still materializes the command, and
    # the removed provider is gone from the extension registry.
    metadata = PresetManager(root).registry.get("selector")
    assert metadata is not None
    assert COMMAND in metadata["registered_commands"]["gemini"]
    assert ExtensionManager(root).registry.get("provider") is None

    # Repeated reconciliation must stay stable (no resurrection, no flip-flop).
    _refresh_presets_and_warn(root)
    _refresh_presets_and_warn(root)
    text = output.read_text()
    assert "SECOND BODY" in text
    assert "EXTENSION BODY" not in text


@pytest.mark.parametrize(
    "strategy,selector_body",
    [
        ("append", "SELECTOR BODY"),
        ("wrap", "WRAPPER START\n{CORE_TEMPLATE}\nWRAPPER END"),
    ],
)
def test_extension_removal_sole_provider_retires_composition(
    tmp_path, monkeypatch, strategy, selector_body
):
    """A composing selector with no surviving lower layer must be retired.

    The affected-name set has to come from the pre-removal selector expansion;
    after removal nothing matches, so a post-state-only scan would leave the
    stale command/alias/skill artifacts and registry provenance behind.
    """
    root = project(tmp_path, monkeypatch)
    ExtensionManager(root).install_from_directory(
        extension(tmp_path), "0.1.5", priority=10
    )
    manager = PresetManager(root)
    manager.install_from_directory(
        preset(
            tmp_path,
            "selector",
            r"regex:speckit\.provider\..*",
            selector_body,
            aliases=True,
            strategy=strategy,
        ),
        "0.1.5",
        priority=5,
    )

    command = root / ".gemini" / "commands" / f"{COMMAND}.toml"
    alias = root / ".gemini" / "commands" / f"{ALIAS}.toml"
    assert command.exists()
    assert alias.exists()

    result = CliRunner().invoke(app, ["extension", "remove", "provider", "--force"])
    assert result.exit_code == 0, result.output
    assert not command.exists()
    assert not alias.exists()

    metadata = PresetManager(root).registry.get("selector")
    assert metadata is not None
    assert metadata["registered_commands"] == {}
    assert metadata["registered_skills"] == {}
    # The raw selector string must never enter concrete command tracking.
    assert all(
        not name.startswith("regex:")
        for names in metadata["registered_commands"].values()
        for name in names
    )

    _refresh_presets_and_warn(root)
    _refresh_presets_and_warn(root)
    assert not command.exists()
    assert not alias.exists()


@pytest.mark.parametrize(
    "agent,skills,relative_output",
    [
        ("gemini", False, f".gemini/commands/{COMMAND}.toml"),
        ("copilot", True, ".github/skills/speckit-provider-collect/SKILL.md"),
        ("claude", True, ".claude/skills/speckit-provider-collect/SKILL.md"),
        ("codex", False, ".agents/skills/speckit-provider-collect/SKILL.md"),
    ],
)
def test_extension_install_refresh_writes_replace_winner_once(
    tmp_path, monkeypatch, agent, skills, relative_output
):
    from pathlib import Path

    from specify_cli.agents import CommandRegistrar
    from specify_cli import shared_infra

    root = project(tmp_path, monkeypatch, agent, skills)
    if agent in {"claude", "codex"}:
        (root / relative_output).parent.parent.mkdir(parents=True)
    PresetManager(root).install_from_directory(
        preset(
            tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY", True
        ),
        "0.1.5",
    )
    output = root / relative_output
    registrations = []
    materializations = []
    original_register = CommandRegistrar.register_commands
    original_write = Path.write_text
    original_shared_write = shared_infra._write_shared_text

    def record_registration(self, *args, **kwargs):
        result = original_register(self, *args, **kwargs)
        if COMMAND in result:
            registrations.append(result)
        return result

    def record_write(path, content, *args, **kwargs):
        result = original_write(path, content, *args, **kwargs)
        if path == output:
            materializations.append(content)
        return result

    def record_shared_write(project_path, dest, content):
        result = original_shared_write(project_path, dest, content)
        if dest == output:
            materializations.append(content)
        return result

    monkeypatch.setattr(CommandRegistrar, "register_commands", record_registration)
    monkeypatch.setattr(Path, "write_text", record_write)
    monkeypatch.setattr(shared_infra, "_write_shared_text", record_shared_write)
    source = extension(tmp_path)
    monkeypatch.setattr(
        "specify_cli.extensions._commands._locate_bundled_extension", lambda _: source
    )
    result = CliRunner().invoke(app, ["extension", "add", "provider"])
    assert result.exit_code == 0, result.output
    assert "SELECTOR BODY" in output.read_text()
    assert "EXTENSION BODY" not in output.read_text()
    metadata = PresetManager(root).registry.get("selector")
    provider = ExtensionManager(root).registry.get("provider")
    assert metadata is not None
    assert provider is not None
    assert provider["enabled"] is True
    assert (root / ".specify/extensions/provider/commands/body.md").is_file()
    if agent == "copilot":
        assert metadata["registered_skills"][agent] == ["speckit-provider-collect"]
        assert provider["registered_skills"] == ["speckit-provider-collect"]
        assert "preset:selector" in output.read_text()
        assert not (root / ".github/agents" / f"{COMMAND}.agent.md").exists()
    else:
        assert metadata["registered_commands"][agent] == [COMMAND, ALIAS]
        assert provider["registered_commands"][agent] == [COMMAND]
        alias = (
            output.parent / f"{ALIAS}.toml"
            if agent == "gemini"
            else output.parent.parent / "speckit-provider-quick/SKILL.md"
        )
        assert "SELECTOR BODY" in alias.read_text()
    assert len(materializations) == 1, {
        "registrations": registrations,
        "materializations": materializations,
    }
    assert all("SELECTOR BODY" in body for body in materializations)
    if agent != "copilot":
        assert len(registrations) == 1


def test_cleanup_failure_preserves_tracking_for_retry(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    manager = PresetManager(root)
    manager.install_from_directory(
        preset(tmp_path, "provider", COMMAND, "PROVIDER BODY"), "0.1.5"
    )
    manager.registry.update("provider", {"enabled": False})
    output = root / ".gemini/commands" / f"{COMMAND}.toml"
    original = manager._unregister_commands

    def fail(_):
        raise OSError("cleanup failed")

    monkeypatch.setattr(manager, "_unregister_commands", fail)
    with pytest.raises(OSError, match="cleanup failed"):
        manager._reconcile_composed_commands([COMMAND])
    assert output.exists()
    assert manager.registry.get("provider")["registered_commands"]["gemini"] == [
        COMMAND
    ]
    monkeypatch.setattr(manager, "_unregister_commands", original)
    manager._reconcile_composed_commands([COMMAND])
    assert not output.exists()
    assert manager.registry.get("provider")["registered_commands"] == {}


def test_zero_layer_skill_cleanup_preserves_foreign_owner(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, "copilot", True)
    manager = PresetManager(root)
    manager.install_from_directory(
        preset(tmp_path, "provider", COMMAND, "PROVIDER BODY"), "0.1.5"
    )
    skill = root / ".github/skills/speckit-provider-collect/SKILL.md"
    skill.write_text(
        "---\nname: speckit-provider-collect\nmetadata:\n  source: user:custom\n---\nUSER BODY\n"
    )
    manager.registry.update("provider", {"enabled": False})
    manager._reconcile_composed_commands([COMMAND])
    assert "USER BODY" in skill.read_text()


def test_extension_disable_retires_inactive_selector_command(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    ExtensionManager(root).install_from_directory(extension(tmp_path), "0.1.5")
    manager = PresetManager(root)
    manager.install_from_directory(
        preset(
            tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY", True
        ),
        "0.1.5",
    )
    save_init_options(root, {"ai": "copilot", "ai_skills": True, "script": "sh"})
    manager.register_enabled_presets_for_agent("copilot")
    gemini = root / ".gemini/commands" / f"{COMMAND}.toml"
    copilot = root / ".github/skills/speckit-provider-collect/SKILL.md"
    assert "SELECTOR BODY" in gemini.read_text()
    assert "SELECTOR BODY" in copilot.read_text()
    result = CliRunner().invoke(app, ["extension", "disable", "provider"])
    assert result.exit_code == 0, result.output
    assert not gemini.exists()
    assert not copilot.exists()
    assert PresetManager(root).registry.get("selector")["registered_commands"] == {}
    assert PresetManager(root).registry.get("selector")["registered_skills"] == {}


def test_extension_add_preserves_provider_aliases_with_selector(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    PresetManager(root).install_from_directory(
        preset(
            tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY", True
        ),
        "0.1.5",
    )
    source = extension(tmp_path)
    manifest_file = source / "extension.yml"
    data = yaml.safe_load(manifest_file.read_text())
    provider_alias = "speckit.provider.provider-alias"
    data["provides"]["commands"][0]["aliases"] = [provider_alias]
    manifest_file.write_text(yaml.safe_dump(data))
    ExtensionManager(root).install_from_directory(source, "0.1.5")
    for name in [COMMAND, ALIAS, provider_alias]:
        assert (
            "SELECTOR BODY" in (root / ".gemini/commands" / f"{name}.toml").read_text()
        )
    assert ExtensionManager(root).registry.get("provider")["registered_commands"][
        "gemini"
    ] == [COMMAND, provider_alias]


@pytest.mark.parametrize(
    "agent,skills",
    [("gemini", False), ("copilot", True), ("claude", True), ("codex", False)],
)
@pytest.mark.parametrize("failure", ["partial-output", "commit"])
def test_extension_selector_install_rolls_back_exact_outputs(
    tmp_path, monkeypatch, agent, skills, failure
):
    from specify_cli.agents import CommandRegistrar
    from specify_cli.extensions import ExtensionRegistry

    root = project(tmp_path, monkeypatch, agent, skills)
    if agent in {"claude", "codex"}:
        (root / (".claude/skills" if agent == "claude" else ".agents/skills")).mkdir(
            parents=True
        )
    PresetManager(root).install_from_directory(
        preset(
            tmp_path, "selector", r"regex:speckit\.provider\..*", "SELECTOR BODY", True
        ),
        "0.1.5",
    )
    output = root / (
        f".gemini/commands/{COMMAND}.toml"
        if agent == "gemini"
        else f"{'.github' if agent == 'copilot' else '.claude' if agent == 'claude' else '.agents'}/skills/speckit-provider-collect/SKILL.md"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("USER BYTES\n")
    preset_registry = root / ".specify/presets/.registry"
    before_registry = preset_registry.read_bytes()
    original_write = CommandRegistrar._write_registered_output

    def fail_output(self, dest, *args, **kwargs):
        if dest != output:
            assert "SELECTOR BODY" in output.read_text()
            raise OSError("partial winner failure")
        return original_write(dest, *args, **kwargs)

    def fail_commit(self, *args, **kwargs):
        assert "SELECTOR BODY" in output.read_text()
        raise OSError("winner commit failure")

    if failure == "partial-output" and agent != "copilot":
        monkeypatch.setattr(CommandRegistrar, "_write_registered_output", fail_output)
    elif failure == "partial-output":
        from specify_cli import shared_infra

        original_skill_write = shared_infra._write_shared_text

        def fail_skill_write(project_path, dest, content):
            original_skill_write(project_path, dest, content)
            assert "SELECTOR BODY" in output.read_text()
            raise OSError("partial winner skill failure")

        monkeypatch.setattr(shared_infra, "_write_shared_text", fail_skill_write)
    else:
        monkeypatch.setattr(ExtensionRegistry, "add", fail_commit)
    with pytest.raises(OSError, match="winner|partial"):
        ExtensionManager(root).install_from_directory(extension(tmp_path), "0.1.5")
    assert output.read_text() == "USER BYTES\n"
    assert preset_registry.read_bytes() == before_registry
    assert not ExtensionManager(root).registry.is_installed("provider")
    assert not (root / ".specify/extensions/provider").exists()
    alias = (
        output.parent / f"{ALIAS}.toml"
        if agent == "gemini"
        else output.parent.parent / "speckit-provider-quick/SKILL.md"
    )
    assert not alias.exists()


def namespace_fallback_extension(tmp_path, extension_id="target", body="TARGET BODY"):
    """Extension whose only extra concrete command comes from a conventional file.

    Primary extension command names are namespace-validated
    (``speckit.<extension-id>.<command>``), so a parallel concrete command is
    contributed through the documented conventional lookup
    ``commands/<name without the speckit. prefix>.md``: the resolver serves the
    stem as ``speckit.<stem>`` even though no manifest entry names it. Its
    declared command is a different name, so the file above is the only source
    of ``speckit.<extension_id>.collect``.
    """
    source = tmp_path / f"{extension_id}-source"
    (source / "commands").mkdir(parents=True)
    (source / "commands" / "body.md").write_text(
        f"---\ndescription: {extension_id}\n---\nDECLARED BODY\n", encoding="utf-8"
    )
    (source / "commands" / f"{extension_id}.collect.md").write_text(
        f"---\ndescription: {extension_id}\n---\n{body}\n", encoding="utf-8"
    )
    (source / "extension.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "extension": {
                    "id": extension_id,
                    "name": extension_id,
                    "version": "1.0.0",
                    "description": "Test",
                    "author": "Test",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "commands": [
                        {
                            "name": f"speckit.{extension_id}.other",
                            "file": "commands/body.md",
                            "description": "Test",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return source


def test_selector_expands_namespace_fallback_conventional_command(
    tmp_path, monkeypatch
):
    """A selector must expand a convention-only command the resolver serves.

    The extension declares ``speckit.target.other``; ``speckit.target.collect``
    exists only as ``commands/target.collect.md``, which the resolver exposes
    through its namespace fallback. Installing the matching selector preset must
    therefore materialize that concrete command instead of expanding to nothing.
    """
    root = project(tmp_path, monkeypatch, "gemini", False)
    ExtensionManager(root).install_from_directory(
        namespace_fallback_extension(tmp_path), "0.1.5"
    )
    output = root / ".gemini" / "commands" / "speckit.target.collect.toml"
    assert not output.exists()

    PresetManager(root).install_from_directory(
        preset(
            tmp_path,
            "selector",
            r"regex:^speckit\.target\.collect$",
            "SELECTOR BODY",
            strategy="append",
        ),
        "0.1.5",
        priority=5,
    )

    assert output.exists(), "selector did not expand the namespace-fallback command"
    text = output.read_text(encoding="utf-8")
    assert "SELECTOR BODY" in text
    assert "TARGET BODY" in text
