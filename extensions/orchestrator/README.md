# Intelligent Agent Orchestrator — Spec Kit Extension

Cross-catalog agent discovery and intelligent prompt-to-command routing for [Spec Kit](https://github.com/github/spec-kit).

## What It Does

| Capability | Description |
|-----------|-------------|
| **Route** | Match natural-language prompts to the best-fit Spec Kit command |
| **Index** | Build a unified capability index across core commands, extensions, workflows, and presets |
| **Discover** | Scan linked repositories for agent definitions (`.agent.md`, `SKILL.md`, etc.) |

## Quick Start

```bash
# Install the extension
specify extension add orchestrator

# Build the capability index
> /speckit.orchestrator.index

# Route a prompt to the best command
> /speckit.orchestrator.route "I want to create a spec for user authentication"
```

## Commands

### `/speckit.orchestrator.route`

Match a user prompt to the most relevant command:

```bash
> /speckit.orchestrator.route "set up git branching"

🎯 Routing Results:
  1  0.91  /speckit.git.feature     extension:git
  2  0.72  /speckit.git.initialize  extension:git
```

### `/speckit.orchestrator.index`

Index all available capabilities:

```bash
> /speckit.orchestrator.index

✅ Capability index built!
📊 Total: 15 capabilities indexed
```

### `/speckit.orchestrator.discover`

Find agents across linked repositories:

```bash
> /speckit.orchestrator.discover --all

🌐 Discovered 8 agents across 4 repositories
```

## Configuration

Edit `.specify/extensions/orchestrator/orchestrator-config.yml`:

```yaml
matching_strategy: "keyword"     # "keyword" or "weighted"
confidence_threshold: 0.5        # 0.0 - 1.0
cross_repo_scan: true

linked_repos:
  - path: "../frontend-app"
    name: "Frontend"
  - path: "../backend-api"
    name: "Backend API"
```

## How Routing Works

1. **Index** — Aggregates all capabilities from core commands, installed extensions, workflows, and presets into a single JSON index
2. **Score** — For each capability, computes relevance against the user prompt using keyword matching, description similarity, and name matching
3. **Rank** — Sorts by score, filters by confidence threshold
4. **Suggest** — Presents top matches with scores and offers to execute the best match

## Roadmap

- [ ] Semantic matching (beyond keyword-based)
- [ ] Integration as a native workflow `route` step type
- [ ] Catalog-level search aggregation
- [ ] Learning from user selections to improve future routing

## Author

**Pragya Chaurasia** — [pragya247](https://github.com/pragya247)

## License

MIT
