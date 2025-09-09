#!/usr/bin/env python3
"""
Setup implementation plan structure for current branch.
Python equivalent of setup-plan.sh for cross-platform compatibility.

Usage: python setup_plan.py [--json]
"""

import argparse
import json
import sys
from pathlib import Path

# Import from common module
import sys
from pathlib import Path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from common import get_feature_paths, check_feature_branch, copy_template


def main():
    parser = argparse.ArgumentParser(
        description="Setup implementation plan structure for current branch"
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
        
        # Create feature directory if it doesn't exist
        feature_dir = Path(paths["FEATURE_DIR"])
        feature_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy plan template if it exists
        repo_root = Path(paths["REPO_ROOT"])
        template_path = repo_root / "templates" / "plan-template.md"
        plan_file = Path(paths["IMPL_PLAN"])
        copy_template(template_path, plan_file)
        
        # Output results
        if args.json:
            result = {
                "FEATURE_SPEC": paths["FEATURE_SPEC"],
                "IMPL_PLAN": paths["IMPL_PLAN"],
                "SPECS_DIR": paths["FEATURE_DIR"],
                "BRANCH": current_branch
            }
            print(json.dumps(result))
        else:
            # Output all paths for LLM use
            print(f"FEATURE_SPEC: {paths['FEATURE_SPEC']}")
            print(f"IMPL_PLAN: {paths['IMPL_PLAN']}")
            print(f"SPECS_DIR: {paths['FEATURE_DIR']}")
            print(f"BRANCH: {current_branch}")
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()