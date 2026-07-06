---
description: "Create or update the AI Team workspace contract for coding/enhancement repository roles and project privacy boundaries."
---

# AI Team Workspace Contract

Define the enterprise AI Team workspace contract before using the SDD workflow.

## User Input

```text
$ARGUMENTS
```

## Goal

Create or update `.specify/extensions/ai-team/ai-team-config.yml` so every
agent can distinguish:

- the enhancement repository: private demand, feature issue, approval, wave
  plan, and acceptance intent;
- the coding repository: source code, public plan, tasks, implementation PR,
  self-test evidence, and Evidence Board.

## Steps

1. Read `.specify/extensions/ai-team/ai-team-config.yml` if it exists. If it is
   missing, create it from the extension config template.
2. Ask for or infer only the repository facts that are safe to record:
   - enhancement repository path or URL;
   - coding repository path or URL;
   - whether the two roles are physically the same repository;
   - visibility of raw customer demand;
   - whether public plan artifacts are allowed.
3. Record the role model:
   - specify role: product manager / customer manager;
   - plan role: architect;
   - tasks and implement role: developer.
4. Confirm context isolation:
   - the architect reads the spec and handoff, not raw product chat;
   - the developer reads approved spec, plan, tasks, and gates, not hidden
     architect chat;
   - roles pass information through documents.
5. Output the workspace contract summary.

## Output Shape

```text
AI Team workspace:
- enhancement repo:
- coding repo:
- same physical repo: yes / no
- raw customer demand public: yes / no
- public plan allowed: yes / no
- role isolation: enabled / missing
- next command:
```

## Stop Conditions

Stop and ask when:

- repository roles cannot be distinguished;
- raw customer demand would be written to a public repository without explicit
  approval;
- context isolation is disabled but the project handles enterprise customer
  demand.
