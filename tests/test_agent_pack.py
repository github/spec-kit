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
    AgentFileModifiedError,
    AgentManifest,
    AgentPackError,
    ManifestValidationError,
    PackResolutionError,
    ResolvedPack,
    _manifest_path,
    _sha256,
    check_modified_files,
    export_pack,
    get_tracked_files,
    list_all_agents,
    list_embedded_agents,
    load_bootstrap,
    record_installed_files,
    remove_tracked_files,
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
        from typing import Any, Dict, List, Optional
        from specify_cli.agent_pack import AgentBootstrap, remove_tracked_files

        class {class_name}(AgentBootstrap):
            AGENT_DIR = "{agent_dir}"

            def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> List[Path]:
                (project_path / self.AGENT_DIR / "commands").mkdir(parents=True, exist_ok=True)
                return []

            def teardown(self, project_path: Path, *, force: bool = False, files: Optional[Dict[str, str]] = None) -> List[str]:
                return remove_tracked_files(project_path, self.manifest.id, force=force, files=files)
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
            b.teardown(tmp_path, force=False)

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
        """Verify a loaded bootstrap can set up and tear down via file tracking."""
        pack_dir = tmp_path / "pack"
        data = _minimal_manifest_dict()
        _write_manifest(pack_dir, data)
        _write_bootstrap(pack_dir)

        m = AgentManifest.from_yaml(pack_dir / MANIFEST_FILENAME)
        b = load_bootstrap(pack_dir, m)

        project = tmp_path / "project"
        project.mkdir()

        agent_files = b.setup(project, "sh", {})
        assert isinstance(agent_files, list)
        assert (project / ".test-agent" / "commands").is_dir()

        # Simulate the init pipeline writing a file
        cmd_file = project / ".test-agent" / "commands" / "hello.md"
        cmd_file.write_text("hello", encoding="utf-8")

        # Simulate extension registration writing a file
        ext_file = project / ".test-agent" / "commands" / "ext-cmd.md"
        ext_file.write_text("ext", encoding="utf-8")

        # finalize_setup records both agent and extension files
        b.finalize_setup(project, agent_files=agent_files, extension_files=[ext_file])
        assert _manifest_path(project, "test-agent").is_file()

        # Verify the manifest separates agent and extension files
        manifest_data = json.loads(_manifest_path(project, "test-agent").read_text())
        assert "agent_files" in manifest_data
        assert "extension_files" in manifest_data

        b.teardown(project)
        # The tracked files should be removed
        assert not cmd_file.exists()
        assert not ext_file.exists()
        # Install manifest itself should be cleaned up
        assert not _manifest_path(project, "test-agent").is_file()
        # Directories are preserved (only files are removed)
        assert (project / ".test-agent" / "commands").is_dir()

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


# ===================================================================
# File tracking (record / check / remove)
# ===================================================================

