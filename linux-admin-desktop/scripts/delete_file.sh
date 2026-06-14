#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: delete_file.sh <target>"
  exit 1
fi

if [[ ! -e "$TARGET" ]]; then
  echo "Target not found: $TARGET"
  exit 1
fi

rm -rf "$TARGET"
echo "Deleted: $TARGET"
