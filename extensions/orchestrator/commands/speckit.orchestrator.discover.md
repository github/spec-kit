---
description: "Discover agents and capabilities across linked repositories"
---

# Discover Cross-Repository Agents

Scan linked repositories for agent definitions, skill files, and capability manifests. Builds a unified view of all available agents across your development ecosystem.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user may provide a specific repo path or URL to scan.

## Prerequisites

1. Ensure Git is available (`git rev-parse --is-inside-work-tree`)
2. Load orchestrator configuration from `.specify/extensions/orchestrator/orchestrator-config.yml`

## Step 1: Identify Repositories to Scan

Determine which repositories to scan:

### Option A: Current Repository

Always scan the current working directory.

### Option B: Linked Repositories

Check for linked repos in orchestrator config:

```yaml
# orchestrator-config.yml
linked_repos:
  - path: "../frontend-app"
    name: "Frontend"
  - path: "../backend-api"
    name: "Backend API"
  - path: "../shared-libs"
    name: "Shared Libraries"
```

### Option C: Git Submodules

If the current repo has submodules, include them:

```bash
if [ -f ".gitmodules" ]; then
  echo "📂 Found git submodules, including in scan..."
  git submodule foreach --quiet 'echo $toplevel/$path'
fi
```

## Step 2: Scan Each Repository

For each repository, search for agent-related files:

```bash
echo "🔍 Scanning repository: $repo_name ($repo_path)"

# Scan for these patterns:
scan_patterns=(
  ".agent.md"
  "SKILL.md"
  "AGENTS.md"
  ".claude/skills/*.md"
  ".github/copilot-instructions.md"
  ".specify/extensions/*/extension.yml"
  ".specify/workflows/*/workflow.yml"
  ".kimi/skills/*.md"
)

for pattern in "${scan_patterns[@]}"; do
  find "$repo_path" -path "*/$pattern" -type f 2>/dev/null
done
```

## Step 3: Parse Discovered Files

For each discovered file, extract agent metadata:

### Agent Files (`.agent.md`, `SKILL.md`)

Extract:
- **Name**: From the first `# Heading` in the file
- **Description**: From the first paragraph or `description` frontmatter
- **Triggers**: Keywords and phrases that indicate when this agent should be invoked
- **Capabilities**: List of actions the agent can perform

### Extension Manifests (`extension.yml`)

Extract:
- **Extension ID**: From `extension.id`
- **Commands**: From `provides.commands[]`
- **Tags**: From `tags[]`

### Workflow Definitions (`workflow.yml`)

Extract:
- **Workflow ID**: From `workflow.id`
- **Steps**: From `steps[]` — what the workflow can do
- **Integrations**: Which AI agents it supports

## Step 4: Build Discovery Report

Generate a human-readable report and machine-readable JSON:

```bash
echo ""
echo "🌐 Cross-Repository Agent Discovery Report"
echo "════════════════════════════════════════════"
echo ""
echo "📂 Repositories Scanned: 3"
echo ""
echo "  Repository          Agents  Commands  Workflows"
echo "  ──────────────────  ──────  ────────  ─────────"
echo "  Current (spec-kit)    2       13        1"
echo "  Frontend              1        0        0"
echo "  Backend API           1        3        0"
echo ""
echo "🤖 Discovered Agents:"
echo ""
echo "  Agent                    Repo           Type"
echo "  ───────────────────────  ─────────────  ──────────"
echo "  Claude Code Agent        Current        .agent.md"
echo "  Copilot Instructions     Current        .github"
echo "  API Testing Agent        Backend API    SKILL.md"
echo "  UI Component Helper      Frontend       .agent.md"
echo ""
echo "💾 Full report saved to .specify/extensions/orchestrator/discovery-report.json"
echo ""
```

## Step 5: Update the Capability Index

Merge discovered agents into the main orchestrator index:

```bash
echo "🔄 Updating capability index with discovered agents..."
# Merge into .specify/extensions/orchestrator/index.json
echo "✅ Index updated with cross-repo agents"
```

## Notes

- Discovery scans local file system only — repos must be cloned
- Files are parsed for metadata, not executed
- Large monorepos may take longer to scan — use `scan_patterns` in config to narrow scope
- Run periodically or after pulling changes in linked repos

## Examples

### Example 1: Scan current repo

```bash
> /speckit.orchestrator.discover

🌐 Discovered 4 agents across 1 repository
```

### Example 2: Scan specific repo

```bash
> /speckit.orchestrator.discover ../backend-api

🌐 Discovered 2 agents in backend-api
```

### Example 3: Scan all linked repos

```bash
> /speckit.orchestrator.discover --all

🌐 Discovered 8 agents across 4 repositories
```
