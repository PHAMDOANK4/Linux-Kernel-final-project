#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: file_info.sh <path>"
  exit 1
fi

if [[ ! -e "$TARGET" ]]; then
  echo "Not found: $TARGET"
  exit 1
fi

echo "========== Metadata =========="
stat "$TARGET" 2>/dev/null || true
echo ""
echo "--------- Type ---------"
file "$TARGET" 2>/dev/null || true

if [[ -d "$TARGET" ]]; then
  ITEM_COUNT=$(ls -1 "$TARGET" 2>/dev/null | wc -l)
  echo ""
  echo "--- Directory Info ---"
  echo "Items: $ITEM_COUNT"
  du -sh "$TARGET" 2>/dev/null || true
elif [[ -f "$TARGET" ]]; then
  LINES=$(wc -l < "$TARGET" 2>/dev/null || echo 0)
  echo ""
  echo "--- File Info ---"
  echo "Lines: $LINES"
  du -h "$TARGET" 2>/dev/null || true
fi

echo ""
echo "--------- Permissions ---------"
ls -la "$TARGET" 2>/dev/null || true
