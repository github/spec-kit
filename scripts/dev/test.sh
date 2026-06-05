#!/usr/bin/env bash
# Spec Kit local test wrapper — chunked FIFO dispatch over pytest-xdist.
#
# Design (matches the chunked-task / bounded-memory pattern):
#   * Collect node ids once: `pytest --collect-only -q`.
#   * Split the collection into fixed-size chunks (default 200 nodes).
#   * Dispatch chunks sequentially as a FIFO queue; inside each chunk,
#     pytest-xdist's `--dist=load` hands tests out one at a time to
#     workers as they finish — natural FIFO progression with bounded
#     in-flight memory.
#   * Persist the cursor (next test index / chunk boundary) to
#     `.pytest_cache/<script>-cursor` after every successful chunk so
#     `--resume` continues from the last completed chunk.
#   * Resume is tied to the current collection order; changing selection
#     or order can skip or re-run tests.
#   * `--reset` clears the cursor; `--bench` reduces pytest output (progress still prints).
#
# Usage:
#   scripts/dev/test.sh                          # full suite, chunked
#   scripts/dev/test.sh --chunk-size 100
#   scripts/dev/test.sh --resume                 # continue from cursor
#   scripts/dev/test.sh --reset                  # clear cursor
#   scripts/dev/test.sh --bench                  # quieter pytest output
#   scripts/dev/test.sh -- tests/test_merge.py   # pass-through to pytest
#
# Notes:
#   --resume assumes the same collection order; changing selection/order
#   can skip or re-run tests.

if [ -z "${BASH_VERSION:-}" ]; then
    echo "This script requires bash." >&2
    exit 1
fi

set -euo pipefail

SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
SCRIPT_STEM="${SCRIPT_NAME%.*}"
LOG_PREFIX="[${SCRIPT_STEM}]"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTEST_CACHE_DIR="$REPO_ROOT/.pytest_cache"
CURSOR_FILE="$PYTEST_CACHE_DIR/${SCRIPT_STEM}-cursor"

CHUNK_SIZE=200
RESUME=0
RESET=0
BENCH=0
PASSTHROUGH=()
RUNTIME_PASSTHROUGH=()
COLLECT_PASSTHROUGH=()
PYTEST_CMD=()
LOCK_FILE="$PYTEST_CACHE_DIR/${SCRIPT_STEM}.lock"
LOCK_DIR="$PYTEST_CACHE_DIR/${SCRIPT_STEM}.lockdir"
LOCK_MODE=""
LOCK_HELD=0
COLLECT_ERR=""
COLLECT_OUT=""
COLLECT_FILTERED=""
CHUNK_NODES=()
COLLECT_ONLY_REQUESTED=0
FD3_OPEN=0

log() {
    echo "$LOG_PREFIX $*" >&2
}

err() {
    echo "$LOG_PREFIX ERROR: $*" >&2
}

ensure_dir_safe() {
    local path="$1"
    local label="$2"
    if [[ -L "$path" ]]; then
        err "$label is a symlink; refusing to use $path"
        exit 1
    fi
    if [[ -e "$path" && ! -d "$path" ]]; then
        err "$label is not a directory; refusing to use $path"
        exit 1
    fi
}

ensure_regular_file_or_missing() {
    local path="$1"
    local label="$2"
    if [[ -L "$path" ]]; then
        err "$label is a symlink; refusing to use $path"
        exit 1
    fi
    if [[ -e "$path" && ! -f "$path" ]]; then
        err "$label is not a regular file; refusing to use $path"
        exit 1
    fi
}

ensure_single_link() {
    local path="$1"
    local label="$2"
    local links=""
    if [[ ! -e "$path" ]]; then
        return 0
    fi
    if links="$(stat -c %h "$path" 2>/dev/null)"; then
        :
    elif links="$(stat -f %l "$path" 2>/dev/null)"; then
        :
    else
        return 0
    fi
    if [[ "$links" =~ ^[0-9]+$ ]] && (( links > 1 )); then
        err "$label has multiple links ($links); refusing to use $path"
        exit 1
    fi
}

remove_cursor_safe() {
    ensure_dir_safe "$PYTEST_CACHE_DIR" "pytest cache dir"
    ensure_regular_file_or_missing "$CURSOR_FILE" "cursor path"
    ensure_single_link "$CURSOR_FILE" "cursor path"
    rm -f "$CURSOR_FILE"
}

print_help() {
    awk '
        /^# Usage:/ {printing=1}
        printing {
            if ($0 !~ /^#/) {exit}
            sub(/^# ?/, "", $0)
            print
        }
    ' "$0"
}

while (( $# )); do
    case "$1" in
        --chunk-size)
            if (( $# < 2 )); then
                err "--chunk-size requires a value"
                exit 1
            fi
            CHUNK_SIZE="$2"
            shift 2
            ;;
        --resume)     RESUME=1; shift ;;
        --reset)      RESET=1;  shift ;;
        --bench)      BENCH=1;  shift ;;
        --)           shift; PASSTHROUGH+=("$@"); break ;;
        -h|--help)    print_help; exit 0 ;;
        *)            PASSTHROUGH+=("$1"); shift ;;
    esac
