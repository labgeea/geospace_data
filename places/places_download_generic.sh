#!/bin/bash
#===============================================================================
# PLACES Download Script Wrapper
#===============================================================================
# This script wraps places_download_generic.py for convenient shell usage.
#
# Usage:
#   ./places_download_generic.sh --year 2025 --output-dir ./data/places/
#   ./places_download_generic.sh --year 2025 --geo-level county --output-dir ./data/places/
#
# Requirements:
#   - Python 3.8+ with requests, pandas
#   - Internet connection
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

# Run the download script
"$PYTHON_CMD" "$SCRIPT_DIR/places_download_generic.py" "$@"
