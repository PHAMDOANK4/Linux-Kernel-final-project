#!/usr/bin/env bash
set -euo pipefail

NEW_TIME="${1:-}"

if [[ -z "$NEW_TIME" ]]; then
  echo "Usage: set_time.sh <YYYY-MM-DD HH:MM:SS>"
  exit 1
fi

timedatectl set-time "$NEW_TIME"
echo "System time updated to: $NEW_TIME"
