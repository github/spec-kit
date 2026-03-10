#!/usr/bin/env python3
"""
Complete Global Memory Installation Script.

Handles platform detection, directory creation, template copying,
and component verification.
"""

import sys
import os
import platform
import subprocess
import shutil
import json
from pathlib import Path

# Add src to path
SCRIPT_DIR = Path(__file__).parent
SRC_DIR = SCRIPT_DIR.parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from specify_cli.memory.config import MemoryConfigManager
from specify_cli.memory.file_manager import FileMemoryManager
from specify_cli.memory.install.ollama_checker import OllamaChecker
from specify_cli.memory.install.degradation import DegradationConfig


def print_step(num, total, message):
    """Print installation step.

    Args:
        num: Step number
        total: Total steps
        message: Step message
    """
    print(f"[{num}/{total}] {message}")


def check_ollama() -> dict:
    """Check Ollama availability.

    Returns:
        Dict with availability info
    """
    checker = OllamaChecker()
    return checker.check_availability()


def create_directory_structure(global_home: Path) -> bool:
    """Create required directory structure.

    Args:
        global_home: Path to global claude home

    Returns:
        True if successful
    """
    directories = [
        global_home / "spec-kit" / "config",
        global_home / "spec-kit" / "templates",
        global_home / "memory" / "projects",
        global_home / "memory" / "backups",
    ]

    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")
            return False

    return True


def copy_templates(global_home: Path, repo_root: Path) -> bool:
    """Copy memory templates to global home.

    Args:
        global_home: Path to global claude home
        repo_root: Path to SpecKit repository root

    Returns:
        True if successful
    """
    templates_source = repo_root / "templates" / "memory"
    templates_dest = global_home / "spec-kit" / "templates" / "memory"

    if not templates_source.exists():
        print(f"Warning: Template source not found at {templates_source}")
        return True  # Not critical

    try:
        if templates_dest.exists():
            shutil.rmtree(templates_dest)

        shutil.copytree(templates_source, templates_dest)
        return True

    except Exception as e:
        print(f"Error copying templates: {e}")
        return False


