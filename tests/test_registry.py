"""Tests for minispec_cli.registry module."""

import json
from pathlib import Path

import pytest
import yaml

from minispec_cli.registry import (
    FileMapping,
    InstalledPackage,
    PackageSpec,
    RegistriesState,
    RegistryConfig,
    RegistryError,
    ReviewInfo,
    _deep_merge,
    _parse_package_yaml,
    load_registries,
    merge_file,
    resolve_package,
    save_registries,
)


# --- Data Models ---


class TestRegistryConfig:
    def test_auto_sets_added_at(self):
        rc = RegistryConfig(name="test", url="https://example.com/repo.git")
        assert rc.added_at  # non-empty string
        assert len(rc.added_at) == 10  # YYYY-MM-DD

    def test_preserves_explicit_added_at(self):
        rc = RegistryConfig(name="test", url="https://example.com/repo.git", added_at="2025-01-01")
        assert rc.added_at == "2025-01-01"


class TestInstalledPackage:
    def test_auto_sets_installed_at(self):
        pkg = InstalledPackage(name="foo", version="1.0", type="hook", registry="test")
        assert pkg.installed_at
        assert len(pkg.installed_at) == 10

    def test_preserves_explicit_installed_at(self):
        pkg = InstalledPackage(name="foo", version="1.0", type="hook", registry="test", installed_at="2025-06-01")
        assert pkg.installed_at == "2025-06-01"


# --- YAML Read/Write ---


class TestYAMLRoundTrip:
    def test_load_missing_file_returns_empty(self, tmp_path):
        state = load_registries(tmp_path)
        assert state.registries == []
        assert state.installed == []

    def test_round_trip(self, tmp_path):
        original = RegistriesState(
            registries=[
                RegistryConfig(name="acme", url="https://github.com/acme/registry.git", added_at="2025-01-01"),
            ],
            installed=[
                InstalledPackage(
                    name="protect-main",
                    version="1.0.0",
                    type="hook",
                    registry="acme",
                    installed_at="2025-01-15",
                    files=[".minispec/hooks/scripts/protect-main.sh"],
                ),
            ],
        )

        save_registries(original, tmp_path)

        # File should exist
        path = tmp_path / ".minispec" / "registries.yaml"
        assert path.exists()

        # Round-trip
        loaded = load_registries(tmp_path)
        assert len(loaded.registries) == 1
        assert loaded.registries[0].name == "acme"
        assert loaded.registries[0].url == "https://github.com/acme/registry.git"
        assert loaded.registries[0].added_at == "2025-01-01"

        assert len(loaded.installed) == 1
        assert loaded.installed[0].name == "protect-main"
        assert loaded.installed[0].version == "1.0.0"
        assert loaded.installed[0].type == "hook"
        assert loaded.installed[0].registry == "acme"
        assert loaded.installed[0].files == [".minispec/hooks/scripts/protect-main.sh"]

    def test_load_empty_yaml(self, tmp_path):
        path = tmp_path / ".minispec" / "registries.yaml"
        path.parent.mkdir(parents=True)
        path.write_text("")
        state = load_registries(tmp_path)
        assert state.registries == []
        assert state.installed == []

    def test_save_creates_parent_dirs(self, tmp_path):
        state = RegistriesState(
            registries=[RegistryConfig(name="r", url="https://example.com/r.git")],
        )
        save_registries(state, tmp_path)
        assert (tmp_path / ".minispec" / "registries.yaml").exists()


# --- Package YAML Parsing ---


