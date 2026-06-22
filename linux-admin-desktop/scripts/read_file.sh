#!/usr/bin/env bash
set -euo pipefail

FILE="${1:-}"

if [[ -z "$FILE" ]]; then
  echo "Usage: read_file.sh <file_path>"
  exit 1
fi

if [[ ! -f "$FILE" ]]; then
  echo "Not a regular file: $FILE"
  exit 1
fi

SIZE=$(stat -c%s "$FILE" 2>/dev/null || stat -f%z "$FILE" 2>/dev/null || echo 0)
if [[ "$SIZE" -gt 10485760 ]]; then
  echo "File too large to display (${SIZE} bytes). Max 10MB."
  exit 1
fi

cat "$FILE"
