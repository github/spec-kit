# [PROJECT_NAME] Constitution
<!-- A full-stack Next.js web application governed by Spec-Driven Development. -->

This constitution governs **behavior**, not technology choices. The team chooses concrete tools in the plan phase; the directives below hold regardless of which framework version, ORM, styling layer, or hosting target is selected.

Every directive carries two tags:

- **Phase** — when the behavior must hold.
- **Criticality** — how strictly it is enforced.

---

## Operating Framework

### Phases

| Phase | Meaning |
|---|---|
| **P1 — Foundation** | Must hold before the first feature is written. Skipping P1 is a refactor with compounding interest. |
| **P2 — MVP** | Must hold before the first real user touches the app. |
| **P3 — Hardening** | Must hold before the first paying customer or production-scale exposure. |
| **P4 — Scale** | Continuous practice for a live, evolving product. |

### Criticality

| Level | Meaning |
|---|---|
| **Critical** | Violations block release. No exceptions without a recorded waiver and a fixed expiry. |
| **High** | Violations require an explicit, time-bound exception approved at review. |
| **Medium** | Default expectation; deviations are noted and tracked. |
| **Low** | Recommended; revisit during regular audits. |

---

## Core Principles

### I. Server-First Architecture (Critical)
The application renders on the server by default. Client interactivity is opted into at the smallest meaningful leaf, with `"use client"` boundaries pushed as deep as possible. The server is the source of truth; the client is a thin interaction surface.

### II. Type-Safety Without Escape Hatches (Critical)
Strict static typing is enforced project-wide. `any`, unchecked `as` casts, and `@ts-ignore` are violations, not stylistic choices. External input (HTTP, environment, storage, third-party SDKs) is parsed through a schema before any business logic sees it. The compiler is the first test suite.

### III. Defense-in-Depth Security (Critical)
Security is enforced in layers: edge → route → Data Access Layer (DAL). **The DAL is the source of truth for authorization.** Middleware is a convenience, never a security boundary. Every mutation re-verifies identity, authorization, and resource ownership at the action — not just at the page or layout.

### IV. Validated Boundaries (Critical)
Every Server Action is a public POST endpoint. Every Route Handler is an untrusted ingress. Every URL parameter is hostile until validated, coerced, and authorized. Inputs are parsed at the boundary; downstream code receives narrowed types only.

### V. Performance is Measured, Not Guessed (High)
Core Web Vitals budgets (LCP, INP, CLS) are set explicitly and enforced in CI on every PR. Optimization decisions are driven by **field data at P75**, not local Lighthouse runs. Caching is **opt-in and explicit** per fetch and per component — there are no implicit assumptions.

### VI. Accessibility is Non-Negotiable (High)
Semantic HTML, keyboard navigation, visible focus, and assistive-technology paths are part of the definition of done — not a P3 retrofit. A component that ships interactivity without an accessible affordance fails review.

### VII. Observability and Auditability (High)
Every request carries a correlation ID across layers. Auth events, permission changes, and admin actions are written to an append-only audit trail. Logs are structured (request ID, user ID, action, outcome). Errors carry context internally but never leak internals to clients.

### VIII. Quality Code is the Default (High)
Lint, format, typecheck, and tests run in CI on every change; warnings on protected branches are errors. Modules are pure where possible; side effects are explicit and isolated; abstractions earn their cost. Public APIs are named precisely and documented with TSDoc.

---

## Frontend Behaviors

