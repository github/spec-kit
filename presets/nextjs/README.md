# Next.js Web Application Preset

A Spec Kit preset for building **state-of-the-art, full-stack Next.js web applications** with Spec-Driven Development.

This preset ships **behaviors, not a tech stack**. It does not pick your ORM, styling layer, auth provider, or hosting target — but it does encode what every part of a production Next.js application must do, regardless of those choices.

## What's inside

| File | Role |
|---|---|
| `templates/constitution-template.md` | The project **directive**. Replaces the core constitution template. Encodes principles, phased criticality, and the full behavior matrix across Frontend, Backend, Security, Performance, TypeScript & Code Quality, and Infrastructure & Operations. |
| `templates/agent-context.md` | The **global agent rules**. A compressed, always-on operating manual for AI coding agents working on the project. Mirror it into the agent's context file (`AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, etc.). |

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
- **TypeScript & Code Quality behaviors** — Strict compiler, banned escape hatches, schema-validated input, typed result envelopes, import boundaries, no barrel files, no dumping grounds.
- **Infrastructure & Operations behaviors** — Reproducible builds, secret management, environment parity, immutable deploys, health-gated rollouts, backups with drills, observability, SLOs, blameless retrospectives.

## Install (local development)

```bash
specify preset add --dev ./presets/nextjs
```

Verify the constitution template resolves to this preset:

```bash
specify preset resolve constitution-template
```

Then run the constitution command in your project:

```bash
/speckit.constitution
```

This produces `.specify/memory/constitution.md` — the project's living directive.

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
