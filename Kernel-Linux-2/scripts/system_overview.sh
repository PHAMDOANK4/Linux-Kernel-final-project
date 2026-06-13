#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd awk
cpu=$(awk -v RS=' ' '/^cpu /{usage=($2+$4)*100/($2+$4+$5)} END{print usage+0}' /proc/stat)
mem=$(free | awk '/Mem:/ {printf "%.2f", $3/$2*100}')
disk=$(df -P / | awk 'NR==2 {gsub("%", "", $5); print $5+0}')
uptime=$(uptime -p | sed 's/up //')
printf 'cpu_usage=%s\nmemory_usage=%s\ndisk_usage=%s\nuptime=%s\n' "$cpu" "$mem" "$disk" "$uptime"