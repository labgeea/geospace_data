#!/bin/bash
#
# CAMS Air Pollution Processing Wrapper Script
# =============================================
#
# Bash wrapper for processing CAMS air pollution variables from NetCDF to analysis-ready formats.
# Integrates with existing GEOSPACE framework patterns.
#
# Author: GEOSPACE Project
# Date: August 2025
# License: Public Domain
#
# Usage:
#     ./cams_process_generic.sh --input-file cams_pm25_202001.nc --output-dir processed/
#     ./cams_process_generic.sh --input-file cams_data.nc --output-dir processed/ --variables all
#     ./cams_process_generic.sh --list-config
#

# Script metadata
SCRIPT_NAME="CAMS Air Pollution Processing"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/cams_process_generic.py"

# Get version from framework
get_framework_version() {
    local version_file="$SCRIPT_DIR/../version.py"
    if [[ -f "$version_file" ]]; then
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
DEFAULT_VARIABLES="all"
DEFAULT_AGGREGATION="daily"
DEFAULT_OUTPUT_FORMAT="geotiff"
DEFAULT_TARGET_CRS="EPSG:5070"
DEFAULT_OUTPUT_DIR="./data/processed/CAMS/"

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
    Process CAMS (Copernicus Atmosphere Monitoring Service) air pollution variables
    from NetCDF files to analysis-ready GeoTIFF or NetCDF formats.
    
    Part of the GEOSPACE Framework for satellite and climate data processing.

USAGE:
    $(basename "$0") [OPTIONS]

REQUIRED OPTIONS:
    -i, --input-file FILE       Input CAMS NetCDF file path
    -o, --output-dir DIR        Output directory for processed files

OPTIONAL OPTIONS:
    -v, --variables VARS        Variables to process (default: $DEFAULT_VARIABLES)
                               Use comma-separated list: pm25,no2,co or packages: all
    -a, --aggregation TYPE      Temporal aggregation (default: $DEFAULT_AGGREGATION)
                               Options: hourly, daily, monthly
    -f, --output-format FMT     Output format (default: $DEFAULT_OUTPUT_FORMAT)
                               Options: geotiff, netcdf, both
    -c, --target-crs CRS        Target coordinate system (default: $DEFAULT_TARGET_CRS)
                               Example: EPSG:4326, EPSG:5070
    --chunk-size SIZE           Memory management chunk size (optional)
    --create-stacks            Create time-series raster stacks instead of individual files
    
    --list-config              List all variable configurations and exit
    --debug                    Enable debug output
    --help                     Show this help message
    --version                  Show version information

SUPPORTED VARIABLES:
    Air Pollution Variables:
      pm25            PM2.5 mass concentration (μg/m³)
      pm10            PM10 mass concentration (μg/m³)  
      no2             Nitrogen dioxide concentration (μg/m³)
      so2             Sulfur dioxide concentration (μg/m³)
      co              Carbon monoxide concentration (mg/m³)
      o3              Ground-level ozone concentration (μg/m³)

    Variable Packages:
      all             All available variables in the file

EXAMPLES:
    # Process all variables with default settings
    $(basename "$0") -i cams_pm25_202001.nc -o processed/

    # Process specific air pollution variables
    $(basename "$0") -i cams_data.nc -o processed/ -v pm25,no2,o3

    # Process with daily aggregation and both output formats
    $(basename "$0") -i cams_data.nc -o processed/ -v all -a daily -f both

    # Create time-series stacks instead of individual files
    $(basename "$0") -i cams_pm25_202001.nc -o processed/ --create-stacks

    # Process with custom projection for regional analysis
    $(basename "$0") -i cams_data.nc -o processed/ -c EPSG:4326

    # Process with monthly aggregation and NetCDF output
    $(basename "$0") -i cams_data.nc -o processed/ -v pm25 -a monthly -f netcdf

    # List available variable configurations
    $(basename "$0") --list-config

FEATURES:
    • Automatic unit conversions (kg/m³ → μg/m³, mg/m³)
    • Handles both 3D and 4D CAMS data (automatically removes extra dimensions)
    • Spatial reprojection to any coordinate system
    • Temporal aggregation (hourly, daily, monthly)
    • Time-series stack creation option
    • Memory-efficient chunked processing
    • Comprehensive validation and range checking

INPUT FILES:
    • CAMS NetCDF files from Copernicus ADS
    • Both 3D (PM2.5, PM10) and 4D (CO, trace gases) formats supported
    • Single or multi-variable files

OUTPUT FILES:
    • GeoTIFF: Compressed, tiled raster files
    • NetCDF: CF-compliant with proper metadata
    • Individual time-step files or time-series stacks
    • CONUS Albers projection (EPSG:5070) by default

REQUIREMENTS:
    • Python 3.7+ with xarray, rioxarray, numpy, rasterio, pandas, psutil
    • Input NetCDF file downloaded from CAMS/ADS
    • Sufficient disk space for output files

NOTES:
    • Processing time varies by file size and number of variables
    • Large time-series may require chunking for memory efficiency
    • Use --create-stacks for time-series analysis workflows
    • CONUS spatial subset is applied automatically

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
    
    echo "CAMS air pollution data processing capabilities"
}

