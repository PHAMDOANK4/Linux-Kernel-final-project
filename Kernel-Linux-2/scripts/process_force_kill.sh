#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
require_root
pid="${1:-}"
if [[ -z "$pid" || ! "$pid" =~ ^[0-9]+$ ]]; then
  echo "ERROR|Invalid PID" >&2
  exit 1
fi
kill -KILL "$pid"
echo "Process $pid force killed"