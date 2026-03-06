"""
Specify MCP Tool

Creates feature specifications from natural language descriptions.
Integrates with domain analysis for data-driven specifications.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from fastmcp import FastMCP


def specify_tool(mcp: FastMCP):
    """MCP tool for creating feature specifications."""

    @mcp.tool()
    def specify(
        description: str,
        repository_path: str,
        feature_name: Optional[str] = None,
        domain_data_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a feature specification from a natural language description.

        Args:
            description: Natural language description of the feature
            repository_path: Path to the git repository
            feature_name: Optional custom feature name (auto-generated if not provided)
            domain_data_directory: Optional path to data files for domain analysis

        Returns:
            Information about the created specification and next steps
        """
        try:
            repo_path = Path(repository_path)
            if not repo_path.exists():
                return {
                    "success": False,
                    "error": f"Repository path does not exist: {repository_path}"
                }

            # Generate feature name if not provided
            if not feature_name:
                # Simple feature name generation from description
                words = description.lower().split()[:3]
                feature_name = "-".join(word.strip(".,!?") for word in words)

            # Sanitize feature name to prevent path traversal
            import re
            feature_name = re.sub(r"[^a-z0-9-]+", "-", feature_name.lower()).strip("-")
            if not feature_name:
                return {"success": False, "error": "Unable to derive a valid feature name from input"}

            # Create feature directory
            features_dir = repo_path / "features"
            features_dir.mkdir(exist_ok=True)

            feature_dir = (features_dir / feature_name).resolve()
            if not feature_dir.is_relative_to(features_dir.resolve()):
                return {"success": False, "error": "Invalid feature_name path"}
            feature_dir.mkdir(exist_ok=True)

            # Create basic specification template
            spec_content = f"""# Feature Specification: {feature_name.replace('-', ' ').title()}

## Overview
{description}

## Key Entities
<!-- Domain entities will be populated by analyze_domain tool -->
- **[Entity Name]**: Description of the entity
  - Key fields: [field1, field2]
  - Relationships: [related entities]

## Business Rules
<!-- Business rules will be inferred by domain analysis -->
- **BR-001**: [Business rule description]
- **BR-002**: [Business rule description]

## Integration Points
<!-- External systems and data flows -->
- **[External System]**: Description of integration
  - Data flow: [input/output/bidirectional]
  - Format: [API/file/database]

## Acceptance Criteria
- [ ] Core functionality implemented
- [ ] Business rules enforced
- [ ] Integration points working
- [ ] Tests passing

## Implementation Notes
- Technology stack: [to be determined]
- Database requirements: [to be specified]
- External dependencies: [to be identified]

## Next Steps
1. Run `/analyze_domain` if data files available
2. Use `/clarify` to refine requirements
3. Execute `/plan` to generate implementation plan
4. Use `/tasks` to break down into actionable items
"""

            spec_file = feature_dir / "spec.md"
            spec_file.write_text(spec_content)

            result = {
                "success": True,
                "feature_name": feature_name,
                "feature_directory": str(feature_dir),
                "spec_file": str(spec_file),
                "next_steps": []
            }

            # Suggest domain analysis if data directory provided
            if domain_data_directory:
                data_path = Path(domain_data_directory)
                if data_path.exists():
                    result["next_steps"].append(
                        f"Run analyze_domain with data_directory='{domain_data_directory}' to populate entities"
                    )
                else:
                    result["warning"] = f"Data directory not found: {domain_data_directory}"

            result["next_steps"].extend([
                "Use /clarify to refine specification details",
                "Execute /plan to generate implementation plan",
                "Use /tasks to break down into actionable items"
            ])

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create specification: {str(e)}"
            }

    return specify_tool