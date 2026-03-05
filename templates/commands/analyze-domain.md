---
description: Analyze data files and extract domain models to populate specification templates with real business entities and rules. Supports interactive mode for user validation and customization.
scripts:
  sh: scripts/bash/analyze-domain.sh --json "{ARGS}"
  ps: scripts/powershell/analyze-domain.ps1 -Json "{ARGS}"
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

Goal: Extract domain-specific entities, business rules, and integration patterns from actual data files to replace template placeholders with concrete, data-driven content. This command should run after `/specify` but before `/plan` to enrich specifications with real domain knowledge.

Execution steps:

1. Run `{SCRIPT}` once from repo root and parse JSON for DATA_DIR, FEATURE_DIR, and SPEC_FILE. All file paths must be absolute.
   Abort with error if spec file is missing (instruct user to run `/specify` first).

2. Scan data directory structure:
   - Identify JSON, CSV, and other structured data files
   - Parse file schemas to extract field names, data types, and relationships
   - Analyze file naming patterns and directory organization
   - Sample data values to infer validation rules and constraints

3. Extract domain entities:
   - Map data file schemas to business entities (e.g., Invoice, Payment, Supplier)
   - Identify primary keys, foreign keys, and relationships between entities
   - Infer entity lifecycles from data patterns and field combinations
   - Generate entity descriptions based on fields and usage patterns

4. Infer business rules:
   - Analyze data constraints, validation patterns, and value ranges
   - Identify business logic from field relationships and naming conventions
   - Extract workflow rules from data state transitions and timestamps
   - Generate testable business rule statements with specific criteria

5. Identify integration points:
   - Map data sources to external systems based on file paths and metadata
   - Identify file format dependencies and processing requirements
   - Extract API interfaces from data structure patterns
   - Document data flow and transformation requirements

6. Populate specification template:
   - Load current spec.md and identify template placeholders:
     * `[Entity Name]` sections in Key Entities
     * `[Business rule]` items in Business Rules
     * `[External System/API]` entries in Integration Points
   - Replace placeholders with extracted domain content
   - Maintain template structure and formatting
   - Add domain-specific examples and constraints

7. Generate domain analysis report:
   - Summary of entities discovered with field counts and relationships
   - List of business rules extracted with confidence levels
   - Integration points identified with data flow descriptions
   - Template sections populated with before/after comparison

8. Update specification file:
   - Write enhanced spec.md with populated domain content
   - Preserve existing functional requirements and user scenarios
   - Add domain-specific validation to acceptance criteria
   - Include data model references and entity relationships

9. Provide completion summary:
   - Report entities extracted, business rules identified
   - List template sections populated vs remaining placeholders
   - Recommend next steps based on domain completeness
   - Suggest areas needing manual review or clarification

Behavior rules:
- ONLY populate template placeholders, never modify existing content
- Preserve all existing functional requirements and user scenarios
- Generate business rules that are testable and measurable
- Maintain backwards compatibility with existing spec-kit workflow
- If data analysis fails, provide specific error messages and recovery steps
- Always include confidence levels for extracted business rules

Example output format:
```
Domain Analysis Complete:
- Entities discovered: 5 (Invoice, Payment, Supplier, MatchResult, ReconciliationRun)
- Business rules extracted: 12 (8 high confidence, 4 medium confidence)
- Integration points identified: 4 (MCP Server, File System, Sage Reports, SQLite)
- Template sections populated: Key Entities, Business Rules, Integration Points
- Specification file updated: specs/007-create-supplier-reconciliation-system/spec.md

Ready for next phase: Run '/clarify' to resolve any remaining ambiguities, then '/plan' for implementation planning.
```

## Usage Options

### Automatic Mode (Default)
```
/analyze-domain
```
Fully automated analysis with no user interaction required.

### Interactive Mode
```
/analyze-domain --interactive
```
Prompts user to validate and customize discovered entities, business rules, and integration points.

### Custom Data Directory
```
/analyze-domain --data-dir=/path/to/data
```
Analyze data from specific directory path.

### Setup Wizard
```
/analyze-domain --setup
```
Run guided setup to configure domain analysis preferences.

### Configuration File
```
/analyze-domain --config=/path/to/domain-config.yaml
```
Use saved configuration file with user preferences.

Context: {ARGS}