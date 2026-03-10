#!/usr/bin/env python3
"""
Verification script for SpecKit Global Memory installation.
Checks that all components are properly installed.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def check_item(condition, description):
    """Check and display item status.

    Args:
        condition: Boolean condition
        description: Item description

    Returns:
        True if passed
    """
    if condition:
        print(f"[PASS] {description}")
        return True
    else:
        print(f"[FAIL] {description}")
        return False


def main():
    """Main verification logic."""
    print("=== SpecKit Global Memory Installation Verification ===")
    print()

    global_home = Path.home() / ".claude"
    checks_passed = 0
    checks_total = 0

    # 1. Global home directory
    checks_total += 1
    if check_item(global_home.exists(), f"Global home exists: {global_home}"):
        checks_passed += 1

    # 2. SpecKit directories
    checks_total += 1
    if check_item((global_home / "spec-kit").exists(), "SpecKit directory exists"):
        checks_passed += 1

    checks_total += 1
    if check_item((global_home / "spec-kit" / "config").exists(), "Config directory exists"):
        checks_passed += 1

    checks_total += 1
    if check_item((global_home / "spec-kit" / "templates").exists(), "Templates directory exists"):
        checks_passed += 1

    # 3. Memory directories
    checks_total += 1
    if check_item((global_home / "memory" / "projects").exists(), "Memory projects directory exists"):
        checks_passed += 1

    checks_total += 1
    if check_item((global_home / "memory" / "backups").exists(), "Memory backups directory exists"):
        checks_passed += 1

    # 4. Global memory files
    checks_total += 1
    if check_item((global_home / "memory" / "projects" / ".global" / "lessons.md").exists(),
                   "Global lessons.md exists"):
        checks_passed += 1

    checks_total += 1
    if check_item((global_home / "memory" / "projects" / ".global" / "patterns.md").exists(),
                   "Global patterns.md exists"):
        checks_passed += 1

    checks_total += 1
    if check_item((global_home / "memory" / "projects" / ".global" / "architecture.md").exists(),
                   "Global architecture.md exists"):
        checks_passed += 1

    # 5. Version file
    checks_total += 1
    version_file = global_home / "spec-kit" / "config" / ".version"
    if version_file.exists():
        version = version_file.read_text().strip()
        if check_item(True, f"Version file exists: {version}"):
            checks_passed += 1
    else:
        check_item(False, "Version file exists")
        checks_total += 1

    # 6. Module imports
    checks_total += 1
    try:
        from specify_cli.memory.config import MemoryConfigManager
        from specify_cli.memory.file_manager import FileMemoryManager
        from specify_cli.memory.project_detector import ProjectDetector
        if check_item(True, "Memory modules importable"):
            checks_passed += 1
    except ImportError as e:
        check_item(False, f"Memory modules importable: {e}")
        checks_total += 1

    # Summary
    print()
    print("=== Verification Summary ===")
    print(f"Passed: {checks_passed}/{checks_total} checks")

    if checks_passed == checks_total:
        print("Installation verified successfully!")
        return 0
    else:
        print("Some checks failed. See details above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
