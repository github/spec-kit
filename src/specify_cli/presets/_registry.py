"""Installed preset registry (private implementation)."""

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from ..extensions import normalize_priority


class PresetRegistry:
    """Manages the registry of installed presets."""

    REGISTRY_FILE = ".registry"
    SCHEMA_VERSION = "1.0"

    def __init__(self, packs_dir: Path):
        """Initialize registry.

        Args:
            packs_dir: Path to .specify/presets/ directory
        """
        self.packs_dir = packs_dir
        self.registry_path = packs_dir / self.REGISTRY_FILE
        self.data = self._load()

    def _load(self) -> dict:
        """Load registry from disk."""
        if not self.registry_path.exists():
            return {
                "schema_version": self.SCHEMA_VERSION,
                "presets": {}
            }

        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Validate loaded data is a dict (handles corrupted registry files)
            if not isinstance(data, dict):
                return {
                    "schema_version": self.SCHEMA_VERSION,
                    "presets": {}
                }
            # Normalize presets field (handles corrupted presets value)
            if not isinstance(data.get("presets"), dict):
                data["presets"] = {}
            return data
        except (json.JSONDecodeError, UnicodeDecodeError, FileNotFoundError):
            # Corrupted or missing registry, start fresh. A registry whose
            # bytes cannot be decoded as UTF-8 is the same corruption class
            # as malformed JSON — only the exception type differs. OSError is
            # deliberately not caught: the data may be intact on disk, and
            # starting fresh would let a later _save() wipe it.
            return {
                "schema_version": self.SCHEMA_VERSION,
                "presets": {}
            }

    def _save(self):
        """Save registry to disk."""
        self.packs_dir.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def add(self, pack_id: str, metadata: dict):
        """Add preset to registry.

        Args:
            pack_id: Preset ID
            metadata: Pack metadata (version, source, etc.)
        """
        self.data["presets"][pack_id] = {
            **copy.deepcopy(metadata),
            "installed_at": datetime.now(timezone.utc).isoformat()
        }
        self._save()

    def remove(self, pack_id: str):
        """Remove preset from registry.

        Args:
            pack_id: Preset ID
        """
        packs = self.data.get("presets")
        if not isinstance(packs, dict):
            return
        if pack_id in packs:
            del packs[pack_id]
            self._save()

    def update(self, pack_id: str, updates: dict):
        """Update preset metadata in registry.

        Merges the provided updates with the existing entry, preserving any
        fields not specified. The installed_at timestamp is always preserved
        from the original entry.

        Args:
            pack_id: Preset ID
            updates: Partial metadata to merge into existing metadata

        Raises:
            KeyError: If preset is not installed
        """
        packs = self.data.get("presets")
        if not isinstance(packs, dict) or pack_id not in packs:
            raise KeyError(f"Preset '{pack_id}' not found in registry")
        existing = packs[pack_id]
        # Handle corrupted registry entries (e.g., string/list instead of dict)
        if not isinstance(existing, dict):
            existing = {}
        # Merge: existing fields preserved, new fields override (deep copy to prevent caller mutation)
        merged = {**existing, **copy.deepcopy(updates)}
        # Always preserve original installed_at based on key existence, not truthiness,
        # to handle cases where the field exists but may be falsy (legacy/corruption)
        if "installed_at" in existing:
            merged["installed_at"] = existing["installed_at"]
        else:
            # If not present in existing, explicitly remove from merged if caller provided it
            merged.pop("installed_at", None)
        packs[pack_id] = merged
        self._save()

    def restore(self, pack_id: str, metadata: dict):
        """Restore preset metadata to registry without modifying timestamps.

        Use this method for rollback scenarios where you have a complete backup
        of the registry entry (including installed_at) and want to restore it
        exactly as it was.

        Args:
            pack_id: Preset ID
            metadata: Complete preset metadata including installed_at

        Raises:
            ValueError: If metadata is None or not a dict
        """
        if metadata is None or not isinstance(metadata, dict):
            raise ValueError(f"Cannot restore '{pack_id}': metadata must be a dict")
        # Ensure presets dict exists (handle corrupted registry)
        if not isinstance(self.data.get("presets"), dict):
            self.data["presets"] = {}
        self.data["presets"][pack_id] = copy.deepcopy(metadata)
        self._save()

    def get(self, pack_id: str) -> Optional[dict]:
        """Get preset metadata from registry.

        Returns a deep copy to prevent callers from accidentally mutating
        nested internal registry state without going through the write path.

        Args:
            pack_id: Preset ID

        Returns:
            Deep copy of preset metadata, or None if not found or corrupted
        """
        packs = self.data.get("presets")
        if not isinstance(packs, dict):
            return None
        entry = packs.get(pack_id)
        # Return None for missing or corrupted (non-dict) entries
        if entry is None or not isinstance(entry, dict):
            return None
        return copy.deepcopy(entry)

    def list(self) -> Dict[str, dict]:
        """Get all installed presets with valid metadata.

        Returns a deep copy of presets with dict metadata only.
        Corrupted entries (non-dict values) are filtered out.

        Returns:
            Dictionary of pack_id -> metadata (deep copies), empty dict if corrupted
        """
        packs = self.data.get("presets", {}) or {}
        if not isinstance(packs, dict):
            return {}
        # Filter to only valid dict entries to match type contract
        return {
            pack_id: copy.deepcopy(meta)
            for pack_id, meta in packs.items()
            if isinstance(meta, dict)
        }

    def keys(self) -> set:
        """Get all preset IDs including corrupted entries.

        Lightweight method that returns IDs without deep-copying metadata.
        Use this when you only need to check which presets are tracked.

        Returns:
            Set of preset IDs (includes corrupted entries)
        """
        packs = self.data.get("presets", {}) or {}
        if not isinstance(packs, dict):
            return set()
        return set(packs.keys())

    def list_by_priority(self, include_disabled: bool = False) -> List[tuple]:
        """Get all installed presets sorted by priority.

        Lower priority number = higher precedence (checked first).
        Presets with equal priority are sorted alphabetically by ID
        for deterministic ordering.

        Args:
            include_disabled: If True, include disabled presets. Default False.

        Returns:
            List of (pack_id, metadata_copy) tuples sorted by priority.
            Metadata is deep-copied to prevent accidental mutation.
        """
        packs = self.data.get("presets", {}) or {}
        if not isinstance(packs, dict):
            packs = {}
        sortable_packs = []
        for pack_id, meta in packs.items():
            if not isinstance(meta, dict):
                continue
            # Skip disabled presets unless explicitly requested
            if not include_disabled and not meta.get("enabled", True):
                continue
            metadata_copy = copy.deepcopy(meta)
            metadata_copy["priority"] = normalize_priority(metadata_copy.get("priority", 10))
            sortable_packs.append((pack_id, metadata_copy))
        return sorted(
            sortable_packs,
            key=lambda item: (item[1]["priority"], item[0]),
        )

    def is_installed(self, pack_id: str) -> bool:
        """Check if preset is installed.

        Args:
            pack_id: Preset ID

        Returns:
            True if pack is installed, False if not or registry corrupted
        """
        packs = self.data.get("presets")
        if not isinstance(packs, dict):
            return False
        return pack_id in packs
