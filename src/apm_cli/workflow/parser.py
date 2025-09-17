"""Parser for workflow definition files."""

import os
import frontmatter


class WorkflowDefinition:
    """Simple container for workflow data."""
    
    def __init__(self, name, file_path, metadata, content):
        """Initialize a workflow definition.
        
        Args:
            name (str): Name of the workflow.
            file_path (str): Path to the workflow file.
            metadata (dict): Metadata from the frontmatter.
            content (str): Content of the workflow file.
        """
        self.name = name
        self.file_path = file_path
        self.description = metadata.get('description', '')
        self.author = metadata.get('author', '')
        self.mcp_dependencies = metadata.get('mcp', [])
        self.input_parameters = metadata.get('input', [])
        self.llm_model = metadata.get('llm', None)  # LLM model specified in frontmatter
        self.content = content
    
    def validate(self):
        """Basic validation of required fields.
        
        Returns:
            list: List of validation errors.
        """
        errors = []
        if not self.description:
            errors.append("Missing 'description' in frontmatter")
        # Input parameters are optional, so we don't check for them
        return errors


def parse_workflow_file(file_path):
    """Parse a workflow file.
    
    Args:
        file_path (str): Path to the workflow file.
    
    Returns:
        WorkflowDefinition: Parsed workflow definition.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # Extract name based on file structure
        name = _extract_workflow_name(file_path)
        metadata = post.metadata
        content = post.content
        
        return WorkflowDefinition(name, file_path, metadata, content)
    except Exception as e:
        raise ValueError(f"Failed to parse workflow file: {e}")


def _extract_workflow_name(file_path):
    """Extract workflow name from file path based on naming conventions.
    
    Args:
        file_path (str): Path to the workflow file.
    
    Returns:
        str: Extracted workflow name.
    """
    # Normalize path separators
    normalized_path = os.path.normpath(file_path)
    path_parts = normalized_path.split(os.sep)
    
    # Check if it's a VSCode .github/prompts convention
    if '.github' in path_parts and 'prompts' in path_parts:
        # For .github/prompts/name.prompt.md, extract name from filename
        github_idx = path_parts.index('.github')
        if (github_idx + 1 < len(path_parts) and 
            path_parts[github_idx + 1] == 'prompts'):
            basename = os.path.basename(file_path)
            if basename.endswith('.prompt.md'):
                return basename.replace('.prompt.md', '')
    
    # For .prompt.md files, extract name from filename
    if file_path.endswith('.prompt.md'):
        return os.path.basename(file_path).replace('.prompt.md', '')
    
    # Fallback: use filename without extension
    return os.path.splitext(os.path.basename(file_path))[0]