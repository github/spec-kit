#!/usr/bin/env python3
"""
Shadow Mode Module for Speckit

Provides functionality to install and manage Speckit in "shadow mode" where:
- Scripts are hidden in .devtools/speckit/
- Templates and commands are unbranded
- Configuration uses custom branding
- Installation is invisible to end users
"""

import os
import json
import shutil
from pathlib import Path
from typing import Optional, Tuple, Dict
from datetime import datetime


def setup_shadow_mode(
    project_path: Path,
    brand: str = "Development Tools",
    shadow_path: str = ".devtools/speckit",
    include_docs: bool = True,
    gitignore_shadow: bool = True,
    agent: str = "claude",
    script_type: str = "sh",
    tracker = None
) -> None:
    """
    Setup shadow mode installation

    Args:
        project_path: Path to the project directory
        brand: Brand name for customization
        shadow_path: Relative path for shadow installation
        include_docs: Whether to include generic documentation
        gitignore_shadow: Whether to add shadow path to .gitignore
        agent: AI agent being used
        script_type: Script type (sh or ps)
        tracker: Optional StepTracker for progress updates
    """
    # Get source root (spec-kit repository)
    source_root = Path(__file__).parent.parent.parent

    if tracker:
        tracker.add("shadow-create-dirs", "Create shadow directory structure")
        tracker.start("shadow-create-dirs")

    # Create directory structure
    shadow_root, bash_dir, ps_dir = create_shadow_directory_structure(project_path, shadow_path)

    if tracker:
        tracker.complete("shadow-create-dirs", f"{shadow_path}")
        tracker.add("shadow-copy-scripts", "Copy all scripts to shadow")
        tracker.start("shadow-copy-scripts")

    # Copy ALL scripts to shadow directory
    scripts_copied = copy_all_scripts_to_shadow(source_root, shadow_root, tracker)

    if tracker:
        tracker.complete("shadow-copy-scripts", f"{scripts_copied} scripts")
        tracker.add("shadow-templates", "Install generic templates")
        tracker.start("shadow-templates")

    # Copy generic templates
    source_templates = source_root / "templates" / "shadow"
    project_templates = project_path / "templates"
    copy_generic_templates(source_templates, project_templates, tracker)

    if tracker:
        tracker.complete("shadow-templates")
        tracker.add("shadow-commands", "Install unbranded commands")
        tracker.start("shadow-commands")

    # Copy unbranded commands
    source_commands = source_root / "templates" / "shadow" / "commands"
    project_commands = project_path / f".{agent}" / "commands"
    copy_unbranded_commands(source_commands, project_commands, shadow_path, script_type, tracker)

    if tracker:
        tracker.complete("shadow-commands")
        tracker.add("shadow-config", "Create configuration")
        tracker.start("shadow-config")

    # Create shadow config
    config_path = project_path / ".devtools" / ".config.json"
    create_shadow_config(config_path, brand, shadow_path, agent, script_type)

    if tracker:
        tracker.complete("shadow-config")

    # Generate docs if requested
    if include_docs:
        if tracker:
            tracker.add("shadow-docs", "Generate generic documentation")
            tracker.start("shadow-docs")

        source_docs = source_root / "docs" / "shadow"
        project_docs = project_path / "docs"
        generate_generic_docs(source_docs, project_docs, brand, tracker)

        if tracker:
            tracker.complete("shadow-docs")

    # Update .gitignore if requested
    if gitignore_shadow:
        if tracker:
            tracker.add("shadow-gitignore", "Update .gitignore")
            tracker.start("shadow-gitignore")

        update_gitignore(project_path, shadow_path)

        if tracker:
            tracker.complete("shadow-gitignore")

    # Create VERSION file
    if tracker:
        tracker.add("shadow-version", "Create VERSION file")
        tracker.start("shadow-version")

    version_file = shadow_root / "VERSION"
    create_version_file(version_file, "1.0.0")

    if tracker:
        tracker.complete("shadow-version")


def create_shadow_directory_structure(
    project_path: Path,
    shadow_path: str
) -> Tuple[Path, Path, Path]:
    """
    Create shadow directory structure

    Returns:
        Tuple of (shadow_root, bash_scripts_dir, ps_scripts_dir)
    """
    shadow_root = project_path / shadow_path
    bash_dir = shadow_root / "scripts" / "bash"
    ps_dir = shadow_root / "scripts" / "powershell"

    # Create all directories
    bash_dir.mkdir(parents=True, exist_ok=True)
    ps_dir.mkdir(parents=True, exist_ok=True)

    # Create lib directory for bash
    (bash_dir / "lib").mkdir(exist_ok=True)

    return shadow_root, bash_dir, ps_dir


