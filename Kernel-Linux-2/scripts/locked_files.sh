#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd lsof
path="${1:-}"
printf 'PID|Command|File|Mode\n'
if [[ -n "$path" ]]; then
  lsof +D "$path" 2>/dev/null | awk 'NR>1 {print $2"|"$1"|"$9"|"$4}'
else
  lsof +L1 2>/dev/null | awk 'NR>1 {print $2"|"$1"|"$9"|"$4}'
fi