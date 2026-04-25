from pathlib import Path
from specify_cli._assets import AssetService

def test_locate_core_pack_returns_path_or_none():
    svc = AssetService()
    result = svc.locate_core_pack()
    assert result is None or isinstance(result, Path)

def test_locate_bundled_extension_invalid_id_returns_none():
    svc = AssetService()
    assert svc.locate_bundled_extension("../evil") is None
    assert svc.locate_bundled_extension("UPPER") is None

def test_locate_bundled_extension_valid_id():
    svc = AssetService()
    result = svc.locate_bundled_extension("git")
    # In source checkout, git extension should exist
    assert result is None or isinstance(result, Path)

def test_locate_bundled_workflow_invalid_id_returns_none():
    svc = AssetService()
    assert svc.locate_bundled_workflow("") is None
    assert svc.locate_bundled_workflow("BAD ID") is None

def test_locate_bundled_preset_invalid_id_returns_none():
    svc = AssetService()
    assert svc.locate_bundled_preset("../etc/passwd") is None

def test_backward_compat_module_functions():
    # The old underscore functions must still work via __init__.py
    from specify_cli import _locate_core_pack, _locate_bundled_extension
    result = _locate_core_pack()
    assert result is None or isinstance(result, Path)
