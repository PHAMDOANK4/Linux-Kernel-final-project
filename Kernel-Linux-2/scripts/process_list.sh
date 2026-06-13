#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ps
printf 'PID|Process Name|User|CPU %%|Memory %%|Status|Start Time\n'
ps -eo pid,comm,user,%cpu,%mem,stat,lstart --sort=-%cpu --no-headers | awk '{
  pid=$1; name=$2; user=$3; cpu=$4; mem=$5; stat=$6;
  start=$7" "$8" "$9" "$10" "$11;
  printf "%s|%s|%s|%s|%s|%s|%s\n", pid, name, user, cpu, mem, stat, start
}'