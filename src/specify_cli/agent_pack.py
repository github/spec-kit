"""
Agent Pack Manager for Spec Kit

Implements self-bootstrapping agent packs with declarative manifests
(speckit-agent.yml) and Python bootstrap modules (bootstrap.py).

Agent packs resolve by priority:
  1. User-level   (~/.specify/agents/<id>/)
  2. Project-level (.specify/agents/<id>/)
  3. Catalog-installed (downloaded via `specify agent add`)
  4. Embedded in wheel (official packs under core_pack/agents/)

The embedded packs ship inside the pip wheel so that
`pip install specify-cli && specify init --ai claude` works offline.
"""

import hashlib
import importlib.util
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from platformdirs import user_data_path


# ---------------------------------------------------------------------------
# Manifest schema
# ---------------------------------------------------------------------------

MANIFEST_FILENAME = "speckit-agent.yml"
BOOTSTRAP_FILENAME = "bootstrap.py"

MANIFEST_SCHEMA_VERSION = "1.0"

# Required top-level keys
_REQUIRED_TOP_KEYS = {"schema_version", "agent"}

# Required keys within the ``agent`` block
_REQUIRED_AGENT_KEYS = {"id", "name", "version"}


class AgentPackError(Exception):
    """Base exception for agent-pack operations."""


class ManifestValidationError(AgentPackError):
    """Raised when a speckit-agent.yml file is invalid."""


class PackResolutionError(AgentPackError):
    """Raised when no pack can be found for the requested agent id."""


class AgentFileModifiedError(AgentPackError):
    """Raised when teardown finds user-modified files and ``--force`` is not set."""


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

@dataclass
class AgentManifest:
    """Parsed and validated representation of a speckit-agent.yml file."""

    # identity
    id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = ""

    # runtime
    requires_cli: bool = False
    install_url: Optional[str] = None
    cli_tool: Optional[str] = None

    # compatibility
    speckit_version: str = ">=0.1.0"

    # discovery
    tags: List[str] = field(default_factory=list)

    # command registration metadata (used by CommandRegistrar / extensions)
    commands_dir: str = ""
    command_format: str = "markdown"
    arg_placeholder: str = "$ARGUMENTS"
    file_extension: str = ".md"

    # raw data for anything else
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    # filesystem path to the pack directory that produced this manifest
    pack_path: Optional[Path] = field(default=None, repr=False)

    @classmethod
    def from_yaml(cls, path: Path) -> "AgentManifest":
        """Load and validate a manifest from *path*.

        Raises ``ManifestValidationError`` on structural problems.
        """
        try:
            text = path.read_text(encoding="utf-8")
            data = yaml.safe_load(text) or {}
        except yaml.YAMLError as exc:
            raise ManifestValidationError(f"Invalid YAML in {path}: {exc}")
        except FileNotFoundError:
            raise ManifestValidationError(f"Manifest not found: {path}")

        return cls.from_dict(data, pack_path=path.parent)

    @classmethod
    def from_dict(cls, data: dict, *, pack_path: Optional[Path] = None) -> "AgentManifest":
        """Build a manifest from a raw dictionary."""
        if not isinstance(data, dict):
            raise ManifestValidationError("Manifest must be a YAML mapping")

        missing_top = _REQUIRED_TOP_KEYS - set(data)
        if missing_top:
            raise ManifestValidationError(
                f"Missing required top-level key(s): {', '.join(sorted(missing_top))}"
            )

        if data.get("schema_version") != MANIFEST_SCHEMA_VERSION:
            raise ManifestValidationError(
                f"Unsupported schema_version: {data.get('schema_version')!r} "
                f"(expected {MANIFEST_SCHEMA_VERSION!r})"
            )

        agent_block = data.get("agent")
        if not isinstance(agent_block, dict):
            raise ManifestValidationError("'agent' must be a mapping")

        missing_agent = _REQUIRED_AGENT_KEYS - set(agent_block)
        if missing_agent:
            raise ManifestValidationError(
                f"Missing required agent key(s): {', '.join(sorted(missing_agent))}"
            )

        runtime = data.get("runtime") or {}
        requires = data.get("requires") or {}
        tags = data.get("tags") or []
        cmd_reg = data.get("command_registration") or {}

        return cls(
            id=str(agent_block["id"]),
            name=str(agent_block["name"]),
            version=str(agent_block["version"]),
            description=str(agent_block.get("description", "")),
            author=str(agent_block.get("author", "")),
            license=str(agent_block.get("license", "")),
            requires_cli=bool(runtime.get("requires_cli", False)),
            install_url=runtime.get("install_url"),
            cli_tool=runtime.get("cli_tool"),
            speckit_version=str(requires.get("speckit_version", ">=0.1.0")),
            tags=[str(t) for t in tags] if isinstance(tags, list) else [],
            commands_dir=str(cmd_reg.get("commands_dir", "")),
            command_format=str(cmd_reg.get("format", "markdown")),
            arg_placeholder=str(cmd_reg.get("arg_placeholder", "$ARGUMENTS")),
            file_extension=str(cmd_reg.get("file_extension", ".md")),
            raw=data,
            pack_path=pack_path,
        )


