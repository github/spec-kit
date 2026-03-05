#!/usr/bin/env python3
"""
Unit tests for domain_analysis module.

Tests the core functionality of entity extraction, business rule inference,
and integration point identification.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

# Import the modules under test
import sys
sys.path.append(str(Path(__file__).parent.parent / "src" / "specify_cli"))

from domain_analysis import (
    DomainAnalyzer,
    BusinessEntity,
    BusinessRule,
    IntegrationPoint,
    EntityField,
    DomainModel
)


class TestDomainAnalyzer:
    """Test cases for the DomainAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_data_dir = Path(__file__).parent / "data" / "sample"
        self.analyzer = DomainAnalyzer(str(self.test_data_dir))

    def test_init(self):
        """Test DomainAnalyzer initialization."""
        assert self.analyzer.data_directory == self.test_data_dir
        assert self.analyzer.domain_model is not None
        assert isinstance(self.analyzer.domain_model.entities, list)
        assert isinstance(self.analyzer.domain_model.business_rules, list)
        assert isinstance(self.analyzer.domain_model.integration_points, list)

    def test_init_with_nonexistent_directory(self):
        """Test initialization with non-existent directory."""
        with pytest.raises(FileNotFoundError):
            DomainAnalyzer("/nonexistent/directory")

    def test_discover_data_files(self):
        """Test data file discovery."""
        files = self.analyzer._discover_data_files()

        # Should find JSON and CSV files
        json_files = [f for f in files if f.suffix == '.json']
        csv_files = [f for f in files if f.suffix == '.csv']

        assert len(json_files) >= 2  # invoices.json, payments.json
        assert len(csv_files) >= 1   # suppliers.csv

        # Check specific files exist
        file_names = [f.name for f in files]
        assert 'invoices.json' in file_names
        assert 'payments.json' in file_names
        assert 'suppliers.csv' in file_names

    def test_load_json_file(self):
        """Test JSON file loading."""
        json_file = self.test_data_dir / "invoices.json"
        data = self.analyzer._load_json_file(json_file)

        assert data is not None
        assert isinstance(data, list)
        assert len(data) >= 1

        # Check structure of first invoice
        invoice = data[0]
        assert 'invoice_id' in invoice
        assert 'supplier_id' in invoice
        assert 'total_amount' in invoice

    def test_load_csv_file(self):
        """Test CSV file loading."""
        csv_file = self.test_data_dir / "suppliers.csv"
        data = self.analyzer._load_csv_file(csv_file)

        assert data is not None
        assert isinstance(data, list)
        assert len(data) >= 1

        # Check structure of first supplier
        supplier = data[0]
        assert 'supplier_id' in supplier
        assert 'company_name' in supplier

    def test_load_invalid_json_file(self):
        """Test handling of invalid JSON files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')  # Invalid JSON
            invalid_file = Path(f.name)

        try:
            data = self.analyzer._load_json_file(invalid_file)
            assert data is None
        finally:
            invalid_file.unlink()

    def test_extract_schema_from_json(self):
        """Test schema extraction from JSON data."""
        test_data = [
            {
                "id": "123",
                "name": "Test Item",
                "amount": 100.50,
                "active": True,
                "tags": ["tag1", "tag2"]
            }
        ]

        schema = self.analyzer._extract_schema_from_data(test_data, "test_entity")

        assert schema['entity_name'] == 'test_entity'
        assert len(schema['fields']) == 5

        # Check field types
        field_types = {f['name']: f['type'] for f in schema['fields']}
        assert field_types['id'] == 'string'
        assert field_types['name'] == 'string'
        assert field_types['amount'] == 'float'
        assert field_types['active'] == 'boolean'
        assert field_types['tags'] == 'array'

    def test_identify_key_fields(self):
        """Test key field identification."""
        schema = {
            'fields': [
                {'name': 'id', 'type': 'string'},
                {'name': 'invoice_id', 'type': 'string'},
                {'name': 'name', 'type': 'string'},
                {'name': 'amount', 'type': 'float'}
            ]
        }

        key_fields = self.analyzer._identify_key_fields(schema)
        key_field_names = [f['name'] for f in key_fields]

        # Should identify ID fields as keys
        assert 'id' in key_field_names or 'invoice_id' in key_field_names

    def test_entity_creation(self):
        """Test business entity creation."""
        schema = {
            'entity_name': 'Invoice',
            'fields': [
                {'name': 'invoice_id', 'type': 'string'},
                {'name': 'amount', 'type': 'float'},
                {'name': 'status', 'type': 'string'}
            ]
        }

        entity = self.analyzer._create_entity_from_schema(schema, 0.95)

        assert isinstance(entity, BusinessEntity)
        assert entity.name == 'Invoice'
        assert entity.confidence == 0.95
        assert len(entity.fields) == 3

        # Check that fields are EntityField objects
        for field in entity.fields:
            assert isinstance(field, EntityField)

    def test_analyze_method(self):
        """Test the main analyze method."""
        domain_model = self.analyzer.analyze()

        assert isinstance(domain_model, DomainModel)
        assert len(domain_model.entities) > 0
        assert len(domain_model.business_rules) >= 0
        assert len(domain_model.integration_points) >= 0

        # Check that entities have meaningful names
        entity_names = [e.name for e in domain_model.entities]
        # Should recognize common business entities
        expected_entities = ['Invoice', 'Payment', 'Supplier']
        found_entities = [name for name in expected_entities if name in entity_names]
        assert len(found_entities) > 0


class TestBusinessEntity:
    """Test cases for the BusinessEntity class."""

    def test_business_entity_creation(self):
        """Test BusinessEntity creation and attributes."""
        fields = [
            EntityField(name="id", field_type="string", is_key=True),
            EntityField(name="name", field_type="string", is_key=False),
            EntityField(name="amount", field_type="float", is_key=False)
        ]

        entity = BusinessEntity(
            name="TestEntity",
            description="A test entity",
            fields=fields,
            confidence=0.85,
            relationships=["related_entity_id"]
        )

        assert entity.name == "TestEntity"
        assert entity.description == "A test entity"
        assert entity.confidence == 0.85
        assert len(entity.fields) == 3
        assert entity.relationships == ["related_entity_id"]

    def test_entity_field_properties(self):
        """Test EntityField properties."""
        field = EntityField(name="test_field", field_type="integer", is_key=True)

        assert field.name == "test_field"
        assert field.field_type == "integer"
        assert field.is_key is True


class TestBusinessRule:
    """Test cases for the BusinessRule class."""

    def test_business_rule_creation(self):
        """Test BusinessRule creation and attributes."""
        rule = BusinessRule(
            rule_id="BR-001",
            description="Test business rule",
            constraint="amount > 0",
            entities_involved=["Invoice", "Payment"],
            confidence=0.90
        )

        assert rule.rule_id == "BR-001"
        assert rule.description == "Test business rule"
        assert rule.constraint == "amount > 0"
        assert rule.entities_involved == ["Invoice", "Payment"]
        assert rule.confidence == 0.90


class TestIntegrationPoint:
    """Test cases for the IntegrationPoint class."""

    def test_integration_point_creation(self):
        """Test IntegrationPoint creation and attributes."""
        integration = IntegrationPoint(
            name="Test API",
            integration_type="api",
            description="Test integration point",
            data_flow="bidirectional",
            format="JSON",
            dependencies=["auth_service"]
        )

        assert integration.name == "Test API"
        assert integration.type == "api"
        assert integration.description == "Test integration point"
        assert integration.data_flow == "bidirectional"
        assert integration.format == "JSON"
        assert integration.dependencies == ["auth_service"]


class TestDomainModel:
    """Test cases for the DomainModel class."""

    def test_domain_model_creation(self):
        """Test DomainModel creation and attributes."""
        entities = [
            BusinessEntity(name="Entity1", description="Test 1", fields=[], confidence=0.8)
        ]
        rules = [
            BusinessRule(rule_id="BR-001", description="Rule 1", constraint="x > 0",
                        entities_involved=["Entity1"], confidence=0.9)
        ]
        integrations = [
            IntegrationPoint(name="API1", integration_type="api", description="Test API",
                           data_flow="input", format="JSON")
        ]

        model = DomainModel(entities=entities, business_rules=rules, integration_points=integrations)

        assert len(model.entities) == 1
        assert len(model.business_rules) == 1
        assert len(model.integration_points) == 1
        assert model.entities[0].name == "Entity1"
        assert model.business_rules[0].rule_id == "BR-001"
        assert model.integration_points[0].name == "API1"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_missing_data_directory(self):
        """Test handling of missing data directory."""
        with pytest.raises(FileNotFoundError):
            DomainAnalyzer("/path/that/does/not/exist")

    def test_empty_data_directory(self):
        """Test handling of empty data directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = DomainAnalyzer(temp_dir)
            files = analyzer._discover_data_files()
            assert len(files) == 0

    def test_corrupted_json_file(self):
        """Test handling of corrupted JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create corrupted JSON file
            corrupted_file = Path(temp_dir) / "corrupted.json"
            corrupted_file.write_text('{"invalid": json syntax}')

            analyzer = DomainAnalyzer(temp_dir)
            data = analyzer._load_json_file(corrupted_file)
            assert data is None


# Integration test fixtures
@pytest.fixture
def sample_analyzer():
    """Fixture providing analyzer with sample data."""
    test_data_dir = Path(__file__).parent / "data" / "sample"
    return DomainAnalyzer(str(test_data_dir))


def test_full_analysis_workflow(sample_analyzer):
    """Test complete analysis workflow."""
    # Run full analysis
    domain_model = sample_analyzer.analyze()

    # Verify results
    assert isinstance(domain_model, DomainModel)
    assert len(domain_model.entities) > 0

    # Check entity quality
    for entity in domain_model.entities:
        assert entity.name is not None
        assert len(entity.name) > 0
        assert entity.confidence > 0
        assert len(entity.fields) > 0

    # Check business rules
    for rule in domain_model.business_rules:
        assert rule.rule_id is not None
        assert rule.description is not None
        assert 0 <= rule.confidence <= 1


if __name__ == "__main__":
    pytest.main([__file__])