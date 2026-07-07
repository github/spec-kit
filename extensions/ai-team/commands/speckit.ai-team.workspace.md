---
description: "Create or update the AI Team workspace contract for requirements/coding repository roles and privacy boundaries."
---

# AI Team Workspace Contract

Define the enterprise AI Team workspace contract before using the SDD workflow.
This command does not replace `specify init`. It runs after a Spec Kit project
exists and records the enterprise repository roles that AI Team commands need.

## User Input

```text
$ARGUMENTS
```

## Goal

Create or update `.specify/extensions/ai-team/ai-team-config.yml` so every
agent can distinguish:

- the requirements-internal repository: private demand, drafts, approval
  discussion, wave plan, and commercial context;
- the requirements-published repository: sanitized public requirement/RFC URLs;
- the coding repository: source code, public plan, tasks, implementation PR,
  self-test evidence, Evidence Board, and optional read-only requirements
  submodule.

## Bootstrap Rule

If the current repository has no `.specify/` directory, stop and bootstrap with
Spec Kit first. Do not copy AI Team template repositories into the product
workspace.

Recommended commands:

```bash
specify init --here --integration <codex|claude|cursor-agent|trae>
specify extension add ai-team
specify extension add agent-context
specify extension add bug
```

Use `--force` only when the user has explicitly accepted merging Spec Kit files
into a non-empty repository.

After extension installation, run this command and then run
`speckit.agent-context.update` when agent context files should be refreshed.

## Steps

1. Confirm `.specify/` exists. If it does not, stop with the bootstrap command
   above.
2. Read `.specify/init-options.json` and `.specify/integration.json` when
   present. Record the active AI integration instead of asking again when it is
   one of `codex`, `claude`, `cursor-agent`, or `trae`.
3. Read `.specify/extensions/ai-team/ai-team-config.yml` if it exists. If it is
   missing, create it from the extension config template.
4. Ask for or infer only the repository facts that are safe to record:
   - coding repository path or URL;
   - published requirements repository URL;
   - published requirements submodule path, commonly `requirements/`;
   - whether a stable published requirement URL is required for feature work;
   - whether this config is committed in the coding repository.
5. Do not record the private requirements-internal path or URL in committed
   coding-repository files. If the operator needs that path, keep it in a local
   private config outside the coding repository or in the requirements-internal
   repository itself.
6. Confirm URL-oriented requirement references:
   - new feature work links the published requirement URL;
   - local submodule paths are allowed for reading cached published content but
     are not authoritative work-item references;
   - the coding repository does not know `requirements-internal` exists.
7. Record the role model:
   - specify role: product manager / customer manager;
   - plan role: architect;
   - tasks and implement role: developer.
8. Confirm context isolation:
   - the architect reads the published requirement and handoff, not raw product
     chat;
   - the developer reads approved spec, plan, tasks, gates, and published
     requirement URL, not hidden architect or private requirement chat;
   - roles pass information through documents.
9. Confirm related extensions:
   - `ai-team` for enterprise gates and evidence;
   - `agent-context` for managed AGENTS/CLAUDE/Cursor/Trae context sections;
   - `bug` for bug assess/fix/test stages.
10. Output the workspace contract summary.

## Output Shape

```text
AI Team workspace:
- coding repo:
- requirements-published repo:
- requirements submodule path:
- requirements-internal recorded in coding repo: no
- authoritative feature reference: published URL
- raw customer demand public: yes / no
- public plan allowed: yes / no
- active AI integration:
- related extensions: ai-team / agent-context / bug
- role isolation: enabled / missing
- next command:
```

## Stop Conditions

Stop and ask when:

- coding and requirements-published repository roles cannot be distinguished;
- the project has not been initialized with `specify init`;
- private requirements-internal path or URL would be committed in the coding
  repository;
- raw customer demand would be written to a public repository without explicit
  approval;
- context isolation is disabled but the project handles enterprise customer
  demand.
