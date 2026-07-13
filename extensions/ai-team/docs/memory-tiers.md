# AI Team Memory Tiers

AI Team memory is not one bucket. Different lessons have different maturity,
privacy, and authority. Use three tiers so contributors can capture experience
early without accidentally turning unreviewed notes into official guidance.

```text
local memory -> department memory -> enterprise memory
```

Promotion is intentional. A repeated lesson is a review signal, not automatic
authority.

## Tier Summary

| Tier | Upload | Lives under docs | Appears in formal releases | Git policy | Typical owner |
|---|---|---|---|---|---|
| local memory | no | no | no | generated Git ignore | individual contributor |
| department memory | yes, internal | no | no | generated Git ignore plus internal service sync | maintainer or team lead |
| enterprise memory | yes, controlled | yes | yes when relevant | commit after review | maintainer, architecture owner, or technical committee |

## Local Memory

Local memory is private contributor memory.

Default path:

```text
.specify/ai-team/memory/local/
```

Use local memory for:

- raw debugging notes;
- failed attempts that are not reviewed;
- personal prompts or command traces;
- work-in-progress bug hypotheses;
- temporary notes while a feature or bugfix is still moving.

Rules:

- do not upload by default;
- do not place in `docs/`;
- do not treat as an instruction to other agents;
- sanitize before promotion;
- run the installed memory adapter, which generates a managed `.gitignore`
  block before writing local memory.

## Department Memory

Department memory is shared team memory that has not become formal guidance.

Default path:

```text
.specify/ai-team/memory/department/
```

Use department memory for:

- bugfix lessons useful to the team;
- repeated review findings;
- integration quirks;
- reusable prompt patterns;
- debugging playbooks that still need more evidence;
- lessons that are safe inside the department but not ready for public docs.

Rules:

- keep the coding-repository cache Git-ignored and upload only to approved
  internal memory services;
- do not put in `docs/`;
- do not include in release documentation by default;
- mark owner, privacy, evidence, and expiry;
- promote to enterprise memory only after owner review.

## Enterprise Memory

Enterprise memory is long-lived, reviewed guidance.

Default path:

```text
docs/ai-team/memory/
```

Use enterprise memory for:

- accepted architecture decisions;
- compatibility commitments;
- bugfix playbooks that prevent repeat incidents;
- migration playbooks for similar projects;
- reusable module/API/config/test patterns;
- security, dependency, operations, and release guidance.

Rules:

- must be sanitized for the target audience;
- must have owner approval;
- should be indexed and discoverable by AI coding tools;
- may appear in release artifacts;
- may guide future projects, but still ranks below current source, current
  spec, current plan, and current owner decisions.

## Adapter Model

The default adapter is local file storage. It atomically writes a validated card,
updates a local index, and ensures local/department/private-release paths are
ignored by Git. A Mem0 adapter is optional and mirrors sanitized department or
enterprise cards using the official `MemoryClient.add` interface.

The memory shape remains compatible with mem0-style memory:

- a memory entry is a small card, not a raw transcript;
- metadata includes tier, owner, privacy, source work item, module, code graph
  nodes, evidence, created date, expiry, and superseded status;
- retrieval is scoped by task, repository role, work type, capability, module,
  and memory tier;
- local memory stays local unless explicitly promoted;
- department memory syncs to an internal namespace;
- enterprise memory syncs to a controlled namespace and has a docs copy.

Suggested namespaces:

```text
ai-team/<org>/<project>/local/<contributor-id>
ai-team/<org>/<project>/department/<team-id>
ai-team/<org>/<project>/enterprise
```

## Promotion Flow

```text
contributor captures local lesson
-> sanitize and submit to department memory
-> maintainer reviews evidence and scope
-> owner approves enterprise guidance when durable
-> docs and release artifacts reference enterprise memory
```

Promotion checks:

- Is the lesson still true against current source?
- Is it supported by evidence?
- Is private customer or commercial context removed?
- Is the owner clear?
- Does it expire or become superseded?
- Should it become a skill, hook, test, gate, or code graph rule instead of
  remaining only as memory?

## Relationship To Release Archive

`speckit.ai-team.memory-consolidate` can run at any time.
`speckit.ai-team.release-archive` is a release-scoped batch view of the same
idea.

Release archive should:

- collect feature and bugfix lessons from the release range;
- promote only reviewed lessons to enterprise memory;
- keep unreviewed lessons in department memory;
- leave contributor scratch in local memory;
- include enterprise memory in release documentation when it is long-lived
  guidance.

## Stop Conditions

Stop before writing or syncing memory when:

- the tier is unclear;
- private data would leave its approved boundary;
- a contributor is publishing someone else's local notes;
- a department lesson is being treated as official enterprise guidance;
- the memory conflicts with current source, spec, plan, issue, release notes, or
  owner decision;
- mem0 or another memory service lacks an approved namespace and access boundary.
- the local file adapter cannot install or verify its managed Git ignore block.
