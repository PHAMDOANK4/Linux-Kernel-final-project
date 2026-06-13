#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"
MODE="${2:-}"

if [[ -z "$TARGET" || -z "$MODE" ]]; then
  echo "Usage: chmod_file.sh <target> <mode>"
  exit 1
fi

chmod "$MODE" "$TARGET"
echo "Permissions updated: $TARGET -> $MODE"
