#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd nc
target="${1:-}"
port="${2:-}"
if [[ -z "$target" || -z "$port" ]]; then
  echo "ERROR|Target and port required" >&2
  exit 1
fi
if nc -zvw3 "$target" "$port" >/tmp/port_check.out 2>&1; then
  echo "OPEN|$target:$port"
else
  echo "CLOSED|$target:$port"
fi