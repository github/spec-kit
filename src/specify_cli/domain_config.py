#!/usr/bin/env python3
"""
Domain Configuration System for Spec-Kit

Manages configuration files, templates, and setup wizards for domain analysis customization.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

try:
    from .error_handling import get_error_handler, safe_file_operation
except ImportError:
    # Handle running as standalone script
    from error_handling import get_error_handler, safe_file_operation


@dataclass
class DomainTemplate:
    """Template for domain-specific analysis configurations."""
    name: str
    description: str
    entity_patterns: Dict[str, List[str]]
    business_rule_templates: List[str]
    integration_patterns: List[Dict[str, str]]
    confidence_threshold: float


class DomainConfigManager:
    """Manages domain analysis configuration files and templates."""

    def __init__(self, config_dir: str = ".specify"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "domain-config.yaml"
        self.error_handler = get_error_handler()

        # Built-in domain templates
        self.templates = {
            'financial': DomainTemplate(
                name='Financial/Accounting',
                description='Invoice reconciliation, payments, financial transactions',
                entity_patterns={
                    'Invoice': ['invoice', 'bill', 'statement'],
                    'Payment': ['payment', 'unallocated', 'receipt', 'remittance'],
                    'Supplier': ['supplier', 'vendor', 'creditor'],
                    'Customer': ['customer', 'debtor', 'client'],
                    'Transaction': ['transaction', 'journal', 'ledger'],
                    'Reconciliation': ['reconcil', 'match', 'allocation']
                },
                business_rule_templates=[
                    'Payments can only be matched to invoices from the same supplier',
                    'Payment amount must not exceed invoice amount by more than {tolerance}%',
                    'Date proximity matching within ±{days} days',
                    'Matching confidence must be ≥{threshold}% to be considered valid',
                    'Once payment is fully allocated, it cannot be re-matched unless reset'
                ],
                integration_patterns=[
                    {'name': 'ERP System', 'type': 'api', 'flow': 'bidirectional'},
                    {'name': 'Bank Feeds', 'type': 'file_system', 'flow': 'input'},
                    {'name': 'Reporting Database', 'type': 'database', 'flow': 'output'}
                ],
                confidence_threshold=0.75
            ),

            'ecommerce': DomainTemplate(
                name='E-commerce/Retail',
                description='Orders, products, customers, inventory management',
                entity_patterns={
                    'Order': ['order', 'purchase', 'sale'],
                    'Product': ['product', 'item', 'sku', 'inventory'],
                    'Customer': ['customer', 'buyer', 'user'],
                    'Payment': ['payment', 'transaction', 'charge'],
                    'Shipment': ['shipment', 'delivery', 'fulfillment'],
                    'Return': ['return', 'refund', 'exchange']
                },
                business_rule_templates=[
                    'Orders must have at least one product line item',
                    'Product inventory must be sufficient before order confirmation',
                    'Payment must be authorized before order processing',
                    'Shipped orders cannot be cancelled',
                    'Returns require original order reference'
                ],
                integration_patterns=[
                    {'name': 'Payment Gateway', 'type': 'api', 'flow': 'bidirectional'},
                    {'name': 'Inventory System', 'type': 'database', 'flow': 'bidirectional'},
                    {'name': 'Shipping Service', 'type': 'api', 'flow': 'output'}
                ],
                confidence_threshold=0.8
            ),

            'crm': DomainTemplate(
                name='CRM/Sales',
                description='Contacts, leads, opportunities, sales pipeline',
                entity_patterns={
                    'Contact': ['contact', 'person', 'individual'],
                    'Lead': ['lead', 'prospect', 'inquiry'],
                    'Opportunity': ['opportunity', 'deal', 'sale'],
                    'Account': ['account', 'company', 'organization'],
                    'Activity': ['activity', 'task', 'interaction'],
                    'Campaign': ['campaign', 'marketing', 'promotion']
                },
                business_rule_templates=[
                    'Leads must be qualified before becoming opportunities',
                    'Opportunities must have associated contact and account',
                    'Activities must be linked to contacts or opportunities',
                    'Pipeline stages must follow defined progression',
                    'Closed opportunities cannot be modified without approval'
                ],
                integration_patterns=[
                    {'name': 'Email System', 'type': 'api', 'flow': 'bidirectional'},
                    {'name': 'Marketing Automation', 'type': 'api', 'flow': 'input'},
                    {'name': 'Analytics Platform', 'type': 'api', 'flow': 'output'}
                ],
                confidence_threshold=0.7
            )
        }

    def run_setup_wizard(self) -> Dict[str, Any]:
        """Run interactive setup wizard to create domain configuration."""
        print("Domain Analysis Setup Wizard")
        print("=" * 40)
        print("\nThis wizard will help configure domain analysis for your specific use case.\n")

        # Step 1: Domain Type Selection
        domain_type = self._select_domain_type()

        # Step 2: Entity Customization
        entities = self._customize_entities(domain_type)

        # Step 3: Business Rules
        business_rules = self._customize_business_rules(domain_type)

        # Step 4: Integration Points
        integrations = self._customize_integrations(domain_type)

        # Step 5: Configuration Settings
        settings = self._configure_settings(domain_type)

        # Create configuration
        config = {
            'domain_type': domain_type,
            'entities': entities,
            'business_rules': business_rules,
            'integrations': integrations,
            'settings': settings,
            'created_by': 'setup_wizard',
            'version': '1.0'
        }

        # Save configuration
        self._save_config(config)

        print(f"\nConfiguration saved to {self.config_file}")
        print("Run '/analyze-domain' to apply these preferences.")

        return config

    def _select_domain_type(self) -> str:
        """Interactive domain type selection."""
        print("Step 1/5: What type of system are you building?\n")

        template_list = list(self.templates.items())
        for i, (key, template) in enumerate(template_list, 1):
            print(f"{i}. {template.name}")
            print(f"   {template.description}")

        print(f"{len(template_list) + 1}. Custom (I'll define my own patterns)")

        while True:
            try:
                choice = int(input(f"\nChoose option (1-{len(template_list) + 1}): "))
                if 1 <= choice <= len(template_list):
                    selected_key = template_list[choice - 1][0]
                    selected_template = self.templates[selected_key]
                    print(f"Selected: {selected_template.name}")
                    return selected_key
                elif choice == len(template_list) + 1:
                    print("Selected: Custom domain")
                    return 'custom'
                else:
                    print("Invalid choice. Please select from the available options.")
            except ValueError:
                print("Please enter a valid number.")

    def _customize_entities(self, domain_type: str) -> Dict[str, Any]:
        """Interactive entity customization."""
        print(f"\nStep 2/5: Entity Configuration\n")

        if domain_type != 'custom':
            template = self.templates[domain_type]
            print("Suggested entities for your domain:")
            for i, (entity, patterns) in enumerate(template.entity_patterns.items(), 1):
                print(f"  {i}. {entity} (patterns: {', '.join(patterns)})")

            use_suggested = input(f"\nUse suggested entities? (Y/n): ").strip().lower()
            if use_suggested != 'n':
                return {'patterns': template.entity_patterns, 'custom_entities': []}

        # Custom entity configuration
        print("Define your entities:")
        custom_entities = {}
        custom_list = []

        while True:
            entity_name = input("Entity name (or press enter to finish): ").strip()
            if not entity_name:
                break

            patterns_input = input(f"File name patterns for {entity_name} (comma-separated): ").strip()
            patterns = [p.strip() for p in patterns_input.split(',') if p.strip()]

            if patterns:
                custom_entities[entity_name] = patterns
                custom_list.append({'name': entity_name, 'patterns': patterns})

        return {'patterns': custom_entities, 'custom_entities': custom_list}

    def _customize_business_rules(self, domain_type: str) -> Dict[str, Any]:
        """Interactive business rules customization."""
        print(f"\nStep 3/5: Business Rules Configuration\n")

        rules_config = {'templates': [], 'custom_rules': []}

        if domain_type != 'custom':
            template = self.templates[domain_type]
            print("Suggested business rule templates:")
            for i, rule_template in enumerate(template.business_rule_templates, 1):
                print(f"  {i}. {rule_template}")

            use_suggested = input(f"\nUse suggested rule templates? (Y/n): ").strip().lower()
            if use_suggested != 'n':
                rules_config['templates'] = template.business_rule_templates

        # Custom rules
        print("\nAdd custom business rules:")
        while True:
            custom_rule = input("Custom business rule (or press enter to finish): ").strip()
            if not custom_rule:
                break
            rules_config['custom_rules'].append(custom_rule)

        return rules_config

    def _customize_integrations(self, domain_type: str) -> Dict[str, Any]:
        """Interactive integration points customization."""
        print(f"\nStep 4/5: Integration Points Configuration\n")

        integrations_config = {'templates': [], 'custom_integrations': []}

        if domain_type != 'custom':
            template = self.templates[domain_type]
            print("Suggested integration patterns:")
            for i, integration in enumerate(template.integration_patterns, 1):
                print(f"  {i}. {integration['name']} ({integration['type']} - {integration['flow']})")

            use_suggested = input(f"\nUse suggested integrations? (Y/n): ").strip().lower()
            if use_suggested != 'n':
                integrations_config['templates'] = template.integration_patterns

        # Custom integrations
        print("\nAdd custom integration points:")
        while True:
            system_name = input("System name (or press enter to finish): ").strip()
            if not system_name:
                break

            system_type = input("Type (api/database/file_system/service): ").strip()
            if not system_type:
                system_type = 'api'

            data_flow = input("Data flow (input/output/bidirectional): ").strip()
            if not data_flow:
                data_flow = 'bidirectional'

            integrations_config['custom_integrations'].append({
                'name': system_name,
                'type': system_type,
                'flow': data_flow
            })

        return integrations_config

    def _configure_settings(self, domain_type: str) -> Dict[str, Any]:
        """Interactive settings configuration."""
        print(f"\nStep 5/5: Analysis Settings\n")

        settings = {}

        # Confidence threshold
        default_threshold = self.templates[domain_type].confidence_threshold if domain_type != 'custom' else 0.75
        threshold_input = input(f"Confidence threshold for automatic matching (default {default_threshold:.0%}): ").strip()

        try:
            if threshold_input:
                threshold = float(threshold_input)
                if 0 <= threshold <= 1:
                    settings['confidence_threshold'] = threshold
                else:
                    settings['confidence_threshold'] = threshold / 100 if threshold > 1 else default_threshold
            else:
                settings['confidence_threshold'] = default_threshold
        except ValueError:
            settings['confidence_threshold'] = default_threshold

        # Interactive mode preference
        interactive_pref = input("Enable interactive mode by default? (Y/n): ").strip().lower()
        settings['default_interactive'] = interactive_pref != 'n'

        # Data directory preference
        data_dir = input("Default data directory (optional): ").strip()
        if data_dir:
            settings['default_data_dir'] = data_dir

        return settings

    def load_config(self) -> Optional[Dict[str, Any]]:
        """Load existing configuration file."""
        if not self.config_file.exists():
            return None

        def load_yaml():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)

        result = safe_file_operation("read", self.config_file, load_yaml)
        if result is None:
            self.error_handler.handle_configuration_error(self.config_file,
                Exception(f"Failed to load configuration from {self.config_file}"))
        return result

    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            self.config_dir.mkdir(exist_ok=True)
        except PermissionError as e:
            self.error_handler.handle_file_access_error(self.config_dir, "create directory", e)
            return

        def save_yaml():
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)

        result = safe_file_operation("write", self.config_file, save_yaml)
        if result is None:
            self.error_handler.handle_configuration_error(self.config_file,
                Exception(f"Failed to save configuration to {self.config_file}"))

    def get_template(self, domain_type: str) -> Optional[DomainTemplate]:
        """Get domain template by type."""
        return self.templates.get(domain_type)

    def list_templates(self) -> Dict[str, DomainTemplate]:
        """List all available domain templates."""
        return self.templates


def main():
    """Command-line interface for domain configuration."""
    import argparse

    parser = argparse.ArgumentParser(description="Domain configuration manager for spec-kit")
    parser.add_argument("--setup", action="store_true", help="Run setup wizard")
    parser.add_argument("--list-templates", action="store_true", help="List available domain templates")
    parser.add_argument("--config-dir", default=".specify", help="Configuration directory")

    args = parser.parse_args()

    config_manager = DomainConfigManager(args.config_dir)

    if args.setup:
        config_manager.run_setup_wizard()
    elif args.list_templates:
        print("Available domain templates:")
        for key, template in config_manager.templates.items():
            print(f"\n{key}: {template.name}")
            print(f"  {template.description}")
            print(f"  Entities: {', '.join(template.entity_patterns.keys())}")
            print(f"  Confidence threshold: {template.confidence_threshold:.0%}")
    else:
        # Show current configuration
        config = config_manager.load_config()
        if config:
            print("Current configuration:")
            print(yaml.dump(config, default_flow_style=False, indent=2))
        else:
            print("No configuration found. Run --setup to create one.")


if __name__ == '__main__':
    main()