#!/bin/bash
#===============================================================================
# NOAA Storm Events Download Wrapper
#===============================================================================
# Usage:
#   ./storms_download_generic.sh --year 2023 --output-dir ./data/storms/
#===============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/storms_download_generic.py"

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

python "$PYTHON_SCRIPT" "$@"
