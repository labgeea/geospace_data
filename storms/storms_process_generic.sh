#!/bin/bash
#===============================================================================
# NOAA Storm Events Processing Wrapper
#===============================================================================
# Usage:
#   ./storms_process_generic.sh --input-file data/raw.csv --output-dir data/proc
#===============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/storms_process_generic.py"

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

python "$PYTHON_SCRIPT" "$@"
