#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
require_root
interface_name="${1:-}"
cidr="${2:-}"
gateway="${3:-}"
if [[ -z "$interface_name" || -z "$cidr" ]]; then
  echo "ERROR|Interface and CIDR required" >&2
  exit 1
fi
ip addr flush dev "$interface_name"
ip addr add "$cidr" dev "$interface_name"
if [[ -n "$gateway" ]]; then
  ip route replace default via "$gateway" dev "$interface_name"
fi
echo "IP updated on $interface_name"