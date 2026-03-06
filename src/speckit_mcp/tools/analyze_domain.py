#!/usr/bin/env python3
"""
MCP Tool: analyze-domain

Analyzes data files and extracts domain models to populate specification
templates with real business entities, rules, and integration points.
Supports interactive mode, setup wizard, and configuration management.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

def run_analyze_domain(
    data_dir: Optional[str] = None,
    interactive: bool = False,
    setup: bool = False,
    config_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run domain analysis with optional interactive mode and setup wizard.

    Args:
        data_dir: Directory containing data files to analyze
        interactive: Enable interactive mode for user validation
        setup: Run setup wizard to configure domain analysis
        config_file: Use saved configuration file

    Returns:
        Dict containing analysis results and status
    """

    # Get repository root and script paths
    repo_root = get_repo_root()
    script_path = repo_root / "scripts" / "bash" / "analyze-domain.sh"

    # Build command arguments
    cmd_args = []
    if interactive:
        cmd_args.append("--interactive")
    if setup:
        cmd_args.append("--setup")
    if config_file:
        cmd_args.append(f"--config={config_file}")
    if data_dir:
        cmd_args.append(f"--data-dir={data_dir}")

    # Add JSON flag for structured output
    cmd_args.append("--json")

    try:
        # Execute the shell script with JSON output
        cmd = [str(script_path)] + cmd_args
        result = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr or "Domain analysis script failed",
                "stdout": result.stdout
            }

        # Parse JSON output from script
        try:
            script_output = json.loads(result.stdout)
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw output
            return {
                "success": False,
                "error": "Failed to parse script output as JSON",
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        # If script indicates setup mode was used, integrate with Python setup wizard
        if setup and script_output.get("setup_mode"):
            return run_python_setup_wizard(data_dir, script_output)

        # If interactive mode was requested, run Python interactive analysis
        if interactive and script_output.get("interactive_mode"):
            return run_python_interactive_analysis(script_output, config_file)

        # For non-interactive mode, run Python domain analysis for template population
        if script_output.get("status") == "ready_for_analysis":
            return run_python_domain_analysis(script_output)

        return {
            "success": True,
            "script_output": script_output
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error running domain analysis: {str(e)}"
        }


def run_python_setup_wizard(data_dir: Optional[str], script_output: Dict[str, Any]) -> Dict[str, Any]:
    """Run Python setup wizard for domain configuration."""
    try:
        # Import Python modules
        sys.path.append(str(get_repo_root() / "src" / "specify_cli"))
        from domain_config import DomainConfigManager

        config_manager = DomainConfigManager()
        config = config_manager.run_setup_wizard()

        return {
            "success": True,
            "setup_complete": True,
            "config": config,
            "config_file": str(config_manager.config_file),
            "message": f"Configuration saved to {config_manager.config_file}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Setup wizard failed: {str(e)}"
        }


def run_python_interactive_analysis(script_output: Dict[str, Any], config_file: Optional[str]) -> Dict[str, Any]:
    """Run Python interactive domain analysis."""
    try:
        # Import Python modules
        sys.path.append(str(get_repo_root() / "src" / "specify_cli"))
        from interactive_domain_analysis import InteractiveDomainAnalyzer

        data_dir = script_output.get("DATA_DIR")
        if not data_dir:
            return {
                "success": False,
                "error": "No data directory found in script output"
            }

        analyzer = InteractiveDomainAnalyzer(
            data_dir,
            interactive_mode=True,
            config_file=config_file
        )

        domain_model = analyzer.analyze()

        return {
            "success": True,
            "interactive_complete": True,
            "domain_analysis": {
                "entities": len(domain_model.entities),
                "business_rules": len(domain_model.business_rules),
                "integration_points": len(domain_model.integration_points)
            },
            "spec_file": script_output.get("SPEC_FILE"),
            "ready_for_template_population": True
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Interactive analysis failed: {str(e)}"
        }


def run_python_domain_analysis(script_output: Dict[str, Any]) -> Dict[str, Any]:
    """Run Python domain analysis and template population."""
    try:
        # Import Python modules
        sys.path.append(str(get_repo_root() / "src" / "specify_cli"))
        from domain_analysis import DomainAnalyzer
        from template_populator import TemplatePopulator

        data_dir = script_output.get("DATA_DIR")
        spec_file = script_output.get("SPEC_FILE")

        if not data_dir or not spec_file:
            return {
                "success": False,
                "error": "Missing data directory or spec file in script output"
            }

        # Step 1: Run domain analysis
        analyzer = DomainAnalyzer(data_dir)
        domain_model = analyzer.analyze()

        # Step 2: Populate template with extracted domain content
        populator = TemplatePopulator(spec_file, domain_model)
        populated_spec = populator.populate_specification()

        return {
            "success": True,
            "analysis_complete": True,
            "domain_analysis": {
                "entities_discovered": len(domain_model.entities),
                "business_rules_extracted": len(domain_model.business_rules),
                "integration_points_identified": len(domain_model.integration_points)
            },
            "template_populated": True,
            "spec_file": spec_file,
            "entities": [entity.name for entity in domain_model.entities],
            "message": f"Domain analysis complete. Specification file updated: {spec_file}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Domain analysis failed: {str(e)}"
        }


def get_repo_root() -> Path:
    """Get repository root directory."""
    try:
        # Try git first
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        # Fall back to searching for .git or .specify
        current = Path.cwd()
        while current.parent != current:
            if (current / ".git").exists() or (current / ".specify").exists():
                return current
            current = current.parent
        return Path.cwd()


def main():
    """Command-line interface for MCP analyze-domain tool."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP analyze-domain tool")
    parser.add_argument("--data-dir", help="Directory containing data files")
    parser.add_argument("--interactive", action="store_true", help="Enable interactive mode")
    parser.add_argument("--setup", action="store_true", help="Run setup wizard")
    parser.add_argument("--config", help="Configuration file path")

    args = parser.parse_args()

    result = run_analyze_domain(
        data_dir=args.data_dir,
        interactive=args.interactive,
        setup=args.setup,
        config_file=args.config
    )

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()