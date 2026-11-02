#!/bin/bash
# ==============================================================================
# GEOSPACE FRAMEWORK
# ==============================================================================
# Module: PM2.5 Components (Harvard) Processing
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/pm25_components_process_generic.py"

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
    echo "PM2.5 Components (Harvard) Processing v${SCRIPT_VERSION}"
    exit 0
}

for arg in "$@"; do
    case "$arg" in
        --version|-V)
            show_version
            ;;
        --help|-h|--list-config)
            exec python3 "$PYTHON_SCRIPT" "$@"
            ;;
    esac
done

check_prerequisites() {
    local missing_deps=0

    if ! command -v python3 &> /dev/null; then
        echo "ERROR: python3 could not be found."
        missing_deps=1
    else
        for pkg in pandas pyarrow numpy; do
            if ! python3 -c "import $pkg" &> /dev/null; then
                echo "WARNING: Missing required Python package: $pkg"
                missing_deps=1
            fi
        done
    fi

    if [[ $missing_deps -eq 1 ]]; then
        echo ""
        echo "=============================================================================="
        echo " MISSING PREREQUISITES DETECTED"
        echo "=============================================================================="
        echo " Required packages: pandas, pyarrow, numpy (plus geopandas, pygris for --include-gpkg)"
        echo " Recommended action: Activate an environment with these packages installed"
        echo "                     e.g., 'conda activate xarray-env'"
        echo "=============================================================================="
        echo ""
        exit 1
    fi
}

check_prerequisites

exec python3 "$PYTHON_SCRIPT" "$@"