done

if ! [[ "$CHUNK_SIZE" =~ ^[1-9][0-9]*$ ]]; then
    err "--chunk-size must be a positive integer (got '$CHUNK_SIZE')"
    exit 1
fi

mktemp_file() {
    local target_dir="${1:-}"
    local tmp
    if [[ -n "$target_dir" ]]; then
        if tmp="$(mktemp -p "$target_dir" "${SCRIPT_STEM}.XXXXXX" 2>/dev/null)"; then
            printf '%s\n' "$tmp"
            return 0
        fi
        if tmp="$(mktemp "$target_dir/${SCRIPT_STEM}.XXXXXX" 2>/dev/null)"; then
            printf '%s\n' "$tmp"
            return 0
        fi
        err "mktemp failed in $target_dir; check permissions"
        return 1
    fi
    if tmp="$(mktemp -t "${SCRIPT_STEM}.XXXXXX" 2>/dev/null)"; then
        printf '%s\n' "$tmp"
        return 0
    fi
    if tmp="$(mktemp "${TMPDIR:-/tmp}/${SCRIPT_STEM}.XXXXXX" 2>/dev/null)"; then
        printf '%s\n' "$tmp"
        return 0
    fi
    err "mktemp failed; set TMPDIR or install a compatible mktemp"
    return 1
}

