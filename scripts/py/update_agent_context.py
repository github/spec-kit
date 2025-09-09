#!/usr/bin/env python3
"""
Incrementally update agent context files based on new feature plan.
Python equivalent of update-agent-context.sh for cross-platform compatibility.
Supports: CLAUDE.md, GEMINI.md, and .github/copilot-instructions.md

Usage: python update_agent_context.py [claude|gemini|copilot]
"""

import argparse
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Import from common module
import sys
from pathlib import Path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from common import get_repo_root, get_current_branch


def extract_tech_from_plan(plan_file: Path) -> dict:
    """Extract technology information from plan.md file."""
    if not plan_file.exists():
        return {}
    
    content = plan_file.read_text(encoding='utf-8')
    tech_info = {}
    
    # Extract tech information using regex patterns
    patterns = {
        'language': r'\*\*Language/Version\*\*:\s*(.+)',
        'framework': r'\*\*Primary Dependencies\*\*:\s*(.+)',
        'testing': r'\*\*Testing\*\*:\s*(.+)',
        'storage': r'\*\*Storage\*\*:\s*(.+)',
        'project_type': r'\*\*Project Type\*\*:\s*(.+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            value = match.group(1).strip()
            # Filter out placeholder values
            if value and value not in ["NEEDS CLARIFICATION", "N/A"]:
                tech_info[key] = value
    
    return tech_info


def create_agent_file_from_template(template_path: Path, target_file: Path, tech_info: dict, repo_root: Path) -> bool:
    """Create a new agent context file from template."""
    if not template_path.exists():
        print(f"ERROR: Template not found at {template_path}")
        return False
    
    content = template_path.read_text(encoding='utf-8')
    current_branch = get_current_branch()
    
    # Replace placeholders
    replacements = {
        r'\[PROJECT NAME\]': repo_root.name,
        r'\[DATE\]': datetime.now().strftime('%Y-%m-%d'),
        r'\[EXTRACTED FROM ALL PLAN\.MD FILES\]': f"- {tech_info.get('language', '')} + {tech_info.get('framework', '')} ({current_branch})",
    }
    
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)
    
    # Add project structure based on type
    project_type = tech_info.get('project_type', '').lower()
    if 'web' in project_type:
        structure = "backend/\nfrontend/\ntests/"
    else:
        structure = "src/\ntests/"
    content = re.sub(r'\[ACTUAL STRUCTURE FROM PLANS\]', structure, content)
    
    # Add commands based on language
    language = tech_info.get('language', '').lower()
    if 'python' in language:
        commands = "cd src && pytest && ruff check ."
    elif 'rust' in language:
        commands = "cargo test && cargo clippy"
    elif 'javascript' in language or 'typescript' in language:
        commands = "npm test && npm run lint"
    else:
        commands = f"# Add commands for {tech_info.get('language', 'your language')}"
    content = re.sub(r'\[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES\]', commands, content)
    
    # Add code style
    code_style = f"{tech_info.get('language', 'Language')}: Follow standard conventions"
    content = re.sub(r'\[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE\]', code_style, content)
    
    # Add recent changes
    recent_changes = f"- {current_branch}: Added {tech_info.get('language', '')} + {tech_info.get('framework', '')}"
    content = re.sub(r'\[LAST 3 FEATURES AND WHAT THEY ADDED\]', recent_changes, content)
    
    # Write the new file
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(content, encoding='utf-8')
    return True


