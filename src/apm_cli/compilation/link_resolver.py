"""Markdown link resolution for AGENTS.md compilation."""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional


def resolve_markdown_links(content: str, base_path: Path) -> str:
    """Resolve markdown links and inline referenced content.
    
    Args:
        content (str): Content with markdown links to resolve.
        base_path (Path): Base directory for resolving relative paths.
    
    Returns:
        str: Content with resolved links and inlined content where appropriate.
    """
    # Pattern to match markdown links: [text](path)
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    def replace_link(match):
        text = match.group(1)
        path = match.group(2)
        
        # Skip external URLs
        if path.startswith(('http://', 'https://', 'ftp://', 'mailto:')):
            return match.group(0)  # Return original link
        
        # Skip anchors
        if path.startswith('#'):
            return match.group(0)  # Return original link
        
        # Resolve relative path
        full_path = _resolve_path(path, base_path)
        
        if full_path and full_path.exists() and full_path.is_file():
            # For certain file types, inline the content
            if full_path.suffix.lower() in ['.md', '.txt']:
                try:
                    file_content = full_path.read_text(encoding='utf-8')
                    # Remove frontmatter if present
                    file_content = _remove_frontmatter(file_content)
                    return f"**{text}**:\n\n{file_content}"
                except (OSError, UnicodeDecodeError):
                    # Fall back to original link if file can't be read
                    return match.group(0)
            else:
                # For other file types, keep the link but update path if needed
                return match.group(0)
        else:
            # File doesn't exist, keep original link (will be caught by validation)
            return match.group(0)
    
    return re.sub(link_pattern, replace_link, content)





def validate_link_targets(content: str, base_path: Path) -> List[str]:
    """Validate that all referenced files exist.
    
    Args:
        content (str): Content to validate links in.
        base_path (Path): Base directory for resolving relative paths.
    
    Returns:
        List[str]: List of error messages for missing or invalid links.
    """
    errors = []
    
    # Check markdown links
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(link_pattern, content):
        text = match.group(1)
        path = match.group(2)
        
        # Skip external URLs and anchors
        if (path.startswith(('http://', 'https://', 'ftp://', 'mailto:')) or 
            path.startswith('#')):
            continue
        
        # Resolve and check path
        full_path = _resolve_path(path, base_path)
        if not full_path or not full_path.exists():
            errors.append(f"Referenced file not found: {path} (in link '{text}')")
        elif not full_path.is_file() and not full_path.is_dir():
            errors.append(f"Referenced path is neither a file nor directory: {path} (in link '{text}')")
    
    return errors


def _resolve_path(path: str, base_path: Path) -> Optional[Path]:
    """Resolve a relative path against a base path.
    
    Args:
        path (str): Relative path to resolve.
        base_path (Path): Base directory for resolution.
    
    Returns:
        Optional[Path]: Resolved path or None if invalid.
    """
    try:
        if Path(path).is_absolute():
            return Path(path)
        else:
            return base_path / path
    except (OSError, ValueError):
        return None


def _remove_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from content.
    
    Args:
        content (str): Content that may contain frontmatter.
    
    Returns:
        str: Content without frontmatter.
    """
    # Remove YAML frontmatter (--- at start, --- at end)
    if content.startswith('---\n'):
        lines = content.split('\n')
        in_frontmatter = True
        content_lines = []
        
        for i, line in enumerate(lines[1:], 1):  # Skip first ---
            if line.strip() == '---' and in_frontmatter:
                in_frontmatter = False
                continue
            if not in_frontmatter:
                content_lines.append(line)
        
        content = '\n'.join(content_lines)
    
    return content.strip()


def _detect_circular_references(content: str, base_path: Path, visited: Optional[set] = None) -> List[str]:
    """Detect circular references in markdown links.
    
    Args:
        content (str): Content to check for circular references.
        base_path (Path): Base directory for resolving paths.
        visited (Optional[set]): Set of already visited files.
    
    Returns:
        List[str]: List of circular reference errors.
    """
    if visited is None:
        visited = set()
    
    errors = []
    current_file = base_path
    
    if current_file in visited:
        errors.append(f"Circular reference detected: {current_file}")
        return errors
    
    visited.add(current_file)
    
    # Check markdown links for potential circular references
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(link_pattern, content):
        path = match.group(2)
        
        # Skip external URLs and anchors
        if (path.startswith(('http://', 'https://', 'ftp://', 'mailto:')) or 
            path.startswith('#')):
            continue
        
        full_path = _resolve_path(path, base_path.parent if base_path.is_file() else base_path)
        if full_path and full_path.exists() and full_path.is_file():
            if full_path.suffix.lower() in ['.md', '.txt']:
                try:
                    linked_content = full_path.read_text(encoding='utf-8')
                    errors.extend(_detect_circular_references(linked_content, full_path, visited.copy()))
                except (OSError, UnicodeDecodeError):
                    continue
    
    return errors