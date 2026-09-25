"""Tests for preset manifest validation in specify_cli.presets._manifest."""

import pytest
import yaml

from specify_cli.presets import (
    VALID_PRESET_TEMPLATE_TYPES,
    PresetManifest,
    PresetValidationError,
)


class TestPresetManifest:
    """Test PresetManifest validation and parsing."""

    def test_valid_manifest(self, pack_dir):
        """Test loading a valid manifest."""
        manifest = PresetManifest(pack_dir / "preset.yml")
        assert manifest.id == "test-pack"
        assert manifest.name == "Test Preset"
        assert manifest.version == "1.0.0"
        assert manifest.description == "A test preset"
        assert manifest.author == "Test Author"
        assert manifest.requires_speckit_version == ">=0.1.0"
        assert len(manifest.templates) == 1
        assert manifest.tags == ["testing", "example"]

    def test_missing_manifest(self, temp_dir):
        """Test that missing manifest raises error."""
        with pytest.raises(PresetValidationError, match="Manifest not found"):
            PresetManifest(temp_dir / "nonexistent.yml")

    def test_invalid_yaml(self, temp_dir):
        """Test that invalid YAML raises error."""
        bad_file = temp_dir / "bad.yml"
        bad_file.write_text(": invalid: yaml: {{{")
        with pytest.raises(PresetValidationError, match="Invalid YAML"):
            PresetManifest(bad_file)

    def test_utf8_non_ascii_description_loads(self, temp_dir, valid_pack_data):
        """Regression for #2325: non-ASCII (UTF-8) description loads on any platform.

        On Windows, Python's default text-mode encoding is the locale codepage
        (e.g. cp1252/GBK), which raises UnicodeDecodeError on UTF-8 bytes
        outside the ASCII range. The loader must open with encoding='utf-8'.
        """
        valid_pack_data["preset"]["description"] = "中文测试 — émojis 🚀"
        manifest_path = temp_dir / "preset.yml"
        manifest_path.write_bytes(
            yaml.safe_dump(valid_pack_data, allow_unicode=True).encode("utf-8")
        )

        manifest = PresetManifest(manifest_path)
        assert manifest.description == "中文测试 — émojis 🚀"

    def test_invalid_utf8_bytes_raises_validation_error(self, temp_dir):
        """Negative case: file containing invalid UTF-8 bytes raises PresetValidationError, not raw UnicodeDecodeError."""
        manifest_path = temp_dir / "preset.yml"
        manifest_path.write_bytes(b"\xff\xfe not valid utf-8 \xff\n")

        with pytest.raises(PresetValidationError, match="not valid UTF-8"):
            PresetManifest(manifest_path)

    def test_non_mapping_yaml_raises_validation_error(self, temp_dir):
        """Manifest whose YAML root is a scalar or list raises PresetValidationError, not TypeError."""
        manifest_path = temp_dir / "preset.yml"
        for bad_content in ("42\n", "[1, 2]\n"):
            manifest_path.write_text(bad_content, encoding="utf-8")
            with pytest.raises(PresetValidationError, match="YAML mapping"):
                PresetManifest(manifest_path)

    @pytest.mark.parametrize("section", ["preset", "requires", "provides"])
    @pytest.mark.parametrize("bad_value", [None, [], "text"])
    def test_required_section_not_mapping_raises_validation_error(
        self, temp_dir, valid_pack_data, section, bad_value
    ):
        """Required manifest sections reject null, list, and scalar values."""
        valid_pack_data[section] = bad_value
        manifest_path = temp_dir / "preset.yml"
        manifest_path.write_text(
            yaml.safe_dump(valid_pack_data),
            encoding="utf-8",
        )

        with pytest.raises(
            PresetValidationError,
            match=rf"Invalid {section}: expected a mapping",
        ):
            PresetManifest(manifest_path)

    @pytest.mark.parametrize("field", ["id", "name", "version", "description"])
    @pytest.mark.parametrize("bad", [1.0, 5, None, ["a"], {"a": 1}, True])
    def test_preset_metadata_field_not_string_raises_validation_error(
        self, temp_dir, valid_pack_data, field, bad
    ):
        """A non-string preset.<field> raises PresetValidationError, not a raw
        TypeError.

        The loop over these four fields only checked key PRESENCE, then fed the
        values to ``re.match`` (id) and ``packaging.Version`` (version), both of
        which raise a bare TypeError on a non-string. YAML makes that an easy
        authoring slip: unquoted ``version: 1.0`` parses as a float and ``id: 2``
        as an int. TypeError is not a PresetValidationError, so it escaped
        list_installed()'s "Corrupted preset" fallback and made
        `specify preset list` exit 1 with a raw traceback, hiding every healthy
        preset too. The sibling IntegrationDescriptor already type-checks the
        same four fields.
        """
        valid_pack_data["preset"][field] = bad
        manifest_path = temp_dir / "preset.yml"
        manifest_path.write_text(yaml.safe_dump(valid_pack_data), encoding="utf-8")

        with pytest.raises(
            PresetValidationError,
            match=rf"Invalid preset\.{field}: expected a string",
        ):
            PresetManifest(manifest_path)

    @pytest.mark.parametrize("field", ["name", "file"])
    @pytest.mark.parametrize("bad", [1.0, 5, None, ["a"], {"a": 1}, True])
    def test_template_entry_field_not_string_raises_validation_error(
        self, temp_dir, valid_pack_data, field, bad
    ):
        """A non-string template ``name``/``file`` raises PresetValidationError.

        ``name`` reaches ``re.match`` and ``file`` reaches ``os.path.normpath``;
        both raise a bare TypeError on a non-string. The sibling extension
        manifest already rejects a non-string command ``file`` via
        relative_extension_path_violation().
        """
        valid_pack_data["provides"]["templates"][0][field] = bad
        manifest_path = temp_dir / "preset.yml"
        manifest_path.write_text(yaml.safe_dump(valid_pack_data), encoding="utf-8")

        with pytest.raises(
            PresetValidationError,
            match=rf"Invalid template {field}: expected a string",
        ):
            PresetManifest(manifest_path)

    @pytest.mark.parametrize(
        "bad",
        [
            5, "oops", {"a": 1},   # truthy non-lists
            0, False, None, "", {},  # FALSY non-lists: must not fall through to
                                     # the misleading "at least one template"
        ],
    )
    def test_non_list_templates_raises_validation_error(
        self, temp_dir, valid_pack_data, bad
    ):
        """A non-list provides.templates raises the accurate type error, not a raw
        'int object is not iterable' TypeError and not the misleading "must provide
        at least one template" (which a falsy non-list hit while the type check
        sat behind the emptiness check) — mirrors ExtensionManifest."""
        valid_pack_data["provides"]["templates"] = bad
        manifest_path = temp_dir / "preset.yml"
        manifest_path.write_text(yaml.dump(valid_pack_data), encoding="utf-8")
        with pytest.raises(PresetValidationError, match="templates.*expected a list"):
            PresetManifest(manifest_path)

    @pytest.mark.parametrize("bad_entry", [None, 5, "oops", ["nested"]])
    def test_non_mapping_template_entry_raises_validation_error(
        self, temp_dir, valid_pack_data, bad_entry
    ):
        """A non-mapping template entry (null/scalar/list) raises PresetValidationError,
        not a raw 'argument of type ... is not iterable' TypeError from the
        `"type" not in tmpl` membership test — mirrors ExtensionManifest."""
        valid_pack_data["provides"]["templates"] = [bad_entry]
        manifest_path = temp_dir / "preset.yml"
        manifest_path.write_text(yaml.dump(valid_pack_data), encoding="utf-8")
        with pytest.raises(PresetValidationError, match="must be a mapping"):
            PresetManifest(manifest_path)

    def test_missing_schema_version(self, temp_dir, valid_pack_data):
        """Test missing schema_version field."""
        del valid_pack_data["schema_version"]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Missing required field: schema_version"):
            PresetManifest(manifest_path)

    def test_wrong_schema_version(self, temp_dir, valid_pack_data):
        """Test unsupported schema version."""
        valid_pack_data["schema_version"] = "2.0"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Unsupported schema version"):
            PresetManifest(manifest_path)

    def test_missing_pack_id(self, temp_dir, valid_pack_data):
        """Test missing preset.id field."""
        del valid_pack_data["preset"]["id"]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Missing preset.id"):
            PresetManifest(manifest_path)

    def test_invalid_pack_id_format(self, temp_dir, valid_pack_data):
        """Test invalid pack ID format."""
        valid_pack_data["preset"]["id"] = "Invalid_ID"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid preset ID"):
            PresetManifest(manifest_path)

    def test_invalid_version(self, temp_dir, valid_pack_data):
        """Test invalid semantic version."""
        valid_pack_data["preset"]["version"] = "not-a-version"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid version"):
            PresetManifest(manifest_path)

    def test_missing_speckit_version(self, temp_dir, valid_pack_data):
        """Test missing requires.speckit_version."""
        del valid_pack_data["requires"]["speckit_version"]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Missing requires.speckit_version"):
            PresetManifest(manifest_path)

    @pytest.mark.parametrize(
        "bad",
        [
            1.0,            # unquoted YAML float -- the likeliest authoring slip
            5,              # unquoted int
            True,           # YAML `yes`/`true`
            None,           # `speckit_version:` written but left empty
            [">=0.1.0"],    # iterable: slips past SpecifierSet() entirely
            {"min": "0.1"},  # iterable: same
            "   ",          # blank string must not mean "any version"
        ],
    )
    def test_non_string_speckit_version(self, temp_dir, valid_pack_data, bad):
        """A non-string requires.speckit_version must be a PresetValidationError.

        It was presence-checked only, so it reached ``SpecifierSet(required)`` in
        check_compatibility(), which is guarded by ``except InvalidSpecifier``
        alone. A non-string escapes that guard two ways: scalars raise TypeError
        from the constructor, and a list/dict is iterable so SpecifierSet accepts
        it and the failure surfaces later as ``AttributeError: 'str' object has no
        attribute 'filter'`` from inside .contains().
        """
        valid_pack_data["requires"]["speckit_version"] = bad
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(
            PresetValidationError, match="Invalid requires.speckit_version"
        ):
            PresetManifest(manifest_path)

    def test_no_templates_provided(self, temp_dir, valid_pack_data):
        """Test pack with no templates."""
        valid_pack_data["provides"]["templates"] = []
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="must provide at least one template"):
            PresetManifest(manifest_path)

    def test_invalid_template_type(self, temp_dir, valid_pack_data):
        """Test template with invalid type."""
        valid_pack_data["provides"]["templates"][0]["type"] = "invalid"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid template type"):
            PresetManifest(manifest_path)

    def test_valid_template_types(self):
        """Test that all expected template types are valid."""
        assert "template" in VALID_PRESET_TEMPLATE_TYPES
        assert "command" in VALID_PRESET_TEMPLATE_TYPES
        assert "script" in VALID_PRESET_TEMPLATE_TYPES

    def test_template_missing_required_fields(self, temp_dir, valid_pack_data):
        """Test template missing required fields."""
        valid_pack_data["provides"]["templates"] = [{"type": "template"}]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="missing 'type', 'name', or 'file'"):
            PresetManifest(manifest_path)

    def test_invalid_template_name_format(self, temp_dir, valid_pack_data):
        """Test template with invalid name format."""
        valid_pack_data["provides"]["templates"][0]["name"] = "Invalid Name"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid template name"):
            PresetManifest(manifest_path)

    def test_get_hash(self, pack_dir):
        """Test manifest hash calculation."""
        manifest = PresetManifest(pack_dir / "preset.yml")
        hash_val = manifest.get_hash()
        assert hash_val.startswith("sha256:")
        import hashlib
        content = (pack_dir / "preset.yml").read_bytes()
        expected = f"sha256:{hashlib.sha256(content).hexdigest()}"
        assert hash_val == expected

    def test_multiple_templates(self, temp_dir, valid_pack_data):
        """Test pack with multiple templates of different types."""
        valid_pack_data["provides"]["templates"] = [
            {"type": "template", "name": "spec-template", "file": "templates/spec-template.md"},
            {"type": "template", "name": "plan-template", "file": "templates/plan-template.md"},
            {"type": "command", "name": "specify", "file": "commands/specify.md"},
            {"type": "script", "name": "create-new-feature", "file": "scripts/create-new-feature.sh"},
        ]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        manifest = PresetManifest(manifest_path)
        assert len(manifest.templates) == 4

    def test_duplicate_template_name_and_type_raises_validation_error(
        self, temp_dir, valid_pack_data
    ):
        """A later entry with the same (name, type) pair must be rejected.

        ``PresetResolver._manifest_declared_template`` returns the FIRST
        'provides.templates' entry matching a given (name, type) pair, so a
        later duplicate would be silently unreachable while still being
        counted by ``PresetManifest.templates`` -- mirroring the sibling bug
        fixed for ``ExtensionManifest``'s provides.templates/scripts (#4016).
        """
        valid_pack_data["provides"]["templates"] = [
            {"type": "command", "name": "specify", "file": "commands/specify-v1.md"},
            {"type": "command", "name": "specify", "file": "commands/specify-v2.md"},
        ]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Duplicate template name"):
            PresetManifest(manifest_path)

    def test_same_name_different_type_templates_allowed(
        self, temp_dir, valid_pack_data
    ):
        """The same name may recur across different template types."""
        valid_pack_data["provides"]["templates"] = [
            {"type": "template", "name": "specify", "file": "templates/specify.md"},
            {"type": "command", "name": "specify", "file": "commands/specify.md"},
        ]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        manifest = PresetManifest(manifest_path)
        assert len(manifest.templates) == 2

    def test_requires_extensions_absent_is_valid(self, temp_dir, valid_pack_data):
        """A preset with no declared dependencies stays valid and reports none."""
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        assert PresetManifest(manifest_path).requires_extensions == []

    def test_requires_extensions_accepts_both_forms(self, temp_dir, valid_pack_data):
        """Bare ids and mappings normalize to the same shape."""
        valid_pack_data["requires"]["extensions"] = [
            "speckit-inventory",
            {"id": "other-ext", "version": ">=1.2.0", "required": False},
        ]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)

        assert PresetManifest(manifest_path).requires_extensions == [
            {"id": "speckit-inventory", "version": None, "required": True},
            {"id": "other-ext", "version": ">=1.2.0", "required": False},
        ]

    @pytest.mark.parametrize(
        "bad, expected",
        [
            ("speckit-inventory", "Invalid requires.extensions"),      # str, not list
            ({"id": "x"}, "Invalid requires.extensions"),              # mapping, not list
            ([123], r"Invalid requires\.extensions\[0\]"),             # member not str/mapping
            ([None], r"Invalid requires\.extensions\[0\]"),
            ([{"version": ">=1"}], r"Missing requires\.extensions\[0\]\.id"),
            ([{"id": 5}], r"Invalid requires\.extensions\[0\]\.id"),
            ([{"id": "Bad_ID"}], r"Invalid requires\.extensions\[0\]\.id"),
            (["Bad_ID"], r"Invalid requires\.extensions\[0\]\.id"),
            ([{"id": "x", "version": 1.0}], r"Invalid requires\.extensions\[0\]\.version"),
            ([{"id": "x", "version": "  "}], r"Invalid requires\.extensions\[0\]\.version"),
            ([{"id": "x", "version": "nonsense"}], r"Invalid requires\.extensions\[0\]\.version"),
            ([{"id": "x", "required": "yes"}], r"Invalid requires\.extensions\[0\]\.required"),
            # `$` also matches before a trailing newline, so an anchored
            # re.match would admit these while the resolver's fullmatch-based
            # safe-id check rejects them.
            (["demo-ext\n"], r"Invalid requires\.extensions\[0\]\.id"),
            ([{"id": "demo-ext\n"}], r"Invalid requires\.extensions\[0\]\.id"),
            (["demo\next"], r"Invalid requires\.extensions\[0\]\.id"),
        ],
    )
    def test_requires_extensions_rejects_malformed(
        self, temp_dir, valid_pack_data, bad, expected
    ):
        """Malformed dependency declarations fail as PresetValidationError.

        Same reasoning as requires.speckit_version: an unvalidated value reaches
        ``SpecifierSet`` or ``re.match`` later and surfaces as a bare TypeError
        that no caller handles as a malformed manifest.
        """
        valid_pack_data["requires"]["extensions"] = bad
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match=expected):
            PresetManifest(manifest_path)


