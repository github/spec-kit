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
CURSOR_FILE="$REPO_ROOT/.pytest_cache/${SCRIPT_STEM}-cursor"

CHUNK_SIZE=200
RESUME=0
RESET=0
BENCH=0
PASSTHROUGH=()
RUNTIME_PASSTHROUGH=()
COLLECT_PASSTHROUGH=()
PYTEST_CMD=()
LOCK_FILE="$REPO_ROOT/.pytest_cache/${SCRIPT_STEM}.lock"
LOCK_DIR="$REPO_ROOT/.pytest_cache/${SCRIPT_STEM}.lockdir"
LOCK_MODE=""
LOCK_HELD=0
CURSOR_TMP="$CURSOR_FILE.tmp"
COLLECT_ERR=""
COLLECT_OUT=""
COLLECT_FILTERED=""
CHUNK_NODES=()
XDIST_IGNORED=0
COLLECT_ONLY_REQUESTED=0
FD3_OPEN=0

log() {
    echo "$LOG_PREFIX $*" >&2
}

err() {
    echo "$LOG_PREFIX $*" >&2
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
    local tmp
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
    local bytes
    for arg in "$@"; do
        bytes="$(LC_ALL=C printf '%s' "$arg" | wc -c | tr -d '[:space:]')"
        bytes="${bytes:-0}"
        total=$(( total + bytes + 1 ))
    done
    printf '%s\n' "$total"
}

# Collection and execution do not share every pytest flag. Keep runtime
# passthrough aligned with user intent while stripping collect-only toggles
# and xdist-specific options that this script owns.
idx=0
while (( idx < ${#PASSTHROUGH[@]} )); do
    arg="${PASSTHROUGH[$idx]}"
    case "$arg" in
        --collect-only|--co) COLLECT_ONLY_REQUESTED=1 ;;
        -n|--numprocesses|--dist)
            next="${PASSTHROUGH[$((idx + 1))]:-}"
            if [[ -z "$next" || "$next" == -* ]]; then
                err "$arg requires a value, but xdist flags are managed by this script"
                exit 1
            fi
            XDIST_IGNORED=1
            idx=$((idx + 1))
            ;;
        -n*|--numprocesses=*|--dist=*) XDIST_IGNORED=1 ;;
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

if (( XDIST_IGNORED )); then
    log "ignoring xdist flags (-n/--numprocesses/--dist); this script manages them"
fi

