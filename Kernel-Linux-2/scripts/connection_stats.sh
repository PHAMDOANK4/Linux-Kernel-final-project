#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ss
json_tcp=$(ss -tanH | wc -l)
json_udp=$(ss -uanH | wc -l)
json_listen=$(ss -ltnH | wc -l)
printf '{"tcp":%s,"udp":%s,"listening":%s}\n' "$json_tcp" "$json_udp" "$json_listen"