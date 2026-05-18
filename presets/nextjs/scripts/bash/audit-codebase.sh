#!/usr/bin/env bash
# audit-codebase.sh — audit a TypeScript / Next.js codebase against the
# behavioral directives in the project constitution. Emits a structured
# JSON report of findings with file:line locations, rule metadata, and
# remediation hints.
#
# Companion command: /speckit.audit (and /speckit.audit.deep, which runs
# this script *plus* extra techniques: tsc --noEmit, eslint, npm audit,
# and LLM cross-file analysis).
#
# Designed for big codebases:
#   - Source files enumerated once into a cached list.
#   - Rule scanners use `xargs -P` for parallel grep.
#   - `--max-findings-per-rule` and `--paths` keep output bounded.

set -e
# Intentionally NOT setting `pipefail`: many scan pipelines run grep through
# xargs and grep returns 1 when a file has no match. With pipefail, xargs
# reports those as 123 and the pipeline aborts. Each scan tolerates failure
# locally where it matters; missing findings are not a script error.

# ---------- Defaults ----------------------------------------------------------

JSON_MODE=true
REPO_ROOT_ARG=""
MAX_PER_RULE="${SPECKIT_AUDIT_MAX_PER_RULE:-50}"
PARALLEL="${SPECKIT_AUDIT_PARALLEL:-4}"
PATHS_ARG=""
RULES_ARG=""           # comma-separated rule IDs (subset)
SECTIONS_ARG=""        # comma-separated sections (subset)
MIN_SEVERITY="low"     # critical|high|medium|low
SNIPPET_MAX_LEN=200

print_help() {
    cat <<EOF
Usage: $0 [options]

Audits the repository against TypeScript and Next.js behavioral directives.

Options:
  --root <path>                    Repository root (default: auto-detect)
  --paths <p1,p2,...>              Limit scan to these paths (relative to root)
  --rules <id1,id2,...>            Run only these rule IDs
  --sections <S1,S2,...>           Run only these sections (TS, FE, BE, SEC, PERF, INFRA)
  --severity <critical|high|medium|low>
                                   Minimum severity to include (default: low)
  --max-findings-per-rule <N>      Cap findings per rule (default: 50)
  --parallel <N>                   xargs parallelism (default: 4)
  --text                           Emit human-readable summary instead of JSON
  --json                           Emit JSON (default)
  --list-rules                     Print rule catalog as JSON and exit
  --help, -h                       Show this help and exit

Environment:
  SPECKIT_AUDIT_MAX_PER_RULE       Default max findings per rule
  SPECKIT_AUDIT_PARALLEL           Default xargs parallelism

Rule sections:
  TS    — TypeScript Engineering (compiler + type system)
  FE    — Frontend (RSC, images, links, metadata)
  BE    — Backend (DAL, env handling)
  SEC   — Security (sessions, SQL, XSS, secrets)
  PERF  — Performance (console.log, perf hygiene)
  INFRA — Infrastructure (CI typecheck)
EOF
}

# ---------- Arg parsing -------------------------------------------------------

while [ $# -gt 0 ]; do
    case "$1" in
        --root)                    REPO_ROOT_ARG="$2"; shift 2 ;;
        --paths)                   PATHS_ARG="$2"; shift 2 ;;
        --rules)                   RULES_ARG="$2"; shift 2 ;;
        --sections)                SECTIONS_ARG="$2"; shift 2 ;;
        --severity)                MIN_SEVERITY="$2"; shift 2 ;;
        --max-findings-per-rule)   MAX_PER_RULE="$2"; shift 2 ;;
        --parallel)                PARALLEL="$2"; shift 2 ;;
        --text)                    JSON_MODE=false; shift ;;
        --json)                    JSON_MODE=true; shift ;;
        --list-rules)              LIST_RULES_ONLY=true; shift ;;
        -h|--help)                 print_help; exit 0 ;;
        *)                         echo "Unknown argument: $1" >&2; print_help >&2; exit 2 ;;
    esac
done

case "$MIN_SEVERITY" in critical|high|medium|low) ;; *)
    echo "Error: --severity must be one of critical, high, medium, low" >&2; exit 2 ;;
esac

# ---------- Resolve repo root -------------------------------------------------

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -n "$REPO_ROOT_ARG" ]; then
    REPO_ROOT="$(CDPATH="" cd "$REPO_ROOT_ARG" 2>/dev/null && pwd)" || {
        echo "Error: --root path does not exist: $REPO_ROOT_ARG" >&2; exit 1
    }
elif [ -f "$SCRIPT_DIR/../../../../scripts/bash/common.sh" ]; then
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/../../../../scripts/bash/common.sh"
    REPO_ROOT="$(get_repo_root)"
elif command -v git >/dev/null 2>&1 && git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT="$(git rev-parse --show-toplevel)"
else
    REPO_ROOT="$(pwd)"
fi
cd "$REPO_ROOT"

# ---------- Helpers -----------------------------------------------------------

has_cmd() { command -v "$1" >/dev/null 2>&1; }

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

FILES_LIST="$WORKDIR/files.txt"
FINDINGS_DIR="$WORKDIR/findings"
mkdir -p "$FINDINGS_DIR"

