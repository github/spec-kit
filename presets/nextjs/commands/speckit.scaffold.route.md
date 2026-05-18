---
description: Scaffold a Next.js App Router route segment. Generates page.tsx (RSC), layout.tsx (optional), loading.tsx, error.tsx ("use client"), and not-found.tsx — all wired to Next.js conventions and the project constitution.
---

## User Input

```text
$ARGUMENTS
```

Parse the route path from `$ARGUMENTS`. Examples:

| Input | Route prefix created |
|---|---|
| `app/dashboard` | `app/dashboard/` |
| `dashboard` | `app/dashboard/` (prefix `app/` if missing) |
| `app/(marketing)/about` | `app/(marketing)/about/` |
| `app/[id]` | `app/[id]/` (dynamic segment) |
| `app/dashboard --no-layout` | skip `layout.tsx` |
| `app/dashboard --auth` | add auth redirect to `page.tsx` |
| `app/dashboard --loading=false` | skip `loading.tsx` |

Flags (all optional):
- `--auth` — add session check + redirect at the top of `page.tsx`
- `--no-layout` — skip `layout.tsx`
- `--loading=false` — skip `loading.tsx`
- `--not-found=false` — skip `not-found.tsx`
- `--title <string>` — inject a placeholder `<title>` into `generateMetadata`
- `--description <string>` — inject a placeholder `description` into `generateMetadata`

If the route path is missing or ambiguous, ask one clarifying question.

## Pre-Execution Checks

Check for `.specify/extensions.yml`. Look for hooks under `hooks.before_scaffold`. Apply standard hook-processing.

## Scaffold Steps

### 1. Resolve the route root

Compute `ROUTE_ROOT` (absolute path in the repo). If `src/app/` exists, use that as the base; otherwise use `app/`.

Example: argument `dashboard` → `ROUTE_ROOT = app/dashboard` (or `src/app/dashboard`).

### 2. Check for collisions

If any of the target files already exist, print a warning per file and ask whether to overwrite, skip, or abort before writing anything.

### 3. Write the files

#### `page.tsx`

```tsx
// <ROUTE_ROOT>/page.tsx
import type { Metadata } from 'next'
// --auth: import { redirect } from 'next/navigation'
// --auth: import { getServerSession } from '<auth-import>'

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: '<Title Placeholder>',
    description: '<Description placeholder>',
  }
}

// --auth block start
// const session = await getServerSession()
// if (!session) redirect('/login')
// --auth block end

export default async function <SegmentName>Page() {
  return (
    <main>
      <h1><SegmentName></h1>
      {/* TODO: fetch data from DAL and render */}
    </main>
  )
}
```

Rules:
- No `'use client'` — this is a Server Component.
- Function name is derived from the route segment: `dashboard` → `DashboardPage`, `[id]` → `IdPage`.
- `generateMetadata` is always present (constitution: `FE.META.missing-generate-metadata`).
- `--auth` flag injects session check before rendering.

#### `layout.tsx` (unless `--no-layout`)

```tsx
// <ROUTE_ROOT>/layout.tsx
import type { ReactNode } from 'react'

export default function <SegmentName>Layout({ children }: { children: ReactNode }) {
  return <>{children}</>
}
```

Rules:
- No `'use client'`.
- No data fetching unless it is data shared across all children (e.g. current-user nav).
- Children typed as `ReactNode`, not `React.ReactNode` (prefer direct named import).

#### `loading.tsx` (unless `--loading=false`)

```tsx
// <ROUTE_ROOT>/loading.tsx
export default function <SegmentName>Loading() {
  return (
    <div aria-busy="true" aria-label="Loading <SegmentName>…">
      {/* TODO: replace with a real skeleton component */}
      <div className="animate-pulse h-8 w-full rounded bg-muted" />
    </div>
  )
}
```

Rules:
- No `'use client'`.
- `aria-busy="true"` and `aria-label` always present (constitution: `FE.A11Y.*`).
- Skeleton must not be an empty `<div>` — placeholder `animate-pulse` block ensures reviewers see what to replace.

#### `error.tsx`

```tsx
// <ROUTE_ROOT>/error.tsx
'use client'

import { useEffect } from 'react'

interface ErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function <SegmentName>Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log to observability provider
    console.error(error)
  }, [error])

  return (
    <div role="alert">
      <h2>Something went wrong</h2>
      <p>{error.message}</p>
      <button type="button" onClick={reset}>
        Try again
      </button>
    </div>
  )
}
```

Rules:
- `'use client'` required — this is a React error boundary.
- `role="alert"` on the wrapper (screen-reader announcement).
- `useEffect` logs to the observability provider — replace `console.error` with your configured logger (Pino, Winston, Sentry, etc.).

#### `not-found.tsx` (unless `--not-found=false`)

```tsx
// <ROUTE_ROOT>/not-found.tsx
import Link from 'next/link'

export default function <SegmentName>NotFound() {
  return (
    <div>
      <h2>Not Found</h2>
      <p>The requested resource could not be found.</p>
      <Link href="/">Return Home</Link>
    </div>
  )
}
```

Rules:
- No `'use client'`.
- Use `next/link` — not `<a>` (constitution: `FE.LINK.anchor-over-link`).

### 4. Print the scaffold summary

After writing all files, output:

```
## Scaffold complete

**Route**: `<ROUTE_ROOT>/`
**Files created**:
- `<ROUTE_ROOT>/page.tsx`          ← RSC, generateMetadata, <auth gate if --auth>
- `<ROUTE_ROOT>/layout.tsx`        ← RSC wrapper  (if not skipped)
- `<ROUTE_ROOT>/loading.tsx`       ← Suspense skeleton (if not skipped)
- `<ROUTE_ROOT>/error.tsx`         ← Client error boundary
- `<ROUTE_ROOT>/not-found.tsx`     ← 404 handler (if not skipped)

**Verify**:
- [ ] Replace `animate-pulse` placeholder in `loading.tsx` with a real skeleton
- [ ] Replace `console.error` in `error.tsx` with your observability logger
- [ ] Implement `page.tsx` body (fetch from DAL, pass props to client islands)
- [ ] Run `tsc --noEmit` — new files must compile cleanly

**Next steps**:
- Run `/speckit.scaffold.dal <entity>` to scaffold the DAL module this route depends on
- Run `/speckit.plan app/<path>` to generate a full feature plan for this route
```

### 5. Constitution compliance check

After generating all files, verify:

1. `page.tsx` does **not** contain `'use client'` — if it does, the scaffold template is broken; do not write the file and report the error.
2. `error.tsx` **does** contain `'use client'` — required by Next.js for error boundaries.
3. `loading.tsx` does **not** contain `'use client'`.
4. `not-found.tsx` does **not** contain `'use client'`.
5. All files pass a basic TypeScript syntax check (no unterminated JSX, no missing brackets) before writing.

## Post-Execution Hooks

Check `.specify/extensions.yml` for `hooks.after_scaffold`. Apply standard hook-processing.