| Phase | Crit. | Behavior |
|---|---|---|
| P1 | Critical | Default every component to Server; opt into client only at the smallest interactive leaf. |
| P1 | Critical | Push `"use client"` boundaries as deep as possible. |
| P1 | High | Co-locate data fetching inside the Server Component that renders it. |
| P2 | Critical | Parallelize fetches with `Promise.all`; kill sequential await waterfalls. |
| P2 | High | Wrap slow segments in `<Suspense>` with meaningful skeletons; never one boundary per page. |
| P2 | High | Use `loading.tsx`, `error.tsx`, `not-found.tsx`, `forbidden.tsx` at every meaningful segment. |
| P2 | High | Use streaming so the static shell paints while dynamic holes resolve. |
| P2 | High | Type all component props strictly; ban `any` and unchecked `as` casts. |
| P2 | High | Use `<Link>` for in-app navigation to benefit from prefetching. |
| P2 | High | Accessibility non-negotiable: semantic HTML, focus management, keyboard paths. |
| P2 | Medium | Define `generateMetadata` per route for SEO and social cards. |
| P2 | Medium | Use route groups, parallel routes, and intercepting routes for layout without URL pollution. |
| P2 | Medium | Use `generateStaticParams` for prerenderable dynamic routes. |
| P3 | High | Treat layouts as untrusted for auth — they don't run on every request. |
| P3 | High | Reserve fixed dimensions for dynamic above-the-fold content to keep CLS near zero. |
| P3 | High | One `priority` image per route (LCP candidate); accurate `sizes` everywhere. |
| P3 | High | Self-host fonts, enable fallback metric adjustment, use `display: swap`. |
| P3 | High | Lazy-load heavy client widgets (editors, charts, maps) via dynamic import. |
| P3 | Medium | Import only icons and utilities actually used; avoid barrel imports that defeat tree-shaking. |
| P3 | Medium | Use optimistic UI hooks for mutations. |
| P3 | Medium | Keep client state minimal; lift server-derived data to the server. |
| P4 | Medium | Prefer CSS and platform primitives over JS for animation, layout, and toggles. |
| P4 | Medium | Make components composable and prop-driven; avoid context-as-props. |
| P4 | High | Test on real devices, mobile networks, and field RUM — not just local Lighthouse. |

---

## Backend Behaviors

| Phase | Crit. | Behavior |
|---|---|---|
| P1 | Critical | Centralize all data access behind a single Data Access Layer. |
| P1 | Critical | Mark sensitive modules `server-only` so client imports fail the build. |
| P1 | Critical | Keep business logic in pure, testable service functions; actions stay thin. |
| P2 | Critical | Treat every Server Action as a public POST endpoint. |
| P2 | Critical | Validate every input at the server boundary with a schema. |
| P2 | Critical | Re-verify auth and authorization inside every action and Route Handler. |
| P2 | Critical | Check resource ownership, not just identity, on every mutation and read. |
| P2 | Critical | Treat URL params as untrusted; validate, coerce, and authorize before querying. |
| P2 | Critical | Use DB transactions for multi-step mutations that must be atomic. |
| P2 | High | Return DTOs with only the fields the client needs; never leak full rows. |
| P2 | High | Never capture sensitive data in Server Action closures; pass IDs from the URL. |
| P2 | High | Route Handlers for webhooks and non-browser clients; Server Actions for in-app mutations. |
| P2 | High | Verify webhook signatures and idempotency keys; reject replays. |
| P2 | High | Return proper HTTP status codes; don't collapse everything to `500`. |
| P2 | High | Wrap fallible operations in typed result envelopes. |
| P3 | Critical | Enforce tenant isolation at the data layer, not the UI layer. |
| P3 | High | Revalidate caches surgically by tag or path after mutations. |
| P3 | High | Make mutations idempotent where feasible to survive retries. |
| P3 | High | Log structured events (request ID, user ID, action, outcome); correlate across layers. |
| P4 | Medium | Offload non-critical side effects to background work or after-response hooks. |

---

## Security Behaviors

