#!/bin/bash
#
# CAMS Air Pollution Download Wrapper Script
# ==========================================
#
# Bash wrapper for downloading CAMS air pollution variables from Copernicus CDS.
# Integrates with existing GEOSPACE framework patterns.
#
# Author: GEOSPACE Project
# Date: August 2025
# License: Public Domain
#
# Usage:
#     ./cams_download_generic.sh --variables pm25 --year 2020 --month 1
#     ./cams_download_generic.sh --variables air_quality --year 2020 --month 1
#     ./cams_download_generic.sh --list-variables
#

# Script metadata
#!/bin/bash

# Script metadata
SCRIPT_NAME="CAMS Air Pollution Download"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/cams_download_generic.py"

# Get version from framework
get_framework_version() {
    local version_file="$SCRIPT_DIR/../version.py"
    if [[ -f "$version_file" ]]; then
        # Extract version from version.py
        FRAMEWORK_VERSION=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR/..')
try:
    from version import get_module_version
    print(get_module_version('cams'))
except:
    print('1.2.0')
" 2>/dev/null)
        
        if [[ -n "$FRAMEWORK_VERSION" ]]; then
            echo "$FRAMEWORK_VERSION"
        else
            echo "1.2.0"  # Fallback
        fi
    else
        echo "1.2.0"  # Fallback if version file not found
    fi
}

SCRIPT_VERSION=$(get_framework_version)

# Default values
DEFAULT_VARIABLES="pm25"
DEFAULT_YEAR=$(date +%Y)
DEFAULT_MONTH=$(date +%m | sed 's/^0//')
DEFAULT_DATA_TYPE="reanalysis"
DEFAULT_BBOX="50,-125,24,-66"  # CONUS
DEFAULT_OUTPUT_DIR="./data/raw/CAMS/"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Function to show help
show_help() {
    cat << EOF
$SCRIPT_NAME v$SCRIPT_VERSION (GEOSPACE Framework v$(get_framework_version))

DESCRIPTION:
    Download CAMS (Copernicus Atmosphere Monitoring Service) air pollution variables
    from the Copernicus Climate Data Store for air quality analysis.
    
    Part of the GEOSPACE Framework for satellite and climate data processing.

USAGE:
    $(basename "$0") [OPTIONS]

OPTIONS:
    -v, --variables VARS     Comma-separated list of variables to download
                            (default: $DEFAULT_VARIABLES)
    -y, --year YEAR         Year to download (default: current year)
    -m, --month MONTH       Month to download 1-12 (default: current month)
    -t, --data-type TYPE    Dataset type: reanalysis, forecast (default: $DEFAULT_DATA_TYPE)
    -b, --bbox BBOX         Bounding box in W,S,E,N format (default: $DEFAULT_BBOX)
    -o, --output-dir DIR    Output directory (default: $DEFAULT_OUTPUT_DIR)
    
    --list-variables        List all available variables and packages
    --help                  Show this help message
    --version              Show version information

VARIABLE PACKAGES:
    air_quality            PM2.5, PM10, NO2, O3 (air quality)
    particulates           PM2.5, PM10 (particulate matter)
    trace_gases            NO2, SO2, CO (gaseous pollutants)
    pollution_full         All available air pollution variables

INDIVIDUAL VARIABLES:
    pm25            PM2.5 mass concentration
    pm10            PM10 mass concentration  
    no2             Nitrogen dioxide concentration
    so2             Sulfur dioxide concentration
    co              Carbon monoxide concentration
    o3              Ground-level ozone concentration

EXAMPLES:
    # Download PM2.5 for January 2020
    $(basename "$0") --variables pm25 --year 2020 --month 1

    # Download air quality package for current month
    $(basename "$0") --variables air_quality

    # Download multiple specific variables
    $(basename "$0") --variables pm25,no2_conc,o3 --year 2023 --month 6

    # Download with forecast data (near real-time)
    $(basename "$0") --variables air_quality --data-type forecast

    # Download for custom region (California)
    $(basename "$0") --variables pm25 --year 2020 --month 1 --bbox "42,-125,32,-114"

    # Download global data (remove spatial subsetting)
    $(basename "$0") --variables pm25 --year 2020 --month 1 --bbox "90,-180,-90,180"

    # List all available variables
    $(basename "$0") --list-variables

REQUIREMENTS:
    - CDS API credentials in ~/.cdsapirc
    - Python packages: cdsapi, xarray, pandas, numpy
    - Internet connection for CDS access
    - Accepted CAMS dataset license terms

DATA TYPES:
    reanalysis      Historical data (2003-present, 2-3 month delay) [RECOMMENDED]
    forecast        Near real-time data (2016-present, daily updates)

NOTES:
    - CAMS downloads may be queued - this is normal
    - Reanalysis data is recommended for scientific analysis
    - Files are typically 50-200 MB per variable per month
    - Processing can be done with cams_process_generic.sh

EOF
}

