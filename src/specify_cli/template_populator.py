#!/usr/bin/env python3
"""
Template Population System for Spec-Kit

Populates specification templates with domain-specific content extracted
from data analysis, replacing placeholders with real business entities and rules.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    from .domain_analysis import DomainModel, BusinessEntity, BusinessRule, IntegrationPoint
    from .error_handling import get_error_handler, safe_file_operation
except ImportError:
    # Handle running as standalone script
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from domain_analysis import DomainModel, BusinessEntity, BusinessRule, IntegrationPoint
    from error_handling import get_error_handler, safe_file_operation


@dataclass
class TemplateSection:
    """Represents a section in the template that can be populated."""
    name: str
    start_marker: str
    end_marker: str
    placeholder_pattern: str
    content: str = ""


class TemplatePopulator:
    """Populates specification templates with domain-specific content."""

    def __init__(self, spec_file_path: str, domain_model: DomainModel):
        self.spec_file_path = Path(spec_file_path)
        self.domain_model = domain_model
        self.original_content = ""
        self.populated_content = ""
        self.error_handler = get_error_handler()

    def populate_specification(self) -> str:
        """Populate the specification template with domain model content."""
        print(f"Populating specification template: {self.spec_file_path}")

        # Read original template content
        self._read_original_content()

        # Start with original content
        self.populated_content = self.original_content

        # Populate each section
        self._populate_key_entities()
        self._populate_business_rules()
        self._populate_integration_points()

        # Write updated content back to file
        self._write_updated_content()

        print("Specification template populated with domain content")
        return self.populated_content

    def _read_original_content(self):
        """Read the original specification file content."""
        if not self.spec_file_path.exists():
            error = FileNotFoundError(f"Specification file not found: {self.spec_file_path}")
            self.error_handler.handle_file_access_error(self.spec_file_path, "read", error)
            raise error

        def read_file():
            with open(self.spec_file_path, 'r', encoding='utf-8') as f:
                return f.read()

        content = safe_file_operation("read", self.spec_file_path, read_file)
        if content is not None:
            self.original_content = content
        else:
            raise FileNotFoundError(f"Could not read specification file: {self.spec_file_path}")

    def _write_updated_content(self):
        """Write the updated content back to the specification file."""
        def write_file():
            with open(self.spec_file_path, 'w', encoding='utf-8') as f:
                f.write(self.populated_content)
            return True

        result = safe_file_operation("write", self.spec_file_path, write_file)
        if result is None:
            error = PermissionError(f"Could not write to specification file: {self.spec_file_path}")
            self.error_handler.handle_file_access_error(self.spec_file_path, "write", error)
            raise error

    def _populate_key_entities(self):
        """Populate the Key Entities section with discovered business entities."""
        print("  Populating Key Entities section...")

        # Find the Key Entities section
        entities_section_pattern = r'(### Key Entities.*?)(- \*\*\[Entity Name\]\*\*:.*?)(\n\n### |$)'
        match = re.search(entities_section_pattern, self.populated_content, re.DOTALL)

        if not match:
            print("    Warning: Key Entities section not found in template")
            return

        section_start = match.group(1)
        section_end = match.group(3) if match.group(3) else ""

        # Generate entity content
        entities_content = []
        for entity in self.domain_model.entities:
            entity_content = self._format_entity(entity)
            entities_content.append(entity_content)

        # Replace the placeholder section
        new_entities_section = section_start + "\n".join(entities_content) + "\n"
        if section_end:
            new_entities_section += section_end

        self.populated_content = re.sub(
            entities_section_pattern,
            new_entities_section,
            self.populated_content,
            flags=re.DOTALL
        )

        print(f"    Added {len(entities_content)} entities")

    def _populate_business_rules(self):
        """Populate the Business Rules section with inferred business rules."""
        print("  Populating Business Rules section...")

        # Find the Business Rules section
        rules_section_pattern = r'(### Business Rules.*?)(- \*\*BR-\d+\*\*:.*?)(\n\n### |$)'
        match = re.search(rules_section_pattern, self.populated_content, re.DOTALL)

        if not match:
            # Try alternative pattern with placeholder
            rules_section_pattern = r'(### Business Rules.*?)(- \*\*\[Business rule.*?\]\*\*:.*?)(\n\n### |$)'
            match = re.search(rules_section_pattern, self.populated_content, re.DOTALL)

        if not match:
            print("    Warning: Business Rules section not found in template")
            return

        section_start = match.group(1)
        section_end = match.group(3) if match.group(3) else ""

        # Generate business rules content
        rules_content = []
        for rule in self.domain_model.business_rules:
            rule_content = self._format_business_rule(rule)
            rules_content.append(rule_content)

        # Replace the placeholder section
        new_rules_section = section_start + "\n".join(rules_content) + "\n"
        if section_end:
            new_rules_section += section_end

        self.populated_content = re.sub(
            rules_section_pattern,
            new_rules_section,
            self.populated_content,
            flags=re.DOTALL
        )

        print(f"    Added {len(rules_content)} business rules")

    def _populate_integration_points(self):
        """Populate the Integration Points section with discovered integration points."""
        print("  Populating Integration Points section...")

        # Find the Integration Points section
        integration_section_pattern = r'(### Integration Points.*?)(- \*\*\[External System.*?\]\*\*:.*?)(\n\n### |$)'
        match = re.search(integration_section_pattern, self.populated_content, re.DOTALL)

        if not match:
            print("    Warning: Integration Points section not found in template")
            return

        section_start = match.group(1)
        section_end = match.group(3) if match.group(3) else ""

        # Generate integration points content
        integration_content = []
        for integration in self.domain_model.integration_points:
            integration_content_str = self._format_integration_point(integration)
            integration_content.append(integration_content_str)

        # Replace the placeholder section
        new_integration_section = section_start + "\n".join(integration_content) + "\n"
        if section_end:
            new_integration_section += section_end

        self.populated_content = re.sub(
            integration_section_pattern,
            new_integration_section,
            self.populated_content,
            flags=re.DOTALL
        )

        print(f"    Added {len(integration_content)} integration points")

    def _format_entity(self, entity: BusinessEntity) -> str:
        """Format a business entity for the specification."""
        # Generate field summary
        key_fields = [f for f in entity.fields if f.is_key]
        key_field_names = [f.name for f in key_fields] if key_fields else ["id"]

        return (f"- **{entity.name}**: {entity.description}\n"
                f"  - Key fields: {', '.join(key_field_names)}\n"
                f"  - Total fields: {len(entity.fields)}\n"
                f"  - Relationships: {', '.join(entity.relationships) if entity.relationships else 'none identified'}")

    def _format_business_rule(self, rule: BusinessRule) -> str:
        """Format a business rule for the specification."""
        confidence_indicator = "HIGH" if rule.confidence >= 0.9 else "MED" if rule.confidence >= 0.8 else "LOW"

        return (f"- **{rule.rule_id}**: {rule.description} - {rule.constraint}\n"
                f"  - Confidence: {rule.confidence:.1%} {confidence_indicator}\n"
                f"  - Applies to: {', '.join(rule.entities_involved)}")

    def _format_integration_point(self, integration: IntegrationPoint) -> str:
        """Format an integration point for the specification."""
        data_flow_arrow = {
            'input': '→',
            'output': '←',
            'bidirectional': '↔'
        }.get(integration.data_flow, '?')

        dependencies_str = ""
        if integration.dependencies:
            dependencies_str = f"\n  - Dependencies: {', '.join(integration.dependencies)}"

        return (f"- **{integration.name} ({integration.type})**: {integration.description}\n"
                f"  - Data flow: {integration.data_flow} {data_flow_arrow}\n"
                f"  - Format: {integration.format}{dependencies_str}")

    def generate_summary_report(self) -> str:
        """Generate a summary report of the population process."""
        entities_count = len(self.domain_model.entities)
        rules_count = len(self.domain_model.business_rules)
        integrations_count = len(self.domain_model.integration_points)

        # Calculate confidence metrics
        avg_rule_confidence = 0
        if self.domain_model.business_rules:
            avg_rule_confidence = sum(r.confidence for r in self.domain_model.business_rules) / len(self.domain_model.business_rules)

        report = f"""
