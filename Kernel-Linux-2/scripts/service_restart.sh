#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
require_root
service_name="${1:-}"
if [[ -z "$service_name" ]]; then
  echo "ERROR|Service name required" >&2
  exit 1
fi
systemctl restart "$service_name"
echo "Service $service_name restarted"