#!/usr/bin/env bash
# Setup product vision document
set -e

JSON_MODE=false
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) echo "Usage: $0 [--json]"; exit 0 ;;
    esac
done

REPO_ROOT=$(git rev-parse --show-toplevel)
DOCS_DIR="$REPO_ROOT/docs"
mkdir -p "$DOCS_DIR"

TEMPLATE="$REPO_ROOT/templates/product-vision-template.md"
PRODUCT_VISION_FILE="$DOCS_DIR/product-vision.md"

if [ -f "$TEMPLATE" ]; then
    cp "$TEMPLATE" "$PRODUCT_VISION_FILE"
else
    touch "$PRODUCT_VISION_FILE"
fi

if $JSON_MODE; then
    printf '{"PRODUCT_VISION_FILE":"%s"}\n' "$PRODUCT_VISION_FILE"
else
    echo "PRODUCT_VISION_FILE: $PRODUCT_VISION_FILE"
fi
