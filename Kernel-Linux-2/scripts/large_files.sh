#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd find
path="${1:-}"
size="${2:-+100M}"
if [[ -z "$path" ]]; then
  echo "ERROR|Directory path required" >&2
  exit 1
fi
printf 'Path|Size\n'
find "$path" -type f -size "$size" -printf '%p|%s bytes\n' 2>/dev/null