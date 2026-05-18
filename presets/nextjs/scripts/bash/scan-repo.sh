#!/usr/bin/env bash
# scan-repo.sh — scan a Next.js / TypeScript web app repository and emit a
# structured inventory used by /speckit.constitution.scan to draft a
# properly-structured constitution.
#
# Outputs JSON by default; pass --text for a human-readable summary.

set -e

JSON_MODE=true
REPO_ROOT_ARG=""
SCAN_MD_HEAD_BYTES="${SPECKIT_SCAN_MD_HEAD_BYTES:-4096}"
MAX_MD_FILES="${SPECKIT_SCAN_MAX_MD_FILES:-200}"

print_help() {
    cat <<EOF
Usage: $0 [--root <path>] [--text] [--json] [--help]

Scans a repository for evidence relevant to a Next.js web application
constitution: Markdown files, package.json, tsconfig.json, Next.js
config, App Router / Route Handlers, "use client" / "use server" usage,
testing setup, linting, CI workflows, and environment files.

Options:
  --root <path>    Root directory to scan (default: auto-detect via
                   .specify, git, or current working directory)
  --json           Emit JSON output (default)
  --text           Emit a human-readable summary instead of JSON
  --help, -h       Show this help and exit

Environment:
  SPECKIT_SCAN_MD_HEAD_BYTES   Bytes of head sampled per .md file (default 4096)
  SPECKIT_SCAN_MAX_MD_FILES    Cap on .md files listed (default 200)
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --root)
            REPO_ROOT_ARG="$2"; shift 2 ;;
        --json)
            JSON_MODE=true; shift ;;
        --text)
            JSON_MODE=false; shift ;;
        -h|--help)
            print_help; exit 0 ;;
        *)
            echo "Unknown argument: $1" >&2; print_help >&2; exit 2 ;;
    esac
done

# ---------- Resolve repo root --------------------------------------------------

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -n "$REPO_ROOT_ARG" ]; then
    REPO_ROOT="$(CDPATH="" cd "$REPO_ROOT_ARG" 2>/dev/null && pwd)" || {
        echo "Error: --root path does not exist: $REPO_ROOT_ARG" >&2
        exit 1
    }
elif [ -f "$SCRIPT_DIR/../../../../scripts/bash/common.sh" ]; then
    # Installed under .specify/presets/nextjs/scripts/bash/
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/../../../../scripts/bash/common.sh"
    REPO_ROOT="$(get_repo_root)"
elif command -v git >/dev/null 2>&1 && git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT="$(git rev-parse --show-toplevel)"
else
    REPO_ROOT="$(pwd)"
fi

cd "$REPO_ROOT"

# ---------- Helpers ------------------------------------------------------------

has_cmd() { command -v "$1" >/dev/null 2>&1; }

