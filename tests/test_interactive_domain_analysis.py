#!/usr/bin/env python3
"""
Unit tests for interactive_domain_analysis module.

Tests the interactive functionality, user preferences, and validation workflows.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call

# Import the modules under test
import sys
sys.path.append(str(Path(__file__).parent.parent / "src" / "specify_cli"))

from interactive_domain_analysis import (
    InteractiveDomainAnalyzer,
    UserPreferences
)
from domain_analysis import (
    BusinessEntity,
    BusinessRule,
    IntegrationPoint,
    EntityField,
    DomainModel
)


class TestUserPreferences:
    """Test cases for the UserPreferences class."""

    def test_user_preferences_creation(self):
        """Test UserPreferences creation and default values."""
        prefs = UserPreferences(
            entity_rename_mappings={"OldName": "NewName"},
            custom_business_rules=["Custom rule"],
            confidence_threshold=0.8,
            additional_integrations=[{"name": "API", "type": "rest"}],
            domain_type="financial"
        )

        assert prefs.entity_rename_mappings == {"OldName": "NewName"}
        assert prefs.custom_business_rules == ["Custom rule"]
        assert prefs.confidence_threshold == 0.8
        assert prefs.additional_integrations == [{"name": "API", "type": "rest"}]
        assert prefs.domain_type == "financial"


class TestInteractiveDomainAnalyzer:
    """Test cases for the InteractiveDomainAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_data_dir = Path(__file__).parent / "data" / "sample"
        self.analyzer = InteractiveDomainAnalyzer(
            str(self.test_data_dir),
            interactive_mode=False  # Disable interactive mode for testing
        )

    def test_init_non_interactive(self):
        """Test InteractiveDomainAnalyzer initialization in non-interactive mode."""
        analyzer = InteractiveDomainAnalyzer(str(self.test_data_dir), interactive_mode=False)

        assert analyzer.data_directory == self.test_data_dir
        assert analyzer.interactive_mode is False
        assert analyzer.config_file is None
        assert isinstance(analyzer.user_preferences, UserPreferences)

    def test_init_with_config_file(self):
        """Test initialization with configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
domain_type: financial
entities:
  patterns:
    Invoice: [invoice, bill]
settings:
  confidence_threshold: 0.85
""")
            config_file = Path(f.name)

        try:
            analyzer = InteractiveDomainAnalyzer(
                str(self.test_data_dir),
                config_file=str(config_file)
            )
            assert analyzer.config_file == str(config_file)
        finally:
            config_file.unlink()

    def test_apply_user_preferences(self):
        """Test application of user preferences to domain model."""
        # Create test domain model
        entities = [
            BusinessEntity(name="Invoice", description="Test invoice", fields=[], confidence=0.9),
            BusinessEntity(name="Payment", description="Test payment", fields=[], confidence=0.5)
        ]
        rules = [
            BusinessRule(rule_id="BR-001", description="High confidence rule",
                        constraint="x > 0", entities_involved=["Invoice"], confidence=0.9),
            BusinessRule(rule_id="BR-002", description="Low confidence rule",
                        constraint="y > 0", entities_involved=["Payment"], confidence=0.4)
        ]

        domain_model = DomainModel(entities=entities, business_rules=rules, integration_points=[])
        self.analyzer.domain_model = domain_model

        # Set user preferences
        self.analyzer.user_preferences.entity_rename_mappings = {"Invoice": "InvoiceDocument"}
        self.analyzer.user_preferences.confidence_threshold = 0.6

        # Apply preferences
        updated_model = self.analyzer._apply_user_preferences()

        # Check entity renaming
        entity_names = [e.name for e in updated_model.entities]
        assert "InvoiceDocument" in entity_names
        assert "Invoice" not in entity_names

        # Check confidence filtering
        assert len(updated_model.business_rules) == 1  # Only high confidence rule should remain
        assert updated_model.business_rules[0].rule_id == "BR-001"

    @patch('builtins.input')
    def test_validate_entity_interactive(self, mock_input):
        """Test interactive entity validation."""
        # Mock user inputs
        mock_input.side_effect = ['1']  # Accept entity as-is

        entity = BusinessEntity(
            name="TestEntity",
            description="Test description",
            fields=[EntityField(name="id", field_type="string", is_key=True)],
            confidence=0.85
        )

        # Test validation (should not modify entity)
        result = self.analyzer._validate_entity_interactive(entity)
        assert result == entity

    @patch('builtins.input')
    def test_add_entity_interactive(self, mock_input):
        """Test interactive entity addition."""
        # Mock user inputs for new entity
        mock_input.side_effect = [
            'CustomEntity',     # Entity name
            'Custom description',  # Description
            'field1,string,key',   # First field
            'field2,integer,',     # Second field
            '',                    # End field input
        ]

        self.analyzer.domain_model = DomainModel(entities=[], business_rules=[], integration_points=[])

        # Test adding entity
        self.analyzer._add_entity_interactive()

        # Check that entity was added
        assert len(self.analyzer.domain_model.entities) == 1
        entity = self.analyzer.domain_model.entities[0]
        assert entity.name == "CustomEntity"
        assert entity.description == "Custom description"
        assert len(entity.fields) == 2

    @patch('builtins.input')
    def test_validate_business_rule_interactive(self, mock_input):
        """Test interactive business rule validation."""
        # Mock user inputs
        mock_input.side_effect = ['1']  # Accept rule as-is

        rule = BusinessRule(
            rule_id="BR-001",
            description="Test rule",
            constraint="amount > 0",
            entities_involved=["Entity1"],
            confidence=0.8
        )

        # Test validation (should not modify rule)
        result = self.analyzer._validate_business_rule_interactive(rule)
        assert result == rule

    @patch('builtins.input')
    def test_add_custom_rule_interactive(self, mock_input):
        """Test interactive custom rule addition."""
        # Mock user inputs
        mock_input.side_effect = [
            'Custom validation rule',  # Rule description
            '1,2',                     # Entity selection (assuming 2 entities)
        ]

        # Set up entities
        entities = [
            BusinessEntity(name="Entity1", description="Test 1", fields=[], confidence=0.8),
            BusinessEntity(name="Entity2", description="Test 2", fields=[], confidence=0.8),
        ]
        self.analyzer.domain_model = DomainModel(entities=entities, business_rules=[], integration_points=[])

        # Test adding custom rule
        self.analyzer._add_custom_rule_interactive()

        # Check that rule was added
        assert len(self.analyzer.domain_model.business_rules) == 1
        rule = self.analyzer.domain_model.business_rules[0]
        assert "Custom validation rule" in rule.description
        assert len(rule.entities_involved) == 2

    @patch('builtins.input')
    def test_adjust_confidence_threshold_interactive(self, mock_input):
        """Test interactive confidence threshold adjustment."""
        # Mock user input
        mock_input.side_effect = ['0.85']  # New threshold

        self.analyzer._adjust_confidence_threshold_interactive()

        assert self.analyzer.user_preferences.confidence_threshold == 0.85

    @patch('builtins.input')
    def test_validate_integration_interactive(self, mock_input):
        """Test interactive integration point validation."""
        # Mock user inputs
        mock_input.side_effect = ['1']  # Accept integration as-is

        integration = IntegrationPoint(
            name="TestAPI",
            integration_type="api",
            description="Test API integration",
            data_flow="bidirectional",
            format="JSON"
        )

        # Test validation (should not modify integration)
        result = self.analyzer._validate_integration_interactive(integration)
        assert result == integration

    @patch('builtins.input')
    def test_add_integration_interactive(self, mock_input):
        """Test interactive integration point addition."""
        # Mock user inputs
        mock_input.side_effect = [
            'CustomAPI',        # System name
            '1',               # Type: API
            '2',               # Data flow: Output
            'XML',             # Format
            'Custom API integration'  # Description
        ]

        self.analyzer.domain_model = DomainModel(entities=[], business_rules=[], integration_points=[])

        # Test adding integration
        self.analyzer._add_integration_interactive()

        # Check that integration was added
        assert len(self.analyzer.domain_model.integration_points) == 1
        integration = self.analyzer.domain_model.integration_points[0]
        assert integration.name == "CustomAPI"
        assert integration.type == "api"
        assert integration.format == "XML"

    def test_load_config_missing_file(self):
        """Test loading non-existent configuration file."""
        analyzer = InteractiveDomainAnalyzer(
            str(self.test_data_dir),
            config_file="/nonexistent/config.yaml"
        )
        # Should not raise exception, just use defaults
        assert analyzer.user_preferences.domain_type == "custom"

    @patch('builtins.input')
    def test_save_preferences(self, mock_input):
        """Test saving user preferences to file."""
        # Mock user input for save confirmation
        mock_input.side_effect = ['y']  # Yes, save preferences

        # Set some preferences
        self.analyzer.user_preferences.domain_type = "financial"
        self.analyzer.user_preferences.confidence_threshold = 0.8

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test-config.yaml"

            # Test saving preferences
            self.analyzer._save_preferences(str(config_path))

            # Check that file was created
            assert config_path.exists()

            # Check file content
            import yaml
            with open(config_path, 'r') as f:
                saved_config = yaml.safe_load(f)

            assert saved_config['domain_type'] == "financial"
            assert saved_config['confidence_threshold'] == 0.8

    def test_analyze_non_interactive_mode(self):
        """Test analyze method in non-interactive mode."""
        analyzer = InteractiveDomainAnalyzer(str(self.test_data_dir), interactive_mode=False)
        domain_model = analyzer.analyze()

        # Should behave like regular domain analyzer
        assert isinstance(domain_model, DomainModel)
        assert len(domain_model.entities) > 0

    @patch('builtins.input')
    def test_analyze_interactive_mode_accept_all(self, mock_input):
        """Test analyze method in interactive mode with user accepting all."""
        # Mock user inputs to accept everything
        mock_input.side_effect = ['4', '5', '3']  # Accept all entities, rules, integrations

        analyzer = InteractiveDomainAnalyzer(str(self.test_data_dir), interactive_mode=True)
        domain_model = analyzer.analyze()

        assert isinstance(domain_model, DomainModel)
        assert len(domain_model.entities) > 0