def update_existing_agent_file(target_file: Path, tech_info: dict) -> bool:
    """Update an existing agent context file with new technology information."""
    if not target_file.exists():
        return False
    
    content = target_file.read_text(encoding='utf-8')
    current_branch = get_current_branch()
    
    # Extract manual additions if they exist
    manual_start = content.find("<!-- MANUAL ADDITIONS START -->")
    manual_end = content.find("<!-- MANUAL ADDITIONS END -->")
    manual_additions = ""
    if manual_start != -1 and manual_end != -1:
        manual_additions = content[manual_start:manual_end + len("<!-- MANUAL ADDITIONS END -->")]
        # Remove manual additions from content for processing
        content = content[:manual_start] + content[manual_end + len("<!-- MANUAL ADDITIONS END -->"):]
    
    # Update Active Technologies section
    tech_section_match = re.search(r'## Active Technologies\n(.*?)\n\n', content, re.DOTALL)
    if tech_section_match:
        existing_tech = tech_section_match.group(1)
        new_additions = []
        
        # Add new tech if not already present
        lang_framework = f"{tech_info.get('language', '')} + {tech_info.get('framework', '')}"
        if tech_info.get('language') and lang_framework not in existing_tech:
            new_additions.append(f"- {lang_framework} ({current_branch})")
        
        storage = tech_info.get('storage')
        if storage and storage not in existing_tech:
            new_additions.append(f"- {storage} ({current_branch})")
        
        if new_additions:
            updated_tech = existing_tech + "\n" + "\n".join(new_additions)
            content = content.replace(
                tech_section_match.group(0),
                f"## Active Technologies\n{updated_tech}\n\n"
            )
    
    # Update project structure if needed for web projects
    if tech_info.get('project_type', '').lower() == 'web' and 'frontend/' not in content:
        struct_match = re.search(r'## Project Structure\n```\n(.*?)\n```', content, re.DOTALL)
        if struct_match:
            updated_struct = struct_match.group(1) + "\nfrontend/src/      # Web UI"
            content = re.sub(
                r'(## Project Structure\n```\n).*?(\n```)',
                f'\\1{updated_struct}\\2',
                content,
                flags=re.DOTALL
            )
    
    # Add new commands if language is new
    language = tech_info.get('language', '')
    if language and f"# {language}" not in content:
        commands_match = re.search(r'## Commands\n```bash\n(.*?)\n```', content, re.DOTALL)
        if not commands_match:
            commands_match = re.search(r'## Commands\n(.*?)\n\n', content, re.DOTALL)
        
        if commands_match:
            new_commands = commands_match.group(1)
            if 'python' in language.lower():
                new_commands += "\ncd src && pytest && ruff check ."
            elif 'rust' in language.lower():
                new_commands += "\ncargo test && cargo clippy"
            elif any(lang in language.lower() for lang in ['javascript', 'typescript']):
                new_commands += "\nnpm test && npm run lint"
            
            if '```bash' in content:
                content = re.sub(
                    r'(## Commands\n```bash\n).*?(\n```)',
                    f'\\1{new_commands}\\2',
                    content,
                    flags=re.DOTALL
                )
            else:
                content = re.sub(
                    r'(## Commands\n).*?(\n\n)',
                    f'\\1{new_commands}\\2',
                    content,
                    flags=re.DOTALL
                )
    
    # Update recent changes (keep only last 3)
    changes_match = re.search(r'## Recent Changes\n(.*?)(\n\n|$)', content, re.DOTALL)
    if changes_match:
        changes_text = changes_match.group(1).strip()
        changes = [line for line in changes_text.split('\n') if line.strip()]
        
        # Add new change at the beginning
        new_change = f"- {current_branch}: Added {tech_info.get('language', '')} + {tech_info.get('framework', '')}"
        changes.insert(0, new_change)
        
        # Keep only last 3
        changes = changes[:3]
        
        content = re.sub(
            r'(## Recent Changes\n).*?(\n\n|$)',
            f'\\1{chr(10).join(changes)}\\2',
            content,
            flags=re.DOTALL
        )
    
    # Update date
    content = re.sub(
        r'Last updated: \d{4}-\d{2}-\d{2}',
        f'Last updated: {datetime.now().strftime("%Y-%m-%d")}',
        content
    )
    
    # Add back manual additions if they existed
    if manual_additions:
        content += "\n" + manual_additions
    
    # Write the updated file
    target_file.write_text(content, encoding='utf-8')
    return True


