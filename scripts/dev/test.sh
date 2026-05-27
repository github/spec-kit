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
#   * Persist the cursor (next chunk index) to
#     `.pytest_cache/fast-test-cursor` after every successful chunk so
#     `--resume` continues exactly where a crash left off.
#   * `--reset` clears the cursor; `--bench` reports wall-time only.
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

while (( $# )); do
    case "$1" in
        --chunk-size) CHUNK_SIZE="$2"; shift 2 ;;
        --resume)     RESUME=1; shift ;;
        --reset)      RESET=1;  shift ;;
        --bench)      BENCH=1;  shift ;;
        --)           shift; PASSTHROUGH+=("$@"); break ;;
        -h|--help)    sed -n '2,22p' "$0"; exit 0 ;;
        *)            PASSTHROUGH+=("$1"); shift ;;
    esac
done

if (( RESET )); then
    rm -f "$CURSOR_FILE"
    echo "[fast-test] cursor cleared"
    exit 0
fi

cd "$REPO_ROOT"
mkdir -p "$(dirname "$CURSOR_FILE")"

# 1. Collect node ids (override addopts so collection itself is serial/quiet).
echo "[fast-test] collecting tests ..."
mapfile -t NODES < <(
    uv run pytest -o addopts= --collect-only -q "${PASSTHROUGH[@]}" \
        2>/dev/null | grep -E '::' || true
)
TOTAL="${#NODES[@]}"
if (( TOTAL == 0 )); then
    echo "[fast-test] no tests collected" >&2
    exit 1
fi

# 2. Determine starting cursor.
START=0
if (( RESUME )) && [[ -f "$CURSOR_FILE" ]]; then
    START="$(cat "$CURSOR_FILE")"
    echo "[fast-test] resuming from chunk cursor: test #$START"
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

    PYTEST_FLAGS=(-o addopts= -n auto --dist=load --tb=short)
    (( BENCH )) && PYTEST_FLAGS+=(-q) || PYTEST_FLAGS+=(--no-header -q)

    if ! uv run pytest "${PYTEST_FLAGS[@]}" "${NODES[@]:i:CHUNK_SIZE}"; then
        echo "[fast-test] chunk failed — cursor preserved at test #$i (use --resume to retry)"
        echo "$i" > "$CURSOR_FILE"
        exit 1
    fi

    i="$end"
    echo "$i" > "$CURSOR_FILE"
done

T_END=$(date +%s)
rm -f "$CURSOR_FILE"
echo "[fast-test] all $TOTAL tests passed in $((T_END - T_START))s"
