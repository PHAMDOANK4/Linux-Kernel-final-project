#!/usr/bin/env bash
set -euo pipefail

echo "System date/time:"
date "+%Y-%m-%d %H:%M:%S %Z"
echo

echo "timedatectl status:"
timedatectl status || true