| Phase | Crit. | Behavior |
|---|---|---|
| P1 | Critical | Defense-in-depth: edge → route → DAL, with the DAL as the source of truth. |
| P1 | Critical | Never rely on middleware as a security boundary. |
| P2 | Critical | Store sessions in `httpOnly`, `Secure`, `SameSite` cookies — never in `localStorage`. |
| P2 | Critical | Hash passwords with a memory-hard algorithm; never store, log, or echo them. |
| P2 | Critical | Use parameterized queries everywhere; ban string-concatenated SQL. |
| P2 | Critical | Sanitize and encode user-generated content before rendering. |
| P2 | Critical | Keep secrets server-side; never use the public env var prefix for sensitive values. |
| P2 | Critical | Rotate and sign session secrets; invalidate sessions on logout, password change, or privilege change. |
| P2 | Critical | Treat file uploads as hostile: validate MIME, size, and extension; store outside the web root; scan. |
| P2 | High | Rate-limit every mutation and auth-adjacent endpoint per IP and per user. |
| P2 | High | Bot mitigation or CAPTCHA on signup, password reset, contact, and abuse-prone actions. |
| P2 | High | Whitelist Server Action allowed origins in multi-domain or reverse-proxied setups. |
| P2 | High | Strip stack traces and internal error details from production responses. |
| P3 | Critical | Apply a strict CSP with nonces; lock `frame-ancestors`, `connect-src`, `img-src`. |
| P3 | Critical | Ship security headers: HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`. |
| P3 | Critical | Enforce MFA at the application level for high-risk actions — not just at the IdP. |
| P3 | Critical | Apply least privilege on DB roles, API keys, and service accounts. |
| P3 | High | Audit every `"use server"` file in review: validation, auth, authorization, ownership, return shape. |
| P3 | High | Audit every `"use client"` prop shape: no private fields leaking through serialization. |
| P3 | High | Log auth events, permission changes, and admin actions to an append-only audit trail. |
| P3 | High | Pin and audit dependencies; vulnerability-scan every PR. |
| P4 | Critical | Keep framework, runtime, and auth libraries patched — CVEs get exploited fast. |
| P4 | High | Regular pen tests and vulnerability scans aligned with release cadence. |

---

## Performance Behaviors

| Phase | Crit. | Behavior |
|---|---|---|
| P1 | High | Make caching explicit and opt-in per fetch and per component; no implicit assumptions. |
| P2 | High | Stream HTML; don't block on the slowest fetch. |
| P2 | High | Fan out Server Component fetches in parallel. |
| P3 | Critical | Measure field data (real users, P75) before optimizing. |
| P3 | Critical | Set Core Web Vitals budgets (LCP, INP, CLS); enforce in CI on every PR. |
| P3 | Critical | Identify the actual LCP element with a perf trace before touching images. |
| P3 | High | Serve static assets from a CDN with immutable filenames and long `Cache-Control`. |
| P3 | High | Use modern image formats (AVIF, WebP), correct `sizes`, and tuned breakpoints. |
| P3 | High | Subset and self-host fonts; preload only weights used above the fold. |
| P3 | High | Cache aggressively at route, component, and fetch level; invalidate by tag on mutation. |
| P3 | High | Compress responses (Brotli or Zstd); serve over HTTP/2 or HTTP/3. |
| P3 | High | Right-size DB connection pooling; pick edge-compatible drivers when relevant. |
| P3 | Medium | Use partial prerendering where supported: static shell plus streamed dynamic holes. |
| P3 | Medium | Use ISR or on-demand revalidation for occasional-change content. |
| P3 | Medium | Load third-party scripts with the lowest-priority strategy that still works. |
| P3 | Medium | Preconnect or preload genuinely critical origins; don't preload everything. |
| P4 | High | Audit the bundle on every release; replace heavy dependencies with lighter equivalents. |
| P4 | High | Monitor CWV continuously in production, segmented by route, device, and geography. |
| P4 | High | Track regressions per deploy; auto-alert on P75 LCP, INP, or CLS degradation. |
| P4 | Medium | Code-split per route automatically; dynamic-import heavy client widgets manually. |
| P4 | Medium | Move heavy computation off the main thread (workers, scheduler yields) to protect INP. |
| P4 | Low | Memoize only after profiling proves a re-render is the bottleneck. |

---

## TypeScript & Code Quality Behaviors

| Phase | Crit. | Behavior |
|---|---|---|
| P1 | Critical | Enable strict TS across the project: `strict`, `noUncheckedIndexedAccess`, `noImplicitOverride`, `exactOptionalPropertyTypes`. |
| P1 | Critical | Ban `any`, `@ts-ignore`, and unchecked `as` casts; require type guards or schema parsing at boundaries. |
| P1 | Critical | Treat lint warnings as errors in CI on protected branches; no green merge with red warnings. |
| P1 | High | Parse all external input (HTTP, env, storage, third-party SDKs) through a schema; pass narrowed types downstream. |
| P1 | High | Read environment variables through a single typed module; fail boot if required vars are missing or malformed. |
| P2 | High | Model state with discriminated unions, not boolean flags. |
| P2 | High | Prefer `readonly` and `as const`; treat mutation as a deliberate, named decision. |
| P2 | High | Keep functions pure where possible; isolate I/O and side effects behind named seams. |
| P2 | High | Co-locate tests with the code they exercise; require unit tests for business logic and integration tests for boundaries. |
| P2 | High | Use typed result envelopes (`ok`/`err`) at fallible seams; never throw across module boundaries without a typed contract. |
| P2 | Medium | Document public APIs with TSDoc; keep private helpers self-explanatory and short. |
| P2 | Medium | Use named exports; avoid default exports for testable modules. |
| P3 | High | Enforce import boundaries (`server-only`, `client-only`, layered module rules) so leakage fails the build. |
| P3 | High | Avoid barrel files at module roots; import from leaves to preserve tree-shaking. |
| P3 | Medium | Cap cyclomatic complexity per function; split when a function holds more than one responsibility. |
| P3 | Medium | Keep modules small and named for what they do, not what they contain (no `utils.ts` dumping grounds). |
| P4 | Medium | Refactor on the third repetition, not the second; resist premature abstraction. |
| P4 | Low | Track dead code and unused exports; remove on sight. |

---

## Infrastructure & Operations Behaviors

| Phase | Crit. | Behavior |
|---|---|---|
| P1 | Critical | Reproducible builds: lockfile committed, pinned runtime version, deterministic install in CI. |
| P1 | Critical | All secrets in a secret manager; never in the repo, never in build args, never echoed in logs. |
| P1 | High | CI runs typecheck, lint, test, and build on every PR; failures block merge. |
| P1 | High | Environment parity: development, preview, and production share the same runtime and major dependency versions. |
| P2 | Critical | Database migrations are reviewed, reversible, and applied through a single pipeline — never by hand in production. |
| P2 | Critical | Deploy immutable artifacts; one promotion path per environment; never edit production in place. |
| P2 | High | Health checks gate rollouts; automatic rollback on health failure. |
| P2 | High | Every release carries a tag and a changelog; deploys are traceable to a commit and an author. |
| P2 | High | Backups are scheduled and restore drills are exercised on a cadence — an untested backup is not a backup. |
| P3 | Critical | Least privilege everywhere: service accounts, DB roles, and API keys scoped to what they need and nothing more. |
| P3 | High | Structured logs, metrics, and traces flow to a central observability stack; alerts page humans only on real signal. |
| P3 | High | Define and publish SLOs; the error budget governs feature velocity versus reliability work. |
| P3 | High | Run regular dependency and image vulnerability scans; treat critical findings as production incidents. |
| P3 | Medium | Document the rollback path; rehearse it; target under five minutes from decision to safe state. |
| P4 | High | Review capacity and cost quarterly; tune autoscaling against real traffic, not guesses. |
| P4 | High | Incident retrospectives are blameless, written, and produce dated action items with owners. |
| P4 | Medium | The disaster recovery plan is current and exercised at least annually. |

---

## Quality Gates

A change reaches `main` only when **all** of the following hold for the phase the project is in:

- All **Critical** directives for the current phase and every prior phase are satisfied — or covered by a recorded, time-bound waiver.
- All **High** directives are satisfied or carry an approved exception with a fix date.
- Typecheck, lint, test, and build pass in CI; coverage does not regress against the baseline.
- Security review has approved any change touching auth, authorization, the DAL, a Server Action, a Route Handler, or a security header.
- Performance budgets (LCP, INP, CLS at P75) are not regressed beyond the configured threshold.

A change reaches **production** only when the deploy is immutable, traceable to a commit, observable, and reversible.

---

## Governance

This constitution supersedes ad-hoc conventions. When a directive here conflicts with a tutorial, a blog post, a framework changelog, or an LLM suggestion, **this document wins** until it is formally amended.

- **Amendments** require a PR that updates this file, a changelog entry, and — when a directive changes criticality or phase — a migration plan for code already in the affected category.
- **Waivers** for Critical or High directives must be recorded inline in the affected code with an owner, a reason, and an expiry date no further than one release cadence away.
- **Reviews** must verify compliance explicitly: every PR description references the directives it touches; every reviewer checks them.
- **Drift audits** run on a scheduled cadence (at minimum once per release) to detect silent regressions against this constitution.

The runtime companion for day-to-day agent guidance lives at `templates/agent-context.md` and is mirrored into the project's agent context file (`AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, or equivalent).

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | **Last Amended**: [LAST_AMENDED_DATE]
