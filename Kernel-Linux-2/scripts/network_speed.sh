#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ip
printf 'current_ip=%s\ngateway=%s\ndns=%s\nupload_speed=%s\ndownload_speed=%s\n' \
  "$(hostname -I | awk '{print $1}')" \
  "$(ip route | awk '/default/ {print $3; exit}')" \
  "$(awk '/^nameserver/ {print $2; exit}' /etc/resolv.conf)" \
  "0" \
  "0"