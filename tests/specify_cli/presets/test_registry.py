"""Tests for preset registry persistence and priority in specify_cli.presets._registry."""

import pytest

from specify_cli.presets import PresetRegistry


class TestPresetRegistry:
    """Test PresetRegistry operations."""

    def test_empty_registry(self, temp_dir):
        """Test empty registry initialization."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)
        assert registry.list() == {}
        assert not registry.is_installed("test-pack")

    def test_load_starts_fresh_for_non_utf8_registry(self, temp_dir):
        """A registry file with undecodable bytes must start fresh, not raise.

        ``_load()`` already treats malformed JSON as "corrupted registry,
        start fresh", but a registry whose *bytes* cannot be decoded as UTF-8
        raised a raw ``UnicodeDecodeError`` from the same boundary — the same
        corruption class reaching a different exception type.
        """
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        (packs_dir / PresetRegistry.REGISTRY_FILE).write_bytes(
            b"\xff\xfe not utf-8 \xc3\x28"
        )

        registry = PresetRegistry(packs_dir)

        assert registry.data == {
            "schema_version": PresetRegistry.SCHEMA_VERSION,
            "presets": {},
        }

    def test_add_and_get(self, temp_dir):
        """Test adding and retrieving a pack."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("test-pack", {"version": "1.0.0", "source": "local"})
        assert registry.is_installed("test-pack")

        metadata = registry.get("test-pack")
        assert metadata is not None
        assert metadata["version"] == "1.0.0"
        assert "installed_at" in metadata

    def test_remove(self, temp_dir):
        """Test removing a pack."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("test-pack", {"version": "1.0.0"})
        assert registry.is_installed("test-pack")

        registry.remove("test-pack")
        assert not registry.is_installed("test-pack")

    def test_remove_nonexistent(self, temp_dir):
        """Test removing a pack that doesn't exist."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)
        registry.remove("nonexistent")  # Should not raise

    def test_list(self, temp_dir):
        """Test listing all packs."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("pack-a", {"version": "1.0.0"})
        registry.add("pack-b", {"version": "2.0.0"})

        all_packs = registry.list()
        assert len(all_packs) == 2
        assert "pack-a" in all_packs
        assert "pack-b" in all_packs

    def test_persistence(self, temp_dir):
        """Test that registry data persists across instances."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()

        # Add with first instance
        registry1 = PresetRegistry(packs_dir)
        registry1.add("test-pack", {"version": "1.0.0"})

        # Load with second instance
        registry2 = PresetRegistry(packs_dir)
        assert registry2.is_installed("test-pack")

    def test_corrupted_registry(self, temp_dir):
        """Test recovery from corrupted registry file."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()

        registry_file = packs_dir / ".registry"
        registry_file.write_text("not valid json{{{")

        registry = PresetRegistry(packs_dir)
        assert registry.list() == {}

    def test_get_nonexistent(self, temp_dir):
        """Test getting a nonexistent pack."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)
        assert registry.get("nonexistent") is None

    def test_restore(self, temp_dir):
        """Test restore() preserves timestamps exactly."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        # Create original entry with a specific timestamp
        original_metadata = {
            "version": "1.0.0",
            "source": "local",
            "installed_at": "2025-01-15T10:30:00+00:00",
            "enabled": True,
        }
        registry.restore("test-pack", original_metadata)

        # Verify exact restoration
        restored = registry.get("test-pack")
        assert restored["installed_at"] == "2025-01-15T10:30:00+00:00"
        assert restored["version"] == "1.0.0"
        assert restored["enabled"] is True

    def test_restore_rejects_none_metadata(self, temp_dir):
        """Test restore() raises ValueError for None metadata."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        with pytest.raises(ValueError, match="metadata must be a dict"):
            registry.restore("test-pack", None)

    def test_restore_rejects_non_dict_metadata(self, temp_dir):
        """Test restore() raises ValueError for non-dict metadata."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        with pytest.raises(ValueError, match="metadata must be a dict"):
            registry.restore("test-pack", "not-a-dict")

        with pytest.raises(ValueError, match="metadata must be a dict"):
            registry.restore("test-pack", ["list", "not", "dict"])

    def test_restore_uses_deep_copy(self, temp_dir):
        """Test restore() deep copies metadata to prevent mutation."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        original_metadata = {
            "version": "1.0.0",
            "nested": {"key": "original"},
        }
        registry.restore("test-pack", original_metadata)

        # Mutate the original metadata after restore
        original_metadata["version"] = "MUTATED"
        original_metadata["nested"]["key"] = "MUTATED"

        # Registry should have the original values
        stored = registry.get("test-pack")
        assert stored["version"] == "1.0.0"
        assert stored["nested"]["key"] == "original"

    def test_get_returns_deep_copy(self, temp_dir):
        """Test that get() returns a deep copy to prevent mutation."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("test-pack", {"version": "1.0.0", "nested": {"key": "original"}})

        # Get and mutate the returned copy
        metadata = registry.get("test-pack")
        metadata["version"] = "MUTATED"
        metadata["nested"]["key"] = "MUTATED"

        # Original should be unchanged
        fresh = registry.get("test-pack")
        assert fresh["version"] == "1.0.0"
        assert fresh["nested"]["key"] == "original"

    def test_get_returns_none_for_corrupted_entry(self, temp_dir):
        """Test that get() returns None for corrupted (non-dict) entries."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        # Directly corrupt the registry with non-dict entries
        registry.data["presets"]["corrupted-string"] = "not a dict"
        registry.data["presets"]["corrupted-list"] = ["not", "a", "dict"]
        registry.data["presets"]["corrupted-int"] = 42
        registry._save()

        # All corrupted entries should return None
        assert registry.get("corrupted-string") is None
        assert registry.get("corrupted-list") is None
        assert registry.get("corrupted-int") is None
        # Non-existent should also return None
        assert registry.get("nonexistent") is None

    def test_list_returns_deep_copy(self, temp_dir):
        """Test that list() returns deep copies to prevent mutation."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("test-pack", {"version": "1.0.0", "nested": {"key": "original"}})

        # Get list and mutate
        all_packs = registry.list()
        all_packs["test-pack"]["version"] = "MUTATED"
        all_packs["test-pack"]["nested"]["key"] = "MUTATED"

        # Original should be unchanged
        fresh = registry.get("test-pack")
        assert fresh["version"] == "1.0.0"
        assert fresh["nested"]["key"] == "original"

    def test_list_returns_empty_dict_for_corrupted_registry(self, temp_dir):
        """Test that list() returns empty dict when presets is not a dict."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        # Corrupt the registry - presets is a list instead of dict
        registry.data["presets"] = ["not", "a", "dict"]
        registry._save()

        # list() should return empty dict, not crash
        result = registry.list()
        assert result == {}

    def test_list_by_priority_excludes_disabled(self, temp_dir):
        """Test that list_by_priority excludes disabled presets by default."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("pack-enabled", {"version": "1.0.0", "enabled": True, "priority": 5})
        registry.add("pack-disabled", {"version": "1.0.0", "enabled": False, "priority": 1})
        registry.add("pack-default", {"version": "1.0.0", "priority": 10})  # no enabled field = True

        # Default: exclude disabled
        by_priority = registry.list_by_priority()
        pack_ids = [p[0] for p in by_priority]
        assert "pack-enabled" in pack_ids
        assert "pack-default" in pack_ids
        assert "pack-disabled" not in pack_ids

    def test_list_by_priority_includes_disabled_when_requested(self, temp_dir):
        """Test that list_by_priority includes disabled presets when requested."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("pack-enabled", {"version": "1.0.0", "enabled": True, "priority": 5})
        registry.add("pack-disabled", {"version": "1.0.0", "enabled": False, "priority": 1})

        # Include disabled
        by_priority = registry.list_by_priority(include_disabled=True)
        pack_ids = [p[0] for p in by_priority]
        assert "pack-enabled" in pack_ids
        assert "pack-disabled" in pack_ids
        # Disabled pack has lower priority number, so it comes first when included
        assert pack_ids[0] == "pack-disabled"