# Function to show version
# Function to show version
show_version() {
    echo "$SCRIPT_NAME v$SCRIPT_VERSION"
    echo "Part of GEOSPACE Framework"
    
    # Try to get full framework info
    local version_file="$SCRIPT_DIR/../version.py"
    if [[ -f "$version_file" ]]; then
        python3 -c "
import sys
sys.path.append('$SCRIPT_DIR/..')
try:
    from version import VERSION_INFO
    print(f'Framework Version: {VERSION_INFO[\"version\"]}')
    print(f'Author: {VERSION_INFO[\"author\"]}')
    print(f'License: {VERSION_INFO[\"license\"]}')
except:
    pass
" 2>/dev/null
    fi
    
    echo "Uses Copernicus Atmosphere Data Store API"
}

# Function to validate inputs
validate_inputs() {
    local variables="$1"
    local year="$2"
    local month="$3"
    local data_type="$4"
    local bbox="$5"
    local output_dir="$6"
    
    # Validate year
    current_year=$(date +%Y)
    if [[ ! "$year" =~ ^[0-9]{4}$ ]] || [ "$year" -lt 2003 ] || [ "$year" -gt "$current_year" ]; then
        print_error "Invalid year: $year. Must be between 2003 and $current_year"
        return 1
    fi
    
    # Validate month
    if [[ ! "$month" =~ ^[0-9]{1,2}$ ]] || [ "$month" -lt 1 ] || [ "$month" -gt 12 ]; then
        print_error "Invalid month: $month. Must be between 1 and 12"
        return 1
    fi
    
    # Validate data type
    if [[ "$data_type" != "reanalysis" ]] && [[ "$data_type" != "forecast" ]]; then
        print_error "Invalid data type: $data_type. Must be 'reanalysis' or 'forecast'"
        return 1
    fi
    
    # Validate bbox format
    if [[ -n "$bbox" ]]; then
        if [[ ! "$bbox" =~ ^-?[0-9]+\.?[0-9]*,-?[0-9]+\.?[0-9]*,-?[0-9]+\.?[0-9]*,-?[0-9]+\.?[0-9]*$ ]]; then
            print_error "Invalid bbox format: $bbox. Use 'north,west,south,east' (e.g., '50,-125,24,-66')"
            return 1
        fi
    fi

    # Check if variables is empty
    if [[ -z "$variables" ]]; then
        print_error "Variables cannot be empty"
        return 1
    fi
    
    return 0
}

# Function to check prerequisites
check_prerequisites() {
    local errors=0

    # Check framework integration
    if ! check_framework; then
        print_warning "Framework integration issues detected (script will still work)"
    fi
    
    # Check if Python script exists
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Python script not found: $PYTHON_SCRIPT"
        ((errors++))
    fi
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "python3 not found. Please install Python 3"
        ((errors++))
    fi
    
    # Check if required Python packages are available
    if ! python3 -c "import cdsapi" &> /dev/null; then
        print_error "cdsapi package not found. Install with: pip install cdsapi"
        ((errors++))
    fi
    
    # Check CDS API credentials
    if [[ ! -f "$HOME/.cdsapirc" ]]; then
        print_error "CDS API credentials not found. Please set up ~/.cdsapirc"
        print_error "Visit: https://cds.climate.copernicus.eu/ to get your credentials"
        ((errors++))
    fi
    
    return $errors
}

# Function to check framework compatibility
check_framework() {
    local version_file="$SCRIPT_DIR/../version.py"
    local framework_ok=true
    
    if [[ ! -f "$version_file" ]]; then
        print_warning "GEOSPACE Framework version file not found"
        print_warning "Script will run with fallback version"
        framework_ok=false
    else
        # Check if CAMS module is registered in framework
        local cams_registered=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR/..')
try:
    from version import VERSION_INFO
    print('cams' in VERSION_INFO['modules'])
except:
    print('False')
" 2>/dev/null)
        
        if [[ "$cams_registered" != "True" ]]; then
            print_warning "CAMS module not registered in framework version file"
            framework_ok=false
        fi
    fi
    
    return $([ "$framework_ok" = true ] && echo 0 || echo 1)
}



