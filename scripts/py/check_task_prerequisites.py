#!/usr/bin/env python3
"""
Check that implementation plan exists and find optional design documents.
Python equivalent of check-task-prerequisites.sh for cross-platform compatibility.

Usage: python check_task_prerequisites.py [--json]
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

from common import get_feature_paths, check_feature_branch, check_file, check_dir


def main():
    parser = argparse.ArgumentParser(
        description="Check that implementation plan exists and find optional design documents"
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
        
        # Check if feature directory exists
        feature_dir = Path(paths["FEATURE_DIR"])
        if not feature_dir.exists():
            print(f"ERROR: Feature directory not found: {feature_dir}")
            print("Run /specify first to create the feature structure.")
            sys.exit(1)
        
        # Check for implementation plan (required)
        impl_plan = Path(paths["IMPL_PLAN"])
        if not impl_plan.exists():
            print(f"ERROR: plan.md not found in {feature_dir}")
            print("Run /plan first to create the plan.")
            sys.exit(1)
        
        if args.json:
            # Build JSON array of available docs that actually exist
            docs = []
            if Path(paths["RESEARCH"]).exists():
                docs.append("research.md")
            if Path(paths["DATA_MODEL"]).exists():
                docs.append("data-model.md")
            
            contracts_dir = Path(paths["CONTRACTS_DIR"])
            if contracts_dir.exists() and any(contracts_dir.iterdir()):
                docs.append("contracts/")
            
            if Path(paths["QUICKSTART"]).exists():
                docs.append("quickstart.md")
            
            result = {
                "FEATURE_DIR": paths["FEATURE_DIR"],
                "AVAILABLE_DOCS": docs
            }
            print(json.dumps(result))
        else:
            # List available design documents (optional)
            print(f"FEATURE_DIR:{paths['FEATURE_DIR']}")
            print("AVAILABLE_DOCS:")
            
            # Use common check functions
            check_file(paths["RESEARCH"], "research.md")
            check_file(paths["DATA_MODEL"], "data-model.md")
            check_dir(paths["CONTRACTS_DIR"], "contracts/")
            check_file(paths["QUICKSTART"], "quickstart.md")
        
        # Always succeed - task generation should work with whatever docs are available
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()