#!/usr/bin/env bash
set -euo pipefail

TIMEZONE="${1:-}"

if [[ -z "$TIMEZONE" ]]; then
  echo "Usage: set_timezone.sh <timezone>"
  exit 1
fi

timedatectl set-timezone "$TIMEZONE"
echo "Timezone updated to: $TIMEZONE"
