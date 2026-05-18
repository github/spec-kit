# Next.js Project — Agent Operating Rules

These rules apply on **every turn**. They are derived from the project constitution at `.specify/memory/constitution.md`; that document is the source of truth and supersedes anything here on conflict.

A directive's weight depends on its **Phase** (when it must hold) and **Criticality** (how strictly).

- Phases: **P1 Foundation** → **P2 MVP** → **P3 Hardening** → **P4 Scale** (continuous).
- Criticality: **Critical** (blocks release) · **High** (needs an approved, time-bound exception) · **Medium** (default expectation) · **Low** (recommended).

Before proposing code, check the relevant section below. When a directive conflicts with a request, surface the conflict — don't silently violate it.

---

## Universal rules (always)

- **Server-first.** Default to Server Components. Add `"use client"` only at the smallest interactive leaf. Push the boundary down, not up.
- **Type safety is a contract.** No `any`. No unchecked `as`. No `@ts-ignore`. Parse external input through a schema at the boundary; pass narrowed types downstream.
- **Authorization lives in the Data Access Layer.** Middleware is a convenience, never a security boundary. Re-verify identity, role, and **resource ownership** inside every action and route handler.
- **Inputs are hostile.** Validate every Server Action body, every Route Handler payload, every URL parameter — and every value read from environment, storage, or third-party SDKs.
- **Measure before optimizing.** Field data at P75 drives perf decisions. Local Lighthouse is a smoke test, not a verdict.
- **Accessibility is part of done.** Semantic HTML, keyboard paths, visible focus, screen-reader labels — every interactive component, every time.
- **Observability is non-optional.** Correlate by request ID across layers. Log structured events. Errors carry context internally and leak nothing externally.

---

## Frontend — what to do

- Co-locate fetches inside the Server Component that renders them.
- Parallelize Server Component fetches with `Promise.all`; never await sequentially when fetches are independent.
- Wrap slow segments in `<Suspense>` with meaningful skeletons. Multiple boundaries per page, not one.
- Use `loading.tsx`, `error.tsx`, `not-found.tsx`, `forbidden.tsx` at every meaningful segment.
- Use `<Link>` for in-app navigation. Define `generateMetadata` per route. Use `generateStaticParams` for prerenderable dynamic routes.
- Reserve dimensions for above-the-fold dynamic content (keep CLS ~0). One `priority` image per route (the LCP candidate). Accurate `sizes` everywhere.
- Self-host fonts, enable fallback metric adjustment, use `display: swap`.
- Lazy-load heavy client widgets via dynamic import. Avoid barrel imports that defeat tree-shaking.
- Keep client state minimal; lift server-derived data to the server. Prefer CSS and platform primitives over JS for animation, layout, toggles.

## Frontend — what NOT to do

- Don't put `"use client"` at a layout or page root to "make a small button work."
- Don't trust a layout to enforce auth — layouts don't run on every request.
- Don't bake static dimensions into shells just to hide a missing skeleton.
- Don't await fetches sequentially for independent data.
- Don't ship one giant `<Suspense>` boundary for the whole page.

---

## Backend — what to do

- All data access flows through a single Data Access Layer. Sensitive modules are marked `server-only` so client imports fail the build.
- Keep business logic in pure service functions. Actions and handlers stay thin (parse → authorize → call service → return DTO).
- Treat every Server Action as a public POST endpoint. Validate the body. Re-verify auth and authorization. Check resource ownership on every mutation and read.
- Use DB transactions for multi-step mutations that must be atomic.
- Return DTOs with only fields the client needs. Don't leak rows.
- Don't capture sensitive data inside Server Action closures — pass IDs from the URL and re-resolve server-side.
- Use Route Handlers for webhooks and non-browser clients; Server Actions for in-app mutations. Verify webhook signatures and idempotency keys; reject replays.
- Return proper HTTP status codes. Wrap fallible operations in typed result envelopes.
- Revalidate caches surgically by tag or path after mutations. Make mutations idempotent where feasible.

## Backend — what NOT to do

- Don't query the database directly from a component or action — go through the DAL.
- Don't authorize once at the page and assume actions inherit it.
- Don't echo internal errors to clients. Don't collapse everything to `500`.
- Don't enforce tenant isolation in the UI layer — enforce it at the data layer.

---

## Security — what to do

