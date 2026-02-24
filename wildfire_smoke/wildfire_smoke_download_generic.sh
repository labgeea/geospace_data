#!/bin/bash
# ==============================================================================
# GEOSPACE FRAMEWORK
# ==============================================================================
# Module: Wildfire Smoke Download
# Version: 1.0.0
# ==============================================================================

# Version display function
show_version() {
    PYTHON_SCRIPT="$(dirname "$0")/wildfire_smoke_download_generic.py"
    if [[ -f "$PYTHON_SCRIPT" ]]; then
        python3 "$PYTHON_SCRIPT" --version
    else
        echo "Wildfire Smoke Download v1.0.0"
    fi
    exit 0
}

check_prerequisites() {
    local missing_deps=0
    
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: python3 could not be found."
        missing_deps=1
    else
        # Check required python packages
        for pkg in requests tqdm; do
            if ! python3 -c "import $pkg" &> /dev/null; then
                echo "WARNING: Missing required Python package: $pkg"
                missing_deps=1
            fi
        done
    fi
    
    if [ $missing_deps -eq 1 ]; then
        echo ""
        echo "=============================================================================="
        echo " MISSING PREREQUISITES DETECTED"
        echo "=============================================================================="
        echo " Required packages: requests, tqdm"
        echo " Recommended action: Activate an environment with these packages installed"
        echo "                     e.g., 'conda activate xarray-env'"
        echo "=============================================================================="
        echo ""
        exit 1
    fi
}

check_prerequisites

# Check for version argument
if [[ "$1" == "--version" || "$1" == "-V" ]]; then
    show_version
fi

PYTHON_SCRIPT="$(dirname "$0")/wildfire_smoke_download_generic.py"
python3 "$PYTHON_SCRIPT" "$@"
