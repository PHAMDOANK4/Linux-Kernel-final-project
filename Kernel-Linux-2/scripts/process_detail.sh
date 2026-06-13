#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ps
check_cmd awk
pid="${1:-}"
if [[ -z "$pid" || ! "$pid" =~ ^[0-9]+$ ]]; then
  echo "ERROR|Invalid PID" >&2
  exit 1
fi
ps -p "$pid" -o pid=,ppid=,user=,%cpu=,%mem=,stat=,lstart=,comm= | awk '{
  print "PID|" $1
  print "PPID|" $2
  print "User|" $3
  print "CPU %|" $4
  print "Memory %|" $5
  print "Status|" $6
  print "Start Time|" $7" "$8" "$9" "$10" "$11
  print "Command|" $12
}'