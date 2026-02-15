"""MiniSpec Registry - Package management for slash commands, skills, and hooks."""

from __future__ import annotations

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