# Numeric severity for filtering
sev_rank() {
    case "$1" in critical) echo 4 ;; high) echo 3 ;; medium) echo 2 ;; low) echo 1 ;; *) echo 0 ;; esac
}
MIN_RANK="$(sev_rank "$MIN_SEVERITY")"

# Whether a rule should run, given --rules / --sections filters
rule_enabled() {
    local rule_id="$1" section
    section="${rule_id%%.*}"
    if [ -n "$RULES_ARG" ] && ! grep -qE "(^|,)$rule_id(,|$)" <<< "$RULES_ARG"; then
        return 1
    fi
    if [ -n "$SECTIONS_ARG" ] && ! grep -qiE "(^|,)$section(,|$)" <<< "$SECTIONS_ARG"; then
        return 1
    fi
    return 0
}

# Severity passes the filter
severity_passes() {
    local sev="$1"
    [ "$(sev_rank "$sev")" -ge "$MIN_RANK" ]
}

# Trim snippet to a single line, max length
trim_snippet() {
    local s="$1"
    # Strip leading whitespace and trailing whitespace/newline
    s="${s#"${s%%[![:space:]]*}"}"
    s="${s%"${s##*[![:space:]]}"}"
    if [ "${#s}" -gt "$SNIPPET_MAX_LEN" ]; then
        s="${s:0:$SNIPPET_MAX_LEN}..."
    fi
    printf '%s' "$s"
}

# Emit a finding as NDJSON to the rule's output file
# Args: rule_id severity file line snippet
emit_finding() {
    local rule_id="$1" sev="$2" file="$3" line="$4" snippet="$5"
    severity_passes "$sev" || return 0

    local out="$FINDINGS_DIR/$rule_id.ndjson"
    # Enforce per-rule cap
    if [ -f "$out" ] && [ "$(wc -l < "$out" | tr -d ' ')" -ge "$MAX_PER_RULE" ]; then
        return 0
    fi

    if has_cmd python3; then
        SPECKIT_RID="$rule_id" SPECKIT_SEV="$sev" SPECKIT_FILE="$file" \
        SPECKIT_LINE="$line" SPECKIT_SNIP="$snippet" \
        python3 -c "
import json, os
print(json.dumps({
    'rule_id':  os.environ['SPECKIT_RID'],
    'severity': os.environ['SPECKIT_SEV'],
    'file':     os.environ['SPECKIT_FILE'],
    'line':     int(os.environ['SPECKIT_LINE']) if os.environ['SPECKIT_LINE'].isdigit() else None,
    'snippet':  os.environ['SPECKIT_SNIP'],
}))" >> "$out"
    else
        # Hand-escaped JSON fallback
        local esc_file esc_snip
        esc_file="$(printf '%s' "$file"    | sed 's/\\/\\\\/g; s/"/\\"/g')"
        esc_snip="$(printf '%s' "$snippet" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g')"
        printf '{"rule_id":"%s","severity":"%s","file":"%s","line":%s,"snippet":"%s"}\n' \
            "$rule_id" "$sev" "$esc_file" "${line:-null}" "$esc_snip" >> "$out"
    fi
}

# ---------- Rule catalog ------------------------------------------------------
#
# Each rule: ID|severity|section|phase|scope|directive|remediation
# Phases / sections match the constitution. The catalog drives both
# evaluation and reporting; --list-rules prints it as JSON.

declare -a RULE_IDS RULE_META
register_rule() {
    RULE_IDS+=("$1")
    RULE_META+=("$2|$3|$4|$5|$6|$7")  # sev|section|phase|scope|directive|remediation
}

# -- TypeScript / Compiler & Project Config -----------------------------------
register_rule "TS.COMPILER.strict-missing"                   "critical" "TypeScript / Compiler & Project Config" "P1" "Both" "Enable strict: true from day one"                              "Set \"strict\": true in tsconfig.json compilerOptions."
register_rule "TS.COMPILER.no-unchecked-indexed-access-missing" "critical" "TypeScript / Compiler & Project Config" "P1" "Both" "Enable noUncheckedIndexedAccess"                              "Set \"noUncheckedIndexedAccess\": true in tsconfig.json."
register_rule "TS.COMPILER.exact-optional-missing"           "critical" "TypeScript / Compiler & Project Config" "P1" "Both" "Enable exactOptionalPropertyTypes"                              "Set \"exactOptionalPropertyTypes\": true to separate absent from explicitly undefined."
register_rule "TS.COMPILER.no-implicit-override-missing"     "high"     "TypeScript / Compiler & Project Config" "P1" "Both" "Enable noImplicitOverride"                                      "Set \"noImplicitOverride\": true in tsconfig.json."
register_rule "TS.COMPILER.no-fallthrough-cases-missing"     "high"     "TypeScript / Compiler & Project Config" "P1" "Both" "Enable noFallthroughCasesInSwitch"                              "Set \"noFallthroughCasesInSwitch\": true in tsconfig.json."
register_rule "TS.COMPILER.no-implicit-returns-missing"      "high"     "TypeScript / Compiler & Project Config" "P1" "Both" "Enable noImplicitReturns"                                       "Set \"noImplicitReturns\": true in tsconfig.json."
register_rule "TS.COMPILER.force-consistent-casing-missing"  "high"     "TypeScript / Compiler & Project Config" "P1" "Both" "Enable forceConsistentCasingInFileNames"                        "Set \"forceConsistentCasingInFileNames\": true to prevent case-sensitivity bugs across OSs."

# -- TypeScript / Type System -------------------------------------------------
register_rule "TS.TYPE.any-usage"                            "critical" "TypeScript / Type System Discipline" "P1" "Both" "Ban any; use unknown for untrusted data and narrow before use"  "Replace 'any' with 'unknown' and narrow at the use site, or define a precise type."
register_rule "TS.TYPE.ts-ignore"                            "critical" "TypeScript / Type System Discipline" "P2" "Both" "Ban @ts-ignore; require @ts-expect-error with a justification"  "Replace @ts-ignore with @ts-expect-error and add a comment explaining why."
register_rule "TS.TYPE.unchecked-as-cast"                    "critical" "TypeScript / Type System Discipline" "P1" "Both" "Never cast with 'as' to bypass the checker"                     "Use a type guard, satisfies, or zod/schema parsing. 'as const' and 'as unknown' are exempt."
register_rule "TS.TYPE.untyped-catch"                        "high"     "TypeScript / Type System Discipline" "P2" "Both" "Narrow errors in catch with instanceof Error or a typed union"  "Declare catch (e: unknown) and narrow via instanceof Error or a typed error union."

# -- Backend ------------------------------------------------------------------
register_rule "BE.DAL.missing-server-only"                   "critical" "Backend Patterns"   "P2" "BE" "Mark server-only modules so client imports fail the build"               "Add \"import 'server-only';\" at the top of every DAL/server module."
register_rule "BE.ENV.direct-process-env-outside-validator"  "high"     "Backend Patterns"   "P2" "BE" "Read env through a single typed module; fail boot if missing/invalid" "Centralize process.env reads in an env.ts (or lib/env.ts) module that validates with a schema."

# -- Frontend -----------------------------------------------------------------
register_rule "FE.RSC.use-client-at-page-or-layout"          "critical" "Frontend Behaviors" "P1" "FE" "Push 'use client' boundaries as deep as possible"                        "Move \"use client\" to the smallest interactive leaf; keep page.tsx and layout.tsx as Server Components."
register_rule "FE.IMG.raw-img-tag"                           "high"     "Frontend Behaviors" "P3" "FE" "Use next/image with proper sizes for non-test images"                    "Replace <img> with next/image and set sizes; mark the LCP image priority=true."
register_rule "FE.LINK.raw-anchor-internal"                  "medium"   "Frontend Behaviors" "P2" "FE" "Use <Link> for in-app navigation to benefit from prefetching"            "Replace <a href=\"/...\"> with <Link href=\"/...\"> from next/link for internal routes."
register_rule "FE.METADATA.missing-generate-metadata"        "medium"   "Frontend Behaviors" "P2" "FE" "Define generateMetadata or static metadata per route for SEO"            "Export a static \`metadata\` or \`generateMetadata\` from this page.tsx."

# -- Security ----------------------------------------------------------------
register_rule "SEC.SESSION.localstorage-auth"                "critical" "Security Behaviors" "P2" "Both" "Store sessions in httpOnly cookies, never localStorage"                  "Move session/token storage to httpOnly+Secure+SameSite cookies. localStorage is XSS-readable."
register_rule "SEC.XSS.dangerously-set"                      "high"     "Security Behaviors" "P2" "FE"   "Sanitize/encode user-generated content before rendering"                "Pass content through a sanitizer (e.g. DOMPurify) or render as text; avoid dangerouslySetInnerHTML."
register_rule "SEC.SECRET.public-env-prefix"                 "critical" "Security Behaviors" "P2" "Both" "Never put secrets behind the public env var prefix"                     "Rename NEXT_PUBLIC_*SECRET/TOKEN/KEY/PASSWORD to a server-only env var (drop the NEXT_PUBLIC_ prefix)."
register_rule "SEC.SQL.template-literal-query"               "high"     "Security Behaviors" "P2" "BE"   "Use parameterized queries everywhere; ban string-concatenated SQL"      "Use parameterized queries / query builder bindings; never interpolate user input into SQL strings."

# -- Performance --------------------------------------------------------------
register_rule "PERF.LOG.console-log-in-source"               "medium"   "Performance Behaviors" "P3" "Both" "Use structured logging; avoid console.log in production source"         "Replace console.log with a structured logger; if intentional, use console.warn/console.error explicitly."

# -- Infrastructure -----------------------------------------------------------
register_rule "INFRA.CI.missing-typecheck-job"               "high"     "Infrastructure & Operations" "P1" "Both" "CI runs typecheck on every PR; failures block merge"                   "Add a CI job that runs 'tsc --noEmit' (or 'npm run typecheck') on PRs and protected branches."

# ---------- --list-rules short-circuit ----------------------------------------

if [ "${LIST_RULES_ONLY:-false}" = true ]; then
    if has_cmd python3; then
        printf '%s\n' "${RULE_IDS[@]}" > "$WORKDIR/ids.txt"
        printf '%s\n' "${RULE_META[@]}" > "$WORKDIR/meta.txt"
        SPECKIT_W="$WORKDIR" python3 <<'PY'
import json, os
w = os.environ["SPECKIT_W"]
ids  = [l.rstrip("\n") for l in open(os.path.join(w, "ids.txt"),  encoding="utf-8")]
meta = [l.rstrip("\n") for l in open(os.path.join(w, "meta.txt"), encoding="utf-8")]
rules = []
for rid, m in zip(ids, meta):
    sev, section, phase, scope, directive, remediation = m.split("|", 5)
    rules.append({
        "id": rid, "severity": sev, "section": section, "phase": phase,
        "scope": scope, "directive": directive, "remediation": remediation,
    })
print(json.dumps({"schema_version": "1.0", "rules": rules}, indent=2))
PY
    else
        echo '{"error":"python3 unavailable; cannot render rule catalog"}'
    fi
    exit 0
fi

# ---------- File enumeration --------------------------------------------------

# Build prune-style find. PATHS_ARG narrows the search root list.
IGNORE_DIRS=(node_modules .git .next .turbo .vercel dist build out coverage .cache .specify .yarn .pnpm-store .swc)

enumerate_into() {
    local out="$1"; shift
    local roots=("$@")
    [ "${#roots[@]}" -eq 0 ] && roots=(".")

    # Build prune expression
    local prune=()
    local first=true
    for d in "${IGNORE_DIRS[@]}"; do
        if $first; then
            prune+=("(" "-type" "d" "-name" "$d"); first=false
        else
            prune+=("-o" "-type" "d" "-name" "$d")
        fi
    done
    prune+=(")")

    : > "$out"
    for root in "${roots[@]}"; do
        if [ ! -e "$root" ]; then
            echo "[audit] Warning: path '$root' does not exist; skipping" >&2
            continue
        fi
        find "$root" "${prune[@]}" -prune -o \
            -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.mjs' -o -name '*.cjs' \) -print 2>/dev/null \
            | sed 's|^\./||' >> "$out"
    done
    sort -u -o "$out" "$out"
}

if [ -n "$PATHS_ARG" ]; then
    IFS=',' read -r -a SCAN_PATHS <<< "$PATHS_ARG"
    enumerate_into "$FILES_LIST" "${SCAN_PATHS[@]}"
else
    enumerate_into "$FILES_LIST" "."
fi

FILES_SCANNED="$(wc -l < "$FILES_LIST" | tr -d ' ')"

# Helper: filter file list to exclude test/story/script files (for some rules)
prod_files() {
    grep -vE '(__tests__/|/test/|/tests/|\.test\.|\.spec\.|\.stories\.|/scripts/|/storybook/)' "$FILES_LIST" || true
}

# ---------- Rule: tsconfig.json compiler flags --------------------------------

read_tsconfig_flags() {
    # Outputs key=value lines for the flags we care about; missing = "absent"
    local path
    for path in tsconfig.json tsconfig.base.json; do
        [ -f "$path" ] && { TSCONFIG_PATH="$path"; break; }
    done
    [ -z "${TSCONFIG_PATH:-}" ] && return 1
    has_cmd python3 || return 1

    SPECKIT_TSC="$TSCONFIG_PATH" python3 <<'PY'
import json, os, re, sys
p = os.environ["SPECKIT_TSC"]
try:
    raw = open(p, encoding="utf-8").read()
except Exception as e:
    print(f"error={e}"); sys.exit(0)
raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)
raw = re.sub(r"^\s*//.*$", "", raw, flags=re.M)
raw = re.sub(r",(\s*[}\]])", r"\1", raw)
try:
    cfg = json.loads(raw)
except Exception as e:
    print(f"error={e}"); sys.exit(0)

co = cfg.get("compilerOptions") or {}
for key in ("strict", "noUncheckedIndexedAccess", "exactOptionalPropertyTypes",
            "noImplicitOverride", "noFallthroughCasesInSwitch",
            "noImplicitReturns", "forceConsistentCasingInFileNames"):
    val = co.get(key, None)
    print(f"{key}={'true' if val is True else 'false' if val is False else 'absent'}")
print(f"path={p}")
PY
}

