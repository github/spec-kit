# Domain Analysis Tool - Usage Guide

This comprehensive guide demonstrates how to use the Domain Analysis Tool for extracting business entities, rules, and integration patterns from your data files.

## Table of Contents

- [Quick Start](#quick-start)
- [Setup and Configuration](#setup-and-configuration)
- [Basic Analysis](#basic-analysis)
- [Interactive Mode](#interactive-mode)
- [Advanced Features](#advanced-features)
- [Examples by Domain](#examples-by-domain)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Basic Analysis (Automatic Mode)

Analyze a directory containing JSON/CSV files and automatically populate your specification template:

```bash
# Linux/macOS
./scripts/bash/analyze-domain.sh --data-dir=./sample-data

# Windows PowerShell
scripts/powershell/analyze-domain.ps1 -DataDir ".\sample-data"
```

This will:
- Scan `./sample-data` for JSON and CSV files
- Extract business entities and relationships
- Generate business rules from data patterns
- Create a domain analysis report
- Populate any specification templates found

### 2. Interactive Analysis

For first-time users or complex domains, use interactive mode:

```bash
# Linux/macOS
./scripts/bash/analyze-domain.sh --interactive --data-dir=./sample-data

# Windows PowerShell
scripts/powershell/analyze-domain.ps1 -Interactive -DataDir ".\sample-data"
```

## Setup and Configuration

### First-Time Setup Wizard

Run the setup wizard to configure domain-specific preferences:

```bash
# Linux/macOS
./scripts/bash/analyze-domain.sh --setup

# Windows PowerShell
scripts/powershell/analyze-domain.ps1 -Setup
```

The wizard will guide you through:

1. **Domain Type Selection**:
   - Financial/Accounting (invoices, payments, reconciliation)
   - E-commerce/Retail (orders, products, customers)
   - CRM/Sales (contacts, leads, opportunities)
   - Custom (define your own patterns)

2. **Entity Configuration**:
   - Review suggested business entities
   - Add custom entities and file patterns
   - Define key fields and relationships

3. **Business Rules Setup**:
   - Configure rule templates for your domain
   - Set confidence thresholds
   - Add custom validation rules

4. **Integration Points**:
   - Define external system connections
   - Specify data flow directions
   - Configure integration patterns

### Configuration File

Your preferences are saved to `.specify/domain-config.yaml`:

```yaml
domain_type: financial
entities:
  patterns:
    Invoice: [invoice, bill, statement]
    Payment: [payment, unallocated, receipt]
    Supplier: [supplier, vendor, creditor]
business_rules:
  templates:
    - "Payments can only be matched to invoices from the same supplier"
    - "Payment amount must not exceed invoice amount by more than {tolerance}%"
  custom_rules:
    - "All invoices must have a valid supplier reference"
settings:
  confidence_threshold: 0.75
  default_interactive: true
```

## Basic Analysis

### Analyzing JSON Data

For JSON files containing business data:

```bash
# Analyze JSON files in a directory
./scripts/bash/analyze-domain.sh --data-dir=./financial-data --output=analysis.json

# Expected directory structure:
financial-data/
├── invoices.json          # Invoice records
├── payments.json          # Payment transactions
├── suppliers.json         # Supplier master data
└── reconciliation.json    # Matching records
```

**Example JSON Structure** (`invoices.json`):
```json
[
  {
    "invoice_id": "INV-2024-001",
    "supplier_id": "SUP-ABC123",
    "invoice_date": "2024-01-15",
    "due_date": "2024-02-14",
    "total_amount": 1250.00,
    "currency": "USD",
    "status": "pending",
    "line_items": [
      {
        "description": "Professional Services",
        "quantity": 10,
        "unit_price": 125.00
      }
    ]
  }
]
```

**Generated Entities**:
```
- Invoice: Financial document representing amount due
  - Key fields: invoice_id, supplier_id
  - Total fields: 8
  - Relationships: supplier_id → Supplier

- Supplier: External entity providing goods/services
  - Key fields: supplier_id
  - Total fields: 5
  - Relationships: none identified
```

### Analyzing CSV Data

For CSV files with structured business data:

```bash
# Analyze mixed JSON/CSV data
./scripts/bash/analyze-domain.sh --data-dir=./ecommerce-data
```

**Example CSV Structure** (`orders.csv`):
```csv
order_id,customer_id,order_date,total_amount,status,payment_method
ORD-001,CUST-ABC,2024-01-15,299.99,shipped,credit_card
ORD-002,CUST-DEF,2024-01-16,145.50,pending,paypal
```

**Generated Business Rules**:
```
- Order amounts must be positive values
- Order status follows progression: pending → confirmed → shipped → delivered
- Payment method must be from allowed list
- Customer reference is required for all orders
```

## Interactive Mode

### Entity Validation Workflow

When running in interactive mode, you'll be prompted to validate discovered entities:

```
=== ENTITY VALIDATION ===

>> Entity: Invoice
Description: Financial document representing amount due (confidence: 95%)
Key fields: invoice_id, supplier_id, total_amount
Relationships: supplier_id → Supplier

Options:
1. Accept entity as-is
2. Modify entity details
3. Remove this entity
4. Accept all remaining entities
Choice (1-4): 2

Enter new name (or press enter to keep 'Invoice'): Invoice
Enter new description: Invoice document with payment terms
Update field 'total_amount' type (current: float): currency
```

### Business Rules Customization

Interactive validation of generated business rules:

```
=== BUSINESS RULES VALIDATION ===

>> Business Rule: BR-001
Description: Payments can only be matched to invoices from the same supplier
Constraint: payment.supplier_id == invoice.supplier_id
Confidence: 89% MED
Applies to: Payment, Invoice

Options:
1. Accept rule as-is
2. Modify rule constraint
3. Remove this rule
4. Add custom rule
5. Accept all remaining rules
Choice (1-5): 4

Enter rule description: Payment date must be within 90 days of invoice date
Which entities does this apply to? (comma-separated): Payment, Invoice
```

### Integration Points Discovery

Configure external system integration patterns:

```
=== INTEGRATION POINTS VALIDATION ===

>> Integration: ERP System (api)
Description: Bidirectional data sync with enterprise system
Data flow: bidirectional ↔
Format: JSON REST API

Options:
1. Accept integration as-is
2. Modify integration details
3. Remove this integration
4. Add new integration
Choice (1-4): 4

System name: Payment Gateway
Integration type (api/database/file_system/service): api
Data flow (input/output/bidirectional): output
Data format: JSON webhook
Description: Process payment transactions and receive status updates
```

## Advanced Features

### Batch Processing Multiple Directories

Analyze multiple data sources in a single operation:

```bash
# Process multiple client datasets
for client_dir in data/client-*; do
  echo "Processing $(basename $client_dir)..."
  ./scripts/bash/analyze-domain.sh \
    --data-dir="$client_dir" \
    --config=".specify/financial-config.yaml" \
    --output="analysis-$(basename $client_dir).json"
done
```

### Custom Configuration Files

Use different configurations for different projects:

```bash
# Financial analysis configuration
./scripts/bash/analyze-domain.sh \
  --data-dir=./finance-data \
  --config=.specify/financial-config.yaml

# E-commerce analysis configuration
./scripts/bash/analyze-domain.sh \
  --data-dir=./ecommerce-data \
  --config=.specify/ecommerce-config.yaml
```

### Confidence Threshold Tuning

Adjust confidence thresholds for different use cases:

```bash
# High-confidence analysis (fewer, more certain results)
./scripts/bash/analyze-domain.sh \
  --data-dir=./data \
  --confidence=0.9

# Lower threshold for discovery (more comprehensive results)
./scripts/bash/analyze-domain.sh \
  --data-dir=./data \
  --confidence=0.6
```

### Specification Template Integration

The tool automatically populates specification templates when found:

```
Before (Template):
### Key Entities
- **[Entity Name]**: [Description]
- **[Entity Name]**: [Description]

After (Populated):
### Key Entities
- **Invoice**: Financial document representing amount due
  - Key fields: invoice_id, supplier_id
  - Total fields: 8
  - Relationships: supplier_id → Supplier
- **Payment**: Financial transaction for invoice settlement
  - Key fields: payment_id, reference
  - Total fields: 6
  - Relationships: reference → Invoice
```

## Examples by Domain

### Financial/Accounting Domain

**Data Structure**:
```
financial-data/
├── chart-of-accounts.json    # Account definitions
├── general-ledger.json       # Transaction records
├── invoices.json            # Accounts receivable
├── payments.json            # Payment processing
└── reconciliation.csv       # Bank reconciliation
```

**Typical Analysis Results**:
- **Entities**: Account, Transaction, Invoice, Payment, Reconciliation
- **Business Rules**: Double-entry validation, date proximity matching, amount tolerances
- **Integrations**: ERP system, banking feeds, reporting database

**Command**:
```bash
./scripts/bash/analyze-domain.sh \
  --data-dir=./financial-data \
  --config=.specify/financial-config.yaml \
  --interactive
```

### E-commerce Domain

**Data Structure**:
```
ecommerce-data/
├── products.json           # Product catalog
├── customers.json          # Customer profiles
├── orders.json            # Order transactions
├── inventory.csv          # Stock levels
└── shipping.json          # Fulfillment data
```

**Typical Analysis Results**:
- **Entities**: Product, Customer, Order, OrderItem, Shipment
- **Business Rules**: Inventory validation, order status progression, payment verification
- **Integrations**: Payment gateway, inventory system, shipping service

**Command**:
```bash
./scripts/bash/analyze-domain.sh \
  --data-dir=./ecommerce-data \
  --config=.specify/ecommerce-config.yaml
```

### CRM Domain

**Data Structure**:
```
crm-data/
├── contacts.json           # Contact information
├── accounts.json          # Company/organization data
├── opportunities.json     # Sales pipeline
├── activities.csv         # Interaction history
└── campaigns.json         # Marketing campaigns
```

**Typical Analysis Results**:
- **Entities**: Contact, Account, Opportunity, Activity, Campaign
- **Business Rules**: Lead qualification, pipeline progression, activity tracking
- **Integrations**: Email system, marketing automation, analytics platform

**Command**:
```bash
./scripts/bash/analyze-domain.sh \
  --data-dir=./crm-data \
  --config=.specify/crm-config.yaml
```

## Troubleshooting

### Common Issues

**1. No entities discovered**
```
Error: No business entities could be identified from the data files.

Solutions:
- Ensure JSON/CSV files contain structured business data
- Check file naming follows recognizable patterns
- Use interactive mode to define custom entity patterns
- Verify files are not empty or corrupted
```

**2. Low confidence scores**
```
Warning: Many business rules have low confidence scores (< 60%).

Solutions:
- Increase the confidence threshold: --confidence=0.8
- Provide more data files for better pattern recognition
- Use interactive mode to manually validate and adjust rules
- Consider domain-specific configuration
```

**3. Configuration file errors**
```
Error: Configuration file '.specify/domain-config.yaml' is invalid.

Solutions:
- Run setup wizard: ./scripts/bash/analyze-domain.sh --setup
- Validate YAML syntax using online validator
- Check file permissions and accessibility
- Use default configuration: remove --config parameter
```

**4. Script execution permissions**
```bash
# Linux/macOS permission error
chmod +x scripts/bash/analyze-domain.sh
chmod +x scripts/bash/common.sh

# Windows PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Linux/macOS
./scripts/bash/analyze-domain.sh --data-dir=./data --debug

# Windows PowerShell
scripts/powershell/analyze-domain.ps1 -DataDir ".\data" -Debug
```

### Performance Optimization

For large datasets:

```bash
# Process files in parallel
./scripts/bash/analyze-domain.sh \
  --data-dir=./large-dataset \
  --parallel \
  --max-files=100
```

### Getting Help

```bash
# Show all available options
./scripts/bash/analyze-domain.sh --help

# Show version information
./scripts/bash/analyze-domain.sh --version
```

## Next Steps

After successful domain analysis:

1. **Review Results**: Examine the generated domain model and business rules
2. **Refine Configuration**: Adjust entity patterns and confidence thresholds
3. **Template Integration**: Ensure specification templates are properly populated
4. **Iterative Improvement**: Re-run analysis as data evolves

For more advanced usage patterns and integration examples, see the project README and CONTRIBUTING guidelines.