def copy_all_scripts_to_shadow(
    source_root: Path,
    shadow_root: Path,
    tracker = None
) -> int:
    """
    Copy ALL bash and PowerShell scripts to shadow directory

    Returns:
        Number of scripts copied
    """
    scripts_copied = 0

    # Copy bash scripts
    bash_source = source_root / "scripts" / "bash"
    bash_dest = shadow_root / "scripts" / "bash"

    if bash_source.exists():
        for script_file in bash_source.glob("*.sh"):
            shutil.copy2(script_file, bash_dest / script_file.name)
            scripts_copied += 1

        # Copy lib/common.sh if it exists
        lib_source = bash_source / "lib" / "common.sh"
        if lib_source.exists():
            lib_dest = bash_dest / "lib" / "common.sh"
            shutil.copy2(lib_source, lib_dest)
            scripts_copied += 1

    # Copy PowerShell scripts
    ps_source = source_root / "scripts" / "powershell"
    ps_dest = shadow_root / "scripts" / "powershell"

    if ps_source.exists():
        for script_file in ps_source.glob("*.ps1"):
            shutil.copy2(script_file, ps_dest / script_file.name)
            scripts_copied += 1

    return scripts_copied


def copy_generic_templates(
    source_templates_dir: Path,
    project_templates_dir: Path,
    tracker = None
) -> None:
    """Copy generic templates to project"""
    project_templates_dir.mkdir(parents=True, exist_ok=True)

    if not source_templates_dir.exists():
        return

    # Copy all template files (except commands directory)
    for template_file in source_templates_dir.iterdir():
        if template_file.is_file():
            shutil.copy2(template_file, project_templates_dir / template_file.name)


def copy_unbranded_commands(
    source_commands_dir: Path,
    project_commands_dir: Path,
    shadow_path: str,
    script_type: str,
    tracker = None
) -> None:
    """
    Copy unbranded commands and update script paths

    Replaces placeholders:
    - {SHADOW_PATH} → actual shadow path
    - {SCRIPT_EXT} → .sh or .ps1 based on script_type
    """
    project_commands_dir.mkdir(parents=True, exist_ok=True)

    if not source_commands_dir.exists():
        return

    script_ext = ".sh" if script_type == "sh" else ".ps1"

    for command_file in source_commands_dir.glob("*.md"):
        # Read command file
        content = command_file.read_text(encoding='utf-8')

        # Replace placeholders
        content = content.replace("{SHADOW_PATH}", shadow_path)
        content = content.replace("{SCRIPT_EXT}", script_ext)

        # Write to project
        dest_file = project_commands_dir / command_file.name
        dest_file.write_text(content, encoding='utf-8')


def create_shadow_config(
    config_path: Path,
    brand: str,
    shadow_path: str,
    agent: str,
    script_type: str
) -> None:
    """Create shadow mode configuration file"""
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine script extension and paths
    script_ext = "sh" if script_type == "sh" else "ps1"
    script_dir = "bash" if script_type == "sh" else "powershell"

    config = {
        "mode": "shadow",
        "brand_name": brand,
        "speckit_version": "1.0.0",
        "shadow_path": shadow_path,
        "templates_path": "templates",
        "agent": agent,
        "script_type": script_type,
        "scripts": {
            script_type: {
                "common": f"{shadow_path}/scripts/{script_dir}/common.{script_ext}",
                "validate": f"{shadow_path}/scripts/{script_dir}/validate-spec.{script_ext}",
                "token_budget": f"{shadow_path}/scripts/{script_dir}/token-budget.{script_ext}",
                "semantic_search": f"{shadow_path}/scripts/{script_dir}/semantic-search.{script_ext}",
                "session_prune": f"{shadow_path}/scripts/{script_dir}/session-prune.{script_ext}",
                "error_analysis": f"{shadow_path}/scripts/{script_dir}/error-analysis.{script_ext}",
                "clarify_history": f"{shadow_path}/scripts/{script_dir}/clarify-history.{script_ext}",
                "project_analysis": f"{shadow_path}/scripts/{script_dir}/project-analysis.{script_ext}",
                "project_catalog": f"{shadow_path}/scripts/{script_dir}/project-catalog.{script_ext}",
                "onboard": f"{shadow_path}/scripts/{script_dir}/onboard.{script_ext}",
                "reverse_engineer": f"{shadow_path}/scripts/{script_dir}/reverse-engineer.{script_ext}",
                "create_feature": f"{shadow_path}/scripts/{script_dir}/create-new-feature.{script_ext}",
                "setup_plan": f"{shadow_path}/scripts/{script_dir}/setup-plan.{script_ext}",
                "setup_ai_doc": f"{shadow_path}/scripts/{script_dir}/setup-ai-doc.{script_ext}",
                "update_context": f"{shadow_path}/scripts/{script_dir}/update-agent-context.{script_ext}",
                "check_prerequisites": f"{shadow_path}/scripts/{script_dir}/check-prerequisites.{script_ext}"
            }
        },
        "claude_commands": [
            "specify", "plan", "tasks", "implement", "validate",
            "budget", "prune", "find", "error-context", "clarify-history",
            "clarify", "analyze", "checklist", "discover", "document",
            "onboard", "project-analysis", "project-catalog", "resume",
            "service-catalog", "validate-contracts", "constitution"
        ]
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
        f.write('\n')


def generate_generic_docs(
    source_docs_dir: Path,
    project_docs_dir: Path,
    brand: str,
    tracker = None
) -> None:
    """Generate generic workflow documentation"""
    project_docs_dir.mkdir(parents=True, exist_ok=True)

    if not source_docs_dir.exists():
        return

    # Copy all documentation files
    for doc_file in source_docs_dir.glob("*.md"):
        content = doc_file.read_text(encoding='utf-8')

        # Replace brand placeholder
        content = content.replace("{BRAND_NAME}", brand)

        dest_file = project_docs_dir / doc_file.name
        dest_file.write_text(content, encoding='utf-8')


def update_gitignore(
    project_path: Path,
    shadow_path: str
) -> None:
    """Add shadow_path to .gitignore"""
    gitignore_path = project_path / ".gitignore"

    # Extract directory to ignore (first component of shadow_path)
    dir_to_ignore = shadow_path.split('/')[0]

    if not dir_to_ignore.startswith('.'):
        dir_to_ignore = '.' + dir_to_ignore

    # Create or read .gitignore
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding='utf-8')
    else:
        content = ""

    # Check if already present
    if dir_to_ignore not in content:
        # Add to .gitignore
        if content and not content.endswith('\n'):
            content += '\n'

        content += f"\n# Shadow mode - hidden development tools\n"
        content += f"{dir_to_ignore}/\n"

        gitignore_path.write_text(content, encoding='utf-8')


def create_version_file(
    version_file_path: Path,
    version: str
) -> None:
    """Create VERSION file in shadow directory"""
    version_file_path.write_text(f"{version}\n", encoding='utf-8')


# Utility functions

def detect_current_mode(project_path: Path = None) -> str:
    """
    Detect if project uses standard or shadow mode

    Returns:
        "standard", "shadow", or "unknown"
    """
    if project_path is None:
        project_path = Path.cwd()

    # Check for shadow mode config
    shadow_config = project_path / ".devtools" / ".config.json"
    if shadow_config.exists():
        try:
            with open(shadow_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if config.get('mode') == 'shadow':
                    return "shadow"
        except (json.JSONDecodeError, KeyError):
            pass

    # Check for standard mode config
    standard_config = project_path / ".speckit.config.json"
    if standard_config.exists():
        return "standard"

    return "unknown"


def load_config(project_path: Path = None) -> Dict:
    """
    Load configuration file

    Returns configuration dict, checks for:
    1. .devtools/.config.json (shadow mode)
    2. .speckit.config.json (standard mode)
    """
    if project_path is None:
        project_path = Path.cwd()

    # Try shadow mode config first
    shadow_config = project_path / ".devtools" / ".config.json"
    if shadow_config.exists():
        try:
            with open(shadow_config, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass

    # Try standard mode config
    standard_config = project_path / ".speckit.config.json"
    if standard_config.exists():
        try:
            with open(standard_config, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass

    return {}


# Conversion functions

def convert_standard_to_shadow(
    project_path: Path,
    brand: str = "Development Tools",
    shadow_path: str = ".devtools/speckit",
    backup: bool = True,
    tracker = None
) -> None:
    """
    Convert standard mode to shadow mode with backup

    Steps:
    1. Create backup directory
    2. Backup current scripts/, templates/, hooks/, docs/
    3. Move scripts to shadow location
    4. Replace templates with generic versions
    5. Replace commands with unbranded versions
    6. Create .devtools/.config.json
    7. Update .gitignore
    8. Remove old .speckit.config.json
    """
    if tracker:
        tracker.add("convert-detect", "Detect current configuration")
        tracker.start("convert-detect")

    # Verify we're in standard mode
    current_mode = detect_current_mode(project_path)
    if current_mode != "standard":
        raise ValueError(f"Cannot convert: project is in '{current_mode}' mode, expected 'standard'")

    config = load_config(project_path)
    agent = config.get('default_agent', 'claude')

    if tracker:
        tracker.complete("convert-detect", "standard mode")

    # Create backup if requested
    backup_dir = None
    if backup:
        if tracker:
            tracker.add("convert-backup", "Create backup")
            tracker.start("convert-backup")

        backup_dir = create_backup(project_path, "standard")

        if tracker:
            tracker.complete("convert-backup", backup_dir.name)

    # Get source root for templates
    source_root = Path(__file__).parent.parent.parent

    if tracker:
        tracker.add("convert-shadow-setup", "Setup shadow structure")
        tracker.start("convert-shadow-setup")

    # Create shadow directory structure
    shadow_root, bash_dir, ps_dir = create_shadow_directory_structure(project_path, shadow_path)

    if tracker:
        tracker.complete("convert-shadow-setup")
        tracker.add("convert-move-scripts", "Move scripts to shadow")
        tracker.start("convert-move-scripts")

    # Move scripts to shadow directory
    scripts_dir = project_path / "scripts"
    if scripts_dir.exists():
        # Move bash scripts
        bash_source = scripts_dir / "bash"
        if bash_source.exists():
            for script_file in bash_source.glob("*.sh"):
                shutil.move(str(script_file), str(bash_dir / script_file.name))

            # Move lib directory
            lib_source = bash_source / "lib"
            if lib_source.exists():
                shutil.copytree(lib_source, bash_dir / "lib", dirs_exist_ok=True)

        # Move PowerShell scripts
        ps_source = scripts_dir / "powershell"
        if ps_source.exists():
            for script_file in ps_source.glob("*.ps1"):
                shutil.move(str(script_file), str(ps_dir / script_file.name))

        # Remove old scripts directory
        shutil.rmtree(scripts_dir)

    if tracker:
        tracker.complete("convert-move-scripts")
        tracker.add("convert-templates", "Replace templates")
        tracker.start("convert-templates")

    # Replace templates with generic versions
    templates_dir = project_path / "templates"
    if templates_dir.exists():
        shutil.rmtree(templates_dir)

    source_templates = source_root / "templates" / "shadow"
    copy_generic_templates(source_templates, templates_dir, tracker)

    if tracker:
        tracker.complete("convert-templates")
        tracker.add("convert-commands", "Replace commands")
        tracker.start("convert-commands")

    # Replace commands with unbranded versions
    commands_dir = project_path / f".{agent}" / "commands"
    if commands_dir.exists():
        shutil.rmtree(commands_dir)

    source_commands = source_root / "templates" / "shadow" / "commands"
    copy_unbranded_commands(source_commands, commands_dir, shadow_path, "sh", tracker)

    if tracker:
        tracker.complete("convert-commands")
        tracker.add("convert-config", "Create shadow config")
        tracker.start("convert-config")

    # Create shadow config
    config_path = project_path / ".devtools" / ".config.json"
    create_shadow_config(config_path, brand, shadow_path, agent, "sh")

    if tracker:
        tracker.complete("convert-config")
        tracker.add("convert-gitignore", "Update .gitignore")
        tracker.start("convert-gitignore")

    # Update .gitignore
    update_gitignore(project_path, shadow_path)

    if tracker:
        tracker.complete("convert-gitignore")
        tracker.add("convert-cleanup", "Remove standard mode files")
        tracker.start("convert-cleanup")

    # Remove old config
    old_config = project_path / ".speckit.config.json"
    if old_config.exists():
        old_config.unlink()

    # Create VERSION file
    version_file = shadow_root / "VERSION"
    create_version_file(version_file, "1.0.0")

    if tracker:
        tracker.complete("convert-cleanup")


def convert_shadow_to_standard(
    project_path: Path,
    backup: bool = True,
    tracker = None
) -> None:
    """
    Convert shadow mode to standard mode with backup

    Steps:
    1. Create backup directory
    2. Backup .devtools/ directory
    3. Move scripts from shadow to standard location (scripts/)
    4. Replace templates with Speckit-branded versions
    5. Replace commands with Speckit commands
    6. Create .speckit.config.json
    7. Remove .devtools/ directory
    8. Update .gitignore (remove .devtools/)
    """
    if tracker:
        tracker.add("convert-detect", "Detect current configuration")
        tracker.start("convert-detect")

    # Verify we're in shadow mode
    current_mode = detect_current_mode(project_path)
    if current_mode != "shadow":
        raise ValueError(f"Cannot convert: project is in '{current_mode}' mode, expected 'shadow'")

    config = load_config(project_path)
    agent = config.get('agent', 'claude')
    shadow_path = config.get('shadow_path', '.devtools/speckit')

    if tracker:
        tracker.complete("convert-detect", "shadow mode")

    # Create backup if requested
    backup_dir = None
    if backup:
        if tracker:
            tracker.add("convert-backup", "Create backup")
            tracker.start("convert-backup")

        backup_dir = create_backup(project_path, "shadow")

        if tracker:
            tracker.complete("convert-backup", backup_dir.name)

    if tracker:
        tracker.add("convert-move-scripts", "Move scripts to standard location")
        tracker.start("convert-move-scripts")

    # Move scripts from shadow to standard location
    shadow_root = project_path / shadow_path
    scripts_dir = project_path / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    # Move bash scripts
    bash_source = shadow_root / "scripts" / "bash"
    if bash_source.exists():
        bash_dest = scripts_dir / "bash"
        shutil.copytree(bash_source, bash_dest, dirs_exist_ok=True)

    # Move PowerShell scripts
    ps_source = shadow_root / "scripts" / "powershell"
    if ps_source.exists():
        ps_dest = scripts_dir / "powershell"
        shutil.copytree(ps_source, ps_dest, dirs_exist_ok=True)

    if tracker:
        tracker.complete("convert-move-scripts")
        tracker.add("convert-cleanup", "Remove shadow directory")
        tracker.start("convert-cleanup")

    # Remove .devtools directory
    devtools_dir = project_path / ".devtools"
    if devtools_dir.exists():
        shutil.rmtree(devtools_dir)

    if tracker:
        tracker.complete("convert-cleanup")
        tracker.add("convert-config", "Create standard config")
        tracker.start("convert-config")

    # Create standard config
    standard_config = {
        "version": "1.0.0",
        "project_name": project_path.name,
        "default_agent": agent
    }

    config_path = project_path / ".speckit.config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(standard_config, f, indent=2)
        f.write('\n')

    if tracker:
        tracker.complete("convert-config")
        tracker.add("convert-gitignore", "Update .gitignore")
        tracker.start("convert-gitignore")

    # Update .gitignore to remove shadow path
    gitignore_path = project_path / ".gitignore"
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding='utf-8')

        # Remove shadow mode entries
        lines = content.split('\n')
        filtered_lines = []
        skip_next = False

        for line in lines:
            if "Shadow mode" in line or "hidden development tools" in line:
                skip_next = True
                continue
            if skip_next and ".devtools" in line:
                skip_next = False
                continue
            filtered_lines.append(line)

        gitignore_path.write_text('\n'.join(filtered_lines), encoding='utf-8')

    if tracker:
        tracker.complete("convert-gitignore")


def create_backup(
    project_path: Path,
    mode: str
) -> Path:
    """
    Create timestamped backup

    Returns:
        backup directory path
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = project_path / ".devtools" / "backups" / f"{mode}-mode-{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    if mode == "standard":
        # Backup standard mode files
        items_to_backup = ["scripts", "templates", "hooks", ".speckit.config.json"]

        for item in items_to_backup:
            source = project_path / item
            if source.exists():
                dest = backup_dir / item
                if source.is_dir():
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)

    elif mode == "shadow":
        # Backup shadow mode files
        devtools = project_path / ".devtools"
        if devtools.exists():
            # Only backup speckit directory and config, not the backups folder itself
            for item in ["speckit", ".config.json"]:
                source = devtools / item
                if source.exists():
                    dest = backup_dir / item
                    if source.is_dir():
                        shutil.copytree(source, dest)
                    else:
                        shutil.copy2(source, dest)

    return backup_dir
