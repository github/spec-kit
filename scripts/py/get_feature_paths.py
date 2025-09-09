#!/usr/bin/env python3
"""
Get paths for current feature branch without creating anything.
Python equivalent of get-feature-paths.sh for cross-platform compatibility.
Used by commands that need to find existing feature files.

Usage: python get_feature_paths.py [--json]
"""

import argparse
import json
import sys

# Import from common module
import sys
from pathlib import Path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from common import get_feature_paths, check_feature_branch


def main():
    parser = argparse.ArgumentParser(
        description="Get paths for current feature branch without creating anything"
    )
    parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    try:
        # Get all paths
        paths = get_feature_paths()
        current_branch = paths["CURRENT_BRANCH"]
        
        # Check if on feature branch
        if not check_feature_branch(current_branch):
            sys.exit(1)
        
        # Output paths (don't create anything)
        if args.json:
            print(json.dumps(paths))
        else:
            print(f"REPO_ROOT: {paths['REPO_ROOT']}")
            print(f"BRANCH: {current_branch}")
            print(f"FEATURE_DIR: {paths['FEATURE_DIR']}")
            print(f"FEATURE_SPEC: {paths['FEATURE_SPEC']}")
            print(f"IMPL_PLAN: {paths['IMPL_PLAN']}")
            print(f"TASKS: {paths['TASKS']}")
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()