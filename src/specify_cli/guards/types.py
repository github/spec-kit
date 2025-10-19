import yaml
from pathlib import Path
from typing import Dict, List, Optional


class GuardType:
    
    def __init__(self, guard_type_dir: Path):
        self.guard_type_dir = guard_type_dir
        self.name = guard_type_dir.name
        self.manifest_path = guard_type_dir / "guard-type.yaml"
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Guard type manifest not found: {self.manifest_path}")
        
        with open(self.manifest_path, 'r') as f:
            return yaml.safe_load(f)
    
    def validate_structure(self) -> bool:
        required_fields = ["name", "version", "description", "category"]
        
        for field in required_fields:
            if field not in self.manifest:
                raise ValueError(f"Missing required field in manifest: {field}")
        
        return True
    
    @staticmethod
    def list_types(types_dir: Path) -> List[str]:
        """List all guard types from both official and custom directories.
        
        Args:
            types_dir: Base guards directory (e.g., .specify/guards)
        
        Returns:
            List of type names from types/ and types-custom/ combined
        """
        type_names = []
        
        official_dir = types_dir / "types"
        if official_dir.exists():
            type_names.extend([
                d.name for d in official_dir.iterdir() 
                if d.is_dir() and (d / "guard-type.yaml").exists()
            ])
        
        custom_dir = types_dir / "types-custom"
        if custom_dir.exists():
            type_names.extend([
                d.name for d in custom_dir.iterdir() 
                if d.is_dir() and (d / "guard-type.yaml").exists()
            ])
        
        return type_names
    
    @staticmethod
    def load_type(types_dir: Path, type_name: str) -> Optional['GuardType']:
        """Load a guard type from either official or custom directory.
        
        Args:
            types_dir: Base guards directory (e.g., .specify/guards)
            type_name: Name of the guard type
        
        Returns:
            GuardType instance or None if not found
        """
        # Check official types first
        official_dir = types_dir / "types" / type_name
        if official_dir.exists() and (official_dir / "guard-type.yaml").exists():
            return GuardType(official_dir)
        
        # Check custom types
        custom_dir = types_dir / "types-custom" / type_name
        if custom_dir.exists() and (custom_dir / "guard-type.yaml").exists():
            return GuardType(custom_dir)
        
        return None
    
    @staticmethod
    def get_all_types_with_descriptions(types_dir: Path) -> List[Dict]:
        """Get all guard types with their descriptions for AI agent context.
        
        Scans both official (types/) and custom (types-custom/) directories.
        
        Args:
            types_dir: Base guards directory (e.g., .specify/guards)
        
        Returns:
            List of dicts with type metadata, includes 'source' field (official/custom)
        """
        types_info = []
        
        official_dir = types_dir / "types"
        custom_dir = types_dir / "types-custom"
        
        # Scan official types
        if official_dir.exists():
            for type_name in [d.name for d in official_dir.iterdir() 
                             if d.is_dir() and (d / "guard-type.yaml").exists()]:
                guard_type = GuardType(official_dir / type_name)
                types_info.append({
                    "name": guard_type.manifest.get("name"),
                    "version": guard_type.manifest.get("version"),
                    "category": guard_type.manifest.get("category"),
                    "description": guard_type.manifest.get("description", "").strip(),
                    "when_to_use": guard_type.manifest.get("ai_hints", {}).get("when_to_use", "").strip(),
                    "boilerplate_explanation": guard_type.manifest.get("ai_hints", {}).get("boilerplate_explanation", "").strip(),
                    "dependencies": guard_type.manifest.get("dependencies", {}),
                    "scaffolder_class": guard_type.manifest.get("scaffolder_class"),
                    "source": "official"
                })
        
        # Scan custom types
        if custom_dir.exists():
            for type_name in [d.name for d in custom_dir.iterdir() 
                             if d.is_dir() and (d / "guard-type.yaml").exists()]:
                guard_type = GuardType(custom_dir / type_name)
                types_info.append({
                    "name": guard_type.manifest.get("name"),
                    "version": guard_type.manifest.get("version"),
                    "category": guard_type.manifest.get("category"),
                    "description": guard_type.manifest.get("description", "").strip(),
                    "when_to_use": guard_type.manifest.get("ai_hints", {}).get("when_to_use", "").strip(),
                    "boilerplate_explanation": guard_type.manifest.get("ai_hints", {}).get("boilerplate_explanation", "").strip(),
                    "dependencies": guard_type.manifest.get("dependencies", {}),
                    "scaffolder_class": guard_type.manifest.get("scaffolder_class"),
                    "source": "custom"
                })
        
        return types_info
