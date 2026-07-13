---
description: "Consolidate AI Team work experience into local, department, or enterprise memory with privacy review and optional mem0-style service sync."
---

# AI Team Memory Consolidate

Convert completed feature, bugfix, review, incident, or release experience into
curated memory. Maintainers and contributors may run this command whenever a
useful lesson is ready; it is not restricted to release time.

This command does not edit production code by default.

## User Input

```text
$ARGUMENTS
```

Useful arguments:

- `scope=work-item|bugfix|feature|incident|release|migration|manual`
- `work_slug=<work-slug>` or `work_slugs=<comma-separated-work-slugs>`
- `bug_slug=<bug-slug>` for bugfix lessons
- `release_id=<version-or-release-candidate>` when consolidating a release
- `since_tag=<previous-release-tag>` and `target_tag=<release-tag-or-rc-tag>`
- `source_issue_url=<coding-or-internal-issue-url>`
- `target_tier=local|department|enterprise`
- `privacy=private|department-internal|public-safe`
- `memory_service=file|mem0` (`file` is the safe default)

## Goal

Distill noisy task artifacts into reusable memory:

- bugfix symptoms, root causes, missing detections, and future guards;
- feature and architecture decisions that future projects should inherit;
- migration playbooks for similar projects;
- repeated AI mistakes that should become skills, gates, tests, hooks, or code
  graph rules;
- lessons that should remain local, be shared with the department, or become
  enterprise guidance.

## Three Memory Tiers

| Tier | Upload? | Formal docs? | Release artifact? | Git policy | Purpose |
|---|---|---|---|---|---|
| local memory | no | no | no | ignore or local-only | private scratch, personal debugging trail, unreviewed lessons |
| department memory | yes, internal | no | no | internal-only repository or service sync | shared team experience before it becomes official guidance |
| enterprise memory | yes, controlled | yes | yes when relevant | commit after review | long-lived, reviewed guidance for projects and releases |

### Local Memory

Default path:

```text
.specify/ai-team/memory/local/
```

Local memory is not uploaded by default. It may include raw notes, failed
attempts, and contributor-specific debugging context, but it must not be treated
as authoritative by other agents.

### Department Memory

Default path:

```text
.specify/ai-team/memory/department/
```

Department memory is uploaded to a controlled internal location, but it does not
live under `docs/` and does not become part of formal release records. Use it
for team-shared bugfix lessons, reusable snippets, and recently discovered
patterns that still need more review.

### Enterprise Memory

Default path:

```text
docs/ai-team/memory/
```

Enterprise memory is reviewed, public-safe for the target audience, and carried
with formal project documentation and releases. It is suitable for long-term
architecture guidance, compatibility rules, bugfix playbooks, and migration
patterns that future projects should load early.

## Memory Adapter

The installed executable adapter is
`.specify/extensions/ai-team/scripts/memory_adapter.py`. The local file adapter
is always available and is the source of truth. The optional Mem0 adapter
mirrors an already sanitized department or enterprise card; it does not replace
the local record.

Before writing memory, generate the managed ignore block:

```text
python .specify/extensions/ai-team/scripts/memory_adapter.py --ensure-ignore
```

Write candidate cards under the ignored
`.specify/ai-team/memory/staging/` directory, then persist a reviewed card:

```text
python .specify/extensions/ai-team/scripts/memory_adapter.py \
  --source <card-path> --tier <local|department|enterprise> \
  --backend <file|mem0>
```

`mem0` requires the optional `mem0ai` package, `MEM0_API_KEY` (or the configured
environment variable), and a non-empty namespace for the selected tier. Local
or `privacy: private` cards are rejected by the remote adapter.

The adapter follows a mem0-like contract:

- memory entries are small, structured cards;
- each card has metadata, evidence links, privacy classification, owner, and
  expiry or superseded status;
- retrieval is scoped by work type, module, capability, source graph node,
  release, and memory tier;
- raw transcripts are not stored by default;
- current source, spec, plan, issue, and owner decisions always outrank memory.

