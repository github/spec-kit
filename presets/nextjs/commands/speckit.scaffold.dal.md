---
description: Scaffold a Next.js Data Access Layer (DAL) module. Generates lib/dal/<entity>.ts with import 'server-only', typed Result envelope, schema-parsed inputs, and method stubs for the most common CRUD pattern — all compliant with the project constitution.
---

## User Input

```text
$ARGUMENTS
```

Parse from `$ARGUMENTS`:

| Token | Meaning | Default |
|---|---|---|
| First positional arg | Entity name (PascalCase or kebab-case accepted) | required |
| `--methods <list>` | Comma-separated method verbs | `get,list,create,update,delete` |
| `--schema <path>` | Path to existing zod/valibot schema file to import | auto-detected or inline stub |
| `--id-type <type>` | Branded ID type to use | `string` (with a TODO to brand it) |
| `--no-result-envelope` | Return raw type instead of `Result<T>` | omit flag to get the envelope |
| `--db <client>` | DB client hint (`prisma`, `drizzle`, `kysely`, `pg`, `mysql2`, `generic`) | `generic` |

If entity name is missing, ask for it before proceeding.

## Pre-Execution Checks

Check for `.specify/extensions.yml`. Look for hooks under `hooks.before_scaffold`. Apply standard hook-processing.

## Scaffold Steps

### 1. Normalize entity name

Convert the input to:
- `EntityName` — PascalCase (used in types, function names)
- `entityName` — camelCase (used in variable names)
- `entity-name` — kebab-case (used in file name)

Examples: `user-post` → `UserPost` / `userPost` / `user-post`

### 2. Resolve output path

Check whether `src/lib/dal/` or `lib/dal/` exists in the repo (prefer `src/` if present). Create the directory if it does not exist.

Output file: `<dal-root>/<entity-name>.ts`

If the file already exists, warn the user and ask whether to overwrite, skip, or abort.

### 3. Resolve the schema import

If `--schema <path>` was provided, import from that path.
Otherwise, look for `lib/schemas/<entity-name>.ts` (or `src/lib/schemas/<entity-name>.ts`).
If neither exists, inline a stub schema inside the DAL file with a `// TODO` directing the user to extract it.

### 4. Write the DAL module

Use this template (adapt to `--db` hint and `--methods` list):

```ts
// <dal-root>/<entity-name>.ts
import 'server-only'

// Replace with your project's DB client import
// import { db } from '@/lib/db'

import { <EntityName>Schema, type <EntityName>Input } from '@/lib/schemas/<entity-name>'

// ─── Types ────────────────────────────────────────────────────────────────────

/** Branded ID — replace `string` with your branded type (e.g. `Brand<string, '<EntityName>Id'>`) */
type <EntityName>Id = string  // TODO: brand this type

export interface <EntityName>DTO {
  id: <EntityName>Id
  // TODO: add DTO fields — expose only what the client needs
  createdAt: Date
  updatedAt: Date
}

export interface Result<T> {
  ok: true
  data: T
} | {
  ok: false
  error: string
}

// ─── Methods ──────────────────────────────────────────────────────────────────

/**
 * Fetch a single <EntityName> by ID.
 * Returns { ok: false } when not found so callers handle absence without exceptions.
 */
export async function get<EntityName>ById(
  id: <EntityName>Id,
): Promise<Result<<EntityName>DTO>> {
  try {
    // TODO: replace with your ORM/query
    // const row = await db.<entity>.findUnique({ where: { id } })
    // if (!row) return { ok: false, error: 'Not found' }
    // return { ok: true, data: to<EntityName>DTO(row) }
    throw new Error('get<EntityName>ById: not implemented')
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : 'Unknown error' }
  }
}

/**
 * List all <EntityName>s accessible to the given actor.
 * Pass ownership filters here — never return rows the actor doesn't own.
 */
export async function list<EntityName>s(
  actorId: string,
): Promise<Result<<EntityName>DTO[]>> {
  try {
    // TODO: replace with your ORM/query
    // const rows = await db.<entity>.findMany({ where: { userId: actorId } })
    // return { ok: true, data: rows.map(to<EntityName>DTO) }
    throw new Error('list<EntityName>s: not implemented')
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : 'Unknown error' }
  }
}

/**
 * Create a new <EntityName>.
 * Input is pre-validated by the schema — do not re-parse here.
 */
export async function create<EntityName>(
  input: <EntityName>Input,
  actorId: string,
): Promise<Result<<EntityName>DTO>> {
  // Schema parse — guard against callers that skip validation
  const parsed = <EntityName>Schema.safeParse(input)
  if (!parsed.success) {
    return { ok: false, error: parsed.error.message }
  }

  try {
    // TODO: replace with your ORM/query
    // const row = await db.<entity>.create({ data: { ...parsed.data, userId: actorId } })
    // return { ok: true, data: to<EntityName>DTO(row) }
    throw new Error('create<EntityName>: not implemented')
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : 'Unknown error' }
  }
}

/**
 * Update an existing <EntityName>.
 * Ownership must be verified by the caller (Server Action) before calling this.
 */
export async function update<EntityName>(
  id: <EntityName>Id,
  input: Partial<<EntityName>Input>,
): Promise<Result<<EntityName>DTO>> {
  try {
    // TODO: replace with your ORM/query
    // const row = await db.<entity>.update({ where: { id }, data: input })
    // return { ok: true, data: to<EntityName>DTO(row) }
    throw new Error('update<EntityName>: not implemented')
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : 'Unknown error' }
  }
}

/**
 * Delete an <EntityName>.
 * Ownership must be verified by the caller (Server Action) before calling this.
 */
export async function delete<EntityName>(
  id: <EntityName>Id,
): Promise<Result<void>> {
  try {
    // TODO: replace with your ORM/query
    // await db.<entity>.delete({ where: { id } })
    // return { ok: true, data: undefined }
    throw new Error('delete<EntityName>: not implemented')
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : 'Unknown error' }
  }
}

// ─── Mapper ───────────────────────────────────────────────────────────────────

/** Convert a DB row to the public DTO shape. Never expose raw DB rows to callers. */
function to<EntityName>DTO(row: unknown): <EntityName>DTO {
  // TODO: implement mapping
  throw new Error('to<EntityName>DTO: not implemented')
}
```

