"""
Guard Scaffolder - Template-based guard file generation

Generates guard files from templates using Jinja2 with category/type metadata.
"""

import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, UndefinedError

from specify_cli.guards.types import GuardType


class BaseScaffolder(ABC):
    """
    Base class for custom guard scaffolders (feature 001 compatibility).
    
    Guard type developers can extend this to create custom scaffolders.
    """
    
    def __init__(self, guard_id: str, name: str, guard_type: str, project_root: Path):
        self.guard_id = guard_id
        self.name = name
        self.guard_type = guard_type
        self.project_root = project_root
        self.templates_dir = project_root / ".specify" / "guards" / "types" / guard_type / "templates"
    
    @abstractmethod
    def scaffold(self) -> Dict[str, Any]:
        """
        Generate guard files.
        
        Must return dictionary with:
            - files: List[str] - Created file paths  
            - command: str - Command to execute guard
        """
        pass
    
    def render_template(self, template_name: str, context: Dict) -> str:
        """Render template with Jinja2."""
        env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        template = env.get_template(template_name)
        return template.render(**context)
    
    def create_file(self, path: Path, content: str) -> None:
        """Create file with parent directories."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    
    def update_makefile(self, target_name: str, target_command: str) -> None:
        """Add target to Makefile."""
        makefile_path = self.project_root / "Makefile"
        
        if not makefile_path.exists():
            makefile_path.write_text("")
        
        content = makefile_path.read_text()
        
        if target_name in content:
            return
        
        new_target = f"\n{target_name}:\n\t{target_command}\n"
        makefile_path.write_text(content + new_target)


class GuardScaffolder:
    """
    Scaffolds guard files from templates with teaching metadata (feature 003).
    
    Uses GuardType to access category/type information and generates
    files based on templates in the guard type's templates directory.
    """
    
    def __init__(
        self,
        guard_id: str,
        guard_type: GuardType,
        name: str,
        project_root: Path
    ):
        """
        Initialize scaffolder.
        
        Args:
            guard_id: Generated guard ID (e.g., "G001")
            guard_type: GuardType instance with category/type metadata
            name: Guard name (kebab-case)
            project_root: Project root directory
        """
        self.guard_id = guard_id
        self.guard_type = guard_type
        self.name = name
        self.project_root = project_root
        
        # Setup Jinja2 environment
        if guard_type.templates_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(guard_type.templates_dir)),
                trim_blocks=True,
                lstrip_blocks=True
            )
        else:
            self.jinja_env = None
    
    def scaffold(self) -> Dict[str, Any]:
        """
        Generate guard files from templates.
        
        Returns:
            Dictionary with:
                - files: List of created file paths
                - command: Command to execute the guard
        
        Raises:
            FileNotFoundError: If scaffolder.py not found
            Exception: If scaffolding fails
        """
        # Try to load custom scaffolder from guard type directory
        scaffolder_path = self.guard_type.scaffolder_path
        
        if scaffolder_path.exists():
            return self._run_custom_scaffolder(scaffolder_path)
        else:
            # Use default scaffolding
            return self._default_scaffold()
    
    def _run_custom_scaffolder(self, scaffolder_path: Path) -> Dict[str, Any]:
        """
        Run custom scaffolder from guard type directory.
        
        Args:
            scaffolder_path: Path to scaffolder.py
        
        Returns:
            Result dictionary from scaffolder
        """
        # Load the scaffolder module
        spec = importlib.util.spec_from_file_location("custom_scaffolder", scaffolder_path)
        if not spec or not spec.loader:
            raise FileNotFoundError(f"Could not load scaffolder from {scaffolder_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get scaffolder class (try common patterns)
        scaffolder_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                attr_name.endswith("Scaffolder") and 
                attr_name != "BaseScaffolder"):
                scaffolder_class = attr
                break
        
        if not scaffolder_class:
            raise ValueError(f"No scaffolder class found in {scaffolder_path}")
        
        # Instantiate and run (use old interface for compatibility)
        scaffolder = scaffolder_class(
            guard_id=self.guard_id,
            name=self.name,
            guard_type=self.guard_type.id,
            project_root=self.project_root
        )
        
        result = scaffolder.scaffold()
        
        # Normalize result format
        if "files_created" in result:
            result["files"] = result.pop("files_created")
        
        return result
    
    def _default_scaffold(self) -> Dict[str, Any]:
        """
        Default scaffolding when no custom scaffolder exists.
        
        Creates a basic test file from template if available.
        
        Returns:
            Result dictionary
        """
        if not self.jinja_env:
            # No templates available - create minimal file
            return self._create_minimal_guard()
        
        # Try to find a test template
        try:
            template = self.jinja_env.get_template("test.py.j2")
        except TemplateNotFound:
            return self._create_minimal_guard()
        
        # Render template with better error handling
        try:
            content = template.render(
                guard_id=self.guard_id,
                name=self.name,
                guard_type=self.guard_type.id,
                category=self.guard_type.category.name,
                type=self.guard_type.type.name
            )
        except UndefinedError as e:
            raise ValueError(
                f"Template rendering failed: {str(e)}\n\n"
                f"Available variables:\n"
                f"  • guard_id: {self.guard_id}\n"
                f"  • name: {self.name}\n"
                f"  • guard_type: {self.guard_type.id}\n"
                f"  • category: {self.guard_type.category.name}\n"
                f"  • type: {self.guard_type.type.name}\n\n"
                f"Check your template for undefined variables."
            ) from e
        except Exception as e:
            raise ValueError(
                f"Template rendering failed: {str(e)}\n\n"
                f"Template: {self.guard_type.templates_dir / 'test.py.j2'}\n"
                f"This may be due to template syntax errors or missing variables."
            ) from e
        
        # Create test file
        test_dir = self.project_root / "tests" / "guards"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = test_dir / f"{self.guard_id}_{self.name}.py"
        test_file.write_text(content)
        
        return {
            "files": [str(test_file)],
            "command": f"python {test_file}"
        }
    
    def _create_minimal_guard(self) -> Dict[str, Any]:
        """
        Create minimal guard file when no templates available.
        
        Returns:
            Result dictionary
        """
        # Create basic test file
        test_dir = self.project_root / "tests" / "guards"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = test_dir / f"{self.guard_id}_{self.name}.py"
        
        content = f'''"""
Guard {self.guard_id}: {self.name}
Type: {self.guard_type.id}
Category: {self.guard_type.category.name}
Type: {self.guard_type.type.name}

Auto-generated by specify guard create
"""

def test_{self.name.replace("-", "_")}():
    """TODO: Implement validation logic."""
    # Add your validation logic here
    assert True, "Replace with actual validation"


if __name__ == "__main__":
    test_{self.name.replace("-", "_")}()
    print("✓ Guard {self.guard_id} passed")
'''
        
        test_file.write_text(content)
        
        return {
            "files": [str(test_file)],
            "command": f"python {test_file}"
        }
