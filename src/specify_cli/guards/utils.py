"""
Guard CLI Utilities

Helper functions for guard system operations.
"""

import json
from pathlib import Path
from typing import Any

import yaml


def generate_guard_id(existing_ids: list[str]) -> str:
    """
    Generate sequential guard ID.
    
    Args:
        existing_ids: List of existing guard IDs (e.g., ["G001", "G002"])
    
    Returns:
        Next sequential ID (e.g., "G003")
    """
    if not existing_ids:
        return "G001"
    
    # Extract numbers from existing IDs
    numbers = []
    for id_str in existing_ids:
        if id_str.startswith("G") and len(id_str) > 1:
            try:
                numbers.append(int(id_str[1:]))
            except ValueError:
                continue
    
    if not numbers:
        return "G001"
    
    next_num = max(numbers) + 1
    return f"G{next_num:03d}"


def generate_run_id(guard_id: str, existing_runs: list[str]) -> str:
    """
    Generate sequential run ID for a guard.
    
    Args:
        guard_id: Guard ID (e.g., "G007")
        existing_runs: List of existing run IDs (e.g., ["G007-R0001", "G007-R0002"])
    
    Returns:
        Next sequential run ID (e.g., "G007-R0003")
    """
    guard_runs = [r for r in existing_runs if r.startswith(f"{guard_id}-R")]
    
    if not guard_runs:
        return f"{guard_id}-R0001"
    
    # Extract run numbers
    numbers = []
    for run_id in guard_runs:
        try:
            run_part = run_id.split("-R")[1]
            numbers.append(int(run_part))
        except (IndexError, ValueError):
            continue
    
    if not numbers:
        return f"{guard_id}-R0001"
    
    next_num = max(numbers) + 1
    return f"{guard_id}-R{next_num:04d}"


def load_yaml(file_path: Path) -> dict[str, Any]:
    """
    Load YAML file.
    
    Args:
        file_path: Path to YAML file
    
    Returns:
        Parsed YAML content as dictionary
    
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def save_yaml(file_path: Path, data: dict[str, Any]) -> None:
    """
    Save dictionary to YAML file.
    
    Args:
        file_path: Path to YAML file
        data: Dictionary to save
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def load_json(file_path: Path) -> Any:
    """
    Load JSON file.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Parsed JSON content
    
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(file_path: Path, data: Any) -> None:
    """
    Save data to JSON file.
    
    Args:
        file_path: Path to JSON file
        data: Data to save (must be JSON-serializable)
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
