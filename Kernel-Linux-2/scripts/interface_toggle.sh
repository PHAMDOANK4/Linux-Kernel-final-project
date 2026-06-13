#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
require_root
interface_name="${1:-}"
state="${2:-}"
if [[ -z "$interface_name" || -z "$state" ]]; then
  echo "ERROR|Interface and state required" >&2
  exit 1
fi
ip link set "$interface_name" "$state"
echo "Interface $interface_name set to $state"