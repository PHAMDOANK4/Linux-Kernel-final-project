#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
if [[ -f /etc/resolv.conf ]]; then
  awk '/^nameserver/{print "DNS|" $2}' /etc/resolv.conf
else
  echo "DNS|unknown"
fi