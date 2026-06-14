#!/usr/bin/env bash
set -euo pipefail

MATCH_TEXT="${1:-}"

if [[ -z "$MATCH_TEXT" ]]; then
  echo "Usage: delete_cron.sh <match_text>"
  exit 1
fi

CURRENT_CRON="$(crontab -l 2>/dev/null || true)"
if [[ -z "$CURRENT_CRON" ]]; then
  echo "No cron jobs found."
  exit 1
fi

FILTERED="$(echo "$CURRENT_CRON" | awk -v mt="$MATCH_TEXT" '
BEGIN { deleted=0 }
{
  if (NR == mt && deleted == 0) {
    deleted=1
    next
  }
  print $0
}
END {
  if (deleted == 0) exit 1
}')" || {
  echo "No cron entry matched: $MATCH_TEXT"
  exit 1
}

if [[ -z "$FILTERED" ]]; then
  crontab -r
  echo "All matching cron entries removed. Crontab is now empty."
else
  echo "$FILTERED" | crontab -
  echo "Cron entry deleted."
fi
