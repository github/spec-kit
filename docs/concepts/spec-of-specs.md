# Spec of Specs

When a feature is too large to run through a single
`/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`
cycle without the model losing track mid-implementation, you can break it into a
**roadmap** of smaller, independently-specified sub-features. This is the "spec of
specs" approach: one up-front pass decomposes a massive feature into self-contained
specs, and each of those runs through its own specify/plan/tasks/implement cycle.

> **When to reach for this.** Decomposition adds the most overhead of any strategy
> in [Handling Complex Features](complex-features.md). Use it **only when the lighter
> options there are insufficient** — first try limiting how many tasks run per
> `/speckit.implement` invocation, then sub-agent delegation, then a combination.
> Reach for a spec of specs only when even a single phase is too large to handle in
> one run.

The rest of this page describes *how* to do it with the tools you already have. No
new commands or extensions are required.

## The roadmap pass

Before writing any sub-spec, do a single decomposition pass to produce a roadmap.
Treat this as a lightweight planning conversation with your agent, not a full spec:

1. **State the whole feature.** Describe the large feature (the "epic") in a
   sentence or two so the agent has the full picture up front.
2. **Identify independent slices.** Ask the agent to propose a small set of
   sub-features that each deliver a coherent piece of the epic and can be specified
   on their own. Aim for slices that are independently testable — implementing just
   one should leave you with something demonstrable.
3. **Draw the boundaries.** For each slice, write one line of intent and an explicit
   scope boundary (what is in, what is deferred to a sibling slice). Sharp
   boundaries are what keep each sub-spec small enough to fit in context.
4. **Order by dependency.** Note which slices depend on others and sequence them so
   prerequisites come first. Slices with no dependency on each other can be built in
   any order. To build independent slices in parallel, use separate worktrees so each
   run has isolated active-feature state.
5. **Record the result as a roadmap.** Capture the slices in a durable roadmap file
   (below) so every later sub-spec can point back to it.

The roadmap is deliberately shallow: it names and orders the sub-features but does
**not** design them. The design happens when each slice runs through its own
`/speckit.specify`.

## The roadmap artifact

The roadmap is an ordinary Markdown file you author and keep under version control —
there is no special tooling behind it. Put it where the sub-specs can find it:

- For a feature-scoped epic: `specs/<epic-slug>/roadmap.md`.
- For a larger, cross-cutting epic: a top-level `ROADMAP.md`.

Each roadmap entry carries a stable id (used later for linking), a name, its intent,
its scope boundary, its dependencies, a status, and — once the sub-spec exists — a
link to it. A minimal template:

```markdown
# Roadmap: <epic name>

<One or two sentences: what the epic is and why it is being decomposed.>

**Status legend**: planned · in-progress · done

| ID | Sub-feature | Intent | Scope boundary | Depends on | Status | Sub-spec |
|----|-------------|--------|----------------|-----------|--------|----------|
| R1 | <name>      | <one line> | <in / deferred> | —      | planned | — |
| R2 | <name>      | <one line> | <in / deferred> | R1     | planned | — |
| R3 | <name>      | <one line> | <in / deferred> | R1     | planned | — |
```

Keep the `ID` column immutable once a sub-spec references it — it is the anchor for
traceability. Fill in the `Sub-spec` column with the path to each sub-feature's spec
directory as you create it, and update `Status` as work progresses.

## Specifying each sub-feature

With the roadmap in hand, work through the entries one at a time using the normal
Spec Kit flow — nothing new to learn:

1. Pick the next roadmap entry whose dependencies are already `done` (or have none).
2. Run `/speckit.specify` for just that slice, describing only its intent and scope
   from the roadmap entry. Because the slice is bounded, its spec, plan, and tasks
   stay well within the context window.
3. Run `/speckit.plan`, `/speckit.tasks`, and `/speckit.implement` for that slice as
   usual.
4. Mark the roadmap entry `done` and move to the next one.

Each slice is a complete, independent Spec Kit feature with its own
`spec.md`/`plan.md`/`tasks.md`. The roadmap is what ties them together.

## Linking sub-specs to the roadmap

To keep scope and intent from drifting across separate runs, every sub-spec
references its roadmap entry, and the roadmap links back — a simple, greppable,
bidirectional convention:

- **Sub-spec → roadmap.** In the sub-feature's `spec.md`, name the parent roadmap
  and entry id in the `Input` / summary line, for example:

  ```markdown
  **Input**: Parent roadmap: `specs/<epic>/roadmap.md` → entry **R3**. <feature description>
  ```

- **Roadmap → sub-spec.** In the roadmap table, set the entry's `Sub-spec` column to
  the sub-feature's directory, e.g. `specs/<epic>-part-3/`.

Because both directions are plain text, you can trace any sub-spec back to its place
in the epic (and find its siblings) with a quick search — no tooling, no metadata
schema.

## Keeping the roadmap and sub-specs in sync

The roadmap is a living document. As you learn more, keep it and the sub-specs
aligned:

- **Roadmap first, then reconcile.** When scope shifts, update the roadmap entry
  first, then update any sub-specs it affects. The roadmap is the source of truth for
  how the epic is divided.
- **Respect dependencies and ordering.** If a slice depends on another, build the
  prerequisite first and cross-reference the dependent sub-spec so the relationship
  is visible from both sides.
- **Recurse when a slice is still too big.** If a sub-feature turns out to be too
  large to specify in one cycle, give it its own roadmap and decompose it further —
  the same approach applies one level down. Recursion adds overhead, so only go as
  deep as the context problem actually requires.

## Worked example

Suppose the epic is **"Add a self-service billing portal"** — far too large for a
single cycle. The roadmap pass breaks it into three independently-specifiable
slices.

`specs/billing-portal/roadmap.md`:

```markdown
# Roadmap: Self-service billing portal

Let customers view invoices, manage payment methods, and change plans without
contacting support. Too large for one cycle, so it is split into independent slices.

**Status legend**: planned · in-progress · done

| ID | Sub-feature        | Intent                                   | Scope boundary                              | Depends on | Status  | Sub-spec |
|----|--------------------|------------------------------------------|---------------------------------------------|-----------|---------|----------|
| R1 | Invoice history    | Customers view and download past invoices | Read-only; no payment actions               | —         | done    | specs/billing-invoices/ |
| R2 | Payment methods    | Add, remove, and set a default card       | No plan changes; assumes invoices exist     | R1        | in-progress | specs/billing-payment-methods/ |
| R3 | Plan changes       | Upgrade/downgrade the subscription plan   | Uses R2's default payment method            | R1, R2    | planned | — |
```

Each slice is then specified on its own. For example, the **R2** sub-feature's
`spec.md` opens with a back-reference:

```markdown
# Feature Specification: Billing — payment methods

**Input**: Parent roadmap: `specs/billing-portal/roadmap.md` → entry **R2**.
Let customers add, remove, and set a default payment method in the billing portal.
```

From here a reader can trace **R2** back to the roadmap, see that it depends on
**R1** (invoice history, already `done`), and see that **R3** (plan changes) is
waiting on it. Building R1, then R2, then R3 keeps every run small while the roadmap
preserves the shape of the whole epic.

## For automation (optional)

If you would rather automate roadmap capture and consistency checks than maintain
the file by hand, the community-maintained
[Spec Roadmap extension](https://github.com/srobroek/speckit-roadmap) explores that
direction. It is a third-party extension and is not required — the manual convention
above is enough on its own.
