# Skill, Knowledge, and Memory Support

AI Team SDD work needs three external support layers around the requirements
and coding repositories.

```text
Skill = how to perform repeatable work
Knowledge = what is true about this project now
Memory = what humans already decided or what past attempts taught us
```

## Skill Layer

Skills are procedural capabilities: reusable workflows, checklists, scripts, and
tool recipes. They should be invoked only when relevant and should not become a
large always-loaded instruction file.

Default sources:

- bundled Spec Kit commands and extensions;
- AI Team extension commands;
- project-local skills;
- reviewed third-party skills such as Agent Skills compatible repositories,
  Claude Code skills, OpenAI Codex skills, Superpowers, or other mature
  engineering skill libraries.

Third-party sources to review before writing a new generic skill:

- Agent Skills format and compatible skill repositories;
- Claude Code bundled or project skills for debugging, code review, run, and
  verify flows;
- OpenAI Codex skills, AGENTS guidance, and repo-level instruction patterns;
- Superpowers engineering skills for planning, executing plans, testing,
  receiving review, requesting review, and skill writing.

Reuse policy:

1. Search for existing skills before writing a new one.
2. Prefer reuse when a skill already covers a generic engineering behavior:
   planning, TDD, debugging, running, verifying, code review, documentation, or
   security review.
3. Adapt when the skill is useful but lacks enterprise boundaries:
   role isolation, repository privacy, evidence board, or human approval.
4. Reject when the skill is too broad, unreviewed, tool-specific in a way that
   breaks our flow, unsafe, or license-incompatible.
5. Record provenance: source, license, version or commit, local changes, owner,
   and whether the skill is adopted unchanged, adapted, or only referenced.

Skill is procedural memory. It should describe how to work, not project facts.

## Knowledge Layer

Knowledge is the current project model that agents need for correct reasoning.
It should be mostly source-derived, reviewed, and updateable.

Minimum knowledge map:

- glossary and domain terms;
- stakeholder and role definitions;
- repository roles and privacy boundary;
- product scope and non-goals;
- module ownership and review routes;
- code graph slices and source structure;
- public API/SPI/contracts/config/metrics/events;
- capability index and reusable components;
- dependency and license inventory;
- test and self-test map;
- release and operations boundaries;
- known integration environments;
- migration and compatibility rules.

Useful knowledge mechanisms:

- source-derived code graph for classes, interfaces, callers, callees, and
  dependency direction;
- module cards for human-owned boundaries and responsibilities;
- glossary or `CONTEXT.md` style terminology for project-specific words;
- public contract index for SPI/API/config/events/metrics;
- capability index for reusable components, forbidden reinventions, and
  preferred extension points;
- evidence index for self-tests, release checks, and known environment limits;
- dependency and license inventory for open-source component decisions.

Knowledge should be indexed by task. An agent should not need to read every doc;
it should load the relevant knowledge slice for the current Work Context Package.

## Memory Layer

Memory stores historical context. It must not override current source, spec,
plan, issue, or human approval.

There are two useful memory types.

### Decision Memory

Decision memory records durable human decisions:

- architecture decisions;
- rejected designs and reasons;
- compatibility commitments;
- security and license decisions;
- release and operations decisions;
- team-specific precedents.

Decision memory can guide agents when humans are offline, but only when:

- the decision has an owner;
- the decision has a date and scope;
- the decision links to evidence or an issue/PR;
- the decision has not expired or been superseded.

### Attempt Memory

Attempt memory records curated lessons from past attempts:

- failed PR patterns;
- repeated review comments;
- failed checks;
- incident remediation;
- debugging paths that did or did not work;
- prompts or skills that caused drift;
- successful playbooks for similar tasks.

Attempt memory is useful, but only as curated episode summaries. Do not store
raw transcripts by default. Keep the outcome, context, evidence, and lesson.

Use attempt memory for:

- preventing repeated mistakes;
- choosing a known debugging path;
- providing few-shot examples for similar work;
- improving skills, gates, tests, or knowledge maps.

Do not use attempt memory to:

- bypass a current spec, plan, code graph, or owner review;
- remember secrets or private customer details;
- justify a design without current evidence;
- preserve every failed experiment forever.

## Precedence

When sources disagree, use this order:

1. current source code and tests;
2. current spec, plan, tasks, and linked issues;
3. current module docs, code graph, contracts, and knowledge map;
4. approved decision memory;
5. curated attempt memory;
6. unreviewed chat or model inference.

## Recommended Artifacts

```text
.specify/ai-team/support/
|-- skill-inventory.md
|-- knowledge-map.md
`-- memory-index.md

.specify/ai-team/memory/
|-- decisions/
|   `-- <date>-<slug>.md
`-- attempts/
    `-- <date>-<slug>.md
```

These files may stay local or be committed depending on repository privacy.
Enterprise teams should keep customer-sensitive memory in the internal
enhancement repository, expose only sanitized handoff knowledge where visibility
allows it, and commit only coding-safe plan-level knowledge to the coding
repository.

## References To Review

Keep these as sources to evaluate, not as automatic dependencies:

- Agent Skills format and public skill repositories;
- Anthropic Claude Code skills and project skill loading;
- OpenAI Codex skills and repository instruction files;
- Superpowers engineering skill libraries.
