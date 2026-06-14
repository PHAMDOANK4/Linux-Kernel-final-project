#!/usr/bin/env bash
set -euo pipefail

COMMAND="${1:-}"

if [[ -z "$COMMAND" ]]; then
  echo "Usage: run_job.sh <command>"
  exit 1
fi

bash -lc "$COMMAND"