# ---------------------------------------------------------------------------
# Bootstrap base class
# ---------------------------------------------------------------------------

class AgentBootstrap:
    """Base class that every agent pack's ``bootstrap.py`` must subclass.

    Subclasses override :meth:`setup` and :meth:`teardown` to define
    agent-specific lifecycle operations.
    """

    def __init__(self, manifest: AgentManifest):
        self.manifest = manifest
        self.pack_path = manifest.pack_path

    # -- lifecycle -----------------------------------------------------------

    def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
        """Install agent files into *project_path*.

        This is invoked by ``specify init --ai <agent>`` and
        ``specify agent switch <agent>``.

        Args:
            project_path: Target project directory.
            script_type: ``"sh"`` or ``"ps"``.
            options: Arbitrary key/value options forwarded from the CLI.
        """
        raise NotImplementedError

    def teardown(self, project_path: Path, *, force: bool = False) -> None:
        """Remove agent-specific files from *project_path*.

        Invoked by ``specify agent switch`` (for the *old* agent) and
        ``specify agent remove`` when the user explicitly uninstalls.
        Must preserve shared infrastructure (specs, plans, tasks, etc.).

        Only individual files recorded in the install manifest are removed
        — directories are never deleted.  If any tracked file has been
        modified since installation and *force* is ``False``, raises
        :class:`AgentFileModifiedError`.

        Args:
            project_path: Project directory to clean up.
            force: When ``True``, remove files even if they were modified
                after installation.
        """
        raise NotImplementedError

    # -- helpers available to subclasses ------------------------------------

    def agent_dir(self, project_path: Path) -> Path:
        """Return the agent's top-level directory inside the project."""
        return project_path / self.manifest.commands_dir.split("/")[0]

    def finalize_setup(self, project_path: Path) -> None:
        """Record all files in the agent directory for tracked teardown.

        This must be called **after** the full init pipeline has finished
        writing files (commands, context files, etc.) into the agent
        directory.  It scans ``self.manifest.commands_dir`` and records
        every file with its SHA-256 hash so that :meth:`teardown` can
        detect user modifications.
        """
        if not self.manifest.commands_dir:
            return
        commands_dir = project_path / self.manifest.commands_dir
        if commands_dir.is_dir():
            installed = [p for p in commands_dir.rglob("*") if p.is_file()]
            record_installed_files(project_path, self.manifest.id, installed)


# ---------------------------------------------------------------------------
# Installed-file tracking
# ---------------------------------------------------------------------------

