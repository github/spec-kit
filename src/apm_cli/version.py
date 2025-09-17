"""Version management for APM CLI."""

import sys
from pathlib import Path

# Build-time version constant (will be injected during build)
# This avoids TOML parsing overhead during runtime
__BUILD_VERSION__ = None


def get_version() -> str:
    """
    Get the current version efficiently.
    
    First tries build-time constant, then falls back to pyproject.toml parsing.
    
    Returns:
        str: Version string
    """
    # Use build-time constant if available (fastest path)
    if __BUILD_VERSION__:
        return __BUILD_VERSION__
    
    # Fallback to reading from pyproject.toml (for development)
    try:
        # Handle PyInstaller bundle vs development
        if getattr(sys, 'frozen', False):
            # Running in PyInstaller bundle
            pyproject_path = Path(sys._MEIPASS) / 'pyproject.toml'
        else:
            # Running in development
            pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
            
        if pyproject_path.exists():
            # Simple regex parsing instead of full TOML library
            with open(pyproject_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for version = "x.y.z" pattern (including PEP 440 prereleases)
            import re
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                version = match.group(1)
                # Validate PEP 440 version patterns: x.y.z or x.y.z{a|b|rc}N
                if re.match(r'^\d+\.\d+\.\d+(a\d+|b\d+|rc\d+)?$', version):
                    return version
    except Exception:
        pass
    
    return "unknown"


# For backward compatibility
__version__ = get_version()
