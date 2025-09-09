"""
Cross-platform script execution utilities for spec-kit.
Handles execution of bash scripts on Unix and Python scripts on Windows.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union


def get_platform() -> str:
    """Get the current platform type."""
    return platform.system().lower()


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_platform() == "windows"


def find_script_path(script_name: str, repo_root: Path) -> Optional[Path]:
    """
    Find the appropriate script path based on platform.
    On Windows, prefer Python scripts. On Unix, prefer bash scripts.
    """
    scripts_dir = repo_root / "scripts"
    
    if is_windows():
        # On Windows, try Python script first, then bash (if available)
        py_script = scripts_dir / "py" / f"{script_name}.py"
        if py_script.exists():
            return py_script
        # Fallback to bash script if Python isn't available
        bash_script = scripts_dir / f"{script_name.replace('_', '-')}.sh"
        if bash_script.exists():
            return bash_script
    else:
        # On Unix, try bash script first, then Python as fallback
        bash_script = scripts_dir / f"{script_name.replace('_', '-')}.sh"
        if bash_script.exists():
            return bash_script
        # Fallback to Python script
        py_script = scripts_dir / "py" / f"{script_name}.py"
        if py_script.exists():
            return py_script
    
    return None


def run_script(
    script_name: str, 
    args: List[str] = None, 
    repo_root: Path = None,
    capture_output: bool = True,
    check: bool = True
) -> Union[subprocess.CompletedProcess, Dict]:
    """
    Run a script with cross-platform compatibility.
    
    Args:
        script_name: Name of the script (without extension)
        args: Arguments to pass to the script
        repo_root: Repository root path (auto-detected if None)
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise exception on non-zero exit
        
    Returns:
        CompletedProcess result or parsed dict for JSON output
    """
    if args is None:
        args = []
    
    if repo_root is None:
        # Try to find repo root
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, check=True
            )
            repo_root = Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            raise RuntimeError("Not in a git repository")
    
    script_path = find_script_path(script_name, repo_root)
    if not script_path:
        raise FileNotFoundError(f"Script '{script_name}' not found in {repo_root / 'scripts'}")
    
    # Build command based on script type
    if script_path.suffix == ".py":
        cmd = [sys.executable, str(script_path)] + args
    elif script_path.suffix == ".sh":
        cmd = ["bash", str(script_path)] + args
    else:
        raise RuntimeError(f"Unknown script type: {script_path}")
    
    # Run the command
    result = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=capture_output,
        text=True,
        check=check
    )
    
    # Try to parse JSON output if --json was in args
    if "--json" in args and capture_output and result.stdout:
        try:
            import json
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            # Not JSON, return as-is
            pass
    
    return result


def get_available_scripts(repo_root: Path = None) -> Dict[str, List[Path]]:
    """Get a list of available scripts and their paths."""
    if repo_root is None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, check=True
            )
            repo_root = Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            raise RuntimeError("Not in a git repository")
    
    scripts_dir = repo_root / "scripts"
    available = {}
    
    # Check bash scripts
    if scripts_dir.exists():
        for script in scripts_dir.glob("*.sh"):
            name = script.stem.replace("-", "_")
            if name not in available:
                available[name] = []
            available[name].append(script)
    
    # Check Python scripts
    py_dir = scripts_dir / "py"
    if py_dir.exists():
        for script in py_dir.glob("*.py"):
            if script.stem == "__init__":
                continue
            name = script.stem
            if name not in available:
                available[name] = []
            available[name].append(script)
    
    return available


def test_script_compatibility(repo_root: Path = None) -> Dict[str, bool]:
    """Test which scripts are available and working on current platform."""
    available = get_available_scripts(repo_root)
    results = {}
    
    for script_name in available:
        try:
            # Try to run the script with --help to test basic functionality
            result = run_script(script_name, ["--help"], repo_root, check=False)
            results[script_name] = result.returncode == 0
        except Exception:
            results[script_name] = False
    
    return results