class TestErrorHandling:
    """Test error handling in interactive scenarios."""

    def test_invalid_input_handling(self):
        """Test handling of invalid user inputs."""
        analyzer = InteractiveDomainAnalyzer("/tmp", interactive_mode=False)

        # Test invalid confidence threshold
        analyzer.user_preferences.confidence_threshold = 1.5  # Invalid (> 1.0)
        analyzer._apply_user_preferences()
        # Should handle gracefully without crashing

    @patch('builtins.input')
    def test_empty_input_handling(self, mock_input):
        """Test handling of empty user inputs."""
        mock_input.side_effect = ['', '', '1']  # Empty inputs followed by valid

        analyzer = InteractiveDomainAnalyzer("/tmp", interactive_mode=False)

        # Should handle empty inputs gracefully
        # This would be tested with actual interactive methods


class TestConfigurationManagement:
    """Test configuration file management."""

    def test_yaml_config_parsing(self):
        """Test YAML configuration file parsing."""
        config_content = """
domain_type: financial
entities:
  patterns:
    Invoice: [invoice, bill, statement]
    Payment: [payment, remittance]
business_rules:
  templates:
    - "Payments must reference valid invoices"
  custom_rules:
    - "Custom validation rule"
settings:
  confidence_threshold: 0.75
  default_interactive: true
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = Path(f.name)

        try:
            analyzer = InteractiveDomainAnalyzer(
                "/tmp",
                config_file=str(config_file)
            )

            # Check that configuration was loaded
            assert analyzer.user_preferences.domain_type == "financial"
            assert analyzer.user_preferences.confidence_threshold == 0.75
        finally:
            config_file.unlink()

    def test_invalid_yaml_config(self):
        """Test handling of invalid YAML configuration."""
        invalid_config = """
