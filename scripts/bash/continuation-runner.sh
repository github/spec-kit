#!/usr/bin/env bash
# Advances a script continuation one hop (#4551).
#
# Consumes the head of SPECKIT_SCRIPT_CONTINUATION — a newline-delimited
# list of the remaining script layers below the one that just called
# $CORE_SCRIPT, highest priority first — and execs into it. If more
# layers remain after that hop, the reduced list is re-exported so that,
# if the next layer is itself a "wrap" script, its own $CORE_SCRIPT call
# (which always points back at this same file) continues the chain
# correctly. If nothing remains, the next layer is the terminating
# "replace" layer and SPECKIT_SCRIPT_CONTINUATION is unset for it, since
# a replace layer never references $CORE_SCRIPT.
#
# Deliberately portable to bash 3.2 (macOS's system bash): no mapfile,
# no ^^ case expansion, no associative arrays.
set -e

if [[ -z "${SPECKIT_SCRIPT_CONTINUATION:-}" ]]; then
    echo "ERROR: continuation-runner invoked with no remaining script layers (SPECKIT_SCRIPT_CONTINUATION is unset)" >&2
    exit 1
fi

__speckit_remaining=()
while IFS= read -r __speckit_line; do
    # Strip a trailing \r defensively (CRLF content from a Windows
    # producer), same as the dispatcher stub does at the source.
    __speckit_line="${__speckit_line%$'\r'}"
    [[ -n "$__speckit_line" ]] && __speckit_remaining+=("$__speckit_line")
done <<< "$SPECKIT_SCRIPT_CONTINUATION"

if [[ ${#__speckit_remaining[@]} -eq 0 ]]; then
    echo "ERROR: continuation-runner found no remaining script layers to run" >&2
    exit 1
fi

__speckit_next="${__speckit_remaining[0]}"

if [[ ${#__speckit_remaining[@]} -gt 1 ]]; then
    SPECKIT_SCRIPT_CONTINUATION=$(printf '%s\n' "${__speckit_remaining[@]:1}")
    export SPECKIT_SCRIPT_CONTINUATION
else
    unset SPECKIT_SCRIPT_CONTINUATION
fi

exec "$__speckit_next" "$@"
