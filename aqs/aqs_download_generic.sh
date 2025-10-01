#!/bin/bash
#
# EPA AQS Criteria Pollutants Download Wrapper Script
# ==================================================
#
# Bash wrapper for downloading EPA AQS criteria air pollutant data using the EPA AQS API.
# Integrates with existing GEOSPACE framework patterns.
#
# Author: GEOSPACE Project
# Date: September 2025
# License: Public Domain
#
# Usage:
#     ./aqs_download_generic.sh --variables PM25 --year 2023 --state CA --output-dir ./data/raw/AQS/
#     ./aqs_download_generic.sh --variables criteria --year 2023 --state 06 --county 037
#     ./aqs_download_generic.sh --list-variables
#

# Script metadata
SCRIPT_NAME="EPA AQS Criteria Pollutants Download"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/aqs_download_generic.py"

# Get version from framework
get_framework_version() {
    local version_file="$SCRIPT_DIR/../version.py"
    if [[ -f "$version_file" ]]; then
        FRAMEWORK_VERSION=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR/..')
try:
    from version import get_module_version
    print(get_module_version('aqs'))
except:
    print('1.0.1')
" 2>/dev/null)
        
        if [[ -n "$FRAMEWORK_VERSION" ]]; then
            echo "$FRAMEWORK_VERSION"
        else
            echo "1.0.1"  # Fallback
        fi
    else
        echo "1.0.1"  # Fallback if version file not found
    fi
}

SCRIPT_VERSION=$(get_framework_version)

# Default values
DEFAULT_VARIABLES="PM25"
DEFAULT_YEAR=$(date +%Y)
DEFAULT_DATA_TYPE="daily"
DEFAULT_OUTPUT_DIR="./data/raw/AQS/"

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
$SCRIPT_NAME v$SCRIPT_VERSION

DESCRIPTION:
    Download EPA AQS criteria air pollutant data using the EPA AQS API.
    Part of the GEOSPACE Framework for satellite and climate data processing.

USAGE:
    $(basename "$0") [OPTIONS]

REQUIRED OPTIONS:
    -v, --variables VARS        Variables to download (default: $DEFAULT_VARIABLES)
                               Use comma-separated list: PM25,Ozone,NO2 or packages: criteria
    -y, --year YEAR            Year to download (default: $DEFAULT_YEAR)

OPTIONAL OPTIONS:
    -s, --state STATE          State FIPS code or abbreviation (e.g., CA, 06)
    -c, --county COUNTY        County FIPS code (3 digits, e.g., 037)
    --site SITE                Site number (4 digits, e.g., 0024)
    --data-type TYPE           Type of data (default: $DEFAULT_DATA_TYPE)
                               Options: sample, daily, annual
    -o, --output-dir DIR       Output directory (default: $DEFAULT_OUTPUT_DIR)
    
    --list-variables           List all available variables and exit
    --help                     Show this help message
    --version                  Show version information

SUPPORTED VARIABLES:
    PM25, PM10, Ozone, NO2, SO2, CO, Pb
    Packages: criteria, pm, gases, all

EXAMPLES:
    # Download PM2.5 data for California
    $(basename "$0") -v PM25 -y 2023 -s CA

    # Download all criteria pollutants for Los Angeles County
    $(basename "$0") -v criteria -y 2023 -s CA -c 037

    # Download ozone data for a specific monitoring site
    $(basename "$0") -v Ozone -y 2023 -s TX -c 201 --site 0024

API REQUIREMENTS:
    • EPA AQS API account (free registration)
    • Environment variables: EPA_AQS_EMAIL and EPA_AQS_KEY
    • Register at: https://aqs.epa.gov/aqsweb/documents/data_api.html#signup

NOTES:
    • State-level requests often timeout - try county-level requests for better reliability
    • EPA API has rate limits (10 requests per minute)
    • Data availability varies by pollutant, location, and year

EOF
}

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
}

# Function to validate inputs
validate_inputs() {
    local variables="$1"
    local year="$2"
    local state="$3"
    local county="$4"
    local site="$5"
    local data_type="$6"
    local output_dir="$7"
    
    # Validate year
    if [[ ! "$year" =~ ^[0-9]{4}$ ]] || [[ "$year" -lt 1980 ]] || [[ "$year" -gt $(date +%Y) ]]; then
        print_error "Invalid year: $year. Must be 4-digit year between 1980 and $(date +%Y)"
        return 1
    fi
    
    # Validate data type
    if [[ ! "$data_type" =~ ^(sample|daily|annual)$ ]]; then
        print_error "Invalid data type: $data_type. Must be sample, daily, or annual"
        return 1
    fi
    
    # Validate county/site dependencies
    if [[ -n "$county" ]] && [[ -z "$state" ]]; then
        print_error "County specified without state. State is required when specifying county"
        return 1
    fi
    
    if [[ -n "$site" ]] && [[ -z "$county" || -z "$state" ]]; then
        print_error "Site specified without county/state. Both state and county are required when specifying site"
        return 1
    fi
    
    # Validate output directory parent exists
    local parent_dir=$(dirname "$output_dir")
    if [[ ! -d "$parent_dir" ]]; then
        print_error "Parent directory does not exist: $parent_dir"
        return 1
    fi
    
    return 0
}