class TestFileTracking:
    """Verify installed-file tracking with hashes."""

    def test_record_and_check_unmodified(self, tmp_path):
        """Files recorded at install time are reported as unmodified."""
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)

        # Create a file to track
        f = project / ".myagent" / "commands" / "hello.md"
        f.parent.mkdir(parents=True)
        f.write_text("hello world", encoding="utf-8")

        record_installed_files(project, "myagent", agent_files=[f])

        # No modifications yet
        assert check_modified_files(project, "myagent") == []

    def test_check_detects_modification(self, tmp_path):
        """A modified file is reported by check_modified_files()."""
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)

        f = project / ".myagent" / "cmd.md"
        f.parent.mkdir(parents=True)
        f.write_text("original", encoding="utf-8")

        record_installed_files(project, "myagent", agent_files=[f])

        # Now modify the file
        f.write_text("modified content", encoding="utf-8")

        modified = check_modified_files(project, "myagent")
        assert len(modified) == 1
        assert ".myagent/cmd.md" in modified[0]

    def test_check_no_manifest(self, tmp_path):
        """check_modified_files returns [] when no manifest exists."""
        assert check_modified_files(tmp_path, "nonexistent") == []

    def test_remove_tracked_unmodified(self, tmp_path):
        """remove_tracked_files deletes unmodified files."""
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)

        f1 = project / ".ag" / "a.md"
        f2 = project / ".ag" / "b.md"
        f1.parent.mkdir(parents=True)
        f1.write_text("aaa", encoding="utf-8")
        f2.write_text("bbb", encoding="utf-8")

        record_installed_files(project, "ag", agent_files=[f1, f2])

        removed = remove_tracked_files(project, "ag")
        assert len(removed) == 2
        assert not f1.exists()
        assert not f2.exists()
        # Directories are preserved
        assert f1.parent.is_dir()
        # Install manifest is cleaned up
        assert not _manifest_path(project, "ag").is_file()

    def test_remove_tracked_modified_without_force_raises(self, tmp_path):
        """Removing modified files without --force raises AgentFileModifiedError."""
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)

        f = project / ".ag" / "c.md"
        f.parent.mkdir(parents=True)
        f.write_text("original", encoding="utf-8")

        record_installed_files(project, "ag", agent_files=[f])
        f.write_text("user-edited", encoding="utf-8")

        with pytest.raises(AgentFileModifiedError, match="modified"):
            remove_tracked_files(project, "ag", force=False)

        # File should still exist
        assert f.is_file()

    def test_remove_tracked_modified_with_force(self, tmp_path):
        """Removing modified files with --force succeeds."""
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)

        f = project / ".ag" / "d.md"
        f.parent.mkdir(parents=True)
        f.write_text("original", encoding="utf-8")

        record_installed_files(project, "ag", agent_files=[f])
        f.write_text("user-edited", encoding="utf-8")

        removed = remove_tracked_files(project, "ag", force=True)
        assert len(removed) == 1
        assert not f.is_file()

    def test_remove_no_manifest(self, tmp_path):
        """remove_tracked_files returns [] when no manifest exists."""
        removed = remove_tracked_files(tmp_path, "nonexistent")
        assert removed == []

    def test_remove_preserves_directories(self, tmp_path):
        """Directories are never deleted, even when all files are removed."""
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)

        d = project / ".myagent" / "commands" / "sub"
        d.mkdir(parents=True)
        f = d / "deep.md"
        f.write_text("deep", encoding="utf-8")

        record_installed_files(project, "myagent", agent_files=[f])
        remove_tracked_files(project, "myagent")

        assert not f.exists()
        # All parent directories remain
        assert d.is_dir()
        assert (project / ".myagent").is_dir()

    def test_deleted_file_skipped_gracefully(self, tmp_path):
        """A file deleted by the user before teardown is silently skipped."""
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)

        f = project / ".ag" / "gone.md"
        f.parent.mkdir(parents=True)
        f.write_text("data", encoding="utf-8")

        record_installed_files(project, "ag", agent_files=[f])

        # User deletes the file before teardown
        f.unlink()

        # Should not raise, and should not report as modified
        assert check_modified_files(project, "ag") == []
        removed = remove_tracked_files(project, "ag")
        assert removed == []

    def test_sha256_consistency(self, tmp_path):
        """_sha256 produces consistent hashes."""
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        h1 = _sha256(f)
        h2 = _sha256(f)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex length

    def test_manifest_json_structure(self, tmp_path):
        """The install manifest has the expected JSON structure."""
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)

        f = project / ".ag" / "x.md"
        f.parent.mkdir(parents=True)
        f.write_text("content", encoding="utf-8")

        manifest_file = record_installed_files(project, "ag", agent_files=[f])
        data = json.loads(manifest_file.read_text(encoding="utf-8"))

        assert data["agent_id"] == "ag"
        assert isinstance(data["agent_files"], dict)
        assert ".ag/x.md" in data["agent_files"]
        assert len(data["agent_files"][".ag/x.md"]) == 64

    # -- New: categorised manifest & explicit file teardown --

    def test_manifest_categorises_agent_and_extension_files(self, tmp_path):
        """record_installed_files stores agent and extension files separately."""
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)

        agent_f = project / ".ag" / "core.md"
        ext_f = project / ".ag" / "ext-cmd.md"
        agent_f.parent.mkdir(parents=True)
        agent_f.write_text("core", encoding="utf-8")
        ext_f.write_text("ext", encoding="utf-8")

        manifest_file = record_installed_files(
            project, "ag", agent_files=[agent_f], extension_files=[ext_f]
        )
        data = json.loads(manifest_file.read_text(encoding="utf-8"))

        assert ".ag/core.md" in data["agent_files"]
        assert ".ag/ext-cmd.md" in data["extension_files"]
        assert ".ag/core.md" not in data.get("extension_files", {})
        assert ".ag/ext-cmd.md" not in data.get("agent_files", {})

    def test_get_tracked_files_returns_both_categories(self, tmp_path):
        """get_tracked_files splits agent and extension files."""
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)

        agent_f = project / ".ag" / "a.md"
        ext_f = project / ".ag" / "e.md"
        agent_f.parent.mkdir(parents=True)
        agent_f.write_text("a", encoding="utf-8")
        ext_f.write_text("e", encoding="utf-8")

        record_installed_files(
            project, "ag", agent_files=[agent_f], extension_files=[ext_f]
        )

        agent_files, extension_files = get_tracked_files(project, "ag")
        assert ".ag/a.md" in agent_files
        assert ".ag/e.md" in extension_files

    def test_get_tracked_files_no_manifest(self, tmp_path):
        """get_tracked_files returns ({}, {}) when no manifest exists."""
        agent_files, extension_files = get_tracked_files(tmp_path, "nope")
        assert agent_files == {}
        assert extension_files == {}

    def test_teardown_with_explicit_files(self, tmp_path):
        """teardown accepts explicit files dict (CLI-driven teardown)."""
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)

        f1 = project / ".ag" / "a.md"
        f2 = project / ".ag" / "b.md"
        f1.parent.mkdir(parents=True)
        f1.write_text("aaa", encoding="utf-8")
        f2.write_text("bbb", encoding="utf-8")

        # Record the files
        record_installed_files(project, "ag", agent_files=[f1, f2])

        # Get the tracked entries
        agent_entries, _ = get_tracked_files(project, "ag")

        # Pass explicit files to remove_tracked_files
        removed = remove_tracked_files(project, "ag", files=agent_entries)
        assert len(removed) == 2
        assert not f1.exists()
        assert not f2.exists()

    def test_check_detects_extension_file_modification(self, tmp_path):
        """Modified extension files are also detected by check_modified_files."""
        project = tmp_path / "project"
        (project / ".specify").mkdir(parents=True)

        ext_f = project / ".ag" / "ext.md"
        ext_f.parent.mkdir(parents=True)
        ext_f.write_text("original", encoding="utf-8")

        record_installed_files(project, "ag", extension_files=[ext_f])

        ext_f.write_text("user-edited", encoding="utf-8")

        modified = check_modified_files(project, "ag")
        assert len(modified) == 1
        assert ".ag/ext.md" in modified[0]


