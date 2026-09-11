"""Public API for artifact inventory and resolution."""

from .catalog import ArtifactCatalog
from .models import (
    AmbiguousArtifactError,
    Artifact,
    ArtifactError,
    ArtifactKind,
    ArtifactNotFoundError,
    ArtifactResolutionError,
    HookArtifact,
    HookLayerName,
    HookStackEntry,
    LayerName,
    NotASpecKitProjectError,
    StackLayer,
    Strategy,
)

__all__ = [
    "AmbiguousArtifactError",
    "Artifact",
    "ArtifactCatalog",
    "ArtifactError",
    "ArtifactKind",
    "ArtifactNotFoundError",
    "ArtifactResolutionError",
    "HookArtifact",
    "HookLayerName",
    "HookStackEntry",
    "LayerName",
    "NotASpecKitProjectError",
    "StackLayer",
    "Strategy",
]
