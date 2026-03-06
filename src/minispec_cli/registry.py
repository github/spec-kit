"""MiniSpec Registry - Package management for slash commands, skills, and hooks."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml


# --- Data Models ---


@dataclass
class RegistryConfig:
    """A configured registry source (Git repo)."""

    name: str
    url: str
    added_at: str = ""

    def __post_init__(self):
        if not self.added_at:
            self.added_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")


@dataclass
class FileMapping:
    """A source-to-target file mapping within a package."""

    source: str
    target: str
    merge: bool = False


@dataclass
class ReviewInfo:
    """Audit trail for package review status."""

    status: str = "pending"  # approved | pending | rejected
    reviewed_by: str = ""
    reviewed_at: str = ""


@dataclass
class PackageSpec:
    """A package definition from package.yaml in a registry."""

    name: str
    version: str
    type: str  # command | skill | hook
    description: str = ""
    author: str = ""
    license: str = ""
    agents: list[str] = field(default_factory=list)
    minispec: str = ""  # version requirement, e.g. ">=0.0.3"
    files: list[FileMapping] = field(default_factory=list)
    review: ReviewInfo = field(default_factory=ReviewInfo)
    # Set at discovery time, not from package.yaml
    registry_name: str = ""


@dataclass
class InstalledPackage:
    """A package that has been installed in the project."""

    name: str
    version: str
    type: str
    registry: str
    installed_at: str = ""
    files: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.installed_at:
            self.installed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")


@dataclass
class RegistriesState:
    """The full state stored in .minispec/registries.yaml."""

    registries: list[RegistryConfig] = field(default_factory=list)
    installed: list[InstalledPackage] = field(default_factory=list)


# --- YAML Read/Write ---

REGISTRIES_PATH = Path(".minispec/registries.yaml")


def load_registries(project_dir: Path | None = None) -> RegistriesState:
    """Load registries state from .minispec/registries.yaml."""
    path = (project_dir or Path.cwd()) / REGISTRIES_PATH
    if not path.exists():
        return RegistriesState()

    with open(path) as f:
        data = yaml.safe_load(f) or {}

    registries = [
        RegistryConfig(
            name=r["name"],
            url=r["url"],
            added_at=r.get("added-at", ""),
        )
        for r in data.get("registries", [])
    ]

    installed = [
        InstalledPackage(
            name=p["name"],
            version=p["version"],
            type=p["type"],
            registry=p["registry"],
            installed_at=p.get("installed-at", ""),
            files=p.get("files", []),
        )
        for p in data.get("installed", [])
    ]

    return RegistriesState(registries=registries, installed=installed)


def save_registries(state: RegistriesState, project_dir: Path | None = None) -> None:
    """Save registries state to .minispec/registries.yaml."""
    path = (project_dir or Path.cwd()) / REGISTRIES_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    data: dict = {"registries": [], "installed": []}

    for r in state.registries:
        data["registries"].append({
            "name": r.name,
            "url": r.url,
            "added-at": r.added_at,
        })

    for p in state.installed:
        data["installed"].append({
            "name": p.name,
            "version": p.version,
            "type": p.type,
            "registry": p.registry,
            "installed-at": p.installed_at,
            "files": p.files,
        })

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# --- Registry Cache ---

CACHE_DIR = Path.home() / ".cache" / "minispec" / "registries"


def _run_git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a git command, raising RegistryError on failure."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "could not read Username" in stderr or "Permission denied" in stderr:
            raise RegistryError(f"Authentication failed for git repo. Check credentials or SSH keys.")
        if "Could not resolve host" in stderr or "unable to access" in stderr:
            raise RegistryError(f"Network error: cannot reach git repo. Check URL and connectivity.")
        if "not found" in stderr or "does not exist" in stderr:
            raise RegistryError(f"Repository not found. Check the URL.")
        raise RegistryError(f"Git error: {stderr}")
    return result


class RegistryError(Exception):
    """Raised when a registry operation fails."""


def cache_path(registry_name: str) -> Path:
    """Return the local cache path for a registry."""
    return CACHE_DIR / registry_name


def ensure_cached(registry: RegistryConfig, refresh: bool = False) -> Path:
    """Ensure a registry repo is cloned to the local cache. Returns cache path.

    If refresh=True, fetches latest from remote even if cache exists.
    """
    dest = cache_path(registry.name)

    if dest.exists() and (dest / ".git").is_dir():
        if refresh:
            _run_git("fetch", "--depth", "1", "origin", cwd=dest)
            _run_git("reset", "--hard", "origin/HEAD", cwd=dest)
        return dest

    # Fresh clone
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        # Stale/broken cache dir — remove and re-clone
        import shutil
        shutil.rmtree(dest)
    _run_git("clone", "--depth", "1", registry.url, str(dest))
    return dest


def remove_cache(registry_name: str) -> None:
    """Remove a registry's local cache."""
    dest = cache_path(registry_name)
    if dest.exists():
        import shutil
        shutil.rmtree(dest)


# --- Package Discovery ---


