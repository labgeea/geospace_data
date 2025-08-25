#!/bin/bash
#
# Generic GridMET Variable Processing Wrapper Script
# =================================================
#
# This bash wrapper provides a convenient interface for processing any GridMET variable
# with command-line argument parsing, validation, and comprehensive options.
#
# Usage:
#   ./gridmet_process_generic.sh --input-file gridmet_data.nc --output-dir processed/ --variables all
#   ./gridmet_process_generic.sh -i gridmet_data.nc -o processed/ -v pr,tmmx
#   ./gridmet_process_generic.sh --input-file gridmet_data.nc --output-dir processed/ --variables weather --aggregation monthly
#   ./gridmet_process_generic.sh --help
#
# Author: GEOSPACE Project
# Date: 2025
# License: Public Domain

# Version information
VERSION="1.3.0"
MODULE_NAME="GridMET Processing"

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
INPUT_FILE=""
OUTPUT_DIR=""
VARIABLES="all"
AGGREGATION="daily"
OUTPUT_FORMAT="geotiff"
TARGET_CRS="EPSG:5070"
CHUNK_SIZE=""
DEBUG_FLAG=""
LIST_CONFIG=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/gridmet_process_generic.py"

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
Generic GridMET Variable Processing Script

USAGE:
    $(basename "$0") [OPTIONS]

OPTIONS:
    -i, --input-file FILE      Input NetCDF file (required)
    -o, --output-dir DIR       Output directory (required)
    -v, --variables LIST       Variables to process: 'all', comma-separated list, or predefined packages
    -a, --aggregation TYPE     Temporal aggregation: daily, monthly (default: daily)
    -f, --output-format FMT    Output format: geotiff, netcdf, both (default: geotiff)
    -c, --target-crs CRS       Target coordinate system (default: EPSG:5070)
    --chunk-size SIZE          Chunk size for memory management (optional)
    --list-config              List variable configurations and exit
    -d, --debug                Enable debug output
    -h, --help                 Show this help message

VARIABLES:
    Individual Variables:
        pr (precipitation), tmmx (max temperature), tmmn (min temperature)
        rmax (max humidity), rmin (min humidity), sph (specific humidity)
        srad (solar radiation), vs (wind speed), th (wind direction)
        bi (burning index), fm100 (100-hr fuel moisture), fm1000 (1000-hr fuel moisture)
        erc (energy release component), etr (reference ET alfalfa), eto (reference ET grass)
        vpd (vapor pressure deficit), pdsi (Palmer Drought Severity Index)

    Predefined Packages:
        weather      # pr, tmmx, tmmn
        temperature  # tmmx, tmmn
        humidity     # rmax, rmin, sph, vpd
        fire         # bi, fm100, fm1000, erc
        evapotranspiration # etr, eto, vpd
        wind         # vs, th
        all          # Process all variables found in file

EXAMPLES:
    # Process all variables with daily aggregation
    $(basename "$0") -i gridmet_pr_202001.nc -o processed/ -v all

    # Process specific variables
    $(basename "$0") -i gridmet_variables_202001.nc -o processed/ -v pr,tmmx

    # Process weather package with monthly aggregation
    $(basename "$0") -i gridmet_data.nc -o processed/ -v weather -a monthly

    # Process with NetCDF output format
    $(basename "$0") -i gridmet_data.nc -o processed/ -v pr -f netcdf

    # Process with custom CRS (keep original projection)
    $(basename "$0") -i gridmet_data.nc -o processed/ -v all -c EPSG:4326

    # Process with both output formats
    $(basename "$0") -i gridmet_data.nc -o processed/ -v fire -f both

    # Process single precipitation file
    $(basename "$0") -i gridmet_pr_202001.nc -o processed/ -v pr

    # List all variable configurations
    $(basename "$0") --list-config