eval_compiler_rules() {
    local out
    if ! out="$(read_tsconfig_flags 2>/dev/null)"; then
        # No tsconfig or no python3 — emit one finding per critical compiler rule
        for rule in TS.COMPILER.strict-missing TS.COMPILER.no-unchecked-indexed-access-missing TS.COMPILER.exact-optional-missing; do
            rule_enabled "$rule" || continue
            emit_finding "$rule" "critical" "tsconfig.json" 0 "tsconfig.json not found or unparseable"
        done
        return 0
    fi

    local TSCONFIG_PATH_REPORTED
    TSCONFIG_PATH_REPORTED="$(printf '%s' "$out" | sed -n 's/^path=//p' | head -n1)"
    [ -z "$TSCONFIG_PATH_REPORTED" ] && TSCONFIG_PATH_REPORTED="tsconfig.json"

    check_flag() {
        local rule="$1" key="$2" severity="$3"
        rule_enabled "$rule" || return 0
        local val
        val="$(printf '%s' "$out" | sed -n "s/^${key}=//p" | head -n1)"
        if [ "$val" != "true" ]; then
            local snippet="compilerOptions.${key} = ${val:-absent} (expected true)"
            emit_finding "$rule" "$severity" "$TSCONFIG_PATH_REPORTED" 0 "$snippet"
        fi
    }

    check_flag TS.COMPILER.strict-missing                      strict                          critical
    check_flag TS.COMPILER.no-unchecked-indexed-access-missing noUncheckedIndexedAccess        critical
    check_flag TS.COMPILER.exact-optional-missing              exactOptionalPropertyTypes      critical
    check_flag TS.COMPILER.no-implicit-override-missing        noImplicitOverride              high
    check_flag TS.COMPILER.no-fallthrough-cases-missing        noFallthroughCasesInSwitch      high
    check_flag TS.COMPILER.no-implicit-returns-missing         noImplicitReturns               high
    check_flag TS.COMPILER.force-consistent-casing-missing     forceConsistentCasingInFileNames high
}

