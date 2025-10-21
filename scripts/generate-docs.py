#!/usr/bin/env python3
"""
Documentation Generator for Spec Kit

Automatically generates and syncs documentation from AGENT_CONFIG in __init__.py.
This ensures documentation stays in sync with code.

Usage:
    python scripts/generate-docs.py --check    # Check if docs are in sync
    python scripts/generate-docs.py --update   # Update documentation files
    python scripts/generate-docs.py --format markdown  # Generate markdown table
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple
import ast


def set_utf8_output():
    """Set UTF-8 encoding for stdout/stderr on Windows."""
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def load_agent_config():
    """Load AGENT_CONFIG from __init__.py without importing dependencies."""
    init_file = Path(__file__).parent.parent / "src" / "specify_cli" / "__init__.py"
    
    if not init_file.exists():
        raise FileNotFoundError(f"Cannot find {init_file}")
    
    # Parse AGENT_CONFIG using AST for security
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'AGENT_CONFIG':
                    if isinstance(node.value, ast.Dict):
                        # Safely evaluate the dictionary using ast.literal_eval
                        return ast.literal_eval(node.value)
    
    raise ValueError("Could not find AGENT_CONFIG in __init__.py")


AGENT_CONFIG = load_agent_config()

class DocGenerator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.readme_path = repo_root / "README.md"
        self.agents_md_path = repo_root / "AGENTS.md"
        
    def generate_agent_table_markdown(self) -> str:
        """Generate markdown table of supported agents"""
        lines = []
        lines.append("## 🤖 Supported AI Agents")
        lines.append("")
        lines.append("Spec Kit supports the following AI coding assistants:")
        lines.append("")
        lines.append("| Agent | CLI Tool | Type | Installation |")
        lines.append("|-------|----------|------|--------------|")
        
        for agent_key, config in AGENT_CONFIG.items():
            name = config["name"]
            cli_tool = f"`{agent_key}`" if config["requires_cli"] else "N/A (IDE-based)"
            agent_type = "CLI" if config["requires_cli"] else "IDE"
            
            if config["install_url"]:
                install = f"[Install Guide]({config['install_url']})"
            else:
                install = "Built-in IDE"
            
            lines.append(f"| **{name}** | {cli_tool} | {agent_type} | {install} |")
        
        lines.append("")
        lines.append(f"**Total Supported Agents:** {len(AGENT_CONFIG)}")
        lines.append("")
        
        return "\n".join(lines)
    
    def generate_cli_help_text(self) -> str:
        """Generate CLI help text for --ai parameter"""
        agent_list = ", ".join(AGENT_CONFIG.keys())
        return f"AI assistant to use: {agent_list}"
    
    def generate_agents_list(self) -> List[str]:
        """Generate list of agent keys for bash scripts"""
        return list(AGENT_CONFIG.keys())
    
    def update_readme_agent_section(self) -> bool:
        """Update the Supported AI Agents section in README.md"""
        if not self.readme_path.exists():
            print(f"❌ README.md not found at {self.readme_path}")
            return False
        
        content = self.readme_path.read_text(encoding="utf-8")
        new_table = self.generate_agent_table_markdown()
        
        # Find and replace the agent section
        pattern = r"## 🤖 Supported AI Agents.*?(?=\n## |\Z)"
        
        if not re.search(pattern, content, re.DOTALL):
            print("⚠️  Could not find '## 🤖 Supported AI Agents' section in README.md")
            return False
        
        new_content = re.sub(pattern, new_table, content, flags=re.DOTALL)
        
        if content == new_content:
            print("✅ README.md agent section is already up to date")
            return True
        
        self.readme_path.write_text(new_content, encoding="utf-8")
        print("✅ Updated README.md agent section")
        return True
    
    def check_agents_md_sync(self) -> Tuple[bool, List[str]]:
        """Check if AGENTS.md lists all agents from AGENT_CONFIG"""
        if not self.agents_md_path.exists():
            return False, ["AGENTS.md not found"]
        
        content = self.agents_md_path.read_text(encoding="utf-8")
        issues = []
        
        for agent_key, config in AGENT_CONFIG.items():
            # Check if agent key is mentioned
            if agent_key not in content:
                issues.append(f"Agent '{agent_key}' not found in AGENTS.md")
            
            # Check if agent name is mentioned
            if config["name"] not in content:
                issues.append(f"Agent name '{config['name']}' not found in AGENTS.md")
        
        return len(issues) == 0, issues
    
    def generate_release_assets_list(self) -> List[str]:
        """Generate list of release asset paths for GitHub release script"""
        assets = []
        for agent_key in AGENT_CONFIG.keys():
            for script_type in ["sh", "ps"]:
                asset = f'.genreleases/spec-kit-template-{agent_key}-{script_type}-"$VERSION".zip'
                assets.append(asset)
        return assets
    
    def update_release_script(self) -> bool:
        """Update create-github-release.sh to use dynamic asset list"""
        script_path = self.repo_root / ".github/workflows/scripts/create-github-release.sh"
        
        if not script_path.exists():
            print(f"❌ Release script not found at {script_path}")
            return False
        
        content = script_path.read_text(encoding="utf-8")
        
        # Check if script already uses dynamic generation
        if "# Auto-generated from AGENT_CONFIG" in content:
            print("✅ Release script already uses dynamic generation")
            return True
        
        # Generate new asset list
        assets = self.generate_release_assets_list()
        assets_text = " \\\n  ".join(assets)
        
        # Create new gh release create command
        new_command = f'''# Auto-generated from AGENT_CONFIG - do not edit manually
# Use scripts/generate-docs.py to regenerate

# Build asset list from all agents
ASSETS=(
  {assets_text}
)

# Create release with all assets
gh release create "$VERSION" "${{ASSETS[@]}}" \\
  --title "Spec Kit Templates - $VERSION_NO_V" \\
  --notes-file release_notes.md'''
        
        # Replace the old gh release create command
        pattern = r'gh release create.*?--notes-file release_notes\.md'
        
        if not re.search(pattern, content, re.DOTALL):
            print("⚠️  Could not find 'gh release create' command in script")
            return False
        
        new_content = re.sub(pattern, new_command, content, flags=re.DOTALL)
        
        if content == new_content:
            print("✅ Release script is already up to date")
            return True
        
        script_path.write_text(new_content, encoding="utf-8")
        print("✅ Updated release script with dynamic asset generation")
        return True
    
    def generate_init_help_params(self) -> str:
        """Generate parameter documentation for init command"""
        agents = sorted(AGENT_CONFIG.keys())
        agent_list = ", ".join(agents)
        
        doc = f"""
