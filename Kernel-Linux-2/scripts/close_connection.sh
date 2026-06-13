#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
require_root
pid=""
port=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pid) pid="$2"; shift 2 ;;
    --port) port="$2"; shift 2 ;;
    *) shift ;;
  esac
done
if [[ -n "$pid" ]]; then
  kill -TERM "$pid"
  echo "Connection closed via PID $pid"
elif [[ -n "$port" ]]; then
  pkill -f ":$port"
  echo "Connection closed via port $port"
else
  echo "ERROR|pid or port required" >&2
  exit 1
fi