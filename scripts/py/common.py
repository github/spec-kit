#!/usr/bin/env python3
"""
Common functions and utilities for spec-kit scripts.
Python equivalent of common.sh for cross-platform compatibility.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


def run_git_command(cmd: list, cwd: Optional[Path] = None) -> str:
    """Run a git command and return the output."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{e.stderr}")


def get_repo_root() -> Path:
    """Get repository root directory."""
    output = run_git_command(["git", "rev-parse", "--show-toplevel"])
    return Path(output)


def get_current_branch() -> str:
    """Get current branch name."""
    return run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def check_feature_branch(branch: str) -> bool:
    """
    Check if current branch is a feature branch.
    Returns True if valid, False if not.
    Feature branches should be named like: 001-feature-name
    """
    pattern = r"^[0-9]{3}-"
    if not re.match(pattern, branch):
        print(f"ERROR: Not on a feature branch. Current branch: {branch}")
        print("Feature branches should be named like: 001-feature-name")
        return False
    return True


def get_feature_dir(repo_root: Path, branch: str) -> Path:
    """Get feature directory path."""
    return repo_root / "specs" / branch


def get_feature_paths() -> Dict[str, str]:
    """
    Get all standard paths for a feature.
    Returns a dictionary with all the paths.
    """
    repo_root = get_repo_root()
    current_branch = get_current_branch()
    feature_dir = get_feature_dir(repo_root, current_branch)
    
    return {
        "REPO_ROOT": str(repo_root),
        "CURRENT_BRANCH": current_branch,
        "FEATURE_DIR": str(feature_dir),
        "FEATURE_SPEC": str(feature_dir / "spec.md"),
        "IMPL_PLAN": str(feature_dir / "plan.md"),
        "TASKS": str(feature_dir / "tasks.md"),
        "RESEARCH": str(feature_dir / "research.md"),
        "DATA_MODEL": str(feature_dir / "data-model.md"),
        "QUICKSTART": str(feature_dir / "quickstart.md"),
        "CONTRACTS_DIR": str(feature_dir / "contracts"),
    }


def check_file(file_path: str, description: str) -> bool:
    """Check if a file exists and report."""
    path = Path(file_path)
    if path.is_file():
        print(f"  ✓ {description}")
        return True
    else:
        print(f"  ✗ {description}")
        return False


def check_dir(dir_path: str, description: str) -> bool:
    """Check if a directory exists and has files."""
    path = Path(dir_path)
    if path.is_dir() and any(path.iterdir()):
        print(f"  ✓ {description}")
        return True
    else:
        print(f"  ✗ {description}")
        return False


def create_branch_name(description: str) -> str:
    """Create a branch name from a description."""
    # Convert to lowercase and replace non-alphanumeric with hyphens
    branch_name = re.sub(r"[^a-z0-9]", "-", description.lower())
    # Remove multiple consecutive hyphens
    branch_name = re.sub(r"-+", "-", branch_name)
    # Remove leading/trailing hyphens
    branch_name = branch_name.strip("-")
    
    # Extract 2-3 meaningful words
    words = [w for w in branch_name.split("-") if w]
    return "-".join(words[:3])


def get_next_feature_number(specs_dir: Path) -> str:
    """Get the next feature number with zero padding."""
    highest = 0
    if specs_dir.exists():
        for item in specs_dir.iterdir():
            if item.is_dir():
                match = re.match(r"^(\d+)-", item.name)
                if match:
                    number = int(match.group(1))
                    if number > highest:
                        highest = number
    
    next_num = highest + 1
    return f"{next_num:03d}"


def copy_template(template_path: Path, destination: Path) -> bool:
    """Copy template file if it exists."""
    if template_path.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(template_path, 'r', encoding='utf-8') as src:
            content = src.read()
        with open(destination, 'w', encoding='utf-8') as dst:
            dst.write(content)
        return True
    else:
        print(f"Warning: Template not found at {template_path}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.touch()
        return False