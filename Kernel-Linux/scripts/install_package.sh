#!/usr/bin/env bash
set -euo pipefail

PKG="${1:-}"

if [[ -z "$PKG" ]]; then
  echo "Usage: install_package.sh <package_name>"
  exit 1
fi

apt-get update
apt-get install -y "$PKG"
echo "Package installed: $PKG"
