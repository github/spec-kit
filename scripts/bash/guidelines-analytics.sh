#!/usr/bin/env bash
# shellcheck disable=SC2155,SC2086

##############################################################################
# Guidelines Analytics Dashboard
# Part of Spec Kit Phase 4: Advanced Features
#
# Purpose: Track compliance metrics across projects and over time
# Usage: ./guidelines-analytics.sh [--output=<format>] [--history]
#
# Features:
#   - Compliance score calculation
#   - Trend tracking over time
#   - Metrics visualization (ASCII charts)
#   - Multi-project comparison
#   - Export for reporting
##############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(pwd)"
GUIDELINES_DIR="${PROJECT_ROOT}/.guidelines"
ANALYTICS_DIR="${PROJECT_ROOT}/.guidelines-analytics"
HISTORY_FILE="${ANALYTICS_DIR}/compliance-history.json"
OUTPUT_FORMAT="dashboard"  # dashboard, json, csv

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "${BOLD}$1${NC}"
    echo "$(printf '=%.0s' {1..80})"
}

print_section() {
    echo ""
    echo -e "${BLUE}$1${NC}"
    echo "$(printf '-%.0s' {1..80})"
}

##############################################################################
# Metrics Collection
##############################################################################

collect_compliance_metrics() {
    local metrics_file="${ANALYTICS_DIR}/current-metrics.json"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Run compliance check and capture output
    local compliance_json=""
    if [ -x "$(dirname "$0")/check-guidelines-compliance.sh" ]; then
        compliance_json=$(bash "$(dirname "$0")/check-guidelines-compliance.sh" --output=json 2>/dev/null || echo "{}")
    else
        echo "{\"error\": \"Compliance checker not found\"}"
        return 1
    fi

    # Extract metrics
    local critical=$(echo "$compliance_json" | jq -r '.summary.critical // 0' 2>/dev/null || echo "0")
    local high=$(echo "$compliance_json" | jq -r '.summary.high // 0' 2>/dev/null || echo "0")
    local medium=$(echo "$compliance_json" | jq -r '.summary.medium // 0' 2>/dev/null || echo "0")
    local low=$(echo "$compliance_json" | jq -r '.summary.low // 0' 2>/dev/null || echo "0")
    local status=$(echo "$compliance_json" | jq -r '.status // "UNKNOWN"' 2>/dev/null || echo "UNKNOWN")

    # Calculate compliance score (0-100)
    # Formula: 100 - (CRITICAL*10 + HIGH*5 + MEDIUM*2 + LOW*1)
    local score=$((100 - (critical * 10 + high * 5 + medium * 2 + low * 1)))
    if [ $score -lt 0 ]; then
        score=0
    fi

    # Create metrics JSON
    cat > "$metrics_file" <<EOF
{
  "timestamp": "$timestamp",
  "project": "$(basename "$PROJECT_ROOT")",
  "compliance_score": $score,
  "violations": {
    "critical": $critical,
    "high": $high,
    "medium": $medium,
    "low": $low
  },
  "status": "$status"
}
EOF

    echo "$metrics_file"
}

save_to_history() {
    local metrics_file="$1"

    # Create analytics directory if it doesn't exist
    if [ ! -d "$ANALYTICS_DIR" ]; then
        mkdir -p "$ANALYTICS_DIR"
    fi

    # Initialize history file if it doesn't exist
    if [ ! -f "$HISTORY_FILE" ]; then
        echo "{\"version\": \"1.0\", \"entries\": []}" > "$HISTORY_FILE"
    fi

    # Append current metrics to history
    local current_metrics=$(cat "$metrics_file")
    local updated_history=$(jq ".entries += [$current_metrics]" "$HISTORY_FILE" 2>/dev/null)

    echo "$updated_history" > "$HISTORY_FILE"
}

##############################################################################
# Visualization Functions
##############################################################################

draw_ascii_bar() {
    local value=$1
    local max=${2:-100}
    local width=${3:-50}

    local filled=$(( (value * width) / max ))
    if [ $filled -lt 0 ]; then
        filled=0
    fi
    if [ $filled -gt $width ]; then
        filled=$width
    fi

    # Color based on value
    local color=$GREEN
    if [ $value -lt 50 ]; then
        color=$RED
    elif [ $value -lt 75 ]; then
        color=$YELLOW
    fi

    printf "${color}"
    printf '█%.0s' $(seq 1 $filled)
    printf "${NC}"
    printf '░%.0s' $(seq 1 $((width - filled)))
    printf " %d%%" $value
}

