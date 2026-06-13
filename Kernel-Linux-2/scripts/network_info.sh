#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ip
printf 'Interface|IP Address|MAC Address|Netmask\n'
ip -br addr show | awk '{
  iface=$1; split($3, addr, "/"); ip=addr[1]; mask=addr[2]; mac="";
  printf "%s|%s|%s|%s\n", iface, ip, mac, mask
}'