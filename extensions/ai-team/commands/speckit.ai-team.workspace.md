---
description: "Create or update the AI Team workspace contract for coding repository and internal enhancement boundaries."
---

# AI Team Workspace Contract

Define the enterprise AI Team workspace contract before using the SDD workflow.
This command does not replace `specify init`. It runs after a Spec Kit project
exists and records the repository roles that AI Team commands need.

## User Input

```text
$ARGUMENTS
```

## Goal

Create or update `.specify/extensions/ai-team/ai-team-config.yml` so every
agent can distinguish:

- the coding repository: source code, public issues, public-safe plan, tasks,
  implementation PR, self-test evidence, and Evidence Board;
- the optional internal enhancement repository: confidential enterprise demand,
  approval discussion, wave plan, commercial context, and internal handoff
  URLs.

Public feature requests may start directly in the coding repository. The
internal enhancement repository is internal-only, not customer-visible, and is
used for traceability when demand cannot be public.

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
   - whether public feature requests should start as coding issues;
   - whether an internal enhancement repository exists for confidential
     enterprise demand;
   - approved handoff URL pattern, if the coding repository may cite it;
   - whether this config is committed in the coding repository.
5. Do not record private raw-demand paths, internal draft links, or customer
   source material in committed public coding-repository files.
6. Confirm work-item references:
   - bug fixes link coding issues or bug slugs;
   - public feature work links coding issues or SDD feature requests;
   - confidential enterprise feature work uses an accepted enhancement-internal
     issue or handoff URL only where visibility allows it, otherwise a
     public-safe summary;
   - enhancement-internal issues use `type/feature` only; bug fixes are routed
     to coding repository issues.
7. Record the role model:
   - specify role: product manager / customer manager;
   - plan role: architect;
   - tasks and implement role: developer.
8. Confirm context isolation:
   - the architect reads spec and handoff documents, not raw product chat;
   - the developer reads approved spec, plan, tasks, gates, and allowed work
     item context, not hidden architect or private requirement chat;
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
- internal enhancement repo: none / configured outside public repo / link allowed
- handoff URL pattern:
- public feature route: coding issue
- confidential feature route: internal enhancement handoff or public-safe summary
- raw customer demand public: yes / no
- public plan allowed: yes / no
- active AI integration:
- related extensions: ai-team / agent-context / bug
- role isolation: enabled / missing
- next command:
```

## Stop Conditions

Stop and ask when:

- coding and internal enhancement repository roles cannot be distinguished for
  confidential work;
- the project has not been initialized with `specify init`;
- private enhancement paths, internal issue URLs, or raw customer demand would
  be committed to a public coding repository;
- raw customer demand would be written to any public repository without
  explicit approval;
- context isolation is disabled but the project handles enterprise customer
  demand.
