#!/usr/bin/env python3
"""
Create a new feature with branch, directory structure, and template.
Python equivalent of create-new-feature.sh for cross-platform compatibility.

Usage: python create_new_feature.py "feature description" [--json]
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

from common import (
    get_repo_root, run_git_command, create_branch_name, 
    get_next_feature_number, copy_template
)


def main():
    parser = argparse.ArgumentParser(
        description="Create a new feature with branch, directory structure, and template"
    )
    parser.add_argument(
        "feature_description", 
        help="Description of the feature to create"
    )
    parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    if not args.feature_description.strip():
        print("ERROR: Feature description cannot be empty", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Get repository root
        repo_root = get_repo_root()
        specs_dir = repo_root / "specs"
        
        # Create specs directory if it doesn't exist
        specs_dir.mkdir(exist_ok=True)
        
        # Get next feature number
        feature_num = get_next_feature_number(specs_dir)
        
        # Create branch name from description
        words = create_branch_name(args.feature_description)
        
        # Final branch name
        branch_name = f"{feature_num}-{words}"
        
        # Create and switch to new branch
        run_git_command(["git", "checkout", "-b", branch_name])
        
        # Create feature directory
        feature_dir = specs_dir / branch_name
        feature_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy template if it exists
        template_path = repo_root / "templates" / "spec-template.md"
        spec_file = feature_dir / "spec.md"
        copy_template(template_path, spec_file)
        
        # Output results
        if args.json:
            result = {
                "BRANCH_NAME": branch_name,
                "SPEC_FILE": str(spec_file),
                "FEATURE_NUM": feature_num
            }
            print(json.dumps(result))
        else:
            # Output results for the LLM to use (legacy key: value format)
            print(f"BRANCH_NAME: {branch_name}")
            print(f"SPEC_FILE: {spec_file}")
            print(f"FEATURE_NUM: {feature_num}")
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()