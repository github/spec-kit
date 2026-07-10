# Evidence Verification Pattern

Spec Kit ships two in-session verification commands: `/speckit.analyze`
checks `spec.md`, `plan.md`, and `tasks.md` for consistency *before*
implementation, and `/speckit.converge` assesses the codebase against those
artifacts *after* implementation and appends any remaining work as tasks.

Both commands are read-only or append-only within the current agent session.
They do not emit a durable, machine-readable record of what was verified, what
risks remain, or what changed. This page names a complementary pattern — the
**evidence verification pattern** — for producing a structured evidence pack
that traces an implementation back to its spec and tasks. The pattern is
tool-agnostic; a concrete example is included at the end.

This is a pattern, not a CLI feature. Spec Kit does not require it, and none
of the fields below are mandated by the toolkit.

## In-session verification vs. durable evidence

`/speckit.analyze` and `/speckit.converge` answer "does the artifact set
agree?" and "does the code satisfy the artifacts?" Their findings live in the
agent transcript and (for converge) in appended `tasks.md` entries. They are
well suited to closing the loop inside one session.

They are less well suited to:

- **Cross-session review**, where a reviewer or CI step needs a standalone
  artifact summarizing what was verified.
- **Audit**, where a team must retain a record of risks, verification status,
  and change scope for a feature long after the session ended.
- **Supply-chain intake**, where a downstream consumer receives an
  implementation and wants to inspect verification evidence without re-running
  the agent.

The evidence verification pattern fills these gaps by emitting a bounded,
portable pack of files alongside the implementation.

## The pattern

An evidence pack is a small set of structured files produced when an
implementation is accepted. Each file carries one concern, is machine-readable,
and is small enough to attach to a pull request or store in artifact
retention. The pack is a derivative of the implementation, not a new source of
truth — the spec, plan, and tasks remain authoritative.

A pack should have four properties:

- **Bounded.** It holds summaries and counts, not full diffs, logs, or command
  output. Size is predictable regardless of how large the implementation grew.
- **Traceable.** Every finding and verification record carries a source
  reference back to a task ID, requirement, or artifact section.
- **Secret-free.** The pack is safe to share. Secrets, tokens, credentials,
  and full diffs are excluded by construction; only categories and counts of
  redactions are recorded.
- **Provenance-tagged.** One file records the tool, version, commit, and
  environment that produced the pack, so a reviewer can tell whether the
  evidence is current.

## What an evidence pack contains

The table below maps each concern to the kind of field a pack should carry.
The names are illustrative; a given implementation may use different file or
field names as long as the concerns are covered.

| Concern | Example file | Contents | Why it matters |
|---|---|---|---|
| Verification status | `verify.json` | Per-task pass/fail, audit verdict, command counts | Answers "did the implementation pass its checks?" without re-running them |
| Risk findings | `risk.json` | Aggregated findings with severity (high/medium/low) and category | Surfaces what `/speckit.converge` would classify as `missing`, `partial`, `contradicts`, or `unrequested`, plus non-convergence risks |
| Change scope | `diffstat.json` | File paths with additions/deletions counts | Shows what the implementation touched, without exposing full diff content |
| Lineage summary | `lineage.json` | Goal, final status, stop reason, iteration and task counts | Lets a reviewer understand the shape of the work at a glance |
| Provenance | `attestation.json` | Tool, version, commit, OS, schema epoch | Lets a reviewer judge whether the evidence is current and reproducible |
| Redactions | `redactions.json` | Categories and counts of redacted values | Proves the pack was filtered, without retaining the filtered values |

A human-readable summary (for example, an `EVIDENCE.md`) is a useful
companion to the machine-readable files, but the JSON files are the contract.

## The security oversight layer

The pattern is most valuable when the pack is produced by a layer that sits
*outside* the coding agent during implementation — a supervisor that observes
commands, applies policy, and records bounded evidence. Keeping the supervisor
separate from the agent that writes the code gives the evidence a different
trust root than the implementation itself.

A supervisor useful for this pattern typically:

- Confines every command to the project workspace and rejects paths outside it.
- Matches commands against an allow-list rather than executing arbitrary shell.
- Blocks sensitive file names (credentials, `.env`, SSH keys, tokens).
- Records only bounded summaries — never full stdout/stderr, full diffs, or
  secret values.
