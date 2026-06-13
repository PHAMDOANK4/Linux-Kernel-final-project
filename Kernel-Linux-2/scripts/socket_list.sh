#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ss
printf 'Proto|Local|Remote|State|PID|Process\n'
ss -tunapH | awk 'BEGIN{OFS="|"} {
  proto=$1; local=$4; remote=$5; state=$2; pidproc=$6;
  print proto, local, remote, state, pidproc, pidproc
}'