cleanup() {
    if (( FD3_OPEN )); then
        { exec 3<&-; } 2>/dev/null || true
        FD3_OPEN=0
    fi
    [[ -n "$COLLECT_ERR" && -f "$COLLECT_ERR" ]] && rm -f "$COLLECT_ERR"
    [[ -n "$COLLECT_OUT" && -f "$COLLECT_OUT" ]] && rm -f "$COLLECT_OUT"
    [[ -n "$COLLECT_FILTERED" && -f "$COLLECT_FILTERED" ]] && rm -f "$COLLECT_FILTERED"
    [[ -n "$CURSOR_TMP" && -f "$CURSOR_TMP" ]] && rm -f "$CURSOR_TMP"
    if [[ "$LOCK_MODE" == "flock" ]]; then
        flock -u 9 2>/dev/null || true
        exec 9>&- || true
    elif [[ "$LOCK_MODE" == "dir" ]] && (( LOCK_HELD )); then
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
    printf '%s\n' "$1" > "$CURSOR_TMP"
    mv "$CURSOR_TMP" "$CURSOR_FILE"
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
mkdir -p "$(dirname "$CURSOR_FILE")"

if command -v flock >/dev/null 2>&1; then
    exec 9>"$LOCK_FILE" || { err "unable to open lock file: $LOCK_FILE"; exit 1; }
    if ! flock -n 9; then
        err "another run is active (lock: $LOCK_FILE)"
        exit 1
    fi
    LOCK_MODE="flock"
    LOCK_HELD=1
else
    if [[ -L "$LOCK_DIR" ]]; then
        err "lock path is a symlink; refusing to use $LOCK_DIR"
        exit 1
    fi
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
        err "another run is active (lock: $LOCK_DIR)"
        exit 1
    fi
    LOCK_MODE="dir"
    LOCK_HELD=1
    printf '%s\n' "$$" > "$LOCK_DIR/pid"
fi

if (( RESET )); then
    rm -f "$CURSOR_FILE" "$CURSOR_TMP"
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

if ! "${PYTEST_CMD[@]}" --help 2>/dev/null | grep -Eq '(-n[[:space:]]|--numprocesses)'; then
    err "pytest-xdist is required for this wrapper (missing -n/--numprocesses)."
    err "install test extras, e.g. 'uv pip install -e .[test]'"
    exit 1
fi

log "collecting tests ..."
COLLECT_ERR="$(mktemp_file)"
COLLECT_OUT="$(mktemp_file)"
if ! "${PYTEST_CMD[@]}" --collect-only -q "${COLLECT_PASSTHROUGH[@]}" >"$COLLECT_OUT" 2>"$COLLECT_ERR"; then
    err "test collection failed"
    [[ -s "$COLLECT_ERR" ]] && { echo "--- collection stderr ---"; cat "$COLLECT_ERR"; } >&2
    rm -f "$COLLECT_ERR" "$COLLECT_OUT"
    exit 1
fi
rm -f "$COLLECT_ERR"
COLLECT_FILTERED="$(mktemp_file)"
awk 'NF' "$COLLECT_OUT" > "$COLLECT_FILTERED"
mv "$COLLECT_FILTERED" "$COLLECT_OUT"
TOTAL="$(wc -l < "$COLLECT_OUT" | tr -d '[:space:]')"
if (( TOTAL == 0 )); then
    err "no tests collected"
    exit 1
fi

ARG_MAX=""
if command -v getconf >/dev/null 2>&1; then
    ARG_MAX="$(getconf ARG_MAX 2>/dev/null || true)"
fi
if [[ "$ARG_MAX" =~ ^[0-9]+$ ]]; then
    MAX_NODE_LEN="$(LC_ALL=C awk 'length > max { max = length } END { print max + 0 }' "$COLLECT_OUT")"
    BASE_PYTEST_ARGS=(-n auto --dist=load --no-header)
    if (( BENCH )); then
        BASE_PYTEST_ARGS+=(-q)
    fi
    BASE_ARGS_SIZE="$(arg_bytes "${PYTEST_CMD[@]}" "${BASE_PYTEST_ARGS[@]}" "${RUNTIME_PASSTHROUGH[@]}")"
    SAFETY_MARGIN=2048
    AVAILABLE=$(( ARG_MAX - BASE_ARGS_SIZE - SAFETY_MARGIN ))
    (( AVAILABLE < 0 )) && AVAILABLE=0
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
    RAW_START="$(tr -d '[:space:]' < "$CURSOR_FILE")"
    if [[ "$RAW_START" =~ ^[0-9]+$ ]]; then
        START="$RAW_START"
        (( START > TOTAL )) && START="$TOTAL"
        log "resuming from next test index: $START"
    else
        err "cursor file is invalid ('$RAW_START'); starting from 0"
        rm -f "$CURSOR_FILE"
    fi
fi

if (( START >= TOTAL )); then
    log "nothing to resume (cursor at end: $START/$TOTAL)"
    rm -f "$CURSOR_FILE"
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
    log "chunk $chunk_idx/$CHUNKS  tests $((i+1))..$end"

    PYTEST_FLAGS=(-n auto --dist=load)
    if (( BENCH )); then
        PYTEST_FLAGS+=(--no-header -q)
    else
        PYTEST_FLAGS+=(--no-header)
    fi

    if ! "${PYTEST_CMD[@]}" "${PYTEST_FLAGS[@]}" "${RUNTIME_PASSTHROUGH[@]}" "${CHUNK_NODES[@]}"; then
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
rm -f "$CURSOR_FILE"
log "all $TOTAL tests passed in $((T_END - T_START))s"
