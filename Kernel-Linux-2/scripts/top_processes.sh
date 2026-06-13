#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ps
printf 'PID|Process Name|User|CPU %%|Memory %%|Status|Start Time\n'
ps -eo pid,comm,user,%cpu,%mem,stat,lstart --sort=-%cpu --no-headers | head -n 10 | awk '{start=$7" "$8" "$9" "$10" "$11; printf "%s|%s|%s|%s|%s|%s|%s\n", $1, $2, $3, $4, $5, $6, start}'