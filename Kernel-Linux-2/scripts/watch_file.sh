#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd inotifywait
path="${1:-}"
duration="${2:-10}"
if [[ -z "$path" ]]; then
  echo "ERROR|File path required" >&2
  exit 1
fi
inotifywait -m -e create -e modify -e delete -e move --format '%e|%w%f' --timeout "$duration" "$path"