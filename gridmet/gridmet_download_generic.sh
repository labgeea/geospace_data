#!/bin/bash
#
# Generic GridMET Variable Download Wrapper Script
# ===============================================
#
# This bash wrapper provides a convenient interface for downloading any GridMET variable
# from the University of Idaho's THREDDS server with command-line argument parsing and validation.
#
# Usage:
#
#   ./gridmet_download_generic.sh --variables pr --year 2020 --month 1 --output-dir /data/GridMET/
#   ./gridmet_download_generic.sh --variables pr,tmmx --year 2020 --month 1
#   ./gridmet_download_generic.sh --variables weather --year 2019 --month 12
#   ./gridmet_download_generic.sh --list-variables
#   ./gridmet_download_generic.sh --help
#
# Author: GEOSPACE Project
# Date: 2025
# License: Public Domain

# Version information
VERSION="1.0.0"
MODULE_NAME="GridMET Download"

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
OUTPUT_DIR=""
LIST_VARIABLES=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/gridmet_download_generic.py"

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
Generic GridMET Variable Download Script

USAGE:
    $(basename "$0") [OPTIONS]

OPTIONS:
    -v, --variables LIST    Comma-separated list of variables to download (required)
    -y, --year YEAR         Year to download (required)
    -m, --month MONTH       Month to download (1-12) (required)
    -o, --output-dir DIR    Output directory (required)
    -l, --list-variables    List all available variables and aliases
    -h, --help              Show this help message

EXAMPLES:
    # Download single variable
    $(basename "$0") -v pr -y 2020 -m 1 -o /data/GridMET/

    # Download multiple variables
    $(basename "$0") --variables pr,tmmx -y 2020 -m 1 -o /data/GridMET/

    # Download weather package (precipitation, max temp, min temp)
    $(basename "$0") -v weather -y 2019 -m 12 -o /data/GridMET/

    # Download fire weather variables
    $(basename "$0") -v fire -y 2020 -m 6 -o /data/GridMET/

    # Download all variables
    $(basename "$0") -v all -y 2020 -m 1 -o /data/GridMET/

    # List all available variables
    $(basename "$0") --list-variables

COMMON VARIABLES:
    Primary Climate:
        pr (precipitation), tmmx (max temperature), tmmn (min temperature)
        rmax (max humidity), rmin (min humidity), sph (specific humidity)
        srad (solar radiation), vs (wind speed), th (wind direction)

    Fire Weather:
        bi (burning index), fm100 (100-hr fuel moisture), fm1000 (1000-hr fuel moisture)
        erc (energy release component)

    Evapotranspiration:
        etr (reference ET alfalfa), eto (reference ET grass), vpd (vapor pressure deficit)

    Drought Indices:
        pdsi (Palmer Drought Severity Index)

VARIABLE ALIASES:
    You can use shorter names for convenience:
        precipitation/precip/rain -> pr
        maximum_temperature/temp_max/tmax -> tmmx
        wind_speed/wind_velocity/wind -> vs
        burning_index/fire_index -> bi

PREDEFINED PACKAGES:
    Use these shortcuts for common variable combinations:
        --variables weather      # pr,tmmx,tmmn
        --variables temperature  # tmmx,tmmn
        --variables humidity     # rmax,rmin,sph,vpd
        --variables fire         # bi,fm100,fm1000,erc
        --variables evapotranspiration # etr,eto,vpd
        --variables wind         # vs,th
        --variables basic        # pr,tmmx,tmmn,vs
        --variables all          # All available variables

REQUIREMENTS:
    - Python 3.6+
    - xarray, requests, pandas, netCDF4, numpy
    - Internet connection for THREDDS OPeNDAP access

OUTPUT:
    - Single variable: gridmet_<variable>_YYYYMM.nc
    - Multiple variables: one file per variable
    - Download verification and statistics

DATA SOURCE:
    GridMET provides daily high-resolution (~4km) surface meteorological data
    covering CONUS from 1979-present via University of Idaho THREDDS server.

For more information visit: http://www.climatologylab.org/gridmet.html
EOF
}

