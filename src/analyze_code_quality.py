#!/usr/bin/env python3
"""
Code quality analysis script for Bicep generator.

This script analyzes the codebase for type hints, docstrings, and error messages,
then generates a report with improvement suggestions.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from specify_cli.bicep.type_checker import (
    analyze_directory,
    display_code_quality_report,
    generate_improvement_suggestions,
    display_improvement_suggestions
)

def main():
    """Run code quality analysis."""
    # Analyze the bicep module
    bicep_dir = Path(__file__).parent.parent / "specify_cli" / "bicep"
    
    if not bicep_dir.exists():
        print(f"Error: Directory not found: {bicep_dir}")
        return 1
    
    print(f"Analyzing code in: {bicep_dir}\n")
    
    # Run analysis
    results = analyze_directory(bicep_dir)
    
    # Display report
    display_code_quality_report(results)
    
    # Generate and display suggestions
    suggestions = generate_improvement_suggestions(results)
    display_improvement_suggestions(suggestions)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