# ===================================================================
# setup() returns actual files (not empty list)
# ===================================================================

class TestSetupReturnsFiles:
    """Verify that every embedded agent's ``setup()`` calls the shared
    scaffolding and returns the actual files it created — not an empty
    list."""

    @pytest.mark.parametrize("agent", [
        a for a in __import__("specify_cli").AGENT_CONFIG if a != "generic"
    ])
    def test_setup_returns_nonempty_file_list(self, agent, tmp_path):
        """setup() must return at least one Path (the scaffolded command
        files, scripts, templates, etc.)."""
        resolved = resolve_agent_pack(agent)
        bootstrap = load_bootstrap(resolved.path, resolved.manifest)

        project = tmp_path / f"setup_{agent}"
        project.mkdir()

        files = bootstrap.setup(project, "sh", {})
        assert isinstance(files, list)
        assert len(files) > 0, (
            f"Agent '{agent}': setup() returned an empty list — "
            f"it must return the files it installed")

    @pytest.mark.parametrize("agent", [
        a for a in __import__("specify_cli").AGENT_CONFIG if a != "generic"
    ])
    def test_setup_returns_only_existing_paths(self, agent, tmp_path):
        """Every path returned by setup() must exist on disk."""
        resolved = resolve_agent_pack(agent)
        bootstrap = load_bootstrap(resolved.path, resolved.manifest)

        project = tmp_path / f"exists_{agent}"
        project.mkdir()

        files = bootstrap.setup(project, "sh", {})
        for f in files:
            assert f.is_file(), (
                f"Agent '{agent}': setup() returned '{f}' but it "
                f"does not exist on disk")

    @pytest.mark.parametrize("agent", [
        a for a in __import__("specify_cli").AGENT_CONFIG if a != "generic"
    ])
    def test_setup_returns_absolute_paths(self, agent, tmp_path):
        """setup() must return absolute paths."""
        resolved = resolve_agent_pack(agent)
        bootstrap = load_bootstrap(resolved.path, resolved.manifest)

        project = tmp_path / f"abs_{agent}"
        project.mkdir()

        files = bootstrap.setup(project, "sh", {})
        for f in files:
            assert f.is_absolute(), (
                f"Agent '{agent}': setup() returned relative path '{f}'")

    @pytest.mark.parametrize("agent", [
        a for a in __import__("specify_cli").AGENT_CONFIG if a != "generic"
    ])
    def test_setup_returns_include_agent_dir_files(self, agent, tmp_path):
        """setup() return list must include files under the agent's
        directory tree (these are the files tracked for teardown)."""
        resolved = resolve_agent_pack(agent)
        bootstrap = load_bootstrap(resolved.path, resolved.manifest)

        project = tmp_path / f"agentdir_{agent}"
        project.mkdir()

        files = bootstrap.setup(project, "sh", {})
        agent_root = bootstrap.agent_dir(project)

        agent_dir_files = [
            f for f in files
            if f.resolve().is_relative_to(agent_root.resolve())
        ]
        assert len(agent_dir_files) > 0, (
            f"Agent '{agent}': setup() returned no files under "
            f"'{agent_root.relative_to(project)}'")


