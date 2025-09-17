"""Workflow dependency aggregator for APM-CLI."""

import os
import glob
from pathlib import Path
import yaml
import frontmatter


def scan_workflows_for_dependencies():
    """Scan all workflow files for MCP dependencies following VSCode's .github/prompts convention.
    
    Returns:
        set: A set of unique MCP server names from all workflows.
    """
    # Support VSCode's .github/prompts convention with .prompt.md files
    prompt_patterns = [
        "**/.github/prompts/*.prompt.md",     # VSCode convention: .github/prompts/
        "**/*.prompt.md"                      # Generic .prompt.md files
    ]
    
    workflows = []
    for pattern in prompt_patterns:
        workflows.extend(glob.glob(pattern, recursive=True))
    
    # Remove duplicates
    workflows = list(set(workflows))
    
    all_servers = set()
    
    for workflow_file in workflows:
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                content = frontmatter.load(f)
                if 'mcp' in content.metadata and isinstance(content.metadata['mcp'], list):
                    all_servers.update(content.metadata['mcp'])
        except Exception as e:
            print(f"Error processing {workflow_file}: {e}")
    
    return all_servers


def sync_workflow_dependencies(output_file="apm.yml"):
    """Extract all MCP servers from workflows into apm.yml.
    
    Args:
        output_file (str, optional): Path to the output file. Defaults to "apm.yml".
        
    Returns:
        tuple: (bool, list) - Success status and list of servers added
    """
    all_servers = scan_workflows_for_dependencies()
    
    # Prepare the configuration
    apm_config = {
        'version': '1.0',
        'servers': sorted(list(all_servers))
    }
    
    try:
        # Create the file
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(apm_config, f, default_flow_style=False)
        return True, apm_config['servers']
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        return False, []