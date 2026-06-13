#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd nc
target="${1:-}"
ports="${2:-1-1024}"
if [[ -z "$target" ]]; then
  echo "ERROR|Target required" >&2
  exit 1
fi
printf 'Port|State\n'
start=${ports%-*}
end=${ports#*-}
for ((port=start; port<=end; port++)); do
  if nc -z -w1 "$target" "$port" >/dev/null 2>&1; then
    echo "$port|OPEN"
  fi
done