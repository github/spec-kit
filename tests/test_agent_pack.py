"""Tests for the agent pack infrastructure.

Covers manifest validation, bootstrap API contract, pack resolution order,
CLI commands, and consistency with AGENT_CONFIG / CommandRegistrar.AGENT_CONFIGS.
"""

import json
import shutil
import textwrap
from pathlib import Path

import pytest
import yaml

from specify_cli.agent_pack import (
    BOOTSTRAP_FILENAME,
    MANIFEST_FILENAME,
    MANIFEST_SCHEMA_VERSION,
    AgentBootstrap,
    AgentManifest,
    AgentPackError,
    ManifestValidationError,
    PackResolutionError,
    ResolvedPack,
    export_pack,
    list_all_agents,
    list_embedded_agents,
    load_bootstrap,
    resolve_agent_pack,
    validate_pack,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_manifest(path: Path, data: dict) -> Path:
    """Write a speckit-agent.yml to *path* and return the file path."""
    path.mkdir(parents=True, exist_ok=True)
    manifest_file = path / MANIFEST_FILENAME
    manifest_file.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    return manifest_file


def _minimal_manifest_dict(agent_id: str = "test-agent", **overrides) -> dict:
    """Return a minimal valid manifest dict, with optional overrides."""
    data = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "agent": {
            "id": agent_id,
            "name": "Test Agent",
            "version": "0.1.0",
            "description": "A test agent",
        },
        "runtime": {"requires_cli": False},
        "requires": {"speckit_version": ">=0.1.0"},
        "tags": ["test"],
        "command_registration": {
            "commands_dir": f".{agent_id}/commands",
            "format": "markdown",
            "arg_placeholder": "$ARGUMENTS",
            "file_extension": ".md",
        },
    }
    data.update(overrides)
    return data


def _write_bootstrap(pack_dir: Path, class_name: str = "TestAgent", agent_dir: str = ".test-agent") -> Path:
    """Write a minimal bootstrap.py to *pack_dir*."""
    pack_dir.mkdir(parents=True, exist_ok=True)
    bootstrap_file = pack_dir / BOOTSTRAP_FILENAME
    bootstrap_file.write_text(textwrap.dedent(f"""\
        from pathlib import Path
        from typing import Any, Dict
        from specify_cli.agent_pack import AgentBootstrap

        class {class_name}(AgentBootstrap):
            AGENT_DIR = "{agent_dir}"

            def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
                (project_path / self.AGENT_DIR / "commands").mkdir(parents=True, exist_ok=True)

            def teardown(self, project_path: Path) -> None:
                import shutil
                d = project_path / self.AGENT_DIR
                if d.is_dir():
                    shutil.rmtree(d)
    """), encoding="utf-8")
    return bootstrap_file


# ===================================================================
# Manifest validation
# ===================================================================