# ---------- Generic regex-scanner over the file list -------------------------
# scan_regex <rule_id> <severity> <regex> [include_filter_grep_args...]
scan_regex() {
    local rule="$1" sev="$2" pattern="$3"
    shift 3
    rule_enabled "$rule" || return 0
    [ "$FILES_SCANNED" -eq 0 ] && return 0

    # Optional filter on the file list (e.g. only .tsx files for some rules)
    local list="$FILES_LIST"
    if [ "$#" -gt 0 ]; then
        local filtered="$WORKDIR/.list.$rule"
        if [ "$1" = "--only" ]; then shift; grep -E "$1" "$FILES_LIST" > "$filtered" || true
        elif [ "$1" = "--exclude" ]; then shift; grep -vE "$1" "$FILES_LIST" > "$filtered" || true
        else cp "$FILES_LIST" "$filtered"
        fi
        list="$filtered"
    fi
    [ ! -s "$list" ] && return 0

    # Parallel grep, capped output
    < "$list" tr '\n' '\0' | xargs -0 -P "$PARALLEL" -n 50 grep -HnE "$pattern" 2>/dev/null \
        | head -n $((MAX_PER_RULE * 4)) \
        | while IFS= read -r match; do
            # match format: file:line:content
            local file line content snippet
            file="${match%%:*}"
            local rest="${match#*:}"
            line="${rest%%:*}"
            content="${rest#*:}"
            snippet="$(trim_snippet "$content")"
            emit_finding "$rule" "$sev" "$file" "$line" "$snippet"
        done
}

