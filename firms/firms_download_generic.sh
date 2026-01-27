#!/bin/bash
#===============================================================================
# FIRMS Download Script Wrapper
#===============================================================================
# This script wraps firms_download_generic.py for easier command-line usage.
#
# Usage:
#   ./firms_download_generic.sh --map-key YOUR_KEY --sensor VIIRS_SNPP_SP \
#       --bbox california --start-date 2023-08-01 --end-date 2023-08-31 \
#       --output-dir ./data/firms/
#
# Requirements:
#   - Python 3.8+
#   - pandas, requests
#   - FIRMS MAP_KEY (free at https://firms.modaps.eosdis.nasa.gov/api/)
#===============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/firms_download_generic.py"

# Check if python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Run the Python script with all arguments
python "$PYTHON_SCRIPT" "$@"