PROCESSING FEATURES:
    Unit Conversions:
        - Temperature: Kelvin → Celsius
        - Specific humidity: kg/kg → g/kg
        - Vapor pressure deficit: Pa → kPa
        - Other variables: no conversion (already in appropriate units)

    Temporal Aggregation:
        - daily: No aggregation (preserve original daily resolution)
        - monthly: Calculate monthly means (or sums for precipitation/ET)

    Output Formats:
        - geotiff: Individual GeoTIFF files (one per variable/time)
        - netcdf: NetCDF files with proper metadata
        - both: Generate both formats

    Spatial Processing:
        - Reproject from WGS84 to target CRS
        - Preserve spatial resolution where possible
        - Apply appropriate resampling methods

REQUIREMENTS:
    - Python 3.6+
    - xarray, rioxarray, numpy, rasterio, pandas, psutil
    - Input file must be GridMET NetCDF format

OUTPUT FILES:
    GeoTIFF Format:
        - gridmet_<variable>_<aggregation>.tif (single time)
        - gridmet_<variable>_<aggregation>_<date>.tif (multiple times)

    NetCDF Format:
        - gridmet_<variable>_<aggregation>.nc

    Reports:
        - processing_report.json (machine-readable)
        - processing_report.txt (human-readable)

TARGET CRS OPTIONS:
    - EPSG:5070 (CONUS Albers Equal Area) - default, best for CONUS analysis
    - EPSG:4326 (WGS84 Geographic) - preserves original projection
    - EPSG:3857 (Web Mercator) - good for web mapping
    - Any valid EPSG code

PERFORMANCE NOTES:
    - Processing time depends on: number of variables, temporal resolution, spatial extent
    - Memory usage: ~1-4 GB for typical monthly files
    - Use --chunk-size for large files or limited memory systems
    - GeoTIFF output is generally faster than NetCDF for single variables
    - Monthly aggregation significantly reduces output file sizes

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

    echo "$vars"
}

# Function to validate inputs
validate_inputs() {
    local errors=0

    # Check if input file is provided and exists
    if [[ -z "$INPUT_FILE" ]] && [[ "$LIST_CONFIG" != true ]]; then
        print_error "Input file is required. Use -i or --input-file"
        ((errors++))
    elif [[ -n "$INPUT_FILE" ]] && [[ ! -f "$INPUT_FILE" ]]; then
        print_error "Input file not found: $INPUT_FILE"
        ((errors++))
    elif [[ -n "$INPUT_FILE" ]] && [[ ! "$INPUT_FILE" =~ \.nc$ ]]; then
        print_warning "Input file doesn't have .nc extension: $INPUT_FILE"
    fi

    # Check if output directory is provided (unless listing config)
    if [[ -z "$OUTPUT_DIR" ]] && [[ "$LIST_CONFIG" != true ]]; then
        print_error "Output directory is required. Use -o or --output-dir"
        ((errors++))
    fi

    # Validate aggregation option
    if [[ ! "$AGGREGATION" =~ ^(daily|monthly)$ ]]; then
        print_error "Aggregation must be: daily or monthly"
        ((errors++))
    fi

    # Validate output format
    if [[ ! "$OUTPUT_FORMAT" =~ ^(geotiff|netcdf|both)$ ]]; then
        print_error "Output format must be: geotiff, netcdf, or both"
        ((errors++))
    fi

    # Validate target CRS format
    if [[ ! "$TARGET_CRS" =~ ^EPSG:[0-9]+$ ]]; then
        print_error "Target CRS must be in EPSG:XXXX format (e.g., EPSG:5070)"
        ((errors++))
    fi

    # Validate chunk size if provided
    if [[ -n "$CHUNK_SIZE" ]] && ! [[ "$CHUNK_SIZE" =~ ^[0-9]+$ ]]; then
        print_error "Chunk size must be a positive integer"
        ((errors++))
    fi

    # Check if Python script exists
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Python script not found: $PYTHON_SCRIPT"
        print_info "Please ensure gridmet_process_generic.py is in the same directory"
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
    local packages=("xarray" "rioxarray" "numpy" "rasterio" "pandas" "psutil")
    for package in "${packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            print_error "$package library not found. Install with: pip install $package"
            ((errors++))
        fi
    done

    return $errors
}

