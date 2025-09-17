"""Discovery functionality for primitive files."""

import os
import glob
from pathlib import Path
from typing import List, Dict

from .models import PrimitiveCollection
from .parser import parse_primitive_file
from ..models.apm_package import APMPackage


# Common primitive patterns for local discovery (with recursive search)
LOCAL_PRIMITIVE_PATTERNS: Dict[str, List[str]] = {
    'chatmode': [
        "**/.apm/chatmodes/*.chatmode.md",
        "**/.github/chatmodes/*.chatmode.md",
        "**/*.chatmode.md"  # Generic .chatmode.md files
    ],
    'instruction': [
        "**/.apm/instructions/*.instructions.md",
        "**/.github/instructions/*.instructions.md",
        "**/*.instructions.md"  # Generic .instructions.md files
    ],
    'context': [
        "**/.apm/context/*.context.md",
        "**/.apm/memory/*.memory.md",  # APM memory convention
        "**/.github/context/*.context.md",
        "**/.github/memory/*.memory.md",  # VSCode compatibility
        "**/*.context.md",  # Generic .context.md files
        "**/*.memory.md"  # Generic .memory.md files
    ]
}

# Dependency primitive patterns (for .apm directory within dependencies)
DEPENDENCY_PRIMITIVE_PATTERNS: Dict[str, List[str]] = {
    'chatmode': ["chatmodes/*.chatmode.md"],
    'instruction': ["instructions/*.instructions.md"],
    'context': [
        "context/*.context.md",
        "memory/*.memory.md"
    ]
}


def discover_primitives(base_dir: str = ".") -> PrimitiveCollection:
    """Find all APM primitive files in the project.
    
    Searches for .chatmode.md, .instructions.md, .context.md, and .memory.md files
    in both .apm/ and .github/ directory structures.
    
    Args:
        base_dir (str): Base directory to search in. Defaults to current directory.
    
    Returns:
        PrimitiveCollection: Collection of discovered and parsed primitives.
    """
    collection = PrimitiveCollection()
    
    # Find and parse files for each primitive type
    for primitive_type, patterns in LOCAL_PRIMITIVE_PATTERNS.items():
        files = find_primitive_files(base_dir, patterns)
        
        for file_path in files:
            try:
                primitive = parse_primitive_file(file_path, source="local")
                collection.add_primitive(primitive)
            except Exception as e:
                print(f"Warning: Failed to parse {file_path}: {e}")
    
    return collection


def discover_primitives_with_dependencies(base_dir: str = ".") -> PrimitiveCollection:
    """Enhanced primitive discovery including dependency sources.
    
    Priority Order:
    1. Local .apm/ (highest priority - always wins)
    2. Dependencies in declaration order (first declared wins)
    
    Args:
        base_dir (str): Base directory to search in. Defaults to current directory.
    
    Returns:
        PrimitiveCollection: Collection of discovered and parsed primitives with source tracking.
    """
    collection = PrimitiveCollection()
    
    # Phase 1: Local primitives (highest priority)
    scan_local_primitives(base_dir, collection)
    
    # Phase 2: Dependency primitives (lower priority, with conflict detection)
    scan_dependency_primitives(base_dir, collection)
    
    return collection


def scan_local_primitives(base_dir: str, collection: PrimitiveCollection) -> None:
    """Scan local .apm/ directory for primitives.
    
    Args:
        base_dir (str): Base directory to search in.
        collection (PrimitiveCollection): Collection to add primitives to.
    """
    # Find and parse files for each primitive type
    for primitive_type, patterns in LOCAL_PRIMITIVE_PATTERNS.items():
        files = find_primitive_files(base_dir, patterns)
        
        # Filter out files from apm_modules to avoid conflicts with dependency scanning
        local_files = []
        base_path = Path(base_dir)
        apm_modules_path = base_path / "apm_modules"
        
        for file_path in files:
            # Only include files that are NOT in apm_modules directory
            if not _is_under_directory(file_path, apm_modules_path):
                local_files.append(file_path)
        
        for file_path in local_files:
            try:
                primitive = parse_primitive_file(file_path, source="local")
                collection.add_primitive(primitive)
            except Exception as e:
                print(f"Warning: Failed to parse local primitive {file_path}: {e}")