Domain Analysis Complete:
- Entities discovered: {entities_count} ({', '.join(e.name for e in self.domain_model.entities)})
- Business rules extracted: {rules_count} (avg confidence: {avg_rule_confidence:.1%})
- Integration points identified: {integrations_count}
- Template sections populated: Key Entities, Business Rules, Integration Points
- Specification file updated: {self.spec_file_path}

Ready for next phase: Run '/clarify' to resolve any remaining ambiguities, then '/plan' for implementation planning.
"""
        return report.strip()


def populate_template_from_analysis(spec_file: str, data_directory: str) -> str:
    """High-level function to analyze domain and populate template in one step."""
    try:
        from .domain_analysis import DomainAnalyzer
    except ImportError:
        from domain_analysis import DomainAnalyzer

    print("Starting domain analysis and template population...")

    # Step 1: Analyze domain
    analyzer = DomainAnalyzer(data_directory)
    domain_model = analyzer.analyze()

    # Step 2: Populate template
    populator = TemplatePopulator(spec_file, domain_model)
    populated_content = populator.populate_specification()

    # Step 3: Generate summary
    summary = populator.generate_summary_report()
    print("\n" + "="*50)
    print(summary)
    print("="*50)

    return summary


def main():
    """Command-line interface for template population."""
    import sys

    if len(sys.argv) != 3:
        print("Usage: python template_populator.py <spec_file> <data_directory>")
        sys.exit(1)

    spec_file = sys.argv[1]
    data_directory = sys.argv[2]

    if not Path(spec_file).exists():
        print(f"Error: Specification file '{spec_file}' does not exist")
        sys.exit(1)

    if not Path(data_directory).exists():
        print(f"Error: Data directory '{data_directory}' does not exist")
        sys.exit(1)

    populate_template_from_analysis(spec_file, data_directory)


if __name__ == '__main__':
    main()