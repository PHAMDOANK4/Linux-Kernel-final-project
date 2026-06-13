#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ip
printf 'Interface|RX/s|TX/s\n'
ip -s link show | awk '/^[0-9]+:/{iface=$2; gsub(":", "", iface)} /RX: bytes/{getline; rx=$1} /TX: bytes/{getline; tx=$1; printf "%s|%s|%s\n", iface, rx, tx}'