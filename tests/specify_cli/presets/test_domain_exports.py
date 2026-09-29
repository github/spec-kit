"""Existing preset import paths remain usable after the domain split."""

from importlib import import_module

import pytest

import specify_cli.presets as presets


@pytest.mark.parametrize(
    ("name", "module"),
    [
        ("PresetError", "_manifest"),
        ("PresetValidationError", "_manifest"),
        ("PresetCompatibilityError", "_manifest"),
        ("PresetManifest", "_manifest"),
        ("PresetRegistry", "_registry"),
        ("PresetCatalogEntry", "_catalog"),
        ("PresetCatalog", "_catalog"),
        ("PresetResolver", "_resolver"),
        ("PresetManager", "_manager"),
        ("_materialize_constitution_template", "_manager"),
        ("_constitution_provenance_matches_preset", "_manager"),
        ("_substitute_core_template", "_manager_commands"),
    ],
)
def test_package_exports_preserve_private_implementation_identity(name, module):
    implementation = import_module(f"specify_cli.presets.{module}")

    assert getattr(presets, name) is getattr(implementation, name)