#### `--db` adaptations

Replace the inline `db.*` comments with the matching pattern for the detected ORM:

| `--db` value | Query stub pattern |
|---|---|
| `prisma` | `await prisma.<entity>.findUnique({ where: { id } })` |
| `drizzle` | `await db.select().from(<entity>Table).where(eq(<entity>Table.id, id)).limit(1)` |
| `kysely` | `await db.selectFrom('<entity>').where('id', '=', id).selectAll().executeTakeFirst()` |
| `pg` | `await pool.query('SELECT * FROM <entity> WHERE id = $1', [id])` |
| `generic` | Comment-only stub (as above) |

#### `--methods` filtering

Only generate the method stubs listed in `--methods`. If `--methods get,list` is passed, omit `create`, `update`, `delete` stubs.

#### `--no-result-envelope`

If this flag is set, replace `Promise<Result<T>>` with `Promise<T | null>` (for get) and `Promise<T>` (for create/update). Remove the `Result` interface. The mapper still applies.

### 5. Print the scaffold summary

```
## DAL scaffold complete

**Entity**: `<EntityName>`
**File**: `<dal-root>/<entity-name>.ts`

**Includes**:
- `import 'server-only'` ← audit rule BE.DAL.missing-server-only satisfied
- `Result<T>` typed envelope ← no raw DB rows exposed to callers
- Schema-validated input on `create<EntityName>` ← BE.ENV.schema-validated-boundaries satisfied
- Method stubs: <method list>

**TODOs** (search `// TODO` in the generated file):
- [ ] Replace DB query stubs with your ORM/client calls
- [ ] Implement `to<EntityName>DTO` mapper — expose only the fields the client needs
- [ ] Brand `<EntityName>Id` — replace `string` with a branded type
- [ ] Add DTO fields that match your DB schema

**Next steps**:
- Run `/speckit.scaffold.route app/<path>` to scaffold the page that uses this DAL
- Run `/speckit.plan <feature>` to generate a full feature plan including this DAL
- Add unit tests at `__tests__/dal/<entity-name>.test.ts`

**Audit check**: run `/speckit.audit --rules BE.DAL.missing-server-only` to verify the
`server-only` import is detected correctly.
```

### 6. Constitution compliance check

Before writing the file, verify:

1. `import 'server-only'` is the **first non-comment line** after any `// `comments at the very top of the file (constitution: `BE.DAL.missing-server-only` / Critical).
2. No return type is `Promise<any>` or untyped — every method has an explicit return type annotation.
3. No raw SQL string interpolation in the stubs (parameterized only — constitution: `SEC.SQL.injection` / Critical).
4. The `to<EntityName>DTO` mapper is present (constitution: `BE.ACTION.dto-missing` — DAL callers should receive DTOs, not raw rows).

## Post-Execution Hooks

Check `.specify/extensions.yml` for `hooks.after_scaffold`. Apply standard hook-processing.
