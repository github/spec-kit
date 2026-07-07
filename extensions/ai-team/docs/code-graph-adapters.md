# Code Graph Adapters

AI Team SDD treats source code as the first truth and a code graph as the first
projection for impact analysis. The extension should not depend on one fixed
graph backend. Teams can start with a file-backed generator and replace it with
a service, MCP tool, or commercial platform later.

## Adapter Contract

Every adapter should produce the same normalized artifact shape:

```text
.specify/ai-team/work/<work_slug>/codegraph/
|-- nodes.jsonl
|-- edges.jsonl
|-- summary.md
`-- adapter-report.md
```

Required node kinds when present:

```text
repository, module, package, file, class, interface, function, method, config, test
```

Required edge kinds when inferable:

```text
contains, imports, calls, implements, extends, reads_config, tests, depends_on
```

`adapter-report.md` records adapter name, version, command, license review,
source snapshot, confidence, skipped evidence, and fallback reason.

## Open Source Candidates

| Candidate | Good fit | Strength | Caution |
|---|---|---|---|
| [SCIP](https://github.com/scip-code/scip) (`scip-code/scip`) | default normalized code intelligence format when language indexers exist | precise symbol/index format with Apache-2.0 license | needs language-specific indexers and conversion to AI Team node/edge JSONL |
| [Joern](https://github.com/joernio/joern) (`joernio/joern`) | security-sensitive or data-flow-heavy analysis | Code Property Graph for several languages with Apache-2.0 license | heavier runtime and query model; best as optional adapter |
| [CodeQL](https://github.com/github/codeql) (`github/codeql`) | security, data-flow, and semantic queries | mature databases and query libraries with MIT repository license | CLI/database setup and GitHub licensing terms must be reviewed for the deployment |
| [jQAssistant](https://github.com/jQAssistant/jqassistant) (`jQAssistant/jqassistant`) | Java/Maven architecture rule checks | graph-backed architecture analysis over Neo4j | GPL-3.0; do not make it a default dependency without license approval |
| [Kythe](https://github.com/kythe/kythe) (`kythe/kythe`) | large cross-language cross-reference indexing | pluggable code indexing ecosystem with Apache-2.0 license | powerful but heavy for a first default |
| [tree-sitter](https://github.com/tree-sitter/tree-sitter) (`tree-sitter/tree-sitter`) | fallback local parser | incremental parser with MIT license and broad language coverage | produces syntax structure, not full semantic call graph by itself |
| [ast-grep](https://github.com/ast-grep/ast-grep) (`ast-grep/ast-grep`) | structural search and lint-like checks | fast AST-based CLI with MIT license | complements graph generation; not a complete graph service |

Avoid GPL tools as default dependencies for enterprise templates. They can be
documented as optional local tools only after legal review and without copying
their code into product repositories.

## Recommended Default

Use a two-layer default:

1. **SCIP-first adapter contract** for teams that can install language indexers.
2. **tree-sitter/source-structure fallback** for every repository so AI agents
   still get file, package, class, function, import, and test relationship
   evidence when no external graph service is available.

Then add optional adapters for Joern, CodeQL, jQAssistant, Kythe, or commercial
graph services by mapping their output into the normalized artifact shape.

## When To Run

Run `speckit.ai-team.codegraph` before implementation when:

- a task touches SPI/API, abstract base classes, public config, wire/event
  shapes, metrics, database or middleware dependencies;
- classes or public modules are added or deleted;
- the change crosses module boundaries;
- the AI agent cannot identify the owner module from source structure;
- a paused task resumes after source or requirement changes.

For small bug fixes that stay inside one file, a source-structure fallback may
be enough if the context pack records the confidence and tests.