arg_bytes() {
    local total=0
    local arg
    local old_lc_all="${LC_ALL-}"
    local had_lc_all=0
    if [[ ${LC_ALL+x} ]]; then
        had_lc_all=1
    fi
    LC_ALL=C
    for arg in "$@"; do
        total=$(( total + ${#arg} + 1 ))
    done
    if (( had_lc_all )); then
        LC_ALL="$old_lc_all"
    else
        unset LC_ALL
    fi
    printf '%s\n' "$total"
}

# Collection and execution do not share every pytest flag. Keep runtime
# passthrough aligned with user intent while stripping collect-only toggles
# and failing fast on xdist-specific options owned by this script.
idx=0
while (( idx < ${#PASSTHROUGH[@]} )); do
    arg="${PASSTHROUGH[$idx]}"
    case "$arg" in
        --collect-only|--co) COLLECT_ONLY_REQUESTED=1 ;;
        -n|--numprocesses|--dist|-n*|--numprocesses=*|--dist=*)
            err "$arg is managed by this script; remove xdist flags from arguments"
            exit 1
            ;;
        *)
            RUNTIME_PASSTHROUGH+=("$arg")
            COLLECT_PASSTHROUGH+=("$arg")
            ;;
    esac
    idx=$((idx + 1))
done

if (( COLLECT_ONLY_REQUESTED )); then
    err "--collect-only is not supported; run pytest --collect-only directly"
    exit 1
fi

cleanup() {
    if (( FD3_OPEN )); then
        { exec 3<&-; } 2>/dev/null || true
        FD3_OPEN=0
    fi
    [[ -n "$COLLECT_ERR" && -f "$COLLECT_ERR" ]] && rm -f "$COLLECT_ERR"
    [[ -n "$COLLECT_OUT" && -f "$COLLECT_OUT" ]] && rm -f "$COLLECT_OUT"
    [[ -n "$COLLECT_FILTERED" && -f "$COLLECT_FILTERED" ]] && rm -f "$COLLECT_FILTERED"
    if [[ "$LOCK_MODE" == "flock" ]]; then
        flock -u 9 2>/dev/null || true
        exec 9>&- || true
    elif [[ "$LOCK_MODE" == "dir" ]] && (( LOCK_HELD )); then
        local PID_CONTENTS
        if [[ -f "$LOCK_DIR/pid" ]]; then
            PID_CONTENTS="$(tr -d '[:space:]' < "$LOCK_DIR/pid" 2>/dev/null || true)"
            if [[ "$PID_CONTENTS" == "$$" ]]; then
                rm -f "$LOCK_DIR/pid"
                rmdir "$LOCK_DIR" 2>/dev/null || true
            fi
        fi
    fi
}

trap cleanup EXIT

write_cursor() {
    ensure_dir_safe "$PYTEST_CACHE_DIR" "pytest cache dir"
    ensure_regular_file_or_missing "$CURSOR_FILE" "cursor path"
    ensure_single_link "$CURSOR_FILE" "cursor path"
    local cursor_tmp
    cursor_tmp="$(mktemp_file "$PYTEST_CACHE_DIR")" || exit 1
    if [[ -L "$cursor_tmp" || ! -f "$cursor_tmp" ]]; then
        err "cursor temp path is unsafe; refusing to write $cursor_tmp"
        rm -f "$cursor_tmp" 2>/dev/null || true
        exit 1
    fi
    printf '%s\n' "$1" > "$cursor_tmp"
    mv "$cursor_tmp" "$CURSOR_FILE"
}

read_chunk() {
    local count=0
    local node
    CHUNK_NODES=()
    while (( count < CHUNK_SIZE )); do
        if ! IFS= read -r node <&3; then
            break
        fi
        CHUNK_NODES+=("$node")
        count=$((count + 1))
    done
}

cd "$REPO_ROOT"
ensure_dir_safe "$PYTEST_CACHE_DIR" "pytest cache dir"
mkdir -p "$PYTEST_CACHE_DIR"

if command -v flock >/dev/null 2>&1; then
    ensure_regular_file_or_missing "$LOCK_FILE" "lock file"
    exec 9>>"$LOCK_FILE" || { err "unable to open lock file: $LOCK_FILE"; exit 1; }
    if ! flock -n 9; then
        err "another run is active (lock: $LOCK_FILE)"
        exit 1
    fi
    LOCK_MODE="flock"
    LOCK_HELD=1
else
    ensure_dir_safe "$LOCK_DIR" "lock dir"
    if [[ -d "$LOCK_DIR" ]]; then
        if [[ -f "$LOCK_DIR/pid" ]]; then
            PID_CONTENTS="$(tr -d '[:space:]' < "$LOCK_DIR/pid" 2>/dev/null || true)"
            if [[ "$PID_CONTENTS" =~ ^[0-9]+$ ]] && kill -0 "$PID_CONTENTS" 2>/dev/null; then
                err "another run is active (lock: $LOCK_DIR)"
                exit 1
            fi
            log "removing stale lock (pid: ${PID_CONTENTS:-unknown})"
        fi
        rm -f "$LOCK_DIR/pid"
        if ! rmdir "$LOCK_DIR" 2>/dev/null; then
            err "lock dir is not empty; refusing to remove $LOCK_DIR"
            exit 1
        fi
    fi
    if ! mkdir "$LOCK_DIR" 2>/dev/null; then
        if [[ -d "$LOCK_DIR" ]]; then
            err "another run is active (lock: $LOCK_DIR)"
        else
            err "failed to create lock dir: $LOCK_DIR"
        fi
        exit 1
    fi
    LOCK_MODE="dir"
    printf '%s\n' "$$" > "$LOCK_DIR/pid" || {
        err "failed to write lock pid file: $LOCK_DIR/pid"
        rmdir "$LOCK_DIR" 2>/dev/null || true
        exit 1
    }
    LOCK_HELD=1
fi

if (( RESET )); then
    remove_cursor_safe
    log "cursor cleared"
    exit 0
fi

# 1. Collect node ids.
if command -v uv >/dev/null 2>&1; then
    PYTEST_CMD=(uv run pytest)
elif command -v python3 >/dev/null 2>&1; then
    PYTEST_CMD=(python3 -m pytest)
elif command -v python >/dev/null 2>&1; then
    PYTEST_CMD=(python -m pytest)
else
    err "pytest runner not found (install uv or ensure python is on PATH)"
    exit 1
fi

if ! "${PYTEST_CMD[@]}" -p xdist --version >/dev/null 2>&1; then
    err "pytest-xdist is required for this wrapper (missing xdist plugin)."
    err "install test extras, e.g. 'uv pip install -e .[test]'"
    exit 1
fi

log "collecting tests ..."
COLLECT_ERR="$(mktemp_file)" || exit 1
COLLECT_OUT="$(mktemp_file)" || exit 1
if ! "${PYTEST_CMD[@]}" --collect-only -q --no-header --no-summary "${COLLECT_PASSTHROUGH[@]}" >"$COLLECT_OUT" 2>"$COLLECT_ERR"; then
    err "test collection failed"
    [[ -s "$COLLECT_ERR" ]] && { echo "--- collection stderr ---"; cat "$COLLECT_ERR"; } >&2
    rm -f "$COLLECT_ERR" "$COLLECT_OUT"
    exit 1
fi
if [[ -s "$COLLECT_ERR" ]] && (( ! BENCH )); then
    log "collection warnings:"
    cat "$COLLECT_ERR" >&2
fi
rm -f "$COLLECT_ERR"
COLLECT_FILTERED="$(mktemp_file)" || exit 1
LC_ALL=C awk 'NF { print }' "$COLLECT_OUT" > "$COLLECT_FILTERED"
mv "$COLLECT_FILTERED" "$COLLECT_OUT"
TOTAL="$(wc -l < "$COLLECT_OUT" | tr -d '[:space:]')"
if (( TOTAL == 0 )); then
    err "no tests collected"
    exit 1
fi

BASE_PYTEST_FLAGS=(-p xdist -n auto --dist=load --no-header)
if (( BENCH )); then
    BASE_PYTEST_FLAGS+=(-q)
fi

ARG_MAX=""
if command -v getconf >/dev/null 2>&1; then
    ARG_MAX="$(getconf ARG_MAX 2>/dev/null || true)"
fi
if [[ "$ARG_MAX" =~ ^[0-9]+$ ]]; then
    MAX_NODE_LEN="$(LC_ALL=C awk 'length > max { max = length } END { print max + 0 }' "$COLLECT_OUT")"
    BASE_ARGS_SIZE="$(arg_bytes "${PYTEST_CMD[@]}" "${BASE_PYTEST_FLAGS[@]}" "${RUNTIME_PASSTHROUGH[@]}")"
    SAFETY_MARGIN=2048
    AVAILABLE=$(( ARG_MAX - BASE_ARGS_SIZE - SAFETY_MARGIN ))
    if (( AVAILABLE <= 0 )); then
        err "base pytest invocation exceeds ARG_MAX; reduce passthrough args"
        exit 1
    fi
    PER_NODE=$(( MAX_NODE_LEN + 1 ))
    if (( PER_NODE > 0 )); then
        MAX_SAFE=$(( AVAILABLE / PER_NODE ))
        if (( MAX_SAFE <= 0 )); then
            err "chunk size too large for ARG_MAX; reduce --chunk-size"
            exit 1
        fi
        if (( CHUNK_SIZE > MAX_SAFE )); then
            log "reducing --chunk-size from $CHUNK_SIZE to $MAX_SAFE to avoid ARG_MAX"
            CHUNK_SIZE="$MAX_SAFE"
        fi
    fi
else
    if (( CHUNK_SIZE > 1000 )); then
        log "warning: large --chunk-size may exceed OS argument limits"
    fi
fi

# 2. Determine starting cursor.
START=0
if (( RESUME )) && [[ -f "$CURSOR_FILE" ]]; then
    ensure_dir_safe "$PYTEST_CACHE_DIR" "pytest cache dir"
    ensure_regular_file_or_missing "$CURSOR_FILE" "cursor path"
    ensure_single_link "$CURSOR_FILE" "cursor path"
    RAW_START="$(tr -d '[:space:]' < "$CURSOR_FILE")"
    if [[ "$RAW_START" =~ ^[0-9]+$ ]]; then
        START="$RAW_START"
        (( START > TOTAL )) && START="$TOTAL"
        log "resuming from next test index: $START"
    else
        err "cursor file is invalid ('$RAW_START'); starting from 0"
        remove_cursor_safe
    fi
fi

if (( START >= TOTAL )); then
    log "nothing to resume (cursor at end: $START/$TOTAL)"
    remove_cursor_safe
    exit 0
fi

CHUNKS=$(( (TOTAL - START + CHUNK_SIZE - 1) / CHUNK_SIZE ))
log "$TOTAL tests · chunk=$CHUNK_SIZE · $CHUNKS chunk(s) queued · workers=auto"

exec 3< "$COLLECT_OUT"
FD3_OPEN=1
skip_count=0
while (( skip_count < START )); do
    if ! IFS= read -r _ <&3; then
        break
    fi
    skip_count=$((skip_count + 1))
done

# 3. FIFO dispatch.
T_START=$(date +%s)
i="$START"
chunk_idx=0
while (( i < TOTAL )); do
    end=$(( i + CHUNK_SIZE ))
    (( end > TOTAL )) && end="$TOTAL"
    chunk_idx=$(( chunk_idx + 1 ))
    read_chunk
    if (( ${#CHUNK_NODES[@]} == 0 )); then
        err "no tests read for chunk; stopping"
        write_cursor "$i"
        exit 1
    fi
    end=$(( i + ${#CHUNK_NODES[@]} ))
    log "chunk $chunk_idx/$CHUNKS tests $((i+1))..$end"

    if ! "${PYTEST_CMD[@]}" "${BASE_PYTEST_FLAGS[@]}" "${RUNTIME_PASSTHROUGH[@]}" "${CHUNK_NODES[@]}"; then
        err "chunk failed — cursor preserved at next test index $i (use --resume to retry)"
        write_cursor "$i"
        exit 1
    fi

    i="$end"
    write_cursor "$i"
done

T_END=$(date +%s)
if (( FD3_OPEN )); then
    { exec 3<&-; } 2>/dev/null || true
    FD3_OPEN=0
fi
rm -f "$COLLECT_OUT"
remove_cursor_safe
log "all $TOTAL tests passed in $((T_END - T_START))s"
