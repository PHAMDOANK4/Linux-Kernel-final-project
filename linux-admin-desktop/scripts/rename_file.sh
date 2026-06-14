#!/usr/bin/env bash
set -euo pipefail

SOURCE="${1:-}"
NEW_NAME="${2:-}"

if [[ -z "$SOURCE" || -z "$NEW_NAME" ]]; then
  echo "Usage: rename_file.sh <source> <new_name_or_path>"
  exit 1
fi

if [[ ! -e "$SOURCE" ]]; then
  echo "Source not found: $SOURCE"
  exit 1
fi

mv "$SOURCE" "$NEW_NAME"
echo "Renamed: $SOURCE -> $NEW_NAME"
