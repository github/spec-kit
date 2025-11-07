#!/usr/bin/env bash

set -e

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo ""
            echo "Options:"
            echo "  --json      Output in JSON format"
            echo "  --help, -h  Show this help message"
            echo ""
            echo "Description:"
            echo "  Estimates token usage for the current session based on file sizes"
            echo "  and provides recommendations for token optimization."
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Get repository root
REPO_ROOT=$(get_repo_root)
SPECS_DIR="$REPO_ROOT/specs"
CONSTITUTION_FILE="$REPO_ROOT/memory/constitution.md"

# Default budget for Claude Sonnet
TOTAL_BUDGET=200000

# Function to estimate tokens from file size
estimate_tokens() {
    local file_path="$1"
    local file_type="$2"

    if [ ! -f "$file_path" ]; then
        echo "0"
        return
    fi

    # Get file size in bytes
    local bytes=$(wc -c < "$file_path" 2>/dev/null || echo "0")

    # Estimate characters (roughly 1 byte = 1 char for ASCII/UTF-8)
    local chars=$bytes

    # Convert to tokens: chars / 4 * multiplier
    # Base: 1 token ≈ 4 characters
    local base_tokens=$((chars / 4))

    # Apply multipliers based on file type
    case "$file_type" in
        markdown)
            # Markdown has formatting overhead
            echo $((base_tokens * 11 / 10))  # 1.1x multiplier
            ;;
        code)
            # Code files are dense
            echo $base_tokens  # 1.0x multiplier
            ;;
        json)
            # JSON is structured/compressed in context
            echo $((base_tokens * 9 / 10))  # 0.9x multiplier
            ;;
        *)
            echo $base_tokens  # Default 1.0x
            ;;
    esac
}

