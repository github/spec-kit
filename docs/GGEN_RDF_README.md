# .specify - RDF-First Specification System

## Constitutional Equation

```
spec.md = μ(feature.ttl)
```

**Core Principle**: All specifications are Turtle/RDF ontologies. Markdown files are **generated** from TTL using Tera templates.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ RDF Ontology (Source of Truth)                             │
│ .ttl files define: user stories, requirements, entities    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ SPARQL queries
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Tera Template Engine                                        │
│ spec.tera template applies transformations                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ Rendering
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Markdown Artifact (Generated, Do Not Edit)                 │
│ spec.md, plan.md, tasks.md for GitHub viewing              │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
.specify/
├── ontology/                      # Ontology schemas
│   └── spec-kit-schema.ttl        # Vocabulary definitions (SHACL shapes, classes)
│
├── memory/                        # Project memory (architectural decisions)
│   ├── constitution.ttl           # Source of truth (RDF)
│   └── constitution.md            # Generated from .ttl
│
├── specs/NNN-feature/             # Feature specifications
│   ├── feature.ttl                # User stories, requirements, success criteria (SOURCE)
│   ├── entities.ttl               # Domain entities and relationships (SOURCE)
│   ├── plan.ttl                   # Architecture decisions (SOURCE)
│   ├── tasks.ttl                  # Task breakdown (SOURCE)
│   ├── spec.md                    # Generated from feature.ttl (DO NOT EDIT)
│   ├── plan.md                    # Generated from plan.ttl (DO NOT EDIT)
│   ├── tasks.md                   # Generated from tasks.ttl (DO NOT EDIT)
│   └── evidence/                  # Test evidence, artifacts
│       ├── tests/
│       ├── benchmarks/
│       └── traces/
│
└── templates/                     # Templates for generation
    ├── rdf-helpers/               # TTL templates for creating RDF instances
    │   ├── user-story.ttl.template
    │   ├── entity.ttl.template
    │   ├── functional-requirement.ttl.template
    │   └── success-criterion.ttl.template
    ├── spec.tera                  # Markdown generation template (SPARQL → Markdown)
    ├── plan-template.md           # Plan template (legacy, being replaced by plan.tera)
    └── tasks-template.md          # Tasks template (legacy, being replaced by tasks.tera)
```

## Workflow

### 1. Create Feature Specification (TTL Source)

```bash
# Start new feature branch
git checkout -b 013-feature-name

# Create feature directory
mkdir -p .specify/specs/013-feature-name

# Copy user story template
cp .specify/templates/rdf-helpers/user-story.ttl.template \
   .specify/specs/013-feature-name/feature.ttl

# Edit feature.ttl with RDF data
vim .specify/specs/013-feature-name/feature.ttl
```

**Example feature.ttl**:
```turtle
@prefix sk: <http://github.com/github/spec-kit#> .
@prefix : <http://github.com/ggen/specs/013-feature-name#> .

:feature a sk:Feature ;
    sk:featureName "Feature Name" ;
    sk:featureBranch "013-feature-name" ;
    sk:status "planning" ;
    sk:hasUserStory :us-001 .

:us-001 a sk:UserStory ;
    sk:storyIndex 1 ;
    sk:title "User can do X" ;
    sk:priority "P1" ;
    sk:description "As a user, I want to do X so that Y" ;
    sk:priorityRationale "Critical for MVP launch" ;
    sk:independentTest "User completes X workflow end-to-end" ;
    sk:hasAcceptanceScenario :us-001-as-001 .

:us-001-as-001 a sk:AcceptanceScenario ;
    sk:scenarioIndex 1 ;
    sk:given "User is logged in" ;
    sk:when "User clicks X button" ;
    sk:then "System displays Y" .
```

### 2. Validate RDF (SHACL)

```bash
# Validate against SHACL shapes
ggen validate .specify/specs/013-feature-name/feature.ttl

# Expected output:
# ✓ Priority values are valid ("P1", "P2", "P3")
# ✓ All required fields present
# ✓ Minimum 1 acceptance scenario per user story
# ✓ Valid RDF syntax
```

### 3. Generate Markdown Artifacts

```bash
# Regenerate spec.md from feature.ttl
ggen render .specify/templates/spec.tera \
            .specify/specs/013-feature-name/feature.ttl \
            > .specify/specs/013-feature-name/spec.md

# Or use cargo make target
cargo make speckit-render
```

### 4. Commit Both TTL and Generated MD

```bash
# Commit TTL source (required)
git add .specify/specs/013-feature-name/feature.ttl

# Commit generated MD (for GitHub viewing)
git add .specify/specs/013-feature-name/spec.md

git commit -m "feat(013): Add feature specification"
```

## NEVER Edit .md Files Directly

❌ **WRONG**:
```bash
vim .specify/specs/013-feature-name/spec.md  # NEVER DO THIS
```

✅ **CORRECT**:
```bash
# 1. Edit TTL source
vim .specify/specs/013-feature-name/feature.ttl

# 2. Regenerate markdown
ggen render .specify/templates/spec.tera \
            .specify/specs/013-feature-name/feature.ttl \
            > .specify/specs/013-feature-name/spec.md
