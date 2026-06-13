#!/usr/bin/env bash
set -euo pipefail

KEYWORD="${1:-}"

if [[ -z "$KEYWORD" ]]; then
  echo "Usage: search_package.sh <keyword>"
  exit 1
fi

apt-cache search "$KEYWORD"
