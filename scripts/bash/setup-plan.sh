#!/usr/bin/env bash

SCRIPT_DIR="${BASH_SOURCE[0]%/*}"
SCRIPT_DIR="$(cd "$SCRIPT_DIR"; pwd)"
exec "$SCRIPT_DIR/context-plan-setup.sh" "$@"