- Defense-in-depth: edge → route → DAL, with the DAL as the source of truth.
- Sessions: `httpOnly`, `Secure`, `SameSite` cookies. Never `localStorage`.
- Passwords: memory-hard hashing. Never store, log, or echo. Rotate and sign session secrets. Invalidate sessions on logout, password change, and privilege change.
- Parameterized queries everywhere. Sanitize and encode user-generated content before rendering.
- Keep secrets server-side; never put sensitive values behind the public env var prefix.
- File uploads are hostile: validate MIME, size, and extension; store outside the web root; scan.
- Rate-limit every mutation and auth-adjacent endpoint per IP and per user. Add bot mitigation or CAPTCHA on signup, password reset, contact, and abuse-prone actions.
- Whitelist Server Action allowed origins in multi-domain or reverse-proxied deployments.
- Apply strict CSP with nonces; ship HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`.
- Enforce MFA at the application level for high-risk actions.
- Audit every `"use server"` file: validation, auth, authz, ownership, return shape. Audit every `"use client"` prop shape for serialization leaks.
- Pin and audit dependencies; vulnerability-scan every PR; patch CVEs in framework, runtime, and auth libraries promptly.
- Log auth events, permission changes, and admin actions to an append-only audit trail.

## Security — what NOT to do

- Never rely on middleware as a security boundary.
- Never store sessions in `localStorage`. Never use a public env prefix for secrets.
- Never concatenate strings into SQL. Never render unsanitized HTML.
- Never return stack traces or internal error details to production clients.

---

## Performance — what to do

- Make caching explicit and opt-in per fetch and per component. No implicit assumptions.
- Stream HTML; never block on the slowest fetch. Fan out Server Component fetches in parallel.
- Set Core Web Vitals budgets (LCP, INP, CLS at P75). Enforce in CI. Measure field data before optimizing.
- Identify the actual LCP element with a perf trace before touching images.
- Serve static assets from a CDN with immutable filenames and long `Cache-Control`. Use AVIF/WebP, correct `sizes`, tuned breakpoints. Subset and self-host fonts; preload only above-the-fold weights.
- Compress responses (Brotli/Zstd). Serve over HTTP/2 or HTTP/3.
- Right-size DB connection pooling. Choose an edge-compatible driver when the route is edge-targeted.
- Use partial prerendering where supported (static shell + streamed dynamic holes). Use ISR or on-demand revalidation for occasional-change content.
- Load third-party scripts with the lowest-priority strategy that still works. Preconnect/preload only genuinely critical origins.
- Audit the bundle every release. Monitor CWV continuously in production, segmented by route, device, geography. Auto-alert on P75 regressions.
- Move heavy computation off the main thread (workers, scheduler yields) to protect INP.

## Performance — what NOT to do

- Don't memoize before profiling — guesses get the cost without the gain.
- Don't preload "just in case." Don't ship a script with `defer` when `afterInteractive` or `lazyOnload` is enough.
- Don't trust local Lighthouse as evidence of field perf.

---

## TypeScript Engineering — what to do

TypeScript directives carry a **Scope** tag: `FE` (frontend), `BE` (backend), or `Both`. The full matrix lives in the constitution under *TypeScript Engineering Behaviors*; the operating cheat sheet below is what every agent must keep in mind on every change.

**Compiler & project config (Both)**
- Strict from day one: `strict: true`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noFallthroughCasesInSwitch`, `noImplicitReturns`, `forceConsistentCasingInFileNames`.
- Use path aliases (`@/*`); avoid `../../../` chains. Use project references / `composite` in monorepos.
- Type errors fail the CI build. Replace `@ts-ignore` with `@ts-expect-error` carrying a justification when truly necessary.

**Type system discipline (Both)**
- `unknown` for untrusted/dynamic data; narrow before use. Never `any`.
- Use `satisfies` for configs/routes/themes; use `as const` to prevent widening.
- Discriminated unions over boolean flags. Make illegal states unrepresentable in the type.
- Branded/nominal types for IDs, emails, and tokens — not raw `string`.
- User-defined type predicates (`x is X`) for runtime narrowing. Type async returns explicitly. Narrow `catch` errors with `instanceof Error` or a typed union.
- Reach for `Pick` / `Omit` / `Partial` / `Required` / `Record` before rolling your own. Use `readonly` and `ReadonlyArray` for inputs. Use template literal types for constrained strings.
- Constrain generics with `extends`. Prefer interfaces for extensible shapes; types for unions/intersections/mapped.

**SOLID**
- **SRP / OCP** apply to both FE and BE: one reason to change; extend via new modules, not by editing existing ones.
- **DIP / dependency injection** (BE): high-level code depends on abstractions. Inject DB, mailer, clock, and logger — never instantiate inside business logic.
- **ISP / LSP** (Both): split fat interfaces; subtypes honor the parent contract.
- Composition over inheritance.

