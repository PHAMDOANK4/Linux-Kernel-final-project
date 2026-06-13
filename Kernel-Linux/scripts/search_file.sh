#!/usr/bin/env bash
set -euo pipefail

BASE_PATH="${1:-}"
KEYWORD="${2:-}"

if [[ -z "$BASE_PATH" || -z "$KEYWORD" ]]; then
  echo "Usage: search_file.sh <base_path> <keyword>"
  exit 1
fi

if [[ ! -d "$BASE_PATH" ]]; then
  echo "Directory not found: $BASE_PATH"
  exit 1
fi

find "$BASE_PATH" -iname "*$KEYWORD*" -print
