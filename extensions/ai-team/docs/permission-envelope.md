# AI Team Permission Envelope

The Permission Envelope records what one AI Team task may read, write, execute,
and access over the network. It is task-scoped and lives beside the Change
Package.

It does not claim that every AI coding tool has a sandbox. The envelope must
state how its restrictions are enforced.

## Storage And Shape

```text
.specify/ai-team/work/<work_slug>/permission-envelope.yml
```

```yaml
schema_version: "1.0"
work_slug: 003-search-export
mode: analysis
enforcement_mode: policy-only
integration: codex
allow:
  read_paths:
    - AGENTS.md
    - specs/003-search-export
    - src/upload
    - tests/upload
  write_paths: []
  commands:
    - rg
    - git diff
  network:
    - none
deny:
  read_paths:
    - .env
    - credentials
  write_paths:
    - .git
    - other-module-internals
  commands:
    - destructive-history-rewrite
    - unreviewed-package-install
  network:
    - upload-source-or-private-data
approval_required:
  - expand-write-paths
  - public-contract-change
  - cross-module-change
  - dependency-install
  - external-network-write
runtime:
  adapter: ""
  verified: false
  gaps:
    - policy is not a runtime sandbox
approved_by: ""
updated_at: ""
```

Paths must be repository-relative and as narrow as practical. Do not use broad
wildcards when the affected module is known.

## Enforcement Modes

| Mode | Meaning | Allowed claim |
|---|---|---|
| `policy-only` | prompts, repository rules, and human gates describe the boundary | "boundary recorded" |
| `agent-native` | the selected AI tool's native sandbox or approval controls are configured and verified | "native controls verified" |
| `wrapper-enforced` | file, command, and network operations pass through a team-owned enforcement adapter | "wrapper controls verified" |

Default to `policy-only`. Never upgrade the mode because a tool usually has a
sandbox; record the concrete adapter or configuration and verification result.

Spec Kit workflow gates can pause work but do not sandbox shell commands. A
workflow command runs with the current user's privileges unless an external
agent or wrapper constrains it.

## Lifecycle

1. At intake, create an analysis envelope with read-only paths and commands.
2. Before code graph or source analysis, a human reviews sensitive reads and
   network access.
3. After plan and task review, revise the envelope for the smallest write paths,
   commands, and dependency operations needed for implementation.
4. Before implementation, a human approves the revised envelope.
5. Evidence records the effective enforcement mode and any operations that
   required approval.
6. Expanding the envelope requires another human decision; AI agents cannot
   self-authorize.

## Stop Conditions

Stop when:

- the work slug, repository role, or target module is unknown;
- a required read, write, command, or network action is outside the envelope;
- private data may leave its approved repository or service boundary;
- hard runtime confinement is required but only `policy-only` is available;
- an AI tool requests broader access without a named human approval;
- the envelope and Work Context Package identify different work units.

## Tool Adapters

Tool-specific enforcement belongs behind an adapter. An adapter should report:

- supported controls: read, write, command, network, approval prompts;
- applied configuration and scope;
- verification evidence;
- unsupported controls and fallback stop conditions.

Codex, Claude Code, Cursor Agent, and Trae may expose different controls. The
shared envelope remains stable while adapters translate it into tool-specific
settings when available.
