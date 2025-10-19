import fcntl
from pathlib import Path


def generate_id_with_lock(registry_path: Path) -> str:
    from specify_cli.guards.registry import GuardRegistry
    
    registry = GuardRegistry(registry_path)
    return registry.generate_id()


def update_makefile(makefile_path: Path, target_name: str, target_command: str) -> None:
    if not makefile_path.exists():
        makefile_path.write_text("")
    
    content = makefile_path.read_text()
    
    if target_name in content:
        return
    
    new_target = f"\n{target_name}:\n\t{target_command}\n"
    makefile_path.write_text(content + new_target)


def get_project_root() -> Path:
    current = Path.cwd()
    
    while current != current.parent:
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    
    return Path.cwd()
