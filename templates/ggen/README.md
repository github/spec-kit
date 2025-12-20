# ggen Integration for Spec-Kit

This directory contains [ggen](https://crates.io/crates/ggen) integration files for ontology-driven code generation in your Spec-Kit project.

## What is ggen?

ggen is an ontology-driven code generator that transforms RDF ontologies into typed code through SPARQL queries and Tera templates. It provides:

- **Single Source of Truth**: Define your domain model once in RDF, generate code for multiple languages
- **Semantic Validation**: Use OWL constraints to catch domain violations at generation time
- **Inference**: SPARQL CONSTRUCT queries materialize implicit relationships before code generation
- **Deterministic Output**: Same ontology + templates = identical output (reproducible builds)

## Prerequisites

1. Install Rust and cargo:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. Install ggen:
   ```bash
   cargo install ggen
   ```

3. Verify installation:
   ```bash
   ggen --version  # Should show: ggen 5.0.0
   ```

## Quick Start

### 1. Initialize ggen in your project

Copy the ggen configuration and templates to your project root:

```bash
# From your spec-kit project root
cp templates/ggen.toml .
cp -r templates/schema .
cp -r templates/ggen .
```

### 2. Review the example ontology

Check out `schema/example-domain.ttl` to see an example RDF ontology that models a project management domain (Project, Task, User, Comment).

### 3. Generate code

Run ggen to generate code from your ontology:

```bash
# Generate all templates
ggen sync

# Preview changes without writing files
ggen sync --dry-run

# Generate to a specific output directory
ggen sync --to src/generated/
```

### 4. Customize for your domain

1. **Edit the ontology** (`schema/example-domain.ttl`):
   - Add your domain classes (e.g., `spec:Order`, `spec:Customer`)
   - Define properties with appropriate types
   - Add relationships between classes

2. **Choose your templates**:
   - `python-dataclass.tera` - Python dataclasses with type hints
   - `typescript-interface.tera` - TypeScript interfaces
   - `rust-struct.tera` - Rust structs with Serde support

3. **Configure ggen.toml**:
   - Set `output_dir` to your desired location
   - Enable `incremental = true` to preserve manual edits
   - Configure `formatting` for your language

## Project Structure

```
your-project/
├── ggen.toml                    # ggen configuration
├── schema/
│   ├── example-domain.ttl       # Your domain ontology (RDF/Turtle)
│   └── inference-rules.ttl      # SPARQL CONSTRUCT rules for inference
├── templates/ggen/
│   ├── python-dataclass.tera    # Python code generation template
│   ├── typescript-interface.tera # TypeScript code generation template
│   └── rust-struct.tera         # Rust code generation template
└── src/generated/               # Generated code (output_dir)
    ├── domain.py
    ├── types.ts
    └── models.rs
```

## Integration with Spec-Driven Development

ggen complements the Spec-Driven Development workflow:

1. **Specification Phase** (`/speckit.specify`):
   - Define your domain concepts in the specification
   - Identify entities, relationships, and constraints

2. **Ontology Modeling** (new step):
   - Model your domain in RDF using the specification as a guide
   - Define classes, properties, and OWL constraints
   - Add SPARQL inference rules for derived relationships

3. **Planning Phase** (`/speckit.plan`):
   - Reference the ontology in your implementation plan
   - Use `ggen sync` to generate initial data models
   - Choose target languages and templates

4. **Task Breakdown** (`/speckit.tasks`):
   - Include ggen sync as a task in your implementation
   - Plan for integrating generated code with application logic

5. **Implementation** (`/speckit.implement`):
   - Run `ggen sync` to generate/update data models
   - Implement business logic using the generated types
   - Preserve manual edits with `// MANUAL` comments

## Preserving Manual Edits

ggen supports incremental sync to preserve your manual changes:

1. Enable in `ggen.toml`:
   ```toml
   [generation]
   incremental = true
   ```

2. Mark custom code with `// MANUAL` comments:
   ```python
   @dataclass
   class User:
       # Generated properties
       name: str
       email: str

       # MANUAL: Custom validation (preserved during sync)
       def validate_email(self) -> bool:
           return "@" in self.email
   ```

3. Run incremental sync:
   ```bash
   ggen sync --mode incremental
   ```

## Using SPARQL Inference

ggen can materialize implicit relationships before code generation using SPARQL CONSTRUCT queries:

1. Define inference rules in `schema/inference-rules.ttl`:
   ```turtle
   spec:TaskAssignmentRule a ggen:ConstructQuery ;
       ggen:query """
           PREFIX spec: <https://example.com/spec-kit#>
           CONSTRUCT {
               ?user spec:assignedTask ?task .
           }
           WHERE {
               ?task spec:taskAssignee ?user .
           }
       """ .
   ```

2. ggen will execute these queries during sync and add the inferred triples to the knowledge graph before generating code.

## CI/CD Integration

Add ggen to your CI/CD pipeline to verify generated code is up-to-date:

```yaml
# .github/workflows/codegen.yml
name: Code Generation
on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo install ggen
      - run: ggen sync --mode verify
      - name: Fail if generated code is out of sync
        run: git diff --exit-code src/generated/
```

## Examples

### Example 1: Generate Python models

```bash
# 1. Edit your ontology
vim schema/example-domain.ttl

# 2. Configure for Python
vim ggen.toml
# Set: templates_dir = "templates/ggen/python-dataclass.tera"
# Set: output_dir = "src/models/"

# 3. Generate
ggen sync

# 4. Check the output
cat src/models/domain.py
```

### Example 2: Multi-language generation

```toml
# ggen.toml
[generation]
templates_dir = "templates/ggen/"
output_dir = "src/generated/"

# Generate all templates: python, typescript, rust
```

## Resources

- [ggen Documentation](https://docs.ggen.io)
- [ggen Crates.io Page](https://crates.io/crates/ggen)
- [RDF Tutorial](https://www.w3.org/TR/rdf11-primer/)
- [SPARQL Tutorial](https://www.w3.org/TR/sparql11-query/)
- [Tera Template Engine](https://keats.github.io/tera/)

## Troubleshooting

### Error: "ggen: command not found"

Make sure cargo's bin directory is in your PATH:
```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

### Error: "Failed to load ontology"

Check your RDF syntax:
```bash
# Validate Turtle syntax
rapper -i turtle -o ntriples schema/example-domain.ttl > /dev/null
```

### Generated code has wrong types

Check the type mappings in your Tera template:
- `xsd:string` → Python: `str`, TypeScript: `string`, Rust: `String`
- `xsd:integer` → Python: `int`, TypeScript: `number`, Rust: `i64`
- `xsd:dateTime` → Python: `datetime`, TypeScript: `Date`, Rust: `DateTime<Utc>`

## Contributing

If you create useful templates or ontologies for common domains, consider contributing them back to the spec-kit project!
