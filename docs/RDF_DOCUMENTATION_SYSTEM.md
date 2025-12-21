# RDF Documentation System

## Overview

This document describes the Spec-Kit RDF Documentation System - a comprehensive refactoring of project documentation to Turtle RDF format, implementing the constitutional equation:

```
documentation.md = μ(documentation.ttl)
```

## Philosophy

The Spec-Kit project treats documentation as a first-class semantic artifact. Rather than maintaining Markdown files as the source of truth, we now use Turtle RDF files as the authoritative source. Markdown documentation is generated from RDF using deterministic transformations via ggen v6.

**Benefits:**
- **Machine-Readable**: Documentation is structured data that can be validated and queried
- **Single Source of Truth**: All documentation derives from RDF, eliminating duplication
- **Automated Generation**: Markdown is generated, ensuring consistency across documents
- **Semantic Relationships**: Cross-references and dependencies are explicit in RDF
- **Validation**: SHACL shapes enforce documentation quality and completeness
- **Deterministic**: Same RDF input always produces identical Markdown output

## Architecture

### Core Components

#### 1. **Ontology** (`ontology/`)

- **`spec-kit-schema.ttl`** - Core Spec-Kit ontology (unchanged)
- **`spec-kit-docs-extension.ttl`** - Documentation ontology extension with:
  - **Classes**: Guide, Principle, Changelog, ConfigurationOption, Workflow phases, etc.
  - **Properties**: Documentation metadata, relationships, validation rules
  - **SHACL Shapes**: Validation constraints for documentation quality

#### 2. **RDF Documentation** (`docs/`, `memory/`)

- **`memory/documentation.ttl`** - Root documentation metadata container
- **`memory/philosophy.ttl`** - Constitutional principles (converted from spec-driven.md)
- **`memory/changelog.ttl`** - Version history and release notes
- **`docs/*.ttl`** - Individual guide documentation files

#### 3. **Transformation Configuration** (`docs/ggen.toml`)

- Defines 13 RDF-to-Markdown transformations
- SPARQL query specifications
- Template bindings
- Validation rules and pipeline stages

#### 4. **SPARQL Queries** (`sparql/`)

- **`guide-query.rq`** - Extract guide documentation metadata
- **`principle-query.rq`** - Extract constitutional principles
- **`changelog-query.rq`** - Extract release information
- **`config-query.rq`** - Extract configuration options
- **`workflow-query.rq`** - Extract workflow phases and steps

#### 5. **Tera Templates** (`templates/`)

- **`philosophy.tera`** - Render principles to Markdown
- **`guide.tera`** - Generic guide rendering
- **`configuration-reference.tera`** - Configuration option reference
- **`changelog.tera`** - Changelog rendering

## Transformation Pipeline

The complete transformation pipeline follows the five-stage μ function:

```
μ₁: Normalize    → Load RDF files, validate SHACL shapes
     ↓
μ₂: Extract      → Execute SPARQL queries against RDF
     ↓
μ₃: Emit         → Render Tera templates with query results
     ↓
μ₄: Canonicalize → Format Markdown (line endings, whitespace)
     ↓
μ₅: Receipt      → Generate SHA256 hash proving determinism
```

## Supported Documentation Types

### 1. Guides (`sk:Guide`)
- Purpose-driven procedural documentation
- Properties: purpose, audience, prerequisites, sections
- Examples: Installation, Quick Start, Development Setup
- Output: Structured guide Markdown

### 2. Principles (`sk:Principle`)
- Constitutional principles and core philosophy
- Properties: principleId, index, rationale, examples, violations
- Rendering: Principle-centric with supporting arguments
- Output: Philosophy documentation

### 3. Changelog (`sk:Changelog`)
- Version history and release information
- Contains: releases (sk:Release) with changes (sk:Change)
- Change types: Added, Fixed, Changed, Deprecated, Removed, Security
- Output: Semantic versioning changelog

### 4. Configuration (`sk:ConfigurationOption`)
- Configuration settings and CLI options
- Properties: name, type, default, required, examples
- Grouping: By category
- Output: Reference table format

### 5. Workflows (`sk:WorkflowPhase`, `sk:WorkflowStep`)
- Multi-step procedures and workflows
- Hierarchical: Phases contain steps
- Properties: description, index, ordering
- Output: Step-by-step procedural guide

### 6. Governance (`sk:Governance`)
- Project rules, policies, and procedures
- Properties: rule, description, enforcement, procedure
- Examples: Code of Conduct, Contributing Guidelines, Security Policy

## Documentation Status Map

