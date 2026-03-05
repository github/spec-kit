#!/usr/bin/env python3
"""
Unit tests for template_populator module.

Tests template population functionality, specification updates, and domain content integration.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the modules under test
import sys
sys.path.append(str(Path(__file__).parent.parent / "src" / "specify_cli"))

from template_populator import (
    TemplatePopulator,
    TemplateSection,
    populate_template_from_analysis
)
from domain_analysis import (
    DomainModel,
    BusinessEntity,
    BusinessRule,
    IntegrationPoint,
    EntityField
)


class TestTemplateSection:
    """Test cases for the TemplateSection class."""

    def test_template_section_creation(self):
        """Test TemplateSection creation and attributes."""
        section = TemplateSection(
            name="Key Entities",
            start_marker="### Key Entities",
            end_marker="### Business Rules",
            placeholder_pattern=r"\*\*\[Entity Name\]\*\*",
            content="Sample content"
        )

        assert section.name == "Key Entities"
        assert section.start_marker == "### Key Entities"
        assert section.end_marker == "### Business Rules"
        assert section.placeholder_pattern == r"\*\*\[Entity Name\]\*\*"
        assert section.content == "Sample content"


class TestTemplatePopulator:
    """Test cases for the TemplatePopulator class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create sample domain model
        self.domain_model = self._create_sample_domain_model()

        # Create temporary spec file
        self.temp_spec_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_spec_file.write(self._get_sample_template_content())
        self.temp_spec_file.close()

        self.populator = TemplatePopulator(self.temp_spec_file.name, self.domain_model)

    def teardown_method(self):
        """Clean up test fixtures."""
        Path(self.temp_spec_file.name).unlink(missing_ok=True)

    def _create_sample_domain_model(self):
        """Create a sample domain model for testing."""
        entities = [
            BusinessEntity(
                name="Invoice",
                description="Financial document representing amount due",
                fields=[
                    EntityField(name="invoice_id", field_type="string", is_key=True),
                    EntityField(name="supplier_id", field_type="string", is_key=False),
                    EntityField(name="total_amount", field_type="float", is_key=False)
                ],
                confidence=0.95,
                relationships=["supplier_id → Supplier"]
            ),
            BusinessEntity(
                name="Payment",
                description="Financial transaction for invoice settlement",
                fields=[
                    EntityField(name="payment_id", field_type="string", is_key=True),
                    EntityField(name="reference", field_type="string", is_key=False),
                    EntityField(name="amount", field_type="float", is_key=False)
                ],
                confidence=0.88,
                relationships=["reference → Invoice"]
            )
        ]

        business_rules = [
            BusinessRule(
                rule_id="BR-001",
                description="Payments can only be matched to invoices from the same supplier",
                constraint="payment.supplier_id == invoice.supplier_id",
                entities_involved=["Payment", "Invoice"],
                confidence=0.92
            ),
            BusinessRule(
                rule_id="BR-002",
                description="Payment amount must not exceed invoice amount",
                constraint="payment.amount <= invoice.amount * 1.05",
                entities_involved=["Payment", "Invoice"],
                confidence=0.85
            )
        ]

        integration_points = [
            IntegrationPoint(
                name="ERP System",
                integration_type="api",
                description="Bidirectional data sync with enterprise system",
                data_flow="bidirectional",
                format="JSON REST API",
                dependencies=["auth_service"]
            ),
            IntegrationPoint(
                name="Bank Feeds",
                integration_type="file_system",
                description="Daily bank statement import",
                data_flow="input",
                format="CSV files",
                dependencies=[]
            )
        ]

        return DomainModel(
            entities=entities,
            business_rules=business_rules,
            integration_points=integration_points
        )

    def _get_sample_template_content(self):
        """Get sample template content for testing."""
        return """# Feature Specification

## Overview
This is a sample specification template.

### Key Entities
- **[Entity Name]**: [Description]
  - Key fields: [field1, field2]
  - Total fields: [count]
  - Relationships: [relationships]

### Business Rules
- **[Business rule identifier]**: [Business rule description]
  - Confidence: [confidence score]
  - Applies to: [entities]

### Integration Points
- **[External System Name]**: [Integration description]
  - Data flow: [direction]
  - Format: [data format]

## Implementation Notes
These are the implementation details.
"""

    def test_init(self):
        """Test TemplatePopulator initialization."""
        assert self.populator.spec_file_path == Path(self.temp_spec_file.name)
        assert self.populator.domain_model == self.domain_model
        assert self.populator.original_content == ""
        assert self.populator.populated_content == ""

    def test_read_original_content(self):
        """Test reading original template content."""
        self.populator._read_original_content()

        assert self.populator.original_content != ""
        assert "### Key Entities" in self.populator.original_content
        assert "### Business Rules" in self.populator.original_content
        assert "### Integration Points" in self.populator.original_content

    def test_read_nonexistent_file(self):
        """Test reading non-existent specification file."""
        populator = TemplatePopulator("/nonexistent/file.md", self.domain_model)

        with pytest.raises(FileNotFoundError):
            populator._read_original_content()

    def test_format_entity(self):
        """Test entity formatting for specification."""
        entity = self.domain_model.entities[0]  # Invoice entity
        formatted = self.populator._format_entity(entity)

        assert "**Invoice**:" in formatted
        assert "Financial document representing amount due" in formatted
        assert "Key fields: invoice_id" in formatted
        assert "Total fields: 3" in formatted
        assert "Relationships: supplier_id → Supplier" in formatted

    def test_format_business_rule(self):
        """Test business rule formatting for specification."""
        rule = self.domain_model.business_rules[0]  # BR-001
        formatted = self.populator._format_business_rule(rule)

        assert "**BR-001**:" in formatted
        assert "Payments can only be matched to invoices" in formatted
        assert "Confidence:" in formatted
        assert "Applies to: Payment, Invoice" in formatted

    def test_format_integration_point(self):
        """Test integration point formatting for specification."""
        integration = self.domain_model.integration_points[0]  # ERP System
        formatted = self.populator._format_integration_point(integration)

        assert "**ERP System (api)**:" in formatted
        assert "Bidirectional data sync" in formatted
        assert "Data flow: bidirectional" in formatted
        assert "Format: JSON REST API" in formatted
        assert "Dependencies: auth_service" in formatted

    def test_format_integration_point_no_dependencies(self):
        """Test integration point formatting without dependencies."""
        integration = self.domain_model.integration_points[1]  # Bank Feeds
        formatted = self.populator._format_integration_point(integration)

        assert "**Bank Feeds (file_system)**:" in formatted
        assert "Daily bank statement import" in formatted
        assert "Data flow: input" in formatted
        assert "Format: CSV files" in formatted
        assert "Dependencies:" not in formatted  # No dependencies section

    def test_populate_key_entities(self):
        """Test populating the Key Entities section."""
        self.populator._read_original_content()
        self.populator.populated_content = self.populator.original_content

        self.populator._populate_key_entities()

        # Check that placeholder was replaced
        assert "**[Entity Name]**:" not in self.populator.populated_content
        assert "**Invoice**:" in self.populator.populated_content
        assert "**Payment**:" in self.populator.populated_content

        # Check content structure
        assert "Financial document representing amount due" in self.populator.populated_content
        assert "Key fields: invoice_id" in self.populator.populated_content

    def test_populate_business_rules(self):
        """Test populating the Business Rules section."""
        self.populator._read_original_content()
        self.populator.populated_content = self.populator.original_content

        self.populator._populate_business_rules()

        # Check that placeholder was replaced
        assert "**[Business rule identifier]**:" not in self.populator.populated_content
        assert "**BR-001**:" in self.populator.populated_content
        assert "**BR-002**:" in self.populator.populated_content

        # Check content structure
        assert "Payments can only be matched to invoices" in self.populator.populated_content
        assert "Confidence:" in self.populator.populated_content

    def test_populate_integration_points(self):
        """Test populating the Integration Points section."""
        self.populator._read_original_content()
        self.populator.populated_content = self.populator.original_content

        self.populator._populate_integration_points()

        # Check that placeholder was replaced
        assert "**[External System Name]**:" not in self.populator.populated_content
        assert "**ERP System (api)**:" in self.populator.populated_content
        assert "**Bank Feeds (file_system)**:" in self.populator.populated_content

        # Check content structure
        assert "Bidirectional data sync" in self.populator.populated_content
        assert "Data flow: bidirectional" in self.populator.populated_content

    def test_populate_specification_complete(self):
        """Test complete specification population."""
        populated_content = self.populator.populate_specification()

        # Check that all sections were populated
        assert "**Invoice**:" in populated_content
        assert "**Payment**:" in populated_content
        assert "**BR-001**:" in populated_content
        assert "**BR-002**:" in populated_content
        assert "**ERP System (api)**:" in populated_content
        assert "**Bank Feeds (file_system)**:" in populated_content

        # Check that original structure is preserved
        assert "## Overview" in populated_content
        assert "## Implementation Notes" in populated_content

        # Check that file was updated
        with open(self.temp_spec_file.name, 'r') as f:
            file_content = f.read()
        assert file_content == populated_content

    def test_generate_summary_report(self):
        """Test summary report generation."""
        summary = self.populator.generate_summary_report()

        assert "Domain Analysis Complete:" in summary
        assert "Entities discovered: 2" in summary
        assert "Business rules extracted: 2" in summary
        assert "Integration points identified: 2" in summary
        assert "Invoice, Payment" in summary

        # Check confidence metrics
        assert "avg confidence:" in summary

    def test_template_without_sections(self):
        """Test template population when sections are missing."""
        # Create template without standard sections
        minimal_template = """# Minimal Template

## Description
This template has no standard sections.

## Notes
Just some notes.
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(minimal_template)
            minimal_file = f.name

        try:
            populator = TemplatePopulator(minimal_file, self.domain_model)
            populated_content = populator.populate_specification()

            # Should not crash, should return original content
            assert "## Description" in populated_content
            assert "## Notes" in populated_content
        finally:
            Path(minimal_file).unlink()


class TestTemplatePopulationIntegration:
    """Integration tests for template population."""

    def test_populate_template_from_analysis_function(self):
        """Test the high-level populate_template_from_analysis function."""
        # Create temporary spec file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as spec_file:
            spec_file.write("""# Test Specification

