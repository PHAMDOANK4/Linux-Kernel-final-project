#!/usr/bin/env bash
set -euo pipefail

MATCH_TEXT="${1:-}"
NEW_SCHEDULE="${2:-}"
NEW_COMMAND="${3:-}"
NEW_LINE="$NEW_SCHEDULE $NEW_COMMAND"

if [[ -z "$MATCH_TEXT" || -z "$NEW_SCHEDULE" || -z "$NEW_COMMAND" ]]; then
  echo "Usage: update_cron.sh <match_text> <new_schedule> <new_command>"
  exit 1
fi

CURRENT_CRON="$(crontab -l 2>/dev/null || true)"
if [[ -z "$CURRENT_CRON" ]]; then
  echo "No cron jobs found."
  exit 1
fi

UPDATED_CRON="$(echo "$CURRENT_CRON" | awk -v mt="$MATCH_TEXT" -v nl="$NEW_LINE" '
BEGIN { updated=0 }
{
  if (NR == mt && updated == 0) {
    print nl
    updated=1
  } else {
    print $0
  }
}
END {
  if (updated == 0) exit 1
}')" || {
  echo "No cron entry matched: $MATCH_TEXT"
  exit 1
}

echo "$UPDATED_CRON" | crontab -
echo "Cron job updated."
