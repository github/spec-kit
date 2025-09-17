"""Discovery functionality for workflow files."""

import os
import glob
from .parser import parse_workflow_file


def discover_workflows(base_dir=None):
    """Find all .prompt.md files following VSCode's .github/prompts convention.
    
    Args:
        base_dir (str, optional): Base directory to search in. Defaults to current directory.
    
    Returns:
        list: List of WorkflowDefinition objects.
    """
    if base_dir is None:
        base_dir = os.getcwd()
    
    # Support VSCode's .github/prompts convention with .prompt.md files
    prompt_patterns = [
        "**/.github/prompts/*.prompt.md",     # VSCode convention: .github/prompts/
        "**/*.prompt.md"                      # Generic .prompt.md files
    ]
    
    workflow_files = []
    for pattern in prompt_patterns:
        workflow_files.extend(glob.glob(os.path.join(base_dir, pattern), recursive=True))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for file_path in workflow_files:
        if file_path not in seen:
            seen.add(file_path)
            unique_files.append(file_path)
    
    workflows = []
    for file_path in unique_files:
        try:
            workflow = parse_workflow_file(file_path)
            workflows.append(workflow)
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
    
    return workflows


def create_workflow_template(name, output_dir=None, description=None, use_vscode_convention=True):
    """Create a basic workflow template file following VSCode's .github/prompts convention.
    
    Args:
        name (str): Name of the workflow.
        output_dir (str, optional): Directory to create the file in. Defaults to current directory.
        description (str, optional): Description for the workflow. Defaults to generic description.
        use_vscode_convention (bool): Whether to use VSCode's .github/prompts structure. Defaults to True.
    
    Returns:
        str: Path to the created file.
    """
    if output_dir is None:
        output_dir = os.getcwd()
    
    title = name.replace("-", " ").title()
    workflow_description = description or f"Workflow for {title.lower()}"
    
    template = f"""---
description: {workflow_description}
author: Your Name
mcp:
  - package1
  - package2
input:
  - param1
  - param2
---

# {title}

1. Step One:
   - Details for step one
   - Use parameters like this: ${{input:param1}}

2. Step Two:
   - Details for step two
"""
    
    if use_vscode_convention:
        # Create .github/prompts directory structure
        prompts_dir = os.path.join(output_dir, ".github", "prompts")
        os.makedirs(prompts_dir, exist_ok=True)
        file_path = os.path.join(prompts_dir, f"{name}.prompt.md")
    else:
        # Create .prompt.md file in output directory
        file_path = os.path.join(output_dir, f"{name}.prompt.md")
    
    with open(file_path, "w", encoding='utf-8') as f:
        f.write(template)
    
    return file_path