def _is_under_directory(file_path: Path, directory: Path) -> bool:
    """Check if a file path is under a specific directory.
    
    Args:
        file_path (Path): Path to check.
        directory (Path): Directory to check against.
    
    Returns:
        bool: True if file_path is under directory, False otherwise.
    """
    try:
        file_path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def scan_dependency_primitives(base_dir: str, collection: PrimitiveCollection) -> None:
    """Scan all dependencies in apm_modules/ with priority handling.
    
    Args:
        base_dir (str): Base directory to search in.
        collection (PrimitiveCollection): Collection to add primitives to.
    """
    apm_modules_path = Path(base_dir) / "apm_modules"
    if not apm_modules_path.exists():
        return
    
    # Get dependency declaration order from apm.yml
    dependency_order = get_dependency_declaration_order(base_dir)
    
    # Process dependencies in declaration order
    for dep_name in dependency_order:
        # Handle org-namespaced structure (e.g., "github/design-guidelines")
        if "/" in dep_name:
            org_name, repo_name = dep_name.split("/", 1)
            dep_path = apm_modules_path / org_name / repo_name
        else:
            # Fallback for non-namespaced dependencies
            dep_path = apm_modules_path / dep_name
            
        if dep_path.exists() and dep_path.is_dir():
            scan_directory_with_source(dep_path, collection, source=f"dependency:{dep_name}")


def get_dependency_declaration_order(base_dir: str) -> List[str]:
    """Get APM dependency names in their declaration order from apm.yml.
    
    Args:
        base_dir (str): Base directory containing apm.yml.
    
    Returns:
        List[str]: List of dependency names in declaration order.
    """
    try:
        apm_yml_path = Path(base_dir) / "apm.yml"
        if not apm_yml_path.exists():
            return []
        
        package = APMPackage.from_apm_yml(apm_yml_path)
        apm_dependencies = package.get_apm_dependencies()
        
        # Extract package names from dependency references
        # Use alias if provided, otherwise use full org/repo path for org-namespaced structure
        dependency_names = []
        for dep in apm_dependencies:
            if dep.alias:
                dependency_names.append(dep.alias)
            else:
                # Use full org/repo path (e.g., "github/design-guidelines")
                # This matches our org-namespaced directory structure
                dependency_names.append(dep.repo_url)
        
        return dependency_names
        
    except Exception as e:
        print(f"Warning: Failed to parse dependency order from apm.yml: {e}")
        return []


def scan_directory_with_source(directory: Path, collection: PrimitiveCollection, source: str) -> None:
    """Scan a directory for primitives with a specific source tag.
    
    Args:
        directory (Path): Directory to scan (e.g., apm_modules/package_name).
        collection (PrimitiveCollection): Collection to add primitives to.
        source (str): Source identifier for discovered primitives.
    """
    # Look for .apm directory within the dependency
    apm_dir = directory / ".apm"
    if not apm_dir.exists():
        return
    
    # Find and parse files for each primitive type
    for primitive_type, patterns in DEPENDENCY_PRIMITIVE_PATTERNS.items():
        for pattern in patterns:
            full_pattern = str(apm_dir / pattern)
            matching_files = glob.glob(full_pattern, recursive=True)
            
            for file_path_str in matching_files:
                file_path = Path(file_path_str)
                if file_path.is_file() and _is_readable(file_path):
                    try:
                        primitive = parse_primitive_file(file_path, source=source)
                        collection.add_primitive(primitive)
                    except Exception as e:
                        print(f"Warning: Failed to parse dependency primitive {file_path}: {e}")


def find_primitive_files(base_dir: str, patterns: List[str]) -> List[Path]:
    """Find primitive files matching the given patterns.
    
    Args:
        base_dir (str): Base directory to search in.
        patterns (List[str]): List of glob patterns to match.
    
    Returns:
        List[Path]: List of unique file paths found.
    """
    if not os.path.isdir(base_dir):
        return []
    
    all_files = []
    
    for pattern in patterns:
        # Use glob to find files matching the pattern
        matching_files = glob.glob(os.path.join(base_dir, pattern), recursive=True)
        all_files.extend(matching_files)
    
    # Remove duplicates while preserving order and convert to Path objects
    seen = set()
    unique_files = []
    
    for file_path in all_files:
        abs_path = os.path.abspath(file_path)
        if abs_path not in seen:
            seen.add(abs_path)
            unique_files.append(Path(abs_path))
    
    # Filter out directories and ensure files are readable
    valid_files = []
    for file_path in unique_files:
        if file_path.is_file() and _is_readable(file_path):
            valid_files.append(file_path)
    
    return valid_files


def _is_readable(file_path: Path) -> bool:
    """Check if a file is readable.
    
    Args:
        file_path (Path): Path to check.
    
    Returns:
        bool: True if file is readable, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to read first few bytes to verify it's readable
            f.read(1)
        return True
    except (PermissionError, UnicodeDecodeError, OSError):
        return False


def _should_skip_directory(dir_path: str) -> bool:
    """Check if a directory should be skipped during scanning.
    
    Args:
        dir_path (str): Directory path to check.
    
    Returns:
        bool: True if directory should be skipped, False otherwise.
    """
    skip_patterns = {
        '.git',
        'node_modules',
        '__pycache__',
        '.pytest_cache',
        '.venv',
        'venv',
        '.tox',
        'build',
        'dist',
        '.mypy_cache'
    }
    
    dir_name = os.path.basename(dir_path)
    return dir_name in skip_patterns