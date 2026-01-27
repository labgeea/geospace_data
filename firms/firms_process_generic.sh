#!/bin/bash
#===============================================================================
# FIRMS Processing Script Wrapper
#===============================================================================
# This script wraps firms_process_generic.py for easier command-line usage.
#
# Usage:
#   ./firms_process_generic.sh --input-file ./data/firms.csv --output-dir ./output/ \
#       --aggregation-level county --temporal monthly
#
# Requirements:
#   - Python 3.8+
#   - pandas, geopandas, pygris
#===============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/firms_process_generic.py"

# Check if python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Run the Python script with all arguments
python "$PYTHON_SCRIPT" "$@"
