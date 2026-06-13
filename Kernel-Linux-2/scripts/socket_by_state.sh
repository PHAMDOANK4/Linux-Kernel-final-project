#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd ss
total=$(ss -tunapH | wc -l)
tcp=$(ss -tanH | wc -l)
udp=$(ss -uanH | wc -l)
listening=$(ss -ltnH | wc -l)
established=$(ss -tunH state established | wc -l)
time_wait=$(ss -tunH state time-wait | wc -l)
close_wait=$(ss -tunH state close-wait | wc -l)
last_ack=$(ss -tunH state last-ack | wc -l)
printf 'total=%s\ntcp=%s\nudp=%s\nlistening=%s\nestablished=%s\ntime_wait=%s\nclose_wait=%s\nlast_ack=%s\n' \
  "$total" "$tcp" "$udp" "$listening" "$established" "$time_wait" "$close_wait" "$last_ack"
