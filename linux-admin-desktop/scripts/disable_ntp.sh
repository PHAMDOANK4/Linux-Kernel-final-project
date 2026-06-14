#!/usr/bin/env bash
set -euo pipefail

timedatectl set-ntp false
echo "NTP disabled."