# Function to check prerequisites
check_prerequisites() {
    local errors=0
    
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
    local required_packages=("requests" "pandas" "numpy")
    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" &> /dev/null; then
            print_error "$package package not found. Install with: pip install $package"
            ((errors++))
        fi
    done
    
    # Check EPA AQS API credentials
    if [[ -z "$EPA_AQS_EMAIL" ]]; then
        print_error "EPA_AQS_EMAIL environment variable not set"
        ((errors++))
    fi
    
    if [[ -z "$EPA_AQS_KEY" ]]; then
        print_error "EPA_AQS_KEY environment variable not set"
        ((errors++))
    fi
    
    if [[ $errors -gt 0 ]]; then
        echo ""
        print_header "EPA AQS API Setup Instructions:"
        echo "1. Register for free account: https://aqs.epa.gov/aqsweb/documents/data_api.html#signup"
        echo "2. Get your API credentials from EPA"
        echo "3. Set environment variables:"
        echo "   export EPA_AQS_EMAIL=your_email@example.com"
        echo "   export EPA_AQS_KEY=your_api_key"
        echo "4. Install required packages: pip install requests pandas numpy"
    fi
    
    return $errors
}

# Function to check framework compatibility
check_framework() {
    local version_file="$SCRIPT_DIR/../version.py"
    local framework_ok=true
    
    if [[ ! -f "$version_file" ]]; then
        print_warning "GEOSPACE Framework version file not found"
        framework_ok=false
    else
        # Check if AQS module is registered in framework
        local aqs_registered=$(python3 -c "
import sys
sys.path.append('$SCRIPT_DIR/..')
try:
    from version import VERSION_INFO
    print('aqs' in VERSION_INFO['modules'])
except:
    print('False')
" 2>/dev/null)
        
        if [[ "$aqs_registered" != "True" ]]; then
            print_warning "AQS module not registered in framework version file"
            framework_ok=false
        fi
    fi
    
    return $([ "$framework_ok" = true ] && echo 0 || echo 1)
}

# Main execution function
main() {
    local variables="$DEFAULT_VARIABLES"
    local year="$DEFAULT_YEAR"
    local state=""
    local county=""
    local site=""
    local data_type="$DEFAULT_DATA_TYPE"
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
            -s|--state)
                state="$2"
                shift 2
                ;;
            -c|--county)
                county="$2"
                shift 2
                ;;
            --site)
                site="$2"
                shift 2
                ;;
            --data-type)
                data_type="$2"
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
        print_status "Listing available EPA AQS criteria pollutants..."
        python3 "$PYTHON_SCRIPT" --list-variables
        exit $?
    fi
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    if ! check_prerequisites; then
        print_error "Prerequisites check failed. Please resolve the issues above."
        exit 1
    fi
    print_status "Prerequisites check passed"
    
    # Check framework integration
    if ! check_framework; then
        print_warning "Framework integration issues detected (script will still work)"
    fi
    echo ""
    
    # Validate inputs
    print_status "Validating inputs..."
    if ! validate_inputs "$variables" "$year" "$state" "$county" "$site" "$data_type" "$output_dir"; then
        exit 1
    fi
    print_status "Input validation passed"
    echo ""
    
    # Show download configuration
    print_header "Download Configuration:"
    echo "  Variables: $variables"
    echo "  Year: $year"
    echo "  Data type: $data_type"
    if [[ -n "$state" ]]; then
        echo "  State: $state"
    fi
    if [[ -n "$county" ]]; then
        echo "  County: $county"
    fi
    if [[ -n "$site" ]]; then
        echo "  Site: $site"
    fi
    echo "  Output directory: $output_dir"
    echo ""
    
    # Warn about state-level requests
    if [[ -n "$state" ]] && [[ -z "$county" ]] && [[ -z "$site" ]]; then
        print_warning "State-level requests often timeout due to large dataset size"
        print_warning "Consider using county-level requests for better reliability"
        echo ""
    fi
    
    # Create output directory
    print_status "Creating output directory: $output_dir"
    mkdir -p "$output_dir"
    
    # Build Python command
    local python_args="--variables '$variables' --year $year --data-type '$data_type' --output-dir '$output_dir'"
    
    if [[ -n "$state" ]]; then
        python_args="$python_args --state '$state'"
    fi
    
    if [[ -n "$county" ]]; then
        python_args="$python_args --county '$county'"
    fi
    
    if [[ -n "$site" ]]; then
        python_args="$python_args --site '$site'"
    fi
    
    # Execute Python script
    print_status "Starting EPA AQS data download..."
    print_status "Executing: python3 $(basename $PYTHON_SCRIPT) $python_args"
    echo ""
    
    # Run the download
    eval "python3 '$PYTHON_SCRIPT' $python_args"
    local exit_code=$?
    
    echo ""
    
    # Report results
    if [[ $exit_code -eq 0 ]]; then
        # Check if any files were actually created
        local file_count=0
        if [[ -d "$output_dir" ]]; then
            file_count=$(find "$output_dir" -name "aqs_*.json" -type f | wc -l)
        fi
        
        if [[ $file_count -gt 0 ]]; then
            print_status "EPA AQS download completed successfully!"
            print_status "Downloaded air quality data saved to: $output_dir"
            print_status "Created $file_count output files"
            print_status "Ready for processing with aqs_process_generic.sh"
        else
            print_warning "EPA AQS download completed but no data files were created"
            print_warning "This usually indicates no data was available for the requested parameters"
            print_warning "For large geographic areas, try county-level requests instead"
            exit_code=1  # Treat as failure
        fi
        
    else
        print_error "EPA AQS download failed with exit code: $exit_code"
        echo ""
        print_header "Common Solutions:"
        echo "  - Check EPA AQS API credentials (EPA_AQS_EMAIL, EPA_AQS_KEY)"
        echo "  - Try smaller geographic areas (county instead of state)"
        echo "  - EPA servers may be slow - retry in a few minutes"
        echo "  - Use EPA's pre-compiled data files: https://aqs.epa.gov/aqsweb/airdata/"
    fi
    
    exit $exit_code
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi