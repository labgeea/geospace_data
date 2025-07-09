#!/usr/bin/env bash

# modis_process_generic.sh
# =========================
# Bash wrapper for modis_process_generic.py
# Supports flexible argument parsing, input validation, and multi-variable processing
# Author: GEOSPACE Project
# Date: July 2025
# License: Public Domain


# Version information
VERSION="1.0.0"
MODULE_NAME="MODIS Processing"

# Version display function
show_version() {
    echo "$MODULE_NAME Framework v$VERSION"
    exit 0
}

# Check for version argument
if [[ "$1" == "--version" || "$1" == "-V" ]]; then
    show_version
fi

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/modis_process_generic.py"

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_header() { echo -e "${PURPLE}$1${NC}"; }

# Variable groups for convenience
declare -A VARIABLE_GROUPS=(
    ["vegetation"]="NDVI,EVI"
    ["temperature"]="LST_Day,LST_Night"
    ["forest"]="Percent_Tree_Cover,Percent_NonTree_Vegetation"
    ["all"]="NDVI,EVI,LST_Day,LST_Night,Percent_Tree_Cover,Percent_NonTree_Vegetation"
)

print_usage() {
cat <<EOF

Generic MODIS Processing Wrapper
================================

Usage:
  $0 --variable <VAR> --input-dir <DIR> --output-dir <DIR> (--date YYYY-MM-DD | --year YYYY --month MM) [options]

Required arguments:
  --variable        Variable(s) to process (e.g., NDVI, LST_Day, Percent_Tree_Cover)
                    Can be comma-separated list: NDVI,EVI
                    Or predefined groups: vegetation, temperature, forest, all
  --input-dir       Path to directory with raw MODIS HDF files
  --output-dir      Path to directory for processed output

Time selection (choose one):
  --date            Specific date to process (YYYY-MM-DD)
  --start-date      Start date for date range processing (YYYY-MM-DD)
  --end-date        End date for date range processing (YYYY-MM-DD)
  --year            Year of data to process (used with --month)
  --month           Month of data to process (used with --year)

Optional arguments:
  --product         MODIS product prefix to filter (e.g., MOD11A1, MYD13A3)
  --config          Custom config JSON or YAML file
  --no-quality-mask Disable quality masking
  --verbose         Enable verbose output
  --dry-run         Show what would be processed without running
  --parallel        Process multiple variables in parallel (experimental)
  --create-config-template <path>   Create a config template and exit
  --test-vcf        Run VCF configuration test and exit
  -h, --help        Show this help message and exit

Variable Groups:
  vegetation        NDVI, EVI
  temperature       LST_Day, LST_Night
  forest            Percent_Tree_Cover, Percent_NonTree_Vegetation
  all               All supported variables

Examples:
  # Single variable, single date
  $0 --variable NDVI --input-dir ./raw/NDVI --output-dir ./proc/NDVI --date 2020-01-01

  # Multiple variables from same input
  $0 --variable NDVI,EVI --input-dir ./raw/NDVI --output-dir ./proc --year 2020 --month 1

  # Variable group
  $0 --variable vegetation --input-dir ./raw/NDVI --output-dir ./proc --date 2020-01-01

  # Date range processing
  $0 --variable LST_Day --input-dir ./raw/LST --output-dir ./proc/LST --start-date 2020-01-01 --end-date 2020-01-07

  # With custom configuration
  $0 --variable all --input-dir ./raw --output-dir ./proc --date 2020-01-01 --config custom.json

  # Dry run to see what would be processed
  $0 --variable vegetation --input-dir ./raw/NDVI --output-dir ./proc --date 2020-01-01 --dry-run

EOF
}

# Function to expand variable groups
expand_variables() {
    vars="$1"
    expanded=""
    
    IFS=',' read -ra VAR_LIST <<< "$vars"
    for var in "${VAR_LIST[@]}"; do
        var=$(echo "$var" | xargs)  # Trim whitespace
        
        # Check if it's a group
        if [[ -v VARIABLE_GROUPS["$var"] ]]; then
            if [[ -n "$expanded" ]]; then
                expanded="$expanded,${VARIABLE_GROUPS[$var]}"
            else
                expanded="${VARIABLE_GROUPS[$var]}"
            fi
        else
            if [[ -n "$expanded" ]]; then
                expanded="$expanded,$var"
            else
                expanded="$var"
            fi
        fi
    done
    
    # Remove duplicates
    echo "$expanded" | tr ',' '\n' | sort -u | tr '\n' ',' | sed 's/,$//'
}

