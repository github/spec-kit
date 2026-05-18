# scan-repo inventory schema

`scan-repo.sh` and `scan-repo.ps1` emit a JSON document with this top-level
shape. The `schema_version` is bumped when fields are renamed or removed;
additive fields do not bump the version.

```jsonc
{
  "schema_version": "1.0",
  "repo_root": "/abs/path/to/repo",

  "package_json": {
    "present": true,
    "name": "...", "version": "...", "private": false, "type": "module|commonjs|null",
    "engines": { "node": "..." }, "package_manager": "...",
    "scripts": ["...", "..."],
    "dep_count": 0, "devdep_count": 0, "peer_count": 0,
    "next_version": "...", "react_version": "...", "ts_version": "...",
    "node_engine": "...",
    "signals": {
      "has_next": true, "has_react": true, "has_typescript": true,
      "has_eslint": true, "has_prettier": false, "has_biome": false,
      "has_vitest": false, "has_jest": false, "has_playwright": false, "has_cypress": false,
      "has_testing_library_react": false,
      "has_zod": false, "has_valibot": false, "has_yup": false,
      "has_prisma": false, "has_drizzle": false, "has_kysely": false,
      "has_authjs": false, "has_clerk": false, "has_lucia": false,
      "has_tailwind": false,
      "has_rate_limit": false,
      "has_argon2": false, "has_bcrypt": false,
      "has_pino": false, "has_winston": false,
      "has_otel": false, "has_sentry": false,
      "has_husky": false, "has_lint_staged": false
    }
  },

  "tsconfig": {
    "present": true,
    "path": "tsconfig.json",
    "extends": "...",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitAny": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "preserve",
    "paths_count": 3
  },

  "nextjs": {
    "config_file": "next.config.mjs",
    "has_app_dir": true,
    "has_pages_dir": false,
    "has_middleware": false,
    "route_handler_count": 4
  },

  "directives": {
    "use_client_files": 12,
    "use_server_files": 3,
    "server_only_imports": 2,
    "client_only_imports": 0
  },

  "data_access": { "has_dal_directory": false },

  "tooling": {
    "eslint": true, "prettier": true, "biome": false,
    "editorconfig": true, "husky": false,
    "ci_workflows": [".github/workflows/ci.yml"]
  },

  "environment": {
    "env_example_files": [".env.example"],
    "node_version_file": ".nvmrc",
    "node_version": "20"
  },

  "testing": { "has_tests_directory": true },

  "git": {
    "is_repo": true,
    "origin_url": "...",
    "default_branch": "main"
  },

  "constitution": { "exists": false, "path": ".specify/memory/constitution.md" },

  "markdown": {
    "total": 42,
    "listed": 42,
    "truncated": false,
    "known_docs": ["README.md", "CONTRIBUTING.md"],
    "files": [
      {
        "path": "README.md",
        "size": 1234,
        "headings": [{ "level": 1, "text": "Project" }, { "level": 2, "text": "Setup" }],
        "excerpt": "A short application that ..."
      }
    ]
  }
}
```

## Field semantics

- `signals.has_*` flags are **evidence**, not principle requirements. The
  constitution stays behavioral; signals only inform the Sync Impact Report.
- `directives.use_client_files` counts files whose first non-whitespace line
  matches `'use client'` (or `"use client"`). Same for `use_server_files`.
- `data_access.has_dal_directory` checks `lib/dal`, `src/lib/dal`,
  `server/dal`, `src/server/dal`, `data/dal`, `src/data/dal`.
- `markdown.files` are sampled from the first
  `SPECKIT_SCAN_MD_HEAD_BYTES` bytes (default 4096) for headings and an
  excerpt. The full file is **not** loaded by the scan; the calling command
  should `Read` files it needs in full.
- `markdown.truncated` is `true` when `total > SPECKIT_SCAN_MAX_MD_FILES`
  (default 200). The `files` array is capped at that count.

## Stability

`schema_version: "1.0"` covers the current top-level layout. The script
and the `/speckit.constitution.scan` command are versioned together; if a
field is renamed or removed, the schema version bumps and the command is
updated in lockstep.

