"""Tests for preset installation and removal in specify_cli.presets._manager."""

import json
import tarfile
import zipfile
from pathlib import Path

import pytest
import yaml

from specify_cli.presets import (
    PresetCompatibilityError,
    PresetError,
    PresetManager,
    PresetManifest,
    PresetResolver,
    PresetValidationError,
)
from tests.specify_cli.presets._helpers import (
    CORE_TEMPLATE_NAMES,
    PresetArtifactTestHelpers,
    install_constitution_sync_preset,
    install_self_test_preset,
)
from tests.specify_cli.presets._helpers import (
    make_convention_constitution_preset as _make_convention_constitution_preset,
)


class TestPresetManifest:
    """Manager handling of invalid installed manifests."""

    def test_one_bad_manifest_does_not_hide_healthy_presets(self, temp_dir):
        """End-to-end guard for the symptom: an unquoted ``version: 1.0`` in one
        installed preset must degrade to "Corrupted preset" and still let
        list_installed() report the healthy ones, instead of raising TypeError
        out of the whole call.
        """
        preset_root = temp_dir / ".specify" / "presets"
        for pack_id, version in (("good-pack", '"1.0.0"'), ("bad-pack", "1.0")):
            pack_path = preset_root / pack_id
            pack_path.mkdir(parents=True, exist_ok=True)
            (pack_path / "preset.yml").write_text(
                f"""schema_version: "1.0"
preset:
  id: {pack_id}
  name: {pack_id}
  version: {version}
  description: desc
requires:
  speckit_version: ">=0.1.0"
provides:
  templates:
    - type: template
      name: spec
      file: templates/spec.md
""",
                encoding="utf-8",
            )
        (preset_root / ".registry").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "presets": {
                        "good-pack": {"version": "1.0.0", "enabled": True},
                        "bad-pack": {"version": "1.0", "enabled": True},
                    },
                }
            ),
            encoding="utf-8",
        )

        listed = {row["id"]: row for row in PresetManager(temp_dir).list_installed()}

        assert set(listed) == {"good-pack", "bad-pack"}
        assert "Corrupted" not in listed["good-pack"]["description"]
        assert "Corrupted" in listed["bad-pack"]["description"]


def test_unreadable_constitution_provenance_fails_closed(
    project_dir, monkeypatch
):
    from specify_cli.presets import _constitution_provenance_matches_preset

    memory = project_dir / ".specify" / "memory" / "constitution.md"
    memory.parent.mkdir(parents=True, exist_ok=True)
    memory.write_text("# Constitution\n", encoding="utf-8")
    provenance = memory.parent / ".constitution-template.json"
    provenance.write_text("{}", encoding="utf-8")
    real_read_text = Path.read_text

    def unreadable(path, *args, **kwargs):
        if path == provenance:
            raise OSError("simulated read failure")
        return real_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", unreadable)

    assert not _constitution_provenance_matches_preset(
        project_dir, memory, "example", "1.0.0"
    )


