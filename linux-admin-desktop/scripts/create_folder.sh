#!/usr/bin/env bash
set -euo pipefail

PARENT_DIR="${1:-}"
FOLDER_NAME="${2:-}"

if [[ -z "$PARENT_DIR" || -z "$FOLDER_NAME" ]]; then
  echo "Usage: create_folder.sh <parent_directory> <folder_name>"
  exit 1
fi

mkdir -p "$PARENT_DIR/$FOLDER_NAME"
echo "Folder created: $PARENT_DIR/$FOLDER_NAME"
