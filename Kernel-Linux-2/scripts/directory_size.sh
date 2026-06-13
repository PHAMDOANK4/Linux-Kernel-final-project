#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd du
path="${1:-}"
if [[ -z "$path" ]]; then
  echo "ERROR|Directory path required" >&2
  exit 1
fi
printf 'Path|Size\n'
du -sh "$path" | awk '{print $2"|"$1}'