class TestPresetManager:
    """Test PresetManager installation and removal."""

    def test_install_from_directory(self, project_dir, pack_dir):
        """Test installing a preset from a directory."""
        manager = PresetManager(project_dir)
        manifest = manager.install_from_directory(pack_dir, "0.1.5")

        assert manifest.id == "test-pack"
        assert manager.registry.is_installed("test-pack")

        # Verify files are copied
        installed_dir = project_dir / ".specify" / "presets" / "test-pack"
        assert installed_dir.exists()
        assert (installed_dir / "preset.yml").exists()
        assert (installed_dir / "templates" / "spec-template.md").exists()

    def test_install_already_installed(self, project_dir, pack_dir):
        """Test installing an already-installed pack raises error."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        with pytest.raises(PresetError, match="already installed"):
            manager.install_from_directory(pack_dir, "0.1.5")

    def test_install_incompatible(self, project_dir, temp_dir, valid_pack_data):
        """Test installing an incompatible pack raises error."""
        valid_pack_data["requires"]["speckit_version"] = ">=99.0.0"
        incompat_dir = temp_dir / "incompat-pack"
        incompat_dir.mkdir()
        manifest_path = incompat_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        (incompat_dir / "templates").mkdir()
        (incompat_dir / "templates" / "spec-template.md").write_text("test")

        manager = PresetManager(project_dir)
        with pytest.raises(PresetCompatibilityError):
            manager.install_from_directory(incompat_dir, "0.1.5")

    def test_install_from_zip(self, project_dir, pack_dir, temp_dir):
        """Test installing from a ZIP file."""
        zip_path = temp_dir / "test-pack.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file_path in pack_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(pack_dir)
                    zf.write(file_path, arcname)

        manager = PresetManager(project_dir)
        manifest = manager.install_from_zip(
            zip_path, "0.1.5", catalog_name="preset-catalog"
        )
        assert manifest.id == "test-pack"
        assert manager.registry.is_installed("test-pack")
        assert manager.registry.get("test-pack")["source"] == {
            "kind": "catalog",
            "catalog": "preset-catalog",
        }

    def test_install_from_zip_forwards_force(
        self, project_dir, pack_dir, temp_dir
    ):
        """The compatibility wrapper must retain forced reinstall behavior."""
        zip_path = temp_dir / "test-pack.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for file_path in pack_dir.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(pack_dir))

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")
        manifest = manager.install_from_zip(
            zip_path,
            "0.1.5",
            force=True,
        )

        assert manifest.id == "test-pack"
        assert manager.registry.is_installed("test-pack")

    def test_install_from_zip_nested(self, project_dir, pack_dir, temp_dir):
        """Test installing from ZIP with nested directory."""
        zip_path = temp_dir / "test-pack.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file_path in pack_dir.rglob('*'):
                if file_path.is_file():
                    arcname = Path("test-pack-v1.0.0") / file_path.relative_to(pack_dir)
                    zf.write(file_path, arcname)

        manager = PresetManager(project_dir)
        manifest = manager.install_from_zip(zip_path, "0.1.5")
        assert manifest.id == "test-pack"

    def test_install_from_zip_no_manifest(self, project_dir, temp_dir):
        """Test installing from ZIP without manifest raises error."""
        zip_path = temp_dir / "bad.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("readme.txt", "no manifest here")

        manager = PresetManager(project_dir)
        with pytest.raises(PresetValidationError, match="No preset.yml found"):
            manager.install_from_zip(zip_path, "0.1.5")

    def test_install_from_zip_rejects_symlink_entry(
        self, project_dir, pack_dir, temp_dir
    ):
        """Preset ZIPs delegate to the shared symlink-safe extractor."""
        import stat

        zip_path = temp_dir / "symlink-preset.zip"
        link = zipfile.ZipInfo("templates/escape")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(zip_path, "w") as zf:
            for file_path in pack_dir.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(pack_dir))
            zf.writestr(link, "../../outside")

        manager = PresetManager(project_dir)
        with pytest.raises(PresetValidationError, match="Unsafe symlink"):
            manager.install_from_zip(zip_path, "0.1.5")

        assert not manager.registry.is_installed("test-pack")

    @pytest.mark.parametrize("suffix", [".tar.gz", ".tgz"])
    @pytest.mark.parametrize("nested", [False, True])
    def test_install_from_tar_archive(
        self, project_dir, pack_dir, temp_dir, suffix, nested
    ):
        """Tar archives install with the same flat/nested behavior as ZIP."""
        archive_path = temp_dir / f"test-pack{suffix}"
        with tarfile.open(archive_path, "w:gz") as archive:
            for file_path in pack_dir.rglob("*"):
                if file_path.is_file():
                    relative = file_path.relative_to(pack_dir)
                    arcname = Path("test-pack-v1") / relative if nested else relative
                    archive.add(file_path, arcname=arcname)

        manager = PresetManager(project_dir)
        manifest = manager.install_from_archive(
            archive_path, "0.1.5", catalog_name="preset-catalog"
        )

        assert manifest.id == "test-pack"
        assert manager.registry.is_installed("test-pack")
        assert manager.registry.get("test-pack")["source"] == {
            "kind": "catalog",
            "catalog": "preset-catalog",
        }

    def test_install_from_tar_rejects_symlink_entry(
        self, project_dir, pack_dir, temp_dir
    ):
        archive_path = temp_dir / "symlink-preset.tar.gz"
        with tarfile.open(archive_path, "w:gz") as archive:
            for file_path in pack_dir.rglob("*"):
                if file_path.is_file():
                    archive.add(file_path, arcname=file_path.relative_to(pack_dir))
            link = tarfile.TarInfo("templates/escape")
            link.type = tarfile.SYMTYPE
            link.linkname = "../../outside"
            archive.addfile(link)

        manager = PresetManager(project_dir)
        with pytest.raises(PresetValidationError, match="Unsafe symlink"):
            manager.install_from_archive(archive_path, "0.1.5")

        assert not manager.registry.is_installed("test-pack")

    def test_remove(self, project_dir, pack_dir):
        """Test removing a preset."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")
        assert manager.registry.is_installed("test-pack")

        result = manager.remove("test-pack")
        assert result is True
        assert not manager.registry.is_installed("test-pack")

        installed_dir = project_dir / ".specify" / "presets" / "test-pack"
        assert not installed_dir.exists()

    def test_remove_nonexistent(self, project_dir):
        """Test removing a pack that doesn't exist."""
        manager = PresetManager(project_dir)
        result = manager.remove("nonexistent")
        assert result is False

    def test_remove_rejects_unsafe_registry_id(self, project_dir):
        """A tampered registry entry must not reach path construction.

        The registry file is user-editable JSON; an id like ``../outside``
        would otherwise let ``remove()`` build a deletion target outside
        ``.specify/presets``.
        """
        manager = PresetManager(project_dir)
        unsafe_id = "../outside-target"
        manager.registry.add(unsafe_id, {"version": "1.0.0"})
        assert manager.registry.is_installed(unsafe_id)

        outside_target = project_dir / ".specify" / "outside-target"
        outside_target.mkdir()
        (outside_target / "keep.txt").write_text("do not delete")

        result = manager.remove(unsafe_id)

        assert result is False
        assert outside_target.exists()
        assert (outside_target / "keep.txt").exists()
        # Refused before the registry entry was mutated.
        assert manager.registry.is_installed(unsafe_id)

    def test_remove_refuses_symlinked_preset_dir(self, project_dir):
        """A symlinked preset directory must fail explicitly, not be deleted."""
        manager = PresetManager(project_dir)
        manager.registry.add("test-pack", {"version": "1.0.0"})

        real_target = project_dir.parent / "real-target"
        real_target.mkdir()
        (real_target / "important.txt").write_text("do not delete")

        pack_dir = project_dir / ".specify" / "presets" / "test-pack"
        pack_dir.symlink_to(real_target, target_is_directory=True)

        result = manager.remove("test-pack")

        assert result is False
        assert real_target.exists()
        assert (real_target / "important.txt").exists()
        assert pack_dir.is_symlink()
        assert manager.registry.is_installed("test-pack")

    def test_list_installed(self, project_dir, pack_dir):
        """Test listing installed packs."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["id"] == "test-pack"
        assert installed[0]["name"] == "Test Preset"
        assert installed[0]["version"] == "1.0.0"
        assert installed[0]["template_count"] == 1

    def test_list_installed_empty(self, project_dir):
        """Test listing when no packs installed."""
        manager = PresetManager(project_dir)
        assert manager.list_installed() == []

    def test_get_pack(self, project_dir, pack_dir):
        """Test getting a specific installed pack."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        pack = manager.get_pack("test-pack")
        assert pack is not None
        assert pack.id == "test-pack"

    def test_get_pack_not_installed(self, project_dir):
        """Test getting a non-installed pack returns None."""
        manager = PresetManager(project_dir)
        assert manager.get_pack("nonexistent") is None

    def test_check_compatibility_valid(self, pack_dir, temp_dir):
        """Test compatibility check with valid version."""
        manager = PresetManager(temp_dir)
        manifest = PresetManifest(pack_dir / "preset.yml")
        assert manager.check_compatibility(manifest, "0.1.5") is True

    def test_check_compatibility_prerelease(self, pack_dir, temp_dir):
        """Test compatibility check allows prereleases and fails on boundary."""
        manager = PresetManager(temp_dir)
        manifest = PresetManifest(pack_dir / "preset.yml")
        # manifest requires >=0.1.0
        assert manager.check_compatibility(manifest, "0.8.8.dev0") is True
        with pytest.raises(PresetCompatibilityError, match="Preset requires spec-kit"):
            manager.check_compatibility(manifest, "0.1.0.dev0")

    def test_check_compatibility_invalid(self, pack_dir, temp_dir):
        """Test compatibility check with invalid specifier."""
        manager = PresetManager(temp_dir)
        manifest = PresetManifest(pack_dir / "preset.yml")
        manifest.data["requires"]["speckit_version"] = "not-a-specifier"
        with pytest.raises(PresetCompatibilityError, match="Invalid version specifier"):
            manager.check_compatibility(manifest, "0.1.5")

    @pytest.mark.parametrize(
        "bad",
        [1.0, 5, True, None, [">=0.1.0"], {"min": "0.1"}],
    )
    def test_check_compatibility_non_string_specifier(self, pack_dir, temp_dir, bad):
        """check_compatibility() must report a non-string as a compatibility error.

        Defense in depth for the validator check: this method is public and the
        specifier is read back out of mutable manifest data, and ``except
        InvalidSpecifier`` does not cover a non-string. Without the guard, scalars
        raise a bare TypeError and iterables construct fine only to break inside
        .contains() -- neither is a PresetCompatibilityError, so both bypass the
        CLI's "Compatibility Error" handler and exit 1 with a raw traceback.
        """
        manager = PresetManager(temp_dir)
        manifest = PresetManifest(pack_dir / "preset.yml")
        manifest.data["requires"]["speckit_version"] = bad
        with pytest.raises(PresetCompatibilityError, match="Invalid version specifier"):
            manager.check_compatibility(manifest, "0.1.5")

    def test_install_with_priority(self, project_dir, pack_dir):
        """Test installing a pack with custom priority."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5", priority=5)

        metadata = manager.registry.get("test-pack")
        assert metadata is not None
        assert metadata["priority"] == 5

    def test_install_default_priority(self, project_dir, pack_dir):
        """Test that default priority is 10."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        metadata = manager.registry.get("test-pack")
        assert metadata is not None
        assert metadata["priority"] == 10

    def test_list_installed_includes_priority(self, project_dir, pack_dir):
        """Test that list_installed includes priority."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5", priority=3)

        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["priority"] == 3


class TestPresetExtensionDependencies:
    """Test find_unmet_extension_dependencies (issue #4231)."""

    @staticmethod
    def _install_extension(
        project_dir, extension_id, version, enabled=True, with_files=True
    ):
        """Register an installed extension the way the extension installer does.

        ``with_files=False`` leaves the registry entry without its directory,
        reproducing the stale state left behind when the files are deleted out
        from under the registry.
        """
        extensions_dir = project_dir / ".specify" / "extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)
        if with_files:
            (extensions_dir / extension_id).mkdir(parents=True, exist_ok=True)
        registry_path = extensions_dir / ".registry"
        data = {"schema_version": "1.0", "extensions": {}}
        if registry_path.exists():
            data = json.loads(registry_path.read_text(encoding="utf-8"))
        data["extensions"][extension_id] = {"version": version, "enabled": enabled}
        registry_path.write_text(json.dumps(data), encoding="utf-8")

    @staticmethod
    def _manifest(temp_dir, valid_pack_data, declared):
        valid_pack_data["requires"]["extensions"] = declared
        manifest_path = temp_dir / "dep-preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        return PresetManifest(manifest_path)

    def test_no_declared_dependencies_is_satisfied(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """A preset declaring nothing never reports an unmet dependency."""
        manifest_path = temp_dir / "plain-preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)

        manager = PresetManager(project_dir)
        assert manager.find_unmet_extension_dependencies(
            PresetManifest(manifest_path)
        ) == []

    def test_missing_dependency_is_reported(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """An uninstalled required extension is reported as missing."""
        manifest = self._manifest(temp_dir, valid_pack_data, ["speckit-inventory"])

        unmet = PresetManager(project_dir).find_unmet_extension_dependencies(manifest)

        assert len(unmet) == 1
        assert unmet[0]["id"] == "speckit-inventory"
        assert unmet[0]["reason"] == "missing"
        assert unmet[0]["installed"] is None

    def test_installed_dependency_is_satisfied(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """An installed extension with no version constraint is satisfied."""
        self._install_extension(project_dir, "speckit-inventory", "0.1.0")
        manifest = self._manifest(temp_dir, valid_pack_data, ["speckit-inventory"])

        assert PresetManager(project_dir).find_unmet_extension_dependencies(
            manifest
        ) == []

    def test_satisfied_version_constraint(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """A satisfied version constraint reports nothing."""
        self._install_extension(project_dir, "speckit-inventory", "1.5.0")
        manifest = self._manifest(
            temp_dir, valid_pack_data,
            [{"id": "speckit-inventory", "version": ">=1.2.0"}],
        )

        assert PresetManager(project_dir).find_unmet_extension_dependencies(
            manifest
        ) == []

    def test_unsatisfied_version_constraint_reports_both_versions(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """A version mismatch reports the installed version alongside the constraint."""
        self._install_extension(project_dir, "speckit-inventory", "0.1.0")
        manifest = self._manifest(
            temp_dir, valid_pack_data,
            [{"id": "speckit-inventory", "version": ">=9.0.0"}],
        )

        unmet = PresetManager(project_dir).find_unmet_extension_dependencies(manifest)

        assert len(unmet) == 1
        assert unmet[0]["reason"] == "version"
        assert unmet[0]["installed"] == "0.1.0"
        assert unmet[0]["version"] == ">=9.0.0"


    def test_optional_dependency_is_never_reported(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """`required: false` opts out of the warning even when absent."""
        manifest = self._manifest(
            temp_dir, valid_pack_data,
            [{"id": "speckit-inventory", "required": False}],
        )

        assert PresetManager(project_dir).find_unmet_extension_dependencies(
            manifest
        ) == []

    @pytest.mark.parametrize("bad_version", [None, 5, "unknown", "", "latest"])
    def test_uncomparable_registry_version_is_not_a_mismatch(
        self, project_dir, temp_dir, valid_pack_data, bad_version
    ):
        """A version that cannot be evaluated must not be reported as a mismatch.

        ``version_satisfies()`` returns False for an unparseable version, which
        is indistinguishable from a genuine mismatch -- so a string like
        "unknown" would otherwise be reported as failing a constraint nobody
        can actually evaluate it against.
        """
        self._install_extension(project_dir, "speckit-inventory", "0.1.0")
        registry_path = project_dir / ".specify" / "extensions" / ".registry"
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        data["extensions"]["speckit-inventory"]["version"] = bad_version
        registry_path.write_text(json.dumps(data), encoding="utf-8")

        manifest = self._manifest(
            temp_dir, valid_pack_data,
            [{"id": "speckit-inventory", "version": ">=9.0.0"}],
        )

        assert PresetManager(project_dir).find_unmet_extension_dependencies(
            manifest
        ) == []

    def test_unregistered_extension_on_disk_is_satisfied(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """A directory with no registry entry still resolves, so it is not missing.

        ``_get_all_extensions_by_priority`` admits safe unregistered
        directories at implicit priority 10, so the preset works -- warning
        that the dependency is absent would be a false alarm.
        """
        (project_dir / ".specify" / "extensions" / "speckit-inventory").mkdir(
            parents=True
        )
        manifest = self._manifest(temp_dir, valid_pack_data, ["speckit-inventory"])

        assert PresetManager(project_dir).find_unmet_extension_dependencies(
            manifest
        ) == []

    def test_unregistered_extension_cannot_be_version_checked(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """No registry entry means no recorded version, so nothing to compare."""
        (project_dir / ".specify" / "extensions" / "speckit-inventory").mkdir(
            parents=True
        )
        manifest = self._manifest(
            temp_dir, valid_pack_data,
            [{"id": "speckit-inventory", "version": ">=9.0.0"}],
        )

        assert PresetManager(project_dir).find_unmet_extension_dependencies(
            manifest
        ) == []

    def test_corrupted_registry_entry_with_directory_is_not_satisfied(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """A corrupted entry keeps its id registered, so its directory is excluded.

        ``get()`` returns None for a non-dict entry just as it does for an
        absent one, but ``keys()`` retains the id specifically so resolution
        does not re-admit the directory as an unregistered extension. The
        fallback must not revive what resolution excludes.
        """
        extensions_dir = project_dir / ".specify" / "extensions"
        (extensions_dir / "speckit-inventory").mkdir(parents=True)
        (extensions_dir / ".registry").write_text(
            json.dumps(
                {"schema_version": "1.0", "extensions": {"speckit-inventory": "corrupt"}}
            ),
            encoding="utf-8",
        )
        manifest = self._manifest(temp_dir, valid_pack_data, ["speckit-inventory"])

        unmet = PresetManager(project_dir).find_unmet_extension_dependencies(manifest)

        # Reported as corrupt rather than missing: the id is still registered,
        # so a plain `extension add` would be refused as already installed.
        assert [dep["reason"] for dep in unmet] == ["corrupt"]




    def test_unregistered_extension_with_corrupt_registry_is_missing(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """A corrupt registry makes resolution fail closed, so it is not usable."""
        extensions_dir = project_dir / ".specify" / "extensions"
        (extensions_dir / "speckit-inventory").mkdir(parents=True)
        (extensions_dir / ".registry").write_text("{not valid json", encoding="utf-8")
        manifest = self._manifest(temp_dir, valid_pack_data, ["speckit-inventory"])

        unmet = PresetManager(project_dir).find_unmet_extension_dependencies(manifest)

        assert [dep["reason"] for dep in unmet] == ["missing"]

    def test_corrupted_entry_gets_a_forced_reinstall_remedy(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """A corrupted entry is not simply absent: `add <id>` would be refused.

        ``get()`` returns None for it, but ``is_installed()`` still counts the
        key, so a plain add reports "already installed". It needs --force.
        """
        extensions_dir = project_dir / ".specify" / "extensions"
        extensions_dir.mkdir(parents=True)
        (extensions_dir / ".registry").write_text(
            json.dumps(
                {"schema_version": "1.0", "extensions": {"speckit-inventory": "bad"}}
            ),
            encoding="utf-8",
        )
        manifest = self._manifest(temp_dir, valid_pack_data, ["speckit-inventory"])

        unmet = PresetManager(project_dir).find_unmet_extension_dependencies(manifest)

        assert [dep["reason"] for dep in unmet] == ["corrupt"]


    def test_unreadable_registry_does_not_raise(
        self, project_dir, temp_dir, valid_pack_data, monkeypatch
    ):
        """An OSError from the registry must not crash an already-completed install.

        ``_load()`` lets OSError through, and ``preset_add`` only handles
        preset-domain errors, so raising here would turn a finished install
        into a traceback over what is only a warning.
        """
        manifest = self._manifest(temp_dir, valid_pack_data, ["speckit-inventory"])

        import specify_cli.presets as presets_mod

        def _boom(*args, **kwargs):
            raise PermissionError("registry unreadable")

        monkeypatch.setattr(presets_mod, "ExtensionRegistry", _boom)

        assert PresetManager(project_dir).find_unmet_extension_dependencies(
            manifest
        ) == []



    def test_exact_duplicate_declarations_warn_once(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """Naming the same dependency twice must not print the warning twice."""
        manifest = self._manifest(
            temp_dir, valid_pack_data, ["speckit-inventory", "speckit-inventory"]
        )

        unmet = PresetManager(project_dir).find_unmet_extension_dependencies(manifest)

        assert [dep["id"] for dep in unmet] == ["speckit-inventory"]

    def test_same_id_with_different_constraints_is_checked_twice(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """Distinct constraints on one id both have to hold, so both are checked."""
        self._install_extension(project_dir, "speckit-inventory", "1.0.0")
        manifest = self._manifest(
            temp_dir, valid_pack_data,
            [
                {"id": "speckit-inventory", "version": ">=9.0.0"},
                {"id": "speckit-inventory", "version": "<0.5"},
            ],
        )

        unmet = PresetManager(project_dir).find_unmet_extension_dependencies(manifest)

        assert [dep["version"] for dep in unmet] == [">=9.0.0", "<0.5"]

    def test_stale_registry_entry_is_reported(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """A registry entry whose extension directory is gone counts as unmet.

        PresetResolver guards on ``ext_dir.is_dir()`` in both template lookup
        and layer collection, so a stale entry contributes nothing -- but the
        surviving registry entry would otherwise read as satisfied.
        """
        self._install_extension(
            project_dir, "speckit-inventory", "0.1.0", with_files=False
        )
        manifest = self._manifest(temp_dir, valid_pack_data, ["speckit-inventory"])

        unmet = PresetManager(project_dir).find_unmet_extension_dependencies(manifest)

        assert len(unmet) == 1
        assert unmet[0]["reason"] == "stale"
        assert unmet[0]["installed"] == "0.1.0"

    def test_stale_is_reported_ahead_of_disabled_and_version(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """Restoring the files is the prerequisite, so it is reported first."""
        self._install_extension(
            project_dir, "speckit-inventory", "0.1.0",
            enabled=False, with_files=False,
        )
        manifest = self._manifest(
            temp_dir, valid_pack_data,
            [{"id": "speckit-inventory", "version": ">=9.0.0"}],
        )

        unmet = PresetManager(project_dir).find_unmet_extension_dependencies(manifest)

        assert [dep["reason"] for dep in unmet] == ["stale"]


    def test_disabled_dependency_is_reported(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """A disabled extension contributes nothing, so it counts as unmet.

        Resolution skips disabled extensions, leaving the preset just as inert
        as if the extension were absent -- but the registry entry exists, so a
        presence-only check would call it satisfied and stay silent.
        """
        self._install_extension(project_dir, "speckit-inventory", "0.1.0", enabled=False)
        manifest = self._manifest(temp_dir, valid_pack_data, ["speckit-inventory"])

        unmet = PresetManager(project_dir).find_unmet_extension_dependencies(manifest)

        assert len(unmet) == 1
        assert unmet[0]["reason"] == "disabled"
        assert unmet[0]["installed"] == "0.1.0"

    def test_disabled_is_reported_ahead_of_version_mismatch(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """Enabling is the prerequisite, so it is reported before the version."""
        self._install_extension(project_dir, "speckit-inventory", "0.1.0", enabled=False)
        manifest = self._manifest(
            temp_dir, valid_pack_data,
            [{"id": "speckit-inventory", "version": ">=9.0.0"}],
        )

        unmet = PresetManager(project_dir).find_unmet_extension_dependencies(manifest)

        assert [dep["reason"] for dep in unmet] == ["disabled"]

    def test_multiple_dependencies_report_independently(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """Each declared dependency is evaluated on its own."""
        self._install_extension(project_dir, "present-ext", "1.0.0")
        self._install_extension(project_dir, "off-ext", "1.0.0", enabled=False)
        manifest = self._manifest(
            temp_dir, valid_pack_data,
            [
                "present-ext",
                "absent-ext",
                "off-ext",
                {"id": "opt-ext", "required": False},
            ],
        )

        unmet = PresetManager(project_dir).find_unmet_extension_dependencies(manifest)

        assert [(dep["id"], dep["reason"]) for dep in unmet] == [
            ("absent-ext", "missing"),
            ("off-ext", "disabled"),
        ]


class TestSelfTestPreset:
    """Installation, removal, and constitution materialization using self-test."""

    def test_install_self_test_preset(self, project_dir):
        """Test installing the self-test preset from its directory."""
        manager = PresetManager(project_dir)
        manifest = install_self_test_preset(manager)
        assert manifest.id == "self-test"
        assert manager.registry.is_installed("self-test")

    def test_self_test_removal_restores_core(self, project_dir):
        """Test that removing self-test falls back to core templates."""
        templates_dir = project_dir / ".specify" / "templates"
        for name in CORE_TEMPLATE_NAMES:
            (templates_dir / f"{name}.md").write_text(f"# Core {name}\n")

        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        install_self_test_preset(manager)
        manager.remove("self-test")

        resolver = PresetResolver(project_dir)
        for name in CORE_TEMPLATE_NAMES:
            result = resolver.resolve_with_source(name)
            assert result is not None
            assert result["source"] == "core"

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.read_text() == "# Core constitution-template\n"

    def test_self_test_removal_preserves_edited_constitution(self, project_dir):
        """Removing a preset does not overwrite an edited generated constitution."""
        templates_dir = project_dir / ".specify" / "templates"
        (templates_dir / "constitution-template.md").write_text("# Core Constitution\n")

        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        install_self_test_preset(manager)
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        edited = memory.read_text() + "\n## Authored amendment\n"
        memory.write_text(edited)

        manager.remove("self-test")

        assert memory.read_text() == edited

    def test_self_test_does_not_seed_constitution_without_sync(self, project_dir):
        """Installing a preset does not materialize its constitution by default."""
        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert not memory.exists()

    def test_self_test_preserves_generated_constitution_without_sync(self, project_dir):
        """Preset install and removal preserve generated content without the opt-in."""
        resolver = PresetResolver(project_dir)
        bundled_core = resolver._find_bundled_core(
            "constitution-template", "template", ".md"
        )
        assert bundled_core is not None
        core = bundled_core.read_bytes()
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        memory.write_bytes(core)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)
        manager.remove("self-test")

        assert memory.read_bytes() == core

    def test_self_test_seeds_constitution_with_sync(self, project_dir):
        """constitution-sync preserves the previous install-time seeding behavior."""
        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        install_self_test_preset(manager)

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert "preset:self-test" in memory.read_text()
        assert "[PROJECT_NAME]" not in memory.read_text()

    @pytest.mark.parametrize(
        "provenance_content",
        [
            '{"sha256": "does-not-match", "source": "old-preset"}\n',
            "{not valid json",
        ],
        ids=["hash-mismatch", "malformed"],
    )
    def test_self_test_preserves_core_content_with_existing_invalid_provenance(
        self, project_dir, provenance_content
    ):
        """A present invalid sidecar disables legacy core-template migration."""
        resolver = PresetResolver(project_dir)
        bundled_core = resolver._find_bundled_core(
            "constitution-template", "template", ".md"
        )
        assert bundled_core is not None
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        memory.write_bytes(bundled_core.read_bytes())
        (memory.parent / ".constitution-template.json").write_text(
            provenance_content
        )
        original = memory.read_bytes()

        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        install_self_test_preset(manager)

        assert memory.read_bytes() == original

    def test_self_test_preserves_mutable_project_core_copy(self, project_dir):
        """A project template copy does not establish generated provenance."""
        authored = "# Acme Organization Constitution\n\nOrganization policy.\n"
        project_template = (
            project_dir / ".specify" / "templates" / "constitution-template.md"
        )
        project_template.write_text(authored)
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        memory.write_text(authored)

        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        install_self_test_preset(manager)

        assert memory.read_text() == authored
        assert not (memory.parent / ".constitution-template.json").exists()

    def test_core_prefixed_preset_does_not_establish_generated_provenance(
        self, project_dir, temp_dir
    ):
        """A preset ID beginning with core is not an immutable core source."""
        authored = "# Acme Organization Constitution\n\nOrganization policy.\n"
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        memory.write_text(authored)

        preset_dir = temp_dir / "core-company"
        (preset_dir / "templates").mkdir(parents=True)
        (preset_dir / "templates" / "constitution-template.md").write_text(authored)
        (preset_dir / "preset.yml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "core-company",
                        "name": "Core Company",
                        "version": "1.0.0",
                        "description": "Company constitution preset",
                        "author": "Test Author",
                        "repository": "https://github.com/test/core-company",
                        "license": "MIT",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "constitution-template",
                                "file": "templates/constitution-template.md",
                                "description": "Company constitution",
                                "replaces": "constitution-template",
                            }
                        ]
                    },
                }
            )
        )

        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        manager.install_from_directory(preset_dir, "0.1.5")

        assert memory.read_text() == authored
        assert not (memory.parent / ".constitution-template.json").exists()

    def test_self_test_preserves_authored_constitution_with_placeholder(
        self, project_dir
    ):
        """A placeholder mention does not establish generated provenance."""
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        authored = "# Acme Constitution\n\nGuidance for [PROJECT_NAME].\n"
        memory.write_text(authored)

        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        install_self_test_preset(manager)

        assert memory.read_text() == authored

    def test_self_test_preserves_authored_constitution(self, project_dir):
        """An authored (placeholder-free) constitution is never overwritten."""
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        authored = "# Acme Constitution\n\n### I. Ship It\nAuthored by a human.\n"
        memory.write_text(authored)

        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        install_self_test_preset(manager)

        assert memory.read_text() == authored, "authored constitution was overwritten"

    def test_constitution_seed_composes_wrap_strategy(self, project_dir, temp_dir):
        """Seeding memory composes wrap constitution-template layers."""
        templates_dir = project_dir / ".specify" / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        (templates_dir / "constitution-template.md").write_text(
            "# Core Constitution\n\n## Core Principle\n"
        )

        preset_dir = temp_dir / "constitution-wrap"
        (preset_dir / "templates").mkdir(parents=True)
        (preset_dir / "templates" / "constitution-template.md").write_text(
            "# Wrapper Constitution\n\n{CORE_TEMPLATE}\n\n## Wrapper Footer\n"
        )
        (preset_dir / "preset.yml").write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "constitution-wrap",
                        "name": "Constitution Wrap",
                        "version": "1.0.0",
                        "description": "Wrap constitution template for testing",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "constitution-template",
                                "file": "templates/constitution-template.md",
                                "strategy": "wrap",
                                "description": "Wrapped constitution template",
                            }
                        ]
                    },
                }
            )
        )

        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        manager.install_from_directory(preset_dir, "0.1.5")

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        content = memory.read_text()
        assert "{CORE_TEMPLATE}" not in content
        assert "# Wrapper Constitution" in content
        assert "## Core Principle" in content

    def test_constitution_follows_priority_when_winning_preset_removed(
        self, project_dir, temp_dir
    ):
        """An unchanged generated constitution follows priority and fallback layers."""
        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        install_self_test_preset(manager)

        preset_dir = temp_dir / "higher-priority"
        (preset_dir / "templates").mkdir(parents=True)
        (preset_dir / "templates" / "constitution-template.md").write_text(
            "# Higher Priority Constitution\n"
        )
        (preset_dir / "preset.yml").write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "higher-priority",
                        "name": "Higher Priority",
                        "version": "1.0.0",
                        "description": "Higher-priority constitution",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "constitution-template",
                                "file": "templates/constitution-template.md",
                                "strategy": "replace",
                                "description": "Higher-priority constitution",
                            }
                        ]
                    },
                }
            )
        )

        manager.install_from_directory(preset_dir, "0.1.5", priority=1)

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.read_text() == "# Higher Priority Constitution\n"

        manager.remove("higher-priority")

        assert "preset:self-test" in memory.read_text()

    def test_convention_constitution_removal_restores_remaining_layer(
        self, project_dir, temp_dir
    ):
        """Removing a convention layer rematerializes the remaining resolver layer."""
        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        install_self_test_preset(manager)
        manager.install_from_directory(
            _make_convention_constitution_preset(temp_dir), "0.1.5", priority=1
        )

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.read_text() == "# Convention Constitution\n"

        manager.remove("convention-constitution")

        assert "preset:self-test" in memory.read_text()

    def test_convention_constitution_removal_preserves_edited_content(
        self, project_dir, temp_dir
    ):
        """Removing a convention layer does not overwrite edited generated content."""
        from specify_cli.command_init import ensure_constitution_from_template

        templates_dir = project_dir / ".specify" / "templates"
        (templates_dir / "constitution-template.md").write_text("# Core Constitution\n")
        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        manager.install_from_directory(
            _make_convention_constitution_preset(temp_dir), "0.1.5"
        )
        ensure_constitution_from_template(project_dir)
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        edited = memory.read_text() + "\n## Authored amendment\n"
        memory.write_text(edited)

        manager.remove("convention-constitution")

        assert memory.read_text() == edited

    def test_custom_constitution_removal_recovers_with_invalid_manifest(
        self, project_dir, temp_dir
    ):
        """Provenance triggers fallback when a custom-path manifest is invalid."""
        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        install_self_test_preset(manager)

        preset_dir = temp_dir / "custom-constitution"
        (preset_dir / "policy").mkdir(parents=True)
        (preset_dir / "policy" / "charter.md").write_text("# Custom Constitution\n")
        (preset_dir / "preset.yml").write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "custom-constitution",
                        "name": "Custom Constitution",
                        "version": "1.0.0",
                        "description": "Custom-path constitution for testing",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "constitution-template",
                                "file": "policy/charter.md",
                            }
                        ]
                    },
                }
            )
        )
        manager.install_from_directory(preset_dir, "0.1.5", priority=1)
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.read_text() == "# Custom Constitution\n"

        installed_manifest = (
            project_dir
            / ".specify"
            / "presets"
            / "custom-constitution"
            / "preset.yml"
        )
        installed_manifest.write_text("invalid: [")

        manager.remove("custom-constitution")

        assert "preset:self-test" in memory.read_text()

    def test_constitution_seed_rejects_symlinked_memory_directory(
        self, project_dir, temp_dir
    ):
        """Preset installation cannot seed through a symlinked memory directory."""
        outside = temp_dir / "outside"
        outside.mkdir()
        try:
            (project_dir / ".specify" / "memory").symlink_to(
                outside, target_is_directory=True
            )
        except OSError:
            pytest.skip("symlinks are unavailable")

        manager = PresetManager(project_dir)
        with pytest.warns(UserWarning, match="symlinked"):
            install_constitution_sync_preset(manager)

        assert manager.registry.is_installed("constitution-sync")
        assert not (outside / "constitution.md").exists()

    def test_constitution_seed_rejects_dangling_destination_symlink(
        self, project_dir, temp_dir
    ):
        """Preset installation cannot seed through a dangling destination symlink."""
        memory = project_dir / ".specify" / "memory"
        memory.mkdir(parents=True)
        outside = temp_dir / "outside-constitution.md"
        try:
            (memory / "constitution.md").symlink_to(outside)
        except OSError:
            pytest.skip("symlinks are unavailable")

        manager = PresetManager(project_dir)
        with pytest.warns(UserWarning, match="symlinked"):
            install_constitution_sync_preset(manager)

        assert manager.registry.is_installed("constitution-sync")
        assert not outside.exists()

    def test_constitution_materialization_error_is_nonfatal(
        self, project_dir, temp_dir
    ):
        """An invalid wrap warns without reporting an uninstalled preset."""
        preset_dir = temp_dir / "invalid-wrap"
        (preset_dir / "templates").mkdir(parents=True)
        (preset_dir / "templates" / "constitution-template.md").write_text(
            "# Missing core placeholder\n"
        )
        (preset_dir / "preset.yml").write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "invalid-wrap",
                        "name": "Invalid Wrap",
                        "version": "1.0.0",
                        "description": "Invalid wrapping constitution",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "constitution-template",
                                "file": "templates/constitution-template.md",
                                "strategy": "wrap",
                                "description": "Invalid wrap",
                            }
                        ]
                    },
                }
            )
        )

        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        with pytest.warns(UserWarning, match="Failed to seed constitution"):
            manifest = manager.install_from_directory(preset_dir, "0.1.5")

        assert manifest.id == "invalid-wrap"
        assert manager.registry.is_installed("invalid-wrap")


