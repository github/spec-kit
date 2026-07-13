# AI Team SDD bundle

One-step bootstrap for enterprise AI Team Spec-Driven Development in a coding
repository.

## What it installs

| Kind | ID | Purpose |
|------|-----|---------|
| Extension | `ai-team` | Enterprise SDD commands, hooks, and work context |
| Extension | `bug` | Bug assess/fix/test stages for bugfix workflow |
| Extension | `agent-context` | Managed Spec Kit section in agent context files |
| Preset | `ai-team-sdd-governance` | Work-item traceability, handoff reading, checks, evidence |
| Workflow | `ai-team-intake` | Plain-language intake → issue → formal handoff |
| Workflow | `ai-team-sdd` | Feature / new-project SDD cycle |
| Workflow | `ai-team-bugfix` | Bug fix lifecycle with evidence |

This bundle is **integration-agnostic** but AI Team workflows require one of:
`codex`, `claude`, `cursor-agent`, or `trae`. Pass `--integration` on init.

## Usage

**Install by bundle id** after registering the catalog (once per project). See
[`../README.md`](../README.md) for the catalog/maintainer model.

```bash
specify init . --integration cursor-agent
specify bundle catalog add https://raw.githubusercontent.com/EuphoriaYan/spec-kit/main/bundles/catalog.json \
  --id ai-team --policy install-allowed
specify bundle info ai-team
specify bundle install ai-team
```

`specify bundle install ai-team` also initializes an uninitialized directory
(after the catalog is registered). Component references resolve from bundled
assets shipped in this distribution's CLI where applicable.

### Validate and build artifact

Authoring commands use `--path` on the bundle directory:

```bash
specify bundle validate --path bundles/ai-team --offline
specify bundle build --path bundles/ai-team --output dist/
specify bundle install ai-team-0.1.0.zip --integration cursor-agent
```

## After install

1. Run `speckit.ai-team.workspace` to record repository boundaries.
2. Optionally run `speckit.agent-context.update` when using the agent-context extension.
3. Start work with `speckit.ai-team.start` or `specify workflow run ai-team-intake`.
