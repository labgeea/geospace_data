#!/bin/bash
#
# Generic ERA5 Single-Level Variable Download Wrapper Script
# =========================================================
#
# This bash wrapper provides a convenient interface for downloading any ERA5 single-level
# variable from the Copernicus Climate Data Store with command-line argument parsing and validation.
#
# Usage:
#   
#   ./download_era5_generic.sh --variables 2m_temperature --year 2020 --month 1 --output-dir /data/ERA5/
#   ./download_era5_generic.sh --variables 2m_temperature,surface_pressure --year 2020 --month 1
#   ./download_era5_generic.sh --list-variables
#   ./download_era5_generic.sh --help
#
# Author: GEOSPACE Project
# Date: 2025
# License: Public Domain

# Version information
VERSION="1.3.0"
MODULE_NAME="ECMWF Download"

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
PYTHON_SCRIPT="${SCRIPT_DIR}/era5_download_generic.py"

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
Generic ERA5 Single-Level Variable Download Script

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
    $(basename "$0") -v 2m_temperature -y 2020 -m 1 -o /data/ERA5/

    # Download multiple variables
    $(basename "$0") --variables 2m_temperature,surface_pressure -y 2020 -m 1 -o /data/ERA5/

    # Download weather package (temp, pressure, precip)
    $(basename "$0") -v 2m_temperature,surface_pressure,total_precipitation -y 2019 -m 12 -o /data/ERA5/

    # Download wind components
    $(basename "$0") -v 100m_u_component_of_wind,100m_v_component_of_wind -y 2020 -m 6 -o /data/ERA5/

    # List all available variables
    $(basename "$0") --list-variables

COMMON VARIABLES:
    Temperature & Humidity:
        2m_temperature, 2m_dewpoint_temperature, skin_temperature, relative_humidity

    Pressure:
        surface_pressure, mean_sea_level_pressure

    Precipitation:
        total_precipitation

    Wind:
        10m_u_component_of_wind, 10m_v_component_of_wind
        100m_u_component_of_wind, 100m_v_component_of_wind

    Atmospheric:
        boundary_layer_height, total_cloud_cover, geopotential

VARIABLE ALIASES:
    You can use shorter names for convenience:
        temp_2m, dewpoint_2m, sp, precip, u100, v100, blh, etc.

PREDEFINED PACKAGES:
    Use these shortcuts for common variable combinations:
        --variables weather      # 2m_temperature,surface_pressure,total_precipitation
        --variables wind         # 100m_u_component_of_wind,100m_v_component_of_wind
        --variables basic        # 2m_temperature,2m_dewpoint_temperature,surface_pressure
        --variables full         # All common variables

REQUIREMENTS:
    - Python 3.6+
    - cdsapi library (pip install cdsapi)
    - CDS API key configured (~/.cdsapirc)
    - xarray library for verification (pip install xarray)

OUTPUT:
    - Single variable: era5_<variable-name>_YYYYMM.nc
    - Multiple variables: era5_variables_YYYYMM.nc
    - Download log and verification report

For more information visit: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels
EOF
}