# Function to show system information
show_system_info() {
    print_header "System Information:"
    echo "  Script: $(basename "$0") v$SCRIPT_VERSION"
    echo "  Framework: GEOSPACE v$(get_framework_version)"
    echo "  Python: $(python3 --version 2>/dev/null || echo 'Not found')"
    echo "  Current directory: $(pwd)"
    echo "  CDS credentials: $(if [[ -f "$HOME/.cdsapirc" ]]; then echo "Found"; else echo "Not found"; fi)"
    echo ""
}

# Main execution function
main() {
    local variables="$DEFAULT_VARIABLES"
    local year="$DEFAULT_YEAR"
    local month="$DEFAULT_MONTH"
    local data_type="$DEFAULT_DATA_TYPE"
    local bbox="$DEFAULT_BBOX"
    local output_dir="$DEFAULT_OUTPUT_DIR"
    local list_variables=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--variables)
                variables="$2"
                shift 2
                ;;
            -y|--year)
                year="$2"
                shift 2
                ;;
            -m|--month)
                month="$2"
                shift 2
                ;;
            -t|--data-type)
                data_type="$2"
                shift 2
                ;;
            -b|--bbox)
                bbox="$2"
                shift 2
                ;;
            -o|--output-dir)
                output_dir="$2"
                shift 2
                ;;
            --list-variables)
                list_variables=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            --version)
                show_version
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Show header
    print_header "$SCRIPT_NAME v$SCRIPT_VERSION"
    print_header "=========================================="
    
    # Handle list variables request
    if [[ "$list_variables" == true ]]; then
        print_status "Listing available CAMS air pollution variables..."
        python3 "$PYTHON_SCRIPT" --list-variables
        exit $?
    fi
    
    # Show system information
    show_system_info
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    if ! check_prerequisites; then
        print_error "Prerequisites check failed. Please resolve the issues above."
        exit 1
    fi
    print_status "Prerequisites check passed"
    echo ""
    
    # Validate inputs
    print_status "Validating inputs..."
    if ! validate_inputs "$variables" "$year" "$month" "$data_type" "$bbox"; then
        exit 1
    fi
    print_status "Input validation passed"
    echo ""

    
    
    # Show download configuration
    print_header "Download Configuration:"
    echo "  Variables: $variables"
    echo "  Year: $year"
    echo "  Month: $month ($(date -d "$year-$month-01" "+%B"))"
    echo "  Data type: $data_type"
    echo "  Bounding box: $bbox $(if [[ "$bbox" == "$DEFAULT_BBOX" ]]; then echo "(CONUS)"; else echo "(custom)"; fi)"
    echo "  Output directory: $output_dir"
    echo ""
    
    # Create output directory
    print_status "Creating output directory: $output_dir"
    mkdir -p "$output_dir"
    
    # Warning about queue times
    if [[ "$data_type" == "reanalysis" ]]; then
        print_warning "CAMS reanalysis requests may be queued - this is normal"
    fi
    
    # Execute Python script
    print_status "Starting CAMS download..."

    python_args="--variables '$variables' --year $year --month $month --data-type $data_type --output-dir '$output_dir'"
    
    if [[ "$bbox" != "$DEFAULT_BBOX" ]] || [[ -n "$bbox" ]]; then
        python_args="$python_args --bbox '$bbox'"
    fi

    print_status "Executing: python3 $PYTHON_SCRIPT $python_args"
    echo ""
    
    # Run the download
     # Run the download
    python3 "$PYTHON_SCRIPT" \
        --variables "$variables" \
        --year "$year" \
        --month "$month" \
        --data-type "$data_type" \
        --bbox "$bbox" \
        --output-dir "$output_dir"
    
    local exit_code=$?
    
    echo ""
    
    # Report results
    if [[ $exit_code -eq 0 ]]; then
        print_status "CAMS download completed successfully!"

    else
        print_error "CAMS download failed with exit code: $exit_code"
        echo ""
        print_header "Troubleshooting:"
        echo "  1. Check CDS API credentials: cat ~/.cdsapirc"
        echo "  2. Verify dataset license terms are accepted"
        echo "  3. Check CDS service status and queue"
        echo "  4. Try downloading a single variable first"
        echo "  5. Check internet connection"
        echo ""
        print_header "Common Solutions:"
        echo "  - Request queued: Wait for processing (normal for CAMS)"
        echo "  - Credentials error: Update ~/.cdsapirc with valid key"
        echo "  - License error: Accept CAMS dataset terms on CDS website"
        echo "  - Network error: Check internet connection and firewall"
    fi
    
    exit $exit_code
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi