#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ss
printf 'Proto|Local|Remote|State|PID|Process\n'
ss -tunapH | awk 'BEGIN{OFS="|"} {print $1, $4, $5, $2, $6, $6}'