### Key Entities
- **[Entity Name]**: [Description]

### Business Rules
- **[Business rule identifier]**: [Business rule description]

### Integration Points
- **[External System Name]**: [Integration description]
""")
            spec_path = spec_file.name

        # Create temporary data directory with sample data
        data_dir = Path(__file__).parent / "data" / "sample"

        try:
            # Mock the print statements to capture output
            with patch('builtins.print') as mock_print:
                summary = populate_template_from_analysis(spec_path, str(data_dir))

            # Check that analysis was performed
            assert isinstance(summary, str)
            assert "Domain Analysis Complete:" in summary

            # Check that template was updated
            with open(spec_path, 'r') as f:
                updated_content = f.read()

            # Should contain real entities instead of placeholders
            assert "**[Entity Name]**:" not in updated_content
            # Should have discovered actual entities from sample data
            # (specific entities depend on sample data content)

        finally:
            Path(spec_path).unlink()

    def test_multiple_template_formats(self):
        """Test population with different template formats."""
        templates = [
            # Format 1: Standard format
            """### Key Entities
- **[Entity Name]**: [Description]
""",
            # Format 2: Alternative format
            """### Key Entities
- **[Entity Name]**: [Description]
  - Key fields: [fields]
""",
            # Format 3: Different placeholder pattern
            """### Key Entities