---

# audit-codebase inventory schema

`audit-codebase.sh` and `audit-codebase.ps1` emit a JSON document with
this top-level shape. Companion commands: `/speckit.audit` and
`/speckit.audit.deep`.

```jsonc
{
  "schema_version": "1.0",
  "command": "audit",
  "scanned_at": "2026-05-18T07:42:00Z",
  "repo_root": "/abs/path/to/repo",

  "scope": {
    "files_scanned":  123,
    "paths_included": ["app", "src"],
    "extensions":     [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"],
    "min_severity":   "low",
    "max_per_rule":   50
  },

  "summary": {
    "rules_evaluated":     23,
    "rules_with_findings": 8,
    "findings_total":      27,
    "by_severity":         { "critical": 13, "high": 10, "medium": 4, "low": 0 },
    "by_section":          { "TypeScript": 12, "Frontend": 6, "Security": 5, "Backend": 2, "Performance": 1, "Infrastructure": 1 },
    "by_rule":             { "TS.TYPE.any-usage": 1, "BE.DAL.missing-server-only": 1, "...": 0 }
  },

  "rules": [
    {
      "id":          "TS.TYPE.any-usage",
      "severity":    "critical",
      "section":     "TypeScript / Type System Discipline",
      "phase":       "P1",
      "scope":       "Both",
      "directive":   "Ban any; use unknown for untrusted data and narrow before use",
      "remediation": "Replace 'any' with 'unknown' and narrow at the use site, or define a precise type."
    }
  ],

  "findings": [
    {
      "rule_id":     "TS.TYPE.any-usage",
      "severity":    "critical",
      "section":     "TypeScript / Type System Discipline",
      "phase":       "P1",
      "scope":       "Both",
      "directive":   "Ban any; ...",
      "remediation": "Replace 'any' with 'unknown' ...",
      "file":        "src/lib/foo.ts",
      "line":        42,
      "snippet":     "function bar(x: any) {"
    }
  ]
}
```

## Rule ID convention

`<SECTION>.<AREA>.<slug>` where `SECTION` is one of:

| Prefix  | Maps to constitution section                         |
|---------|------------------------------------------------------|
| `TS.`   | TypeScript Engineering Behaviors                     |
| `FE.`   | Frontend Behaviors                                   |
| `BE.`   | Backend Behaviors                                    |
| `SEC.`  | Security Behaviors                                   |
| `PERF.` | Performance Behaviors                                |
| `INFRA.`| Infrastructure & Operations Behaviors                |

`AREA` is a short subsection slug (`COMPILER`, `TYPE`, `RSC`, `IMG`, `DAL`,
`ENV`, `SESSION`, `SECRET`, `SQL`, `XSS`, `LOG`, `CI`, …). The full
catalog is printable with `--list-rules` (bash) or `-ListRules`
(PowerShell).

## Severity → constitution criticality

| Severity   | Constitution criticality | Release impact                                                                 |
|------------|--------------------------|--------------------------------------------------------------------------------|
| `critical` | Critical                 | Blocks release. No exception without a recorded waiver and a fixed expiry.     |
| `high`     | High                     | Requires an explicit, time-bound exception approved at review.                 |
| `medium`   | Medium                   | Default expectation; deviations are noted and tracked.                         |
| `low`      | Low                      | Recommended; revisit during regular audits.                                    |

## Performance for big codebases

- Single file-enumeration pass; rules grep over the cached list.
- Parallel grep via `xargs -P` (POSIX) or per-file `Select-String` (PS).
- `--paths` / `-Paths` to narrow scope to specific directories.
- `--rules` / `-Rules` and `--sections` / `-Sections` to run a subset.
- `--max-findings-per-rule` / `-MaxFindingsPerRule` to keep reports bounded.
- `--severity` / `-Severity` to raise the floor.

## Stability

`schema_version: "1.0"` covers the audit document layout. If a field is
renamed or removed, the schema version bumps in lockstep with the
`/speckit.audit*` commands.