class TestManifestValidation:
    """Validate speckit-agent.yml parsing and error handling."""

    def test_valid_manifest(self, tmp_path):
        data = _minimal_manifest_dict()
        _write_manifest(tmp_path, data)
        m = AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)
        assert m.id == "test-agent"
        assert m.name == "Test Agent"
        assert m.version == "0.1.0"
        assert m.command_format == "markdown"

    def test_missing_schema_version(self, tmp_path):
        data = _minimal_manifest_dict()
        del data["schema_version"]
        _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="Missing required top-level"):
            AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)

    def test_wrong_schema_version(self, tmp_path):
        data = _minimal_manifest_dict()
        data["schema_version"] = "99.0"
        _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="Unsupported schema_version"):
            AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)

    def test_missing_agent_block(self, tmp_path):
        data = {"schema_version": MANIFEST_SCHEMA_VERSION}
        _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="Missing required top-level"):
            AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)

    def test_missing_agent_id(self, tmp_path):
        data = _minimal_manifest_dict()
        del data["agent"]["id"]
        _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="Missing required agent key"):
            AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)

    def test_missing_agent_name(self, tmp_path):
        data = _minimal_manifest_dict()
        del data["agent"]["name"]
        _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="Missing required agent key"):
            AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)

    def test_missing_agent_version(self, tmp_path):
        data = _minimal_manifest_dict()
        del data["agent"]["version"]
        _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="Missing required agent key"):
            AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)

    def test_agent_block_not_dict(self, tmp_path):
        data = {"schema_version": MANIFEST_SCHEMA_VERSION, "agent": "not-a-dict"}
        _write_manifest(tmp_path, data)
        with pytest.raises(ManifestValidationError, match="must be a mapping"):
            AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)

    def test_missing_file(self, tmp_path):
        with pytest.raises(ManifestValidationError, match="Manifest not found"):
            AgentManifest.from_yaml(tmp_path / "nonexistent" / MANIFEST_FILENAME)

    def test_invalid_yaml(self, tmp_path):
        tmp_path.mkdir(parents=True, exist_ok=True)
        bad = tmp_path / MANIFEST_FILENAME
        bad.write_text("{{{{bad yaml", encoding="utf-8")
        with pytest.raises(ManifestValidationError, match="Invalid YAML"):
            AgentManifest.from_yaml(bad)

    def test_runtime_fields(self, tmp_path):
        data = _minimal_manifest_dict()
        data["runtime"] = {
            "requires_cli": True,
            "install_url": "https://example.com",
            "cli_tool": "myagent",
        }
        _write_manifest(tmp_path, data)
        m = AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)
        assert m.requires_cli is True
        assert m.install_url == "https://example.com"
        assert m.cli_tool == "myagent"

    def test_command_registration_fields(self, tmp_path):
        data = _minimal_manifest_dict()
        data["command_registration"] = {
            "commands_dir": ".test/commands",
            "format": "toml",
            "arg_placeholder": "{{args}}",
            "file_extension": ".toml",
        }
        _write_manifest(tmp_path, data)
        m = AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)
        assert m.commands_dir == ".test/commands"
        assert m.command_format == "toml"
        assert m.arg_placeholder == "{{args}}"
        assert m.file_extension == ".toml"

    def test_tags_field(self, tmp_path):
        data = _minimal_manifest_dict()
        data["tags"] = ["cli", "test", "agent"]
        _write_manifest(tmp_path, data)
        m = AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)
        assert m.tags == ["cli", "test", "agent"]

    def test_optional_fields_default(self, tmp_path):
        """Manifest with only required fields uses sensible defaults."""
        data = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "agent": {"id": "bare", "name": "Bare Agent", "version": "0.0.1"},
        }
        _write_manifest(tmp_path, data)
        m = AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)
        assert m.requires_cli is False
        assert m.install_url is None
        assert m.command_format == "markdown"
        assert m.arg_placeholder == "$ARGUMENTS"
        assert m.tags == []

    def test_from_dict(self):
        data = _minimal_manifest_dict("dict-agent")
        m = AgentManifest.from_dict(data)
        assert m.id == "dict-agent"
        assert m.pack_path is None

    def test_from_dict_not_dict(self):
        with pytest.raises(ManifestValidationError, match="must be a YAML mapping"):
            AgentManifest.from_dict("not-a-dict")


# ===================================================================
# Bootstrap API contract
# ===================================================================

class TestBootstrapContract:
    """Verify AgentBootstrap interface and load_bootstrap()."""

    def test_base_class_setup_raises(self, tmp_path):
        m = AgentManifest.from_dict(_minimal_manifest_dict())
        b = AgentBootstrap(m)
        with pytest.raises(NotImplementedError):
            b.setup(tmp_path, "sh", {})

    def test_base_class_teardown_raises(self, tmp_path):
        m = AgentManifest.from_dict(_minimal_manifest_dict())
        b = AgentBootstrap(m)
        with pytest.raises(NotImplementedError):
            b.teardown(tmp_path)

    def test_load_bootstrap(self, tmp_path):
        data = _minimal_manifest_dict()
        _write_manifest(tmp_path, data)
        _write_bootstrap(tmp_path)
        m = AgentManifest.from_yaml(tmp_path / MANIFEST_FILENAME)
        b = load_bootstrap(tmp_path, m)
        assert isinstance(b, AgentBootstrap)

    def test_load_bootstrap_missing_file(self, tmp_path):
        m = AgentManifest.from_dict(_minimal_manifest_dict())
        with pytest.raises(AgentPackError, match="Bootstrap module not found"):
            load_bootstrap(tmp_path, m)

    def test_bootstrap_setup_and_teardown(self, tmp_path):
        """Verify a loaded bootstrap can set up and tear down."""
        pack_dir = tmp_path / "pack"
        data = _minimal_manifest_dict()
        _write_manifest(pack_dir, data)
        _write_bootstrap(pack_dir)

        m = AgentManifest.from_yaml(pack_dir / MANIFEST_FILENAME)
        b = load_bootstrap(pack_dir, m)

        project = tmp_path / "project"
        project.mkdir()

        b.setup(project, "sh", {})
        assert (project / ".test-agent" / "commands").is_dir()

        b.teardown(project)
        assert not (project / ".test-agent").exists()

    def test_load_bootstrap_no_subclass(self, tmp_path):
        """A bootstrap module without an AgentBootstrap subclass fails."""
        pack_dir = tmp_path / "pack"
        pack_dir.mkdir(parents=True)
        data = _minimal_manifest_dict()
        _write_manifest(pack_dir, data)
        (pack_dir / BOOTSTRAP_FILENAME).write_text("x = 1\n", encoding="utf-8")
        m = AgentManifest.from_yaml(pack_dir / MANIFEST_FILENAME)
        with pytest.raises(AgentPackError, match="No AgentBootstrap subclass"):
            load_bootstrap(pack_dir, m)