# ===================================================================
# --agent / --ai parity via CliRunner (end-to-end init command)
# ===================================================================

def _collect_project_files(
    root: Path,
    *,
    exclude_metadata: bool = False,
) -> dict[str, bytes]:
    """Walk *root* and return ``{relative_posix_path: file_bytes}``.

    When *exclude_metadata* is True, files that are expected to differ
    between ``--ai`` and ``--agent`` flows are excluded:

    - ``.specify/agent-manifest-*.json`` (tracking data, ``--agent`` only)
    - ``.specify/init-options.json`` (contains ``agent_pack`` flag)
    """
    result: dict[str, bytes] = {}
    for p in root.rglob("*"):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            if exclude_metadata:
                if rel.startswith(".specify/agent-manifest-"):
                    continue
                if rel == ".specify/init-options.json":
                    continue
            result[rel] = p.read_bytes()
    return result


# All agents except "generic" (which requires --ai-commands-dir)
_ALL_AGENTS = [a for a in __import__("specify_cli").AGENT_CONFIG if a != "generic"]


def _run_init_via_cli(
    project_dir: Path,
    agent: str,
    *,
    use_agent_flag: bool,
) -> tuple[int, str]:
    """Invoke ``specify init <project_dir> --ai/--agent <agent>`` via CliRunner.

    Patches ``download_and_extract_template`` to use
    ``scaffold_from_core_pack`` so the test works without network access
    while exercising the real CLI code path — the same functions and
    branching that the user runs.

    Returns ``(exit_code, captured_output)``.
    """
    from unittest.mock import patch as _patch

    from typer.testing import CliRunner

    from specify_cli import app as specify_app
    from specify_cli import scaffold_from_core_pack as _scaffold

    runner = CliRunner()

    def _mock_download(
        project_path, ai_assistant, script_type,
        is_current_dir=False, **kwargs,
    ):
        ok = _scaffold(project_path, ai_assistant, script_type, is_current_dir)
        if not ok:
            raise RuntimeError(
                f"scaffold_from_core_pack failed for {ai_assistant}")
        tracker = kwargs.get("tracker")
        if tracker:
            for key in [
                "fetch", "download", "extract",
                "zip-list", "extracted-summary",
            ]:
                try:
                    tracker.start(key)
                    tracker.complete(key, "mocked")
                except Exception:
                    pass

    flag = "--agent" if use_agent_flag else "--ai"
    args = [
        "init", str(project_dir),
        flag, agent,
        "--no-git", "--ignore-agent-tools",
    ]

    # Agents migrated to skills need --ai-skills to avoid the fail-fast
    # migration error — same requirement as the real CLI.
    try:
        from specify_cli import AGENT_SKILLS_MIGRATIONS
        if agent in AGENT_SKILLS_MIGRATIONS:
            args.append("--ai-skills")
    except (ImportError, AttributeError):
        pass

    with _patch(
        "specify_cli.download_and_extract_template", _mock_download,
    ):
        result = runner.invoke(specify_app, args)

    return result.exit_code, result.output or ""


