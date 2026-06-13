#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/common.sh"
check_cmd stat
path="${1:-}"
if [[ -z "$path" ]]; then
  echo "ERROR|File path required" >&2
  exit 1
fi
stat -c 'File:%n
Permissions:%A
Owner:%U
Group:%G
Size:%s
Modified:%y' "$path"