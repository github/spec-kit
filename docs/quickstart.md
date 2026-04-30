# Quick Start Guide

This guide walks you through creating a production-ready Crossplane composition using InfraKit's full workflow.

---

## Prerequisites

- InfraKit CLI installed and project initialized (`infrakit init`)
- `/infrakit:setup` has been run to configure project context

---

## The Workflow

```
setup → new_composition → plan → checklist (opt) → implement → review
```

`/infrakit:plan` automatically generates `tasks.md` after you accept the plan. The implement command works through those tasks in order.

Each step builds on the last, and every artifact lives in `.infrakit_tracks/tracks/<track-name>/`.

---

## Step 1: Configure Project Standards

Run `/infrakit:setup` once per project to define your infrastructure standards:

```
/infrakit:setup
```

You will be guided through:
- Cloud provider and base API group
- Naming conventions (XRD kinds, claim kinds, composition names)
- Environment policy (dev / staging / prod)
- Security defaults (encryption at rest, private networking, TLS)
- Required tags

This creates three files that every other command reads:
- `.infrakit/context.md` — project standards
- `.infrakit/coding-style.md` — coding standards
- `.infrakit/tagging.md` — tagging requirements

---

## Step 2: Create a Resource Specification

Use `/infrakit:new_composition` to start the multi-persona solutioning workflow:

```
/infrakit:new_composition
```

You will be asked for:
1. Resource name (e.g., `postgres-database`)
2. Target directory (e.g., `./resources/postgres`)
3. Resource description, cloud provider, environment, security requirements, parameters, and outputs

The **Cloud Solutions Engineer** gathers your requirements and writes `spec.md`.

Next, the **Cloud Architect** reviews the spec for architecture correctness, reliability, and cost. Then the **Cloud Security Engineer** audits against your chosen compliance frameworks (SOC2, HIPAA, ISO 27001, etc.).

You review the combined findings and decide which recommendations to apply before confirming the final spec.

The track is registered in `.infrakit_tracks/tracks.md` with status `spec-generated`.

---

## Step 3: Generate the Implementation Plan and Task List

```
/infrakit:plan <track-name>
```

Example: `/infrakit:plan postgres-database-20260401-120000`

The **Crossplane Engineer** generates a detailed plan covering:
- XRD schema design (parameters → OpenAPI v3 fields, status fields)
- Managed resources with verified `apiVersion` values (looked up from doc.crds.dev)
- Patch mappings: input parameters → `spec.forProvider`, status outputs → `status.atProvider`
- Required tag patches (per your `tagging.md`)

After you accept the plan, `tasks.md` is automatically generated with ordered, executable tasks across 5 phases:
1. XRD definition (`definition.yaml`)
2. Composition with all patches and tags (`composition.yaml`)
3. Example claim (`claim.yaml`)
4. Documentation (`README.md`)
5. Validation (`crossplane render`)

Run `/infrakit:analyze <track-name>` after planning to verify spec/plan consistency.

---

## Step 4: (Optional) Generate a Verification Checklist

```
/infrakit:checklist <track-name>
```

The **Crossplane Engineer** generates a comprehensive checklist to verify the implementation against the spec and plan. This is useful for manual verification or as a guide during implementation.

---

## Step 5: Implement

```
/infrakit:implement <track-name>
```

The Crossplane Engineer works through each task in `tasks.md` in order, marking `- [ ]` → `- [x]` as it goes. All generated YAML follows your `coding-style.md` and `tagging.md` exactly.

After all tasks complete, it:
1. Updates `.infrakit_context.md` with the final resource interface
2. Appends an entry to `.infrakit_changelog.md`
3. Regenerates `infrakit_composition_contract.md` from the implemented YAML

---

## Step 6: Review

```
/infrakit:review <resource-directory>
```

Example: `/infrakit:review ./resources/postgres`

The Crossplane Engineer reviews the generated files against:
- Pipeline mode requirement
- Required tags on every managed resource
- `providerConfigRef` on every managed resource
- No hardcoded secrets
- XRD naming conventions
- All parameters patched
- All status fields patched

The review report shows findings by severity (CRITICAL / HIGH / MEDIUM / LOW) and offers to apply fixes.

---

## Complete Example: PostgreSQL Database

```
# Step 1 (done once per project)
/infrakit:setup

# Step 2: Create spec
/infrakit:new_composition
> Resource name: postgres-database
> Directory: ./resources/postgres
> Description: A managed PostgreSQL database with encryption at rest and connection secret

# Step 3: Plan (tasks.md auto-generated after you accept)
/infrakit:plan postgres-database-20260401-120000

# Step 4: (Optional) Checklist
/infrakit:checklist postgres-database-20260401-120000

# Step 5: Implement
/infrakit:implement postgres-database-20260401-120000

# Step 6: Review
/infrakit:review ./resources/postgres
```

---

## Track Status

Check the status of all tracks at any time:

```
/infrakit:status
```

| Status | Meaning |
|--------|---------|
| 🔵 `initializing` | Track created, spec in progress |
| 📝 `spec-generated` | Spec confirmed, ready for plan |
| 📋 `planned` | Plan and task list generated, ready for implementation |
| ⚙️ `in-progress` | Implementation underway |
| ✅ `done` | Implementation complete and reviewed |
| ❌ `blocked` | Blocked, needs attention |

---

## Key Principles

- **Never skip the spec** — the spec is the source of truth; the plan and tasks derive from it
- **One question at a time** — every command prompts interactively and waits for your response
- **Reviewer personas are read-only** — architect-review and security-review never modify files without your explicit approval
- **Standards are non-negotiable** — the Crossplane Engineer will flag any conflict with coding-style.md before writing code
