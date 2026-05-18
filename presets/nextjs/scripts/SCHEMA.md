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