def _manifest_path(project_path: Path, agent_id: str) -> Path:
    """Return the path to the install manifest for *agent_id*."""
    return project_path / ".specify" / f"agent-manifest-{agent_id}.json"


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def record_installed_files(
    project_path: Path,
    agent_id: str,
    files: List[Path],
) -> Path:
    """Record the installed files and their SHA-256 hashes.

    Writes ``.specify/agent-manifest-<agent_id>.json`` containing a
    mapping of project-relative paths to their SHA-256 digests.

    Args:
        project_path: Project root directory.
        agent_id: Agent identifier.
        files: Absolute or project-relative paths of the files that
            were created during ``setup()``.

    Returns:
        Path to the written manifest file.
    """
    entries: Dict[str, str] = {}
    for file_path in files:
        abs_path = project_path / file_path if not file_path.is_absolute() else file_path
        if abs_path.is_file():
            rel = str(abs_path.relative_to(project_path))
            entries[rel] = _sha256(abs_path)

    manifest_file = _manifest_path(project_path, agent_id)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(
        json.dumps({"agent_id": agent_id, "files": entries}, indent=2),
        encoding="utf-8",
    )
    return manifest_file


def check_modified_files(
    project_path: Path,
    agent_id: str,
) -> List[str]:
    """Return project-relative paths of files modified since installation.

    Returns an empty list when no install manifest exists or when every
    tracked file still has its original hash.
    """
    manifest_file = _manifest_path(project_path, agent_id)
    if not manifest_file.is_file():
        return []

    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    modified: List[str] = []
    for rel_path, original_hash in data.get("files", {}).items():
        abs_path = project_path / rel_path
        if abs_path.is_file():
            if _sha256(abs_path) != original_hash:
                modified.append(rel_path)
        # If the file was deleted by the user, treat it as not needing
        # removal — skip rather than flag as modified.

    return modified


def remove_tracked_files(
    project_path: Path,
    agent_id: str,
    *,
    force: bool = False,
) -> List[str]:
    """Remove the individual files recorded in the install manifest.

    Raises :class:`AgentFileModifiedError` if any tracked file was
    modified and *force* is ``False``.

    Directories are **never** deleted — only individual files.

    Args:
        project_path: Project root directory.
        agent_id: Agent identifier.
        force: When ``True``, delete even modified files.

    Returns:
        List of project-relative paths that were removed.
    """
    manifest_file = _manifest_path(project_path, agent_id)
    if not manifest_file.is_file():
        return []

    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    entries: Dict[str, str] = data.get("files", {})
    if not entries:
        manifest_file.unlink(missing_ok=True)
        return []

    if not force:
        modified = check_modified_files(project_path, agent_id)
        if modified:
            raise AgentFileModifiedError(
                f"The following agent files have been modified since installation:\n"
                + "\n".join(f"  {p}" for p in modified)
                + "\nUse --force to remove them anyway."
            )

    removed: List[str] = []
    for rel_path in entries:
        abs_path = project_path / rel_path
        if abs_path.is_file():
            abs_path.unlink()
            removed.append(rel_path)

    # Clean up the install manifest itself
    manifest_file.unlink(missing_ok=True)
    return removed


# ---------------------------------------------------------------------------
# Pack resolution
# ---------------------------------------------------------------------------

def _embedded_agents_dir() -> Path:
    """Return the path to the embedded agent packs inside the wheel."""
    return Path(__file__).parent / "core_pack" / "agents"


def _user_agents_dir() -> Path:
    """Return the user-level agent overrides directory."""
    return user_data_path("specify", "github") / "agents"


def _project_agents_dir(project_path: Path) -> Path:
    """Return the project-level agent overrides directory."""
    return project_path / ".specify" / "agents"


def _catalog_agents_dir() -> Path:
    """Return the catalog-installed agent cache directory."""
    return user_data_path("specify", "github") / "agent-cache"


@dataclass
class ResolvedPack:
    """Result of resolving an agent pack through the priority stack."""
    manifest: AgentManifest
    source: str          # "user", "project", "catalog", "embedded"
    path: Path
    overrides: Optional[str] = None  # version of the pack being overridden


