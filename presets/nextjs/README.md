# Next.js Web Application Preset

A Spec Kit preset for building **state-of-the-art, full-stack Next.js web applications** with Spec-Driven Development.

This preset ships **behaviors, not a tech stack**. It does not pick your ORM, styling layer, auth provider, or hosting target — but it does encode what every part of a production Next.js application must do, regardless of those choices.

## What's inside

| File | Role |
|---|---|
| `templates/constitution-template.md` | The project **directive**. Replaces the core constitution template. Encodes principles, phased criticality, and the full behavior matrix across Frontend, Backend, Security, Performance, TypeScript & Code Quality, and Infrastructure & Operations. |
| `templates/agent-context.md` | The **global agent rules**. A compressed, always-on operating manual for AI coding agents working on the project. Mirror it into the agent's context file (`AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, etc.). |
| `commands/speckit.constitution.scan.md` | New command **`/speckit.constitution.scan`**. Sibling to `/speckit.constitution`: instead of taking a prompt, it scans the repository (Markdown docs, `package.json`, `tsconfig.json`, Next.js structure, tooling, CI) and exports `.specify/memory/constitution.md` with a Sync Impact Report mapping evidence to every Critical directive. |
| `scripts/bash/scan-repo.sh` · `scripts/powershell/scan-repo.ps1` | Repository scanners invoked by the command. Emit JSON conforming to `scripts/SCHEMA.md` — `.md` inventory (with headings + excerpts), parsed `package.json` (deps, scripts, signals), `tsconfig.json` strict-flag posture, App Router / Pages Router / middleware presence, `"use client"` / `"use server"` counts, DAL directory detection, CI workflows, env files, pinned Node version, git metadata. |
| `scripts/SCHEMA.md` | Stable contract between the scanners and the command (`schema_version: "1.0"`). |

## Operating framework

Every directive is tagged with a **Phase** and a **Criticality**:

- **Phase** — when it must hold: `P1 Foundation` → `P2 MVP` → `P3 Hardening` → `P4 Scale` (continuous).
- **Criticality** — how strictly: `Critical` (blocks release) · `High` (needs an approved, time-bound exception) · `Medium` (default) · `Low` (recommended).

The framework lets a team start enforcing the right things at the right time — without pretending a green-field MVP needs the same controls as a production app with paying customers, and without letting a production app drift on principles that should have been settled before the first commit.

## Coverage

- **Core principles** — Server-first architecture · Type-safety without escape hatches · Defense-in-depth security · Validated boundaries · Performance measured, not guessed · Accessibility non-negotiable · Observability and auditability · Quality code by default.
- **Frontend behaviors** — Server Components, streaming, Suspense layering, route conventions, accessibility, image and font discipline, client-state minimization.
- **Backend behaviors** — Data Access Layer, thin actions, schema-validated boundaries, authorization at the action, ownership checks, DTOs, transactions, webhooks, idempotency.
- **Security behaviors** — Layered enforcement, session hygiene, secrets handling, CSP and security headers, MFA, audit trail, dependency posture.
- **Performance behaviors** — Explicit caching, parallel fetches, field-data-driven optimization, CWV budgets in CI, image/font/script discipline, bundle audits, INP protection.
- **TypeScript Engineering behaviors** (carries a third tag — **Scope**: `FE` / `BE` / `Both`) — organized into eight subsections: Compiler & Project Config, Type System Discipline, SOLID, Clean Code & Functional Discipline, Runtime Boundaries, Frontend Patterns, Backend Patterns, Project Hygiene & DX. Covers strict compiler flags, banned escape hatches, `satisfies` vs `as`, branded/nominal IDs, discriminated unions, parse-don't-validate boundaries, schema-derived types, dependency injection, exhaustive switches with `never`, and naming/linting/test discipline.
- **Infrastructure & Operations behaviors** — Reproducible builds, secret management, environment parity, immutable deploys, health-gated rollouts, backups with drills, observability, SLOs, blameless retrospectives.

## Install (local development)

```bash
specify preset add --dev ./presets/nextjs
```

Verify the constitution template resolves to this preset:

```bash
specify preset resolve constitution-template
```

Then run **one** of the constitution commands in your project:

```bash
# Interactive: drafts the constitution from a prompt + repo context
/speckit.constitution

# Scan-driven: scans the repo (Markdown + package.json + tsconfig + Next.js
# structure + tooling + CI) and exports a properly-structured constitution
# with a Sync Impact Report mapping evidence to every Critical directive.
/speckit.constitution.scan
```

Both produce `.specify/memory/constitution.md` — the project's living directive.

### What `/speckit.constitution.scan` does

1. Runs `scripts/bash/scan-repo.sh` (or `scan-repo.ps1`) to build a JSON inventory of the repository.
2. Reads the most relevant Markdown evidence (`README.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `SECURITY.md`, agent context files, plus up to 10 likely product/engineering docs).
3. Decides the operating **phase** (P1–P4) from evidence — defaults to P1 if no production signal is present.
4. Fills the Next.js constitution template (does **not** rewrite the behavior matrix — the matrix is the source of truth).
5. Prepends a **Sync Impact Report** as an HTML comment: inventory snapshot, per-directive status (`MET` / `NOT MET` / `PARTIAL` / `UNVERIFIED`), Markdown evidence consulted, and follow-up TODOs.
6. Flags downstream templates (`plan-template`, `spec-template`, `tasks-template`, command files, agent context files) that may need realignment — **without** silently editing them.
7. Writes `.specify/memory/constitution.md` and prints a summary plus a suggested commit message.

You can pass freeform context with the command, e.g.:

```bash
/speckit.constitution.scan ratification date 2026-05-18; treat auth as Critical from P1
```

## Wiring the agent context

After installation, mirror `templates/agent-context.md` into your agent's context file so the rules apply on every turn:

- **Claude Code** → `CLAUDE.md`
- **GitHub Copilot** → `.github/copilot-instructions.md`
- **Gemini CLI** → `GEMINI.md`
- **Codex / generic** → `AGENTS.md`

Either copy the contents directly or reference the file from your agent context:

```markdown
<!-- in AGENTS.md / CLAUDE.md / .github/copilot-instructions.md -->
The operating rules for this project live in
`.specify/presets/nextjs/templates/agent-context.md`. Read them before
proposing changes; the constitution at `.specify/memory/constitution.md`
is authoritative on conflict.
```

## Governance

The constitution **supersedes ad-hoc conventions**. When a directive here conflicts with a tutorial, a blog post, a framework changelog, or an LLM suggestion, the constitution wins until it is formally amended via PR with a changelog entry — and, where criticality or phase changes, a migration plan for affected code.

Waivers for Critical or High directives must be recorded inline with an owner, a reason, and an expiry no further than one release cadence away.
