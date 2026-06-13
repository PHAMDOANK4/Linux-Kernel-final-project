#!/usr/bin/env bash
set -euo pipefail

if command -v chronyc >/dev/null 2>&1; then
  chronyc -a makestep
  echo "Time synchronized by chrony."
elif command -v ntpdate >/dev/null 2>&1; then
  ntpdate -u pool.ntp.org
  echo "Time synchronized by ntpdate."
else
  timedatectl set-ntp true
  echo "NTP enabled for synchronization."
fi
