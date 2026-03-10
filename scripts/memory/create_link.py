#!/usr/bin/env python3
"""
Cross-platform symlink creation utility.

Creates symlinks or junctions as appropriate for the platform.
"""

import sys
import os
import subprocess
from pathlib import Path


def create_cross_platform_link(
    source: Path,
    target: Path,
    force: bool = False
) -> bool:
    """Create a cross-platform symlink/junction.

    Args:
        source: Source directory (where SpecKit is)
        target: Target link path (where to create link)
        force: Remove existing link if present

    Returns:
        True if successful
    """
    source = Path(source).resolve()
    target = Path(target)

    # Remove existing if requested
    if force and target.exists() and (target.is_symlink() or target.is_dir()):
        if target.is_dir():
            if sys.platform == "win32":
                # Windows: remove junction
                subprocess.run(["rmdir", str(target)], shell=True)
            else:
                target.unlink()

    # Create based on platform
    if sys.platform == "win32":
        # Windows: Use junction (requires admin or SeCreateSymbolicLinkPrivilege)
        try:
            # Try CreateSymbolicLinkW (requires privileges)
            import ctypes
            ctypes.windll.kernel32.CreateSymbolicLinkW(
                str(source),
                str(target),
                None,
                1  # SYMBOLIC_LINK_FLAG
            )
            return True
        except (AttributeError, OSError):
            # Fallback to cmd.exe mklink (requires admin)
            try:
                subprocess.run([
                    "cmd", "/c",
                    f"mklink /D \"{source}\" \"{target}\""
                ], check=True, shell=True)
                return True
            except subprocess.CalledProcessError:
                return False
    else:
        # Unix: Use symlink
        target.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(source, target)
        return True


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: python create_link.py <source> <target> [--force]")
        sys.exit(1)

    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    force = "--force" in sys.argv[3:] if len(sys.argv) > 3 else False

    success = create_cross_platform_link(source, target, force)

    if success:
        print(f"Link created: {target} -> {source}")
        sys.exit(0)
    else:
        print(f"Failed to create link")
        sys.exit(1)


if __name__ == "__main__":
    main()
