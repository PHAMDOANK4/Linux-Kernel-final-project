#!/usr/bin/env bash
set -euo pipefail

DIRECTORY="${1:-}"
FILENAME="${2:-}"

if [[ -z "$DIRECTORY" || -z "$FILENAME" ]]; then
  echo "Usage: create_file.sh <directory> <filename>"
  exit 1
fi

mkdir -p "$DIRECTORY"
touch "$DIRECTORY/$FILENAME"
echo "File created: $DIRECTORY/$FILENAME"
