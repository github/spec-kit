---
description: "Match a user prompt to the best-fit command across all catalogs"
---

# Intelligent Prompt Router

Match a user's natural-language request to the most relevant Spec Kit command, extension, or workflow by searching across all installed catalogs.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input as the prompt to route.

## Prerequisites

1. Verify the orchestrator index exists at `.specify/extensions/orchestrator/index.json`
2. If the index does not exist, run `/speckit.orchestrator.index` first to build it
3. Load orchestrator configuration from `.specify/extensions/orchestrator/orchestrator-config.yml` (use defaults if missing)

## Step 1: Load the Capability Index

Load the cached capability index:

```bash
index_file=".specify/extensions/orchestrator/index.json"

if [ ! -f "$index_file" ]; then
  echo "⚠️ Index not found. Building index first..."
  # Trigger index rebuild
fi

echo "📋 Loaded capability index"
```

The index contains entries in this format:

```json
{
  "capabilities": [
    {
      "id": "speckit.specify",
      "type": "core-command",
      "name": "Specify",
      "description": "Generate a specification from a feature description",
      "keywords": ["spec", "specification", "feature", "describe", "requirements"],
      "source": "core"
    },
    {
      "id": "speckit.git.feature",
      "type": "extension-command",
      "name": "Create Feature Branch",
      "description": "Create a feature branch with sequential or timestamp numbering",
      "keywords": ["git", "branch", "feature", "create"],
      "source": "extension:git"
    }
  ]
}
```

## Step 2: Score Each Capability Against the Prompt

For each capability in the index, compute a relevance score:

1. **Keyword match** (weight: 0.4) — Count how many of the capability's keywords appear in the user prompt
2. **Description match** (weight: 0.3) — Check if words from the user prompt appear in the capability description
3. **Name match** (weight: 0.2) — Check if the capability name is mentioned or closely related
4. **Type bonus** (weight: 0.1) — Prefer workflows > extension commands > core commands for complex prompts; prefer core commands for simple ones

Normalize scores to a 0.0–1.0 range.

## Step 3: Rank and Filter Results

1. Sort capabilities by score (descending)
2. Apply the confidence threshold from config (default: 0.5)
3. Take the top 5 results that exceed the threshold

## Step 4: Present Results

Display the routing results to the user:

```bash
echo ""
echo "🎯 Routing Results for: \"$ARGUMENTS\""
echo ""
echo "  Rank  Score  Command                        Source"
echo "  ────  ─────  ─────────────────────────────  ──────────"
echo "  1     0.92   /speckit.specify                core"
echo "  2     0.78   /speckit.orchestrator.discover   extension"
echo "  3     0.61   sdd-full-cycle (workflow)        workflow"
echo ""
echo "💡 Suggested: Run /speckit.specify to proceed"
echo ""
```

If no results exceed the threshold:

```bash
echo ""
echo "🤷 No confident match found for: \"$ARGUMENTS\""
echo ""
echo "Suggestions:"
echo "  • Try rephrasing your request"
echo "  • Run /speckit.orchestrator.index to refresh the index"
echo "  • Use 'specify extension search <query>' to browse available extensions"
echo ""
```

## Step 5: Offer to Execute

If a top result has confidence ≥ 0.8, offer to execute it:

```bash
echo "Would you like me to run /speckit.specify with your prompt? (y/n)"
```

## Notes

- The routing is deterministic (keyword-based) — no external AI API calls required
- Scores are cached per prompt in `.specify/extensions/orchestrator/route-cache.json`
- Re-run `/speckit.orchestrator.index` after installing new extensions to update the index

## Examples

### Example 1: Finding the right command

```bash
> /speckit.orchestrator.route "I want to create a specification for a login feature"

🎯 Routing Results:
  1  0.95  /speckit.specify         core
  2  0.62  /speckit.plan            core
```

### Example 2: Cross-catalog discovery

```bash
> /speckit.orchestrator.route "set up git branching for my project"

🎯 Routing Results:
  1  0.91  /speckit.git.feature     extension:git
  2  0.72  /speckit.git.initialize  extension:git
```

### Example 3: Workflow matching

```bash
> /speckit.orchestrator.route "run the full development cycle end to end"

🎯 Routing Results:
  1  0.88  sdd-full-cycle           workflow:speckit
  2  0.54  /speckit.specify         core
```