# ---------- Specific rule scanners --------------------------------------------

# TS.TYPE.any-usage — matches `: any`, `<any>`, `Array<any>`, `as any`, `(...): any`
# Avoids `anyone`/`anything`/`anywhere` via word-boundary patterns.
scan_any_usage() {
    rule_enabled "TS.TYPE.any-usage" || return 0
    scan_regex "TS.TYPE.any-usage" "critical" \
        '(:\s*any\b)|(<\s*any\s*[,>])|(\bArray<\s*any\s*>)|(\bas\s+any\b)|(:\s*Promise<any>)' \
        --only '\.(ts|tsx)$'
}

# TS.TYPE.ts-ignore
scan_ts_ignore() {
    rule_enabled "TS.TYPE.ts-ignore" || return 0
    scan_regex "TS.TYPE.ts-ignore" "critical" \
        '@ts-ignore' \
        --only '\.(ts|tsx|js|jsx)$'
}

# TS.TYPE.unchecked-as-cast — `as Foo` not in {const, unknown}
scan_unchecked_as() {
    rule_enabled "TS.TYPE.unchecked-as-cast" || return 0
    # We use grep -P if available for negative lookahead; otherwise fall back
    # to a permissive ERE and filter via awk.
    local list="$WORKDIR/ts_files.txt"
    grep -E '\.(ts|tsx)$' "$FILES_LIST" > "$list" || true
    [ ! -s "$list" ] && return 0

    if echo "x" | grep -qP "x" 2>/dev/null; then
        < "$list" tr '\n' '\0' | xargs -0 -P "$PARALLEL" -n 50 \
            grep -HnP '\bas\s+(?!(const|unknown)\b)[A-Z][A-Za-z0-9_]*' 2>/dev/null \
            | head -n $((MAX_PER_RULE * 4)) \
            | while IFS= read -r match; do
                local file line content snippet
                file="${match%%:*}"
                local rest="${match#*:}"
                line="${rest%%:*}"
                content="${rest#*:}"
                snippet="$(trim_snippet "$content")"
                emit_finding "TS.TYPE.unchecked-as-cast" "critical" "$file" "$line" "$snippet"
            done
    else
        # POSIX ERE fallback: match `as Foo`, then awk-filter to skip const/unknown
        < "$list" tr '\n' '\0' | xargs -0 -P "$PARALLEL" -n 50 \
            grep -HnE '\bas[[:space:]]+[A-Z][A-Za-z0-9_]*' 2>/dev/null \
            | awk -F: '!($0 ~ /\bas[[:space:]]+(const|unknown)\b/)' \
            | head -n $((MAX_PER_RULE * 4)) \
            | while IFS= read -r match; do
                local file line content snippet
                file="${match%%:*}"
                local rest="${match#*:}"
                line="${rest%%:*}"
                content="${rest#*:}"
                snippet="$(trim_snippet "$content")"
                emit_finding "TS.TYPE.unchecked-as-cast" "critical" "$file" "$line" "$snippet"
            done
    fi
}

