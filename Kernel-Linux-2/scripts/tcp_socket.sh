#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ss
printf 'Proto|Local|Remote|State|PID|Process\n'
ss -tanpH | awk 'BEGIN{OFS="|"} {
  print "tcp", $4, $5, $1, $6, $6
}'