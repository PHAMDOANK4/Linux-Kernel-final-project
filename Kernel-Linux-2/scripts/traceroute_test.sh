#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd traceroute
target="${1:-}"
if [[ -z "$target" ]]; then
  echo "ERROR|Target required" >&2
  exit 1
fi
traceroute "$target"