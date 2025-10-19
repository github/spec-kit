from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any
from jinja2 import Environment, FileSystemLoader


class GuardScaffolder(ABC):
    
    def __init__(self, guard_id: str, name: str, guard_type: str, project_root: Path):
        self.guard_id = guard_id
        self.name = name
        self.guard_type = guard_type
        self.project_root = project_root
        self.templates_dir = project_root / ".specify" / "guards" / "types" / guard_type / "templates"
    
    @abstractmethod
    def scaffold(self) -> Dict[str, Any]:
        pass
    
    def render_template(self, template_name: str, context: Dict) -> str:
        env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        template = env.get_template(template_name)
        return template.render(**context)
    
    def create_file(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    
    def update_makefile(self, target_name: str, target_command: str) -> None:
        makefile_path = self.project_root / "Makefile"
        
        if not makefile_path.exists():
            makefile_path.write_text("")
        
        content = makefile_path.read_text()
        
        if target_name in content:
            return
        
        new_target = f"\n{target_name}:\n\t{target_command}\n"
        makefile_path.write_text(content + new_target)
