---
description: "Index all available commands, extensions, workflows, and presets"
---

# Index Capabilities

Scan and index all available Spec Kit capabilities — core commands, installed extensions, workflows, and presets — into a unified searchable index for intelligent routing.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user may specify flags like `--force` to rebuild the index or `--verbose` for detailed output.

## Prerequisites

1. Ensure the project has been initialized (`specify init` has been run)
2. Check that `.specify/` directory exists

## Step 1: Discover Core Commands

Enumerate all built-in Spec Kit commands and their descriptions:

| Command | Description | Keywords |
|---------|-------------|----------|
| `speckit.constitution` | Set up project constitution and rules | constitution, rules, setup, project |
| `speckit.specify` | Generate a specification from a feature description | spec, specification, feature, describe, requirements |
| `speckit.clarify` | Clarify and refine a specification | clarify, refine, questions, ambiguity |
| `speckit.plan` | Generate an implementation plan from a specification | plan, implementation, design, architecture |
| `speckit.tasks` | Break down a plan into actionable tasks | tasks, breakdown, issues, work items |
| `speckit.implement` | Implement code from tasks | implement, code, build, develop |
| `speckit.checklist` | Generate a review checklist | checklist, review, verify, quality |
| `speckit.analyze` | Analyze existing code or specifications | analyze, analysis, inspect, audit |

## Step 2: Discover Installed Extensions

Scan the extension registry at `.specify/extensions/.registry`:

```bash
registry_file=".specify/extensions/.registry"

if [ -f "$registry_file" ]; then
  echo "📦 Scanning installed extensions..."
  # Parse registry JSON for each extension
  # For each extension, read its extension.yml manifest
  # Extract: id, commands[], description, tags[]
fi
```

For each installed extension:
1. Read `.specify/extensions/{ext_id}/extension.yml`
2. Extract all commands from `provides.commands[]`
3. Extract keywords from `tags[]` and description
4. Record source as `extension:{ext_id}`

## Step 3: Discover Installed Workflows

Scan the workflow registry at `.specify/workflows/workflow-registry.json`:

```bash
workflow_registry=".specify/workflows/workflow-registry.json"

if [ -f "$workflow_registry" ]; then
  echo "🔄 Scanning installed workflows..."
  # Parse registry for each workflow
  # Extract: id, name, description, tags
fi
```

For each installed workflow:
1. Read the workflow YAML definition
2. Extract: id, name, description, steps (for keyword extraction)
3. Record source as `workflow:{workflow_id}`

## Step 4: Discover Installed Presets

Scan the preset registry at `.specify/presets/.registry`:

```bash
preset_registry=".specify/presets/.registry"

if [ -f "$preset_registry" ]; then
  echo "📝 Scanning installed presets..."
  # Parse registry for each preset
fi
```

## Step 5: Cross-Repository Scan (Optional)

If `cross_repo_scan` is enabled in config, scan for agent files in linked repositories:

```bash
echo "🔍 Scanning for cross-repo agents..."

# Scan patterns from config (default):
# - .agent.md
# - SKILL.md
# - AGENTS.md

# For each discovered file:
# 1. Parse name, description, trigger phrases
# 2. Add to index as type: "external-agent"
# 3. Record source as "repo:{repo_path}"
```

## Step 6: Build and Save the Index

Compile all discovered capabilities into a unified index:

```bash
output_file=".specify/extensions/orchestrator/index.json"

cat > "$output_file" <<EOF
{
  "schema_version": "1.0",
  "generated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "capabilities": [
    ... all discovered capabilities ...
  ],
  "stats": {
    "core_commands": 8,
    "extension_commands": 5,
    "workflows": 1,
    "presets": 1,
    "external_agents": 0,
    "total": 15
  }
}
EOF

echo ""
echo "✅ Capability index built successfully!"
echo ""
echo "📊 Index Statistics:"
echo "  • Core commands:      8"
echo "  • Extension commands: 5"
echo "  • Workflows:          1"
echo "  • Presets:            1"
echo "  • External agents:    0"
echo "  ──────────────────────"
echo "  • Total:              15"
echo ""
echo "💾 Index saved to $output_file"
echo ""
```

## Notes

- The index is a static JSON file — no runtime dependencies
- Re-run this command after installing/removing extensions or workflows
- Cross-repo scanning requires the repos to be cloned locally
- Use `--force` to rebuild the index from scratch (ignore cache)

## Examples

### Example 1: Build index

```bash
> /speckit.orchestrator.index

✅ Capability index built successfully!
📊 Total: 15 capabilities indexed
```

### Example 2: Force rebuild

```bash
> /speckit.orchestrator.index --force

🔄 Rebuilding index from scratch...
✅ Capability index rebuilt! 15 capabilities indexed
```