| Document | RDF File | Status | Next Phase |
|---|---|---|---|
| README.md | `docs/overview.ttl` | ⏳ Planned | Convert guide content to RDF |
| spec-driven.md | `memory/philosophy.ttl` | ⏳ Planned | Extract and structure principles |
| RDF_WORKFLOW_GUIDE.md | `docs/rdf-workflow.ttl` | ⏳ Planned | Create workflow RDF instances |
| docs/installation.md | `docs/installation.ttl` | ⏳ Planned | Structure installation steps |
| docs/quickstart.md | `docs/quickstart.ttl` | ⏳ Planned | Create quickstart workflow |
| docs/local-development.md | `docs/development.ttl` | ⏳ Planned | Document dev setup process |
| AGENTS.md | `docs/agents.ttl` | ⏳ Planned | Extract agent configurations |
| CONTRIBUTING.md | `docs/contributing.ttl` | ⏳ Planned | Structure contribution rules |
| CHANGELOG.md | `memory/changelog.ttl` | ⏳ Planned | Structure release information |
| GGEN_RDF_README.md | `docs/ggen-integration.ttl` | ⏳ Planned | Document ggen architecture |
| CODE_OF_CONDUCT.md | `docs/code-of-conduct.ttl` | ⏳ Planned | Embed as governance |
| SECURITY.md | `docs/security-policy.ttl` | ⏳ Planned | Structure security rules |
| SUPPORT.md | `docs/support.ttl` | ⏳ Planned | Create support guide |
| docs/upgrade.md | `docs/upgrade.ttl` | ⏳ Planned | Document upgrade procedure |
| docs/index.md | Memory | ✅ Complete | Auto-generated from metadata |

## Usage

### Running Transformations

Generate all Markdown documentation from RDF:

```bash
ggen sync --config docs/ggen.toml
```

Generate specific documentation:

```bash
ggen sync --config docs/ggen.toml --spec project-overview
ggen sync --config docs/ggen.toml --spec specification-driven-philosophy
```

### Validating Documentation

Validate all documentation RDF against SHACL shapes:

```bash
ggen validate --config docs/ggen.toml
```

### Adding New Documentation

1. **Create RDF file** in appropriate location:
   - Guides → `docs/your-guide.ttl`
   - Principles → `memory/philosophy.ttl` (append to existing)
   - Changelog → `memory/changelog.ttl`

2. **Define instances** using documentation ontology classes:
   ```turtle
   sk:YourGuide
     a sk:Guide ;
     sk:documentTitle "Your Guide Title" ;
     sk:documentDescription "Description..." ;
     sk:purpose "Why this guide exists" ;
     ...
   ```

3. **Add transformation** to `docs/ggen.toml`:
   ```toml
   [[transformations.specs]]
   name = "your-guide"
   input_files = ["docs/your-guide.ttl"]
   # ... rest of configuration
   ```

4. **Create template** in `templates/` if needed

5. **Run transformation**:
   ```bash
   ggen sync --config docs/ggen.toml --spec your-guide
   ```

## SHACL Validation

All documentation RDF is validated against SHACL shapes defined in `spec-kit-docs-extension.ttl`. Shapes ensure:

- Required properties are present
- Property values are correct types
- String lengths meet minimums
- Identifiers follow patterns
- Enum values are valid
- Relationships are consistent

Validation runs automatically during transformations (stage μ₁).

## Examples

### Creating a Guide

```turtle
@prefix sk: <http://github.com/github/spec-kit#> .

sk:MyGuide
  a sk:Guide ;
  sk:documentTitle "My Guide" ;
  sk:documentDescription "A comprehensive guide about X" ;
  sk:purpose "Help users understand X" ;
  sk:audience "Users new to X" ;
  sk:prerequisites "Basic knowledge of Y" ;
  sk:guideSections "Introduction, Core Concepts, Advanced Usage, Troubleshooting" ;
  sk:maintenanceStatus "Current" ;
  sk:lastUpdatedDate "2025-12-21T00:00:00Z"^^xsd:dateTime ;
  .
```

### Creating a Configuration Option

```turtle
sk:ConfigOption1
  a sk:ConfigurationOption ;
  sk:configName "verbose" ;
  sk:configDescription "Enable verbose output during transformations" ;
  sk:configType "boolean" ;
  sk:configDefault "false" ;
  sk:configRequired false ;
  sk:configExamples "verbose=true" ;
  sk:inCategory sk:GeneralCategory ;
  .
```

### Adding a Release to Changelog

