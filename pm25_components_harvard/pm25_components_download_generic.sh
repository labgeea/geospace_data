#!/bin/bash
# ==============================================================================
# GEOSPACE FRAMEWORK
# ==============================================================================
# Module: PM2.5 Components (Harvard) Download
# Sources:
#   - Gridded (50-m urban / 1-km non-urban): doi:10.7910/DVN/3H7DNP
#   - Aggregated (state, county, tract, ZCTA, block group, ESRI ZIP, block):
#     doi:10.7910/DVN/F6PQAA
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/pm25_components_download_generic.py"

get_framework_version() {
    local version_file="${SCRIPT_DIR}/../version.py"
    if [[ -f "$version_file" ]]; then
        python3 -c "
import sys
sys.path.append('${SCRIPT_DIR}/..')
try:
    from version import get_module_version
    print(get_module_version('pm25_components_harvard'))
except Exception:
    print('1.0.0')
" 2>/dev/null || echo "1.0.0"
    else
        echo "1.0.0"
    fi
}

SCRIPT_VERSION="$(get_framework_version)"

show_version() {
    echo "PM2.5 Components (Harvard) Download v${SCRIPT_VERSION}"
    exit 0
}

if [[ "${1:-}" == "--version" || "${1:-}" == "-V" ]]; then
    show_version
fi

check_prerequisites() {
    local missing_deps=0

    if ! command -v python3 &> /dev/null; then
        echo "ERROR: python3 could not be found."
        missing_deps=1
    else
        if ! python3 -c "import requests" &> /dev/null; then
            echo "WARNING: Missing required Python package: requests"
            missing_deps=1
        fi
    fi

    if [[ $missing_deps -eq 1 ]]; then
        echo ""
        echo "=============================================================================="
        echo " MISSING PREREQUISITES DETECTED"
        echo "=============================================================================="
        echo " Required packages: requests (optional: tqdm)"
        echo " Recommended action: Activate an environment with these packages installed"
        echo "                     e.g., 'conda activate xarray-env'"
        echo "=============================================================================="
        echo ""
        exit 1
    fi
}

check_prerequisites

exec python3 "$PYTHON_SCRIPT" "$@"

