#!/bin/bash
#
# PRISM Climate Data Processing Wrapper
# =======================================
#
# Bash wrapper for prism_process_generic.py
#
# Usage:
#   ./prism_process_generic.sh --input-dir ./raw/prism/ --output-dir ./proc/prism/
#   ./prism_process_generic.sh --input-dir ./raw/prism/ --output-dir ./proc/prism/ --element ppt
#   ./prism_process_generic.sh --help
#
# Author: GEOSPACE Project
# License: Public Domain

VERSION="1.9.0"
MODULE_NAME="PRISM Processing"

if [[ "${1:-}" == "--version" || "${1:-}" == "-V" ]]; then
    echo "$MODULE_NAME Framework v$VERSION"
    exit 0
fi

set -euo pipefail

INPUT_DIR=""
OUTPUT_DIR=""
ELEMENT=""
CRS="EPSG:5070"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/prism_process_generic.py"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; PURPLE='\033[0;35m'; NC='\033[0m'
print_info()    { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error()   { echo -e "${RED}✗${NC} $1"; }
print_header()  { echo -e "${PURPLE}$1${NC}"; }

show_help() {
    cat << EOF
$MODULE_NAME Framework v$VERSION

USAGE:
    $(basename "$0") [OPTIONS]

OPTIONS:
    -i, --input-dir DIR    Directory with downloaded PRISM files (required)
    -o, --output-dir DIR   Output directory for processed GeoTIFFs (required)
    -e, --element CODE     Filter to one element: ppt tmin tmax tmean tdmean vpdmin vpdmax
                           solslope soltotal solclear soltrans
        --crs CRS          Target CRS (default: EPSG:5070)
    -h, --help             Show this help
        --version          Show version

EXAMPLES:
    # Process all PRISM elements
    $(basename "$0") -i ./raw/prism/ -o ./proc/prism/

    # Process precipitation only
    $(basename "$0") -i ./raw/prism/ -o ./proc/prism/ -e ppt

OUTPUT:
    GeoTIFFs at EPSG:5070 (CONUS Albers), LZW compressed, tiled
    Filename convention mirrors PRISM source filenames with .tif extension
    Processing report: proc/prism/prism_processing_report.json

DATA SOURCE:
    PRISM Climate Group, Oregon State University
    https://prism.oregonstate.edu/
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--input-dir)  INPUT_DIR="$2"; shift 2 ;;
            -o|--output-dir) OUTPUT_DIR="$2"; shift 2 ;;
            -e|--element)    ELEMENT="$2"; shift 2 ;;
            --crs)           CRS="$2"; shift 2 ;;
            -h|--help)       show_help; exit 0 ;;
            *) print_error "Unknown option: $1"; echo "Use --help for usage."; exit 1 ;;
        esac
    done
}

check_prerequisites() {
    if ! command -v python3 &>/dev/null; then
        print_error "python3 not found"; exit 1
    fi
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Python script not found: $PYTHON_SCRIPT"; exit 1
    fi
    for pkg in rasterio numpy; do
        if ! python3 -c "import $pkg" 2>/dev/null; then
            print_error "$pkg not found. Install with: pip install $pkg"
            exit 1
        fi
    done
}

main() {
    print_header "$MODULE_NAME Framework v$VERSION"
    print_header "$(printf '=%.0s' {1..45})"

    parse_args "$@"

    if [[ -z "$INPUT_DIR" || -z "$OUTPUT_DIR" ]]; then
        print_error "--input-dir and --output-dir are required"
        echo "Use --help for usage."; exit 1
    fi

    if [[ ! -d "$INPUT_DIR" ]]; then
        print_error "Input directory not found: $INPUT_DIR"; exit 1
    fi

    check_prerequisites

    print_info "Configuration:"
    print_info "  Input dir  : $INPUT_DIR"
    print_info "  Output dir : $OUTPUT_DIR"
    print_info "  Element    : ${ELEMENT:-all}"
    print_info "  Target CRS : $CRS"
    echo

    CMD=(python3 "$PYTHON_SCRIPT"
        --input-dir "$INPUT_DIR"
        --output-dir "$OUTPUT_DIR"
        --crs "$CRS"
    )
    [[ -n "$ELEMENT" ]] && CMD+=(--element "$ELEMENT")

    if "${CMD[@]}"; then
        print_success "Processing completed."
        print_info "Output: $OUTPUT_DIR"
    else
        print_error "Processing failed. See errors above."
        exit 1
    fi
}

main "$@"
