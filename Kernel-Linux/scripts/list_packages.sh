#!/usr/bin/env bash
set -euo pipefail

dpkg-query -W -f='${binary:Package}\t${Version}\n' | sort
