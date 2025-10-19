import yaml
from pathlib import Path
from specify_cli.guards.types import GuardType


def test_load_guard_type(temp_project_dir, sample_guard_type_manifest):
    types_dir = temp_project_dir / ".specify" / "guards" / "types"
    type_dir = types_dir / "unit-pytest"
    type_dir.mkdir(parents=True)
    
    manifest_path = type_dir / "guard-type.yaml"
    with open(manifest_path, 'w') as f:
        yaml.dump(sample_guard_type_manifest, f)
    
    guard_type = GuardType(type_dir)
    
    assert guard_type.name == "unit-pytest"
    assert guard_type.manifest["version"] == "1.0.0"
    assert guard_type.manifest["description"] == "Unit testing with pytest"


def test_validate_structure(temp_project_dir, sample_guard_type_manifest):
    types_dir = temp_project_dir / ".specify" / "guards" / "types"
    type_dir = types_dir / "unit-pytest"
    type_dir.mkdir(parents=True)
    
    manifest_path = type_dir / "guard-type.yaml"
    with open(manifest_path, 'w') as f:
        yaml.dump(sample_guard_type_manifest, f)
    
    guard_type = GuardType(type_dir)
    
    assert guard_type.validate_structure() is True


def test_list_types(temp_project_dir, sample_guard_type_manifest):
    guards_base = temp_project_dir / ".specify" / "guards"
    types_dir = guards_base / "types"
    
    for type_name in ["unit-pytest", "api", "database"]:
        type_dir = types_dir / type_name
        type_dir.mkdir(parents=True)
        manifest_path = type_dir / "guard-type.yaml"
        manifest = sample_guard_type_manifest.copy()
        manifest["name"] = type_name
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f)
    
    types = GuardType.list_types(guards_base)
    
    assert len(types) == 3
    assert "unit-pytest" in types
    assert "api" in types
    assert "database" in types


def test_list_types_with_custom(temp_project_dir, sample_guard_type_manifest):
    guards_base = temp_project_dir / ".specify" / "guards"
    official_dir = guards_base / "types"
    custom_dir = guards_base / "types-custom"
    
    # Create official types
    for type_name in ["unit-pytest", "api"]:
        type_dir = official_dir / type_name
        type_dir.mkdir(parents=True)
        manifest_path = type_dir / "guard-type.yaml"
        manifest = sample_guard_type_manifest.copy()
        manifest["name"] = type_name
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f)
    
    # Create custom types
    for type_name in ["my-custom", "another-custom"]:
        type_dir = custom_dir / type_name
        type_dir.mkdir(parents=True)
        manifest_path = type_dir / "guard-type.yaml"
        manifest = sample_guard_type_manifest.copy()
        manifest["name"] = type_name
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f)
    
    types = GuardType.list_types(guards_base)
    
    assert len(types) == 4
    assert "unit-pytest" in types
    assert "api" in types
    assert "my-custom" in types
    assert "another-custom" in types


def test_load_type(temp_project_dir, sample_guard_type_manifest):
    guards_base = temp_project_dir / ".specify" / "guards"
    types_dir = guards_base / "types"
    type_dir = types_dir / "unit-pytest"
    type_dir.mkdir(parents=True)
    
    manifest_path = type_dir / "guard-type.yaml"
    with open(manifest_path, 'w') as f:
        yaml.dump(sample_guard_type_manifest, f)
    
    guard_type = GuardType.load_type(guards_base, "unit-pytest")
    
    assert guard_type is not None
    assert guard_type.name == "unit-pytest"


def test_load_custom_type(temp_project_dir, sample_guard_type_manifest):
    guards_base = temp_project_dir / ".specify" / "guards"
    custom_dir = guards_base / "types-custom"
    type_dir = custom_dir / "my-custom"
    type_dir.mkdir(parents=True)
    
    manifest_path = type_dir / "guard-type.yaml"
    manifest = sample_guard_type_manifest.copy()
    manifest["name"] = "my-custom"
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f)
    
    guard_type = GuardType.load_type(guards_base, "my-custom")
    
    assert guard_type is not None
    assert guard_type.name == "my-custom"


def test_load_nonexistent_type(temp_project_dir):
    guards_base = temp_project_dir / ".specify" / "guards"
    guards_base.mkdir(parents=True)
    
    guard_type = GuardType.load_type(guards_base, "nonexistent")
    
    assert guard_type is None
