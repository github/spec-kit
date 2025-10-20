import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from specify_cli.guards.scaffolder import BaseScaffolder


class StaticAnalysisPythonScaffolder(BaseScaffolder):
    """Scaffolder for static-analysis-python guard type."""
    
    def scaffold(self) -> Dict[str, Any]:
        guard_file = self.project_root / ".specify" / "guards" / self.guard_id / f"{self.guard_id}.py"
        
        context = {
            "guard_id": self.guard_id,
            "name": self.name,
            "description": f"Python static analysis for {self.name}"
        }
        
        guard_content = self.render_template("guard.py.j2", context)
        self.create_file(guard_file, guard_content)
        
        return {
            "guard_id": self.guard_id,
            "files_created": [str(guard_file)],
            "command": f"python {guard_file}",
            "next_steps": f"Run: specify guard run {self.guard_id}"
        }