class TestParsePackageYaml:
    def _write_package_yaml(self, path: Path, data: dict) -> Path:
        pkg_yaml = path / "package.yaml"
        pkg_yaml.parent.mkdir(parents=True, exist_ok=True)
        with open(pkg_yaml, "w") as f:
            yaml.dump(data, f)
        return pkg_yaml

    def test_valid_minimal(self, tmp_path):
        pkg_yaml = self._write_package_yaml(tmp_path, {
            "name": "my-hook",
            "version": "1.0.0",
            "type": "hook",
        })
        spec = _parse_package_yaml(pkg_yaml, "test-reg")
        assert spec is not None
        assert spec.name == "my-hook"
        assert spec.version == "1.0.0"
        assert spec.type == "hook"
        assert spec.registry_name == "test-reg"
        assert spec.files == []
        assert spec.agents == []
        assert spec.review.status == "pending"

    def test_valid_full(self, tmp_path):
        pkg_yaml = self._write_package_yaml(tmp_path, {
            "name": "protect-main",
            "version": "2.0.0",
            "type": "hook",
            "description": "Blocks commits to main",
            "author": "security-team",
            "license": "MIT",
            "agents": ["claude", "cursor"],
            "minispec": ">=0.0.3",
            "files": [
                {"source": "hook.sh", "target": ".minispec/hooks/scripts/protect-main.sh"},
                {"source": "settings.json", "target": ".claude/settings.json", "merge": True},
            ],
            "review": {
                "status": "approved",
                "reviewed-by": "security-team",
                "reviewed-at": "2025-02-01",
            },
        })
        spec = _parse_package_yaml(pkg_yaml, "acme")
        assert spec is not None
        assert spec.description == "Blocks commits to main"
        assert spec.agents == ["claude", "cursor"]
        assert len(spec.files) == 2
        assert spec.files[0].source == "hook.sh"
        assert spec.files[0].merge is False
        assert spec.files[1].merge is True
        assert spec.review.status == "approved"
        assert spec.review.reviewed_by == "security-team"

    def test_missing_required_fields(self, tmp_path):
        pkg_yaml = self._write_package_yaml(tmp_path, {
            "name": "incomplete",
            # missing version and type
        })
        assert _parse_package_yaml(pkg_yaml, "reg") is None

    def test_malformed_yaml(self, tmp_path):
        pkg_yaml = tmp_path / "package.yaml"
        pkg_yaml.write_text("{{invalid yaml")
        assert _parse_package_yaml(pkg_yaml, "reg") is None

    def test_version_coerced_to_string(self, tmp_path):
        pkg_yaml = self._write_package_yaml(tmp_path, {
            "name": "numver",
            "version": 1.0,  # numeric, should be stringified
            "type": "command",
        })
        spec = _parse_package_yaml(pkg_yaml, "reg")
        assert spec is not None
        assert spec.version == "1.0"
        assert isinstance(spec.version, str)


# --- Deep Merge ---


class TestDeepMerge:
    def test_adds_new_keys(self):
        assert _deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_overwrites_scalars(self):
        assert _deep_merge({"a": 1}, {"a": 2}) == {"a": 2}

    def test_recursive_merge(self):
        base = {"nested": {"a": 1, "b": 2}}
        update = {"nested": {"b": 3, "c": 4}}
        result = _deep_merge(base, update)
        assert result == {"nested": {"a": 1, "b": 3, "c": 4}}

    def test_replaces_list(self):
        assert _deep_merge({"items": [1, 2]}, {"items": [3]}) == {"items": [3]}

    def test_empty_base(self):
        assert _deep_merge({}, {"a": 1}) == {"a": 1}

    def test_empty_update(self):
        assert _deep_merge({"a": 1}, {}) == {"a": 1}

    def test_deeply_nested(self):
        base = {"l1": {"l2": {"l3": {"a": 1}}}}
        update = {"l1": {"l2": {"l3": {"b": 2}}}}
        result = _deep_merge(base, update)
        assert result == {"l1": {"l2": {"l3": {"a": 1, "b": 2}}}}


# --- File Merge ---


class TestMergeFile:
    def test_json_merge_creates_if_missing(self, tmp_path):
        source = tmp_path / "source.json"
        target = tmp_path / "out" / "target.json"
        source.write_text(json.dumps({"key": "value"}))

        merge_file(source, target)

        assert target.exists()
        with open(target) as f:
            data = json.load(f)
        assert data == {"key": "value"}

    def test_json_merge_preserves_existing(self, tmp_path):
        source = tmp_path / "source.json"
        target = tmp_path / "target.json"
        target.write_text(json.dumps({"existing": True, "nested": {"a": 1}}))
        source.write_text(json.dumps({"new_key": "val", "nested": {"b": 2}}))

        merge_file(source, target)

        with open(target) as f:
            data = json.load(f)
        assert data["existing"] is True
        assert data["new_key"] == "val"
        assert data["nested"] == {"a": 1, "b": 2}

    def test_yaml_merge_creates_if_missing(self, tmp_path):
        source = tmp_path / "source.yaml"
        target = tmp_path / "out" / "target.yaml"
        with open(source, "w") as f:
            yaml.dump({"key": "value"}, f)

        merge_file(source, target)

        assert target.exists()
        with open(target) as f:
            data = yaml.safe_load(f)
        assert data == {"key": "value"}

    def test_yaml_merge_preserves_existing(self, tmp_path):
        source = tmp_path / "source.yml"
        target = tmp_path / "target.yml"
        with open(target, "w") as f:
            yaml.dump({"existing": True}, f)
        with open(source, "w") as f:
            yaml.dump({"new_key": "val"}, f)

        merge_file(source, target)

        with open(target) as f:
            data = yaml.safe_load(f)
        assert data["existing"] is True
        assert data["new_key"] == "val"

    def test_non_structured_file_overwrites(self, tmp_path):
        source = tmp_path / "hook.sh"
        target = tmp_path / "hook_dest.sh"
        source.write_text("#!/bin/bash\necho new")
        target.write_text("#!/bin/bash\necho old")

        merge_file(source, target)

        assert target.read_text() == "#!/bin/bash\necho new"

    def test_json_merge_handles_corrupt_target(self, tmp_path):
        source = tmp_path / "source.json"
        target = tmp_path / "target.json"
        source.write_text(json.dumps({"key": "value"}))
        target.write_text("not valid json {{{")

        merge_file(source, target)

        with open(target) as f:
            data = json.load(f)
        assert data == {"key": "value"}


