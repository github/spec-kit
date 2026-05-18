---
description: Next.js-specialized planning command. Decomposes a feature into routes, RSC/client boundaries, Server Actions, Route Handlers, schema validators, DAL methods, caching strategy, prerendering strategy, metadata, and accessibility checkpoints — all tagged with Phase and Criticality.
handoffs:
  - label: Generate Tasks
    agent: speckit.tasks
    prompt: Generate Next.js-shaped tasks from this plan. Sequence by dependency order.
---

## User Input

```text
$ARGUMENTS
```

Parse the user's description to extract:
- Feature name / route prefix (e.g. `app/dashboard`, `app/(auth)/login`)
- Data shape (entities, fields, relationships) — infer from context if not stated
- Auth requirement — `none` / `required` / `required + ownership`
- Known dependencies — ORM, auth provider, validation library, styling layer

If critical fields are missing and cannot be reasonably inferred, ask one clarifying question before proceeding.

## Pre-Execution Checks

Check for `.specify/extensions.yml`. If present, look for hooks under `hooks.before_plan`. Apply the same hook-processing rules as `/speckit.audit`: skip hooks with `enabled: false`, skip hooks with non-empty `condition`, surface optional hooks as instructions, auto-execute mandatory hooks.

## Outline

Produce a structured plan using this exact template. Omit any sub-section that is not applicable; add a one-line note explaining why.

---

