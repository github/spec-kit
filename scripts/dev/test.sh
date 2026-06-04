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
#     `.pytest_cache/fast-test-cursor` after every successful chunk so
#     `--resume` continues from the last completed chunk.
#   * `--reset` clears the cursor; `--bench` reduces pytest output (progress still prints).
#
# Usage:
#   scripts/dev/test.sh                          # full suite, chunked
#   scripts/dev/test.sh --chunk-size 100
#   scripts/dev/test.sh --resume                 # continue from cursor
#   scripts/dev/test.sh --reset                  # clear cursor
#   scripts/dev/test.sh --bench                  # time only, no -v
#   scripts/dev/test.sh -- tests/test_merge.py   # pass-through to pytest

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CURSOR_FILE="$REPO_ROOT/.pytest_cache/fast-test-cursor"

CHUNK_SIZE=200
RESUME=0
RESET=0
BENCH=0
PASSTHROUGH=()
RUNTIME_PASSTHROUGH=()

while (( $# )); do
    case "$1" in
        --chunk-size)
            if (( $# < 2 )); then
                echo "[fast-test] --chunk-size requires a value" >&2
                exit 1
            fi
            CHUNK_SIZE="$2"
            shift 2
            ;;
        --resume)     RESUME=1; shift ;;
        --reset)      RESET=1;  shift ;;
        --bench)      BENCH=1;  shift ;;
        --)           shift; PASSTHROUGH+=("$@"); break ;;
        -h|--help)    sed -n '2,22p' "$0"; exit 0 ;;
        *)            PASSTHROUGH+=("$1"); shift ;;
    esac
done

if ! [[ "$CHUNK_SIZE" =~ ^[1-9][0-9]*$ ]]; then
    echo "[fast-test] --chunk-size must be a positive integer (got '$CHUNK_SIZE')" >&2
    exit 1
fi

# Collection and execution do not share every pytest flag. Keep runtime
# passthrough aligned with user intent while stripping collect-only toggles.
for arg in "${PASSTHROUGH[@]}"; do
    case "$arg" in
        --collect-only|--co) ;;
        *) RUNTIME_PASSTHROUGH+=("$arg") ;;
    esac
done

if (( RESET )); then
    rm -f "$CURSOR_FILE"
    echo "[fast-test] cursor cleared"
    exit 0
fi

cd "$REPO_ROOT"
mkdir -p "$(dirname "$CURSOR_FILE")"

# 1. Collect node ids.
echo "[fast-test] collecting tests ..."
COLLECT_ERR="$(mktemp)"
COLLECT_OUT="$(mktemp)"
if ! uv run pytest --collect-only -q "${PASSTHROUGH[@]}" >"$COLLECT_OUT" 2>"$COLLECT_ERR"; then
    echo "[fast-test] test collection failed" >&2
    [[ -s "$COLLECT_ERR" ]] && { echo "--- collection stderr ---"; cat "$COLLECT_ERR"; } >&2
    rm -f "$COLLECT_ERR" "$COLLECT_OUT"
    exit 1
fi
NODES=()
while IFS= read -r node; do
    NODES+=("$node")
done < <(grep -E '::' "$COLLECT_OUT" || true)
rm -f "$COLLECT_ERR" "$COLLECT_OUT"
TOTAL="${#NODES[@]}"
if (( TOTAL == 0 )); then
    echo "[fast-test] no tests collected" >&2
    exit 1
fi

# 2. Determine starting cursor.
START=0
if (( RESUME )) && [[ -f "$CURSOR_FILE" ]]; then
    RAW_START="$(tr -d '[:space:]' < "$CURSOR_FILE")"
    if [[ "$RAW_START" =~ ^[0-9]+$ ]]; then
        START="$RAW_START"
        (( START > TOTAL )) && START="$TOTAL"
        echo "[fast-test] resuming from next test index: $START"
    else
        echo "[fast-test] cursor file is invalid ('$RAW_START'); starting from 0" >&2
    fi
fi

if (( START >= TOTAL )); then
    echo "[fast-test] nothing to resume (cursor at end: $START/$TOTAL)"
    rm -f "$CURSOR_FILE"
    exit 0
fi

CHUNKS=$(( (TOTAL - START + CHUNK_SIZE - 1) / CHUNK_SIZE ))
echo "[fast-test] $TOTAL tests · chunk=$CHUNK_SIZE · $CHUNKS chunk(s) queued · workers=auto"

# 3. FIFO dispatch.
T_START=$(date +%s)
i="$START"
chunk_idx=0
while (( i < TOTAL )); do
    end=$(( i + CHUNK_SIZE ))
    (( end > TOTAL )) && end="$TOTAL"
    chunk_idx=$(( chunk_idx + 1 ))
    echo "[fast-test] chunk $chunk_idx/$CHUNKS  tests $((i+1))..$end"

    PYTEST_FLAGS=(-n auto --dist=load)
    (( BENCH )) && PYTEST_FLAGS+=(-q) || PYTEST_FLAGS+=(--no-header -q)

    if ! uv run pytest "${PYTEST_FLAGS[@]}" "${RUNTIME_PASSTHROUGH[@]}" "${NODES[@]:i:CHUNK_SIZE}"; then
        echo "[fast-test] chunk failed — cursor preserved at next test index $i (use --resume to retry)"
        echo "$i" > "$CURSOR_FILE"
        exit 1
    fi

    i="$end"
    echo "$i" > "$CURSOR_FILE"
done

T_END=$(date +%s)
rm -f "$CURSOR_FILE"
echo "[fast-test] all $TOTAL tests passed in $((T_END - T_START))s"
