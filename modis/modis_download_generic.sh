#!/bin/bash
#
# Generic MODIS Variable Download Wrapper Script
# ==============================================
#
# This bash wrapper provides a convenient interface for downloading any MODIS variable
# from NASA Earthdata with command-line argument parsing and validation.
#
# Usage:
#
#   ./modis_download_generic.sh --variables LST --year 2020 --month 1 --output-dir /data/MODIS/
#   ./modis_download_generic.sh --variables LST,NDVI --year 2020 --month 1
#   ./modis_download_generic.sh --variables vegetation --year 2019 --month 12
#   ./modis_download_generic.sh --list-variables
#   ./modis_download_generic.sh --help
#
# Author: GEOSPACE Project
# Date: July 2025
# License: Public Domain

# Version information
VERSION="1.0.0"
MODULE_NAME="MODIS Download"

# Version display function
show_version() {
    echo "$MODULE_NAME Framework v$VERSION"
    exit 0
}

# Check for version argument
if [[ "$1" == "--version" || "$1" == "-V" ]]; then
    show_version
fi

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Default values
VARIABLES=""
YEAR=""
MONTH=""
DATE=""
INSTRUMENT="Both"
OUTPUT_DIR=""
MAX_WORKERS="5"
LIST_VARIABLES=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/modis_download_generic.py"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_header() { echo -e "${PURPLE}$1${NC}"; }
print_variable() { echo -e "${CYAN}$1${NC}"; }

# Function to display help
show_help() {
    cat << EOF
Generic MODIS Variable Download Script

USAGE:
    $(basename "$0") [OPTIONS]

OPTIONS:
    -v, --variables LIST    Comma-separated list of variables to download (required)
    -y, --year YEAR         Year to download (use with --month)
    -m, --month MONTH       Month to download (1-12) (use with --year)
    -d, --date YYYY-MM-DD   Download specific date
    -i, --instrument INST   Satellite instrument: Terra, Aqua, or Both (default: Both)
    -o, --output-dir DIR    Output directory (required)
    -w, --workers NUM       Number of parallel downloads (default: 5)
    -l, --list-variables    List all available variables and aliases
    -h, --help              Show this help message

EXAMPLES:
    # Download for a specific month
    $(basename "$0") -v LST -y 2020 -m 1 -o /data/MODIS/

    # Download for a specific date
    $(basename "$0") -v LST -d 2020-01-15 -o /data/MODIS/

    # Download multiple variables
    $(basename "$0") --variables LST,NDVI -y 2020 -m 1 -o /data/MODIS/

    # Download vegetation package (NDVI, EVI, VCF)
    $(basename "$0") -v vegetation -y 2019 -m 12 -o /data/MODIS/

    # Download Terra data only
    $(basename "$0") -v LST -y 2020 -m 1 -o /data/MODIS/ -i Terra

    # Download with more parallel workers
    $(basename "$0") -v all -y 2020 -m 1 -o /data/MODIS/ -w 10

    # List all available variables
    $(basename "$0") --list-variables

COMMON VARIABLES:
    Land Surface:
        LST (land surface temperature)

    Vegetation:
        NDVI (normalized difference vegetation index)
        EVI (enhanced vegetation index)
        VCF (vegetation continuous fields - tree cover)

VARIABLE ALIASES:
    You can use shorter names for convenience:
        land_surface_temperature/temperature/temp -> LST
        vegetation_index/vegetation -> NDVI
        tree_cover/forest_cover -> VCF

PREDEFINED PACKAGES:
    Use these shortcuts for common variable combinations:
        --variables vegetation   # NDVI,EVI,VCF
        --variables temperature  # LST
        --variables land         # LST,NDVI,VCF
        --variables all          # All available variables

INSTRUMENTS:
    Terra: Morning overpass (~10:30 AM local time)
    Aqua:  Afternoon overpass (~1:30 PM local time)
    Both:  Download from both satellites (recommended)

REQUIREMENTS:
    - Python 3.6+
    - requests, beautifulsoup4, pyproj, pandas, numpy
    - NASA Earthdata account and bearer token
    - EARTHDATA_BEARER_TOKEN environment variable

OUTPUT:
    - Individual HDF files organized by product and date
    - Files named following MODIS convention: PRODUCT.AYYYYDDD.TILE.VVV.YYYYDDDHHMMSS.hdf
    - Download verification and statistics

DATA SOURCE:
    MODIS data from NASA Earthdata repository via USGS servers.
    Provides high-quality satellite observations for land surface analysis.

For more information visit: https://modis.gsfc.nasa.gov/
EOF
}

