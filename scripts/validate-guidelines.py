#!/usr/bin/env python3
"""
Guideline Validation Tool

Validates corporate guideline files and configurations for:
- JSON schema compliance
- File existence
- Path pattern validity
- Version consistency
- Required sections in guideline markdown files
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import re


class GuidelineValidator:
    """Validates corporate guidelines structure and content."""

    def __init__(self, guidelines_dir: Path):
        self.guidelines_dir = guidelines_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.success_count = 0

    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 Validating Corporate Guidelines...\n")

        # Check if guidelines directory exists
        if not self.guidelines_dir.exists():
            self.errors.append(f"Guidelines directory not found: {self.guidelines_dir}")
            return False

        # Validate configuration files
        self.validate_branch_config()
        self.validate_stack_mapping()

        # Validate guideline markdown files
        self.validate_guideline_files()

        # Print results
        self.print_results()

        return len(self.errors) == 0

    def validate_branch_config(self) -> None:
        """Validate branch-config.json."""
        config_file = self.guidelines_dir / "branch-config.json"

        if not config_file.exists():
            self.warnings.append("branch-config.json not found (optional)")
            return

        try:
            with open(config_file) as f:
                config = json.load(f)

            # Check required fields
            required_fields = ["version", "branch_pattern", "jira"]
            for field in required_fields:
                if field not in config:
                    self.errors.append(f"branch-config.json: Missing required field '{field}'")
                else:
                    self.success_count += 1

            # Validate jira regex if present
            if "jira" in config and "regex" in config["jira"]:
                try:
                    re.compile(config["jira"]["regex"])
                    self.success_count += 1
                except re.error as e:
                    self.errors.append(f"branch-config.json: Invalid jira regex: {e}")

        except json.JSONDecodeError as e:
            self.errors.append(f"branch-config.json: Invalid JSON: {e}")
        except Exception as e:
            self.errors.append(f"branch-config.json: Error reading file: {e}")

    def validate_stack_mapping(self) -> None:
        """Validate stack-mapping.json."""
        config_file = self.guidelines_dir / "stack-mapping.json"

        if not config_file.exists():
            self.warnings.append("stack-mapping.json not found (optional for single-stack)")
            return

        try:
            with open(config_file) as f:
                config = json.load(f)

            # Check required fields
            if "version" not in config:
                self.errors.append("stack-mapping.json: Missing 'version' field")
            else:
                self.success_count += 1

            if "stacks" not in config:
                self.errors.append("stack-mapping.json: Missing 'stacks' array")
                return

            # Validate each stack configuration
            for i, stack in enumerate(config["stacks"]):
                self.validate_stack_entry(stack, i)

            # Validate precedence rules
            if "precedence_rules" in config:
                self.success_count += 1
            else:
                self.warnings.append("stack-mapping.json: No precedence_rules defined")

        except json.JSONDecodeError as e:
            self.errors.append(f"stack-mapping.json: Invalid JSON: {e}")
        except Exception as e:
            self.errors.append(f"stack-mapping.json: Error reading file: {e}")

    def validate_stack_entry(self, stack: Dict, index: int) -> None:
        """Validate a single stack entry in stack-mapping.json."""
        required = ["name", "guideline", "paths"]

        for field in required:
            if field not in stack:
                self.errors.append(
                    f"stack-mapping.json: Stack #{index} missing required field '{field}'"
                )
                return

        # Check if guideline file exists
        guideline_file = self.guidelines_dir / stack["guideline"]
        if not guideline_file.exists():
            self.errors.append(
                f"stack-mapping.json: Stack '{stack['name']}' references "
                f"non-existent guideline: {stack['guideline']}"
            )
        else:
            self.success_count += 1

        # Validate path patterns
        if "paths" in stack and isinstance(stack["paths"], list):
            for path in stack["paths"]:
                if not isinstance(path, str):
                    self.errors.append(
                        f"stack-mapping.json: Stack '{stack['name']}' has invalid path: {path}"
                    )
            self.success_count += 1

        # Validate priority
        if "priority" in stack:
            if not isinstance(stack["priority"], (int, float)):
                self.errors.append(
                    f"stack-mapping.json: Stack '{stack['name']}' has invalid priority"
                )
            else:
                self.success_count += 1

    def validate_guideline_files(self) -> None:
        """Validate guideline markdown files."""
        guideline_files = [
            "reactjs-guidelines.md",
            "java-guidelines.md",
            "dotnet-guidelines.md",
            "nodejs-guidelines.md",
            "python-guidelines.md",
        ]

        for filename in guideline_files:
            filepath = self.guidelines_dir / filename
            if filepath.exists():
                self.validate_guideline_structure(filepath)
            else:
                # Not an error - guidelines are optional based on tech stack
                pass

    def validate_guideline_structure(self, filepath: Path) -> None:
        """Validate structure of a guideline markdown file."""
        try:
            with open(filepath) as f:
                content = f.read()

            # Check for required sections (recommended but not enforced)
            recommended_sections = [
                "Scaffolding",
                "Package Registry",
                "Mandatory Libraries",
                "Architecture",
                "Security",
            ]

            found_sections = []
            for section in recommended_sections:
                # Look for markdown headers with these names
                if re.search(rf"^#+ {section}", content, re.MULTILINE | re.IGNORECASE):
                    found_sections.append(section)

            if len(found_sections) >= 3:
                self.success_count += 1
            else:
                self.warnings.append(
                    f"{filepath.name}: Consider adding recommended sections: "
                    f"{', '.join(set(recommended_sections) - set(found_sections))}"
                )

            # Check for version metadata (optional)
            if re.search(r"^---\s*\nversion:", content, re.MULTILINE):
                self.success_count += 1
            else:
                self.warnings.append(f"{filepath.name}: No version metadata found (optional)")

        except Exception as e:
            self.errors.append(f"{filepath.name}: Error reading file: {e}")

    def print_results(self) -> None:
        """Print validation results."""
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60 + "\n")

        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):\n")
            for error in self.errors:
                print(f"  • {error}")
            print()

        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):\n")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()

        print(f"✅ PASSED CHECKS: {self.success_count}\n")

        if not self.errors and not self.warnings:
            print("🎉 All guidelines are valid!\n")
        elif not self.errors:
            print("✓ Validation passed with warnings (non-blocking)\n")
        else:
            print("✗ Validation failed - please fix errors above\n")


def main():
    """Main entry point."""
    # Determine guidelines directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    guidelines_dir = repo_root / ".guidelines"

    # Allow custom path as argument
    if len(sys.argv) > 1:
        guidelines_dir = Path(sys.argv[1])

    validator = GuidelineValidator(guidelines_dir)
    success = validator.validate_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
