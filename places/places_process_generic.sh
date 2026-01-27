#!/bin/bash
#===============================================================================
# PLACES Processing Script Wrapper
#===============================================================================
# This script wraps places_process_generic.py for convenient shell usage.
#
# Usage:
#   ./places_process_generic.sh --input-file ./data/places_zcta_2024.csv --output-dir ./output --year 2024
#
# Requirements:
#   - Python 3.8+ with pandas, geopandas, pygris
#===============================================================================

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default Python command
PYTHON_CMD="${PYTHON_CMD:-python3}"

# Check for Python
if ! command -v "$PYTHON_CMD" &> /dev/null; then
    echo "Error: Python not found. Set PYTHON_CMD environment variable."
    exit 1
fi

# Run the processing script
"$PYTHON_CMD" "$SCRIPT_DIR/places_process_generic.py" "$@"
