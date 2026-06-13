#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ps
pid_filter=""
name_filter=""
for arg in "$@"; do
  case "$arg" in
    pid=*) pid_filter="${arg#pid=}" ;;
    name=*) name_filter="${arg#name=}" ;;
  esac
done
printf 'PID|Process Name|User|CPU %%|Memory %%|Status|Start Time\n'
ps -eo pid,comm,user,%cpu,%mem,stat,lstart --no-headers | awk -v pid_filter="$pid_filter" -v name_filter="$name_filter" '
{
  pid=$1; name=$2;
  if (pid_filter != "" && pid != pid_filter) next;
  if (name_filter != "" && tolower(name) !~ tolower(name_filter)) next;
  start=$7" "$8" "$9" "$10" "$11;
  printf "%s|%s|%s|%s|%s|%s|%s\n", $1, $2, $3, $4, $5, $6, start
}'