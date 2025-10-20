"""
Guard Registry - Category × Type Architecture

Manages guard types, categories, types, and guard instances using
the Category × Type matrix organization.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .types import Category, GuardType, Type
from .utils import generate_guard_id, load_yaml, save_json, save_yaml


class GuardRegistry:
    """Registry for managing guards with Category × Type architecture."""
    
    def __init__(self, guards_base_path: Path):
        """
        Initialize guard registry.
        
        Directory structure:
        .specify/guards/
        ├── G001/
        │   ├── guard.yaml
        │   └── history.json
        ├── G002/
        └── manifest.yaml
        """
        self.base_path = guards_base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.manifest_path = self.base_path / "manifest.yaml"
        
        # Root paths for guard type definitions
        self.official_types_path = Path(__file__).parent.parent.parent.parent / "guards" / "types"
        self.custom_types_path = Path(__file__).parent.parent.parent.parent / ".specify" / "guards" / "types-custom"
        
        # Cache for loaded categories and types
        self._categories_cache: Optional[dict[str, Category]] = None
        self._types_cache: Optional[dict[str, Type]] = None
        self._guard_types_cache: Optional[dict[str, GuardType]] = None
    
    def get_categories(self) -> list[Category]:
        """Get all registered categories."""
        if self._categories_cache is None:
            self._load_categories()
        assert self._categories_cache is not None
        return list(self._categories_cache.values())
    
    def get_types(self) -> list[Type]:
        """Get all registered types."""
        if self._types_cache is None:
            self._load_types()
        assert self._types_cache is not None
        return list(self._types_cache.values())
    
    def get_guard_type(self, type_id: str) -> Optional[GuardType]:
        """
        Get guard type by ID (e.g., 'pytest-unit-tests').
        
        Args:
            type_id: Guard type identifier
        
        Returns:
            GuardType if found, None otherwise
        """
        if self._guard_types_cache is None:
            self._load_guard_types()
        assert self._guard_types_cache is not None
        return self._guard_types_cache.get(type_id)
    
    def get_matrix(self) -> dict[str, dict[str, Optional[GuardType]]]:
        """
        Get Category × Type matrix showing available guard types.
        
        Returns:
            Dictionary: {category_name: {type_name: GuardType or None}}
        """
        categories = self.get_categories()
        types = self.get_types()
        
        if self._guard_types_cache is None:
            self._load_guard_types()
        assert self._guard_types_cache is not None
        
        matrix = {}
        for category in categories:
            matrix[category.name] = {}
            for type_obj in types:
                matrix[category.name][type_obj.name] = None
        
        for guard_type in self._guard_types_cache.values():
            category_name = guard_type.category.name
            type_name = guard_type.type.name
            if category_name in matrix and type_name in matrix[category_name]:
                matrix[category_name][type_name] = guard_type
        
        return matrix
    
    def register_category(self, category: Category) -> None:
        """Register a new category."""
        if self._categories_cache is None:
            self._load_categories()
        assert self._categories_cache is not None
        self._categories_cache[category.name] = category
    
    def register_type(self, type_obj: Type) -> None:
        """Register a new type."""
        if self._types_cache is None:
            self._load_types()
        assert self._types_cache is not None
        self._types_cache[type_obj.name] = type_obj
    
    def _load_categories(self) -> None:
        """Load categories from guard type definitions."""
        self._categories_cache = {}
        
        # TODO: Implement category loading from YAML files
        # For now, create default categories from existing guard types
        
        # Check official types
        if self.official_types_path.exists():
            for type_dir in self.official_types_path.iterdir():
                if type_dir.is_dir():
                    # Create category from directory name
                    category = self._create_category_from_dir(type_dir)
                    if category:
                        self._categories_cache[category.name] = category
    
    def _load_types(self) -> None:
        """Load types from guard type definitions."""
        self._types_cache = {}
        
        # TODO: Implement type loading from YAML files
        # For now, create default types
        default_types = [
            Type(
                name="unit-testing",
                description="Unit-level component testing",
                standard_definition="100% coverage of public APIs, test isolation, deterministic tests",
                success_criteria=[
                    "All public functions have tests",
                    "Test coverage >= threshold",
                    "All tests pass independently"
                ],
                common_failures=[
                    "Missing test coverage for new functions",
                    "Tests depend on execution order",
                    "Flaky tests with non-deterministic results"
                ],
                teaching_content="Unit tests validate individual components in isolation"
            ),
            Type(
                name="api-contracts",
                description="API endpoint contract validation",
                standard_definition="All endpoints conform to schema, proper status codes, error handling",
                success_criteria=[
                    "All endpoints return expected schemas",
                    "Proper HTTP status codes",
                    "Error responses are well-formed"
                ],
                common_failures=[
                    "Schema mismatches",
                    "Missing error handling",
                    "Incorrect status codes"
                ],
                teaching_content="API contracts ensure consistent interfaces"
            )
        ]
        
        for type_obj in default_types:
            self._types_cache[type_obj.name] = type_obj
    
    def _load_guard_types(self) -> None:
        """Load guard types from filesystem."""
        self._guard_types_cache = {}
        
        # Ensure categories and types are loaded
        if self._categories_cache is None:
            self._load_categories()
        if self._types_cache is None:
            self._load_types()
        
        # Load from official types
        if self.official_types_path.exists():
            for type_dir in self.official_types_path.iterdir():
                if type_dir.is_dir():
                    guard_type = self._create_guard_type_from_dir(type_dir)
                    if guard_type:
                        self._guard_types_cache[guard_type.id] = guard_type
        
        # Load from custom types
        if self.custom_types_path.exists():
            for type_dir in self.custom_types_path.iterdir():
                if type_dir.is_dir():
                    guard_type = self._create_guard_type_from_dir(type_dir)
                    if guard_type:
                        self._guard_types_cache[guard_type.id] = guard_type
    
    def _create_category_from_dir(self, type_dir: Path) -> Optional[Category]:
        """Create Category from guard type directory."""
        guard_type_yaml = type_dir / "guard-type.yaml"
        if not guard_type_yaml.exists():
            return None
        
        try:
            data = load_yaml(guard_type_yaml)
            
            category_name = data.get("category", type_dir.name)
            
            return Category(
                name=category_name,
                description=data.get("description", f"{category_name} guard category"),
                yaml_path=guard_type_yaml,
                src_path=type_dir / "scaffolder.py" if (type_dir / "scaffolder.py").exists() else None,
                invocation_pattern=data.get("invocation_pattern", ""),
                input_schema=data.get("input_schema", {}),
                output_schema=data.get("output_schema", {}),
                params_schema=data.get("params_schema", {}),
                teaching_content=data.get("category_teaching", f"How to build {category_name} guards")
            )
        except Exception:
            return None
    
    def _create_guard_type_from_dir(self, type_dir: Path) -> Optional[GuardType]:
        """Create GuardType from directory."""
        guard_type_yaml = type_dir / "guard-type.yaml"
        if not guard_type_yaml.exists():
            return None
        
        try:
            data = load_yaml(guard_type_yaml)
            
            type_id = type_dir.name
            
            category_name = data.get("category", type_id)
            type_name = data.get("type", "validation")
            
            assert self._categories_cache is not None
            assert self._types_cache is not None
            
            category = self._categories_cache.get(category_name)
            if not category:
                category = Category(
                    name=category_name,
                    description=data.get("description", f"{category_name} guard category"),
                    yaml_path=guard_type_yaml,
                    src_path=type_dir / "scaffolder.py" if (type_dir / "scaffolder.py").exists() else None,
                    invocation_pattern=data.get("invocation_pattern", ""),
                    input_schema=data.get("input_schema", {}),
                    output_schema=data.get("output_schema", {}),
                    params_schema=data.get("params_schema", {}),
                    teaching_content=data.get("category_teaching", f"How to build {category_name} guards")
                )
                self._categories_cache[category_name] = category
            
            type_obj = self._types_cache.get(type_name)
            if not type_obj:
                type_obj = Type(
                    name=type_name,
                    description=data.get("description", ""),
                    standard_definition=data.get("standard", ""),
                    success_criteria=[],
                    common_failures=[],
                    teaching_content=data.get("type_teaching", "")
                )
                self._types_cache[type_name] = type_obj
            
            if not category or not type_obj:
                return None
            
            return GuardType(
                id=type_id,
                category=category,
                type=type_obj,
                scaffolder_path=type_dir / "scaffolder.py",
                templates_dir=type_dir / "templates",
                combined_teaching=f"{category.teaching_content} {type_obj.teaching_content}"
            )
        except Exception:
            return None
    
    def generate_id(self) -> str:
        """Generate next sequential guard ID."""
        existing_ids = []
        if self.base_path.exists():
            for guard_dir in self.base_path.iterdir():
                if guard_dir.is_dir() and guard_dir.name.startswith("G"):
                    existing_ids.append(guard_dir.name)
        
        return generate_guard_id(existing_ids)
    
    def add_guard(
        self,
        guard_id: str,
        guard_type: str,
        name: str,
        command: str,
        files: list[str],
        tags: Optional[list[str]] = None,
        tasks: Optional[list[str]] = None
    ) -> None:
        """Add a new guard to the registry."""
        guard_dir = self.base_path / guard_id
        guard_dir.mkdir(parents=True, exist_ok=True)
        
        guard_yaml_path = guard_dir / "guard.yaml"
        history_json_path = guard_dir / "history.json"
        
        # Create guard.yaml
        guard_data = {
            "id": guard_id,
            "guard_type": guard_type,
            "name": name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": files,
            "command": command,
            "params": {},
            "tags": tags or [],
            "tasks": tasks or []
        }
        save_yaml(guard_yaml_path, guard_data)
        
        # Create empty history.json
        save_json(history_json_path, [])
        
        # Update manifest
        self._update_manifest(guard_id, guard_type, name, tags or [], tasks or [])
    
    def get_guard(self, guard_id: str) -> Optional[dict]:
        """Get guard by ID."""
        guard_yaml = self.base_path / guard_id / "guard.yaml"
        if not guard_yaml.exists():
            return None
        return load_yaml(guard_yaml)
    
    def list_guards(self) -> list[dict]:
        """List all guards."""
        guards = []
        if self.base_path.exists():
            for guard_dir in sorted(self.base_path.iterdir()):
                if guard_dir.is_dir() and guard_dir.name.startswith("G"):
                    guard_yaml = guard_dir / "guard.yaml"
                    if guard_yaml.exists():
                        guards.append(load_yaml(guard_yaml))
        return guards
    
    def _update_manifest(
        self,
        guard_id: str,
        guard_type: str,
        name: str,
        tags: list[str],
        tasks: list[str]
    ) -> None:
        """Update guards manifest with new guard."""
        if self.manifest_path.exists():
            manifest_data = load_yaml(self.manifest_path)
        else:
            manifest_data = {"guards": {}, "tasks": {}, "tags": {}}
        
        # Add guard metadata
        manifest_data["guards"][guard_id] = {
            "type": guard_type,
            "category": guard_type.split("-")[0] if "-" in guard_type else guard_type,
            "name": name,
            "created": datetime.now(timezone.utc).isoformat(),
            "tags": tags,
            "tasks": tasks
        }
        
        # Update tag associations
        for tag in tags:
            if tag not in manifest_data["tags"]:
                manifest_data["tags"][tag] = []
            if guard_id not in manifest_data["tags"][tag]:
                manifest_data["tags"][tag].append(guard_id)
        
        # Update task associations
        for task_id in tasks:
            if task_id not in manifest_data["tasks"]:
                manifest_data["tasks"][task_id] = {
                    "name": f"Task {task_id}",
                    "guards": [],
                    "guard_policy": "all_pass"
                }
            if guard_id not in manifest_data["tasks"][task_id]["guards"]:
                manifest_data["tasks"][task_id]["guards"].append(guard_id)
        
        save_yaml(self.manifest_path, manifest_data)
