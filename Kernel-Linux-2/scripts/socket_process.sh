#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ss
pid=""
port=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pid) pid="$2"; shift 2 ;;
    --port) port="$2"; shift 2 ;;
    *) shift ;;
  esac
done
printf 'Proto|Local|Remote|State|PID|Process\n'
ss -tunapH | awk -v pid="$pid" -v port="$port" 'BEGIN{OFS="|"} {
  if (pid != "" && $6 !~ pid) next;
  if (port != "" && $4 !~ port) next;
  print $1, $4, $5, $2, $6, $6
}'