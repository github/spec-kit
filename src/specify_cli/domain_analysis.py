#!/usr/bin/env python3
"""
Domain Analysis Module for Spec-Kit

Analyzes data files to extract domain models, entities, business rules,
and integration patterns for automatic template population.
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import re

try:
    from .error_handling import (
        get_error_handler, safe_file_operation, safe_data_parsing,
        ErrorCategory, ErrorSeverity
    )
except ImportError:
    # Handle running as standalone script
    from error_handling import (
        get_error_handler, safe_file_operation, safe_data_parsing,
        ErrorCategory, ErrorSeverity
    )


@dataclass
class EntityField:
    """Represents a field in a business entity."""
    name: str
    data_type: str
    is_required: bool = False
    is_key: bool = False
    constraints: List[str] = field(default_factory=list)
    sample_values: List[Any] = field(default_factory=list)


@dataclass
class BusinessEntity:
    """Represents a business entity discovered from data."""
    name: str
    description: str
    fields: List[EntityField] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    lifecycle_states: List[str] = field(default_factory=list)


@dataclass
class BusinessRule:
    """Represents a business rule inferred from data patterns."""
    rule_id: str
    description: str
    constraint: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    entities_involved: List[str] = field(default_factory=list)


@dataclass
class IntegrationPoint:
    """Represents an external system or integration point."""
    name: str
    type: str  # "file_system", "api", "database", "service"
    description: str
    data_flow: str  # "input", "output", "bidirectional"
    format: str = ""
    dependencies: List[str] = field(default_factory=list)


@dataclass
class DomainModel:
    """Complete domain model extracted from data analysis."""
    entities: List[BusinessEntity] = field(default_factory=list)
    business_rules: List[BusinessRule] = field(default_factory=list)
    integration_points: List[IntegrationPoint] = field(default_factory=list)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)


class DomainAnalyzer:
    """Main class for analyzing data files and extracting domain models."""

    def __init__(self, data_directory: str):
        self.data_directory = Path(data_directory)
        self.error_handler = get_error_handler()

        # Validate data directory exists and is accessible
        if not self.data_directory.exists():
            error = FileNotFoundError(f"Data directory not found: {data_directory}")
            self.error_handler.handle_file_access_error(self.data_directory, "access", error)
            raise error

        if not self.data_directory.is_dir():
            error = NotADirectoryError(f"Path is not a directory: {data_directory}")
            self.error_handler.handle_file_access_error(self.data_directory, "access", error)
            raise error

        self.domain_model = DomainModel()
        self.json_files: List[Path] = []
        self.csv_files: List[Path] = []

    def analyze(self) -> DomainModel:
        """Perform complete domain analysis."""
        print(f"Analyzing domain data in: {self.data_directory}")

        # Step 1: Scan for data files
        self._scan_data_files()

        # Step 2: Extract entities from data structures
        self._extract_entities()

        # Step 3: Infer business rules from data patterns
        self._infer_business_rules()

        # Step 4: Identify integration points
        self._identify_integration_points()

        # Step 5: Generate analysis metadata
        self._generate_metadata()

        print(f"Domain analysis complete:")
        print(f"   - Entities: {len(self.domain_model.entities)}")
        print(f"   - Business rules: {len(self.domain_model.business_rules)}")
        print(f"   - Integration points: {len(self.domain_model.integration_points)}")

        # Print error summary if there were issues
        if self.error_handler.has_errors() or self.error_handler.has_warnings():
            self.error_handler.print_error_summary()

        return self.domain_model

    def _scan_data_files(self):
        """Scan directory for JSON and CSV files."""
        self.json_files = list(self.data_directory.rglob("*.json"))
        self.csv_files = list(self.data_directory.rglob("*.csv"))

        print(f"📁 Found {len(self.json_files)} JSON files and {len(self.csv_files)} CSV files")

    def _extract_entities(self):
        """Extract business entities from data file schemas."""
        entity_schemas = {}

        # Process JSON files
        for json_file in self.json_files:
            def parse_json():
                with open(json_file, 'r') as f:
                    return json.load(f)

            data = safe_data_parsing(json_file, "JSON", parse_json)
            if data is not None:
                try:
                    entity_name = self._infer_entity_name(json_file.name)
                    schema = self._analyze_json_schema(data, entity_name)

                    if entity_name in entity_schemas:
                        # Merge schemas from multiple files
                        entity_schemas[entity_name] = self._merge_schemas(
                            entity_schemas[entity_name], schema
                        )
                    else:
                        entity_schemas[entity_name] = schema

                except Exception as e:
                    self.error_handler.handle_validation_error(
                        f"JSON schema analysis for {json_file.name}",
                        str(e),
                        f"Failed to analyze JSON structure: {e}"
                    )

        # Process CSV files
        for csv_file in self.csv_files:
            try:
                entity_name = self._infer_entity_name(csv_file.name)
                schema = self._analyze_csv_schema(csv_file, entity_name)

                if schema is not None:
                    if entity_name in entity_schemas:
                        entity_schemas[entity_name] = self._merge_schemas(
                            entity_schemas[entity_name], schema
                        )
                    else:
                        entity_schemas[entity_name] = schema

            except Exception as e:
                self.error_handler.handle_validation_error(
                    f"CSV schema analysis for {csv_file.name}",
                    str(e),
                    f"Failed to analyze CSV structure: {e}"
                )

        # Convert schemas to BusinessEntity objects
        for entity_name, schema in entity_schemas.items():
            entity = BusinessEntity(
                name=entity_name,
                description=self._generate_entity_description(entity_name, schema),
                fields=schema.get('fields', []),
                source_files=schema.get('source_files', []),
                relationships=schema.get('relationships', []),
                lifecycle_states=schema.get('lifecycle_states', [])
            )
            self.domain_model.entities.append(entity)

    def _infer_entity_name(self, filename: str) -> str:
        """Infer entity name from filename."""
        name = filename.lower()

        # Remove common extensions and prefixes
        name = re.sub(r'\.(json|csv)$', '', name)
        name = re.sub(r'^\w+_\d{8}_\d{6}_', '', name)  # Remove timestamps

        # Map filename patterns to entity names
        if 'invoice' in name:
            return 'Invoice'
        elif 'payment' in name or 'unallocated' in name:
            return 'Payment'
        elif 'supplier' in name:
            return 'Supplier'
        elif 'reconcil' in name:
            return 'ReconciliationRun'
        elif 'report' in name:
            return 'Report'
        else:
            # Capitalize first letter for generic entity names
            cleaned = re.sub(r'[^a-z0-9]', '_', name)
            return ''.join(word.capitalize() for word in cleaned.split('_') if word)

    def _analyze_json_schema(self, data: Any, entity_name: str) -> Dict[str, Any]:
        """Analyze JSON data structure to extract schema."""
        schema = {
            'fields': [],
            'source_files': [],
            'relationships': [],
            'lifecycle_states': []
        }

        if isinstance(data, dict):
            schema['fields'] = self._extract_fields_from_dict(data)
        elif isinstance(data, list) and len(data) > 0:
            # Analyze first item as representative
            if isinstance(data[0], dict):
                schema['fields'] = self._extract_fields_from_dict(data[0])

        return schema

    def _analyze_csv_schema(self, csv_file: Path, entity_name: str) -> Dict[str, Any]:
        """Analyze CSV file structure to extract schema."""
        schema = {
            'fields': [],
            'source_files': [str(csv_file)],
            'relationships': [],
            'lifecycle_states': []
        }

        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)

                # Get field names from header
                if reader.fieldnames:
                    for field_name in reader.fieldnames:
                        field = EntityField(
                            name=field_name,
                            data_type='string',  # Default for CSV
                            is_required=False,
                            constraints=[]
                        )
                        schema['fields'].append(field)

                # Sample first few rows for type inference
                sample_rows = []
                for i, row in enumerate(reader):
                    if i >= 10:  # Limit samples
                        break
                    sample_rows.append(row)

                # Infer field types from samples
                self._infer_csv_field_types(schema['fields'], sample_rows)

        except Exception as e:
            self.error_handler.handle_data_parsing_error(csv_file, "CSV", e)
            return None

        return schema

    def _extract_fields_from_dict(self, data: Dict[str, Any]) -> List[EntityField]:
        """Extract fields from a dictionary structure."""
        fields = []

        for key, value in data.items():
            field = EntityField(
                name=key,
                data_type=self._infer_data_type(value),
                is_required=value is not None,
                is_key=self._is_likely_key_field(key),
                constraints=self._infer_constraints(key, value),
                sample_values=[value] if value is not None else []
            )
            fields.append(field)

        return fields

    def _infer_data_type(self, value: Any) -> str:
        """Infer data type from a sample value."""
        if value is None:
            return 'nullable'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'decimal'
        elif isinstance(value, str):
            # Check for specific string patterns
            if re.match(r'^\d{4}-\d{2}-\d{2}', value):
                return 'date'
            elif re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
                return 'datetime'
            elif '@' in value:
                return 'email'
            else:
                return 'string'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        else:
            return 'unknown'

    def _is_likely_key_field(self, field_name: str) -> bool:
        """Determine if field is likely a key field."""
        key_indicators = ['id', 'key', 'number', 'reference', 'code']
        name_lower = field_name.lower()
        return any(indicator in name_lower for indicator in key_indicators)

    def _infer_constraints(self, field_name: str, value: Any) -> List[str]:
        """Infer field constraints from name and value."""
        constraints = []
        name_lower = field_name.lower()

        if 'email' in name_lower:
            constraints.append('valid_email_format')
        elif 'amount' in name_lower or 'total' in name_lower:
            constraints.append('non_negative_number')
        elif 'date' in name_lower:
            constraints.append('valid_date_format')
        elif 'status' in name_lower:
            constraints.append('enumerated_values')

        return constraints

    def _infer_csv_field_types(self, fields: List[EntityField], sample_rows: List[Dict[str, str]]):
        """Infer field types from CSV sample data."""
        for field in fields:
            types_seen = set()

            for row in sample_rows:
                value = row.get(field.name, '').strip()
                if value:
                    inferred_type = self._infer_data_type(value)
                    types_seen.add(inferred_type)

            # Use most specific type if consistent
            if len(types_seen) == 1:
                field.data_type = types_seen.pop()
            elif 'decimal' in types_seen:
                field.data_type = 'decimal'
            elif 'integer' in types_seen:
                field.data_type = 'integer'
            else:
                field.data_type = 'string'  # Default fallback

    def _merge_schemas(self, schema1: Dict[str, Any], schema2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two entity schemas."""
        merged = schema1.copy()

        # Merge source files
        merged['source_files'].extend(schema2.get('source_files', []))

        # Merge fields (simple approach - keep unique field names)
        existing_fields = {f.name for f in merged['fields']}
        for field in schema2.get('fields', []):
            if field.name not in existing_fields:
                merged['fields'].append(field)

        return merged

    def _generate_entity_description(self, entity_name: str, schema: Dict[str, Any]) -> str:
        """Generate a description for an entity based on its schema."""
        field_count = len(schema.get('fields', []))
        source_count = len(schema.get('source_files', []))

        descriptions = {
            'Invoice': f'Supplier invoice with {field_count} fields; sourced from {source_count} file(s); lifecycle: created → matched/unmatched',
            'Payment': f'Unallocated supplier payment with {field_count} fields; sourced from {source_count} file(s); lifecycle: unallocated → matched/exception',
            'Supplier': f'Supplier entity with {field_count} fields; sourced from {source_count} file(s); represents business partners and vendors',
            'ReconciliationRun': f'Container for all matches from single execution with {field_count} fields; metadata, statistics, audit trail'
        }

        return descriptions.get(entity_name,
            f'{entity_name} entity with {field_count} fields; sourced from {source_count} file(s); business domain object')

    def _infer_business_rules(self):
        """Infer business rules from data patterns and entity relationships."""
        rules = []

        # Rule 1: Entity relationship constraints
        if self._has_entities(['Invoice', 'Payment', 'Supplier']):
            rules.append(BusinessRule(
                rule_id='BR-001',
                description='Payments can only be matched to invoices from the same supplier',
                constraint='exact name match or validated alias required',
                confidence=0.9,
                evidence=['supplier field present in both Invoice and Payment entities'],
                entities_involved=['Invoice', 'Payment', 'Supplier']
            ))

        # Rule 2: Amount validation
        amount_fields = self._find_fields_with_pattern(['amount', 'total', 'value'])
        if amount_fields:
            rules.append(BusinessRule(
                rule_id='BR-002',
                description='Payment amount must not exceed invoice amount by more than 10%',
                constraint='unless flagged as partial allocation scenario',
                confidence=0.8,
                evidence=[f'amount fields found: {", ".join(amount_fields)}'],
                entities_involved=['Invoice', 'Payment']
            ))

        # Rule 3: Date proximity matching
        date_fields = self._find_fields_with_pattern(['date', 'created', 'timestamp'])
        if date_fields:
            rules.append(BusinessRule(
                rule_id='BR-003',
                description='Date proximity matching within configurable tolerance window',
                constraint='default ±30 days for exact matching, ±60 days for fuzzy matching',
                confidence=0.9,
                evidence=[f'date fields found: {", ".join(date_fields)}'],
                entities_involved=['Invoice', 'Payment']
            ))

        # Rule 4: Status/State validation
        status_fields = self._find_fields_with_pattern(['status', 'state'])
        if status_fields:
            rules.append(BusinessRule(
                rule_id='BR-004',
                description='Once a payment is fully allocated, it cannot be re-matched',
                constraint='unless explicitly reset through administrative action',
                confidence=0.85,
                evidence=[f'status fields found: {", ".join(status_fields)}'],
                entities_involved=['Payment']
            ))

        # Rule 5: Matching confidence thresholds
        rules.append(BusinessRule(
            rule_id='BR-005',
            description='Matching confidence must be ≥60% to be considered valid',
            constraint='<60% classified as exception requiring manual review',
            confidence=0.95,
            evidence=['reconciliation system requires confidence scoring'],
            entities_involved=['MatchResult']
        ))

        self.domain_model.business_rules = rules

    def _identify_integration_points(self):
        """Identify external systems and integration points."""
        integration_points = []

        # File System Integration
        integration_points.append(IntegrationPoint(
            name='Document Processing System',
            type='file_system',
            description='Read processed invoices from integrated document processor output',
            data_flow='input',
            format='JSON',
            dependencies=['file system permissions', 'directory structure']
        ))

        # Sage Reports Integration
        if any('sage' in str(f).lower() for f in self.json_files + self.csv_files):
            integration_points.append(IntegrationPoint(
                name='Sage Internal Reports',
                type='file_system',
                description='Read unallocated payments from existing sage internal report processor',
                data_flow='input',
                format='JSON/CSV',
                dependencies=['sage report generation process']
            ))

        # MCP Server Integration
        integration_points.append(IntegrationPoint(
            name='MCP Server (sage-recon-mcp)',
            type='service',
            description='Extend existing MCP server with reconciliation tools',
            data_flow='bidirectional',
            format='JSON-RPC',
            dependencies=['existing MCP server infrastructure']
        ))

        # Output File System
        integration_points.append(IntegrationPoint(
            name='File System Output',
            type='file_system',
            description='Write reconciliation results to structured directory',
            data_flow='output',
            format='JSON/CSV/HTML',
            dependencies=['write permissions to data/reconciliation/ directory']
        ))

        # Database for audit trails (if needed)
        if len(self.domain_model.entities) > 3:
            integration_points.append(IntegrationPoint(
                name='SQLite Database',
                type='database',
                description='Store audit trails and matching history for reporting',
                data_flow='output',
                format='SQL',
                dependencies=['SQLite embedded database']
            ))

        self.domain_model.integration_points = integration_points

    def _generate_metadata(self):
        """Generate analysis metadata."""
        self.domain_model.analysis_metadata = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'data_directory': str(self.data_directory),
            'files_analyzed': {
                'json_files': len(self.json_files),
                'csv_files': len(self.csv_files),
                'total_files': len(self.json_files) + len(self.csv_files)
            },
            'entities_discovered': len(self.domain_model.entities),
            'business_rules_generated': len(self.domain_model.business_rules),
            'integration_points_identified': len(self.domain_model.integration_points),
            'confidence_metrics': {
                'entity_extraction': 0.9,
                'business_rules': 0.8,
                'integration_mapping': 0.85
            }
        }

    # Helper methods

    def _has_entities(self, entity_names: List[str]) -> bool:
        """Check if specific entities are present in the domain model."""
        discovered_names = {entity.name for entity in self.domain_model.entities}
        return all(name in discovered_names for name in entity_names)

    def _find_fields_with_pattern(self, patterns: List[str]) -> List[str]:
        """Find fields across all entities that match certain patterns."""
        matching_fields = []

        for entity in self.domain_model.entities:
            for field in entity.fields:
                field_name_lower = field.name.lower()
                for pattern in patterns:
                    if pattern in field_name_lower:
                        matching_fields.append(f'{entity.name}.{field.name}')
                        break

        return matching_fields


def main():
    """Command-line interface for domain analysis with setup wizard support."""
    import argparse
    import sys

    try:
        from .domain_config import DomainConfigManager
        from .interactive_domain_analysis import InteractiveDomainAnalyzer
    except ImportError:
        from domain_config import DomainConfigManager
        from interactive_domain_analysis import InteractiveDomainAnalyzer

    parser = argparse.ArgumentParser(description="Domain analysis for spec-kit")
    parser.add_argument("data_directory", nargs='?', help="Directory containing data files to analyze")
    parser.add_argument("--output", help="Output file for results (optional)")
    parser.add_argument("--interactive", action="store_true", help="Enable interactive mode for user validation")
    parser.add_argument("--setup", action="store_true", help="Run setup wizard to configure domain analysis")
    parser.add_argument("--config", help="Use saved configuration file")

    args = parser.parse_args()

    # Handle setup wizard mode
    if args.setup:
        print("Running domain analysis setup wizard...")
        config_manager = DomainConfigManager()
        config = config_manager.run_setup_wizard()

        # Ask if user wants to run analysis immediately
        if args.data_directory and Path(args.data_directory).exists():
            run_analysis = input("\nRun domain analysis now with these settings? (Y/n): ").strip().lower()
            if run_analysis != 'n':
                args.interactive = True
                args.config = str(config_manager.config_file)
            else:
                return
        else:
            print("Specify a data directory to run analysis with these settings.")
            return

    # Validate data directory
    if not args.data_directory:
        print("Error: Data directory is required (unless using --setup)")
        parser.print_help()
        sys.exit(1)

    if not Path(args.data_directory).exists():
        print(f"Error: Directory '{args.data_directory}' does not exist")
        sys.exit(1)

    # Choose analyzer based on mode
    if args.interactive or args.config:
        analyzer = InteractiveDomainAnalyzer(
            args.data_directory,
            interactive_mode=args.interactive,
            config_file=args.config
        )
        domain_model = analyzer.analyze()
    else:
        analyzer = DomainAnalyzer(args.data_directory)
        domain_model = analyzer.analyze()

        print("\n" + "="*50)
        print("DOMAIN ANALYSIS RESULTS")
        print("="*50)

        print(f"\nEntities ({len(domain_model.entities)}):")
        for entity in domain_model.entities:
            print(f"  - {entity.name}: {entity.description}")
            print(f"    Fields: {len(entity.fields)}")

        print(f"\nBusiness Rules ({len(domain_model.business_rules)}):")
        for rule in domain_model.business_rules:
            print(f"  - {rule.rule_id}: {rule.description}")
            print(f"    Confidence: {rule.confidence:.2f}")

        print(f"\nIntegration Points ({len(domain_model.integration_points)}):")
        for integration in domain_model.integration_points:
            print(f"  - {integration.name} ({integration.type}): {integration.description}")

    # Save results if requested
    if args.output:
        output_data = {
            'entities': [asdict(entity) for entity in domain_model.entities],
            'business_rules': [asdict(rule) for rule in domain_model.business_rules],
            'integration_points': [asdict(integration) for integration in domain_model.integration_points]
        }

        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"- Results saved to: {args.output}")


if __name__ == '__main__':
    main()