domain_type: financial
entities:
  patterns:
    Invoice: [invoice
    # Invalid YAML - missing closing bracket
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_config)
            config_file = Path(f.name)

        try:
            # Should not crash, should use defaults
            analyzer = InteractiveDomainAnalyzer(
                "/tmp",
                config_file=str(config_file)
            )
            assert analyzer.user_preferences.domain_type == "custom"  # Default value
        finally:
            config_file.unlink()


# Test fixtures and utilities
@pytest.fixture
def mock_domain_model():
    """Fixture providing a mock domain model for testing."""
    entities = [
        BusinessEntity(
            name="Invoice",
            description="Invoice entity",
            fields=[
                EntityField(name="invoice_id", field_type="string", is_key=True),
                EntityField(name="amount", field_type="float", is_key=False)
            ],
            confidence=0.9
        ),
        BusinessEntity(
            name="Payment",
            description="Payment entity",
            fields=[
                EntityField(name="payment_id", field_type="string", is_key=True),
                EntityField(name="amount", field_type="float", is_key=False)
            ],
            confidence=0.8
        )
    ]

    rules = [
        BusinessRule(
            rule_id="BR-001",
            description="Payment amount validation",
            constraint="payment.amount <= invoice.amount",
            entities_involved=["Payment", "Invoice"],
            confidence=0.85
        )
    ]

    integrations = [
        IntegrationPoint(
            name="Payment Gateway",
            integration_type="api",
            description="External payment processing",
            data_flow="bidirectional",
            format="JSON"
        )
    ]

    return DomainModel(entities=entities, business_rules=rules, integration_points=integrations)


def test_full_interactive_workflow_simulation(mock_domain_model):
    """Test simulation of full interactive workflow."""
    analyzer = InteractiveDomainAnalyzer("/tmp", interactive_mode=False)
    analyzer.domain_model = mock_domain_model

    # Apply some user preferences
    analyzer.user_preferences.confidence_threshold = 0.8
    analyzer.user_preferences.entity_rename_mappings = {"Invoice": "InvoiceDocument"}

    # Apply preferences
    result_model = analyzer._apply_user_preferences()

    # Verify results
    assert len(result_model.entities) == 2
    entity_names = [e.name for e in result_model.entities]
    assert "InvoiceDocument" in entity_names
    assert "Payment" in entity_names

    # Business rules should be filtered by confidence
    assert len(result_model.business_rules) == 1
    assert result_model.business_rules[0].confidence >= 0.8


if __name__ == "__main__":
    pytest.main([__file__])