# Function to get file info
get_file_info() {
    local file="$1"

    print_info "Input file information:"
    print_info "  Path: $file"
    print_info "  Size: $(du -h "$file" | cut -f1)"
    print_info "  Modified: $(date -r "$file" '+%Y-%m-%d %H:%M:%S')"

    if command -v ncdump &> /dev/null; then
        print_info "  NetCDF structure:"
        ncdump -h "$file" 2>/dev/null | grep -E "(variables:|dimensions:)" | head -10 | sed 's/^/    /'

        # Get variable list
        local vars=$(ncdump -h "$file" 2>/dev/null | grep -A 100 "variables:" | grep -E "^\s+[a-zA-Z]" | sed 's/.*\([a-zA-Z0-9_]*\)(.*/\1/' | grep -v "^$" | sort | tr '\n' ',' | sed 's/,$//')
        if [[ -n "$vars" ]]; then
            print_info "  Variables: $vars"
        fi
    else
        print_warning "Install netcdf-bin for detailed file information: apt-get install netcdf-bin"
    fi
}

# Function to estimate processing requirements
estimate_processing() {
    local file="$1"
    local vars="$2"
    local format="$3"

    print_info "Processing estimates:"

    # File size
    local file_size_mb=$(du -m "$file" | cut -f1)
    print_info "  Input file size: ${file_size_mb} MB"

    # Estimate output size
    local var_count=1
    if [[ "$vars" == "all" ]]; then
        var_count=3  # Rough estimate for typical GridMET files
    else
        var_count=$(echo "$vars" | tr ',' '\n' | wc -l)
    fi

    local format_multiplier=1
    if [[ "$format" == "both" ]]; then
        format_multiplier=2
    fi

    local estimated_output_mb=$((file_size_mb * var_count * format_multiplier / 2))  # Rough compression estimate
    print_info "  Estimated output size: ~${estimated_output_mb} MB"
    print_info "  Variables to process: $var_count"
    print_info "  Estimated memory needed: ~$((file_size_mb * 2)) MB"

    # Time estimate
    local estimated_minutes=$((file_size_mb / 100))  # Rough estimate: 100 MB/minute
    if [[ $estimated_minutes -lt 1 ]]; then
        print_info "  Estimated processing time: <1 minute"
    else
        print_info "  Estimated processing time: ~${estimated_minutes} minutes"
    fi
}

