#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ss
printf 'Proto|Local|PID|Process\n'
ss -ltnupH | awk 'BEGIN{OFS="|"} {
  print $1, $4, $6, $6
}'