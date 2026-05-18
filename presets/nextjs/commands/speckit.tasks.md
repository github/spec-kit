---
description: Next.js-specialized task generation. Converts a feature plan into an ordered, constitution-compliant task list with Next.js-shaped task titles, acceptance criteria referencing behavioral directives, and explicit phase tags.
handoffs:
  - label: Open Plan
    agent: speckit.plan
    prompt: Produce a Next.js plan for this feature so tasks can be generated from it.
---

## User Input

```text
$ARGUMENTS
```

If a plan document path is supplied (e.g. `.specify/plans/feature-name.md`), read it and derive tasks from it.
If the argument is a freeform feature description, derive tasks directly from the description.
If the argument is empty, look for the most recent plan at `.specify/plans/` and generate tasks from it.

## Pre-Execution Checks

Check for `.specify/extensions.yml`. Look for hooks under `hooks.before_tasks`. Apply standard hook-processing (skip `enabled: false`, skip non-empty `condition`, surface optional, auto-execute mandatory).

## Outline

### 1. Parse the plan

Extract:
- Route prefix (e.g. `app/dashboard`)
- List of segments (page, layout, loading, error, not-found, route handlers)
- List of Server Actions + their recipe columns (Parse / Authorize / Ownership / DTO)
- List of DAL methods
- List of schemas
- Caching directives
- Phase target
- Auth requirement
- Testing plan

### 2. Produce the task list

Generate tasks using the template below. Follow these ordering rules:

**Dependency order** (tasks must be listed in this order unless a dependency makes an exception necessary):

1. Schema validators (schemas are imported by both DAL and Actions)
2. DAL methods (depend on schemas; are imported by Actions)
3. Server Actions (depend on schemas + DAL)
4. Route structure scaffold (RSC pages, layouts, loading, error, not-found)
5. RSC data-fetching components (depend on DAL)
6. Client islands (depend on RSC boundary decisions)
7. Route Handlers (independent of above, but after DAL)
8. Metadata (`generateMetadata`)
9. Suspense / Skeleton components
10. Tests (unit → integration → E2E)

Within each group, order by dependency (e.g. `getEntityById` before `createEntity`).

---

