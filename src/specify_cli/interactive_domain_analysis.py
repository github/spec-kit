#!/usr/bin/env python3
"""
Interactive Domain Analysis for Spec-Kit

Extends the automated domain analysis with user interaction capabilities
for validation, customization, and refinement of extracted domain models.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, replace

try:
    from .domain_analysis import DomainAnalyzer, DomainModel, BusinessEntity, BusinessRule, IntegrationPoint, EntityField
    from .error_handling import get_error_handler, safe_user_input
except ImportError:
    # Handle running as standalone script
    sys.path.append(str(Path(__file__).parent))
    from domain_analysis import DomainAnalyzer, DomainModel, BusinessEntity, BusinessRule, IntegrationPoint, EntityField
    from error_handling import get_error_handler, safe_user_input


@dataclass
class UserPreferences:
    """User preferences for domain analysis customization."""
    entity_rename_mappings: Dict[str, str]
    custom_business_rules: List[str]
    confidence_threshold: float
    additional_integrations: List[Dict[str, str]]
    domain_type: str  # financial, ecommerce, crm, custom


class InteractiveDomainAnalyzer(DomainAnalyzer):
    """Interactive version of domain analyzer with user validation and customization."""

    def __init__(self, data_directory: str, interactive_mode: bool = True, config_file: Optional[str] = None):
        super().__init__(data_directory)
        self.interactive_mode = interactive_mode
        self.config_file = config_file
        self.error_handler = get_error_handler()
        self.user_preferences = UserPreferences(
            entity_rename_mappings={},
            custom_business_rules=[],
            confidence_threshold=0.6,
            additional_integrations=[],
            domain_type="custom"
        )
        self._load_config_if_provided()

    def analyze(self) -> DomainModel:
        """Perform interactive domain analysis with user validation."""
        print(f"Starting interactive domain analysis in: {self.data_directory}")

        # Step 1: Automated analysis
        super().analyze()

        # Step 2: Interactive validation and customization
        if self.interactive_mode:
            self._interactive_entity_validation()
            self._interactive_business_rule_validation()
            self._interactive_integration_validation()

        # Step 3: Apply user preferences
        self._apply_user_preferences()

        # Step 4: Save preferences for future use
        self._save_preferences_if_requested()

        return self.domain_model

    def _interactive_entity_validation(self):
        """Interactive validation and customization of discovered entities."""
        print("\n" + "="*50)
        print("ENTITY VALIDATION")
        print("="*50)

        print(f"\nDiscovered {len(self.domain_model.entities)} entities:")
        for i, entity in enumerate(self.domain_model.entities, 1):
            print(f"  {i}. {entity.name} ({len(entity.fields)} fields)")
            print(f"     {entity.description}")

        while True:
            print("\nEntity validation options:")
            print("1. Accept all entities as-is")
            print("2. Rename an entity")
            print("3. Remove an entity")
            print("4. Add a new entity")
            print("5. View entity details")

            choice = input("\nChoose option (1-5): ").strip()

            if choice == '1':
                print("All entities accepted")
                break
            elif choice == '2':
                self._rename_entity_interactive()
            elif choice == '3':
                self._remove_entity_interactive()
            elif choice == '4':
                self._add_entity_interactive()
            elif choice == '5':
                self._view_entity_details()
            else:
                print("Invalid choice. Please select 1-5.")

    def _rename_entity_interactive(self):
        """Interactive entity renaming."""
        if not self.domain_model.entities:
            print("No entities to rename.")
            return

        print("\nAvailable entities:")
        for i, entity in enumerate(self.domain_model.entities, 1):
            print(f"  {i}. {entity.name}")

        try:
            entity_num = int(input("Which entity to rename (number): ")) - 1
            if 0 <= entity_num < len(self.domain_model.entities):
                old_name = self.domain_model.entities[entity_num].name
                new_name = input(f"New name for '{old_name}': ").strip()

                if new_name and new_name != old_name:
                    self.domain_model.entities[entity_num].name = new_name
                    self.user_preferences.entity_rename_mappings[old_name] = new_name
                    print(f"Renamed '{old_name}' to '{new_name}'")
                else:
                    print("Invalid name or no change")
            else:
                print("Invalid entity number")
        except ValueError:
            print("Please enter a valid number")

    def _remove_entity_interactive(self):
        """Interactive entity removal."""
        if not self.domain_model.entities:
            print("No entities to remove.")
            return

        print("\nAvailable entities:")
        for i, entity in enumerate(self.domain_model.entities, 1):
            print(f"  {i}. {entity.name}")

        try:
            entity_num = int(input("Which entity to remove (number): ")) - 1
            if 0 <= entity_num < len(self.domain_model.entities):
                entity_name = self.domain_model.entities[entity_num].name
                confirm = input(f"Really remove '{entity_name}'? (y/N): ").strip().lower()

                if confirm == 'y':
                    removed_entity = self.domain_model.entities.pop(entity_num)
                    print(f"Removed entity '{removed_entity.name}'")
                else:
                    print("Entity removal cancelled")
            else:
                print("Invalid entity number")
        except ValueError:
            print("Please enter a valid number")

    def _add_entity_interactive(self):
        """Interactive entity addition."""
        print("\nAdding new entity:")
        name = input("Entity name: ").strip()
        description = input("Entity description: ").strip()

        if not name:
            print("Error: Entity name is required")
            return

        # Create basic entity
        new_entity = BusinessEntity(
            name=name,
            description=description if description else f"User-defined {name} entity",
            fields=[],
            source_files=[],
            relationships=[]
        )

        # Ask for basic fields
        print("\nAdd fields (press enter with empty name to finish):")
        while True:
            field_name = input("  Field name: ").strip()
            if not field_name:
                break

            field_type = input(f"  Field type for '{field_name}' (string/integer/decimal/date): ").strip()
            if not field_type:
                field_type = "string"

            is_key = input(f"  Is '{field_name}' a key field? (y/N): ").strip().lower() == 'y'

            field = EntityField(
                name=field_name,
                data_type=field_type,
                is_key=is_key
            )
            new_entity.fields.append(field)

        self.domain_model.entities.append(new_entity)
        print(f"Added entity '{name}' with {len(new_entity.fields)} fields")

    def _view_entity_details(self):
        """View detailed information about entities."""
        if not self.domain_model.entities:
            print("No entities to view.")
            return

        print("\nAvailable entities:")
        for i, entity in enumerate(self.domain_model.entities, 1):
            print(f"  {i}. {entity.name}")

        try:
            entity_num = int(input("Which entity to view (number): ")) - 1
            if 0 <= entity_num < len(self.domain_model.entities):
                entity = self.domain_model.entities[entity_num]
                print(f"\n--- {entity.name} Details ---")
                print(f"Description: {entity.description}")
                print(f"Source files: {', '.join(entity.source_files) if entity.source_files else 'None'}")
                print(f"Fields ({len(entity.fields)}):")
                for field in entity.fields:
                    key_indicator = " [KEY]" if field.is_key else ""
                    print(f"  - {field.name}: {field.data_type}{key_indicator}")
            else:
                print("Invalid entity number")
        except ValueError:
            print("Please enter a valid number")

    def _interactive_business_rule_validation(self):
        """Interactive validation and customization of business rules."""
        print("\n" + "="*50)
        print("📏 BUSINESS RULE VALIDATION")
        print("="*50)

        print(f"\nInferred {len(self.domain_model.business_rules)} business rules:")
        for i, rule in enumerate(self.domain_model.business_rules, 1):
            confidence_indicator = "HIGH" if rule.confidence >= 0.9 else "MED" if rule.confidence >= 0.8 else "LOW"
            print(f"  {i}. {rule.rule_id}: {rule.description}")
            print(f"     Confidence: {rule.confidence:.1%} {confidence_indicator}")
            print(f"     Applies to: {', '.join(rule.entities_involved)}")

        while True:
            print("\nBusiness rule validation options:")
            print("1. Accept all rules as-is")
            print("2. Modify a rule")
            print("3. Remove a rule")
            print("4. Add a custom rule")
            print("5. Set confidence threshold")

            choice = input("\nChoose option (1-5): ").strip()

            if choice == '1':
                print("All business rules accepted")
                break
            elif choice == '2':
                self._modify_rule_interactive()
            elif choice == '3':
                self._remove_rule_interactive()
            elif choice == '4':
                self._add_rule_interactive()
            elif choice == '5':
                self._set_confidence_threshold()
            else:
                print("Invalid choice. Please select 1-5.")

    def _modify_rule_interactive(self):
        """Interactive business rule modification."""
        if not self.domain_model.business_rules:
            print("No rules to modify.")
            return

        print("\nAvailable rules:")
        for i, rule in enumerate(self.domain_model.business_rules, 1):
            print(f"  {i}. {rule.rule_id}: {rule.description}")

        try:
            rule_num = int(input("Which rule to modify (number): ")) - 1
            if 0 <= rule_num < len(self.domain_model.business_rules):
                rule = self.domain_model.business_rules[rule_num]
                print(f"\nCurrent rule: {rule.description}")
                print(f"Current constraint: {rule.constraint}")

                new_description = input("New description (or press enter to keep current): ").strip()
                new_constraint = input("New constraint (or press enter to keep current): ").strip()

                if new_description:
                    rule.description = new_description
                if new_constraint:
                    rule.constraint = new_constraint

                print("Business rule updated")
            else:
                print("Error: Invalid rule number")
        except ValueError:
            print("Please enter a valid number")

    def _remove_rule_interactive(self):
        """Interactive business rule removal."""
        if not self.domain_model.business_rules:
            print("No rules to remove.")
            return

        print("\nAvailable rules:")
        for i, rule in enumerate(self.domain_model.business_rules, 1):
            print(f"  {i}. {rule.rule_id}: {rule.description}")

        try:
            rule_num = int(input("Which rule to remove (number): ")) - 1
            if 0 <= rule_num < len(self.domain_model.business_rules):
                rule = self.domain_model.business_rules[rule_num]
                confirm = input(f"Really remove rule '{rule.rule_id}'? (y/N): ").strip().lower()

                if confirm == 'y':
                    removed_rule = self.domain_model.business_rules.pop(rule_num)
                    print(f"Removed rule '{removed_rule.rule_id}'")
                else:
                    print("Rule removal cancelled")
            else:
                print("Error: Invalid rule number")
        except ValueError:
            print("Please enter a valid number")

    def _add_rule_interactive(self):
        """Interactive custom business rule addition."""
        print("\nAdding custom business rule:")
        description = input("Rule description: ").strip()
        constraint = input("Rule constraint: ").strip()

        if not description:
            print("Error: Rule description is required")
            return

        # Generate rule ID
        next_id = len(self.domain_model.business_rules) + 1
        rule_id = f"BR-{next_id:03d}"

        # Ask for entities involved
        print("\nWhich entities does this rule apply to?")
        entity_names = [entity.name for entity in self.domain_model.entities]
        if entity_names:
            print("Available entities:")
            for i, name in enumerate(entity_names, 1):
                print(f"  {i}. {name}")

            entity_input = input("Entity numbers (comma-separated, or enter for all): ").strip()
            entities_involved = []

            if entity_input:
                try:
                    entity_nums = [int(x.strip()) - 1 for x in entity_input.split(',')]
                    entities_involved = [entity_names[i] for i in entity_nums if 0 <= i < len(entity_names)]
                except ValueError:
                    print("Warning: Invalid entity numbers, applying to all entities")
                    entities_involved = entity_names
            else:
                entities_involved = entity_names
        else:
            entities_involved = []

        new_rule = BusinessRule(
            rule_id=rule_id,
            description=description,
            constraint=constraint if constraint else "User-defined constraint",
            confidence=1.0,  # User rules have full confidence
            evidence=["User-defined rule"],
            entities_involved=entities_involved
        )

        self.domain_model.business_rules.append(new_rule)
        self.user_preferences.custom_business_rules.append(description)
        print(f"Added custom rule '{rule_id}'")

    def _set_confidence_threshold(self):
        """Set confidence threshold for automatic matching."""
        current = self.user_preferences.confidence_threshold
        print(f"\nCurrent confidence threshold: {current:.1%}")

        try:
            new_threshold = float(input("New threshold (0.0 to 1.0): "))
            if 0.0 <= new_threshold <= 1.0:
                self.user_preferences.confidence_threshold = new_threshold
                print(f"Confidence threshold set to {new_threshold:.1%}")
            else:
                print("Error: Threshold must be between 0.0 and 1.0")
        except ValueError:
            print("Please enter a valid number")

    def _interactive_integration_validation(self):
        """Interactive validation and customization of integration points."""
        print("\n" + "="*50)
        print("🔌 INTEGRATION POINT VALIDATION")
        print("="*50)

        print(f"\nIdentified {len(self.domain_model.integration_points)} integration points:")
        for i, integration in enumerate(self.domain_model.integration_points, 1):
            print(f"  {i}. {integration.name} ({integration.type})")
            print(f"     {integration.description}")
            print(f"     Data flow: {integration.data_flow}")

        while True:
            print("\nIntegration point validation options:")
            print("1. Accept all integration points as-is")
            print("2. Add additional integration")
            print("3. Modify an integration")
            print("4. Remove an integration")

            choice = input("\nChoose option (1-4): ").strip()

            if choice == '1':
                print("All integration points accepted")
                break
            elif choice == '2':
                self._add_integration_interactive()
            elif choice == '3':
                self._modify_integration_interactive()
            elif choice == '4':
                self._remove_integration_interactive()
            else:
                print("Error: Invalid choice. Please select 1-4.")

    def _add_integration_interactive(self):
        """Interactive integration point addition."""
        print("\nAdding new integration point:")
        name = input("System name: ").strip()

        if not name:
            print("Error: System name is required")
            return

        print("Integration type:")
        print("1. API")
        print("2. Database")
        print("3. File System")
        print("4. Service")

        type_choice = input("Choose type (1-4): ").strip()
        type_mapping = {'1': 'api', '2': 'database', '3': 'file_system', '4': 'service'}
        integration_type = type_mapping.get(type_choice, 'api')

        description = input("Description: ").strip()

        print("Data flow:")
        print("1. Input (data comes into system)")
        print("2. Output (data goes out of system)")
        print("3. Bidirectional")

        flow_choice = input("Choose data flow (1-3): ").strip()
        flow_mapping = {'1': 'input', '2': 'output', '3': 'bidirectional'}
        data_flow = flow_mapping.get(flow_choice, 'bidirectional')

        format_type = input("Data format (e.g., JSON, XML, CSV): ").strip()

        new_integration = IntegrationPoint(
            name=name,
            type=integration_type,
            description=description if description else f"User-defined {name} integration",
            data_flow=data_flow,
            format=format_type if format_type else "JSON",
            dependencies=[]
        )

        self.domain_model.integration_points.append(new_integration)
        self.user_preferences.additional_integrations.append({
            'name': name,
            'type': integration_type,
            'description': new_integration.description,
            'data_flow': data_flow,
            'format': new_integration.format
        })

        print(f"Added integration point '{name}'")

    def _modify_integration_interactive(self):
        """Interactive integration point modification."""
        if not self.domain_model.integration_points:
            print("No integration points to modify.")
            return

        print("\nAvailable integration points:")
        for i, integration in enumerate(self.domain_model.integration_points, 1):
            print(f"  {i}. {integration.name} ({integration.type})")

        try:
            integration_num = int(input("Which integration to modify (number): ")) - 1
            if 0 <= integration_num < len(self.domain_model.integration_points):
                integration = self.domain_model.integration_points[integration_num]
                print(f"\nCurrent: {integration.name}")
                print(f"Description: {integration.description}")

                new_description = input("New description (or press enter to keep current): ").strip()
                if new_description:
                    integration.description = new_description
                    print("Integration point updated")
            else:
                print("Error: Invalid integration number")
        except ValueError:
            print("Please enter a valid number")

    def _remove_integration_interactive(self):
        """Interactive integration point removal."""
        if not self.domain_model.integration_points:
            print("No integration points to remove.")
            return

        print("\nAvailable integration points:")
        for i, integration in enumerate(self.domain_model.integration_points, 1):
            print(f"  {i}. {integration.name}")

        try:
            integration_num = int(input("Which integration to remove (number): ")) - 1
            if 0 <= integration_num < len(self.domain_model.integration_points):
                integration = self.domain_model.integration_points[integration_num]
                confirm = input(f"Really remove '{integration.name}'? (y/N): ").strip().lower()

                if confirm == 'y':
                    removed_integration = self.domain_model.integration_points.pop(integration_num)
                    print(f"Removed integration '{removed_integration.name}'")
                else:
                    print("Integration removal cancelled")
            else:
                print("Error: Invalid integration number")
        except ValueError:
            print("Please enter a valid number")

    def _apply_user_preferences(self):
        """Apply user preferences to the domain model."""
        print("\nApplying user preferences...")

        # Apply confidence threshold (filter low-confidence rules)
        original_rule_count = len(self.domain_model.business_rules)
        self.domain_model.business_rules = [
            rule for rule in self.domain_model.business_rules
            if rule.confidence >= self.user_preferences.confidence_threshold
        ]

        filtered_count = original_rule_count - len(self.domain_model.business_rules)
        if filtered_count > 0:
            print(f"  Filtered out {filtered_count} low-confidence rules")

        print("User preferences applied")

    def _load_config_if_provided(self):
        """Load configuration file if provided."""
        if not self.config_file:
            return

        config_path = Path(self.config_file)
        if not config_path.exists():
            print(f"Warning: Configuration file not found: {self.config_file}")
            return

        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)

            # Load preferences from config
            if 'entity_rename_mappings' in config_data:
                self.user_preferences.entity_rename_mappings = config_data['entity_rename_mappings']
            if 'confidence_threshold' in config_data:
                self.user_preferences.confidence_threshold = config_data['confidence_threshold']
            if 'domain_type' in config_data:
                self.user_preferences.domain_type = config_data['domain_type']

            print(f"📄 Loaded configuration from {self.config_file}")

        except Exception as e:
            self.error_handler.handle_configuration_error(
                Path(self.config_file) if self.config_file else None, e
            )

    def _save_preferences_if_requested(self):
        """Ask user if they want to save preferences for future use."""
        if not self.interactive_mode:
            return

        save_prefs = input("\nSave these preferences for future use? (y/N): ").strip().lower()

        if save_prefs == 'y':
            config_path = Path(".specify/domain-config.json")
            config_path.parent.mkdir(exist_ok=True)

            config_data = {
                'entity_rename_mappings': self.user_preferences.entity_rename_mappings,
                'confidence_threshold': self.user_preferences.confidence_threshold,
                'domain_type': self.user_preferences.domain_type,
                'custom_business_rules': self.user_preferences.custom_business_rules,
                'additional_integrations': self.user_preferences.additional_integrations
            }

            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)

            print(f"Preferences saved to {config_path}")
            print("Use --config=.specify/domain-config.json to load these preferences in future runs")


def main():
    """Command-line interface for interactive domain analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Interactive domain analysis for spec-kit")
    parser.add_argument("data_directory", help="Directory containing data files to analyze")
    parser.add_argument("--interactive", action="store_true", help="Enable interactive mode")
    parser.add_argument("--config", help="Configuration file with saved preferences")

    args = parser.parse_args()

    if not Path(args.data_directory).exists():
        print(f"Error: Directory '{args.data_directory}' does not exist")
        sys.exit(1)

    analyzer = InteractiveDomainAnalyzer(
        args.data_directory,
        interactive_mode=args.interactive,
        config_file=args.config
    )

    domain_model = analyzer.analyze()

    print("\n" + "="*50)
    print("INTERACTIVE DOMAIN ANALYSIS COMPLETE")
    print("="*50)

    print(f"\nFinal Results:")
    print(f"- Entities: {len(domain_model.entities)}")
    print(f"- Business rules: {len(domain_model.business_rules)}")
    print(f"- Integration points: {len(domain_model.integration_points)}")


if __name__ == '__main__':
    main()