def _parse_package_yaml(path: Path, registry_name: str) -> PackageSpec | None:
    """Parse a package.yaml into a PackageSpec. Returns None if malformed."""
    try:
        with open(path) as f:
            data = yaml.safe_load(f) or {}

        # Required fields
        if not all(k in data for k in ("name", "version", "type")):
            return None

        files = [
            FileMapping(
                source=fm["source"],
                target=fm["target"],
                merge=fm.get("merge", False),
            )
            for fm in data.get("files", [])
            if "source" in fm and "target" in fm
        ]

        review_data = data.get("review", {})
        review = ReviewInfo(
            status=review_data.get("status", "pending"),
            reviewed_by=review_data.get("reviewed-by", ""),
            reviewed_at=review_data.get("reviewed-at", ""),
        )

        return PackageSpec(
            name=data["name"],
            version=str(data["version"]),
            type=data["type"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            license=data.get("license", ""),
            agents=data.get("agents", []),
            minispec=data.get("minispec", ""),
            files=files,
            review=review,
            registry_name=registry_name,
        )
    except (yaml.YAMLError, KeyError, TypeError):
        return None


def discover_packages(
    registry: RegistryConfig,
    refresh: bool = False,
    warnings: list[str] | None = None,
) -> list[PackageSpec]:
    """Discover all packages in a registry. Returns list of parsed PackageSpecs.

    Skips malformed packages. If warnings list is provided, appends skip messages.
    """
    repo_path = ensure_cached(registry, refresh=refresh)
    packages_dir = repo_path / "packages"
    if not packages_dir.is_dir():
        return []

    results = []
    for pkg_dir in sorted(packages_dir.iterdir()):
        if not pkg_dir.is_dir():
            continue
        pkg_yaml = pkg_dir / "package.yaml"
        if not pkg_yaml.exists():
            continue

        spec = _parse_package_yaml(pkg_yaml, registry.name)
        if spec is None:
            if warnings is not None:
                warnings.append(f"Skipping malformed package at {pkg_dir.name} in {registry.name}")
            continue
        results.append(spec)

    return results


def resolve_package(
    name: str,
    state: RegistriesState,
    registry_filter: str | None = None,
    refresh: bool = False,
) -> tuple[PackageSpec, list[str]]:
    """Find a package by name across registries. Returns (package, warnings).

    Raises RegistryError if not found, or found in multiple registries without filter.
    """
    warnings: list[str] = []
    matches: list[PackageSpec] = []

    targets = state.registries
    if registry_filter:
        targets = [r for r in targets if r.name == registry_filter]
        if not targets:
            raise RegistryError(f"Registry '{registry_filter}' not found.")

    for reg in targets:
        packages = discover_packages(reg, refresh=refresh, warnings=warnings)
        for pkg in packages:
            if pkg.name == name:
                matches.append(pkg)

    if not matches:
        raise RegistryError(f"Package '{name}' not found in any registry.")

    if len(matches) > 1:
        registries = ", ".join(m.registry_name for m in matches)
        raise RegistryError(
            f"Package '{name}' found in multiple registries: {registries}. "
            f"Use --registry to specify which one."
        )

    return matches[0], warnings


def install_package_files(
    spec: PackageSpec,
    registry: RegistryConfig,
    project_dir: Path | None = None,
) -> list[str]:
    """Copy/merge package files into the project. Returns list of installed target paths."""
    import shutil

    proj = project_dir or Path.cwd()
    repo = ensure_cached(registry)
    pkg_dir = repo / "packages" / spec.name
    installed_files: list[str] = []

    for fm in spec.files:
        source = pkg_dir / fm.source
        target = proj / fm.target

        if not source.exists():
            raise RegistryError(f"Package file not found: {fm.source}")

        if fm.merge:
            merge_file(source, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        installed_files.append(fm.target)

    return installed_files


# --- File Merge Logic ---


def _deep_merge(base: dict, update: dict) -> dict:
    """Recursively merge update dict into base dict.

    - New keys are added
    - Existing keys are preserved unless overwritten
    - Nested dicts are merged recursively
    - Lists and scalars are replaced
    """
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def merge_file(source: Path, target: Path) -> None:
    """Deep-merge a source file into a target file. Creates target if missing.

    Supports JSON and YAML files based on extension.
    """
    target.parent.mkdir(parents=True, exist_ok=True)

    if not target.exists():
        # No existing file — just copy
        import shutil
        shutil.copy2(source, target)
        return

    suffix = target.suffix.lower()

    if suffix == ".json":
        with open(source, encoding="utf-8") as f:
            source_data = json.load(f)
        try:
            with open(target, encoding="utf-8") as f:
                target_data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            target_data = {}
        merged = _deep_merge(target_data, source_data)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)

    elif suffix in (".yaml", ".yml"):
        with open(source, encoding="utf-8") as f:
            source_data = yaml.safe_load(f) or {}
        try:
            with open(target, encoding="utf-8") as f:
                target_data = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            target_data = {}
        merged = _deep_merge(target_data, source_data)
        with open(target, "w", encoding="utf-8") as f:
            yaml.dump(merged, f, default_flow_style=False, sort_keys=False)

    else:
        # Non-structured files: overwrite
        import shutil
        shutil.copy2(source, target)
