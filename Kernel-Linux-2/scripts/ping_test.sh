#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ping
target="${1:-}"
if [[ -z "$target" ]]; then
  echo "ERROR|Target required" >&2
  exit 1
fi
ping -c 4 "$target"