# TS.TYPE.untyped-catch — `catch (e)` or `catch (err)` without `: unknown`
scan_untyped_catch() {
    rule_enabled "TS.TYPE.untyped-catch" || return 0
    scan_regex "TS.TYPE.untyped-catch" "high" \
        'catch\s*\(\s*[A-Za-z_$][A-Za-z0-9_$]*\s*\)' \
        --only '\.(ts|tsx)$'
}

# BE.DAL.missing-server-only — files inside lib/dal (etc.) without `server-only`
scan_dal_server_only() {
    rule_enabled "BE.DAL.missing-server-only" || return 0
    local list="$WORKDIR/dal_files.txt"
    grep -E '(^|/)(src/)?(lib|server|data)/dal/.*\.(ts|tsx)$' "$FILES_LIST" > "$list" || true
    [ ! -s "$list" ] && return 0

    while IFS= read -r f; do
        if ! grep -qE "^\s*import\s+(.*\s+from\s+)?['\"]server-only['\"]" "$f" 2>/dev/null; then
            emit_finding "BE.DAL.missing-server-only" "critical" "$f" 1 "DAL module missing import 'server-only'"
        fi
    done < "$list"
}

# BE.ENV.direct-process-env-outside-validator — process.env.X reads outside env validator file
scan_direct_process_env() {
    rule_enabled "BE.ENV.direct-process-env-outside-validator" || return 0
    local list="$WORKDIR/code_files.txt"
    # Exclude env validator candidates and tests/scripts.
    grep -E '\.(ts|tsx|js|jsx|mjs|cjs)$' "$FILES_LIST" \
        | grep -vE '(^|/)(env|environment|config)\.(ts|tsx|js|mjs|cjs)$' \
        | grep -vE '(^|/)(lib|src/lib|server|src/server)/env(\.|/)' \
        | grep -vE '(__tests__/|/test/|/tests/|\.test\.|\.spec\.|/scripts/|/storybook/)' \
        > "$list" || true
    [ ! -s "$list" ] && return 0

    < "$list" tr '\n' '\0' | xargs -0 -P "$PARALLEL" -n 50 \
        grep -HnE 'process\.env\.[A-Z_][A-Z0-9_]*' 2>/dev/null \
        | head -n $((MAX_PER_RULE * 4)) \
        | while IFS= read -r match; do
            local file line content snippet
            file="${match%%:*}"; local rest="${match#*:}"
            line="${rest%%:*}";  content="${rest#*:}"
            snippet="$(trim_snippet "$content")"
            emit_finding "BE.ENV.direct-process-env-outside-validator" "high" "$file" "$line" "$snippet"
        done
}

# FE.RSC.use-client-at-page-or-layout — `"use client"` at the top of page.tsx/layout.tsx
scan_use_client_at_root() {
    rule_enabled "FE.RSC.use-client-at-page-or-layout" || return 0
    local list="$WORKDIR/app_roots.txt"
    grep -E '(^|/)app/.*/(page|layout|template)\.(tsx?|jsx?)$|(^|/)src/app/.*/(page|layout|template)\.(tsx?|jsx?)$' "$FILES_LIST" > "$list" || true
    [ ! -s "$list" ] && return 0

    while IFS= read -r f; do
        # Read the first few non-empty lines; flag if first non-empty line is "use client"
        local first
        first="$(head -n 5 "$f" 2>/dev/null | grep -m1 -vE '^\s*$' || true)"
        if printf '%s' "$first" | grep -qE "^\s*['\"]use client['\"]"; then
            emit_finding "FE.RSC.use-client-at-page-or-layout" "critical" "$f" 1 "$(trim_snippet "$first")"
        fi
    done < "$list"
}

# FE.IMG.raw-img-tag — `<img ` in .tsx (excluding tests/stories)
scan_raw_img() {
    rule_enabled "FE.IMG.raw-img-tag" || return 0
    local list="$WORKDIR/tsx_prod.txt"
    grep -E '\.(tsx|jsx)$' "$FILES_LIST" \
        | grep -vE '(__tests__/|/test/|/tests/|\.test\.|\.spec\.|\.stories\.|/storybook/)' \
        > "$list" || true
    [ ! -s "$list" ] && return 0

    < "$list" tr '\n' '\0' | xargs -0 -P "$PARALLEL" -n 50 \
        grep -HnE '<img\s' 2>/dev/null \
        | head -n $((MAX_PER_RULE * 4)) \
        | while IFS= read -r match; do
            local file line content snippet
            file="${match%%:*}"; local rest="${match#*:}"
            line="${rest%%:*}";  content="${rest#*:}"
            snippet="$(trim_snippet "$content")"
            emit_finding "FE.IMG.raw-img-tag" "high" "$file" "$line" "$snippet"
        done
}