def initialize_global_memory(global_home: Path) -> bool:
    """Initialize global memory files.

    Args:
        global_home: Path to global claude home

    Returns:
        True if successful
    """
    try:
        # Import and run init script
        init_script = SCRIPT_DIR / "init_memory.py"

        if not init_script.exists():
            print(f"Error: init_memory.py not found at {init_script}")
            return False

        result = subprocess.run(
            [sys.executable, str(init_script),
             "--project-id", ".global",
             "--project-name", "Global Memory",
             "--global-home", str(global_home)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Error initializing memory: {result.stderr}")
            return False

        return True

    except Exception as e:
        print(f"Error initializing memory: {e}")
        return False


def create_version_file(global_home: Path, version: str = "0.1.0") -> bool:
    """Create version file.

    Args:
        global_home: Path to global claude home
        version: Version string

    Returns:
        True if successful
    """
    version_file = global_home / "spec-kit" / "config" / ".version"

    try:
        version_file.parent.mkdir(parents=True, exist_ok=True)
        version_file.write_text(version)
        return True
    except Exception as e:
        print(f"Error creating version file: {e}")
        return False


def setup_degradation_config(global_home: Path) -> bool:
    """Setup graceful degradation configuration.

    Args:
        global_home: Path to global claude home

    Returns:
        True if successful
    """
    try:
        config_path = global_home / "spec-kit" / "config" / "degradation.json"
        degradation = DegradationConfig(config_path=config_path)

        # Config will be created with defaults if not exists
        return True

    except Exception as e:
        print(f"Error setting up degradation config: {e}")
        return False


def verify_installation(global_home: Path) -> bool:
    """Verify installation was successful.

    Args:
        global_home: Path to global claude home

    Returns:
        True if verification passes
    """
    required_items = [
        (global_home / "spec-kit" / "config", "Config directory"),
        (global_home / "spec-kit" / "templates", "Templates directory"),
        (global_home / "memory" / "projects", "Projects directory"),
        (global_home / "memory" / "backups", "Backups directory"),
        (global_home / "spec-kit" / "config" / ".version", "Version file"),
        (global_home / "memory" / "projects" / ".global", "Global memory"),
    ]

    all_passed = True

    for path, name in required_items:
        if path.exists():
            print(f"  [OK] {name}")
        else:
            print(f"  [MISSING] {name}: {path}")
            all_passed = False

    return all_passed


def main():
    """Main installation logic."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Install SpecKit Global Memory System"
    )

    parser.add_argument(
        "--global-home",
        type=str,
        default=None,
        help="Path to global claude home (default: ~/.claude)"
    )

    parser.add_argument(
        "--skip-ollama",
        action="store_true",
        help="Skip Ollama availability check"
    )

    parser.add_argument(
        "--version",
        type=str,
        default="0.1.0",
        help="Version to install (default: 0.1.0)"
    )

    args = parser.parse_args()

    # Detect platform
    system = platform.system()
    print(f"=== SpecKit Global Memory Installation ===")
    print(f"Platform: {system}")
    print()

    # Determine global home
    global_home = Path(args.global_home) if args.global_home else Path.home() / ".claude"
    print(f"Global Home: {global_home}")
    print()

    # Detect repo root
    repo_root = SCRIPT_DIR.parent.parent
    print(f"Repo Root: {repo_root}")
    print()

    total_steps = 7

    # Step 1: Create directory structure
    print_step(1, total_steps, "Creating directory structure...")
    if not create_directory_structure(global_home):
        print("Failed to create directory structure")
        return 1
    print("Directory structure created.")
    print()

    # Step 2: Copy templates
    print_step(2, total_steps, "Copying memory templates...")
    if not copy_templates(global_home, repo_root):
        print("Failed to copy templates")
        return 1
    print("Templates copied.")
    print()

    # Step 3: Setup degradation config
    print_step(3, total_steps, "Setting up degradation config...")
    if not setup_degradation_config(global_home):
        print("Failed to setup degradation config")
        return 1
    print("Degradation config created.")
    print()

    # Step 4: Initialize global memory
    print_step(4, total_steps, "Initializing global memory...")
    if not initialize_global_memory(global_home):
        print("Failed to initialize global memory")
        return 1
    print("Global memory initialized.")
    print()

    # Step 5: Check Ollama
    print_step(5, total_steps, "Checking Ollama availability...")
    if args.skip_ollama:
        print("Skipping Ollama check (--skip-ollama specified).")
    else:
        ollama_status = check_ollama()
        if ollama_status["available"]:
            print(f"Ollama detected: {ollama_status}")
        else:
            print("Note: Ollama not detected. Vector memory will be disabled.")
            print("To install Ollama: https://ollama.ai/download")
            print("To use vector memory, install Ollama and run: ollama pull mxbai-embed-large")
    print()

    # Step 6: Create version file
    print_step(6, total_steps, f"Creating version file ({args.version})...")
    if not create_version_file(global_home, args.version):
        print("Failed to create version file")
        return 1
    print(f"Version {args.version} installed.")
    print()

    # Step 7: Verify
    print_step(7, total_steps, "Verifying installation...")
    if not verify_installation(global_home):
        print()
        print("Installation verification failed!")
        return 1
    print()

    # Success
    print("=== Installation Complete ===")
    print()
    print(f"Memory location: {global_home / 'memory' / 'projects' / '.global'}")
    print(f"Config location: {global_home / 'spec-kit' / 'config'}")
    print()
    print("Next steps:")
    print("1. Initialize memory for your project:")
    print(f"   python {SCRIPT_DIR / 'init_memory.py'}")
    print("2. See documentation:")
    print(f"   {repo_root / 'docs' / 'INSTALL_MEMORY.md'}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
