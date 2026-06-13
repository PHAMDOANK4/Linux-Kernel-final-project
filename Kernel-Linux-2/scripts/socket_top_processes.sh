#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ss
printf 'Sockets|PID|Process\n'
ss -tunapH | awk '{
  pidproc = $6
  gsub(/users:\(\(/, "", pidproc)
  gsub(/\)\)/, "", pidproc)
  split(pidproc, a, ",")
  for (i in a) {
    gsub(/^[^,]*pid=/, "", a[i])
    gsub(/,.*$/, "", a[i])
    if (a[i] != "") print a[i]
  }
}' | sort | uniq -c | sort -rn | head -20 | while read count pid; do
  proc=$(ps -p "$pid" -o comm= 2>/dev/null || echo "?")
  printf '%s|%s|%s\n' "$count" "$pid" "$proc"
done