- **{Entity Name}**: {Description}
"""
        ]

        domain_model = DomainModel(
            entities=[BusinessEntity(
                name="TestEntity",
                description="Test description",
                fields=[EntityField(name="id", field_type="string", is_key=True)],
                confidence=0.9
            )],
            business_rules=[],
            integration_points=[]
        )

        for i, template_content in enumerate(templates):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(template_content)
                template_file = f.name

            try:
                populator = TemplatePopulator(template_file, domain_model)

                # For formats that match our regex patterns
                if i < 2:
                    populated = populator.populate_specification()
                    assert "**TestEntity**:" in populated
                else:
                    # Format 3 uses different placeholders, won't be replaced
                    populated = populator.populate_specification()
                    # Should preserve original content
                    assert "{Entity Name}" in populated

            finally:
                Path(template_file).unlink()


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_file_permission_error(self):
        """Test handling of file permission errors."""
        # Create a read-only file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Template")
            readonly_file = f.name

        try:
            # Make file read-only
            import os
            os.chmod(readonly_file, 0o444)

            domain_model = DomainModel(entities=[], business_rules=[], integration_points=[])
            populator = TemplatePopulator(readonly_file, domain_model)

            # Should handle permission error gracefully
            with pytest.raises(PermissionError):
                populator.populate_specification()

        finally:
            # Restore permissions and clean up
            os.chmod(readonly_file, 0o644)
            Path(readonly_file).unlink()

    def test_empty_domain_model(self):
        """Test template population with empty domain model."""
        empty_model = DomainModel(entities=[], business_rules=[], integration_points=[])

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""### Key Entities
- **[Entity Name]**: [Description]

### Business Rules
- **[Business rule identifier]**: [Business rule description]
""")
            template_file = f.name

        try:
            populator = TemplatePopulator(template_file, empty_model)
            populated = populator.populate_specification()

            # Should handle empty model gracefully
            # Placeholders might remain if no content to replace
            assert "### Key Entities" in populated
            assert "### Business Rules" in populated

        finally:
            Path(template_file).unlink()

    def test_malformed_template_structure(self):
        """Test handling of malformed template structure."""
        malformed_template = """# Malformed Template

### Key Entities
This section has no proper structure
- No proper entity format

### Business Rules
- **Partial rule
Missing closing markers
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(malformed_template)
            template_file = f.name

        try:
            domain_model = DomainModel(
                entities=[BusinessEntity(
                    name="TestEntity",
                    description="Test",
                    fields=[],
                    confidence=0.8
                )],
                business_rules=[],
                integration_points=[]
            )

            populator = TemplatePopulator(template_file, domain_model)

            # Should not crash, should handle gracefully
            populated = populator.populate_specification()
            assert "# Malformed Template" in populated

        finally:
            Path(template_file).unlink()


class TestConfidenceScoring:
    """Test confidence score handling in template population."""

    def test_confidence_indicators(self):
        """Test confidence indicators in formatted output."""
        # Create rules with different confidence levels
        high_confidence_rule = BusinessRule(
            rule_id="BR-HIGH",
            description="High confidence rule",
            constraint="test > 0",
            entities_involved=["Entity1"],
            confidence=0.95
        )

        medium_confidence_rule = BusinessRule(
            rule_id="BR-MED",
            description="Medium confidence rule",
            constraint="test > 0",
            entities_involved=["Entity1"],
            confidence=0.85
        )

        low_confidence_rule = BusinessRule(
            rule_id="BR-LOW",
            description="Low confidence rule",
            constraint="test > 0",
            entities_involved=["Entity1"],
            confidence=0.65
        )

        domain_model = DomainModel(
            entities=[],
            business_rules=[high_confidence_rule, medium_confidence_rule, low_confidence_rule],
            integration_points=[]
        )

        populator = TemplatePopulator("/tmp/test.md", domain_model)

        # Test formatting of different confidence levels
        high_formatted = populator._format_business_rule(high_confidence_rule)
        medium_formatted = populator._format_business_rule(medium_confidence_rule)
        low_formatted = populator._format_business_rule(low_confidence_rule)

        # Check that confidence indicators are different
        assert "HIGH" in high_formatted
        assert "MED" in medium_formatted
        assert "LOW" in low_formatted


if __name__ == "__main__":
    pytest.main([__file__])