#!/usr/bin/env bash
set -euo pipefail

SOURCE="${1:-}"
DESTINATION="${2:-}"

if [[ -z "$SOURCE" || -z "$DESTINATION" ]]; then
  echo "Usage: move_file.sh <source> <destination>"
  exit 1
fi

if [[ ! -e "$SOURCE" ]]; then
  echo "Source not found: $SOURCE"
  exit 1
fi

mv "$SOURCE" "$DESTINATION"
echo "Moved: $SOURCE -> $DESTINATION"