# Function to expand variable packages
expand_variable_packages() {
    local vars="$1"
    
    # Replace predefined packages with variable lists
    vars="${vars//weather/2m_temperature,surface_pressure,total_precipitation}"
    vars="${vars//wind/100m_u_component_of_wind,100m_v_component_of_wind}"
    vars="${vars//basic/2m_temperature,2m_dewpoint_temperature,surface_pressure}"
    vars="${vars//full/2m_temperature,2m_dewpoint_temperature,surface_pressure,total_precipitation,boundary_layer_height,100m_u_component_of_wind,100m_v_component_of_wind}"
    
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
        elif ! [[ "$YEAR" =~ ^[0-9]{4}$ ]] || [[ "$YEAR" -lt 1940 ]] || [[ "$YEAR" -gt $(date +%Y) ]]; then
            print_error "Year must be between 1940 and $(date +%Y)"
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
        print_info "Please ensure era5_download_generic.py is in the same directory"
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
    
    # Check cdsapi
    if ! python3 -c "import cdsapi" 2>/dev/null; then
        print_error "cdsapi library not found. Install with: pip install cdsapi"
        ((errors++))
    fi
    
    # Check CDS API key (only if not listing variables)
    if [[ "$LIST_VARIABLES" != true ]] && [[ ! -f "$HOME/.cdsapirc" ]]; then
        print_warning "CDS API key file not found at ~/.cdsapirc"
        print_info "Please set up your CDS API key: https://cds.climate.copernicus.eu/api-how-to"
        ((errors++))
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
    print_header "ERA5 Generic Variable Download Wrapper"
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
    
    # Estimate download size
    local var_count=$(echo "$VARIABLES" | tr ',' '\n' | wc -l)
    local days_in_month=$(cal $MONTH $YEAR | awk 'NF {DAYS = $NF} END {print DAYS}')
    local estimated_size=$((var_count * days_in_month * 24 * 2 / 1024))  # Rough estimate in MB
    
    print_info "Download estimate:"
    print_info "  Variables: $var_count"
    print_info "  Days in month: $days_in_month"
    print_info "  Hours per day: 24"
    print_info "  Estimated size: ~${estimated_size} MB"
    echo
    
    # Run the Python download script
    print_info "Starting download..."
    
    if python3 "$PYTHON_SCRIPT" \
        --variables "$VARIABLES" \
        --year "$YEAR" \
        --month "$MONTH" \
        --output-dir "$OUTPUT_DIR"; then
        
        print_success "Download completed successfully!"
        
        # Find the output file
        if [[ $(echo "$VARIABLES" | tr ',' '\n' | wc -l) -eq 1 ]]; then
            # Single variable - specific filename
            VAR_NAME=$(echo "$VARIABLES" | tr '_' '-')
            EXPECTED_FILE="$OUTPUT_DIR/era5_${VAR_NAME}_$(printf "%04d%02d" "$YEAR" "$MONTH").nc"
        else
            # Multiple variables - generic filename
            EXPECTED_FILE="$OUTPUT_DIR/era5_variables_$(printf "%04d%02d" "$YEAR" "$MONTH").nc"
        fi
        
        # Check for output file
        if [[ -f "$EXPECTED_FILE" ]]; then
            FILE_SIZE=$(du -h "$EXPECTED_FILE" | cut -f1)
            print_success "Output file: $EXPECTED_FILE ($FILE_SIZE)"
        else
            # Look for any ERA5 files created in the output directory
            OUTPUT_FILES=$(find "$OUTPUT_DIR" -name "era5_*.nc" -newer <(date -d '5 minutes ago' '+%Y-%m-%d %H:%M:%S') 2>/dev/null || true)
            if [[ -n "$OUTPUT_FILES" ]]; then
                print_success "Output files created:"
                echo "$OUTPUT_FILES" | while read -r file; do
                    if [[ -f "$file" ]]; then
                        FILE_SIZE=$(du -h "$file" | cut -f1)
                        print_success "  $(basename "$file") ($FILE_SIZE)"
                    fi
                done
            else
                print_warning "No output files found in $OUTPUT_DIR"
            fi
        fi
        
        print_info "Next steps:"
        print_info "  1. Use appropriate processing script for your variables"
        print_info "  2. Check the downloaded file with: ncdump -h <filename>"
        print_info "  3. Verify data with: python -c \"import xarray as xr; ds = xr.open_dataset('<filename>'); print(ds)\""
        
    else
        print_error "Download failed. Check error messages above."
        print_info "Common issues:"
        print_info "  - Check your CDS API key setup (~/.cdsapirc)"
        print_info "  - Verify variable names with --list-variables"
        print_info "  - Check internet connection"
        print_info "  - Ensure you have accepted the CDS license terms"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"