# FE.LINK.raw-anchor-internal — `<a href="/...` (root-relative) in app/
scan_raw_anchor() {
    rule_enabled "FE.LINK.raw-anchor-internal" || return 0
    local list="$WORKDIR/tsx_app.txt"
    grep -E '(^|/)(src/)?app/.*\.(tsx|jsx)$' "$FILES_LIST" \
        | grep -vE '(__tests__/|/test/|/tests/|\.test\.|\.spec\.|\.stories\.|/storybook/)' \
        > "$list" || true
    [ ! -s "$list" ] && return 0

    < "$list" tr '\n' '\0' | xargs -0 -P "$PARALLEL" -n 50 \
        grep -HnE '<a\s[^>]*href=["'\'']/[^/"'\'']' 2>/dev/null \
        | head -n $((MAX_PER_RULE * 4)) \
        | while IFS= read -r match; do
            local file line content snippet
            file="${match%%:*}"; local rest="${match#*:}"
            line="${rest%%:*}";  content="${rest#*:}"
            snippet="$(trim_snippet "$content")"
            emit_finding "FE.LINK.raw-anchor-internal" "medium" "$file" "$line" "$snippet"
        done
}

# FE.METADATA.missing-generate-metadata — app/.../page.tsx without metadata export
scan_missing_metadata() {
    rule_enabled "FE.METADATA.missing-generate-metadata" || return 0
    local list="$WORKDIR/pages.txt"
    grep -E '(^|/)(src/)?app/.*/page\.(tsx|jsx|ts|js)$' "$FILES_LIST" > "$list" || true
    [ ! -s "$list" ] && return 0

    while IFS= read -r f; do
        # Skip dynamic-only fragments (e.g. parallel route slots) and group folders.
        if ! grep -qE 'export\s+(const|let|var|async\s+function|function)\s+(metadata|generateMetadata)\b' "$f" 2>/dev/null; then
            emit_finding "FE.METADATA.missing-generate-metadata" "medium" "$f" 1 "page module exports no \`metadata\` or \`generateMetadata\`"
        fi
    done < "$list"
}

# SEC.SESSION.localstorage-auth
scan_localstorage_auth() {
    rule_enabled "SEC.SESSION.localstorage-auth" || return 0
    scan_regex "SEC.SESSION.localstorage-auth" "critical" \
        'localStorage\.(setItem|getItem)\s*\(\s*["'\''](session|token|auth|jwt|access|refresh|bearer)' \
        --only '\.(ts|tsx|js|jsx)$'
}

# SEC.XSS.dangerously-set
scan_dangerously_set() {
    rule_enabled "SEC.XSS.dangerously-set" || return 0
    scan_regex "SEC.XSS.dangerously-set" "high" \
        'dangerouslySetInnerHTML' \
        --only '\.(tsx|jsx)$'
}

# SEC.SECRET.public-env-prefix
scan_public_env_secret() {
    rule_enabled "SEC.SECRET.public-env-prefix" || return 0
    # Match NEXT_PUBLIC_* env keys whose names suggest secrecy.
    scan_regex "SEC.SECRET.public-env-prefix" "critical" \
        'NEXT_PUBLIC_[A-Z0-9_]*(SECRET|TOKEN|KEY|PASSWORD|PASSWD|PRIVATE)[A-Z0-9_]*' \
        --only '\.(ts|tsx|js|jsx|mjs|cjs|env|env\..*|envrc)$'

    # Also scan .env* files (top-level only) — these aren't in FILES_LIST since
    # they aren't .ts/.js. Iterate explicitly.
    if rule_enabled "SEC.SECRET.public-env-prefix"; then
        local f
        for f in .env .env.local .env.production .env.development .env.example .env.sample .env.template; do
            [ -f "$f" ] || continue
            grep -nE '^NEXT_PUBLIC_[A-Z0-9_]*(SECRET|TOKEN|KEY|PASSWORD|PASSWD|PRIVATE)' "$f" 2>/dev/null \
                | while IFS=: read -r line content; do
                    emit_finding "SEC.SECRET.public-env-prefix" "critical" "$f" "$line" "$(trim_snippet "$content")"
                done
        done
    fi
}

# SEC.SQL.template-literal-query — heuristic
scan_sql_template() {
    rule_enabled "SEC.SQL.template-literal-query" || return 0
    scan_regex "SEC.SQL.template-literal-query" "high" \
        '`[^`]*\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b[^`]*\$\{' \
        --only '\.(ts|tsx|js|jsx|mjs|cjs)$'
}

# PERF.LOG.console-log-in-source
scan_console_log() {
    rule_enabled "PERF.LOG.console-log-in-source" || return 0
    local list="$WORKDIR/prod_files.txt"
    prod_files > "$list"
    [ ! -s "$list" ] && return 0
    < "$list" tr '\n' '\0' | xargs -0 -P "$PARALLEL" -n 50 \
        grep -HnE '\bconsole\.log\s*\(' 2>/dev/null \
        | head -n $((MAX_PER_RULE * 4)) \
        | while IFS= read -r match; do
            local file line content snippet
            file="${match%%:*}"; local rest="${match#*:}"
            line="${rest%%:*}";  content="${rest#*:}"
            snippet="$(trim_snippet "$content")"
            emit_finding "PERF.LOG.console-log-in-source" "medium" "$file" "$line" "$snippet"
        done
}

# INFRA.CI.missing-typecheck-job — no CI workflow file contains tsc/typecheck
scan_ci_typecheck() {
    rule_enabled "INFRA.CI.missing-typecheck-job" || return 0
    local ci_dir=".github/workflows"
    if [ ! -d "$ci_dir" ]; then
        emit_finding "INFRA.CI.missing-typecheck-job" "high" ".github/workflows" 0 "no CI workflow directory found"
        return 0
    fi
    if ! grep -rlE '\b(tsc|typecheck|type-check|type:check)\b' "$ci_dir" 2>/dev/null | grep -q .; then
        emit_finding "INFRA.CI.missing-typecheck-job" "high" "$ci_dir" 0 "no workflow references tsc or a typecheck script"
    fi
}

# ---------- Run all enabled rules ---------------------------------------------

eval_compiler_rules
scan_any_usage
scan_ts_ignore
scan_unchecked_as
scan_untyped_catch
scan_dal_server_only
scan_direct_process_env
scan_use_client_at_root
scan_raw_img
scan_raw_anchor
scan_missing_metadata
scan_localstorage_auth
scan_dangerously_set
scan_public_env_secret
scan_sql_template
scan_console_log
scan_ci_typecheck

# ---------- Render report -----------------------------------------------------

if [ "$JSON_MODE" = true ]; then
    if has_cmd python3; then
        # Write rules catalog and findings for python aggregation
        printf '%s\n' "${RULE_IDS[@]}"  > "$WORKDIR/ids.txt"
        printf '%s\n' "${RULE_META[@]}" > "$WORKDIR/meta.txt"

        SPECKIT_W="$WORKDIR" \
        SPECKIT_REPO_ROOT="$REPO_ROOT" \
        SPECKIT_FILES_SCANNED="$FILES_SCANNED" \
        SPECKIT_PATHS="$PATHS_ARG" \
        SPECKIT_MAX_PER_RULE="$MAX_PER_RULE" \
        SPECKIT_MIN_SEVERITY="$MIN_SEVERITY" \
        python3 <<'PY'
import datetime as dt, glob, json, os
w = os.environ["SPECKIT_W"]
ids   = [l.rstrip("\n") for l in open(os.path.join(w, "ids.txt"),  encoding="utf-8") if l.strip()]
metas = [l.rstrip("\n") for l in open(os.path.join(w, "meta.txt"), encoding="utf-8") if l.strip()]

rule_meta = {}
for rid, m in zip(ids, metas):
    sev, section, phase, scope, directive, remediation = m.split("|", 5)
    rule_meta[rid] = {
        "id": rid, "severity": sev, "section": section, "phase": phase,
        "scope": scope, "directive": directive, "remediation": remediation,
    }

findings = []
findings_dir = os.path.join(w, "findings")
for path in sorted(glob.glob(os.path.join(findings_dir, "*.ndjson"))):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            rid = rec.get("rule_id")
            meta = rule_meta.get(rid, {})
            rec["section"]     = meta.get("section")
            rec["phase"]       = meta.get("phase")
            rec["scope"]       = meta.get("scope")
            rec["directive"]   = meta.get("directive")
            rec["remediation"] = meta.get("remediation")
            findings.append(rec)

by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
by_section = {}
by_rule = {}
for fnd in findings:
    by_sev[fnd["severity"]] = by_sev.get(fnd["severity"], 0) + 1
    sec_key = (fnd.get("section") or "").split(" /", 1)[0].split(" ", 1)[0] or "unknown"
    by_section[sec_key] = by_section.get(sec_key, 0) + 1
    by_rule[fnd["rule_id"]] = by_rule.get(fnd["rule_id"], 0) + 1

paths = os.environ.get("SPECKIT_PATHS") or None
if paths:
    paths = [p for p in paths.split(",") if p]

result = {
    "schema_version": "1.0",
    "command": "audit",
    "scanned_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    "repo_root": os.environ["SPECKIT_REPO_ROOT"],
    "scope": {
        "files_scanned":   int(os.environ["SPECKIT_FILES_SCANNED"]),
        "paths_included":  paths,
        "extensions":      [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"],
        "min_severity":    os.environ["SPECKIT_MIN_SEVERITY"],
        "max_per_rule":    int(os.environ["SPECKIT_MAX_PER_RULE"]),
    },
    "summary": {
        "rules_evaluated":     len(ids),
        "rules_with_findings": len(by_rule),
        "findings_total":      len(findings),
        "by_severity":         by_sev,
        "by_section":          by_section,
        "by_rule":             by_rule,
    },
    "rules":    list(rule_meta.values()),
    "findings": findings,
}
print(json.dumps(result, indent=2))
PY
    else
        echo '{"error":"python3 unavailable; cannot render JSON report"}'
    fi
else
    # Human-readable summary
    echo "speckit audit — $REPO_ROOT"
    echo "Files scanned: $FILES_SCANNED"
    echo "Min severity:  $MIN_SEVERITY"
    echo ""
    local_total=0
    for f in "$FINDINGS_DIR"/*.ndjson; do
        [ -f "$f" ] || continue
        rule_id="$(basename "$f" .ndjson)"
        n="$(wc -l < "$f" | tr -d ' ')"
        local_total=$((local_total + n))
        printf '  %-55s %3d finding(s)\n' "$rule_id" "$n"
    done
    if [ "$local_total" -eq 0 ]; then
        echo "  (no findings)"
    fi
    echo ""
    echo "Total findings: $local_total"
fi
