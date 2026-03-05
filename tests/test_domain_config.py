#!/usr/bin/env python3
"""
Unit tests for domain_config module.

Tests the domain configuration management, setup wizard, and template functionality.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the modules under test
import sys
sys.path.append(str(Path(__file__).parent.parent / "src" / "specify_cli"))

from domain_config import (
    DomainConfigManager,
    DomainTemplate
)


class TestDomainTemplate:
    """Test cases for the DomainTemplate class."""

    def test_domain_template_creation(self):
        """Test DomainTemplate creation and attributes."""
        entity_patterns = {
            'Invoice': ['invoice', 'bill'],
            'Payment': ['payment', 'remittance']
        }
        business_rules = [
            'Payments must reference valid invoices',
            'Invoice amounts must be positive'
        ]
        integrations = [
            {'name': 'ERP System', 'type': 'api', 'flow': 'bidirectional'}
        ]

        template = DomainTemplate(
            name="Financial",
            description="Financial domain template",
            entity_patterns=entity_patterns,
            business_rule_templates=business_rules,
            integration_patterns=integrations,
            confidence_threshold=0.8
        )

        assert template.name == "Financial"
        assert template.description == "Financial domain template"
        assert template.entity_patterns == entity_patterns
        assert template.business_rule_templates == business_rules
        assert template.integration_patterns == integrations
        assert template.confidence_threshold == 0.8


class TestDomainConfigManager:
    """Test cases for the DomainConfigManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = DomainConfigManager(self.temp_dir)

    def test_init(self):
        """Test DomainConfigManager initialization."""
        assert self.config_manager.config_dir == Path(self.temp_dir)
        assert self.config_manager.config_file == Path(self.temp_dir) / "domain-config.yaml"
        assert len(self.config_manager.templates) >= 3  # financial, ecommerce, crm

    def test_built_in_templates(self):
        """Test built-in domain templates."""
        templates = self.config_manager.templates

        # Check financial template
        financial = templates['financial']
        assert financial.name == 'Financial/Accounting'
        assert 'Invoice' in financial.entity_patterns
        assert 'Payment' in financial.entity_patterns
        assert len(financial.business_rule_templates) > 0

        # Check ecommerce template
        ecommerce = templates['ecommerce']
        assert ecommerce.name == 'E-commerce/Retail'
        assert 'Order' in ecommerce.entity_patterns
        assert 'Product' in ecommerce.entity_patterns

        # Check CRM template
        crm = templates['crm']
        assert crm.name == 'CRM/Sales'
        assert 'Contact' in crm.entity_patterns
        assert 'Lead' in crm.entity_patterns

    def test_get_template(self):
        """Test getting domain template by type."""
        financial_template = self.config_manager.get_template('financial')
        assert financial_template is not None
        assert financial_template.name == 'Financial/Accounting'

        # Test non-existent template
        invalid_template = self.config_manager.get_template('nonexistent')
        assert invalid_template is None

    def test_list_templates(self):
        """Test listing all available templates."""
        templates = self.config_manager.list_templates()
        assert isinstance(templates, dict)
        assert 'financial' in templates
        assert 'ecommerce' in templates
        assert 'crm' in templates

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        config = {
            'domain_type': 'financial',
            'entities': {
                'patterns': {'Invoice': ['invoice', 'bill']},
                'custom_entities': []
            },
            'business_rules': {
                'templates': ['Test rule'],
                'custom_rules': []
            },
            'integrations': {
                'templates': [],
                'custom_integrations': []
            },
            'settings': {
                'confidence_threshold': 0.8,
                'default_interactive': True
            },
            'created_by': 'test',
            'version': '1.0'
        }

        # Save configuration
        self.config_manager._save_config(config)

        # Load configuration
        loaded_config = self.config_manager.load_config()

        assert loaded_config is not None
        assert loaded_config['domain_type'] == 'financial'
        assert loaded_config['entities']['patterns']['Invoice'] == ['invoice', 'bill']
        assert loaded_config['settings']['confidence_threshold'] == 0.8

    def test_load_config_missing_file(self):
        """Test loading configuration when file doesn't exist."""
        # Don't create config file
        loaded_config = self.config_manager.load_config()
        assert loaded_config is None

    def test_load_config_invalid_yaml(self):
        """Test loading configuration with invalid YAML."""
        # Create invalid YAML file
        config_file = self.config_manager.config_file
        config_file.parent.mkdir(exist_ok=True)

        with open(config_file, 'w') as f:
            f.write('invalid: yaml: content: [unclosed')

        loaded_config = self.config_manager.load_config()
        assert loaded_config is None

    @patch('builtins.input')
    def test_select_domain_type_predefined(self, mock_input):
        """Test domain type selection for predefined template."""
        # Mock user selecting financial domain (option 1)
        mock_input.side_effect = ['1']

        domain_type = self.config_manager._select_domain_type()
        assert domain_type == 'financial'

    @patch('builtins.input')
    def test_select_domain_type_custom(self, mock_input):
        """Test domain type selection for custom domain."""
        # Mock user selecting custom domain (option 4)
        mock_input.side_effect = ['4']

        domain_type = self.config_manager._select_domain_type()
        assert domain_type == 'custom'

    @patch('builtins.input')
    def test_select_domain_type_invalid_then_valid(self, mock_input):
        """Test domain type selection with invalid input followed by valid."""
        # Mock invalid input then valid selection
        mock_input.side_effect = ['invalid', '999', '1']

        domain_type = self.config_manager._select_domain_type()
        assert domain_type == 'financial'

    @patch('builtins.input')
    def test_customize_entities_use_suggested(self, mock_input):
        """Test entity customization using suggested entities."""
        # Mock user accepting suggested entities
        mock_input.side_effect = ['y']

        entities = self.config_manager._customize_entities('financial')

        assert 'patterns' in entities
        assert 'Invoice' in entities['patterns']
        assert 'Payment' in entities['patterns']
        assert entities['custom_entities'] == []

    @patch('builtins.input')
    def test_customize_entities_custom(self, mock_input):
        """Test entity customization with custom entities."""
        # Mock user creating custom entities
        mock_input.side_effect = [
            'n',                    # Don't use suggested
            'CustomEntity',         # Entity name
            'custom, entity',       # Patterns
            'AnotherEntity',        # Another entity
            'another, test',        # Patterns
            '',                     # End input
        ]

        entities = self.config_manager._customize_entities('financial')

        assert 'patterns' in entities
        assert 'CustomEntity' in entities['patterns']
        assert 'AnotherEntity' in entities['patterns']
        assert entities['patterns']['CustomEntity'] == ['custom', 'entity']
        assert len(entities['custom_entities']) == 2

    @patch('builtins.input')
    def test_customize_business_rules_use_suggested(self, mock_input):
        """Test business rules customization using suggested rules."""
        # Mock user accepting suggested rules
        mock_input.side_effect = ['y', '']  # Accept suggested, no custom rules

        rules = self.config_manager._customize_business_rules('financial')

        assert 'templates' in rules
        assert len(rules['templates']) > 0
        assert rules['custom_rules'] == []

    @patch('builtins.input')
    def test_customize_business_rules_custom(self, mock_input):
        """Test business rules customization with custom rules."""
        # Mock user adding custom rules
        mock_input.side_effect = [
            'n',                    # Don't use suggested
            'Custom rule 1',        # First custom rule
            'Custom rule 2',        # Second custom rule
            '',                     # End input
        ]

        rules = self.config_manager._customize_business_rules('financial')

        assert rules['templates'] == []
        assert len(rules['custom_rules']) == 2
        assert 'Custom rule 1' in rules['custom_rules']
        assert 'Custom rule 2' in rules['custom_rules']

    @patch('builtins.input')
    def test_customize_integrations_use_suggested(self, mock_input):
        """Test integration customization using suggested integrations."""
        # Mock user accepting suggested integrations
        mock_input.side_effect = ['y', '']  # Accept suggested, no custom integrations

        integrations = self.config_manager._customize_integrations('financial')

        assert 'templates' in integrations
        assert len(integrations['templates']) > 0
        assert integrations['custom_integrations'] == []

    @patch('builtins.input')
    def test_customize_integrations_custom(self, mock_input):
        """Test integration customization with custom integrations."""
        # Mock user adding custom integrations
        mock_input.side_effect = [
            'n',                    # Don't use suggested
            'Custom API',           # System name
            'api',                  # Type
            'bidirectional',        # Data flow
            'Another Service',      # Another system
            'database',             # Type
            'input',                # Data flow
            '',                     # End input
        ]

        integrations = self.config_manager._customize_integrations('financial')

        assert integrations['templates'] == []
        assert len(integrations['custom_integrations']) == 2

        custom_api = integrations['custom_integrations'][0]
        assert custom_api['name'] == 'Custom API'
        assert custom_api['type'] == 'api'
        assert custom_api['flow'] == 'bidirectional'

    @patch('builtins.input')
    def test_configure_settings(self, mock_input):
        """Test settings configuration."""
        # Mock user inputs for settings
        mock_input.side_effect = [
            '0.85',                 # Confidence threshold
            'y',                    # Enable interactive mode
            '/custom/data',         # Data directory
        ]

        settings = self.config_manager._configure_settings('financial')

        assert settings['confidence_threshold'] == 0.85
        assert settings['default_interactive'] is True
        assert settings['default_data_dir'] == '/custom/data'

    @patch('builtins.input')
    def test_configure_settings_defaults(self, mock_input):
        """Test settings configuration with default values."""
        # Mock user pressing enter for all defaults
        mock_input.side_effect = ['', 'n', '']

        settings = self.config_manager._configure_settings('financial')

        assert settings['confidence_threshold'] == 0.75  # Default for financial
        assert settings['default_interactive'] is False
        assert 'default_data_dir' not in settings

    @patch('builtins.input')
    def test_run_setup_wizard_complete(self, mock_input):
        """Test complete setup wizard workflow."""
        # Mock user inputs for complete wizard
        mock_input.side_effect = [
            '1',                    # Select financial domain
            'y',                    # Use suggested entities
            'y',                    # Use suggested business rules
            '',                     # No custom rules
            'y',                    # Use suggested integrations
            '',                     # No custom integrations
            '',                     # Default confidence threshold
            'y',                    # Enable interactive mode
            '',                     # No custom data directory
        ]

        config = self.config_manager.run_setup_wizard()

        assert config['domain_type'] == 'financial'
        assert config['created_by'] == 'setup_wizard'
        assert config['version'] == '1.0'
        assert 'entities' in config
        assert 'business_rules' in config
        assert 'integrations' in config
        assert 'settings' in config

        # Check that config file was created
        assert self.config_manager.config_file.exists()


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_config_manager_with_readonly_directory(self):
        """Test config manager with read-only directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Make directory read-only
            import os
            os.chmod(temp_dir, 0o444)

            try:
                config_manager = DomainConfigManager(temp_dir)
                config = {'test': 'value'}

                # This should handle the permission error gracefully
                try:
                    config_manager._save_config(config)
                except PermissionError:
                    # Expected behavior
                    pass
            finally:
                # Restore permissions for cleanup
                os.chmod(temp_dir, 0o755)

    def test_invalid_confidence_threshold_input(self):
        """Test handling of invalid confidence threshold input."""
        config_manager = DomainConfigManager("/tmp")

        with patch('builtins.input', side_effect=['invalid', '150', '0.8']):
            settings = config_manager._configure_settings('custom')
            assert settings['confidence_threshold'] == 0.8


class TestTemplateValidation:
    """Test domain template validation."""

    def test_financial_template_validation(self):
        """Test financial domain template structure."""
        config_manager = DomainConfigManager("/tmp")
        financial = config_manager.get_template('financial')

        # Check required entities
        required_entities = ['Invoice', 'Payment', 'Supplier']
        for entity in required_entities:
            assert entity in financial.entity_patterns
            assert len(financial.entity_patterns[entity]) > 0

        # Check business rules
        assert len(financial.business_rule_templates) > 0
        for rule in financial.business_rule_templates:
            assert isinstance(rule, str)
            assert len(rule) > 0

        # Check integration patterns
        assert len(financial.integration_patterns) > 0
        for integration in financial.integration_patterns:
            assert 'name' in integration
            assert 'type' in integration
            assert 'flow' in integration

    def test_ecommerce_template_validation(self):
        """Test e-commerce domain template structure."""
        config_manager = DomainConfigManager("/tmp")
        ecommerce = config_manager.get_template('ecommerce')

        # Check required entities
        required_entities = ['Order', 'Product', 'Customer']
        for entity in required_entities:
            assert entity in ecommerce.entity_patterns

        # Validate confidence threshold
        assert 0.0 <= ecommerce.confidence_threshold <= 1.0

    def test_crm_template_validation(self):
        """Test CRM domain template structure."""
        config_manager = DomainConfigManager("/tmp")
        crm = config_manager.get_template('crm')

        # Check required entities
        required_entities = ['Contact', 'Lead', 'Opportunity']
        for entity in required_entities:
            assert entity in crm.entity_patterns

        # Check template completeness
        assert len(crm.business_rule_templates) > 0
        assert len(crm.integration_patterns) > 0


if __name__ == "__main__":
    pytest.main([__file__])