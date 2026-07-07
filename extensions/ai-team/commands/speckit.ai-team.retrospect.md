---
description: "Convert failed PRs, checks, incidents, or repeated AI mistakes into durable process improvements."
---

# AI Team Retrospect

Close the learning loop after AI-assisted work fails. This command does not
edit production code by default.

## User Input

```text
$ARGUMENTS
```

## Failure Classes

| Class | Meaning | Likely improvement |
|---|---|---|
| context missing | AI did not load the right requirement, module, or owner | Task Context Package or auto-load rule |
| graph missing | AI misunderstood source structure or impact radius | code graph slice or impact command update |
| skill missing | workflow lacked a step or decision gate | command/skill update |
| hook missing | repeated mechanical mistake was not blocked early | hook or script |
| gate missing | risky change reached PR without evidence | policy or PR gate |
| evidence missing | tests or reports did not prove behavior | self-test, contract test, or Evidence Board |
| human decision missing | AI decided something that needed authority | maintainer, technical committee, or architecture route |
| privacy leak | private requirement context entered public/coding artifacts | repository boundary or handoff gate |

## Workflow

1. Identify the failed artifact: PR, review, test, incident, issue, or repeated
   correction.
2. Reconstruct the expected flow:
   - work item;
   - coding issue, handoff requirement URL, or bug slug;
   - task context from `.specify/ai-team/tasks/<task-id>/`;
   - code graph impact;
   - evidence;
   - human decision.
3. Classify the failure.
4. Propose the smallest durable change:
   - update an AI Team command;
   - update a knowledge map;
   - add a check or hook;
   - add or adjust a self-test;
   - add a code graph overlay note;
   - record decision memory or curated attempt memory.
5. Separate immediate fix from process improvement.
6. Update the Task Context Package with failure class, durable improvement,
   current phase, and follow-up command when the task is not done.

## Output Shape

```text
Failure retrospective:
- task id:
- context path:
- failure source:
- linked issue or PR:
- coding issue, handoff requirement URL, or bug slug:
- expected flow:
- actual failure:
- failure class:
- missed stop condition:
- missed evidence:
- proposed immediate fix:
- proposed durable improvement:
- repository to change:
- memory entry: decision / attempt / none
- required human approver:
- follow-up command:
```

## Stop Conditions

Stop and ask when:

- the failure source is unavailable;
- the durable improvement changes public interfaces or module ownership without
  human approval;
- a production incident needs incident response before process cleanup;
- repeated failure has no owner to accept the new gate or rule.