class TestCompositionStrategyValidation:
    """Test strategy field validation in PresetManifest."""

    def test_valid_replace_strategy(self, temp_dir, valid_pack_data):
        """Test that replace strategy is accepted."""
        valid_pack_data["provides"]["templates"][0]["strategy"] = "replace"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        (temp_dir / "templates").mkdir(exist_ok=True)
        (temp_dir / "templates" / "spec-template.md").write_text("test")
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "replace"

    def test_valid_prepend_strategy(self, temp_dir, valid_pack_data):
        """Test that prepend strategy is accepted for templates."""
        valid_pack_data["provides"]["templates"][0]["strategy"] = "prepend"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        (temp_dir / "templates").mkdir(exist_ok=True)
        (temp_dir / "templates" / "spec-template.md").write_text("test")
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "prepend"

    def test_valid_append_strategy(self, temp_dir, valid_pack_data):
        """Test that append strategy is accepted for templates."""
        valid_pack_data["provides"]["templates"][0]["strategy"] = "append"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        (temp_dir / "templates").mkdir(exist_ok=True)
        (temp_dir / "templates" / "spec-template.md").write_text("test")
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "append"

    def test_valid_wrap_strategy(self, temp_dir, valid_pack_data):
        """Test that wrap strategy is accepted for templates."""
        valid_pack_data["provides"]["templates"][0]["strategy"] = "wrap"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        (temp_dir / "templates").mkdir(exist_ok=True)
        (temp_dir / "templates" / "spec-template.md").write_text("test")
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "wrap"

    def test_default_strategy_is_replace(self, pack_dir):
        """Test that omitting strategy defaults to replace (key is absent)."""
        manifest = PresetManifest(pack_dir / "preset.yml")
        # Strategy key should not be present in the manifest data
        assert "strategy" not in manifest.templates[0]
        # But consumers should treat missing strategy as "replace"
        assert manifest.templates[0].get("strategy", "replace") == "replace"

    def test_invalid_strategy_rejected(self, temp_dir, valid_pack_data):
        """Test that invalid strategy values are rejected."""
        valid_pack_data["provides"]["templates"][0]["strategy"] = "merge"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid strategy"):
            PresetManifest(manifest_path)

    def test_prepend_rejected_for_scripts(self, temp_dir, valid_pack_data):
        """Test that prepend strategy is rejected for scripts."""
        valid_pack_data["provides"]["templates"] = [{
            "type": "script",
            "name": "create-new-feature",
            "file": "scripts/create-new-feature.sh",
            "strategy": "prepend",
        }]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid strategy.*for script"):
            PresetManifest(manifest_path)

    def test_append_rejected_for_scripts(self, temp_dir, valid_pack_data):
        """Test that append strategy is rejected for scripts."""
        valid_pack_data["provides"]["templates"] = [{
            "type": "script",
            "name": "create-new-feature",
            "file": "scripts/create-new-feature.sh",
            "strategy": "append",
        }]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid strategy.*for script"):
            PresetManifest(manifest_path)

    def test_wrap_accepted_for_scripts(self, temp_dir, valid_pack_data):
        """Test that wrap strategy is accepted for scripts."""
        valid_pack_data["provides"]["templates"] = [{
            "type": "script",
            "name": "create-new-feature",
            "file": "scripts/create-new-feature.sh",
            "strategy": "wrap",
        }]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "wrap"

    def test_replace_accepted_for_scripts(self, temp_dir, valid_pack_data):
        """Test that replace strategy is accepted for scripts."""
        valid_pack_data["provides"]["templates"] = [{
            "type": "script",
            "name": "create-new-feature",
            "file": "scripts/create-new-feature.sh",
            "strategy": "replace",
        }]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "replace"

    def test_prepend_accepted_for_commands(self, temp_dir, valid_pack_data):
        """Test that prepend strategy is accepted for commands."""
        valid_pack_data["provides"]["templates"] = [{
            "type": "command",
            "name": "speckit.specify",
            "file": "commands/speckit.specify.md",
            "strategy": "prepend",
        }]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "prepend"
