"""Scaffolder for ui-playwright guard type"""
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from specify_cli.guards.scaffolder import BaseScaffolder


class UiPlaywrightScaffolder(BaseScaffolder):
    """Scaffolder for ui-playwright guard type."""
    
    def scaffold(self) -> Dict[str, Any]:
        guard_file = self.project_root / ".specify" / "guards" / self.guard_id / f"{self.guard_id}.py"
        
        context = {
            "guard_id": self.guard_id,
            "name": self.name,
            "description": f"UI E2E testing with Playwright for {self.name}",
            "browser": "chromium",
            "headless": True,
            "test_paths": ["tests/ui/"],
            "screenshots_on_failure": True,
            "timeout": 30000,
        }
        
        guard_content = self.render_template("guard.py.j2", context)
        self.create_file(guard_file, guard_content)
        
        return {
            "guard_id": self.guard_id,
            "files_created": [str(guard_file)],
            "command": f"python {guard_file}",
            "next_steps": [
                f"1. Review guard configuration in .specify/guards/{self.guard_id}/guard.yaml",
                "2. Ensure Playwright is installed: uvx playwright install chromium",
                "3. Create test files in: tests/ui/",
                f"4. Run the guard: specify guard run {self.guard_id}",
                f"5. View results: specify guard history {self.guard_id}",
            ]
        }
