#!/usr/bin/env bash
set -euo pipefail

SCHEDULE="${1:-}"
COMMAND="${2:-}"

if [[ -z "$SCHEDULE" || -z "$COMMAND" ]]; then
  echo "Usage: create_cron.sh <schedule> <command>"
  exit 1
fi

( crontab -l 2>/dev/null; echo "$SCHEDULE $COMMAND" ) | awk '!seen[$0]++' | crontab -
echo "Cron job created: $SCHEDULE $COMMAND"