# Estimate tokens for specs
SPECS_TOKENS=0
SPEC_BREAKDOWN=""
if [ -d "$SPECS_DIR" ]; then
    while IFS= read -r spec_dir; do
        spec_name=$(basename "$spec_dir")
        spec_total=0

        # spec.md
        if [ -f "$spec_dir/spec.md" ]; then
            tokens=$(estimate_tokens "$spec_dir/spec.md" "markdown")
            spec_total=$((spec_total + tokens))
        fi

        # plan.md (weight: 0.9, often partially referenced)
        if [ -f "$spec_dir/plan.md" ]; then
            tokens=$(estimate_tokens "$spec_dir/plan.md" "markdown")
            tokens=$((tokens * 9 / 10))
            spec_total=$((spec_total + tokens))
        fi

        # tasks.md (weight: 0.8, scanned not fully read)
        if [ -f "$spec_dir/tasks.md" ]; then
            tokens=$(estimate_tokens "$spec_dir/tasks.md" "markdown")
            tokens=$((tokens * 8 / 10))
            spec_total=$((spec_total + tokens))
        fi

        # ai-doc.md
        if [ -f "$spec_dir/ai-doc.md" ]; then
            tokens=$(estimate_tokens "$spec_dir/ai-doc.md" "markdown")
            spec_total=$((spec_total + tokens))
        fi

        # quick-ref.md
        if [ -f "$spec_dir/quick-ref.md" ]; then
            tokens=$(estimate_tokens "$spec_dir/quick-ref.md" "markdown")
            spec_total=$((spec_total + tokens))
        fi

        SPECS_TOKENS=$((SPECS_TOKENS + spec_total))

        if [ $spec_total -gt 0 ]; then
            SPEC_BREAKDOWN="$SPEC_BREAKDOWN,\"$spec_name\": $spec_total"
        fi
    done < <(find "$SPECS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort)
fi

# Remove leading comma from spec breakdown
SPEC_BREAKDOWN="${SPEC_BREAKDOWN#,}"

# Estimate constitution tokens
CONSTITUTION_TOKENS=0
if [ -f "$CONSTITUTION_FILE" ]; then
    CONSTITUTION_TOKENS=$(estimate_tokens "$CONSTITUTION_FILE" "markdown")
fi

# Estimate conversation tokens (rough heuristic)
# This is hard to estimate accurately - we use a baseline
# In a real session, this would need integration with the AI agent
# For now, use a baseline of 20K as starting estimate
CONVERSATION_TOKENS=20000

# Estimate code context (if any code files were recently read)
# This is also a rough estimate - in practice would need AI integration
CODE_CONTEXT_TOKENS=0

# Calculate session total
SESSION_TOKENS=$((CONVERSATION_TOKENS + SPECS_TOKENS + CONSTITUTION_TOKENS + CODE_CONTEXT_TOKENS))
REMAINING_TOKENS=$((TOTAL_BUDGET - SESSION_TOKENS))
USAGE_PERCENT=$((SESSION_TOKENS * 100 / TOTAL_BUDGET))

# Determine status
if [ $USAGE_PERCENT -lt 40 ]; then
    STATUS="healthy"
    STATUS_ICON="✓"
elif [ $USAGE_PERCENT -lt 60 ]; then
    STATUS="moderate"
    STATUS_ICON="⚠️"
elif [ $USAGE_PERCENT -lt 80 ]; then
    STATUS="high"
    STATUS_ICON="⚠️"
else
    STATUS="critical"
    STATUS_ICON="🚨"
fi

# Generate recommendations
RECOMMENDATIONS=()
if [ $USAGE_PERCENT -lt 40 ]; then
    RECOMMENDATIONS+=("You have plenty of budget remaining")
    RECOMMENDATIONS+=("Safe to proceed with planning and implementation")
    RECOMMENDATIONS+=("No optimization needed at this stage")
elif [ $USAGE_PERCENT -lt 60 ]; then
    RECOMMENDATIONS+=("Moderate token usage detected")
    RECOMMENDATIONS+=("Consider using quick-ref.md instead of full ai-doc.md (saves ~2K per feature)")
    RECOMMENDATIONS+=("Use /speckit.analyze --summary for quick checks (90% faster)")
    RECOMMENDATIONS+=("Continue monitoring usage")
elif [ $USAGE_PERCENT -lt 80 ]; then
    RECOMMENDATIONS+=("High token usage - optimization recommended")
    RECOMMENDATIONS+=("Run /speckit.prune to compress session (saves 40-60K tokens)")
    RECOMMENDATIONS+=("Use /speckit.analyze --incremental (70-90% faster)")
    RECOMMENDATIONS+=("Load only essential specs/docs")
    RECOMMENDATIONS+=("Budget may be tight for implementation")
else
    RECOMMENDATIONS+=("CRITICAL: Token budget nearly exhausted")
    RECOMMENDATIONS+=("IMMEDIATE: Run /speckit.prune NOW to free up space")
    RECOMMENDATIONS+=("Use summary modes for all analysis")
    RECOMMENDATIONS+=("Consider starting fresh session for implementation")
    RECOMMENDATIONS+=("Estimated remaining capacity: 1-2 major operations")
fi

# Format numbers with K suffix
format_tokens() {
    local num=$1
    if [ $num -ge 1000 ]; then
        echo "$((num / 1000))K"
    else
        echo "$num"
    fi
}

# Output results
if [ "$JSON_MODE" = true ]; then
    # JSON output
    cat <<EOF
{
  "session_tokens": $SESSION_TOKENS,
  "total_budget": $TOTAL_BUDGET,
  "remaining_tokens": $REMAINING_TOKENS,
  "usage_percentage": $USAGE_PERCENT,
  "breakdown": {
    "conversation": $CONVERSATION_TOKENS,
    "specs": {$SPEC_BREAKDOWN},
    "constitution": $CONSTITUTION_TOKENS,
    "code_context": $CODE_CONTEXT_TOKENS
  },
  "status": "$STATUS",
  "recommendations": [
$(IFS=$'\n'; echo "${RECOMMENDATIONS[*]}" | sed 's/^/    "/' | sed 's/$/"/' | sed '$!s/$/,/')
  ]
}
EOF
else
    # Human-readable output
    echo "Token Budget Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Current Session: ~$(format_tokens $SESSION_TOKENS) tokens used"
    echo "Remaining: ~$(format_tokens $REMAINING_TOKENS) tokens ($((100 - USAGE_PERCENT))% available)"
    echo ""
    echo "Breakdown:"
    echo "  Conversation: $(format_tokens $CONVERSATION_TOKENS) (estimated)"

    if [ $SPECS_TOKENS -gt 0 ]; then
        echo "  Specifications: $(format_tokens $SPECS_TOKENS)"
        while IFS= read -r spec_dir; do
            spec_name=$(basename "$spec_dir")
            # Calculate this spec's tokens again for display
            spec_total=0
            [ -f "$spec_dir/spec.md" ] && spec_total=$((spec_total + $(estimate_tokens "$spec_dir/spec.md" "markdown")))
            [ -f "$spec_dir/plan.md" ] && spec_total=$((spec_total + $(estimate_tokens "$spec_dir/plan.md" "markdown") * 9 / 10))
            [ -f "$spec_dir/tasks.md" ] && spec_total=$((spec_total + $(estimate_tokens "$spec_dir/tasks.md" "markdown") * 8 / 10))
            [ -f "$spec_dir/ai-doc.md" ] && spec_total=$((spec_total + $(estimate_tokens "$spec_dir/ai-doc.md" "markdown")))
            [ -f "$spec_dir/quick-ref.md" ] && spec_total=$((spec_total + $(estimate_tokens "$spec_dir/quick-ref.md" "markdown")))
            [ $spec_total -gt 0 ] && echo "    • $spec_name: $(format_tokens $spec_total)"
        done < <(find "$SPECS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort)
    fi

    [ $CONSTITUTION_TOKENS -gt 0 ] && echo "  Constitution: $(format_tokens $CONSTITUTION_TOKENS)"
    [ $CODE_CONTEXT_TOKENS -gt 0 ] && echo "  Code context: $(format_tokens $CODE_CONTEXT_TOKENS)"

    echo ""
    echo "Status: $STATUS_ICON $STATUS"

    echo ""
    if [ $USAGE_PERCENT -lt 40 ]; then
        echo "💡 Recommendations:"
    elif [ $USAGE_PERCENT -lt 60 ]; then
        echo "💡 Recommendations:"
    elif [ $USAGE_PERCENT -lt 80 ]; then
        echo "⚠️  Recommendations:"
    else
        echo "🚨 IMMEDIATE ACTIONS REQUIRED:"
    fi

    for rec in "${RECOMMENDATIONS[@]}"; do
        echo "  • $rec"
    done

    # Show optimization options if usage is moderate or higher
    if [ $USAGE_PERCENT -ge 40 ]; then
        echo ""
        echo "🔧 Optimization Options:"
        [ $USAGE_PERCENT -ge 60 ] && echo "  /speckit.prune              - Compress session (save ~40-50K tokens)"
        echo "  /speckit.analyze --summary  - Quick analysis (90% faster)"
        echo "  /speckit.analyze --incremental - Smart analysis (70% faster)"
        echo ""
        echo "  Load quick refs:"
        while IFS= read -r spec_dir; do
            spec_name=$(basename "$spec_dir")
            [ -f "$spec_dir/quick-ref.md" ] && echo "    cat specs/$spec_name/quick-ref.md (~200 tokens)"
        done < <(find "$SPECS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -3)
    fi
fi
