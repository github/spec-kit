#!/usr/bin/env python3
"""
Memory initialization script.

Initializes global memory system for a project.
Usage: python scripts/memory/init_memory.py [--project-id ID]
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from specify_cli.memory.project_detector import ProjectDetector
from specify_cli.memory.file_manager import FileMemoryManager
from specify_cli.memory.config import MemoryConfigManager


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize global memory for a project"
    )

    parser.add_argument(
        "--project-id",
        type=str,
        default=None,
        help="Project ID (auto-detected if not provided)"
    )

    parser.add_argument(
        "--project-name",
        type=str,
        default=None,
        help="Project name (auto-detected if not provided)"
    )

    parser.add_argument(
        "--global-home",
        type=str,
        default=None,
        help="Path to global claude home (default: ~/.claude)"
    )

    args = parser.parse_args()

    # Determine global home
    global_home = Path(args.global_home) if args.global_home else Path.home() / ".claude"

    print(f"Global home: {global_home}")

    # Detect or use provided project ID
    if args.project_id:
        project_id = args.project_id
        project_name = args.project_name or args.project_id
    else:
        detector = ProjectDetector(global_home=global_home)
        project_info = detector.detect_current_project()

        project_id = project_info["project_id"]
        project_name = project_info["project_name"]

    print(f"Project ID: {project_id}")
    print(f"Project name: {project_name}")

    # Initialize memory structure
    detector = ProjectDetector(global_home=global_home)
    memory_path = Path(global_home) / "memory" / "projects" / project_id

    success = detector.ensure_project_memory_structure(project_id, memory_path)

    if not success:
        print("Error: Failed to create memory structure")
        sys.exit(1)

    # Initialize memory files
    file_manager = FileMemoryManager(global_home=global_home)

    # For global project, create templates
    if project_id == ".global":
        success = file_manager.initialize_memory_files(template_dir=None)
    else:
        # For project-specific, initialize empty files
        success = file_manager.initialize_memory_files(
            project_id=project_id,
            template_dir=None
        )

    if not success:
        print("Error: Failed to initialize memory files")
        sys.exit(1)

    # Create project config
    config_manager = MemoryConfigManager(global_home=global_home)

    config_data = {
        "project_id": project_id,
        "project_name": project_name,
        "memory_enabled": True,
        "memory_config": {
            "auto_save": True,
            "vector_memory": False,
            "skillsmp_search": True,
            "context_optimization": True
        }
    }

    config_path = memory_path / ".spec-kit" / "project.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)

    print(f"Memory initialized at: {memory_path}")
    print(f"Config file: {config_path}")
    print("\nMemory files created:")
    print(f"  - lessons.md")
    print(f"  - patterns.md")
    print(f"  - architecture.md")
    print(f"  - projects-log.md")
    print(f"  - handoff.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