# Function to validate inputs
validate_inputs() {
    errors=0
    
    # Check if Python script exists
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Python script not found: $PYTHON_SCRIPT"
        ((errors++))
    fi
    
    # Check required arguments
    if [[ -z "$VARIABLE" ]]; then
        print_error "--variable is required"
        ((errors++))
    fi
    
    if [[ -z "$INPUT_DIR" ]]; then
        print_error "--input-dir is required"
        ((errors++))
    elif [[ ! -d "$INPUT_DIR" ]]; then
        print_error "Input directory does not exist: $INPUT_DIR"
        ((errors++))
    fi
    
    if [[ -z "$OUTPUT_DIR" ]]; then
        print_error "--output-dir is required"
        ((errors++))
    fi
    
    # Check time specification
    time_options=0
    [[ -n "$DATE" ]] && ((time_options++))
    [[ -n "$START_DATE" && -n "$END_DATE" ]] && ((time_options++))
    [[ -n "$YEAR" && -n "$MONTH" ]] && ((time_options++))
    
    if [[ $time_options -eq 0 ]]; then
        print_error "Time specification required: --date, --start-date/--end-date, or --year/--month"
        ((errors++))
    elif [[ $time_options -gt 1 ]]; then
        print_error "Only one time specification method allowed"
        ((errors++))
    fi
    
    # Validate date range
    if [[ -n "$START_DATE" && -z "$END_DATE" ]] || [[ -z "$START_DATE" && -n "$END_DATE" ]]; then
        print_error "--start-date and --end-date must be provided together"
        ((errors++))
    fi
    
    # Validate dates
    if [[ -n "$DATE" ]] && ! date -d "$DATE" >/dev/null 2>&1; then
        print_error "Invalid date format: $DATE (use YYYY-MM-DD)"
        ((errors++))
    fi
    
    if [[ -n "$START_DATE" ]] && ! date -d "$START_DATE" >/dev/null 2>&1; then
        print_error "Invalid start date format: $START_DATE (use YYYY-MM-DD)"
        ((errors++))
    fi
    
    if [[ -n "$END_DATE" ]] && ! date -d "$END_DATE" >/dev/null 2>&1; then
        print_error "Invalid end date format: $END_DATE (use YYYY-MM-DD)"
        ((errors++))
    fi
    
    # Validate year/month (only if they are provided)
    if [[ -n "$YEAR" ]]; then
        if ! [[ "$YEAR" =~ ^[0-9]{4}$ ]]; then
            print_error "Invalid year format: $YEAR (use YYYY)"
            ((errors++))
        fi
    fi
    
    if [[ -n "$MONTH" ]]; then
        if ! [[ "$MONTH" =~ ^[0-9]{1,2}$ ]] || [[ "$MONTH" -lt 1 ]] || [[ "$MONTH" -gt 12 ]]; then
            print_error "Invalid month: $MONTH (use 1-12)"
            ((errors++))
        fi
    fi
    
    # Check config file
    if [[ -n "$CONFIG" ]] && [[ ! -f "$CONFIG" ]]; then
        print_error "Configuration file does not exist: $CONFIG"
        ((errors++))
    fi
    
    return $errors
}

# Function to show processing summary
show_processing_summary() {
    print_header "Processing Summary"
    print_header "=================="
    print_info "Variables: $VARIABLE"
    print_info "Input directory: $INPUT_DIR"
    print_info "Output directory: $OUTPUT_DIR"
    
    if [[ -n "$DATE" ]]; then
        print_info "Date: $DATE"
    elif [[ -n "$START_DATE" ]]; then
        print_info "Date range: $START_DATE to $END_DATE"
    else
        print_info "Time period: $YEAR-$(printf '%02d' $MONTH)"
    fi
    
    [[ -n "$PRODUCT" ]] && print_info "Product filter: $PRODUCT"
    [[ "$NO_QUALITY_MASK" -eq 1 ]] && print_warning "Quality masking: DISABLED"
    [[ -n "$CONFIG" ]] && print_info "Configuration: $CONFIG"
    
    echo
}

# Function to process a single variable
process_variable() {
    var="$1"
    date_arg="$2"
    
    print_header "Processing $var"
    
    # Create variable-specific output directory
    var_output_dir="$OUTPUT_DIR"
    if [[ $(echo "$VARIABLE" | tr ',' '\n' | wc -l) -gt 1 ]]; then
        var_output_dir="$OUTPUT_DIR/$var"
        mkdir -p "$var_output_dir"
    fi
    
    # Build command
    cmd=(python3 "$PYTHON_SCRIPT")
    cmd+=(--variable "$var" --input-dir "$INPUT_DIR" --output-dir "$var_output_dir")
    cmd+=($date_arg)
    
    [[ -n "$PRODUCT" ]] && cmd+=(--product "$PRODUCT")
    [[ -n "$CONFIG" ]] && cmd+=(--config "$CONFIG")
    [[ "$NO_QUALITY_MASK" -eq 1 ]] && cmd+=(--no-quality-mask)
    
    if [[ "$VERBOSE" -eq 1 ]]; then
        print_info "Command: ${cmd[*]}"
    fi
    
    if [[ "$DRY_RUN" -eq 1 ]]; then
        print_info "DRY RUN: Would execute: ${cmd[*]}"
        return 0
    fi
    
    # Execute command
    if "${cmd[@]}"; then
        print_success "$var processing completed!"
        return 0
    else
        print_error "$var processing failed!"
        return 1
    fi
}