# Function to validate inputs
validate_inputs() {
    local input_file="$1"
    local output_dir="$2"
    local variables="$3"
    local aggregation="$4"
    local output_format="$5"
    local target_crs="$6"
    
    # Validate input file
    if [[ ! -f "$input_file" ]]; then
        print_error "Input file does not exist: $input_file"
        return 1
    fi
    
    if [[ ! "$input_file" =~ \.nc$ ]]; then
        print_warning "Input file does not have .nc extension: $input_file"
    fi
    
    # Validate output directory parent exists
    local parent_dir=$(dirname "$output_dir")
    if [[ ! -d "$parent_dir" ]]; then
        print_error "Parent directory does not exist: $parent_dir"
        return 1
    fi
    
    # Validate aggregation
    if [[ ! "$aggregation" =~ ^(hourly|daily|monthly)$ ]]; then
        print_error "Invalid aggregation: $aggregation. Must be hourly, daily, or monthly"
        return 1
    fi
    
    # Validate output format
    if [[ ! "$output_format" =~ ^(geotiff|netcdf|both)$ ]]; then
        print_error "Invalid output format: $output_format. Must be geotiff, netcdf, or both"
        return 1
    fi
    
    # Validate CRS format
    if [[ ! "$target_crs" =~ ^EPSG:[0-9]+$ ]]; then
        print_error "Invalid CRS format: $target_crs. Use format EPSG:XXXX"
        return 1
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
    local required_packages=("xarray" "rioxarray" "numpy" "rasterio" "pandas" "psutil")
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
    echo "  Python script: $(basename "$PYTHON_SCRIPT")"
    echo ""
}

# Function to estimate processing requirements
estimate_processing() {
    local input_file="$1"
    local variables="$2"
    local output_format="$3"
    
    if [[ -f "$input_file" ]]; then
        local file_size_mb=$(( $(stat -f%z "$input_file" 2>/dev/null || stat -c%s "$input_file" 2>/dev/null || echo 0) / 1024 / 1024 ))
        print_header "Processing Estimates:"
        echo "  Input file size: ${file_size_mb} MB"
        
        # Rough estimates based on file size and format
        local output_multiplier=1
        if [[ "$output_format" == "both" ]]; then
            output_multiplier=2
        fi
        
        local estimated_output=$(( file_size_mb * output_multiplier ))
        echo "  Estimated output size: ~${estimated_output} MB"
        
        local estimated_time=10
        if [[ $file_size_mb -gt 100 ]]; then
            estimated_time=30
        fi
        echo "  Estimated processing time: ~${estimated_time}s"
        echo ""
    fi
}