Available AI Agents ({len(agents)} total):
  {agent_list}

CLI-based agents (require tool installation):
"""
        cli_agents = [(k, v) for k, v in AGENT_CONFIG.items() if v["requires_cli"]]
        for agent_key, config in sorted(cli_agents, key=lambda x: x[1]["name"]):
            doc += f"  - {agent_key:15} ({config['name']})\n"
        
        doc += "\nIDE-based agents (no CLI required):\n"
        ide_agents = [(k, v) for k, v in AGENT_CONFIG.items() if not v["requires_cli"]]
        for agent_key, config in sorted(ide_agents, key=lambda x: x[1]["name"]):
            doc += f"  - {agent_key:15} ({config['name']})\n"
        
        return doc
    
    def validate_all(self) -> Tuple[bool, List[str]]:
        """Validate that all documentation is in sync"""
        issues = []
        
        # Check AGENTS.md
        sync, agent_issues = self.check_agents_md_sync()
        if not sync:
            issues.extend(agent_issues)
        
        # Check README.md has agent section
        if not self.readme_path.exists():
            issues.append("README.md not found")
        else:
            content = self.readme_path.read_text(encoding="utf-8")
            if "## 🤖 Supported AI Agents" not in content:
                issues.append("README.md missing '## 🤖 Supported AI Agents' section")
        
        # Check release script
        script_path = self.repo_root / ".github/workflows/scripts/create-github-release.sh"
        if not script_path.exists():
            issues.append("Release script not found")
        else:
            content = script_path.read_text(encoding="utf-8")
            # Check if all agents are in release script
            for agent_key in AGENT_CONFIG.keys():
                if f"spec-kit-template-{agent_key}" not in content:
                    issues.append(f"Agent '{agent_key}' missing from release script")
        
        return len(issues) == 0, issues


def main():
    import argparse
    
    # Set UTF-8 encoding for Windows console
    set_utf8_output()
    
    parser = argparse.ArgumentParser(description="Generate and sync Spec Kit documentation")
    parser.add_argument("--check", action="store_true", help="Check if docs are in sync")
    parser.add_argument("--update", action="store_true", help="Update documentation files")
    parser.add_argument("--format", choices=["markdown", "bash", "help"], 
                       help="Output specific format")
    parser.add_argument("--update-readme", action="store_true", 
                       help="Update README.md agent section")
    parser.add_argument("--update-release", action="store_true",
                       help="Update release script")
    
    args = parser.parse_args()
    
    repo_root = Path(__file__).parent.parent
    generator = DocGenerator(repo_root)
    
    if args.format == "markdown":
        print(generator.generate_agent_table_markdown())
        return 0
    
    if args.format == "bash":
        agents = generator.generate_agents_list()
        print(" ".join(agents))
        return 0
    
    if args.format == "help":
        print(generator.generate_init_help_params())
        return 0
    
    if args.update_readme:
        success = generator.update_readme_agent_section()
        return 0 if success else 1
    
    if args.update_release:
        success = generator.update_release_script()
        return 0 if success else 1
    
    if args.check:
        print("🔍 Checking documentation sync...")
        is_valid, issues = generator.validate_all()
        
        if is_valid:
            print("✅ All documentation is in sync!")
            return 0
        else:
            print("❌ Documentation sync issues found:")
            for issue in issues:
                print(f"  - {issue}")
            print("\nRun with --update to fix these issues")
            return 1
    
    if args.update:
        print("🔄 Updating documentation...")
        
        success = True
        success &= generator.update_readme_agent_section()
        success &= generator.update_release_script()
        
        if success:
            print("\n✅ All documentation updated successfully!")
            return 0
        else:
            print("\n❌ Some updates failed")
            return 1
    
    # Default: show usage
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