draw_sparkline() {
    local -a values=("$@")
    local chars=("▁" "▂" "▃" "▄" "▅" "▆" "▇" "█")

    # Find min and max
    local min=${values[0]}
    local max=${values[0]}

    for val in "${values[@]}"; do
        if [ $val -lt $min ]; then
            min=$val
        fi
        if [ $val -gt $max ]; then
            max=$val
        fi
    done

    local range=$((max - min))
    if [ $range -eq 0 ]; then
        range=1
    fi

    # Draw sparkline
    for val in "${values[@]}"; do
        local normalized=$(( ((val - min) * 7) / range ))
        printf "%s" "${chars[$normalized]}"
    done
}

##############################################################################
# Dashboard Generation
##############################################################################

generate_dashboard() {
    print_header "Guidelines Compliance Analytics Dashboard"

    echo "Project: $(basename "$PROJECT_ROOT")"
    echo "Generated: $(date)"
    echo ""

    # Collect current metrics
    local metrics_file=$(collect_compliance_metrics)

    if [ ! -f "$metrics_file" ]; then
        echo -e "${RED}Error: Could not collect metrics${NC}"
        return 1
    fi

    local current_metrics=$(cat "$metrics_file")

    # Extract values
    local score=$(echo "$current_metrics" | jq -r '.compliance_score')
    local critical=$(echo "$current_metrics" | jq -r '.violations.critical')
    local high=$(echo "$current_metrics" | jq -r '.violations.high')
    local medium=$(echo "$current_metrics" | jq -r '.violations.medium')
    local low=$(echo "$current_metrics" | jq -r '.violations.low')
    local status=$(echo "$current_metrics" | jq -r '.status')

    # Current Status
    print_section "Current Compliance Status"

    echo -e "${BOLD}Overall Score:${NC} $score/100"
    echo "  "
    draw_ascii_bar $score 100 40
    echo ""
    echo ""

    # Status indicator
    local status_color=$GREEN
    local status_icon="✓"
    if [ "$status" = "FAILED" ]; then
        status_color=$RED
        status_icon="✗"
    elif [ "$status" = "WARNING" ]; then
        status_color=$YELLOW
        status_icon="⚠"
    fi

    echo -e "${BOLD}Status:${NC} ${status_color}${status_icon} $status${NC}"
    echo ""

    # Violations breakdown
    print_section "Violations Breakdown"

    printf "%-12s %5s  " "CRITICAL" "$critical"
    draw_ascii_bar $critical 20 30
    echo ""

    printf "%-12s %5s  " "HIGH" "$high"
    draw_ascii_bar $high 20 30
    echo ""

    printf "%-12s %5s  " "MEDIUM" "$medium"
    draw_ascii_bar $medium 20 30
    echo ""

    printf "%-12s %5s  " "LOW" "$low"
    draw_ascii_bar $low 20 30
    echo ""

    # Historical trend (if available)
    if [ -f "$HISTORY_FILE" ]; then
        local entry_count=$(jq '.entries | length' "$HISTORY_FILE" 2>/dev/null || echo "0")

        if [ $entry_count -gt 1 ]; then
            print_section "Historical Trend (Last 30 Days)"

            # Get scores from history
            local scores=$(jq -r '.entries[-30:] | .[].compliance_score' "$HISTORY_FILE" 2>/dev/null | tr '\n' ' ')
            local -a score_array=($scores)

            if [ ${#score_array[@]} -gt 0 ]; then
                echo "Compliance Score: $(draw_sparkline "${score_array[@]}")"

                # Calculate trend
                local first_score=${score_array[0]}
                local last_score=${score_array[-1]}
                local trend=$((last_score - first_score))

                if [ $trend -gt 0 ]; then
                    echo -e "Trend: ${GREEN}↑ +${trend} (improving)${NC}"
                elif [ $trend -lt 0 ]; then
                    echo -e "Trend: ${RED}↓ ${trend} (declining)${NC}"
                else
                    echo -e "Trend: ${BLUE}→ 0 (stable)${NC}"
                fi

                # Show date range
                local first_date=$(jq -r '.entries[-30] | .timestamp' "$HISTORY_FILE" 2>/dev/null | cut -d'T' -f1)
                local last_date=$(jq -r '.entries[-1] | .timestamp' "$HISTORY_FILE" 2>/dev/null | cut -d'T' -f1)
                echo "Period: $first_date to $last_date ($entry_count entries)"
            fi
        fi
    fi

    # Recommendations
    print_section "Recommendations"

    if [ $critical -gt 0 ]; then
        echo -e "${RED}🔴 URGENT: Fix $critical CRITICAL violation(s)${NC}"
    fi

    if [ $high -gt 0 ]; then
        echo -e "${YELLOW}🟡 PRIORITY: Fix $high HIGH severity violation(s)${NC}"
    fi

    if [ $score -ge 90 ]; then
        echo -e "${GREEN}✓ Excellent compliance! Keep up the good work.${NC}"
    elif [ $score -ge 75 ]; then
        echo -e "${BLUE}→ Good compliance. Address medium/low issues for improvement.${NC}"
    elif [ $score -ge 50 ]; then
        echo -e "${YELLOW}⚠ Moderate compliance. Focus on high-priority violations.${NC}"
    else
        echo -e "${RED}⚠ Low compliance. Immediate action required.${NC}"
    fi

    # Quick actions
    print_section "Quick Actions"

    echo "1. Review violations:    ./scripts/bash/check-guidelines-compliance.sh"
    echo "2. Auto-fix issues:      ./scripts/bash/autofix-guidelines.sh"
    echo "3. Compare guidelines:   ./scripts/bash/diff-guidelines.sh"
    echo "4. Update history:       ./scripts/bash/guidelines-analytics.sh --save-history"
}

generate_json_report() {
    local metrics_file=$(collect_compliance_metrics)
    cat "$metrics_file"
}

generate_csv_report() {
    if [ ! -f "$HISTORY_FILE" ]; then
        echo "timestamp,project,score,critical,high,medium,low,status"
        return 0
    fi

    echo "timestamp,project,score,critical,high,medium,low,status"

    jq -r '.entries[] | [.timestamp, .project, .compliance_score, .violations.critical, .violations.high, .violations.medium, .violations.low, .status] | @csv' "$HISTORY_FILE" 2>/dev/null
}

##############################################################################
# Main Execution
##############################################################################

show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --output=FORMAT       Output format: dashboard (default), json, csv
  --save-history        Save current metrics to history file
  --show-history        Show historical data
  --help                Show this help message

Examples:
  $0                          # Show dashboard
  $0 --save-history           # Record current metrics
  $0 --output=json            # Export as JSON
  $0 --output=csv > report.csv  # Export as CSV

Analytics Files:
  History: .guidelines-analytics/compliance-history.json
  Current: .guidelines-analytics/current-metrics.json
EOF
}

main() {
    local save_history=false
    local show_history=false

    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --output=*)
                OUTPUT_FORMAT="${arg#*=}"
                ;;
            --save-history)
                save_history=true
                ;;
            --show-history)
                show_history=true
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $arg" >&2
                show_usage
                exit 3
                ;;
        esac
    done

    # Create analytics directory if needed
    if [ ! -d "$ANALYTICS_DIR" ]; then
        mkdir -p "$ANALYTICS_DIR"
    fi

    # Save to history if requested
    if [ "$save_history" = true ]; then
        local metrics_file=$(collect_compliance_metrics)
        save_to_history "$metrics_file"
        echo "Metrics saved to history: $HISTORY_FILE"
        exit 0
    fi

    # Generate output based on format
    case "$OUTPUT_FORMAT" in
        json)
            generate_json_report
            ;;
        csv)
            generate_csv_report
            ;;
        dashboard|*)
            generate_dashboard
            ;;
    esac
}

# Check for jq dependency
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed" >&2
    echo "Install: sudo apt-get install jq (Linux) or brew install jq (Mac)" >&2
    exit 3
fi

# Run main function
main "$@"
