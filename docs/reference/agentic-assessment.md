# Agentic Idea Assessment

The bundled, opt-in **assess** extension evaluates an idea through
**intake → research → define → shape → decide**. It is a standalone process:
it can run in an initialized project with no source code, produces only
assessment artifacts, and does not automatically start SDD. For a guided example,
see the [Idea Assessment Quickstart](../guides/assessment.md).

Install it from an initialized project's root:

```bash
specify extension add assess
```

Commands below use GitHub Copilot's default skills notation, `/speckit-assess-*`.
Other integrations may use a different prefix.
See [Command invocation](integrations.md#command-invocation).

## Commands and artifacts

Every artifact is written under `.specify/assessments/<slug>/`.

| Command | Purpose | Output |
| --- | --- | --- |
| `/speckit-assess-intake` | Capture an idea from text, a URL, a ticket, or a codebase pointer | `intake.md` |
| `/speckit-assess-research` | Gather evidence for and against the idea, with sources and confidence | `research.md` |
| `/speckit-assess-define` | Define users, the problem, goals, non-goals, metrics, and cost of inaction | `problem.md` |
| `/speckit-assess-shape` | Compare concept-level options, appetite, and trade-offs | `concept.md` |
| `/speckit-assess-decide` | Record a scorecard, verdict, rationale, and optional SDD handoff | `decision.md` |

Pass the initial idea and a slug to intake, then reuse the slug:

```text
/speckit-assess-intake "Let users work offline and sync when they reconnect." slug=offline-mode
/speckit-assess-research slug=offline-mode
/speckit-assess-define slug=offline-mode
/speckit-assess-shape slug=offline-mode
/speckit-assess-decide slug=offline-mode
```

## Prerequisites and scope

The five-stage sequence is the normal path, but not every stage is mandatory:

- `define` can work directly from user input; intake and research are optional
  for producing a problem definition.
- `shape` requires `problem.md` and stays at concept level. Architecture,
  data models, APIs, tasks, and implementation belong to delivery, not assessment.
- `decide` requires `problem.md` and reads every available assessment artifact.
  A `go` verdict additionally requires a shaped concept and adequate evidence;
  skipping research does not waive the evidence requirement.

## Slugs and existing artifacts

The slug identifies one idea's directory. User-provided slugs are normalized to
lowercase kebab-case and retained without appended timestamps or numbers.
If no slug is supplied, intake asks for one interactively; automated runs
generate a unique slug. Later stages can reuse the slug from context when its
directory exists.

Existing artifacts are not overwritten without confirmation. In automated mode,
commands refuse to overwrite them. For routine clarification, refine the existing
artifact rather than rerunning the command.

## Decisions and evidence

The decision scorecard rates criteria as `strong`, `adequate`, `weak`, or
`unknown`, with justifications drawn from the artifacts.

| Verdict | Requirement or meaning |
| --- | --- |
| `go` | Problem validity and evidence strength are at least `adequate`, and a concept option is recommended |
| `needs-clarification` | Named unknowns block the decision; weak or unknown evidence, or a missing concept, cannot justify `go` |
| `kill` | The idea is not worth pursuing now; the decisive reason is recorded explicitly |

Research must include evidence against the idea. Unsourced claims remain marked
as `ASSUMPTION`; do not invent citations or present uncertain evidence as fact.
A documented decision to stop is a useful result.

## Refining an assessment

Run each stage once in the usual flow. To resolve clarification markers or a
`needs-clarification` verdict, edit the affected Markdown directly or ask the
agent in free-form chat to incorporate the missing facts. Preserve sources and
confidence tags, then review dependent artifacts and revise `decision.md` as
needed. This is artifact refinement, not repeated command execution.

Rerunning an earlier command is reserved for exceptions such as a wrong slug or
discarded draft. See the
[guided clarification example](../guides/assessment.md#resolve-unknowns-by-refining-the-artifacts).

## Handoff and guardrails

A `go` decision includes a handoff summary you can choose to pass to
`/speckit-specify`. No lifecycle hooks install assessment as a prerequisite of
SDD, and non-software ideas need not enter SDD at all.

Assessment commands write only within `.specify/assessments/<slug>/`; they do not
edit source code. The extension checks slugs and paths, treats fetched content
as untrusted data, and applies its URL trust policy. Consult the
[extension documentation](https://github.com/github/spec-kit/blob/main/extensions/assess/README.md)
for the complete guardrails and relationships to other extensions.
