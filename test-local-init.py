#!/usr/bin/env python3
"""
Test script to initialize a project with local template packages using monkey patching.
This bypasses the GitHub download and uses locally built ZIPs from .genreleases/.

Usage:
    uv run test-local-init.py <project-path> --ai <ai> --script <script> --version <version>

Example:
    # Build local packages first
    bash .github/workflows/scripts/create-release-packages.sh v0.0.70

    # Test with local packages
    uv run test-local-init.py /path/to/project --ai claude --script sh --version v0.0.70
"""

import sys
import specify_cli
from pathlib import Path

def create_local_download(version):
    """Create a mock download function that returns local ZIPs."""
    def local_download(ai_assistant, download_dir, **kwargs):
        script_type = kwargs.get('script_type', 'sh')
        local_zip = Path(__file__).parent / f".genreleases/spec-kit-template-{ai_assistant}-{script_type}-{version}.zip"

        if not local_zip.exists():
            raise FileNotFoundError(f"Local package not found: {local_zip}")

        return local_zip, {
            "filename": local_zip.name,
            "size": local_zip.stat().st_size,
            "release": version
        }
    return local_download

if __name__ == "__main__":
    # Extract mandatory --version from args
    if "--version" not in sys.argv:
        print("Error: --version is required")
        print("Usage: test-local-init.py <project> --ai <ai> --script <script> --version <version>")
        print("\nExample:")
        print("  uv run test-local-init.py /path/to/project --ai claude --script sh --version v0.0.70")
        sys.exit(1)

    idx = sys.argv.index("--version")
    version = sys.argv[idx + 1]
    sys.argv.pop(idx)  # Remove --version
    sys.argv.pop(idx)  # Remove value

    print(f"[test-local-init] Using local packages with version: {version}")

    # Monkey patch the download function
    specify_cli.download_template_from_github = create_local_download(version)

    # Run the real init command - it will use our local packages!
    specify_cli.main()