# --- Package Resolution ---


class TestResolvePackage:
    def _make_registry_with_packages(self, tmp_path, reg_name, packages):
        """Create a fake cached registry with packages on disk."""
        from minispec_cli.registry import CACHE_DIR

        reg_path = CACHE_DIR / reg_name / "packages"
        reg_path.mkdir(parents=True, exist_ok=True)

        # Create a fake .git dir so ensure_cached thinks it's already cloned
        git_dir = CACHE_DIR / reg_name / ".git"
        git_dir.mkdir(parents=True, exist_ok=True)

        for pkg_data in packages:
            pkg_dir = reg_path / pkg_data["name"]
            pkg_dir.mkdir(parents=True, exist_ok=True)
            with open(pkg_dir / "package.yaml", "w") as f:
                yaml.dump(pkg_data, f)

    def test_finds_package(self, tmp_path):
        self._make_registry_with_packages(tmp_path, "test-reg", [
            {"name": "my-hook", "version": "1.0.0", "type": "hook"},
        ])
        state = RegistriesState(
            registries=[RegistryConfig(name="test-reg", url="https://fake.com/repo.git")],
        )

        spec, warnings = resolve_package("my-hook", state)
        assert spec.name == "my-hook"
        assert spec.version == "1.0.0"

    def test_not_found_raises(self, tmp_path):
        self._make_registry_with_packages(tmp_path, "test-reg2", [
            {"name": "other", "version": "1.0.0", "type": "hook"},
        ])
        state = RegistriesState(
            registries=[RegistryConfig(name="test-reg2", url="https://fake.com/repo.git")],
        )

        with pytest.raises(RegistryError, match="not found"):
            resolve_package("nonexistent", state)

    def test_ambiguous_raises(self, tmp_path):
        # Same package in two registries
        for reg_name in ("reg-a", "reg-b"):
            self._make_registry_with_packages(tmp_path, reg_name, [
                {"name": "shared-pkg", "version": "1.0.0", "type": "command"},
            ])
        state = RegistriesState(
            registries=[
                RegistryConfig(name="reg-a", url="https://fake.com/a.git"),
                RegistryConfig(name="reg-b", url="https://fake.com/b.git"),
            ],
        )

        with pytest.raises(RegistryError, match="multiple registries"):
            resolve_package("shared-pkg", state)

    def test_registry_filter_resolves_ambiguity(self, tmp_path):
        for reg_name in ("reg-a", "reg-b"):
            self._make_registry_with_packages(tmp_path, reg_name, [
                {"name": "shared-pkg", "version": "1.0.0", "type": "command"},
            ])
        state = RegistriesState(
            registries=[
                RegistryConfig(name="reg-a", url="https://fake.com/a.git"),
                RegistryConfig(name="reg-b", url="https://fake.com/b.git"),
            ],
        )

        spec, _ = resolve_package("shared-pkg", state, registry_filter="reg-a")
        assert spec.registry_name == "reg-a"

    def test_invalid_registry_filter_raises(self):
        state = RegistriesState(
            registries=[RegistryConfig(name="real", url="https://fake.com/r.git")],
        )

        with pytest.raises(RegistryError, match="not found"):
            resolve_package("anything", state, registry_filter="nonexistent")


# --- CLI Helper: Registry Name Derivation ---


class TestDeriveRegistryName:
    def test_https_url(self):
        from minispec_cli import _derive_registry_name

        assert _derive_registry_name("https://github.com/acme/minispec-registry.git") == "minispec-registry"

    def test_ssh_url(self):
        from minispec_cli import _derive_registry_name

        assert _derive_registry_name("git@github.com:acme/my-hooks.git") == "my-hooks"

    def test_no_git_suffix(self):
        from minispec_cli import _derive_registry_name

        assert _derive_registry_name("https://github.com/acme/registry") == "registry"

    def test_trailing_slash(self):
        from minispec_cli import _derive_registry_name

        assert _derive_registry_name("https://github.com/acme/repo.git/") == "repo"