# Function to process date range
process_date_range() {
    start_date="$1"
    end_date="$2"
    
    print_info "Processing date range: $start_date to $end_date"
    
    current_date="$start_date"
    success_count=0
    total_count=0
    
    while [[ "$current_date" != $(date -I -d "$end_date + 1 day") ]]; do
        ((total_count++))
        print_header "Processing date: $current_date"
        
        IFS=',' read -ra VAR_LIST <<< "$VARIABLE"
        date_success=true
        
        for var in "${VAR_LIST[@]}"; do
            var=$(echo "$var" | xargs)
            if ! process_variable "$var" "--date $current_date"; then
                date_success=false
            fi
        done
        
        if [[ "$date_success" == true ]]; then
            ((success_count++))
            print_success "Date $current_date completed successfully"
        else
            print_error "Date $current_date had failures"
        fi
        
        current_date=$(date -I -d "$current_date + 1 day")
        echo
    done
    
    print_info "Date range summary: $success_count/$total_count dates processed successfully"
}

# --- Default values ---
VARIABLE=""
INPUT_DIR=""
OUTPUT_DIR=""
START_DATE=""
END_DATE=""
DATE=""
YEAR=""
MONTH=""
PRODUCT=""
CONFIG=""
NO_QUALITY_MASK=0
CREATE_TEMPLATE=""
TEST_VCF=0
VERBOSE=0
DRY_RUN=0
PARALLEL=0

# --- Argument parsing ---
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --variable)
            VARIABLE="$2"
            shift 2
            ;;
        --input-dir)
            INPUT_DIR="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --start-date)
            START_DATE="$2"
            shift 2
            ;;
        --end-date)
            END_DATE="$2"
            shift 2
            ;;
        --date)
            DATE="$2"
            shift 2
            ;;
        --year)
            YEAR="$2"
            shift 2
            ;;
        --month)
            MONTH="$2"
            shift 2
            ;;
        --product)
            PRODUCT="$2"
            shift 2
            ;;
        --config)
            CONFIG="$2"
            shift 2
            ;;
        --no-quality-mask)
            NO_QUALITY_MASK=1
            shift
            ;;
        --verbose)
            VERBOSE=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --parallel)
            PARALLEL=1
            shift
            ;;
        --create-config-template)
            CREATE_TEMPLATE="$2"
            shift 2
            ;;
        --test-vcf)
            TEST_VCF=1
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# --- Handle special modes ---
if [[ -n "$CREATE_TEMPLATE" ]]; then
    print_info "Creating configuration template: $CREATE_TEMPLATE"
    python3 "$PYTHON_SCRIPT" --create-config-template "$CREATE_TEMPLATE"
    exit 0
fi

if [[ "$TEST_VCF" -eq 1 ]]; then
    print_info "Running VCF configuration test"
    python3 "$PYTHON_SCRIPT" --test-vcf
    exit $?
fi

# --- Validate inputs ---
if ! validate_inputs; then
    print_error "Validation failed. Use -h for help."
    exit 1
fi

# --- Expand variable groups ---
VARIABLE=$(expand_variables "$VARIABLE")

# --- Show processing summary ---
show_processing_summary

if [[ "$DRY_RUN" -eq 1 ]]; then
    print_info "Dry run completed. Variables that would be processed: $VARIABLE"
    exit 0
fi

# --- Main processing logic ---
if [[ -n "$START_DATE" && -n "$END_DATE" ]]; then
    # Date range processing
    process_date_range "$START_DATE" "$END_DATE"
else
    # Single date or month processing
    date_arg=""
    if [[ -n "$DATE" ]]; then
        date_arg="--date $DATE"
    else
        date_arg="--year-month $YEAR $MONTH"
    fi
    
    # Process variables
    IFS=',' read -ra VAR_LIST <<< "$VARIABLE"
    success_count=0
    total_count=${#VAR_LIST[@]}
    
    for var in "${VAR_LIST[@]}"; do
        var=$(echo "$var" | xargs)
        if process_variable "$var" "$date_arg"; then
            ((success_count++))
        fi
        echo
    done
    
    # Final summary
    print_header "Final Summary"
    print_header "============="
    print_info "Variables processed: $success_count/$total_count"
    
    if [[ $success_count -eq $total_count ]]; then
        print_success "All processing completed successfully!"
        
        # Show output files if they exist
        output_files=()
        while IFS= read -r -d '' file; do
            output_files+=("$file")
        done < <(find "$OUTPUT_DIR" -name "*.tif" -type f -print0 2>/dev/null || true)
        
        if [[ ${#output_files[@]} -gt 0 ]]; then
            print_info "Generated ${#output_files[@]} output files in: $OUTPUT_DIR"
        fi
        
        exit 0
    else
        print_error "Some processing failed. Check error messages above."
        exit 1
    fi
fi