# Function to expand variable packages
expand_variable_packages() {
    local vars="$1"

    # Replace predefined packages with variable lists
    vars="${vars//vegetation/NDVI,EVI,VCF}"
    vars="${vars//temperature/LST}"
    vars="${vars//land/LST,NDVI,VCF}"
    vars="${vars//all/LST,NDVI,VCF,EVI}"

    echo "$vars"
}

# Function to validate inputs
validate_inputs() {
    local errors=0

    # Check if variables are provided
    if [[ -z "$VARIABLES" ]] && [[ "$LIST_VARIABLES" != true ]]; then
        print_error "Variables are required. Use -v or --variables"
        print_info "Use --list-variables to see available options"
        ((errors++))
    fi

    # Check time specification
    if [[ "$LIST_VARIABLES" != true ]]; then
        local time_specified=false
        if [[ -n "$DATE" ]]; then
            time_specified=true
            if ! date -d "$DATE" >/dev/null 2>&1; then
                print_error "Invalid date format: $DATE (use YYYY-MM-DD)"
                ((errors++))
            fi
        fi

        if [[ -n "$YEAR" ]] || [[ -n "$MONTH" ]]; then
            if [[ "$time_specified" == true ]]; then
                print_error "Cannot specify both --date and --year/--month"
                ((errors++))
            fi
            time_specified=true

            if [[ -z "$YEAR" ]]; then
                print_error "Year is required when using --month"
                ((errors++))
            elif ! [[ "$YEAR" =~ ^[0-9]{4}$ ]] || [[ "$YEAR" -lt 2000 ]] || [[ "$YEAR" -gt $(date +%Y) ]]; then
                print_error "Year must be between 2000 and $(date +%Y)"
                ((errors++))
            fi

            if [[ -z "$MONTH" ]]; then
                print_error "Month is required when using --year"
                ((errors++))
            elif ! [[ "$MONTH" =~ ^[0-9]+$ ]] || [[ "$MONTH" -lt 1 ]] || [[ "$MONTH" -gt 12 ]]; then
                print_error "Month must be between 1 and 12"
                ((errors++))
            fi
        fi

        if [[ "$time_specified" != true ]]; then
            print_error "Time period must be specified using --date or --year/--month"
            ((errors++))
        fi

        # Check if output directory is provided
        if [[ -z "$OUTPUT_DIR" ]]; then
            print_error "Output directory is required. Use -o or --output-dir"
            ((errors++))
        fi
    fi

    # Validate instrument
    if [[ ! "$INSTRUMENT" =~ ^(Terra|Aqua|Both)$ ]]; then
        print_error "Instrument must be: Terra, Aqua, or Both"
        ((errors++))
    fi

    # Validate max workers
    if ! [[ "$MAX_WORKERS" =~ ^[0-9]+$ ]] || [[ "$MAX_WORKERS" -lt 1 ]] || [[ "$MAX_WORKERS" -gt 20 ]]; then
        print_error "Max workers must be between 1 and 20"
        ((errors++))
    fi

    # Check if Python script exists
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Python script not found: $PYTHON_SCRIPT"
        print_info "Please ensure modis_download_generic.py is in the same directory"
        ((errors++))
    fi

    return $errors
}

# Function to check prerequisites
check_prerequisites() {
    local errors=0

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        ((errors++))
    fi

    # Check required Python packages
    local packages=("requests" "bs4" "pyproj" "pandas" "numpy")
    for package in "${packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            if [[ "$package" == "bs4" ]]; then
                print_error "beautifulsoup4 library not found. Install with: pip install beautifulsoup4"
            else
                print_error "$package library not found. Install with: pip install $package"
            fi
            ((errors++))
        fi
    done

    # Check Earthdata bearer token (unless listing variables)
    if [[ "$LIST_VARIABLES" != true ]] && [[ -z "${EARTHDATA_BEARER_TOKEN:-}" ]]; then
        print_error "EARTHDATA_BEARER_TOKEN environment variable not set"
        print_info "Please obtain a bearer token from NASA Earthdata:"
        print_info "1. Visit: https://urs.earthdata.nasa.gov/"
        print_info "2. Login and generate a bearer token"
        print_info "3. Set environment variable: export EARTHDATA_BEARER_TOKEN=your_token"
        ((errors++))
    fi

    # Check internet connectivity to Earthdata
    if [[ "$LIST_VARIABLES" != true ]]; then
        print_info "Checking connectivity to NASA Earthdata..."
        if ! curl -s --connect-timeout 10 "https://e4ftl01.cr.usgs.gov/" > /dev/null; then
            print_warning "Cannot reach NASA Earthdata servers. Check internet connection."
            print_info "Server: https://e4ftl01.cr.usgs.gov/"
            ((errors++))
        else
            print_success "NASA Earthdata connectivity confirmed"
        fi
    fi

    return $errors
}

