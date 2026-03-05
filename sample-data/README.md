# Sample Datasets for Domain Analysis Tool

This directory contains sample datasets for demonstrating the Domain Analysis Tool's capabilities across different business domains.

## Overview

The sample datasets are organized by business domain and contain realistic, interconnected data that showcases the tool's ability to:

- Extract business entities from structured data files
- Infer business rules from data patterns and relationships
- Identify integration points and data flow patterns
- Generate comprehensive domain models

## Dataset Structure

### Financial Domain (`financial/`)

**Use Case**: Invoice processing, payment reconciliation, and supplier management

**Files**:
- `invoices.json` - Invoice records with line items, approval workflows, and payment terms
- `payments.json` - Payment transactions with reconciliation status and banking details
- `suppliers.csv` - Supplier master data with contact information and payment preferences
- `reconciliation.csv` - Payment-to-invoice matching records with confidence scores

**Key Entities**: Invoice, Payment, Supplier, Reconciliation
**Business Rules**: Payment matching, approval workflows, date proximity matching
**Integration Points**: ERP systems, banking feeds, payment gateways

### E-commerce Domain (`ecommerce/`)

**Use Case**: Online retail operations, order management, and customer lifecycle

**Files**:
- `orders.json` - Order transactions with items, shipping, and payment details
- `products.csv` - Product catalog with inventory, pricing, and supplier information
- `customers.json` - Customer profiles with addresses, preferences, and purchase history

**Key Entities**: Order, Product, Customer, OrderItem, Address
**Business Rules**: Inventory validation, order status progression, payment processing
**Integration Points**: Payment gateways, shipping services, inventory systems

### CRM Domain (`crm/`)

**Use Case**: Customer relationship management, sales pipeline, and lead tracking

**Files**:
- `contacts.json` - Contact information with lifecycle stages and engagement data
- `opportunities.csv` - Sales opportunities with stages, amounts, and close dates
- `activities.json` - Sales activities, meetings, emails, and follow-up actions

**Key Entities**: Contact, Account, Opportunity, Activity, Lead
**Business Rules**: Lead qualification, pipeline progression, activity tracking
**Integration Points**: Email systems, marketing automation, analytics platforms

## Usage Examples

### Quick Analysis

Analyze any domain using the bash script:

```bash
# Financial domain analysis
./scripts/bash/analyze-domain.sh --data-dir=./sample-data/financial

# E-commerce domain analysis
./scripts/bash/analyze-domain.sh --data-dir=./sample-data/ecommerce

# CRM domain analysis
./scripts/bash/analyze-domain.sh --data-dir=./sample-data/crm
```

### Interactive Mode

Use interactive mode for guided analysis and customization:

```bash
# Interactive financial analysis
./scripts/bash/analyze-domain.sh --interactive --data-dir=./sample-data/financial

# With custom confidence threshold
./scripts/bash/analyze-domain.sh --interactive --data-dir=./sample-data/ecommerce --confidence=0.8
```

### Domain-Specific Configuration

Use pre-configured domain settings:

```bash
# Setup wizard for financial domain
./scripts/bash/analyze-domain.sh --setup

# Use saved configuration
./scripts/bash/analyze-domain.sh --data-dir=./sample-data/financial --config=.specify/financial-config.yaml
```

## Expected Analysis Results

### Financial Domain Results

**Discovered Entities**:
- Invoice (confidence: 95%) - 8 fields, relationships to Supplier
- Payment (confidence: 92%) - 6 fields, relationships to Invoice
- Supplier (confidence: 88%) - 12 fields, master data entity
- Reconciliation (confidence: 85%) - 5 fields, matching logic

**Inferred Business Rules**:
- Payments must reference valid invoices or be marked as unallocated
- Payment amounts should not exceed invoice amounts by more than 5%
- Date proximity matching within ±7 days for automatic reconciliation
- Approval workflows required for payments above threshold amounts

**Integration Points**:
- ERP System (bidirectional API) - invoice and supplier data sync
- Banking Feeds (input file system) - daily bank statement imports
- Payment Gateway (output API) - payment processing and status updates

### E-commerce Domain Results

