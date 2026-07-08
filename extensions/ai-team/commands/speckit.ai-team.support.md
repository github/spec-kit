---
description: "Audit and maintain the external Skill, Knowledge, and Memory support layers for AI Team SDD work."
---

# AI Team Support Layers

Audit the Skill, Knowledge, and Memory support layers around the current SDD
project.

## User Input

```text
$ARGUMENTS
```

## Goal

Create or update support artifacts so agents can reuse reviewed skills, load
the right project knowledge, and apply historical decisions or curated attempt
lessons without relying on hidden chat context.

## Steps

1. Locate the project root and `.specify/`.
2. Read:
   - `.specify/extensions/ai-team/ai-team-config.yml` when present;
   - current feature spec, plan, tasks, and gate files when present;
   - project agent files such as `AGENTS.md`, `CLAUDE.md`, Cursor rules, or
     equivalent;
   - project docs, module docs, code graph outputs, test maps, and evidence
     boards when present.
3. Create `.specify/ai-team/support/` when missing.
4. Produce or update `skill-inventory.md`:
   - local skills;
   - Spec Kit commands/extensions;
   - project-specific skills;
   - third-party skills considered for reuse, including Agent Skills compatible
     repositories, Claude Code skills, OpenAI Codex skills, Superpowers, or
     other mature engineering skill libraries;
   - adopt/adapt/reject decision;
   - provenance, license, version or commit, local changes, and owner.
5. Produce or update `knowledge-map.md`:
   - glossary;
   - repository roles;
   - module boundaries;
   - code graph slices;
   - capability index;
   - public contracts;
   - dependency/license/security inventory;
   - self-test and evidence map;
   - missing knowledge.
6. Produce or update `memory-index.md`:
   - decision memory entries;
   - attempt memory entries;
   - owner, scope, date, evidence, expiry/superseded status;
   - privacy classification.
7. Classify memory precedence:
   - decision memory may guide default choices when current source, spec, plan,
     issue, and owner decisions do not conflict;
   - attempt memory is advisory only and must be converted into a skill,
     knowledge entry, gate, or test before it becomes a repeatable rule.
8. Recommend what should be committed and what should remain private or local.

## Output Shape

```markdown
# AI Team Support Audit

- **Project**:
- **Feature**:
- **Support status**: pass / revise / blocked

## Skill Layer

- reusable skills found:
- third-party sources reviewed:
- third-party skills to adopt:
- third-party skills to adapt:
- skills to reject:
- missing skills:

## Knowledge Layer

- knowledge sources found:
- code graph or source structure:
- capability index:
- public contracts:
- missing knowledge:

## Memory Layer

- decision memory:
- attempt memory:
- privacy classification:
- stale or superseded memory:
- missing memory:

## Recommended Actions

## Stop Conditions
```

## Stop Conditions

Stop and ask when:

- a third-party skill would be installed without source, license, and safety
  review;
- raw customer demand or secrets would be written into a public coding
  repository;
- memory conflicts with current source, spec, plan, or owner decision;
- attempt memory is being treated as binding decision memory.
