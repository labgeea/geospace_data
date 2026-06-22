#!/bin/bash
#
# PRISM Climate Data Download Wrapper
# ====================================
#
# Bash wrapper for prism_download_generic.py
#
# Usage:
#   ./prism_download_generic.sh --element ppt --time 20200101 --data-type ts --output-dir ./raw/prism/
#   ./prism_download_generic.sh --element ppt,tmax,tmin --time 202001,202002 --output-dir ./raw/prism/
#   ./prism_download_generic.sh --list-variables
#   ./prism_download_generic.sh --help
#
# Author: GEOSPACE Project
# License: Public Domain

VERSION="1.9.0"
MODULE_NAME="PRISM Download"

if [[ "${1:-}" == "--version" || "${1:-}" == "-V" ]]; then
    echo "$MODULE_NAME Framework v$VERSION"
    exit 0
fi

set -euo pipefail

# Defaults
ELEMENT=""
TIME=""
DATA_TYPE="ts"
FORMAT="nc"
OUTPUT_DIR="./raw/prism/"
NO_UNZIP=false
LIST_VARS=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/prism_download_generic.py"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; PURPLE='\033[0;35m'; CYAN='\033[0;36m'; NC='\033[0m'
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
    -e, --element LIST      Comma-separated PRISM element(s) (required)
                            Time series:  ppt tmin tmax tmean tdmean vpdmin vpdmax
                            Normals only: solslope soltotal solclear soltrans
    -t, --time LIST         Comma-separated time string(s) (required)
                            ts:      YYYYMMDD | YYYYMM | YYYY
                            normals: MM | MMDD | 14 (annual normal)
    -d, --data-type TYPE    ts (default) | normals_800 | normals
    -f, --format FMT        nc (default) | asc | grib2  [ts only]
    -o, --output-dir DIR    Output directory (default: ./raw/prism/)
        --no-unzip          Keep zip files without extracting
    -l, --list-variables    List all available elements
    -h, --help              Show this help message
        --version           Show version

EXAMPLES:
    # Daily precipitation
    $(basename "$0") -e ppt -t 20200115 -o ./raw/prism/

    # Monthly tmax for Q1 2020
    $(basename "$0") -e tmax -t 202001,202002,202003 -o ./raw/prism/

    # Annual mean temperature 2015-2020
    $(basename "$0") -e tmean -t 2015,2016,2017,2018,2019,2020 -o ./raw/prism/

    # Multiple elements, single day
    $(basename "$0") -e ppt,tmin,tmax -t 20200101 -o ./raw/prism/

    # 800m monthly normals for April precipitation
    $(basename "$0") -e ppt -t 04 -d normals_800 -o ./raw/prism/

    # List variables
    $(basename "$0") --list-variables

DATA SOURCE:
    PRISM Climate Group, Oregon State University
    https://prism.oregonstate.edu/
    Web Service: https://services.nacse.org/prism/data/public/

OUTPUT:
    ./raw/prism/{element}/PRISM_{element}_{data_type}_{time}_{YYYYMMDD}/
    Files extracted from zip: .bil, .hdr, .nc, or .asc depending on format
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--element)    ELEMENT="$2"; shift 2 ;;
            -t|--time)       TIME="$2";    shift 2 ;;
            -d|--data-type)  DATA_TYPE="$2"; shift 2 ;;
            -f|--format)     FORMAT="$2";  shift 2 ;;
            -o|--output-dir) OUTPUT_DIR="$2"; shift 2 ;;
            --no-unzip)      NO_UNZIP=true; shift ;;
            -l|--list-variables) LIST_VARS=true; shift ;;
            -h|--help)       show_help; exit 0 ;;
            *) print_error "Unknown option: $1"; echo "Use --help for usage."; exit 1 ;;
        esac
    done
}

check_prerequisites() {
    if ! command -v python3 &>/dev/null; then
        print_error "python3 is required but not found"
        exit 1
    fi
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Python script not found: $PYTHON_SCRIPT"
        exit 1
    fi
    if ! python3 -c "import requests" 2>/dev/null; then
        print_error "requests library not found. Install with: pip install requests"
        exit 1
    fi
    # Check connectivity to PRISM Web Service
    if [[ "$LIST_VARS" != true ]]; then
        if ! curl -s --connect-timeout 10 "https://services.nacse.org/prism/" > /dev/null 2>&1; then
            print_warning "Cannot reach PRISM Web Service. Check internet connection."
        else
            print_success "PRISM Web Service connectivity confirmed"
        fi
    fi
}

main() {
    print_header "$MODULE_NAME Framework v$VERSION"
    print_header "$(printf '=%.0s' {1..45})"

    parse_args "$@"

    if [[ "$LIST_VARS" == true ]]; then
        python3 "$PYTHON_SCRIPT" --list-variables
        exit 0
    fi

    if [[ -z "$ELEMENT" || -z "$TIME" ]]; then
        print_error "--element and --time are required"
        echo "Use --help for usage."
        exit 1
    fi

    check_prerequisites

    print_info "Configuration:"
    print_info "  Element(s)   : $ELEMENT"
    print_info "  Time(s)      : $TIME"
    print_info "  Data type    : $DATA_TYPE"
    [[ "$DATA_TYPE" == "ts" ]] && print_info "  Format       : $FORMAT"
    print_info "  Output dir   : $OUTPUT_DIR"
    print_info "  Unzip        : $( [[ "$NO_UNZIP" == true ]] && echo "no" || echo "yes" )"
    echo

    CMD=(python3 "$PYTHON_SCRIPT"
        --element "$ELEMENT"
        --time "$TIME"
        --data-type "$DATA_TYPE"
        --format "$FORMAT"
        --output-dir "$OUTPUT_DIR"
    )
    [[ "$NO_UNZIP" == true ]] && CMD+=(--no-unzip)

    if "${CMD[@]}"; then
        print_success "Download completed."
        print_info "Next step: ./prism_process_generic.sh --input-dir $OUTPUT_DIR --output-dir ./proc/prism/"
    else
        print_error "Download failed. See errors above."
        exit 1
    fi
}

main "$@"