**Discovered Entities**:
- Order (confidence: 96%) - 15 fields, relationships to Customer and Product
- Product (confidence: 94%) - 18 fields, catalog master data
- Customer (confidence: 91%) - 12 fields, relationships to Address and Order
- OrderItem (confidence: 89%) - 6 fields, order line item details

**Inferred Business Rules**:
- Orders must have at least one product line item
- Product inventory must be sufficient before order confirmation
- Payment authorization required before order processing
- Shipped orders cannot be cancelled without return process

**Integration Points**:
- Payment Gateway (bidirectional API) - payment processing and refunds
- Inventory System (bidirectional database) - stock level synchronization
- Shipping Service (output API) - order fulfillment and tracking

### CRM Domain Results

**Discovered Entities**:
- Contact (confidence: 93%) - 14 fields, relationships to Account and Activity
- Opportunity (confidence: 91%) - 16 fields, sales pipeline data
- Activity (confidence: 87%) - 11 fields, interaction tracking
- Account (confidence: 85%) - implied from contact relationships

**Inferred Business Rules**:
- Leads must be qualified before becoming opportunities
- Opportunities must have associated contact and account information
- Activities must be linked to contacts or opportunities
- Follow-up dates required for open activities

**Integration Points**:
- Email System (bidirectional API) - email activity tracking and campaigns
- Calendar System (bidirectional API) - meeting scheduling and reminders
- Marketing Automation (input API) - lead scoring and nurture campaigns

## Data Characteristics

### Realistic Business Scenarios

The datasets include realistic business scenarios:

- **Financial**: Mix of paid/pending invoices, unallocated payments, approval workflows
- **E-commerce**: Various order statuses, customer tiers, product categories, returns
- **CRM**: Different contact lifecycle stages, opportunity pipelines, activity types

### Data Quality Patterns

Each dataset demonstrates common data quality patterns:

- **Complete Records**: Most records have all required fields populated
- **Missing Data**: Some optional fields are null/empty (realistic scenarios)
- **Inconsistent Formats**: Phone numbers, dates, and addresses in various formats
- **Relationship Integrity**: Foreign key relationships are maintained across files

### Scalability Testing

The datasets are sized for demonstration but can be extended:

- **Small Scale**: 3-5 records per entity for quick testing
- **Medium Scale**: 50-100 records for performance testing
- **Large Scale**: Can be multiplied using data generation scripts

## Customizing Sample Data

### Adding Your Own Data

To test with your own data structure:

1. Create a new directory under `sample-data/`
2. Add JSON/CSV files following similar patterns
3. Run analysis: `./scripts/bash/analyze-domain.sh --data-dir=./sample-data/your-domain`

### Modifying Existing Data

To test different scenarios:

1. Edit the JSON/CSV files to add/remove fields
2. Change relationship patterns (foreign keys)
3. Adjust data distributions and patterns
4. Re-run analysis to see how results change

### Data Generation

For larger datasets, consider using data generation tools:

```python
# Example: Generate more invoice records
import json
from datetime import datetime, timedelta

# Load existing data
with open('sample-data/financial/invoices.json', 'r') as f:
    invoices = json.load(f)

# Generate additional records following the same pattern
# (implementation details omitted for brevity)
```

## Troubleshooting

### Common Issues

1. **No entities discovered**: Ensure JSON/CSV files contain structured business data
2. **Low confidence scores**: Increase data volume or use domain-specific configuration
3. **Missing relationships**: Check that foreign key fields use consistent naming
4. **File format errors**: Validate JSON syntax and CSV column headers

### Debugging Analysis

Enable debug mode for detailed analysis information:

```bash
./scripts/bash/analyze-domain.sh --data-dir=./sample-data/financial --debug
```

### Performance Optimization

For large datasets:

```bash
# Limit file processing
./scripts/bash/analyze-domain.sh --data-dir=./sample-data/financial --max-files=10

# Adjust confidence thresholds
./scripts/bash/analyze-domain.sh --data-dir=./sample-data/financial --confidence=0.9
```

## Contributing

To contribute additional sample datasets:

1. Follow the existing directory structure (`domain-name/`)
2. Include README documentation for your domain
3. Provide realistic, interconnected data
4. Test analysis results and document expected outcomes
5. Submit pull request with dataset and documentation

## License

The sample datasets are provided under the same MIT license as the Domain Analysis Tool project.