# ===================================================================
# Pack resolution
# ===================================================================

class TestResolutionOrder:
    """Verify the 4-level priority resolution stack."""

    def test_embedded_resolution(self):
        """Embedded agents are resolvable (at least claude should exist)."""
        resolved = resolve_agent_pack("claude")
        assert resolved.source == "embedded"
        assert resolved.manifest.id == "claude"

    def test_missing_agent_raises(self):
        with pytest.raises(PackResolutionError, match="not found"):
            resolve_agent_pack("nonexistent-agent-xyz")

    def test_project_level_overrides_embedded(self, tmp_path):
        """A project-level pack shadows the embedded pack."""
        proj_agents = tmp_path / ".specify" / "agents" / "claude"
        data = _minimal_manifest_dict("claude")
        data["agent"]["version"] = "99.0.0"
        _write_manifest(proj_agents, data)
        _write_bootstrap(proj_agents, class_name="ClaudeOverride", agent_dir=".claude")

        resolved = resolve_agent_pack("claude", project_path=tmp_path)
        assert resolved.source == "project"
        assert resolved.manifest.version == "99.0.0"

    def test_user_level_overrides_everything(self, tmp_path, monkeypatch):
        """A user-level pack has highest priority."""
        from specify_cli import agent_pack

        user_dir = tmp_path / "user_agents"
        monkeypatch.setattr(agent_pack, "_user_agents_dir", lambda: user_dir)

        user_pack = user_dir / "claude"
        data = _minimal_manifest_dict("claude")
        data["agent"]["version"] = "999.0.0"
        _write_manifest(user_pack, data)

        # Also create a project-level override
        proj_agents = tmp_path / "project" / ".specify" / "agents" / "claude"
        data2 = _minimal_manifest_dict("claude")
        data2["agent"]["version"] = "50.0.0"
        _write_manifest(proj_agents, data2)

        resolved = resolve_agent_pack("claude", project_path=tmp_path / "project")
        assert resolved.source == "user"
        assert resolved.manifest.version == "999.0.0"

    def test_catalog_overrides_embedded(self, tmp_path, monkeypatch):
        """A catalog-cached pack overrides embedded."""
        from specify_cli import agent_pack

        cache_dir = tmp_path / "agent-cache"
        monkeypatch.setattr(agent_pack, "_catalog_agents_dir", lambda: cache_dir)

        catalog_pack = cache_dir / "claude"
        data = _minimal_manifest_dict("claude")
        data["agent"]["version"] = "2.0.0"
        _write_manifest(catalog_pack, data)

        resolved = resolve_agent_pack("claude")
        assert resolved.source == "catalog"
        assert resolved.manifest.version == "2.0.0"


# ===================================================================
# List and discovery
# ===================================================================

class TestDiscovery:
    """Verify list_embedded_agents() and list_all_agents()."""

    def test_list_embedded_agents_nonempty(self):
        agents = list_embedded_agents()
        assert len(agents) > 0
        ids = {a.id for a in agents}
        # Verify core agents are present
        for core_agent in ("claude", "gemini", "copilot"):
            assert core_agent in ids

    def test_list_all_agents(self):
        all_agents = list_all_agents()
        assert len(all_agents) > 0
        # Should be sorted by id
        ids = [a.manifest.id for a in all_agents]
        assert ids == sorted(ids)
        # Verify core agents are present
        id_set = set(ids)
        for core_agent in ("claude", "gemini", "copilot"):
            assert core_agent in id_set


# ===================================================================
# Validate pack
# ===================================================================

