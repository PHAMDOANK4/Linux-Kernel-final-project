#!/usr/bin/env bash
set -euo pipefail

PKG="${1:-}"

if [[ -z "$PKG" ]]; then
  echo "Usage: remove_package.sh <package_name>"
  exit 1
fi

apt-get remove -y "$PKG"
echo "Package removed: $PKG"
