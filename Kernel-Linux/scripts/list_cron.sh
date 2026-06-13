#!/usr/bin/env bash
set -euo pipefail

crontab -l 2>/dev/null || echo "No cron jobs configured."