```

## RDF Templates Reference

### User Story Template
- Location: `.specify/templates/rdf-helpers/user-story.ttl.template`
- Required fields: `storyIndex`, `title`, `priority`, `description`, `priorityRationale`, `independentTest`
- Priority values: **MUST** be `"P1"`, `"P2"`, or `"P3"` (SHACL validated)
- Minimum: 1 acceptance scenario per story

### Entity Template
- Location: `.specify/templates/rdf-helpers/entity.ttl.template`
- Required fields: `entityName`, `definition`, `keyAttributes`
- Used for: Domain model, data structures

### Functional Requirement Template
- Location: `.specify/templates/rdf-helpers/functional-requirement.ttl.template`
- Required fields: `requirementId`, `reqDescription`, `category`
- Categories: `"Functional"`, `"Non-Functional"`, `"Security"`, etc.

### Success Criterion Template
- Location: `.specify/templates/rdf-helpers/success-criterion.ttl.template`
- Required fields: `criterionId`, `scDescription`, `measurable`, `metric`, `target`
- Used for: Definition of Done, acceptance criteria

## SPARQL Queries (spec.tera)

The `spec.tera` template uses SPARQL to query the RDF graph:

```sparql
PREFIX sk: <http://github.com/github/spec-kit#>

SELECT ?storyIndex ?title ?priority ?description
WHERE {
    ?story a sk:UserStory ;
           sk:storyIndex ?storyIndex ;
           sk:title ?title ;
           sk:priority ?priority ;
           sk:description ?description .
}
ORDER BY ?storyIndex
```

## Integration with cargo make

```bash
# Verify TTL specs exist for current branch
cargo make speckit-check

# Validate TTL → Markdown generation chain
cargo make speckit-validate

# Regenerate all markdown from TTL sources
cargo make speckit-render

# Full workflow: validate + render
cargo make speckit-full
```

## Constitutional Compliance

From `.specify/memory/constitution.ttl` (Principle II):

> **Deterministic RDF Projections**: Every feature specification SHALL be defined as a Turtle/RDF ontology. Code and documentation are **projections** of the ontology via deterministic transformations (μ). NO manual markdown specifications permitted.

## SHACL Validation Rules

The `spec-kit-schema.ttl` defines SHACL shapes that enforce:

1. **Priority Constraint**: `sk:priority` must be exactly `"P1"`, `"P2"`, or `"P3"`
2. **Minimum Scenarios**: Each user story must have at least 1 acceptance scenario
3. **Required Fields**: All required properties must be present with valid datatypes
4. **Referential Integrity**: All links (e.g., `sk:hasUserStory`) must reference valid instances

## Benefits of RDF-First Approach

1. **Machine-Readable**: SPARQL queries enable automated analysis
2. **Version Control**: Diffs show semantic changes, not formatting
3. **Validation**: SHACL shapes catch errors before implementation
4. **Consistency**: Single source of truth prevents divergence
5. **Automation**: Generate docs, tests, code from single ontology
6. **Traceability**: RDF links specifications to implementation artifacts

## Migration from Markdown

If you have existing `.md` specifications:

```bash
# 1. Use ggen to parse markdown into RDF
ggen parse-spec .specify/specs/NNN-feature/spec.md \
               > .specify/specs/NNN-feature/feature.ttl

# 2. Validate the generated RDF
ggen validate .specify/specs/NNN-feature/feature.ttl

# 3. Regenerate markdown to verify
ggen render .specify/templates/spec.tera \
            .specify/specs/NNN-feature/feature.ttl \
            > .specify/specs/NNN-feature/spec-regenerated.md

# 4. Compare original vs regenerated
diff .specify/specs/NNN-feature/spec.md \
     .specify/specs/NNN-feature/spec-regenerated.md
```

## Troubleshooting

**Problem**: SHACL validation fails with "Priority must be P1, P2, or P3"

**Solution**: Change `sk:priority "HIGH"` to `sk:priority "P1"` (exact string match required)

---

**Problem**: Generated markdown missing sections

**Solution**: Ensure all required RDF predicates are present:
```turtle
:us-001 a sk:UserStory ;
    sk:storyIndex 1 ;           # Required
    sk:title "..." ;            # Required
    sk:priority "P1" ;          # Required
    sk:description "..." ;      # Required
    sk:priorityRationale "..." ; # Required
    sk:independentTest "..." ;  # Required
    sk:hasAcceptanceScenario :us-001-as-001 . # Min 1 required
```

---

**Problem**: `ggen render` command not found

**Solution**: Build ggen CLI:
```bash
cargo make build
./target/release/ggen render --help
```

## Further Reading

- [Spec-Kit Schema](./ontology/spec-kit-schema.ttl) - Full vocabulary reference
- [Constitution](./memory/constitution.ttl) - Architectural principles
- [ggen CLAUDE.md](../CLAUDE.md) - Development guidelines
- [Turtle Syntax](https://www.w3.org/TR/turtle/) - W3C specification
- [SPARQL Query Language](https://www.w3.org/TR/sparql11-query/) - W3C specification
- [SHACL Shapes](https://www.w3.org/TR/shacl/) - W3C specification