class TestRegistryPriority:
    """Test registry priority sorting."""

    def test_list_by_priority(self, temp_dir):
        """Test that list_by_priority sorts by priority number."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("pack-high", {"version": "1.0.0", "priority": 1})
        registry.add("pack-low", {"version": "1.0.0", "priority": 20})
        registry.add("pack-mid", {"version": "1.0.0", "priority": 10})

        sorted_packs = registry.list_by_priority()
        assert len(sorted_packs) == 3
        assert sorted_packs[0][0] == "pack-high"
        assert sorted_packs[1][0] == "pack-mid"
        assert sorted_packs[2][0] == "pack-low"

    def test_list_by_priority_default(self, temp_dir):
        """Test that packs without priority default to 10."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("pack-a", {"version": "1.0.0"})  # no priority, defaults to 10
        registry.add("pack-b", {"version": "1.0.0", "priority": 5})

        sorted_packs = registry.list_by_priority()
        assert sorted_packs[0][0] == "pack-b"
        assert sorted_packs[1][0] == "pack-a"

    def test_list_by_priority_invalid_priority_defaults(self, temp_dir):
        """Malformed priority values fall back to the default priority."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("pack-high", {"version": "1.0.0", "priority": 1})
        registry.data["presets"]["pack-invalid"] = {
            "version": "1.0.0",
            "priority": "high",
        }
        registry._save()

        sorted_packs = registry.list_by_priority()

        assert [item[0] for item in sorted_packs] == ["pack-high", "pack-invalid"]
        assert sorted_packs[1][1]["priority"] == 10


class TestPresetPriorityBackwardsCompatibility:
    """Test backwards compatibility for presets installed before priority feature."""

    def test_legacy_preset_without_priority_field(self, temp_dir):
        """Presets installed before priority feature should default to 10."""
        presets_dir = temp_dir / ".specify" / "presets"
        presets_dir.mkdir(parents=True)

        # Simulate legacy registry entry without priority field
        registry = PresetRegistry(presets_dir)
        registry.data["presets"]["legacy-pack"] = {
            "version": "1.0.0",
            "source": "local",
            "enabled": True,
            "installed_at": "2025-01-01T00:00:00Z",
            # No "priority" field - simulates pre-feature preset
        }
        registry._save()

        # Reload registry
        registry2 = PresetRegistry(presets_dir)

        # list_by_priority should use default of 10
        result = registry2.list_by_priority()
        assert len(result) == 1
        assert result[0][0] == "legacy-pack"
        # Priority defaults to 10 and is normalized in returned metadata
        assert result[0][1]["priority"] == 10

    def test_mixed_legacy_and_new_presets_ordering(self, temp_dir):
        """Legacy presets (no priority) sort with default=10 among prioritized presets."""
        presets_dir = temp_dir / ".specify" / "presets"
        presets_dir.mkdir(parents=True)

        registry = PresetRegistry(presets_dir)

        # Add preset with explicit priority=5
        registry.add("pack-with-priority", {"version": "1.0.0", "priority": 5})

        # Add legacy preset without priority (manually)
        registry.data["presets"]["legacy-pack"] = {
            "version": "1.0.0",
            "source": "local",
            "enabled": True,
            # No priority field
        }

        # Add another preset with priority=15
        registry.add("low-priority-pack", {"version": "1.0.0", "priority": 15})
        registry._save()

        # Reload and check ordering
        registry2 = PresetRegistry(presets_dir)
        sorted_presets = registry2.list_by_priority()

        # Should be: pack-with-priority (5), legacy-pack (default 10), low-priority-pack (15)
        assert [p[0] for p in sorted_presets] == [
            "pack-with-priority",
            "legacy-pack",
            "low-priority-pack",
        ]