```
# Tasks: <Feature Name>

**Plan ref**: <path or "inline">
**Phase**: <P1 | P2 | P3 | P4>
**Total tasks**: <N>
**Constitution ref**: `.specify/memory/constitution.md`

---

## Foundation (unblock everything)

### TASK-001 — Add `<EntityName>` zod schema
*File*: `lib/schemas/<entity>.ts`
*Phase/Crit*: P1 / Critical · Scope: Both

**What**:
- Create `<EntityName>Schema` with `z.object({ ... })`
- Export `type <EntityName>Input = z.infer<typeof <EntityName>Schema>`
- Add `<EntityName>ParamsSchema` for dynamic route params if applicable

**Acceptance criteria**:
- [ ] Schema compiles under `tsc --noEmit` with no errors
- [ ] `parse()` throws `ZodError` on invalid input (test in unit suite)
- [ ] No field typed as `any` or `unknown` without explicit narrowing

**Constitution directives**: `BE.ENV.schema-validated-boundaries` (Critical) · `TS.TYPE.any-usage` (Critical)

---

### TASK-002 — Scaffold DAL module `lib/dal/<entity>.ts`
*File*: `lib/dal/<entity>.ts`
*Phase/Crit*: P1 / Critical · Scope: BE

**What**:
- `import 'server-only'` as first line
- `get<Entity>ById(id: BrandedId): Promise<Result<EntityDTO>>`
- `create<Entity>(input: CreateEntityInput): Promise<Result<EntityDTO>>`
- *(add other methods from plan §3c)*
- Return `{ ok: true; data }` / `{ ok: false; error }` — never throw to callers

**Acceptance criteria**:
- [ ] `server-only` import present — verified by audit rule `BE.DAL.missing-server-only`
- [ ] Return type is `Promise<Result<EntityDTO>>`, not `Promise<any>`
- [ ] No raw SQL string interpolation (parameterized queries only)
- [ ] Unit tested with a mock DB fixture

**Constitution directives**: `BE.DAL.missing-server-only` (Critical) · `SEC.SQL.injection` (Critical) · `TS.TYPE.any-usage` (Critical)

---

## Server Actions

### TASK-003 — Implement `<actionName>` Server Action
*File*: `app/<path>/actions.ts`
*Phase/Crit*: P2 / Critical · Scope: BE

**What**:
- `'use server'` directive at file top
- **Parse**: `<EntityName>Schema.parse(formData / input)` at function top
- **Authorize**: `const session = await getServerSession(); if (!session) redirect('/login')`
- **Ownership**: `if (resource.userId !== session.user.id) throw new Error('Forbidden')`
- **DTO**: return `{ <field>, <field> }` — only the fields the client needs
- Call the DAL method, handle `Result.ok === false`

**Acceptance criteria**:
- [ ] Parse fires before any DB call
- [ ] Auth check is inside the action (not just at layout/middleware)
- [ ] Ownership check present when action mutates a user-owned resource
- [ ] Return value is a typed DTO — no raw DB row exposed to the client
- [ ] Integration-tested with an authenticated + unauthenticated fixture

**Constitution directives**: `BE.ACTION.recipe-violation` (Critical) · `SEC.SESSION.auth-at-action` (Critical)

---

## Route Structure

### TASK-004 — Scaffold route segment `app/<path>/`
*Files*: `page.tsx` · `layout.tsx` · `loading.tsx` · `error.tsx` · `not-found.tsx`
*Phase/Crit*: P1 / High · Scope: FE

**What**:
- `page.tsx` — async RSC; fetches data via DAL (no `"use client"`)
- `layout.tsx` — RSC; wraps children; no data fetching unless shared data (e.g. nav user)
- `loading.tsx` — instant skeleton shown during page-level Suspense
- `error.tsx` — `"use client"` boundary; receives `error` + `reset` props
- `not-found.tsx` — RSC; shown when `notFound()` is thrown

**Acceptance criteria**:
- [ ] `page.tsx` has no `"use client"` directive
- [ ] `error.tsx` is the only file with `"use client"` in this segment (unless client islands are needed)
- [ ] `loading.tsx` renders a skeleton — not an empty `<div>`
- [ ] `generateMetadata` exported from `page.tsx` (or a separate `metadata.ts`)

**Constitution directives**: `FE.RSC.use-client-at-page-or-layout` (High) · `FE.META.missing-generate-metadata` (Medium)

---

## RSC Data Components

### TASK-005 — Implement `<EntityList>` RSC component
*File*: `app/<path>/_components/<EntityList>.tsx`
*Phase/Crit*: P1 / Medium · Scope: FE

**What**:
- `async` function — fetches data via DAL, NOT via `fetch('/api/...')`
- Wrapped in `<Suspense fallback={<EntityListSkeleton />}>` at the call site in `page.tsx`
- Uses `Promise.all([...])` if multiple independent fetches are needed

**Acceptance criteria**:
- [ ] No `useEffect`, `useState`, or browser API calls
- [ ] Parallel fetches for independent data (not sequential `await`)
- [ ] Skeleton shown while data loads (Suspense in page.tsx)

**Constitution directives**: `FE.RSC.client-fetch` (High) · `PERF.FETCH.parallel-fetches` (Medium)

---

## Client Islands

### TASK-006 — Implement `<InteractiveWidget>` client component
*File*: `app/<path>/_components/<InteractiveWidget>.tsx`
*Phase/Crit*: P1 / High · Scope: FE

**What**:
- `'use client'` at the top
- Receives pre-fetched data as props from the RSC parent
- Calls Server Actions via `useTransition` / `useFormState` — no `fetch('/api/...')`
- Manages only UI state (open/closed, form values) — no auth state, no session

**Acceptance criteria**:
- [ ] Props typed as `Readonly<{ ... }>` — no `any`
- [ ] No direct DB or DAL imports
- [ ] No auth context — identity passed as a prop if needed for display
- [ ] Accessible: interactive elements are native HTML or fully ARIA-labelled

**Constitution directives**: `FE.RSC.use-client-at-page-or-layout` (High) · `TS.TYPE.any-usage` (Critical) · `FE.A11Y.*` (Critical)

---

## Route Handlers (if applicable)

### TASK-007 — Implement `POST app/api/<path>/route.ts`
*File*: `app/api/<path>/route.ts`
*Phase/Crit*: P2 / Critical · Scope: BE

**What**:
- Verify `Authorization` header (Bearer) or session cookie
- Parse body with schema before any processing
- Rate-limit via `<rate-limiter>` (project-configured)
- HMAC signature check for webhook endpoints (`X-<Provider>-Signature`)
- Return typed `NextResponse.json(dto, { status })` — no raw DB row

**Acceptance criteria**:
- [ ] Returns `401` for unauthenticated requests
- [ ] Returns `400` for schema-invalid bodies
- [ ] Rate limiting wired
- [ ] No secrets in response body or headers

**Constitution directives**: `SEC.SESSION.auth-at-action` (Critical) · `BE.ENV.schema-validated-boundaries` (Critical) · `SEC.RATE.missing` (High)

---

## Metadata

### TASK-008 — Add `generateMetadata` to `app/<path>/page.tsx`
*File*: `app/<path>/page.tsx`
*Phase/Crit*: P2 / Medium · Scope: FE

**What**:
- Export `generateMetadata({ params, searchParams }: Props): Promise<Metadata>`
- Fetch minimal fields (title, description image) — use `{ cache: 'force-cache' }` if data is stable
- Return `title`, `description`, `openGraph`, `twitter` at minimum

**Acceptance criteria**:
- [ ] No `<title>` hard-coded in JSX — only `generateMetadata`
- [ ] OG image included for public pages
- [ ] Dynamic pages fetch their own metadata — not a copy-paste of the layout's metadata

**Constitution directives**: `FE.META.missing-generate-metadata` (Medium)

---

## Suspense Skeletons

### TASK-009 — Build `<EntityListSkeleton>` component
*File*: `app/<path>/_components/<EntityList>.skeleton.tsx`
*Phase/Crit*: P1 / Medium · Scope: FE

**What**:
- RSC (no `"use client"`)
- Renders placeholder UI matching the shape of `<EntityList>` (same layout, no real data)
- Used as `fallback` in `<Suspense>` in `page.tsx`

**Acceptance criteria**:
- [ ] Skeleton renders without any async calls
- [ ] Dimensions approximately match the loaded component (prevents layout shift)
- [ ] `aria-busy="true"` on the container (accessibility)

**Constitution directives**: `FE.PERF.streaming-suspense` (Medium)

---

## Tests

### TASK-010 — Unit tests for `<EntityName>` schema
*File*: `__tests__/schemas/<entity>.test.ts`
*Phase/Crit*: P2 / High · Scope: Both

**What**:
- Valid input → `parse()` returns typed object
- Missing required field → `ZodError` thrown with field path
- Type coercion edge cases (empty string, null, undefined)

### TASK-011 — Unit tests for DAL methods
*File*: `__tests__/dal/<entity>.test.ts`
*Phase/Crit*: P2 / High · Scope: BE

**What**:
- Mock the DB client
- `get<Entity>ById` with existing / missing ID
- `create<Entity>` with valid / schema-invalid input
- Verify `Result` envelope shape in all paths

### TASK-012 — Integration tests for Server Actions
*File*: `__tests__/actions/<entity>.test.ts`
*Phase/Crit*: P2 / High · Scope: BE

**What**:
- Authenticated fixture: action succeeds, returns DTO
- Unauthenticated fixture: action redirects or returns `{ error: 'Unauthorized' }`
- Schema-invalid input: action returns `{ error: '...' }` without reaching DB
- Ownership violation: action returns `{ error: 'Forbidden' }`

### TASK-013 — E2E test: happy path + auth gate
*File*: `e2e/<feature>.spec.ts`
*Phase/Crit*: P3 / Medium · Scope: FE

**What**:
- Unauthenticated user is redirected to login
- Authenticated user sees data and can perform the primary action
- Form validation errors are visible and announced (screen-reader check via `axe-core`)

---

## Phase Gate Summary

Tasks required to complete **Phase <P1/P2/P3/P4>** for this feature:

| ID | Title | Phase | Criticality | Status |
|---|---|---|---|---|
| TASK-001 | Add schema | P1 | Critical | ☐ |
| TASK-002 | Scaffold DAL | P1 | Critical | ☐ |
| TASK-003 | Server Action | P2 | Critical | ☐ |
| TASK-004 | Route scaffold | P1 | High | ☐ |
| TASK-005 | RSC component | P1 | Medium | ☐ |
| TASK-006 | Client island | P1 | High | ☐ |
| TASK-007 | Route Handler | P2 | Critical | ☐ |
| TASK-008 | Metadata | P2 | Medium | ☐ |
| TASK-009 | Skeleton | P1 | Medium | ☐ |
| TASK-010 | Schema tests | P2 | High | ☐ |
| TASK-011 | DAL tests | P2 | High | ☐ |
| TASK-012 | Action tests | P2 | High | ☐ |
| TASK-013 | E2E tests | P3 | Medium | ☐ |

*Adjust task IDs and rows to match the actual tasks generated above.*
```

---

## Formatting Rules

- Task IDs are sequential (`TASK-001`, `TASK-002`, …) within a session.
- Every task has: *File*, *Phase/Crit/Scope*, **What** (bullet list), **Acceptance criteria** (checklist), **Constitution directives** (rule IDs).
- Do not invent constitution directives — use only rule IDs from the audit script's `--list-rules` output or the constitution's behavior table.
- Omit task groups (Route Handlers, Client Islands, etc.) that are not relevant to this feature.
- The Phase Gate Summary table is always present; it is the first thing a release reviewer checks.

## Post-Execution Hooks

Check `.specify/extensions.yml` for `hooks.after_tasks`. Apply standard hook-processing.
