"""Ephemeral installed-component state, never serialized into bundle records."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .manifest import ComponentRef


@dataclass
class ArtifactSnapshot:
    path: Path
    backup: Path | None
    trusted_root: Path


@dataclass
class ComponentSnapshot:
    component: ComponentRef
    metadata: dict[str, Any]
    directory: Path | None = None
    hooks: dict[str, list[tuple[int, dict[str, Any]]]] = field(default_factory=dict)
    backup: TemporaryDirectory | None = field(default=None, repr=False)
    artifacts: list[ArtifactSnapshot] = field(default_factory=list)
    absent_artifact_parents: set[tuple[Path, Path]] = field(default_factory=set)

    def close(self) -> None:
        if self.backup is not None:
            self.backup.cleanup()