def resolve_agent_pack(
    agent_id: str,
    project_path: Optional[Path] = None,
) -> ResolvedPack:
    """Resolve an agent pack through the priority stack.

    Priority (highest first):
      1. User-level     ``~/.specify/agents/<id>/``
      2. Project-level  ``.specify/agents/<id>/``
      3. Catalog-installed cache
      4. Embedded in wheel

    Raises ``PackResolutionError`` when no pack is found at any level.
    """
    candidates: List[tuple[str, Path]] = []

    # Priority 1 — user level
    user_dir = _user_agents_dir() / agent_id
    candidates.append(("user", user_dir))

    # Priority 2 — project level
    if project_path is not None:
        proj_dir = _project_agents_dir(project_path) / agent_id
        candidates.append(("project", proj_dir))

    # Priority 3 — catalog cache
    catalog_dir = _catalog_agents_dir() / agent_id
    candidates.append(("catalog", catalog_dir))

    # Priority 4 — embedded
    embedded_dir = _embedded_agents_dir() / agent_id
    candidates.append(("embedded", embedded_dir))

    embedded_manifest: Optional[AgentManifest] = None

    for source, pack_dir in candidates:
        manifest_file = pack_dir / MANIFEST_FILENAME
        if manifest_file.is_file():
            manifest = AgentManifest.from_yaml(manifest_file)
            if source == "embedded":
                embedded_manifest = manifest

            overrides = None
            if source != "embedded" and embedded_manifest is None:
                # Try loading embedded to record what it overrides
                emb_file = _embedded_agents_dir() / agent_id / MANIFEST_FILENAME
                if emb_file.is_file():
                    try:
                        emb = AgentManifest.from_yaml(emb_file)
                        overrides = f"embedded v{emb.version}"
                    except AgentPackError:
                        pass

            return ResolvedPack(
                manifest=manifest,
                source=source,
                path=pack_dir,
                overrides=overrides,
            )

    raise PackResolutionError(
        f"Agent '{agent_id}' not found locally or in any active catalog.\n"
        f"Run 'specify agent search' to browse available agents, or\n"
        f"'specify agent add {agent_id} --from <path>' for offline install."
    )


# ---------------------------------------------------------------------------
# Pack discovery helpers
# ---------------------------------------------------------------------------

def list_embedded_agents() -> List[AgentManifest]:
    """Return manifests for all agent packs embedded in the wheel."""
    agents_dir = _embedded_agents_dir()
    if not agents_dir.is_dir():
        return []

    manifests: List[AgentManifest] = []
    for child in sorted(agents_dir.iterdir()):
        manifest_file = child / MANIFEST_FILENAME
        if child.is_dir() and manifest_file.is_file():
            try:
                manifests.append(AgentManifest.from_yaml(manifest_file))
            except AgentPackError:
                continue
    return manifests


def list_all_agents(project_path: Optional[Path] = None) -> List[ResolvedPack]:
    """List all available agents, resolved through the priority stack.

    Each agent id appears at most once, at its highest-priority source.
    """
    seen: dict[str, ResolvedPack] = {}

    # Start from lowest priority (embedded) so higher priorities overwrite
    for manifest in list_embedded_agents():
        seen[manifest.id] = ResolvedPack(
            manifest=manifest,
            source="embedded",
            path=manifest.pack_path or _embedded_agents_dir() / manifest.id,
        )

    # Catalog cache
    catalog_dir = _catalog_agents_dir()
    if catalog_dir.is_dir():
        for child in sorted(catalog_dir.iterdir()):
            mf = child / MANIFEST_FILENAME
            if child.is_dir() and mf.is_file():
                try:
                    m = AgentManifest.from_yaml(mf)
                    overrides = f"embedded v{seen[m.id].manifest.version}" if m.id in seen else None
                    seen[m.id] = ResolvedPack(manifest=m, source="catalog", path=child, overrides=overrides)
                except AgentPackError:
                    continue

    # Project-level
    if project_path is not None:
        proj_dir = _project_agents_dir(project_path)
        if proj_dir.is_dir():
            for child in sorted(proj_dir.iterdir()):
                mf = child / MANIFEST_FILENAME
                if child.is_dir() and mf.is_file():
                    try:
                        m = AgentManifest.from_yaml(mf)
                        overrides = f"embedded v{seen[m.id].manifest.version}" if m.id in seen else None
                        seen[m.id] = ResolvedPack(manifest=m, source="project", path=child, overrides=overrides)
                    except AgentPackError:
                        continue

    # User-level
    user_dir = _user_agents_dir()
    if user_dir.is_dir():
        for child in sorted(user_dir.iterdir()):
            mf = child / MANIFEST_FILENAME
            if child.is_dir() and mf.is_file():
                try:
                    m = AgentManifest.from_yaml(mf)
                    overrides = f"embedded v{seen[m.id].manifest.version}" if m.id in seen else None
                    seen[m.id] = ResolvedPack(manifest=m, source="user", path=child, overrides=overrides)
                except AgentPackError:
                    continue

    return sorted(seen.values(), key=lambda r: r.manifest.id)