**Clean code & functional discipline (Both)**
- Pure functions by default; isolate side effects at the edges. Immutable data; mutation is opt-in.
- DRY only after the third repetition (Rule of Three). KISS / YAGNI. Law of Demeter.
- Self-documenting names. Small functions, single level of abstraction, low cyclomatic complexity.
- Early returns over `if`/`else` pyramids. Boolean parameters are a smell — split or pass an enum. Limit args to ≤ 3; group into a typed options object.

**Runtime boundaries (Both / BE / FE)**
- **Parse, don't validate.** Convert untrusted input into a typed value at the boundary, then trust the type.
- (BE) Validate every external input — HTTP body, params, headers, env, queue messages — with a schema.
- Validate environment variables at startup. Fail fast.
- Never trust TS types at runtime across a process boundary. Define DTOs decoupling internal models from wire shapes.
- (FE) Validate API responses on the client if the server contract isn't generated from a single source of truth.
- Generate types from the source of truth (DB schema, OpenAPI, schema). `Result<T, E>` for expected failures; exceptions for unexpected ones.

**Frontend patterns (FE)**
- Type every prop explicitly. Discriminated-union props for component variants.
- Type event handlers with the specific event type. Type `useState` explicitly when initial value doesn't capture the full union. Type refs with the specific element interface.
- Generic components for reusable lists / forms / tables to preserve item types end-to-end.
- Don't pass private or server-only types to client components.
- Type custom hooks' return as `const` tuples or named objects for stable inference.

**Backend patterns (BE)**
- Mark server-only modules so client imports fail the build.
- Type all service-layer inputs and outputs.
- Model domain errors as a typed union. Use `never` to enforce exhaustive `switch` on discriminated unions.
- Type DB rows from the schema. Keep domain ↔ persistence ↔ API types separate. Use opaque/branded IDs (`UserId` ≠ `OrderId`).

**Project hygiene & DX (Both)**
- One linter, one formatter, both on pre-commit and in CI. Ban circular imports via lint rule.
- `PascalCase` types/components, `camelCase` values, `SCREAMING_SNAKE_CASE` constants.
- Co-locate types with their module; export only what consumers need. At most one barrel per public boundary.
- Write tests against the type-level contract, not only runtime behavior. Document non-obvious types with TSDoc.
- Track `tsc` performance; use `--incremental`; split projects when builds exceed budget.

## TypeScript Engineering — what NOT to do

- No `any`. No `@ts-ignore`. No unchecked `as`. No `// eslint-disable` without a justified reason.
- No raw `string` for IDs / emails / tokens — use branded types.
- No boolean-parameter explosions — split or use an enum / discriminated union.
- No deep class hierarchies — compose.
- No hand-rolled DB row interfaces — type from the schema.
- No global `index.ts` barrels that hide circular deps.
- No premature abstraction — refactor on the third repetition, not the second.
- No `HTMLElement` as a catch-all ref type. No `Promise<any>` as an inferred return.

---

## Infrastructure & Operations — what to do

- Reproducible builds: lockfile committed, runtime version pinned, deterministic CI install.
- All secrets in a secret manager. Never in repo, build args, or logs.
- CI runs typecheck, lint, test, and build on every PR. Failures block merge.
- Environment parity: dev, preview, prod share the same runtime and major dependency versions.
- DB migrations: reviewed, reversible, applied through a single pipeline. Never edit production by hand.
- Deploy immutable artifacts. Health checks gate rollouts; automatic rollback on health failure. Every release carries a tag and a changelog.
- Backups scheduled; restore drills exercised on a cadence.
- Structured logs, metrics, and traces in a central observability stack. Alerts page humans only on real signal. SLOs published; error budget governs reliability vs. feature work.
- Document the rollback path; rehearse it; target under five minutes.

## Infrastructure & Operations — what NOT to do

- Don't ship to prod without a tag, a changelog, and a traceable commit.
- Don't keep secrets in `.env.production` checked into the repo.
- Don't run a migration manually "just this once."
- Don't trust a backup you've never restored.

---

## When in doubt

1. Re-read the constitution section that governs the area you're touching.
2. If a behavior is missing or ambiguous, **propose an amendment** rather than improvising.
3. If a directive blocks a legitimate goal, raise it — don't quietly violate it. A waiver with an owner and an expiry beats a silent regression.
