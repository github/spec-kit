#!/usr/bin/env python3
"""
Create release packages for each supported agent and script type.

Usage: python create-release-packages.py v0.1.0

Package naming must match what __init__.py expects:
  spectrena-template-{agent}-{script_type}-v{version}.zip

Example: spectrena-template-claude-sh-v0.1.0.zip
"""
import sys
import re
import shutil
import zipfile
from pathlib import Path

# Claude-only for now - other agents may be added later
AGENTS = {
    "claude": ".claude/",
}

COMMAND_DIRS = {
    "claude": ".claude/commands",
}

SCRIPT_TYPES = ["sh", "ps"]


def rewrite_paths(content: str) -> str:
    """Rewrite template paths to .spectrena/ paths."""
    content = re.sub(r"/?memory/", ".spectrena/memory/", content)
    content = re.sub(r"/?scripts/", ".spectrena/scripts/", content)
    content = re.sub(r"/?templates/", ".spectrena/templates/", content)
    return content


def create_agent_package(agent: str, script_type: str, version: str, output_dir: Path):
    """Create a release package for a specific agent and script type."""
    # Package name must match pattern in __init__.py download_template_from_github()
    package_name = f"spectrena-template-{agent}-{script_type}-{version}"
    package_dir = output_dir / package_name
    package_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy .spectrena/ structure
    spectrena_dir = package_dir / ".spectrena"
    spectrena_dir.mkdir(parents=True, exist_ok=True)

    # Copy memory/
    memory_src = Path("memory")
    if memory_src.exists():
        shutil.copytree(memory_src, spectrena_dir / "memory")

    # Copy scripts/ (only the relevant script type)
    scripts_src = Path("scripts")
    if scripts_src.exists():
        scripts_dest = spectrena_dir / "scripts"
        scripts_dest.mkdir(parents=True, exist_ok=True)

        if script_type == "sh":
            bash_src = scripts_src / "bash"
            if bash_src.exists():
                shutil.copytree(bash_src, scripts_dest / "bash")
        elif script_type == "ps":
            ps_src = scripts_src / "powershell"
            if ps_src.exists():
                shutil.copytree(ps_src, scripts_dest / "powershell")

        # Copy top-level script files
        for item in scripts_src.iterdir():
            if item.is_file():
                shutil.copy2(item, scripts_dest / item.name)

    # Copy templates/ (excluding commands/)
    templates_src = Path("templates")
    if templates_src.exists():
        templates_dest = spectrena_dir / "templates"
        templates_dest.mkdir(parents=True, exist_ok=True)

        for item in templates_src.rglob("*"):
            if item.is_file() and "commands" not in item.parts:
                rel_path = item.relative_to(templates_src)
                dest_file = templates_dest / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_file)

    # 2. Generate agent commands
    commands_src = Path("templates/commands")
    if commands_src.exists():
        commands_dest = package_dir / COMMAND_DIRS.get(agent, f".{agent}/commands")
        commands_dest.mkdir(parents=True, exist_ok=True)

        for cmd_file in commands_src.glob("*.md"):
            content = cmd_file.read_text()
            content = rewrite_paths(content)
            content = content.replace("{ARGS}", "$ARGUMENTS")

            output_file = commands_dest / f"spectrena.{cmd_file.stem}.md"
            output_file.write_text(content)

    # 3. Create zip
    zip_path = output_dir / f"{package_name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in package_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(package_dir)
                zf.write(file, arcname)

    # Cleanup directory
    shutil.rmtree(package_dir)

    print(f"Created: {zip_path.name}")
    return zip_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python create-release-packages.py <version>")
        sys.exit(1)

    version = sys.argv[1]
    output_dir = Path(".releases")
    output_dir.mkdir(exist_ok=True)

    print(f"Creating release packages for {version}...")

    count = 0
    for agent in AGENTS:
        for script_type in SCRIPT_TYPES:
            create_agent_package(agent, script_type, version, output_dir)
            count += 1

    print(f"\nCreated {count} packages in {output_dir}/")


if __name__ == "__main__":
    main()
