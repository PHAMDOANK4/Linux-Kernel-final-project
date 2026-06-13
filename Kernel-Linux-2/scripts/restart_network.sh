#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
require_root
if systemctl restart NetworkManager; then
  echo "NetworkManager restarted"
else
  systemctl restart networking
  echo "networking restarted"
fi