"""
Domain Analysis MCP Tool

Integrates the existing domain analysis functionality as an MCP tool.
Extracts business entities, rules, and integration patterns from data files.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from fastmcp import FastMCP

# Import existing domain analysis modules
sys.path.append(str(Path(__file__).parent.parent.parent / "specify_cli"))

try:
    from specify_cli.domain_analysis import DomainAnalyzer
    from specify_cli.interactive_domain_analysis import InteractiveDomainAnalysis
    from specify_cli.domain_config import DomainConfigManager
    from specify_cli.template_populator import populate_template_from_analysis
except ImportError as e:
    print(f"Failed to import domain analysis modules: {e}", file=sys.stderr)


def analyze_domain_tool(mcp: FastMCP):
    """MCP tool for domain analysis and entity extraction."""

    @mcp.tool()
    def analyze_domain(
        data_directory: str,
        interactive: bool = False,
        domain_type: Optional[str] = None,
        confidence_threshold: float = 0.75,
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Analyze data files to extract business entities, rules, and integration patterns.

        Args:
            data_directory: Path to directory containing data files (JSON/CSV)
            interactive: Enable interactive mode for user validation
            domain_type: Domain type hint (financial, ecommerce, crm, or None for auto-detect)
            confidence_threshold: Minimum confidence for rule extraction (0.0-1.0)
            output_format: Output format (json, summary, or detailed)

        Returns:
            Dictionary containing extracted domain model with entities, rules, and integrations
        """
        try:
            data_path = Path(data_directory)
            if not data_path.exists():
                return {
                    "success": False,
                    "error": f"Data directory not found: {data_directory}"
                }

            if not data_path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {data_directory}"
                }

            # Check for data files
            data_files = list(data_path.glob("*.json")) + list(data_path.glob("*.csv"))
            if not data_files:
                return {
                    "success": False,
                    "error": f"No JSON or CSV files found in: {data_directory}"
                }

            if interactive:
                # Use interactive analysis
                interactive_analyzer = InteractiveDomainAnalysis(str(data_path))
                domain_model = interactive_analyzer.run_interactive_analysis()
            else:
                # Use direct analysis
                analyzer = DomainAnalyzer(str(data_path))
                domain_model = analyzer.analyze()

            # Apply domain type hints if provided
            if domain_type:
                config_manager = DomainConfigManager()
                template = config_manager.get_template(domain_type)
                if template:
                    # Enhance analysis with domain-specific patterns
                    analyzer.entity_patterns.update(template.entity_patterns)
                    analyzer.confidence_threshold = confidence_threshold

            # Format output based on requested format
            if output_format == "summary":
                return {
                    "success": True,
                    "summary": {
                        "entities_count": len(domain_model.entities),
                        "business_rules_count": len(domain_model.business_rules),
                        "integration_points_count": len(domain_model.integration_points),
                        "entities": [e.name for e in domain_model.entities],
                        "confidence_scores": {
                            "avg_rule_confidence": sum(r.confidence for r in domain_model.business_rules) / len(domain_model.business_rules) if domain_model.business_rules else 0
                        }
                    }
                }
            elif output_format == "detailed":
                return {
                    "success": True,
                    "domain_model": {
                        "entities": [
                            {
                                "name": e.name,
                                "description": e.description,
                                "fields": [{"name": f.name, "type": f.data_type, "is_key": f.is_key} for f in e.fields],
                                "source_files": e.source_files,
                                "relationships": e.relationships
                            }
                            for e in domain_model.entities
                        ],
                        "business_rules": [
                            {
                                "rule_id": r.rule_id,
                                "description": r.description,
                                "constraint": r.constraint,
                                "confidence": r.confidence,
                                "entities_involved": r.entities_involved
                            }
                            for r in domain_model.business_rules
                        ],
                        "integration_points": [
                            {
                                "name": i.name,
                                "type": i.type,
                                "description": i.description,
                                "data_flow": i.data_flow,
                                "format": i.format
                            }
                            for i in domain_model.integration_points
                        ]
                    }
                }
            else:  # json format (default)
                # Convert domain model to JSON-serializable format
                return {
                    "success": True,
                    "domain_model": {
                        "entities": len(domain_model.entities),
                        "business_rules": len(domain_model.business_rules),
                        "integration_points": len(domain_model.integration_points),
                        "data_files_analyzed": len(data_files),
                        "analysis_completed": True
                    },
                    "next_steps": [
                        "Use /specify to create a feature specification",
                        "Use /plan to generate implementation plan",
                        "Use template_populator to populate spec templates with extracted entities"
                    ]
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Domain analysis failed: {str(e)}"
            }

    @mcp.tool()
    def setup_domain_config(config_directory: str = ".specify") -> Dict[str, Any]:
        """
        Run interactive setup wizard to configure domain analysis preferences.

        Args:
            config_directory: Directory to store configuration files

        Returns:
            Configuration settings created by the wizard
        """
        try:
            config_manager = DomainConfigManager(config_directory)
            config = config_manager.run_setup_wizard()

            return {
                "success": True,
                "config_saved": True,
                "config_location": str(config_manager.config_file),
                "configuration": config
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Setup wizard failed: {str(e)}"
            }

    @mcp.tool()
    def list_domain_templates() -> Dict[str, Any]:
        """
        List available domain templates and their patterns.

        Returns:
            Available domain templates with descriptions and patterns
        """
        try:
            config_manager = DomainConfigManager()
            templates = config_manager.list_templates()

            template_info = {}
            for key, template in templates.items():
                template_info[key] = {
                    "name": template.name,
                    "description": template.description,
                    "entities": list(template.entity_patterns.keys()),
                    "confidence_threshold": template.confidence_threshold,
                    "business_rule_count": len(template.business_rule_templates),
                    "integration_pattern_count": len(template.integration_patterns)
                }

            return {
                "success": True,
                "templates": template_info
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list templates: {str(e)}"
            }

    return analyze_domain_tool