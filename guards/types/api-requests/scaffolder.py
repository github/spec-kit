"""Scaffolder for api-requests guard type"""
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from specify_cli.guards.scaffolder import BaseScaffolder


class ApiRequestsScaffolder(BaseScaffolder):
    """Scaffolder for api-requests guard type."""
    
    def scaffold(self) -> Dict[str, Any]:
        guard_file = self.project_root / ".specify" / "guards" / self.guard_id / f"{self.guard_id}.py"
        
        context = {
            "guard_id": self.guard_id,
            "name": self.name,
            "description": f"API validation for {self.name}",
            "base_url": "",
            "endpoints": [],
            "timeout": 10,
            "verify_ssl": True,
            "follow_redirects": True,
        }
        
        guard_content = self.render_template("guard.py.j2", context)
        self.create_file(guard_file, guard_content)
        
        return {
            "guard_id": self.guard_id,
            "files_created": [str(guard_file)],
            "command": f"python {guard_file}",
            "next_steps": [
                f"1. Review guard configuration in .specify/guards/{self.guard_id}/guard.yaml",
                "2. Configure base_url and endpoints in guard.yaml",
                "3. Ensure httpx is installed: uv pip install httpx",
                f"4. Run the guard: specify guard run {self.guard_id}",
                f"5. View results: specify guard history {self.guard_id}",
            ]
        }