# Main execution function
main() {
    local input_file=""
    local output_dir="$DEFAULT_OUTPUT_DIR"
    local variables="$DEFAULT_VARIABLES"
    local aggregation="$DEFAULT_AGGREGATION"
    local output_format="$DEFAULT_OUTPUT_FORMAT"
    local target_crs="$DEFAULT_TARGET_CRS"
    local chunk_size=""
    local create_stacks=false
    local list_config=false
    local debug=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--input-file)
                input_file="$2"
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
            -a|--aggregation)
                aggregation="$2"
                shift 2
                ;;
            -f|--output-format)
                output_format="$2"
                shift 2
                ;;
            -c|--target-crs)
                target_crs="$2"
                shift 2
                ;;
            --chunk-size)
                chunk_size="$2"
                shift 2
                ;;
            --create-stacks)
                create_stacks=true
                shift
                ;;
            --list-config)
                list_config=true
                shift
                ;;
            --debug)
                debug=true
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
    
    # Handle list config request
    if [[ "$list_config" == true ]]; then
        print_status "Listing available CAMS air pollution variable configurations..."
        python3 "$PYTHON_SCRIPT" --list-config
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
    
    # Check framework integration
    if ! check_framework; then
        print_warning "Framework integration issues detected (script will still work)"
    fi
    echo ""
    
    # Validate required arguments
    if [[ -z "$input_file" ]]; then
        print_error "Input file is required. Use -i or --input-file"
        echo "Use --help for usage information"
        exit 1
    fi
    
    # Validate inputs
    print_status "Validating inputs..."
    if ! validate_inputs "$input_file" "$output_dir" "$variables" "$aggregation" "$output_format" "$target_crs"; then
        exit 1
    fi
    print_status "Input validation passed"
    echo ""
    
    # Show processing configuration
    print_header "Processing Configuration:"
    echo "  Input file: $input_file"
    echo "  Output directory: $output_dir"
    echo "  Variables: $variables"
    echo "  Aggregation: $aggregation"
    echo "  Output format: $output_format"
    echo "  Target CRS: $target_crs"
    if [[ "$create_stacks" == true ]]; then
        echo "  Create stacks: Yes"
    fi
    if [[ -n "$chunk_size" ]]; then
        echo "  Chunk size: $chunk_size"
    fi
    echo ""
    
    # Show processing estimates
    estimate_processing "$input_file" "$variables" "$output_format"
    
    # Create output directory
    print_status "Creating output directory: $output_dir"
    mkdir -p "$output_dir"
    
    # Build Python command
    local python_args="--input-file '$input_file' --output-dir '$output_dir' --variables '$variables' --aggregation '$aggregation' --output-format '$output_format' --target-crs '$target_crs'"
    
    if [[ "$create_stacks" == true ]]; then
        python_args="$python_args --create-stacks"
    fi
    
    if [[ -n "$chunk_size" ]]; then
        python_args="$python_args --chunk-size $chunk_size"
    fi
    
    if [[ "$debug" == true ]]; then
        python_args="$python_args --debug"
    fi
    
    # Execute Python script
    print_status "Starting CAMS air pollution processing..."
    print_status "Executing: python3 $(basename $PYTHON_SCRIPT) $python_args"
    echo ""
    
    # Run the processing
    eval "python3 '$PYTHON_SCRIPT' $python_args"
    
    local exit_code=$?
    
    echo ""
    
    # Report results
    if [[ $exit_code -eq 0 ]]; then
        print_status "CAMS processing completed successfully!"
        print_status "Processed air pollution variables saved to: $output_dir"
        
        # Show output files if directory exists
        if [[ -d "$output_dir" ]]; then
            local file_count=$(find "$output_dir" -name "cams_*" -type f | wc -l)
            if [[ $file_count -gt 0 ]]; then
                print_status "Created $file_count output files"
            fi
        fi
        
    else
        print_error "CAMS processing failed with exit code: $exit_code"
        echo ""
        print_header "Troubleshooting:"
        echo "  1. Check input file format and accessibility"
        echo "  2. Verify sufficient disk space in output directory"
        echo "  3. Ensure Python packages are properly installed"
        echo "  4. Try processing with --debug for detailed output"
        echo "  5. Check file permissions"
        echo ""
        print_header "Common Solutions:"
        echo "  - NetCDF error: Verify file is valid CAMS NetCDF format"
        echo "  - Memory error: Use --chunk-size to reduce memory usage"
        echo "  - CRS error: Use standard projections like EPSG:4326 or EPSG:5070"
        echo "  - Variable error: Use --list-config to see available variables"
        echo "  - Permission error: Check write permissions to output directory"
    fi
    
    exit $exit_code
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi