# Lean Workflow

A minimal preset that strips the Spec Kit workflow down to its essentials — just the prompt, just the artifact.

## When to Use

Use Lean when you want the structured specify → plan → tasks → implement pipeline without the ceremony of the full templates. Each command produces a single focused Markdown file with no boilerplate sections to fill in.

## Commands Included

| Command | Output | Description |
|---------|--------|-------------|
| `speckit.specify` | `spec.md` | Create a specification from a feature description |
| `speckit.plan` | `plan.md` | Create an implementation plan from the spec |
| `speckit.tasks` | `tasks.md` | Create dependency-ordered tasks from spec and plan |
| `speckit.implement` | *(code)* | Execute all tasks in order, marking progress |
| `speckit.constitution` | `constitution.md` | Create or update the project constitution |

## What It Replaces

Lean overrides the five core workflow commands with self-contained prompts that produce each artifact directly — no separate template files involved. The result is a shorter, more direct workflow.

## Installation

```bash
# Lean is a bundled preset — no download needed
specify preset add lean
```

## Development

```bash
# Test from local directory
specify preset add --dev ./presets/lean

# Verify commands resolve
specify preset resolve speckit.specify

# Remove when done
specify preset remove lean
```

## License

MIT

## Cost Profile

Lean uses approximately 67% fewer tokens per spec/plan/tasks cycle than the
standard templates. The reduced prompt size also makes haiku the appropriate
model tier for all lean commands.

| Command | Lean | Standard | Reduction |
|---------|------|----------|-----------|
| `speckit.specify` | ~800 tokens | ~2,400 tokens | ~67% |
| `speckit.plan` | ~1,200 tokens | ~3,600 tokens | ~67% |
| `speckit.tasks` | ~600 tokens | ~1,800 tokens | ~67% |
| `speckit.implement` | ~500 tokens | ~500 tokens | ~0% |
| `speckit.constitution` | ~400 tokens | ~1,200 tokens | ~67% |

*Token estimates are approximate and vary with input size.*

### When to Use Lean by Priority

| Priority | Recommendation |
|----------|---------------|
| **P1** | Use standard. P1 features justify full artifacts and review gates. |
| **P2** | Lean is suitable. Reduced boilerplate still produces reviewable artifacts. |
| **P3** | Lean is preferred. Minimal investment for exploratory or low-risk changes. |
