#!/bin/bash
#
# EPA AQS Criteria Pollutants Processing Wrapper Script
# ====================================================
#
# Bash wrapper for processing EPA AQS criteria air pollutant data from JSON to analysis-ready formats.
# Integrates with existing GEOSPACE framework patterns.
#
# Author: GEOSPACE Project
# Date: September 2025
# License: Public Domain
#
# Usage:
#     ./aqs_process_generic.sh --input-file aqs_pm25_daily_2023.json --output-dir processed/
#     ./aqs_process_generic.sh --input-dir raw/AQS/ --output-dir processed/ --variables all
#

# Script metadata
SCRIPT_NAME="EPA AQS Criteria Pollutants Processing"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/aqs_process_generic.py"

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
    print('1.0.0')
" 2>/dev/null)
        
        if [[ -n "$FRAMEWORK_VERSION" ]]; then
            echo "$FRAMEWORK_VERSION"
        else
            echo "1.0.0"  # Fallback
        fi
    else
        echo "1.0.0"  # Fallback if version file not found
    fi
}

SCRIPT_VERSION=$(get_framework_version)

# Default values
DEFAULT_VARIABLES="all"
DEFAULT_OUTPUT_FORMATS="csv"
DEFAULT_OUTPUT_DIR="./data/processed/AQS/"

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
    Process EPA AQS criteria air pollutant data from JSON files to analysis-ready formats.
    Part of the GEOSPACE Framework for satellite and climate data processing.

USAGE:
    $(basename "$0") [OPTIONS]

REQUIRED OPTIONS (choose one input method):
    -i, --input-file FILE       Single AQS JSON file to process
    -d, --input-dir DIR         Directory containing AQS JSON files

    -o, --output-dir DIR        Output directory for processed files

OPTIONAL OPTIONS:
    -v, --variables VARS        Variables to process (default: $DEFAULT_VARIABLES)
                               Use comma-separated list: PM25,Ozone,NO2 or 'all'
    -f, --output-formats FMTS   Output formats (default: $DEFAULT_OUTPUT_FORMATS)
                               Options: csv, geojson (comma-separated)
    
    --help                     Show this help message
    --version                  Show version information

SUPPORTED VARIABLES:
    PM25, PM10, Ozone, NO2, SO2, CO, Pb, all

EXAMPLES:
    # Process single file
    $(basename "$0") -i aqs_pm25_daily_2023.json -o processed/

    # Process all files in directory
    $(basename "$0") -d raw/AQS/ -o processed/

    # Process specific pollutants
    $(basename "$0") -d raw/AQS/ -o processed/ -v PM25,Ozone -f csv,geojson

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
    local input_file="$1"
    local input_dir="$2"
    local output_dir="$3"
    
    # Check that exactly one input method is provided
    if [[ -n "$input_file" ]] && [[ -n "$input_dir" ]]; then
        print_error "Cannot specify both input file and input directory"
        return 1
    fi
    
    if [[ -z "$input_file" ]] && [[ -z "$input_dir" ]]; then
        print_error "Must specify either input file (-i) or input directory (-d)"
        return 1
    fi
    
    # Validate input file if provided
    if [[ -n "$input_file" ]]; then
        if [[ ! -f "$input_file" ]]; then
            print_error "Input file does not exist: $input_file"
            return 1
        fi
    fi
    
    # Validate input directory if provided
    if [[ -n "$input_dir" ]]; then
        if [[ ! -d "$input_dir" ]]; then
            print_error "Input directory does not exist: $input_dir"
            return 1
        fi
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
    local required_packages=("pandas" "numpy")
    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" &> /dev/null; then
            print_error "$package package not found. Install with: pip install $package"
            ((errors++))
        fi
    done
    
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
    local input_file=""
    local input_dir=""
    local output_dir="$DEFAULT_OUTPUT_DIR"
    local variables="$DEFAULT_VARIABLES"
    local output_formats="$DEFAULT_OUTPUT_FORMATS"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--input-file)
                input_file="$2"
                shift 2
                ;;
            -d|--input-dir)
                input_dir="$2"
                shift 2
                ;;
            -o|--output-dir)
                output_dir="$2"
                shift 2
                ;;
            -v|--variables)
                variables="$2"
                shift 2
                ;;
            -f|--output-formats)
                output_formats="$2"
                shift 2
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
    
    # Validate required arguments
    if [[ -z "$output_dir" ]]; then
        print_error "Output directory is required. Use -o or --output-dir"
        echo "Use --help for usage information"
        exit 1
    fi
    
    # Validate inputs
    print_status "Validating inputs..."
    if ! validate_inputs "$input_file" "$input_dir" "$output_dir"; then
        exit 1
    fi
    print_status "Input validation passed"
    echo ""
    
    # Show processing configuration
    print_header "Processing Configuration:"
    if [[ -n "$input_file" ]]; then
        echo "  Input file: $input_file"
    fi
    if [[ -n "$input_dir" ]]; then
        echo "  Input directory: $input_dir"
    fi
    echo "  Output directory: $output_dir"
    echo "  Variables: $variables"
    echo "  Output formats: $output_formats"
    echo ""
    
    # Create output directory
    print_status "Creating output directory: $output_dir"
    mkdir -p "$output_dir"
    
    # Build Python command
    local python_args=""
    
    if [[ -n "$input_file" ]]; then
        python_args="--input-file '$input_file'"
    else
        python_args="--input-dir '$input_dir'"
    fi
    
    python_args="$python_args --output-dir '$output_dir'"
    
    if [[ "$variables" != "$DEFAULT_VARIABLES" ]]; then
        python_args="$python_args --variables '$variables'"
    fi
    
    if [[ "$output_formats" != "$DEFAULT_OUTPUT_FORMATS" ]]; then
        python_args="$python_args --output-formats '$output_formats'"
    fi
    
    # Execute Python script
    print_status "Starting EPA AQS data processing..."
    print_status "Executing: python3 $(basename $PYTHON_SCRIPT) $python_args"
    echo ""
    
    # Run the processing
    eval "python3 '$PYTHON_SCRIPT' $python_args"
    
    local exit_code=$?
    
    echo ""
    
    # Report results
    if [[ $exit_code -eq 0 ]]; then
        print_status "EPA AQS processing completed successfully!"
        print_status "Processed air quality data saved to: $output_dir"
        
        # Show output files if directory exists
        if [[ -d "$output_dir" ]]; then
            local file_count=$(find "$output_dir" -name "aqs_*" -type f | wc -l)
            if [[ $file_count -gt 0 ]]; then
                print_status "Created $file_count output files"
            fi
        fi
        
    else
        print_error "EPA AQS processing failed with exit code: $exit_code"
        echo ""
        print_header "Common Solutions:"
        echo "  - Verify input files are valid EPA AQS JSON format"
        echo "  - Install missing packages: pip install pandas numpy"
        echo "  - For GeoJSON: pip install geopandas"
        echo "  - Check file permissions and disk space"
    fi
    
    exit $exit_code
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi