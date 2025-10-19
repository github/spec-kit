from pathlib import Path
from typing import Dict, Any
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

from specify_cli.guards.scaffolder import GuardScaffolder


class APIScaffolder(GuardScaffolder):
    """Scaffolder for api guard type."""
    
    def scaffold(self) -> Dict[str, Any]:
        """Generate API test files with pytest and schema validation boilerplate."""
        
        test_filename = f"{self.guard_id}_{self.name}.py"
        test_file_path = self.project_root / "tests" / "api" / "guards" / test_filename
        
        schema_filename = f"{self.guard_id}_{self.name}_schema.json"
        schema_file_path = self.project_root / "tests" / "api" / "guards" / "schemas" / schema_filename
        
        context = {
            "guard_id": self.guard_id,
            "name": self.name,
            "description": f"API contract tests for {self.name}",
            "schema_path": f"schemas/{schema_filename}"
        }
        
        test_content = self.render_template("test.py.j2", context)
        self.create_file(test_file_path, test_content)
        
        schema_content = self.render_template("schema.json.j2", context)
        self.create_file(schema_file_path, schema_content)
        
        make_target = f"test-guard-{self.guard_id}"
        make_command = f"uv run pytest {test_file_path} -v"
        self.update_makefile(make_target, make_command)
        
        files_created = [str(test_file_path), str(schema_file_path)]
        
        return {
            "guard_id": self.guard_id,
            "files_created": files_created,
            "command": f"make {make_target}",
            "next_steps": (
                f"\n✓ Guard {self.guard_id} created successfully!\n\n"
                f"Files generated:\n"
                f"  - {test_file_path}\n"
                f"  - {schema_file_path}\n\n"
                f"Next steps:\n"
                f"  1. Update API endpoint URLs in {test_file_path}\n"
                f"  2. Define expected schemas in {schema_file_path}\n"
                f"  3. Add endpoint-specific tests in {test_file_path}\n"
                f"  4. Run guard: specify guard run {self.guard_id}\n"
                f"  5. Or run directly: make {make_target}\n"
            )
        }
