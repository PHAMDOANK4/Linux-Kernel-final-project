#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ip
printf 'Destination|Gateway|Mask|Iface\n'
ip route show | awk '{
  dest=$1; gw=""; iface="";
  for (i=1;i<=NF;i++) {
    if ($i=="via") gw=$(i+1);
    if ($i=="dev") iface=$(i+1);
  }
  printf "%s|%s|%s|%s\n", dest, gw, "", iface
}'