# Function to display variable summary
show_variable_summary() {
    local vars="$1"

    print_header "Variable Summary:"
    print_header "================"

    # Count variables
    local var_count=$(echo "$vars" | tr ',' '\n' | wc -l)
    print_info "Number of variables: $var_count"

    # List variables
    echo "$vars" | tr ',' '\n' | while read -r var; do
        if [[ -n "$var" ]]; then
            print_variable "  - $var"
        fi
    done
    echo
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--variables|--vars)
                VARIABLES="$2"
                shift 2
                ;;
            -y|--year)
                YEAR="$2"
                shift 2
                ;;
            -m|--month)
                MONTH="$2"
                shift 2
                ;;
            -d|--date)
                DATE="$2"
                shift 2
                ;;
            -i|--instrument)
                INSTRUMENT="$2"
                shift 2
                ;;
            -o|--output-dir)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            -w|--workers)
                MAX_WORKERS="$2"
                shift 2
                ;;
            -l|--list-variables)
                LIST_VARIABLES=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                print_info "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Main function
main() {
    print_header "MODIS Generic Variable Download Wrapper"
    print_header "======================================"

    # Parse arguments
    parse_args "$@"

    # Handle list variables request
    if [[ "$LIST_VARIABLES" == true ]]; then
        print_info "Listing available variables..."
        if python3 "$PYTHON_SCRIPT" --list-variables; then
            exit 0
        else
            print_error "Failed to list variables"
            exit 1
        fi
    fi

    # Validate inputs
    if ! validate_inputs; then
        print_error "Validation failed. Use -h for help."
        exit 1
    fi

    # Check prerequisites
    if ! check_prerequisites; then
        print_error "Prerequisites check failed. Please install missing components."
        exit 1
    fi

    # Expand variable packages
    VARIABLES=$(expand_variable_packages "$VARIABLES")

    # Create output directory if it doesn't exist
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        print_info "Creating output directory: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi

    # Show configuration
    print_info "Configuration:"
    print_info "  Variables: $VARIABLES"
    if [[ -n "$DATE" ]]; then
        print_info "  Date: $DATE"
    else
        print_info "  Year: $YEAR"
        print_info "  Month: $MONTH"
    fi
    print_info "  Instrument: $INSTRUMENT"
    print_info "  Output Directory: $OUTPUT_DIR"
    print_info "  Max Workers: $MAX_WORKERS"
    print_info "  Python Script: $PYTHON_SCRIPT"
    echo

    # Run the Python download script
    print_info "Starting download..."

    python_cmd="python3 '$PYTHON_SCRIPT' --variables '$VARIABLES' --instrument '$INSTRUMENT' --output-dir '$OUTPUT_DIR' --workers '$MAX_WORKERS'"

    if [[ -n "$DATE" ]]; then
        python_cmd="$python_cmd --date '$DATE'"
    else
        python_cmd="$python_cmd --year '$YEAR' --month '$MONTH'"
    fi

    if eval "$python_cmd"; then
        print_success "Download completed successfully!"

        # Count output files and calculate total size
        local hdf_count=$(find "$OUTPUT_DIR" -name "*.hdf" -type f 2>/dev/null | wc -l || echo "0")
        local total_size=$(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1 || echo "unknown")

        print_success "Output summary:"
        if [[ $hdf_count -gt 0 ]]; then
            print_success "  HDF files: $hdf_count"
        fi
        print_success "  Total output size: $total_size"
        print_success "  Output directory: $OUTPUT_DIR"

        # Show specific files created (sample)
        print_success "  Sample files created:"
        find "$OUTPUT_DIR" -name "*.hdf" -type f -newer <(date -d '5 minutes ago' '+%Y-%m-%d %H:%M:%S') 2>/dev/null | head -5 | while read -r file; do
            if [[ -f "$file" ]]; then
                local filename=$(basename "$file")
                local file_size=$(du -h "$file" | cut -f1)
                print_success "    $filename ($file_size)"
            fi
        done

        if [[ $hdf_count -gt 5 ]]; then
            print_success "    ... and $((hdf_count - 5)) more files"
        fi

        print_info "Next steps:"
        print_info "  1. Use modis_process_generic.sh to process the downloaded files"
        print_info "  2. Check the downloaded files with: gdalinfo <filename>"
        print_info "  3. Verify data with HDF tools or Python/R"

    else
        print_error "Download failed. Check error messages above."
        print_info "Common issues:"
        print_info "  - Check EARTHDATA_BEARER_TOKEN environment variable"
        print_info "  - Verify variable names with --list-variables"
        print_info "  - Ensure sufficient disk space"
        print_info "  - Check internet connection to NASA Earthdata"
        print_info "  - Verify that the requested time period has available data"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