Teams may implement this with mem0, another vector/memory service, files only,
or an internal service. The AI Team contract is the artifact shape and
precedence rules, not a mandatory backend.

## Entry Shapes

### Bugfix Lesson

```markdown
---
memory_type: bugfix_lesson
tier: local | department | enterprise
privacy: private | department-internal | public-safe
owner:
source_work_slug:
source_issue_url:
source_pr_url:
modules:
code_graph_nodes:
created_at:
expires_at:
supersedes:
---

# <short symptom>

- **Symptom**:
- **User impact**:
- **Root cause**:
- **Fault pattern**:
- **Fix pattern**:
- **Missing detection**:
- **Future guard**:
- **Reusable lesson**:
- **Similar projects/modules**:
- **Evidence**:
```

### Feature Or Architecture Lesson

```markdown
---
memory_type: feature_decision
tier: local | department | enterprise
privacy: private | department-internal | public-safe
owner:
source_work_slug:
source_issue_url:
source_pr_url:
release_id:
modules:
created_at:
expires_at:
supersedes:
---

# <decision or reusable pattern>

- **Problem solved**:
- **Accepted scope**:
- **Rejected scope**:
- **Architecture decision**:
- **Compatibility rule**:
- **Reusable pattern**:
- **Migration steps for similar projects**:
- **Evidence**:
```

## Workflow

1. Identify the source:
   - work item, bug slug, PR, incident, release range, or manual note.
2. Load source artifacts:
   - Work Context Package;
   - spec, plan, tasks, handoffs;
   - bug assessment/fix/test artifacts;
   - code graph and impact evidence;
   - evidence boards, PR reviews, CI output, incidents, or release notes.
3. Summarize the lesson:
   - remove raw customer demand and secrets;
   - separate fact, decision, inference, and opinion;
   - link evidence instead of copying large raw traces.
4. Choose memory tier:
   - contributor chooses `local` for personal unreviewed notes;
   - maintainer may promote to `department`;
   - maintainer, architecture owner, technical committee, or equivalent owner
     approves `enterprise`.
5. Write the candidate card inside the project, then run `memory_adapter.py`.
   The adapter validates metadata, writes the canonical tier path atomically,
   updates `index.json`, and ensures private paths are ignored by Git.
6. If `memory_service=mem0`, the adapter syncs the sanitized card to the
   configured namespace after the canonical file write succeeds.
7. Update indexes:
   - local index for local memory;
   - department memory index for uploaded internal memory;
   - `docs/ai-team/memory/` index for enterprise memory.
8. Recommend durable conversions:
   - skill;
   - knowledge map;
   - test;
   - gate;
   - hook;
   - code graph adapter or overlay.

## Promotion Rules

| From | To | Required review |
|---|---|---|
| local | department | contributor self-check plus maintainer acceptance |
| department | enterprise | maintainer and relevant owner approval |
| attempt lesson | decision memory | human owner decision and evidence |
| memory card | skill/gate/test | implementation PR and verification |

Do not promote memory automatically because it appears often. Repetition is a
signal for review, not authority.

## Output Shape

```text
Memory consolidation:
- source:
- scope:
- target tier:
- privacy:
- memory service:
- memory path:
- service namespace, if any:
- entries created:
- entries updated:
- entries rejected:
- sanitized fields:
- evidence links:
- recommended promotions:
- owner approval required:
- follow-up command:
```

## Stop Conditions

Stop and ask when:

- the source artifact is unavailable or ambiguous;
- raw customer demand, credentials, secrets, or private commercial context would
  be uploaded outside the approved tier;
- the contributor tries to publish another contributor's unreviewed local
  memory;
- a department memory entry is being treated as enterprise guidance;
- an enterprise memory entry lacks owner approval;
- memory conflicts with current source, spec, plan, issue, release notes, or
  owner decision;
- mem0 or another service would receive data without a configured namespace,
  access boundary, and privacy classification.
- the managed `.gitignore` block cannot be generated or is malformed.
