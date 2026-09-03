#!/usr/bin/env bash
# Compose multiple evaluator results with deterministic precedence.
#
# Usage:
#   compose-results.sh --results-dir <path> --phase <phase> [--strategy strict|majority|optimistic] [--output <path>]
#
# Reads evaluator result JSON files from a results directory and produces a
# composed result. Requires `jq` for JSON processing.

set -euo pipefail

RESULTS_DIR=""
PHASE=""
STRATEGY="strict"
OUTPUT=""

usage() {
    cat <<EOF
Usage: $0 --results-dir <path> --phase <phase> [--strategy strict|majority|optimistic] [--output <path>]

Compose multiple evaluator results with deterministic precedence.

Options:
  --results-dir <path>   Directory containing evaluator result JSON files.
  --phase <phase>        Lifecycle phase to compose results for (e.g., after_plan).
  --strategy <strategy>  Composition strategy: strict (default), majority, or optimistic.
  --output <path>        Write composed result to this file instead of stdout.
EOF
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --results-dir) RESULTS_DIR="$2"; shift 2 ;;
        --phase) PHASE="$2"; shift 2 ;;
        --strategy) STRATEGY="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        *) usage ;;
    esac
done

if [[ -z "$RESULTS_DIR" || -z "$PHASE" ]]; then
    echo "Error: --results-dir and --phase are required." >&2
    usage
fi

if [[ ! -d "$RESULTS_DIR" ]]; then
    echo "Error: results directory not found: $RESULTS_DIR" >&2
    exit 1
fi

# Check for jq
if ! command -v jq &>/dev/null; then
    echo "Error: jq is required but not installed." >&2
    exit 1
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Collect result files for the phase (exclude previously composed files)
# Portable to bash 3.2+ (macOS): avoid mapfile (bash 4+)
RESULT_FILES=()
while IFS= read -r f; do
    RESULT_FILES+=("$f")
done < <(find "$RESULTS_DIR" -maxdepth 1 -name "*-${PHASE}-*.json" ! -name "composed-*" | sort)

if [[ ${#RESULT_FILES[@]} -eq 0 ]]; then
    # No results found — produce empty composed result
    COMPOSED=$(jq -n \
        --arg phase "$PHASE" \
        --arg strategy "$STRATEGY" \
        --arg ts "$TIMESTAMP" \
        '{
            schema_version: "1.0",
            evaluator: { id: "composed", version: "1.0", name: "Composed (\($strategy))" },
            phase: $phase,
            outcome: "pass",
            summary: "No evaluator results found for this phase.",
            findings: [],
            next_action: { kind: "pass", target_phase: null, message: "No evaluator results found." },
            metadata: {
                timestamp: $ts,
                duration_ms: 0,
                artifacts_evaluated: [],
                deterministic: true,
                evaluator_count: 0,
                contradictory_findings: [],
                composition_strategy: $strategy,
                evaluator_results: []
            },
            state: {}
        }')
else
    # Build a jq filter that merges all result files
    # Strategy: read all files into an array, then apply composition logic
    JQ_FILTER='def severity_order($s):
        if $s == "critical" then 0
        elif $s == "high" then 1
        elif $s == "medium" then 2
        elif $s == "low" then 3
        else 4 end;

    def resolve_outcome(outcomes; strategy):
        if strategy == "optimistic" then
            if outcomes | index("pass") then "pass"
            elif outcomes | index("warn") then "warn"
            elif outcomes | index("clarify") then "clarify"
            elif outcomes | index("iterate") then "iterate"
            elif outcomes | index("gather_evidence") then "gather_evidence"
            else "block" end
        elif strategy == "majority" then
            (outcomes | group_by(.) | sort_by([-(length),
                if .[0] == "block" then 0
                elif .[0] == "gather_evidence" then 1
                elif .[0] == "iterate" then 2
                elif .[0] == "clarify" then 3
                elif .[0] == "warn" then 4
                else 5 end]) | .[0][0])
        else
            if outcomes | index("block") then "block"
            elif outcomes | index("gather_evidence") then "gather_evidence"
            elif outcomes | index("iterate") then "iterate"
            elif outcomes | index("clarify") then "clarify"
            elif outcomes | index("warn") then "warn"
            else "pass" end
        end;

    . as $results
    | ($results | map(.outcome)) as $outcomes
    | ($results | map(.findings // []) | flatten) as $all_findings
    | resolve_outcome($outcomes; $STRATEGY) as $composed_outcome
    | {
        schema_version: "1.0",
        evaluator: { id: "composed", version: "1.0", name: "Composed (\($STRATEGY))" },
        phase: $PHASE,
        outcome: $composed_outcome,
        summary: "\($results | length) evaluator(s) ran. \($all_findings | length) finding(s) total.",
        findings: $all_findings | sort_by(severity_order(.severity)),
        next_action: { kind: $composed_outcome, target_phase: null, message: "Composed outcome: \($composed_outcome)." },
        metadata: {
            timestamp: $TIMESTAMP,
            duration_ms: 0,
            artifacts_evaluated: [],
            deterministic: true,
            evaluator_count: $results | length,
            contradictory_findings: ([$all_findings[] | {
                subject: .subject,
                kind: .kind,
                id: .id,
                evidence_refs: (.evidence_refs // [])
            }] | group_by(.subject) | map(select(length > 1)) | map({
                subject: .[0].subject,
                finding_ids: [.[].id],
                description: ("Conflicting findings on subject \(.[0].subject)")
            })),
            composition_strategy: $STRATEGY,
            evaluator_results: $results | map({ evaluator_id: .evaluator.id, outcome: .outcome, findings_count: (.findings // [] | length) })
        },
        state: $results | map({ key: .evaluator.id, value: (.state // {}) }) | from_entries
    }'

    COMPOSED=$(for f in "${RESULT_FILES[@]}"; do cat "$f"; done | jq -s "$JQ_FILTER" \
        --arg PHASE "$PHASE" \
        --arg STRATEGY "$STRATEGY" \
        --arg TIMESTAMP "$TIMESTAMP")
fi

if [[ -n "$OUTPUT" ]]; then
    mkdir -p "$(dirname "$OUTPUT")"
    echo "$COMPOSED" > "$OUTPUT"
    echo "Composed result written to $OUTPUT"
else
    echo "$COMPOSED"
fi