- Tags each pack with its own version and commit so the evidence can be
  audited independently.

Spec Kit's extension hook system (`before_implement`, `after_converge`, etc.,
in `.specify/extensions.yml`) is one way to wire such a supervisor into the
existing workflow without changing the core commands. An extension can run the
supervisor at a hook and write the pack into the feature directory or a
dedicated evidence path.

## Example: PatchWarden Evidence Pack v2

[PatchWarden](https://github.com/jiezeng2004-design/PatchWarden) is one implementation
of this pattern. Its `export_task_evidence_pack` operation writes eight files
to a per-lineage directory. The mapping to the concerns above:

| PatchWarden file | Concern |
|---|---|
| `evidence.json` | Complete bounded pack (machine-readable, includes lineage and policy summary) |
| `EVIDENCE.md` | Human-readable summary |
| `risk.json` | Risk findings, aggregated from fail/warn checks and lineage warnings, with `by_severity` counts |
| `verify.json` | Per-iteration and per-session verification records (status and counts only) |
| `diffstat.json` | File-level additions/deletions, no diff body; paths redacted |
| `lineage.json` | Goal, final status, stop reason, task counts, worktree isolation mode |
| `attestation.json` | Version, commit, Node/OS, tool profile, schema epoch |
| `redactions.json` | Categories (private key, bearer token, npm token, credential assignment, known token format) and counts — never original values |

A `risk.json` entry, for example, is a bounded record rather than a log dump:

```json
{
  "risks": [
    {
      "source": "round",
      "task_id": "task-main",
      "severity": "high",
      "category": "fail_check",
      "detail": "verification failed: npm test exited with code 1"
    }
  ],
  "count": 1,
  "by_severity": { "high": 1, "medium": 0, "low": 0 }
}
```

The `severity` mapping mirrors how `/speckit.converge` grades findings: a
failed check is high, a warning check is medium, and a lineage-level warning
is low. A reviewer can read `risk.json` alongside a converge report and expect
the two to agree on severity ordering, even though they come from different
tools.

PatchWarden is shown here as a reference, not a recommendation. Any tool that
emits bounded, traceable, secret-free, provenance-tagged files covering the
concerns above satisfies the pattern.

## Mapping to Spec Kit artifacts

| Spec Kit artifact | Evidence field that should trace back to it |
|---|---|
| `spec.md` (FR-###, SC-###) | Risk findings and verification records reference the requirement keys |
| `plan.md` (architecture, phases) | Change scope (`diffstat`) is bounded to files the plan names |
| `tasks.md` (task IDs) | `verify.json` and `risk.json` carry `task_id` per record |
| `/speckit.analyze` findings | Risks that duplicate analyze findings should be flagged so a reviewer does not act on them twice |
| `/speckit.converge` appended tasks | Verification records should reflect whether convergence tasks were resolved |

## Relationship to analyze and converge

The evidence pack does not replace the in-session commands:

- Run `/speckit.analyze` before implementation to catch gaps across the
  artifact set. The pack is not a substitute for fixing those gaps first.
- Run `/speckit.implement`, then `/speckit.converge`, until converge reports
  no remaining work.
- Produce the evidence pack when the implementation is accepted. The pack
  captures the *final* verification state, the residual risks, and the change
  scope — a snapshot converge does not retain.

If converge appended tasks and a later implement pass resolved them, the pack's
`verify.json` should reflect the resolved status, and `lineage.json` should
record the iteration count so a reviewer can see the convergence loop ran.

## When to use this pattern

| Situation | Use the pattern? | Reason |
|---|---|---|
| Solo prototype that will be thrown away | No | Overhead exceeds value; converge is enough |
| Team project with code review | Yes | Reviewers get a standalone, bounded summary |
| Regulated or audited environment | Yes | Retained evidence is the point |
| Implementation consumed by another team or product | Yes | Downstream consumers need intake evidence they can inspect without the agent |
| Spec-as-source regeneration (see [Spec Persistence Models](spec-persistence.md)) | Optional | The pack verifies one regeneration; keep it only if the regeneration is itself audited |

If your team adopts the pattern, record the convention in your project
constitution or onboarding notes, including where packs are stored and how long
they are retained. Like the persistence models, this is a team convention
rather than a CLI setting.
