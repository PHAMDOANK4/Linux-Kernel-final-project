#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export PATH=/usr/sbin:/usr/bin:/sbin:/bin:$PATH

require_root() {
  if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
    echo "ERROR|Root privileges required" >&2
    exit 1
  fi
}

check_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR|Missing command: $1" >&2
    exit 1
  }
}

escape_pipe() {
  sed 's/|/ /g'
}