```
# Plan: <Feature Name>

**Route prefix**: `<app/...>`
**Phase**: <P1 | P2 | P3 | P4>
**Auth**: <none | required | required + ownership>
**Constitution ref**: `.specify/memory/constitution.md`

---

## 1. Route Map

| Segment | Type | RSC? | Auth gate |
|---|---|---|---|
| `app/<path>/page.tsx` | Page | Yes | <none/required> |
| `app/<path>/layout.tsx` | Layout | Yes | <none/required> |
| `app/<path>/loading.tsx` | Skeleton | Yes | — |
| `app/<path>/error.tsx` | Error boundary | Client | — |
| `app/<path>/not-found.tsx` | 404 | Yes | — |
| `app/api/<path>/route.ts` | Route Handler | — | <method list> |

*List only the segments this feature actually needs. Mark `RSC?` as No only when `"use client"` is required.*

---

## 2. RSC / Client Boundary

**Server boundary**: `<root segment — everything above this is RSC>`
**Client islands**:
- `<ComponentName>` — reason (user interaction / browser API / client-state)
- ...

**Discipline check**:
- [ ] `"use client"` pushed to the smallest leaf, not to a page or layout
- [ ] No `async` / `await` inside `"use client"` components (use Server Components or Route Handlers for data fetching)
- [ ] No `useEffect` for data fetching

---

## 3. Data Flow

### 3a. Server Actions

| Action | File | Parse | Authorize | Ownership | DTO |
|---|---|---|---|---|---|
| `<actionName>` | `app/<path>/actions.ts` | zod/valibot | session.userId | resourceId === actor | `Pick<...>` |

*Each action is a public POST endpoint. Parse → Authorize → Ownership → DTO is non-negotiable (constitution: BE.ACTION / Critical).*

### 3b. Route Handlers

| Method | File | Auth | Rate-limit | Purpose |
|---|---|---|---|---|
| POST | `app/api/<path>/route.ts` | Bearer / session | yes | webhook / external client |

### 3c. DAL Methods

| Method | File | Input type | Return type |
|---|---|---|---|
| `get<Entity>ById` | `lib/dal/<entity>.ts` | `{ id: BrandedId }` | `Result<EntityDTO>` |
| `create<Entity>` | `lib/dal/<entity>.ts` | `CreateEntityInput` | `Result<EntityDTO>` |

*Every DAL file starts with `import 'server-only'`. Inputs are schema-parsed; return type is a typed envelope, never `any`.*

---

## 4. Schema Validators

| Schema name | File | Validates |
|---|---|---|
| `<EntityName>Schema` | `lib/schemas/<entity>.ts` | Create/Update body |
| `<RouteParams>Schema` | `lib/schemas/<entity>.ts` | Dynamic route params |

*Use the project's configured validator (zod / valibot / yup). Never widen to `unknown` without narrowing; never use `any`.*

---

## 5. Caching Strategy

| Fetch / Query | Cache directive | Revalidation |
|---|---|---|
| `<description>` | `{ cache: 'force-cache' }` / `unstable_cache` | `revalidateTag('<tag>')` on mutation |
| `<description>` | `{ cache: 'no-store' }` | — (real-time) |

*Every `fetch` or `unstable_cache` call must have an explicit cache directive. No implicit defaults.*

---

## 6. Prerendering Strategy

| Segment | Strategy | Reason |
|---|---|---|
| `app/<path>/page.tsx` | Static (`generateStaticParams`) | Content known at build |
| `app/<path>/page.tsx` | Dynamic (`force-dynamic`) | User-specific data |
| `app/<path>/page.tsx` | ISR (`revalidate: N`) | Shared, time-sensitive |

---

## 7. Streaming & Suspense

List every data-fetch boundary and its Suspense skeleton:

- `<DataComponent>` wrapped in `<Suspense fallback={<SkeletonName />}>` in `app/<path>/page.tsx`
- Loading skeleton: `app/<path>/loading.tsx` covers the full route segment

*Avoid blocking the whole page on a slow query. Use parallel `Promise.all` for independent fetches.*

---

## 8. Metadata

```ts
// app/<path>/page.tsx — generateMetadata
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  // fetch minimal fields for title / description / OG
  return {
    title: `<Title> | <Site>`,
    description: `...`,
    openGraph: { ... },
  };
}
```

*Required for every public-facing page (constitution: FE / Medium).*

---

## 9. Accessibility Checkpoints

- [ ] Interactive elements are native HTML (`<button>`, `<a>`) or carry full ARIA role/label
- [ ] Images carry descriptive `alt`; decorative images use `alt=""`
- [ ] Form errors announced via `aria-describedby` / `role="alert"`
- [ ] Color contrast ≥ 4.5:1 (AA) for normal text, ≥ 3:1 for large text
- [ ] Keyboard navigation tested for all interactive flows

---

## 10. Error Handling

| Layer | Mechanism | Scope |
|---|---|---|
| Server Action failure | Return `{ error: string }` DTO | Caller shows inline error |
| RSC fetch error | `error.tsx` boundary | Segment-level |
| Route Handler error | `NextResponse.json({ error }, { status })` | HTTP client |
| DAL failure | Typed `Result` envelope (`{ ok: false; error }`) | Bubbles to Action |

*Never throw untyped errors from Server Actions or DAL methods. The client should always receive a typed failure state.*

---

## 11. Security Checklist

- [ ] CSRF: Server Actions are protected by Next.js origin check (same-origin + `SameSite=Lax` cookie)
- [ ] Route Handler webhooks verify HMAC signature before processing
- [ ] Rate limiting on public Route Handlers
- [ ] Authorization re-checked inside every Server Action (not only at the route level)
- [ ] Ownership enforced: `resource.userId === session.userId` before mutation
- [ ] No secrets interpolated into client components or public env vars (`NEXT_PUBLIC_`)
- [ ] Content-Security-Policy header configured in `next.config.*`

---

## 12. Testing Plan

| Test type | Target | Tool |
|---|---|---|
| Unit | Schema validators | vitest |
| Unit | DAL methods (mock DB) | vitest |
| Integration | Server Actions | vitest + db fixture |
| E2E | Happy path + auth gate | Playwright |

---

## 13. Phase Gate

**This plan targets Phase <P1/P2/P3/P4>.** Directives from higher phases are noted as `[future]` and do not block this iteration.

Items deferred to a higher phase:
- `[P3]` Rate limiting on public endpoints
- `[P3]` Full audit trail in `audit_log` table
- *(adjust to match your actual deferrals)*

---

## 14. Open Questions

List any decisions the team needs to make before implementation starts:

1. <Question>
2. ...

*(Delete this section if there are none.)*
```

---

## Post-Plan Checks

After producing the plan:

1. Verify every Server Action listed in §3a has Parse / Authorize / Ownership / DTO columns completed. If any column is marked `—` without justification, call it out as a constitution risk.
2. Verify every DAL method listed in §3c has a typed return envelope — not `Promise<any>` or `Promise<Row>`.
3. Verify every `fetch` in §5 has an explicit cache directive — no row is left blank.
4. If the plan targets P1 but includes Critical directives that are marked `[future]`, flag each one and ask the user to confirm the deferral.

After completing these checks, offer:

```
## Next Steps

Run `/speckit.tasks` to generate implementation tasks from this plan, or
run `/speckit.scaffold.route app/<path>` to scaffold the route structure now.
```

## Post-Execution Hooks

Check `.specify/extensions.yml` for `hooks.after_plan` entries and apply the same hook-processing rules.
