#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"
OWNER="${2:-}"
GROUP="${3:-}"

if [[ -z "$TARGET" || -z "$OWNER" ]]; then
  echo "Usage: chown_file.sh <target_path> <owner> [group]" >&2
  exit 1
fi

if [[ ! -e "$TARGET" ]]; then
  echo "Target not found: $TARGET" >&2
  exit 1
fi

if [[ -n "$GROUP" ]]; then
  chown "$OWNER:$GROUP" "$TARGET"
  echo "Changed ownership: $TARGET -> $OWNER:$GROUP"
else
  chown "$OWNER" "$TARGET"
  echo "Changed ownership: $TARGET -> $OWNER"
fi