class TestValidatePack:

    def test_valid_pack(self, tmp_path):
        pack_dir = tmp_path / "pack"
        data = _minimal_manifest_dict()
        _write_manifest(pack_dir, data)
        _write_bootstrap(pack_dir)
        warnings = validate_pack(pack_dir)
        assert warnings == []  # All fields present, no warnings

    def test_missing_manifest(self, tmp_path):
        pack_dir = tmp_path / "pack"
        pack_dir.mkdir(parents=True)
        with pytest.raises(ManifestValidationError, match="Missing"):
            validate_pack(pack_dir)

    def test_missing_bootstrap_warning(self, tmp_path):
        pack_dir = tmp_path / "pack"
        data = _minimal_manifest_dict()
        _write_manifest(pack_dir, data)
        warnings = validate_pack(pack_dir)
        assert any("bootstrap.py" in w for w in warnings)

    def test_missing_description_warning(self, tmp_path):
        pack_dir = tmp_path / "pack"
        data = _minimal_manifest_dict()
        data["agent"]["description"] = ""
        _write_manifest(pack_dir, data)
        _write_bootstrap(pack_dir)
        warnings = validate_pack(pack_dir)
        assert any("description" in w for w in warnings)

    def test_missing_tags_warning(self, tmp_path):
        pack_dir = tmp_path / "pack"
        data = _minimal_manifest_dict()
        data["tags"] = []
        _write_manifest(pack_dir, data)
        _write_bootstrap(pack_dir)
        warnings = validate_pack(pack_dir)
        assert any("tags" in w.lower() for w in warnings)


# ===================================================================
# Export pack
# ===================================================================

class TestExportPack:

    def test_export_embedded(self, tmp_path):
        dest = tmp_path / "export"
        result = export_pack("claude", dest)
        assert (result / MANIFEST_FILENAME).is_file()
        assert (result / BOOTSTRAP_FILENAME).is_file()


# ===================================================================
# Embedded packs consistency with AGENT_CONFIG
# ===================================================================

class TestEmbeddedPacksConsistency:
    """Ensure embedded agent packs match the runtime AGENT_CONFIG."""

    def test_all_agent_config_agents_have_embedded_packs(self):
        """Every agent in AGENT_CONFIG (except 'generic') has an embedded pack."""
        from specify_cli import AGENT_CONFIG

        embedded = {m.id for m in list_embedded_agents()}

        for agent_key in AGENT_CONFIG:
            if agent_key == "generic":
                continue
            assert agent_key in embedded, (
                f"Agent '{agent_key}' is in AGENT_CONFIG but has no embedded pack"
            )

    def test_embedded_packs_match_agent_config_metadata(self):
        """Embedded pack manifests are consistent with AGENT_CONFIG fields."""
        from specify_cli import AGENT_CONFIG

        for manifest in list_embedded_agents():
            config = AGENT_CONFIG.get(manifest.id)
            if config is None:
                continue  # Extra embedded packs are fine

            assert manifest.name == config["name"], (
                f"{manifest.id}: name mismatch: pack={manifest.name!r} config={config['name']!r}"
            )
            assert manifest.requires_cli == config["requires_cli"], (
                f"{manifest.id}: requires_cli mismatch"
            )

            if config.get("install_url"):
                assert manifest.install_url == config["install_url"], (
                    f"{manifest.id}: install_url mismatch"
                )

    def test_embedded_packs_match_command_registrar(self):
        """Embedded pack command_registration matches CommandRegistrar.AGENT_CONFIGS."""
        from specify_cli.agents import CommandRegistrar

        for manifest in list_embedded_agents():
            registrar_config = CommandRegistrar.AGENT_CONFIGS.get(manifest.id)
            if registrar_config is None:
                # Some agents in AGENT_CONFIG may not be in the registrar
                # (e.g., agy, vibe — recently added)
                continue

            assert manifest.commands_dir == registrar_config["dir"], (
                f"{manifest.id}: commands_dir mismatch: "
                f"pack={manifest.commands_dir!r} registrar={registrar_config['dir']!r}"
            )
            assert manifest.command_format == registrar_config["format"], (
                f"{manifest.id}: format mismatch"
            )
            assert manifest.arg_placeholder == registrar_config["args"], (
                f"{manifest.id}: arg_placeholder mismatch"
            )
            assert manifest.file_extension == registrar_config["extension"], (
                f"{manifest.id}: file_extension mismatch"
            )

    def test_each_embedded_pack_validates(self):
        """Every embedded pack passes validate_pack()."""
        from specify_cli.agent_pack import _embedded_agents_dir

        agents_dir = _embedded_agents_dir()
        for child in sorted(agents_dir.iterdir()):
            if not child.is_dir():
                continue
            manifest_file = child / MANIFEST_FILENAME
            if not manifest_file.is_file():
                continue
            # Should not raise
            warnings = validate_pack(child)
            # Warnings are acceptable; hard errors are not
