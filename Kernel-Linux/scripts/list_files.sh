#!/usr/bin/env bash
set -euo pipefail

TARGET_PATH="${1:-/home}"
if [[ ! -d "$TARGET_PATH" ]]; then
  echo "Directory not found: $TARGET_PATH"
  exit 1
fi

TARGET_PATH="$(realpath "$TARGET_PATH")"
shopt -s nullglob dotglob

for item in "$TARGET_PATH"/*; do
  name="$(basename "$item")"
  if [[ "$name" == "." || "$name" == ".." ]]; then
    continue
  fi
  if [[ -d "$item" ]]; then
    printf 'DIR\t%s\t%s\n' "$name" "$item"
  fi
done

for item in "$TARGET_PATH"/*; do
  name="$(basename "$item")"
  if [[ "$name" == "." || "$name" == ".." ]]; then
    continue
  fi
  if [[ ! -d "$item" ]]; then
    printf 'FILE\t%s\t%s\n' "$name" "$item"
  fi
done