class TestInitFlowParity:
    """End-to-end parity: ``specify init --ai`` and ``specify init --agent``
    produce identical project files for every supported agent.

    Each test invokes the actual CLI via ``typer.testing.CliRunner`` with the
    network download mocked so both flows exercise the same init pipeline
    without requiring internet access.

    The ``--agent`` flow additionally calls ``finalize_setup()`` which writes
    a tracking manifest in ``.specify/agent-manifest-<id>.json``.  Aside from
    that manifest and the ``agent_pack`` key in ``init-options.json``, every
    project file must be byte-for-byte identical between the two flows.

    All {n} non-generic agents are tested.
    """.format(n=len(_ALL_AGENTS))

    # -- per-class lazy caches (init is run once per agent per flow) --------

    @pytest.fixture(scope="class")
    def ai_projects(self, tmp_path_factory):
        """Cache: run ``specify init --ai`` once per agent."""
        cache: dict[str, tuple[Path, int, str]] = {}
        def _get(agent: str) -> Path:
            if agent not in cache:
                project = tmp_path_factory.mktemp("parity_ai") / agent
                exit_code, output = _run_init_via_cli(
                    project, agent, use_agent_flag=False)
                cache[agent] = (project, exit_code, output)
            project, exit_code, output = cache[agent]
            assert exit_code == 0, (
                f"specify init --ai {agent} failed (exit {exit_code}):\n"
                f"{output}")
            return project
        return _get

    @pytest.fixture(scope="class")
    def agent_projects(self, tmp_path_factory):
        """Cache: run ``specify init --agent`` once per agent."""
        cache: dict[str, tuple[Path, int, str]] = {}
        def _get(agent: str) -> Path:
            if agent not in cache:
                project = tmp_path_factory.mktemp("parity_agent") / agent
                exit_code, output = _run_init_via_cli(
                    project, agent, use_agent_flag=True)
                cache[agent] = (project, exit_code, output)
            project, exit_code, output = cache[agent]
            assert exit_code == 0, (
                f"specify init --agent {agent} failed (exit {exit_code}):\n"
                f"{output}")
            return project
        return _get

    # -- parametrized parity tests over every agent -------------------------

    @pytest.mark.parametrize("agent", _ALL_AGENTS)
    def test_ai_init_succeeds(self, agent, ai_projects):
        """``specify init --ai <agent>`` completes successfully."""
        assert ai_projects(agent).is_dir()

    @pytest.mark.parametrize("agent", _ALL_AGENTS)
    def test_agent_init_succeeds(self, agent, agent_projects):
        """``specify init --agent <agent>`` completes successfully."""
        assert agent_projects(agent).is_dir()

    @pytest.mark.parametrize("agent", _ALL_AGENTS)
    def test_same_file_set(self, agent, ai_projects, agent_projects):
        """--ai and --agent produce the same set of project files."""
        ai_files = _collect_project_files(
            ai_projects(agent), exclude_metadata=True)
        agent_files = _collect_project_files(
            agent_projects(agent), exclude_metadata=True)

        only_ai = sorted(set(ai_files) - set(agent_files))
        only_agent = sorted(set(agent_files) - set(ai_files))

        assert not only_ai, (
            f"Agent '{agent}': files only in --ai output:\n  "
            + "\n  ".join(only_ai))
        assert not only_agent, (
            f"Agent '{agent}': files only in --agent output:\n  "
            + "\n  ".join(only_agent))

    @pytest.mark.parametrize("agent", _ALL_AGENTS)
    def test_same_file_contents(self, agent, ai_projects, agent_projects):
        """--ai and --agent produce byte-for-byte identical file contents."""
        ai_files = _collect_project_files(
            ai_projects(agent), exclude_metadata=True)
        agent_files = _collect_project_files(
            agent_projects(agent), exclude_metadata=True)

        for name in ai_files:
            if name not in agent_files:
                continue  # caught by test_same_file_set
            assert ai_files[name] == agent_files[name], (
                f"Agent '{agent}': file '{name}' content differs "
                f"between --ai and --agent flows")

    @pytest.mark.parametrize("agent", _ALL_AGENTS)
    def test_same_directory_structure(self, agent, ai_projects, agent_projects):
        """--ai and --agent produce the same directory tree."""
        def _dirs(root: Path) -> set[str]:
            return {
                p.relative_to(root).as_posix()
                for p in root.rglob("*") if p.is_dir()
            }

        ai_dirs = _dirs(ai_projects(agent))
        agent_dirs = _dirs(agent_projects(agent))

        only_ai = sorted(ai_dirs - agent_dirs)
        only_agent = sorted(agent_dirs - ai_dirs)

        assert not only_ai, (
            f"Agent '{agent}': dirs only in --ai:\n  "
            + "\n  ".join(only_ai))
        assert not only_agent, (
            f"Agent '{agent}': dirs only in --agent:\n  "
            + "\n  ".join(only_agent))

    # -- pack lifecycle (setup / finalize / teardown) -----------------------

    @pytest.mark.parametrize("agent", _ALL_AGENTS)
    def test_agent_resolves_through_pack_system(self, agent):
        """Every AGENT_CONFIG agent resolves a valid pack."""
        try:
            resolved = resolve_agent_pack(agent)
        except PackResolutionError:
            pytest.fail(f"--agent {agent} would fail: no pack found")
        assert resolved.manifest.id == agent

    @pytest.mark.parametrize("agent", _ALL_AGENTS)
    def test_setup_creates_commands_dir(self, agent, agent_projects):
        """The pack's setup() creates the commands directory that the
        scaffold pipeline writes command files into.

        For agents that migrate to skills (``--ai-skills``), the commands
        directory is replaced by a skills directory during init — verify
        that the agent directory itself exists instead.
        """
        project = agent_projects(agent)
        resolved = resolve_agent_pack(agent)
        cmd_dir = project / resolved.manifest.commands_dir

        if cmd_dir.is_dir():
            return  # commands directory present — normal flow

        # For skills-migrated agents, the commands dir is removed and
        # replaced by a skills dir.  Verify the parent agent dir exists.
        try:
            from specify_cli import AGENT_SKILLS_MIGRATIONS
            if agent in AGENT_SKILLS_MIGRATIONS:
                agent_dir = cmd_dir.parent
                assert agent_dir.is_dir(), (
                    f"Agent '{agent}': agent dir "
                    f"'{agent_dir.relative_to(project)}' missing "
                    f"(skills migration removes commands)")
                return
        except (ImportError, AttributeError):
            pass

        pytest.fail(
            f"Agent '{agent}': commands_dir "
            f"'{resolved.manifest.commands_dir}' not present after init")

    @pytest.mark.parametrize("agent", _ALL_AGENTS)
    def test_commands_dir_matches_agent_config(self, agent):
        """Pack commands_dir matches the directory derived from AGENT_CONFIG."""
        from specify_cli import AGENT_CONFIG

        config = AGENT_CONFIG[agent]
        try:
            resolved = resolve_agent_pack(agent)
        except PackResolutionError:
            pytest.fail(f"No pack for {agent}")

        folder = config.get("folder", "").rstrip("/")
        subdir = config.get("commands_subdir", "commands")
        expected = (f"{folder}/{subdir}" if folder else "").lstrip("/")

        assert resolved.manifest.commands_dir == expected, (
            f"{agent}: pack={resolved.manifest.commands_dir!r} "
            f"vs config={expected!r}")

    @pytest.mark.parametrize("agent", _ALL_AGENTS)
    def test_tracking_manifest_present(self, agent, agent_projects):
        """--agent flow writes an install manifest for tracked teardown."""
        manifest = _manifest_path(agent_projects(agent), agent)
        assert manifest.is_file(), (
            f"Agent '{agent}': missing tracking manifest")

    @pytest.mark.parametrize("agent", _ALL_AGENTS)
    def test_tracking_manifest_records_all_commands(self, agent, agent_projects):
        """The install manifest tracks every file in the commands (or skills)
        directory that exists after init."""
        project = agent_projects(agent)
        resolved = resolve_agent_pack(agent)
        cmd_dir = project / resolved.manifest.commands_dir

        # For skills-migrated agents the commands_dir is removed.
        # Check the parent agent dir for skills files instead.
        if not cmd_dir.is_dir():
            try:
                from specify_cli import AGENT_SKILLS_MIGRATIONS
                if agent in AGENT_SKILLS_MIGRATIONS:
                    cmd_dir = cmd_dir.parent
                    if not cmd_dir.is_dir():
                        pytest.skip(
                            f"{agent}: skills dir not present")
            except (ImportError, AttributeError):
                pytest.skip(f"{agent}: commands_dir missing")

        # Actual files on disk
        on_disk = {
            p.relative_to(project).as_posix()
            for p in cmd_dir.rglob("*") if p.is_file()
        }

        # Files recorded in the tracking manifest
        manifest = _manifest_path(project, agent)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        tracked = {
            *data.get("agent_files", {}),
            *data.get("extension_files", {}),
        }

        missing = on_disk - tracked
        assert not missing, (
            f"Agent '{agent}': files not tracked by manifest:\n  "
            + "\n  ".join(sorted(missing)))

    @pytest.mark.parametrize("agent", _ALL_AGENTS)
    def test_teardown_removes_all_tracked_files(self, agent, tmp_path):
        """Full lifecycle: setup → scaffold → finalize → teardown.

        After teardown every tracked file must be deleted, but directories
        are preserved.  This proves the pack's teardown() is functional.
        """
        from specify_cli import scaffold_from_core_pack

        project = tmp_path / f"lifecycle_{agent}"
        project.mkdir()

        # 1. Scaffold (same as init pipeline)
        ok = scaffold_from_core_pack(project, agent, "sh")
        assert ok, f"scaffold failed for {agent}"

        # 2. Resolve pack and finalize
        resolved = resolve_agent_pack(agent)
        bootstrap = load_bootstrap(resolved.path, resolved.manifest)
        bootstrap.finalize_setup(project)

        # 3. Read tracked files
        agent_files, ext_files = get_tracked_files(project, agent)
        all_tracked = {**agent_files, **ext_files}
        assert len(all_tracked) > 0, f"{agent}: no files tracked"

        # 4. Teardown
        removed = remove_tracked_files(
            project, agent, force=True, files=all_tracked)
        assert len(removed) > 0, f"{agent}: teardown removed nothing"

        # 5. Verify all tracked files are gone
        for rel_path in all_tracked:
            assert not (project / rel_path).exists(), (
                f"{agent}: '{rel_path}' still present after teardown")

    # -- extension registration metadata ------------------------------------

    @pytest.mark.parametrize("agent", _ALL_AGENTS)
    def test_extension_registration_metadata_matches(self, agent):
        """Pack command_registration matches CommandRegistrar config."""
        from specify_cli.agents import CommandRegistrar

        try:
            resolved = resolve_agent_pack(agent)
        except PackResolutionError:
            pytest.skip(f"No pack for {agent}")

        reg = CommandRegistrar.AGENT_CONFIGS.get(agent)
        if reg is None:
            pytest.skip(f"No CommandRegistrar config for {agent}")

        m = resolved.manifest
        assert m.commands_dir == reg["dir"]
        assert m.command_format == reg["format"]
        assert m.arg_placeholder == reg["args"]
        assert m.file_extension == reg["extension"]