class TestPresetSkills(PresetArtifactTestHelpers):
    """Manager lifecycle behavior across skill and command mode changes."""

    def test_remove_after_partial_command_to_skills_toggle_keeps_skills_mode_agent_command_free(
        self, project_dir, temp_dir
    ):
        """Removal must not recreate a command file for a skills-mode agent.

        A partially failed command→skills toggle leaves the active agent's
        stale ``registered_commands`` entry behind. Removing that preset
        records the agent in ``extra_agents`` for post-removal
        reconciliation, and ``register_commands_for_non_skill_agents``
        admits every ``extra_agents`` member even when the active-only
        ``only_agent`` guard excludes the agent — so the surviving
        lower-priority preset's command file was recreated for an agent
        now running in skills mode (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)

        lower_dir = self._create_command_preset(
            temp_dir, "stale-toggle-lower-preset", "speckit.plan",
            "Lower preset", "Lower body",
        )
        higher_dir = self._create_command_preset(
            temp_dir, "stale-toggle-higher-preset", "speckit.plan",
            "Higher preset", "Higher body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(lower_dir, "0.1.5", priority=20)
        manager.install_from_directory(higher_dir, "0.1.5", priority=10)

        command_file = copilot_commands_dir / "speckit.plan.agent.md"
        assert "Higher body" in command_file.read_text(encoding="utf-8"), (
            "sanity: command mode should have written the winning preset"
        )

        # Break the higher preset's installed source so its skill
        # replacement is silently skipped during the toggle — a genuine
        # partial command→skills toggle that leaves the stale
        # registered_commands entry for copilot behind.
        (manager.presets_dir / "stale-toggle-higher-preset" / "commands" / "speckit.plan.md").unlink()
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.register_enabled_presets_for_agent("copilot")

        metadata = manager.registry.get("stale-toggle-higher-preset")
        assert "speckit.plan" in metadata["registered_commands"].get("copilot", []), (
            "sanity: the partial toggle must leave the stale command "
            "tracking behind"
        )

        manager.remove("stale-toggle-higher-preset")

        assert not command_file.exists(), (
            "removing the preset while copilot runs in skills mode must "
            "not recreate its command file from the surviving lower "
            "preset via the stale extra_agents entry (#2948)"
        )

    def test_remove_after_partial_skills_to_command_toggle_deletes_stale_skill(
        self, project_dir, temp_dir
    ):
        """Removal must delete, not restore, a command-mode agent's stale skill.

        The inverse partial toggle: a skills→command conversion that could
        not replace one command leaves that skill tracked in
        ``registered_skills``. Removing the preset while the agent is now
        in command mode sent it through ``_unregister_skills()``, which
        restored a core/extension ``SKILL.md``, and ``extra_skills_dirs``
        then let ``_reconcile_skills`` reapply the surviving lower preset —
        leaving the active command-mode agent with a skill artifact it
        must not have (#2948).
        """
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        copilot_commands_dir = project_dir / ".github" / "agents"
        copilot_commands_dir.mkdir(parents=True)

        lower_dir = self._create_command_preset(
            temp_dir, "inverse-toggle-lower-preset", "speckit.plan",
            "Lower preset", "Lower body",
        )
        higher_dir = self._create_command_preset(
            temp_dir, "inverse-toggle-higher-preset", "speckit.plan",
            "Higher preset", "Higher body",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(lower_dir, "0.1.5", priority=20)
        manager.install_from_directory(higher_dir, "0.1.5", priority=10)

        skill_dir = project_dir / ".github" / "skills" / "speckit-plan"
        assert (skill_dir / "SKILL.md").exists(), (
            "sanity: skills mode should have written the skill"
        )

        # Break the higher preset's installed source so its command
        # replacement never lands during the skills→command toggle,
        # leaving the skill tracked for copilot.
        (manager.presets_dir / "inverse-toggle-higher-preset" / "commands" / "speckit.plan.md").unlink()
        self._write_init_options(project_dir, ai="copilot", ai_skills=False)
        manager.register_enabled_presets_for_agent("copilot")

        metadata = manager.registry.get("inverse-toggle-higher-preset")
        registered_skills = metadata.get("registered_skills") or {}
        assert registered_skills.get("copilot"), (
            "sanity: the partial toggle must leave the stale skill "
            "tracking behind"
        )
        assert (skill_dir / "SKILL.md").exists(), (
            "sanity: the stale skill artifact must survive the partial toggle"
        )

        manager.remove("inverse-toggle-higher-preset")

        assert not skill_dir.exists(), (
            "removing the preset while copilot runs in command mode must "
            "delete the stale preset-owned skill instead of restoring core "
            "content or reapplying the surviving lower preset (#2948)"
        )

    def test_partial_skill_install_failure_rolls_back_persisted_writes(
        self, project_dir, temp_dir, monkeypatch
    ):
        """Install rollback must reload partial skill ownership before removal."""
        self._write_init_options(project_dir, ai="copilot", ai_skills=True)
        (project_dir / ".github" / "agents").mkdir(parents=True)
        preset_dir = self._create_multi_command_preset(
            temp_dir,
            "partial-install-failure-preset",
            ["speckit.specify", "speckit.plan"],
        )
        manager = PresetManager(project_dir)
        original_read_text = Path.read_text

        def fail_plan_source(path, *args, **kwargs):
            if (
                path.name == "speckit.plan.md"
                and path.parent.name == "commands"
                and "partial-install-failure-preset" in path.parts
            ):
                raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid")
            return original_read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", fail_plan_source)
        with pytest.raises(UnicodeDecodeError):
            manager.install_from_directory(preset_dir, "0.1.5")

        assert not manager.registry.is_installed(
            "partial-install-failure-preset"
        )
        skill_file = (
            project_dir
            / ".github"
            / "skills"
            / "speckit-specify"
            / "SKILL.md"
        )
        assert (
            not skill_file.exists()
            or "preset:partial-install-failure-preset"
            not in original_read_text(skill_file, encoding="utf-8")
        ), "rollback must not orphan a skill written before the later failure"


class TestPresetPriorityBackwardsCompatibility:
    """Test backwards compatibility for presets installed before priority feature."""

    def test_legacy_preset_in_list_installed(self, project_dir, pack_dir):
        """list_installed returns priority=10 for legacy presets without priority field."""
        manager = PresetManager(project_dir)

        # Install preset normally
        manager.install_from_directory(pack_dir, "0.1.5")

        # Manually remove priority to simulate legacy preset
        pack_data = manager.registry.data["presets"]["test-pack"]
        del pack_data["priority"]
        manager.registry._save()

        # list_installed should still return priority=10
        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["priority"] == 10


class TestRemoveReconciliation:
    """Test that removing a preset re-registers the next layer's command."""

    def test_remove_restores_extension_command_subdir_paths_for_non_skill_agent(
        self, project_dir, temp_dir
    ):
        """When a preset override of an extension command is removed, the
        reconciled non-skill-agent command file should have the extension's
        own subdir references rewritten to their installed location (#2101),
        not left as bare, unresolvable paths."""
        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control" / "commander.md").write_text("# Commander\n")
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\ndescription: Extension fakeext cmd\n---\n\n"
            "Read agents/control/commander.md for context.\n"
        )
        extension_manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "fakeext",
                "name": "Fake Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/cmd.md",
                        "description": "Fake extension command",
                    }
                ]
            },
        }
        with open(extension_dir / "extension.yml", "w") as f:
            yaml.dump(extension_manifest, f)

        manager = PresetManager(project_dir)

        preset_dir = temp_dir / "ext-cmd-override"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\n\npreset override content\n"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-cmd-override",
                "name": "Ext Cmd Override",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/speckit.fakeext.cmd.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(preset_manifest, f)

        manager.install_from_directory(preset_dir, "0.1.5")

        cmd_files = list(gemini_dir.glob("*fakeext*"))
        assert cmd_files, "Command file should exist in gemini dir"
        assert "preset override content" in cmd_files[0].read_text()

        manager.remove("ext-cmd-override")

        cmd_files = list(gemini_dir.glob("*fakeext*"))
        assert cmd_files, "Command file should still exist after removal"
        content = cmd_files[0].read_text()
        assert "preset override content" not in content
        assert ".specify/extensions/fakeext/agents/control/commander.md" in content
        assert "Read agents/control" not in content

    def test_remove_restores_lower_priority_command(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """After removing the top-priority preset, the next preset's command
        should be re-registered in agent directories."""
        manager = PresetManager(project_dir)

        # Create a gemini commands dir so reconciliation writes there
        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        # Install a low-priority preset with a command
        lo_data = {**valid_pack_data}
        lo_data["preset"] = {
            **valid_pack_data["preset"],
            "id": "lo-preset",
            "name": "Lo",
        }
        lo_data["provides"] = {
            "templates": [{
                "type": "command",
                "name": "speckit.specify",
                "file": "commands/speckit.specify.md",
            }]
        }
        lo_dir = temp_dir / "lo-preset"
        lo_dir.mkdir()
        with open(lo_dir / "preset.yml", "w") as f:
            yaml.dump(lo_data, f)
        (lo_dir / "commands").mkdir()
        (lo_dir / "commands" / "speckit.specify.md").write_text(
            "---\ndescription: lo\n---\nLo content\n"
        )
        manager.install_from_directory(lo_dir, "0.1.5", priority=10)

        # Install a high-priority preset overriding the same command
        hi_data = {**valid_pack_data}
        hi_data["preset"] = {
            **valid_pack_data["preset"],
            "id": "hi-preset",
            "name": "Hi",
        }
        hi_data["provides"] = {
            "templates": [{
                "type": "command",
                "name": "speckit.specify",
                "file": "commands/speckit.specify.md",
            }]
        }
        hi_dir = temp_dir / "hi-preset"
        hi_dir.mkdir()
        with open(hi_dir / "preset.yml", "w") as f:
            yaml.dump(hi_data, f)
        (hi_dir / "commands").mkdir()
        (hi_dir / "commands" / "speckit.specify.md").write_text(
            "---\ndescription: hi\n---\nHi content\n"
        )
        manager.install_from_directory(hi_dir, "0.1.5", priority=1)

        # Verify the hi-preset's content is active in agent dir
        cmd_files = list(gemini_dir.glob("*specify*"))
        assert cmd_files, "Command file should exist in gemini dir"
        assert "Hi content" in cmd_files[0].read_text()

        # Remove the high-priority preset
        manager.remove("hi-preset")

        # The low-priority preset's command should now be in the resolution stack
        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("speckit.specify", "command")
        assert len(layers) >= 1
        assert "lo-preset" in layers[0]["source"]

        # Verify on-disk agent command file switched to lo-preset content
        cmd_files = list(gemini_dir.glob("*specify*"))
        assert cmd_files, "Command file should still exist after removal"
        assert "Lo content" in cmd_files[0].read_text()
