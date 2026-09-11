"""Ephemeral installed-component state, never serialized into bundle records."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .manifest import ComponentRef

logger = logging.getLogger(__name__)


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
            try:
                self.backup.cleanup()
            except OSError as exc:
                logger.warning(
                    "Could not clean up rollback snapshot at %s; remove it manually: %s",
                    self.backup.name, exc,
                )