# JSON string escape (fallback when jq is unavailable)
json_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\t'/\\t}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\b'/\\b}"
    s="${s//$'\f'/\\f}"
    local LC_ALL=C i char code
    local out=""
    for (( i=0; i<${#s}; i++ )); do
        char="${s:$i:1}"
        printf -v code '%d' "'$char" 2>/dev/null || code=256
        if (( code >= 1 && code <= 31 )); then
            out+="$(printf '\\u%04x' "$code")"
        else
            out+="$char"
        fi
    done
    printf '%s' "$out"
}

# Common find prune pattern for noise directories
find_prune() {
    find "$1" \
        \( -type d \( \
            -name node_modules -o \
            -name .git -o \
            -name .next -o \
            -name .turbo -o \
            -name .vercel -o \
            -name dist -o \
            -name build -o \
            -name out -o \
            -name coverage -o \
            -name .cache -o \
            -name .specify -o \
            -name .yarn -o \
            -name .pnpm-store \
            \) -prune \) -o \
        "${@:2}" -print 2>/dev/null
}

file_exists_first() {
    # Return first existing file from the argument list, empty if none
    local f
    for f in "$@"; do
        [ -f "$f" ] && { printf '%s' "$f"; return 0; }
    done
    return 1
}

# ---------- Inventory: package.json -------------------------------------------

PKG_JSON_PATH=""
PKG_JSON_INVENTORY='{}'

if [ -f "package.json" ]; then
    PKG_JSON_PATH="package.json"
    if has_cmd python3; then
        PKG_JSON_INVENTORY="$(SPECKIT_PKG="$PKG_JSON_PATH" python3 <<'PY'
import json, os, sys
path = os.environ["SPECKIT_PKG"]
try:
    with open(path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
except Exception as e:
    print(json.dumps({"error": f"failed to parse package.json: {e}"}))
    sys.exit(0)

def names(d):
    if not isinstance(d, dict):
        return []
    return sorted(d.keys())

deps = pkg.get("dependencies") or {}
devdeps = pkg.get("devDependencies") or {}
peerdeps = pkg.get("peerDependencies") or {}
all_deps = {}
all_deps.update(deps)
all_deps.update(devdeps)
all_deps.update(peerdeps)

def has(name): return name in all_deps

signals = {
    "has_next":          has("next"),
    "has_react":         has("react"),
    "has_typescript":    has("typescript"),
    "has_eslint":        has("eslint"),
    "has_prettier":      has("prettier"),
    "has_biome":         has("@biomejs/biome"),
    "has_vitest":        has("vitest"),
    "has_jest":          has("jest"),
    "has_playwright":    any(k.startswith("@playwright/") or k == "playwright" for k in all_deps),
    "has_cypress":       has("cypress"),
    "has_testing_library_react": has("@testing-library/react"),
    "has_zod":           has("zod"),
    "has_valibot":       has("valibot"),
    "has_yup":           has("yup"),
    "has_prisma":        has("prisma") or has("@prisma/client"),
    "has_drizzle":       has("drizzle-orm"),
    "has_kysely":        has("kysely"),
    "has_authjs":        any(k.startswith("next-auth") or k.startswith("@auth/") for k in all_deps),
    "has_clerk":         any(k.startswith("@clerk/") for k in all_deps),
    "has_lucia":         has("lucia"),
    "has_tailwind":      has("tailwindcss"),
    "has_helmet_headers": has("next-secure-headers"),
    "has_rate_limit":    has("@upstash/ratelimit") or has("express-rate-limit"),
    "has_argon2":        has("argon2") or has("@node-rs/argon2"),
    "has_bcrypt":        has("bcrypt") or has("bcryptjs"),
    "has_winston":       has("winston"),
    "has_pino":          has("pino"),
    "has_otel":          any(k.startswith("@opentelemetry/") for k in all_deps),
    "has_sentry":        any(k.startswith("@sentry/") for k in all_deps),
    "has_husky":         has("husky"),
    "has_lint_staged":   has("lint-staged"),
}

result = {
    "name":            pkg.get("name"),
    "version":         pkg.get("version"),
    "private":         pkg.get("private", False),
    "type":            pkg.get("type"),
    "engines":         pkg.get("engines"),
    "package_manager": pkg.get("packageManager"),
    "scripts":         names(pkg.get("scripts")),
    "dep_count":       len(deps),
    "devdep_count":    len(devdeps),
    "peer_count":      len(peerdeps),
    "next_version":    deps.get("next") or devdeps.get("next"),
    "react_version":   deps.get("react") or devdeps.get("react"),
    "ts_version":      deps.get("typescript") or devdeps.get("typescript"),
    "node_engine":     (pkg.get("engines") or {}).get("node"),
    "signals":         signals,
}
print(json.dumps(result))
PY
)"
    elif has_cmd jq; then
        PKG_JSON_INVENTORY="$(jq -c '{
            name, version, private: (.private // false), type, engines,
            package_manager: .packageManager,
            scripts: ((.scripts // {}) | keys),
            dep_count:    ((.dependencies // {})    | length),
            devdep_count: ((.devDependencies // {}) | length),
            peer_count:   ((.peerDependencies // {}) | length),
            next_version: ((.dependencies.next) // (.devDependencies.next)),
            react_version:((.dependencies.react) // (.devDependencies.react)),
            ts_version:   ((.dependencies.typescript) // (.devDependencies.typescript)),
            node_engine:  ((.engines // {}).node),
            signals: {
                has_next:       (((.dependencies // {}) + (.devDependencies // {})) | has("next")),
                has_react:      (((.dependencies // {}) + (.devDependencies // {})) | has("react")),
                has_typescript: (((.dependencies // {}) + (.devDependencies // {})) | has("typescript"))
            }
        }' package.json 2>/dev/null || echo '{"error":"jq parse failed"}')"
    else
        PKG_JSON_INVENTORY='{"error":"no python3 or jq available to parse package.json"}'
    fi
fi

# ---------- Inventory: tsconfig.json ------------------------------------------

TSCONFIG_INVENTORY='{}'
TSCONFIG_PATH="$(file_exists_first tsconfig.json tsconfig.base.json || true)"
if [ -n "$TSCONFIG_PATH" ] && has_cmd python3; then
    TSCONFIG_INVENTORY="$(SPECKIT_TSC="$TSCONFIG_PATH" python3 <<'PY'
import json, os, re, sys
path = os.environ["SPECKIT_TSC"]
try:
    raw = open(path, "r", encoding="utf-8").read()
except Exception as e:
    print(json.dumps({"error": str(e)})); sys.exit(0)

# Strip // line and /* block */ comments to tolerate tsconfig JSON-with-comments
raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)
raw = re.sub(r"^\s*//.*$", "", raw, flags=re.M)
# Strip trailing commas
raw = re.sub(r",(\s*[}\]])", r"\1", raw)

try:
    cfg = json.loads(raw)
except Exception as e:
    print(json.dumps({"error": f"parse failed: {e}", "path": path})); sys.exit(0)

co = cfg.get("compilerOptions") or {}
result = {
    "path": path,
    "extends": cfg.get("extends"),
    "strict":                       co.get("strict"),
    "noUncheckedIndexedAccess":     co.get("noUncheckedIndexedAccess"),
    "noImplicitOverride":           co.get("noImplicitOverride"),
    "exactOptionalPropertyTypes":   co.get("exactOptionalPropertyTypes"),
    "noImplicitAny":                co.get("noImplicitAny"),
    "noUnusedLocals":               co.get("noUnusedLocals"),
    "noUnusedParameters":           co.get("noUnusedParameters"),
    "target":                       co.get("target"),
    "module":                       co.get("module"),
    "moduleResolution":             co.get("moduleResolution"),
    "jsx":                          co.get("jsx"),
    "paths_count":                  len(co.get("paths") or {}),
}
print(json.dumps(result))
PY
)"
elif [ -n "$TSCONFIG_PATH" ]; then
    TSCONFIG_INVENTORY="{\"path\":\"$(json_escape "$TSCONFIG_PATH")\",\"warning\":\"python3 unavailable; tsconfig not parsed\"}"
fi

# ---------- Inventory: Next.js & structure ------------------------------------

NEXT_CONFIG_FILE="$(file_exists_first next.config.ts next.config.mjs next.config.js next.config.cjs || true)"
HAS_APP_DIR="false";   [ -d "app" ] || [ -d "src/app" ] && HAS_APP_DIR="true"
HAS_PAGES_DIR="false"; [ -d "pages" ] || [ -d "src/pages" ] && HAS_PAGES_DIR="true"
HAS_MIDDLEWARE="false"
file_exists_first middleware.ts middleware.js src/middleware.ts src/middleware.js >/dev/null 2>&1 && HAS_MIDDLEWARE="true"

# Count Route Handlers (route.ts / route.js) under app/
ROUTE_HANDLER_COUNT=0
if [ "$HAS_APP_DIR" = "true" ]; then
    ROUTE_HANDLER_COUNT="$(find_prune . -type f \( -name 'route.ts' -o -name 'route.tsx' -o -name 'route.js' \) | wc -l | tr -d ' ')"
fi

# Count files with "use client" / "use server" directives
USE_CLIENT_COUNT=0
USE_SERVER_COUNT=0
if has_cmd grep; then
    USE_CLIENT_COUNT="$(grep -rl --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' \
        --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.next --exclude-dir=dist \
        --exclude-dir=build --exclude-dir=out --exclude-dir=coverage --exclude-dir=.turbo \
        --exclude-dir=.specify --exclude-dir=.vercel \
        -E "^['\"]use client['\"]" . 2>/dev/null | wc -l | tr -d ' ')"
    USE_SERVER_COUNT="$(grep -rl --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' \
        --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.next --exclude-dir=dist \
        --exclude-dir=build --exclude-dir=out --exclude-dir=coverage --exclude-dir=.turbo \
        --exclude-dir=.specify --exclude-dir=.vercel \
        -E "^['\"]use server['\"]" . 2>/dev/null | wc -l | tr -d ' ')"
fi

# Look for a Data Access Layer convention
HAS_DAL="false"
for d in lib/dal src/lib/dal server/dal src/server/dal data/dal src/data/dal; do
    [ -d "$d" ] && HAS_DAL="true" && break
done

# `server-only` / `client-only` imports
SERVER_ONLY_HITS=0
CLIENT_ONLY_HITS=0
if has_cmd grep; then
    # Match both side-effect-only (`import 'server-only'`) and named
    # (`import x from 'server-only'`) forms.
    SERVER_ONLY_HITS="$(grep -rlE \
        --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' \
        --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.next \
        --exclude-dir=dist --exclude-dir=build --exclude-dir=out \
        --exclude-dir=coverage --exclude-dir=.turbo --exclude-dir=.specify \
        --exclude-dir=.vercel \
        "(^|[[:space:]])import[[:space:]]+(.*[[:space:]]+from[[:space:]]+)?['\"]server-only['\"]" \
        . 2>/dev/null | wc -l | tr -d ' ')"
    CLIENT_ONLY_HITS="$(grep -rlE \
        --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' \
        --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.next \
        --exclude-dir=dist --exclude-dir=build --exclude-dir=out \
        --exclude-dir=coverage --exclude-dir=.turbo --exclude-dir=.specify \
        --exclude-dir=.vercel \
        "(^|[[:space:]])import[[:space:]]+(.*[[:space:]]+from[[:space:]]+)?['\"]client-only['\"]" \
        . 2>/dev/null | wc -l | tr -d ' ')"
fi

# ---------- Inventory: tooling ------------------------------------------------

HAS_ESLINT="false"
file_exists_first .eslintrc .eslintrc.json .eslintrc.js .eslintrc.cjs eslint.config.js eslint.config.mjs eslint.config.cjs eslint.config.ts >/dev/null 2>&1 && HAS_ESLINT="true"

HAS_PRETTIER="false"
file_exists_first .prettierrc .prettierrc.json .prettierrc.js .prettierrc.cjs prettier.config.js prettier.config.cjs prettier.config.mjs .prettierrc.yaml .prettierrc.yml >/dev/null 2>&1 && HAS_PRETTIER="true"

HAS_BIOME="false"
file_exists_first biome.json biome.jsonc >/dev/null 2>&1 && HAS_BIOME="true"

HAS_EDITORCONFIG="false"; [ -f ".editorconfig" ] && HAS_EDITORCONFIG="true"

HAS_HUSKY="false"; [ -d ".husky" ] && HAS_HUSKY="true"

# CI workflows
CI_WORKFLOWS=""
if [ -d ".github/workflows" ]; then
    CI_WORKFLOWS="$(find .github/workflows -maxdepth 1 -type f \( -name '*.yml' -o -name '*.yaml' \) 2>/dev/null | sort)"
fi

# Env files (presence only — never read contents)
ENV_FILES=""
for f in .env.example .env.sample .env.template .env.local.example; do
    [ -f "$f" ] && ENV_FILES="$ENV_FILES $f"
done
ENV_FILES="$(printf '%s' "$ENV_FILES" | sed -E 's/^ +//')"

# Runtime version files
NODE_VERSION_FILE=""
NODE_VERSION_VALUE=""
if [ -f ".nvmrc" ]; then
    NODE_VERSION_FILE=".nvmrc"
    NODE_VERSION_VALUE="$(head -n1 .nvmrc 2>/dev/null | tr -d '[:space:]')"
elif [ -f ".node-version" ]; then
    NODE_VERSION_FILE=".node-version"
    NODE_VERSION_VALUE="$(head -n1 .node-version 2>/dev/null | tr -d '[:space:]')"
elif [ -f ".tool-versions" ]; then
    NODE_VERSION_FILE=".tool-versions"
    NODE_VERSION_VALUE="$(grep -E '^node ' .tool-versions 2>/dev/null | awk '{print $2}' | head -n1)"
fi

# Test directories
HAS_TESTS_DIR="false"
for d in __tests__ tests test e2e; do
    if find_prune . -type d -name "$d" 2>/dev/null | grep -q .; then
        HAS_TESTS_DIR="true"; break
    fi
done

# Git
HAS_GIT="false"
GIT_REMOTE_URL=""
GIT_DEFAULT_BRANCH=""
if has_cmd git && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    HAS_GIT="true"
    GIT_REMOTE_URL="$(git remote get-url origin 2>/dev/null || echo "")"
    GIT_DEFAULT_BRANCH="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@' || echo "")"
fi

# Existing constitution
HAS_CONSTITUTION="false"
[ -f ".specify/memory/constitution.md" ] && HAS_CONSTITUTION="true"

# ---------- Inventory: Markdown files -----------------------------------------

# Build a sorted list of .md files (excluding noise directories and node_modules)
MD_FILES_LIST="$(find_prune . -type f \( -name '*.md' -o -name '*.mdx' \) 2>/dev/null | sed 's|^\./||' | sort)"
MD_FILES_TOTAL=0
[ -n "$MD_FILES_LIST" ] && MD_FILES_TOTAL="$(printf '%s\n' "$MD_FILES_LIST" | wc -l | tr -d ' ')"

# Pick well-known docs we want to surface explicitly
KNOWN_DOCS=""
for f in README.md README.MD ARCHITECTURE.md CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md \
         CHANGELOG.md AGENTS.md CLAUDE.md GEMINI.md .github/copilot-instructions.md; do
    [ -f "$f" ] && KNOWN_DOCS="$KNOWN_DOCS $f"
done
KNOWN_DOCS="$(printf '%s' "$KNOWN_DOCS" | sed -E 's/^ +//')"

# ---------- Emit output -------------------------------------------------------

if [ "$JSON_MODE" = true ]; then
    # Build JSON via python3 (preferred) so escaping of headings/paths is correct.
    if has_cmd python3; then
        SPECKIT_REPO_ROOT="$REPO_ROOT" \
        SPECKIT_PKG_INV="$PKG_JSON_INVENTORY" \
        SPECKIT_TSC_INV="$TSCONFIG_INVENTORY" \
        SPECKIT_NEXT_CFG="$NEXT_CONFIG_FILE" \
        SPECKIT_HAS_APP="$HAS_APP_DIR" \
        SPECKIT_HAS_PAGES="$HAS_PAGES_DIR" \
        SPECKIT_HAS_MIDDLEWARE="$HAS_MIDDLEWARE" \
        SPECKIT_ROUTE_COUNT="$ROUTE_HANDLER_COUNT" \
        SPECKIT_USE_CLIENT="$USE_CLIENT_COUNT" \
        SPECKIT_USE_SERVER="$USE_SERVER_COUNT" \
        SPECKIT_HAS_DAL="$HAS_DAL" \
        SPECKIT_SERVER_ONLY="$SERVER_ONLY_HITS" \
        SPECKIT_CLIENT_ONLY="$CLIENT_ONLY_HITS" \
        SPECKIT_HAS_ESLINT="$HAS_ESLINT" \
        SPECKIT_HAS_PRETTIER="$HAS_PRETTIER" \
        SPECKIT_HAS_BIOME="$HAS_BIOME" \
        SPECKIT_HAS_EDITORCONFIG="$HAS_EDITORCONFIG" \
        SPECKIT_HAS_HUSKY="$HAS_HUSKY" \
        SPECKIT_CI_WORKFLOWS="$CI_WORKFLOWS" \
        SPECKIT_ENV_FILES="$ENV_FILES" \
        SPECKIT_NODE_VER_FILE="$NODE_VERSION_FILE" \
        SPECKIT_NODE_VER_VALUE="$NODE_VERSION_VALUE" \
        SPECKIT_HAS_TESTS_DIR="$HAS_TESTS_DIR" \
        SPECKIT_HAS_GIT="$HAS_GIT" \
        SPECKIT_GIT_REMOTE="$GIT_REMOTE_URL" \
        SPECKIT_GIT_DEFAULT_BRANCH="$GIT_DEFAULT_BRANCH" \
        SPECKIT_HAS_CONSTITUTION="$HAS_CONSTITUTION" \
        SPECKIT_MD_FILES="$MD_FILES_LIST" \
        SPECKIT_MD_TOTAL="$MD_FILES_TOTAL" \
        SPECKIT_KNOWN_DOCS="$KNOWN_DOCS" \
        SPECKIT_MD_HEAD_BYTES="$SCAN_MD_HEAD_BYTES" \
        SPECKIT_MD_MAX="$MAX_MD_FILES" \
        python3 <<'PY'
import json, os, re

def env(name, default=""):
    return os.environ.get(name, default)

def as_bool(s): return s == "true"
def as_int(s):
    try: return int(s)
    except: return 0
def split_ws(s):
    return [x for x in (s or "").split() if x]
def parse_json_or(s, fallback=None):
    if not s: return fallback if fallback is not None else {}
    try: return json.loads(s)
    except Exception: return {"error": "embedded JSON invalid", "raw_len": len(s)}

repo_root = env("SPECKIT_REPO_ROOT")
md_head_bytes = max(0, as_int(env("SPECKIT_MD_HEAD_BYTES", "4096")))
md_max = max(1, as_int(env("SPECKIT_MD_MAX", "200")))

md_files = [p for p in (env("SPECKIT_MD_FILES") or "").splitlines() if p.strip()]
md_total = as_int(env("SPECKIT_MD_TOTAL"))

def file_summary(rel_path):
    """Return path, size, mtime, and first-N-bytes-derived heading sample."""
    full = os.path.join(repo_root, rel_path)
    info = {"path": rel_path}
    try:
        st = os.stat(full)
        info["size"] = st.st_size
    except Exception:
        info["error"] = "stat failed"
        return info
    try:
        with open(full, "rb") as f:
            head = f.read(md_head_bytes)
        try:
            text = head.decode("utf-8", errors="replace")
        except Exception:
            text = ""
        headings = []
        for line in text.splitlines():
            m = re.match(r"^(#{1,6})\s+(.*\S)\s*$", line)
            if m:
                headings.append({"level": len(m.group(1)), "text": m.group(2)[:200]})
            if len(headings) >= 25:
                break
        info["headings"] = headings
        # First paragraph (non-heading, non-empty) excerpt
        excerpt = ""
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("<!--"):
                continue
            excerpt = s[:300]; break
        info["excerpt"] = excerpt
    except Exception as e:
        info["error"] = f"read failed: {e}"
    return info

md_summaries = [file_summary(p) for p in md_files[:md_max]]
md_truncated = md_total > md_max

result = {
    "schema_version": "1.0",
    "repo_root": repo_root,
    "package_json":   parse_json_or(env("SPECKIT_PKG_INV"), fallback={"present": False}),
    "tsconfig":       parse_json_or(env("SPECKIT_TSC_INV"), fallback={"present": False}),
    "nextjs": {
        "config_file":          env("SPECKIT_NEXT_CFG") or None,
        "has_app_dir":          as_bool(env("SPECKIT_HAS_APP")),
        "has_pages_dir":        as_bool(env("SPECKIT_HAS_PAGES")),
        "has_middleware":       as_bool(env("SPECKIT_HAS_MIDDLEWARE")),
        "route_handler_count":  as_int(env("SPECKIT_ROUTE_COUNT")),
    },
    "directives": {
        "use_client_files":  as_int(env("SPECKIT_USE_CLIENT")),
        "use_server_files":  as_int(env("SPECKIT_USE_SERVER")),
        "server_only_imports": as_int(env("SPECKIT_SERVER_ONLY")),
        "client_only_imports": as_int(env("SPECKIT_CLIENT_ONLY")),
    },
    "data_access": {
        "has_dal_directory": as_bool(env("SPECKIT_HAS_DAL")),
    },
    "tooling": {
        "eslint":        as_bool(env("SPECKIT_HAS_ESLINT")),
        "prettier":      as_bool(env("SPECKIT_HAS_PRETTIER")),
        "biome":         as_bool(env("SPECKIT_HAS_BIOME")),
        "editorconfig":  as_bool(env("SPECKIT_HAS_EDITORCONFIG")),
        "husky":         as_bool(env("SPECKIT_HAS_HUSKY")),
        "ci_workflows":  split_ws(env("SPECKIT_CI_WORKFLOWS").replace("\n", " ")),
    },
    "environment": {
        "env_example_files":  split_ws(env("SPECKIT_ENV_FILES")),
        "node_version_file":  env("SPECKIT_NODE_VER_FILE") or None,
        "node_version":       env("SPECKIT_NODE_VER_VALUE") or None,
    },
    "testing": {
        "has_tests_directory": as_bool(env("SPECKIT_HAS_TESTS_DIR")),
    },
    "git": {
        "is_repo":         as_bool(env("SPECKIT_HAS_GIT")),
        "origin_url":      env("SPECKIT_GIT_REMOTE") or None,
        "default_branch":  env("SPECKIT_GIT_DEFAULT_BRANCH") or None,
    },
    "constitution": {
        "exists": as_bool(env("SPECKIT_HAS_CONSTITUTION")),
        "path":   ".specify/memory/constitution.md",
    },
    "markdown": {
        "total":           md_total,
        "listed":          len(md_summaries),
        "truncated":       md_truncated,
        "known_docs":      split_ws(env("SPECKIT_KNOWN_DOCS")),
        "files":           md_summaries,
    },
}
print(json.dumps(result, indent=2))
PY
    else
        # Minimal JSON fallback (no python3): emit a stub the LLM can still read.
        printf '{\n'
        printf '  "schema_version": "1.0",\n'
        printf '  "warning": "python3 unavailable; emitting limited fallback inventory",\n'
        printf '  "repo_root": "%s",\n' "$(json_escape "$REPO_ROOT")"
        printf '  "package_json_present": %s,\n' "$([ -n "$PKG_JSON_PATH" ] && echo true || echo false)"
        printf '  "tsconfig_present": %s,\n' "$([ -n "$TSCONFIG_PATH" ] && echo true || echo false)"
        printf '  "next_config_file": "%s",\n' "$(json_escape "$NEXT_CONFIG_FILE")"
        printf '  "has_app_dir": %s,\n' "$HAS_APP_DIR"
        printf '  "has_pages_dir": %s,\n' "$HAS_PAGES_DIR"
        printf '  "markdown_total": %s\n' "$MD_FILES_TOTAL"
        printf '}\n'
    fi
else
    # Human-readable summary
    echo "Repo root:           $REPO_ROOT"
    echo "package.json:        $([ -n "$PKG_JSON_PATH" ] && echo present || echo absent)"
    echo "tsconfig.json:       $([ -n "$TSCONFIG_PATH" ] && echo present || echo absent)"
    echo "next.config:         ${NEXT_CONFIG_FILE:-absent}"
    echo "App Router (app/):   $HAS_APP_DIR"
    echo "Pages Router:        $HAS_PAGES_DIR"
    echo "middleware:          $HAS_MIDDLEWARE"
    echo "route handlers:      $ROUTE_HANDLER_COUNT"
    echo "use client files:    $USE_CLIENT_COUNT"
    echo "use server files:    $USE_SERVER_COUNT"
    echo "server-only imports: $SERVER_ONLY_HITS"
    echo "client-only imports: $CLIENT_ONLY_HITS"
    echo "DAL directory:       $HAS_DAL"
    echo "ESLint:              $HAS_ESLINT"
    echo "Prettier:            $HAS_PRETTIER"
    echo "Biome:               $HAS_BIOME"
    echo "Husky:                $HAS_HUSKY"
    echo "CI workflows:        $(printf '%s' "$CI_WORKFLOWS" | tr '\n' ' ')"
    echo "Env example files:   $ENV_FILES"
    echo "Node version:        ${NODE_VERSION_VALUE:-unknown} (from ${NODE_VERSION_FILE:-no file})"
    echo "Tests directory:     $HAS_TESTS_DIR"
    echo "Git repository:      $HAS_GIT"
    echo "Constitution file:   $HAS_CONSTITUTION"
    echo "Markdown files:      $MD_FILES_TOTAL"
    if [ -n "$KNOWN_DOCS" ]; then
        echo "Known docs:"
        for f in $KNOWN_DOCS; do echo "  - $f"; done
    fi
fi
