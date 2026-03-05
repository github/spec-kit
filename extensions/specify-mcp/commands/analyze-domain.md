---
description: "Extract business entities and rules from JSON/CSV data files"
tools:
  - 'specify-mcp/analyze_domain'
  - 'specify-mcp/list_domain_templates'
  - 'specify-mcp/setup_domain_config'
---

# Analyze Domain

Extract business entities, rules, and integration patterns from your data files.

## Purpose

Analyze JSON or CSV data files to automatically:
- Identify business entities with fields and relationships
- Infer business rules from data patterns
- Detect integration points and data flows
- Generate domain-specific documentation

## Prerequisites

1. Specify MCP server configured and running
2. Data files (JSON or CSV) available for analysis
3. Optional: Domain configuration set up

## User Input

$ARGUMENTS

## Steps

### Step 1: Check Available Domain Templates

Review available domain templates for your analysis:

Use MCP tool: `specify-mcp/list_domain_templates`

This shows pre-built patterns for:
- **Financial**: Invoices, payments, transactions
- **E-commerce**: Orders, products, customers
- **CRM**: Contacts, leads, opportunities

### Step 2: Configure Domain Analysis (Optional)

Set up domain-specific preferences:

Use MCP tool: `specify-mcp/setup_domain_config`

Parameters:
- `domain_type`: One of "financial", "ecommerce", "crm", or "custom"
- `custom_patterns`: Custom extraction patterns (if domain_type is "custom")

### Step 3: Analyze Data Files

Run domain analysis on your data:

Use MCP tool: `specify-mcp/analyze_domain`

Parameters:
- `data_path`: Path to JSON/CSV file or directory
- `domain_type`: Optional domain template to apply
- `output_format`: "markdown" (default) or "json"
- `validate`: Whether to validate extracted entities (default: true)

```json
{
  "data_path": "/path/to/data/",
  "domain_type": "financial",
  "output_format": "markdown",
  "validate": true
}
```

### Step 4: Review Extracted Entities

The analysis outputs:

**Business Entities**:
- Entity name and description
- Fields with types and constraints
- Relationships to other entities

**Business Rules**:
- Inferred validation rules
- Data integrity constraints
- State transition rules

**Integration Points**:
- External system references
- Data flow patterns
- API endpoint indicators

### Step 5: Save Analysis Results

Save the domain analysis to your project:

```bash
# Create domain analysis directory
mkdir -p specs/domain-analysis

# The tool outputs markdown documentation
# Copy to your specs folder for version control
```

## Configuration Reference

Configuration in `specify-mcp-config.yml`:

- **analysis.domain_templates**: List of enabled domain templates
  - Type: array
  - Default: `["financial", "ecommerce", "crm"]`

- **analysis.validation_strict**: Enable strict validation mode
  - Type: boolean
  - Default: `false`

## Environment Variables

- `SPECKIT_SPECIFY_MCP_DOMAIN_TEMPLATES` - Override domain templates
- `SPECKIT_SPECIFY_MCP_VALIDATION_STRICT` - Enable strict validation

## Examples

### Analyze Financial Data

```json
{
  "data_path": "./sample-data/financial/",
  "domain_type": "financial"
}
```

### Analyze E-commerce Orders

```json
{
  "data_path": "./data/orders.json",
  "domain_type": "ecommerce"
}
```

### Custom Domain Analysis

```json
{
  "data_path": "./data/",
  "domain_type": "custom",
  "custom_patterns": {
    "entity_patterns": ["user_*", "account_*"],
    "rule_patterns": ["must_*", "should_*"]
  }
}
```

## Notes

- Large datasets may take longer to analyze
- Validation helps identify inconsistent data patterns
- Use domain templates for faster, more accurate analysis
- Results improve with larger sample sizes

---

*For more information: `specify extension info specify-mcp`*
