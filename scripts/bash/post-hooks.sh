#!/usr/bin/env bash

SCRIPT_DIR=${BASH_SOURCE[0]%/*}
source "$SCRIPT_DIR/pre-hooks.sh"
resolve_hooks after "$1"