def update_agent_file(target_file: Path, agent_name: str, tech_info: dict, repo_root: Path) -> bool:
    """Update a single agent context file."""
    print(f"Updating {agent_name} context file: {target_file}")
    
    if not target_file.exists():
        print(f"Creating new {agent_name} context file...")
        template_path = repo_root / "templates" / "agent-file-template.md"
        return create_agent_file_from_template(template_path, target_file, tech_info, repo_root)
    else:
        print(f"Updating existing {agent_name} context file...")
        return update_existing_agent_file(target_file, tech_info)


def main():
    parser = argparse.ArgumentParser(
        description="Incrementally update agent context files based on new feature plan"
    )
    parser.add_argument(
        "agent_type",
        nargs='?',
        choices=['claude', 'gemini', 'copilot'],
        help="Agent type to update (leave empty to update all existing files)"
    )
    
    args = parser.parse_args()
    
    try:
        # Get repository information
        repo_root = get_repo_root()
        current_branch = get_current_branch()
        feature_dir = repo_root / "specs" / current_branch
        new_plan = feature_dir / "plan.md"
        
        # Check if plan exists
        if not new_plan.exists():
            print(f"ERROR: No plan.md found at {new_plan}")
            sys.exit(1)
        
        print(f"=== Updating agent context files for feature {current_branch} ===")
        
        # Extract tech information from plan
        tech_info = extract_tech_from_plan(new_plan)
        
        # Define agent context files
        agent_files = {
            'claude': repo_root / "CLAUDE.md",
            'gemini': repo_root / "GEMINI.md", 
            'copilot': repo_root / ".github" / "copilot-instructions.md"
        }
        
        # Update files based on argument or detect existing files
        if args.agent_type:
            # Update specific agent file
            target_file = agent_files[args.agent_type]
            agent_name = {
                'claude': 'Claude Code',
                'gemini': 'Gemini CLI',
                'copilot': 'GitHub Copilot'
            }[args.agent_type]
            
            success = update_agent_file(target_file, agent_name, tech_info, repo_root)
            if success:
                print(f"✅ {agent_name} context file updated successfully")
            else:
                print(f"❌ Failed to update {agent_name} context file")
                sys.exit(1)
        else:
            # Update all existing files
            updated_any = False
            for agent_type, file_path in agent_files.items():
                if file_path.exists():
                    agent_name = {
                        'claude': 'Claude Code',
                        'gemini': 'Gemini CLI', 
                        'copilot': 'GitHub Copilot'
                    }[agent_type]
                    
                    success = update_agent_file(file_path, agent_name, tech_info, repo_root)
                    if success:
                        print(f"✅ {agent_name} context file updated successfully")
                        updated_any = True
                    else:
                        print(f"❌ Failed to update {agent_name} context file")
            
            # If no files exist, create Claude Code context file by default
            if not updated_any:
                print("No agent context files found. Creating Claude Code context file by default.")
                success = update_agent_file(
                    agent_files['claude'], 
                    'Claude Code', 
                    tech_info, 
                    repo_root
                )
                if success:
                    print("✅ Claude Code context file created successfully")
                else:
                    print("❌ Failed to create Claude Code context file")
                    sys.exit(1)
        
        # Print summary
        print("\nSummary of changes:")
        if tech_info.get('language'):
            print(f"- Added language: {tech_info['language']}")
        if tech_info.get('framework'):
            print(f"- Added framework: {tech_info['framework']}")
        if tech_info.get('storage'):
            print(f"- Added database: {tech_info['storage']}")
        
        print("\nUsage: python update_agent_context.py [claude|gemini|copilot]")
        print("  - No argument: Update all existing agent context files")
        print("  - claude: Update only CLAUDE.md")
        print("  - gemini: Update only GEMINI.md")
        print("  - copilot: Update only .github/copilot-instructions.md")
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()