```turtle
sk:Release1_0_0
  a sk:Release ;
  sk:versionNumber "1.0.0" ;
  sk:releaseDate "2025-12-21T00:00:00Z"^^xsd:dateTime ;
  sk:breakingChanges false ;
  sk:hasChange sk:Change1_0_0_1 ;
  sk:hasChange sk:Change1_0_0_2 ;
  .

sk:Change1_0_0_1
  a sk:Change ;
  sk:changeType "Added" ;
  sk:changeDescription "Support for RDF documentation transformation" ;
  .
```

## Maintenance and Updates

### Updating Documentation

1. Edit the corresponding `.ttl` file (source of truth)
2. Run `ggen sync --config docs/ggen.toml`
3. Markdown files are automatically regenerated
4. Commit both `.ttl` source files and generated `.md` files

### Validating Changes

Before committing:

```bash
ggen sync --config docs/ggen.toml
ggen validate --config docs/ggen.toml
```

Both must succeed for documentation to be valid.

### Cross-References

Use `sk:documentLinks` and `sk:relatedDocuments` to create semantic relationships between documents.

## File Organization

```
spec-kit/
├── ontology/
│   ├── spec-kit-schema.ttl              # Core ontology
│   └── spec-kit-docs-extension.ttl      # Documentation ontology (NEW)
├── memory/
│   ├── constitution.md                  # Existing
│   ├── documentation.ttl                # Documentation root (NEW)
│   ├── philosophy.ttl                   # Philosophy/principles (NEW)
│   └── changelog.ttl                    # Changelog (NEW)
├── docs/
│   ├── ggen.toml                        # Transformation config (NEW)
│   ├── overview.ttl                     # Overview guide (NEW)
│   ├── rdf-workflow.ttl                 # Workflow guide (NEW)
│   ├── installation.ttl                 # Installation guide (NEW)
│   ├── quickstart.ttl                   # Quick start guide (NEW)
│   ├── development.ttl                  # Development guide (NEW)
│   ├── agents.ttl                       # Agents guide (NEW)
│   ├── contributing.ttl                 # Contributing guide (NEW)
│   ├── ggen-integration.ttl             # ggen guide (NEW)
│   ├── upgrade.ttl                      # Upgrade guide (NEW)
│   ├── code-of-conduct.ttl              # CoC governance (NEW)
│   ├── security-policy.ttl              # Security policy (NEW)
│   ├── support.ttl                      # Support guide (NEW)
│   ├── RDF_DOCUMENTATION_SYSTEM.md      # This file (NEW)
│   └── RDF_WORKFLOW_GUIDE.md            # Generated from rdf-workflow.ttl
├── templates/
│   ├── philosophy.tera                  # Philosophy template (NEW)
│   ├── guide.tera                       # Guide template (NEW)
│   ├── configuration-reference.tera     # Config template (NEW)
│   └── changelog.tera                   # Changelog template (NEW)
├── sparql/
│   ├── guide-query.rq                   # Guide extraction (NEW)
│   ├── principle-query.rq               # Principle extraction (NEW)
│   ├── changelog-query.rq               # Changelog extraction (NEW)
│   ├── config-query.rq                  # Config extraction (NEW)
│   └── workflow-query.rq                # Workflow extraction (NEW)
└── tests/
    └── validation/
        └── doc-shapes.ttl               # Documentation SHACL shapes (NEW)
```

## Git Workflow

### Source Files (Always Commit)
- `*.ttl` files in ontology/, memory/, docs/
- `*.rq` files in sparql/
- `*.tera` files in templates/
- `ggen.toml` configuration

### Generated Files (Commit After Generation)
- `.md` files generated from RDF
- Include header comment: `<!-- Auto-generated from RDF, do not edit manually -->`

### .gitignore Considerations
You may choose to:
1. **Commit generated files** (simpler for end-users)
2. **Ignore generated files** (leaner repo, requires build step)

Current recommendation: **Commit generated files** for consistency with existing README.md.

## Future Enhancements

- [ ] Automated documentation linting via SPARQL queries
- [ ] Cross-reference validation during transformation
- [ ] Documentation dependency analysis
- [ ] Auto-generated table of contents from RDF structure
- [ ] Multi-language documentation support via RDF language tags
- [ ] API documentation generation from ontology
- [ ] Audit trail for documentation changes

## References

- [Spec-Kit Philosophy](../spec-driven.md) - Core SDD principles
- [RDF Workflow Guide](RDF_WORKFLOW_GUIDE.md) - RDF development workflow
- [SHACL Specification](https://www.w3.org/TR/shacl/) - Shape validation
- [SPARQL Query Language](https://www.w3.org/TR/sparql11-query/) - Data extraction
- [Tera Template Engine](https://keats.github.io/tera/) - Template rendering

---

*This RDF documentation system implements the Spec-Kit constitutional equation, ensuring that all documentation is generated deterministically from semantic specifications.*
