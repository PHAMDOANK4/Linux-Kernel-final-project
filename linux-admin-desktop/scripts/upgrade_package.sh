#!/usr/bin/env bash
set -euo pipefail

PKG="${1:-}"

apt-get update
if [[ -n "$PKG" ]]; then
  apt-get install --only-upgrade -y "$PKG"
  echo "Package upgraded: $PKG"
else
  apt-get upgrade -y
  echo "All packages upgraded."
fi
