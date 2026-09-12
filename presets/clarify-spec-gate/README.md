# Clarify spec-stage gate

Opt-in wrap of `/speckit.clarify`. Core already lists the spec taxonomy. This preset adds a stage gate so agents do not dump NFRs, acceptance criteria, edge cases, and similar items into Plan.

Install it if you want that enforcement. Leave it off if core `/speckit.clarify` is enough.

## What it does

It wraps `speckit.clarify` with `{CORE_TEMPLATE}`, so core command updates still land. On top of that it:

- Treats a taxonomy hit as a spec-stage question
- Defers only implementation method, tech-stack comparison, or task breakdown
- Pauses when more than 60% of unresolved items would be deferred
- Adds a MUST-NOT on spec-taxonomy deferral

## Installation

```bash
specify preset add clarify-spec-gate
```

## Development

```bash
specify preset add --dev ./presets/clarify-spec-gate
specify preset resolve speckit.clarify
specify preset remove clarify-spec-gate
```