# Function to show variable summary
show_variable_summary() {
    local vars="$1"

    print_header "Processing Configuration:"
    print_header "========================"

    if [[ "$vars" == "all" ]]; then
        print_info "Variables: All variables found in input file"
    else
        # Expand packages and count variables
        local expanded_vars=$(expand_variable_packages "$vars")
        local var_count=$(echo "$expanded_vars" | tr ',' '\n' | wc -l)

        print_info "Variables ($var_count):"
        echo "$expanded_vars" | tr ',' '\n' | while read -r var; do
            if [[ -n "$var" ]]; then
                print_variable "  - $var"
            fi
        done
    fi
    echo
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--input-file)
                INPUT_FILE="$2"
                shift 2
                ;;
            -o|--output-dir)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            -v|--variables)
                VARIABLES="$2"
                shift 2
                ;;
            -a|--aggregation)
                AGGREGATION="$2"
                shift 2
                ;;
            -f|--output-format)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            -c|--target-crs)
                TARGET_CRS="$2"
                shift 2
                ;;
            --chunk-size)
                CHUNK_SIZE="$2"
                shift 2
                ;;
            --list-config)
                LIST_CONFIG=true
                shift
                ;;
            -d|--debug)
                DEBUG_FLAG="--debug"
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
    print_header "GridMET Generic Variable Processing Wrapper"
    print_header "==========================================="

    # Parse arguments
    parse_args "$@"

    # Handle list config request
    if [[ "$LIST_CONFIG" == true ]]; then
        print_info "Listing variable configurations..."
        if python3 "$PYTHON_SCRIPT" --list-config; then
            exit 0
        else
            print_error "Failed to list configurations"
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
    if [[ "$VARIABLES" != "all" ]]; then
        VARIABLES=$(expand_variable_packages "$VARIABLES")
    fi

    # Show variable summary
    show_variable_summary "$VARIABLES"

    # Create output directory if it doesn't exist
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        print_info "Creating output directory: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi

    # Show configuration
    print_info "Configuration:"
    print_info "  Input File: $INPUT_FILE"
    print_info "  Output Directory: $OUTPUT_DIR"
    print_info "  Variables: $VARIABLES"
    print_info "  Aggregation: $AGGREGATION"
    print_info "  Output Format: $OUTPUT_FORMAT"
    print_info "  Target CRS: $TARGET_CRS"
    if [[ -n "$CHUNK_SIZE" ]]; then
        print_info "  Chunk Size: $CHUNK_SIZE"
    fi
    print_info "  Python Script: $PYTHON_SCRIPT"
    if [[ -n "$DEBUG_FLAG" ]]; then
        print_info "  Debug Mode: Enabled"
    fi
    echo

    # Show input file info and estimates
    get_file_info "$INPUT_FILE"
    echo
    estimate_processing "$INPUT_FILE" "$VARIABLES" "$OUTPUT_FORMAT"
    echo

    # Build Python command with all arguments
    PYTHON_CMD="python3 \"$PYTHON_SCRIPT\" --input-file \"$INPUT_FILE\" --output-dir \"$OUTPUT_DIR\" --variables \"$VARIABLES\" --aggregation \"$AGGREGATION\" --output-format \"$OUTPUT_FORMAT\" --target-crs \"$TARGET_CRS\""

    # Add optional arguments
    if [[ -n "$CHUNK_SIZE" ]]; then
        PYTHON_CMD="$PYTHON_CMD --chunk-size $CHUNK_SIZE"
    fi

    if [[ -n "$DEBUG_FLAG" ]]; then
        PYTHON_CMD="$PYTHON_CMD $DEBUG_FLAG"
    fi

    # Run the Python processing script
    print_info "Starting processing..."
    print_info "Command: $PYTHON_CMD"
    echo

    local start_time=$(date +%s)

    # Execute the command
    if eval "$PYTHON_CMD"; then

        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        print_success "Processing completed successfully in ${duration}s!"

        # Count output files and calculate total size
        local geotiff_count=$(find "$OUTPUT_DIR" -name "*.tif" -type f 2>/dev/null | wc -l || echo "0")
        local netcdf_count=$(find "$OUTPUT_DIR" -name "*.nc" -type f 2>/dev/null | wc -l || echo "0")
        local total_size=$(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1 || echo "unknown")

        print_success "Output summary:"
        if [[ $geotiff_count -gt 0 ]]; then
            print_success "  GeoTIFF files: $geotiff_count"
        fi
        if [[ $netcdf_count -gt 0 ]]; then
            print_success "  NetCDF files: $netcdf_count"
        fi
        print_success "  Total output size: $total_size"
        print_success "  Output directory: $OUTPUT_DIR"

        # Check for processing reports
        local json_report="$OUTPUT_DIR/processing_report.json"
        local txt_report="$OUTPUT_DIR/processing_report.txt"

        if [[ -f "$json_report" ]]; then
            print_success "  JSON report: $json_report"
        fi
        if [[ -f "$txt_report" ]]; then
            print_success "  Text report: $txt_report"
        fi

        print_info "Next steps:"
        print_info "  - Review processing reports for details"
        print_info "  - Check output files with GIS software"
        print_info "  - Use files for your analysis workflow"

    else
        local exit_code=$?
        print_error "Processing failed with exit code $exit_code. Check error messages above."

        print_info "Common troubleshooting:"
        print_info "  - Verify input file format and variables"
        print_info "  - Check available memory (processing may need 1-4 GB)"
        print_info "  - Ensure output directory has sufficient space"
        print_info "  - Try processing fewer variables or smaller chunks"

        exit $exit_code
    fi
}

# Run main function with all arguments
main "$@"