def load_bootstrap(pack_path: Path, manifest: AgentManifest) -> AgentBootstrap:
    """Import ``bootstrap.py`` from *pack_path* and return the bootstrap instance.

    The bootstrap module must define exactly one public subclass of
    ``AgentBootstrap``.  That class is instantiated with *manifest* and
    returned.
    """
    bootstrap_file = pack_path / BOOTSTRAP_FILENAME
    if not bootstrap_file.is_file():
        raise AgentPackError(
            f"Bootstrap module not found: {bootstrap_file}"
        )

    spec = importlib.util.spec_from_file_location(
        f"speckit_agent_{manifest.id}_bootstrap", bootstrap_file
    )
    if spec is None or spec.loader is None:
        raise AgentPackError(f"Cannot load bootstrap module: {bootstrap_file}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find the AgentBootstrap subclass
    candidates = [
        obj
        for name, obj in vars(module).items()
        if (
            isinstance(obj, type)
            and issubclass(obj, AgentBootstrap)
            and obj is not AgentBootstrap
            and not name.startswith("_")
        )
    ]
    if not candidates:
        raise AgentPackError(
            f"No AgentBootstrap subclass found in {bootstrap_file}"
        )
    if len(candidates) > 1:
        raise AgentPackError(
            f"Multiple AgentBootstrap subclasses in {bootstrap_file}: "
            f"{[c.__name__ for c in candidates]}"
        )

    return candidates[0](manifest)


def validate_pack(pack_path: Path) -> List[str]:
    """Validate a pack directory structure and return a list of warnings.

    Returns an empty list when the pack is fully valid.
    Raises ``ManifestValidationError`` on hard errors.
    """
    warnings: List[str] = []
    manifest_file = pack_path / MANIFEST_FILENAME

    if not manifest_file.is_file():
        raise ManifestValidationError(
            f"Missing {MANIFEST_FILENAME} in {pack_path}"
        )

    manifest = AgentManifest.from_yaml(manifest_file)

    bootstrap_file = pack_path / BOOTSTRAP_FILENAME
    if not bootstrap_file.is_file():
        warnings.append(f"Missing {BOOTSTRAP_FILENAME} (pack cannot be bootstrapped)")

    if not manifest.commands_dir:
        warnings.append("command_registration.commands_dir not set in manifest")

    if not manifest.description:
        warnings.append("agent.description is empty")

    if not manifest.tags:
        warnings.append("No tags specified (reduces discoverability)")

    return warnings


def export_pack(agent_id: str, dest: Path, project_path: Optional[Path] = None) -> Path:
    """Export the active pack for *agent_id* to *dest*.

    Returns the path to the exported pack directory.
    """
    resolved = resolve_agent_pack(agent_id, project_path=project_path)
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(resolved.path, dest, dirs_exist_ok=True)
    return dest