# Function to expand variable packages
expand_variable_packages() {
    local vars="$1"

    # Replace predefined packages with variable lists
    vars="${vars//weather/pr,tmmx,tmmn}"
    vars="${vars//temperature/tmmx,tmmn}"
    vars="${vars//humidity/rmax,rmin,sph,vpd}"
    vars="${vars//fire/bi,fm100,fm1000,erc}"
    vars="${vars//evapotranspiration/etr,eto,vpd}"
    vars="${vars//wind/vs,th}"
    vars="${vars//basic/pr,tmmx,tmmn,vs}"
    vars="${vars//all/pr,tmmx,tmmn,rmax,rmin,sph,srad,vs,th,bi,fm100,fm1000,erc,etr,eto,vpd,pdsi}"

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

    # Check if year is provided and valid (unless listing variables)
    if [[ "$LIST_VARIABLES" != true ]]; then
        if [[ -z "$YEAR" ]]; then
            print_error "Year is required. Use -y or --year"
            ((errors++))
        elif ! [[ "$YEAR" =~ ^[0-9]{4}$ ]] || [[ "$YEAR" -lt 1979 ]] || [[ "$YEAR" -gt $(date +%Y) ]]; then
            print_error "Year must be between 1979 and $(date +%Y)"
            ((errors++))
        fi

        # Check if month is provided and valid
        if [[ -z "$MONTH" ]]; then
            print_error "Month is required. Use -m or --month"
            ((errors++))
        elif ! [[ "$MONTH" =~ ^[0-9]+$ ]] || [[ "$MONTH" -lt 1 ]] || [[ "$MONTH" -gt 12 ]]; then
            print_error "Month must be between 1 and 12"
            ((errors++))
        fi

        # Check if output directory is provided
        if [[ -z "$OUTPUT_DIR" ]]; then
            print_error "Output directory is required. Use -o or --output-dir"
            ((errors++))
        fi
    fi

    # Check if Python script exists
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Python script not found: $PYTHON_SCRIPT"
        print_info "Please ensure gridmet_download_generic.py is in the same directory"
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
    local packages=("xarray" "requests" "pandas" "numpy")
    for package in "${packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            print_error "$package library not found. Install with: pip install $package"
            ((errors++))
        fi
    done

    # Check internet connectivity to THREDDS server
    if [[ "$LIST_VARIABLES" != true ]]; then
        print_info "Checking connectivity to THREDDS server..."
        if ! curl -s --connect-timeout 10 "http://thredds.northwestknowledge.net:8080/thredds/" > /dev/null; then
            print_warning "Cannot reach THREDDS server. Check internet connection."
            print_info "Server: http://thredds.northwestknowledge.net:8080/thredds/"
            ((errors++))
        else
            print_success "THREDDS server connectivity confirmed"
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

# Function to estimate download requirements
estimate_download() {
    local vars="$1"
    local year="$2"
    local month="$3"

    print_info "Download estimates:"

    # Count variables
    local var_count=$(echo "$vars" | tr ',' '\n' | wc -l)
    print_info "  Variables: $var_count"

    # Days in month
    local days_in_month=$(python3 -c "import calendar; print(calendar.monthrange($year, $month)[1])")
    print_info "  Days in month: $days_in_month"
    print_info "  Data frequency: Daily (1 value per day per grid cell)"
    print_info "  Spatial resolution: ~4km (~1000x600 grid for CONUS)"

    # Estimate file sizes (rough)
    local estimated_size_per_var=$((days_in_month * 2))  # ~2MB per day per variable
    local total_estimated_size=$((var_count * estimated_size_per_var))

    print_info "  Estimated size per variable: ~${estimated_size_per_var} MB"
    print_info "  Total estimated size: ~${total_estimated_size} MB"

    # Time estimate
    local estimated_minutes=$((var_count * 2))  # ~2 minutes per variable
    if [[ $estimated_minutes -lt 1 ]]; then
        print_info "  Estimated download time: <1 minute"
    else
        print_info "  Estimated download time: ~${estimated_minutes} minutes"
    fi
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
            -o|--output-dir)
                OUTPUT_DIR="$2"
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
    print_header "GridMET Generic Variable Download Wrapper"
    print_header "========================================"

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

    # Show variable summary
    show_variable_summary "$VARIABLES"

    # Create output directory if it doesn't exist
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        print_info "Creating output directory: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi

    # Show configuration
    print_info "Configuration:"
    print_info "  Variables: $VARIABLES"
    print_info "  Year: $YEAR"
    print_info "  Month: $MONTH"
    print_info "  Output Directory: $OUTPUT_DIR"
    print_info "  Python Script: $PYTHON_SCRIPT"
    echo

    # Show estimates
    estimate_download "$VARIABLES" "$YEAR" "$MONTH"

    # Run the Python download script
    print_info "Starting download..."

    if python3 "$PYTHON_SCRIPT" \
        --variables "$VARIABLES" \
        --year "$YEAR" \
        --month "$MONTH" \
        --output-dir "$OUTPUT_DIR"; then

        print_success "Download completed successfully!"

        # Count output files and calculate total size
        local nc_count=$(find "$OUTPUT_DIR" -name "gridmet_*.nc" -type f 2>/dev/null | wc -l || echo "0")
        local total_size=$(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1 || echo "unknown")

        print_success "Output summary:"
        if [[ $nc_count -gt 0 ]]; then
            print_success "  NetCDF files: $nc_count"
        fi
        print_success "  Total output size: $total_size"
        print_success "  Output directory: $OUTPUT_DIR"

        # Show specific files created
        print_success "  Files created:"
        find "$OUTPUT_DIR" -name "gridmet_*.nc" -type f -newer <(date -d '5 minutes ago' '+%Y-%m-%d %H:%M:%S') 2>/dev/null | while read -r file; do
            if [[ -f "$file" ]]; then
                local filename=$(basename "$file")
                local file_size=$(du -h "$file" | cut -f1)
                print_success "    $filename ($file_size)"
            fi
        done

        print_info "Next steps:"
        print_info "  1. Use gridmet_process_generic.sh to process the downloaded files"
        print_info "  2. Check the downloaded files with: ncdump -h <filename>"
        print_info "  3. Verify data with: python -c \"import xarray as xr; ds = xr.open_dataset('<filename>'); print(ds)\""

    else
        print_error "Download failed. Check error messages above."
        print_info "Common issues:"
        print_info "  - Check internet connection to THREDDS server"
        print_info "  - Verify variable names with --list-variables"
        print_info "  - Ensure sufficient disk space"
        print_info "  - Check that the requested time period is available (1979-present)"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
