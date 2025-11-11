#!/usr/bin/env bash

#
# check-artifactory.sh - Query Artifactory for library availability
#
# Usage:
#   ./check-artifactory.sh <artifactory-url> <library-name> [api-key]
#
# Returns:
#   Exit 0: Library found (prints download URL)
#   Exit 1: Library not found
#   Exit 2: Authentication error
#   Exit 3: API error (network, timeout, etc.)
#   Exit 4: Artifactory URL not configured (skip check)
#

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Show help if requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<EOF
Usage: $(basename "$0") <artifactory-url> <library-name> [api-key]

Query Artifactory for library availability.

Arguments:
  artifactory-url    URL of the Artifactory instance (e.g., https://artifactory.company.com/api)
  library-name       Name of the library to check (e.g., axios, lodash, jackson-databind)
  api-key           Optional API key for authentication (or set ARTIFACTORY_API_KEY env var)

Exit Codes:
  0  Library found (prints download URL)
  1  Library not found (not whitelisted)
  2  Authentication error
  3  API error (network, timeout, etc.)
  4  Artifactory URL not configured (skip check)

Examples:
  # Check if axios is available
  $(basename "$0") https://artifactory.company.com/api axios

  # With API key
  $(basename "$0") https://artifactory.company.com/api axios YOUR_API_KEY

  # Using environment variable for API key
  export ARTIFACTORY_API_KEY=YOUR_API_KEY
  $(basename "$0") https://artifactory.company.com/api axios

  # Skip validation if URL not configured
  $(basename "$0") "Not configured" axios
EOF
    exit 0
fi

# Parse arguments
ARTIFACTORY_URL="${1:-}"
LIBRARY_NAME="${2:-}"
API_KEY="${3:-${ARTIFACTORY_API_KEY:-}}"

# Function to print status
print_status() {
    local status="$1"
    local message="$2"
    case "$status" in
        FOUND)
            echo -e "${GREEN}✅ FOUND${NC}: $message"
            ;;
        NOT_FOUND)
            echo -e "${YELLOW}❌ NOT FOUND${NC}: $message"
            ;;
        SKIPPED)
            echo -e "${YELLOW}⊘ SKIPPED${NC}: $message"
            ;;
        ERROR)
            echo -e "${RED}⚠️  ERROR${NC}: $message"
            ;;
    esac
}

# Validate inputs
if [ -z "$LIBRARY_NAME" ]; then
    echo "ERROR: Library name is required" >&2
    echo "Usage: $0 <artifactory-url> <library-name> [api-key]" >&2
    exit 3
fi

# Check if Artifactory URL is configured
if [ -z "$ARTIFACTORY_URL" ] || [ "$ARTIFACTORY_URL" = "Not configured" ] || [ "$ARTIFACTORY_URL" = "null" ]; then
    print_status "SKIPPED" "Artifactory URL not configured - skipping validation for $LIBRARY_NAME"
    exit 4
fi

# Build API endpoint
API_ENDPOINT="${ARTIFACTORY_URL}/api/search/artifact?name=${LIBRARY_NAME}"

# Query Artifactory with timeout
if [ -n "$API_KEY" ]; then
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -H "X-JFrog-Art-Api: ${API_KEY}" \
        --max-time 5 \
        --connect-timeout 3 \
        "$API_ENDPOINT" 2>/dev/null || echo -e "\n000")
else
    # Try without authentication (some Artifactory instances allow anonymous read)
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        --max-time 5 \
        --connect-timeout 3 \
        "$API_ENDPOINT" 2>/dev/null || echo -e "\n000")
fi

# Parse response
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

# Handle response
case "$HTTP_CODE" in
    200)
        # Check if jq is available
        if command -v jq &> /dev/null; then
            RESULTS=$(echo "$BODY" | jq -r '.results | length' 2>/dev/null || echo "0")
            if [ "$RESULTS" -gt 0 ]; then
                DOWNLOAD_URI=$(echo "$BODY" | jq -r '.results[0].downloadUri' 2>/dev/null || echo "")
                VERSION=$(echo "$DOWNLOAD_URI" | grep -oP '[\d\.]+(?=\.(jar|tar\.gz|zip|whl))' | head -1 || echo "latest")
                print_status "FOUND" "$LIBRARY_NAME${VERSION:+:$VERSION} available in Artifactory"
                echo "$DOWNLOAD_URI"
                exit 0
            else
                print_status "NOT_FOUND" "$LIBRARY_NAME not found in Artifactory"
                exit 1
            fi
        else
            # Fallback without jq - simple check
            if echo "$BODY" | grep -q "downloadUri"; then
                print_status "FOUND" "$LIBRARY_NAME available in Artifactory"
                echo "$BODY"
                exit 0
            else
                print_status "NOT_FOUND" "$LIBRARY_NAME not found in Artifactory"
                exit 1
            fi
        fi
        ;;
    401|403)
        print_status "ERROR" "Authentication failed. Check ARTIFACTORY_API_KEY environment variable"
        exit 2
        ;;
    000)
        print_status "ERROR" "Network error or timeout (Artifactory may be unreachable)"
        exit 3
        ;;
    *)
        print_status "ERROR" "Artifactory API returned HTTP $HTTP_CODE"
        exit 3
        ;;
esac
