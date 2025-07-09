#!/usr/bin/env python3
"""
Generic ERA5 Single-Level Variable Download Script
=================================================

This script downloads ERA5 single-level variables from the Copernicus Climate Data Store (CDS)
for a specified time period and geographic region (CONUS).

Supports any variable from: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels

Requirements:
- cdsapi library: pip install cdsapi
- CDS API key setup: https://cds.climate.copernicus.eu/api-how-to

Author: GEOSPACE Project
Date: 2025
License: Public Domain

Usage:
    python era5_download_generic.py --variables 2m_temperature --year 2020 --month 1
    python era5_download_generic.py --variables 2m_temperature,2m_dewpoint_temperature --year 2020 --month 1

Output:
    - era5_variables_YYYYMM.nc (NetCDF file with hourly data)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_module_version

__version__ = get_module_version("ecmwf")
__module__ = "ECMWF Download"

from datetime import datetime, timedelta
import calendar
import argparse

# Variable mapping for common names to CDS API names
VARIABLE_MAPPING = {
    # Temperature variables
    '2m_temperature': '2m_temperature',
    'temp_2m': '2m_temperature',
    'temperature_2m': '2m_temperature',
    't2m': '2m_temperature',
    
    # Dewpoint temperature
    '2m_dewpoint_temperature': '2m_dewpoint_temperature',
    'dewpoint_2m': '2m_dewpoint_temperature',
    'dewpoint_temperature_2m': '2m_dewpoint_temperature',
    'd2m': '2m_dewpoint_temperature',
    
    # Surface pressure
    'surface_pressure': 'surface_pressure',
    'surface_press': 'surface_pressure',
    'sp': 'surface_pressure',
    'press_surface': 'surface_pressure',
    
    # Total precipitation
    'total_precipitation': 'total_precipitation',
    'precipitation': 'total_precipitation',
    'precip': 'total_precipitation',
    'tp': 'total_precipitation',
    
    # Boundary layer height
    'boundary_layer_height': 'boundary_layer_height',
    'blh': 'boundary_layer_height',
    'pbl_height': 'boundary_layer_height',
    
    # Wind components at 100m
    '100m_u_component_of_wind': '100m_u_component_of_wind',
    'u_wind_100m': '100m_u_component_of_wind',
    'u100': '100m_u_component_of_wind',
    'wind_u_100m': '100m_u_component_of_wind',
    
    '100m_v_component_of_wind': '100m_v_component_of_wind',
    'v_wind_100m': '100m_v_component_of_wind',
    'v100': '100m_v_component_of_wind',
    'wind_v_100m': '100m_v_component_of_wind',
    
    # Additional common variables
    'mean_sea_level_pressure': 'mean_sea_level_pressure',
    'msl': 'mean_sea_level_pressure',
    'sea_level_pressure': 'mean_sea_level_pressure',
    
    '10m_u_component_of_wind': '10m_u_component_of_wind',
    'u10': '10m_u_component_of_wind',
    'wind_u_10m': '10m_u_component_of_wind',
    
    '10m_v_component_of_wind': '10m_v_component_of_wind',
    'v10': '10m_v_component_of_wind',
    'wind_v_10m': '10m_v_component_of_wind',
    
    'skin_temperature': 'skin_temperature',
    'skt': 'skin_temperature',
    
    'total_cloud_cover': 'total_cloud_cover',
    'tcc': 'total_cloud_cover',
    'cloud_cover': 'total_cloud_cover',
    
    'relative_humidity': 'relative_humidity',
    'rh': 'relative_humidity',
    
    'geopotential': 'geopotential',
    'z': 'geopotential',
    
    'specific_humidity': 'specific_humidity',
    'q': 'specific_humidity',
}

def setup_cds_client():
    """
    Initialize CDS API client.
    Requires .cdsapirc file in home directory with API key.
    """
    try:
        import cdsapi
        c = cdsapi.Client()
        return c
    except ImportError:
        print("Error: cdsapi library not found")
        print("Please install with: pip install cdsapi")
        sys.exit(1)
    except Exception as e:
        print(f"Error setting up CDS client: {e}")
        print("Please ensure you have:")
        print("1. Installed cdsapi: pip install cdsapi")
        print("2. Set up your CDS API key: https://cds.climate.copernicus.eu/api-how-to")
        sys.exit(1)

def normalize_variables(variables):
    """
    Normalize variable names using the mapping.
    
    Parameters:
    -----------
    variables : list
        List of variable names (user input)
        
    Returns:
    --------
    list
        List of normalized CDS API variable names
    """
    normalized = []
    unknown_vars = []
    
    for var in variables:
        var_clean = var.strip().lower()
        if var_clean in VARIABLE_MAPPING:
            cds_name = VARIABLE_MAPPING[var_clean]
            if cds_name not in normalized:  # Avoid duplicates
                normalized.append(cds_name)
        else:
            # Try the variable name as-is (in case it's already a valid CDS name)
            normalized.append(var.strip())
            unknown_vars.append(var)
    
    if unknown_vars:
        print(f"Warning: Unknown variable names: {unknown_vars}")
        print("These will be passed to CDS as-is. Check CDS documentation if download fails.")
    
    return normalized

def list_available_variables():
    """List all available variables in the mapping."""
    print("Available Variables (aliases -> CDS API name):")
    print("=" * 60)
    
    # Group by CDS API name
    cds_vars = {}
    for alias, cds_name in VARIABLE_MAPPING.items():
        if cds_name not in cds_vars:
            cds_vars[cds_name] = []
        cds_vars[cds_name].append(alias)
    
    for cds_name, aliases in sorted(cds_vars.items()):
        print(f"{cds_name}:")
        for alias in sorted(aliases):
            if alias == cds_name:
                print(f"  - {alias} (canonical)")
            else:
                print(f"  - {alias}")
        print()

def download_era5_variables(variables, year=2020, month=1, output_dir="./data/raw/ERA5/"):
    """
    Download ERA5 single-level variables for specified year and month.
    
    Parameters:
    -----------
    variables : list
        List of variable names to download
    year : int
        Year to download (default: 2020)
    month : int  
        Month to download (default: 1 for January)
    output_dir : str
        Directory to save downloaded files
        
    Returns:
    --------
    str or None
        Path to downloaded file if successful, None if failed
    """
    
    # Setup
    c = setup_cds_client()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Normalize variable names
    variables = normalize_variables(variables)
    
    # Generate all days for the month
    days_in_month = calendar.monthrange(year, month)[1]
    days = [f"{day:02d}" for day in range(1, days_in_month + 1)]
    
    # All hours in a day (24-hour format)
    hours = [f"{hour:02d}:00" for hour in range(24)]
    
    # CONUS bounding box (approximate)
    # [North, West, South, East] = [lat_max, lon_min, lat_min, lon_max]
    area = [50, -130, 25, -65]  # Covers continental US with buffer
    
    # Generate output filename
    if len(variables) == 1:
        var_name = variables[0].replace('_', '-')
        output_file = os.path.join(output_dir, f"era5_{var_name}_{year}{month:02d}.nc")
    else:
        # Multiple variables - use generic name
        output_file = os.path.join(output_dir, f"era5_variables_{year}{month:02d}.nc")
    
    print(f"Downloading ERA5 single-level variables for {calendar.month_name[month]} {year}")
    print(f"Variables: {', '.join(variables)}")
    print(f"Geographic area: {area}")
    print(f"Output file: {output_file}")
    print(f"Days: {len(days)} days")
    print(f"Hours per day: {len(hours)} hours")
    print(f"Total data points: {len(days) * len(hours)} time steps")
    print("-" * 60)
    
    # CDS API request parameters
    request_params = {
        'product_type': 'reanalysis',
        'variable': variables,
        'year': str(year),
        'month': f"{month:02d}",
        'day': days,
        'time': hours,
        'area': area,  # North, West, South, East
        'grid': [0.25, 0.25],  # 0.25 degree resolution (~28km)
        'format': 'netcdf',
    }
    
    try:
        # Submit download request
        print("Submitting download request to CDS...")
        print(f"Request parameters: {len(variables)} variables, {len(days)} days, {len(hours)} hours/day")
        
        c.retrieve('reanalysis-era5-single-levels', request_params, output_file)
        
        print(f"✓ Download completed successfully!")
        print(f"✓ File saved: {output_file}")
        
        # Check file size
        file_size = os.path.getsize(output_file) / (1024**2)  # MB
        print(f"✓ File size: {file_size:.1f} MB")
        
        return output_file
        
    except Exception as e:
        print(f"✗ Download failed: {e}")
        return None

def verify_download(filepath, variables):
    """
    Verify the downloaded NetCDF file.
    """
    try:
        import xarray as xr
        
        print(f"\nVerifying downloaded file: {filepath}")
        print("-" * 40)
        
        # Open dataset
        ds = xr.open_dataset(filepath)
        
        # Print basic info
        print(f"Variables: {list(ds.data_vars.keys())}")
        print(f"Dimensions: {dict(ds.dims)}")
        
        # Check if expected variables are present
        missing_vars = []
        for var in variables:
            # Check common variable name variations
            var_found = False
            for ds_var in ds.data_vars.keys():
                if var.lower() in ds_var.lower() or ds_var.lower() in var.lower():
                    var_found = True
                    break
            if not var_found:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Warning: Expected variables not found: {missing_vars}")
        else:
            print(f"✓ All expected variables found")
        
        # Time and spatial info
        time_coords = [coord for coord in ds.coords if 'time' in coord.lower()]
        if time_coords:
            time_coord = time_coords[0]
            print(f"Time range: {ds[time_coord].min().values} to {ds[time_coord].max().values}")
        
        lat_coords = [coord for coord in ds.coords if 'lat' in coord.lower()]
        lon_coords = [coord for coord in ds.coords if 'lon' in coord.lower()]
        
        if lat_coords and lon_coords:
            lat_coord, lon_coord = lat_coords[0], lon_coords[0]
            print(f"Spatial extent:")
            print(f"  Latitude: {ds[lat_coord].min().values:.2f} to {ds[lat_coord].max().values:.2f}")
            print(f"  Longitude: {ds[lon_coord].min().values:.2f} to {ds[lon_coord].max().values:.2f}")
        
        # Check data completeness for each variable
        for var_name in ds.data_vars:
            var_data = ds[var_name]
            total_points = var_data.size
            valid_points = var_data.count().values
            completeness = 100 * valid_points / total_points
            print(f"{var_name}: {valid_points}/{total_points} ({completeness:.1f}% complete)")
        
        ds.close()
        print("✓ File verification completed successfully!")
        
    except ImportError:
        print("Warning: xarray not installed. Skipping file verification.")
        print("Install with: pip install xarray")
    except Exception as e:
        print(f"✗ File verification failed: {e}")

def main():
    """
    Main function to download ERA5 single-level variables.
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Download ERA5 single-level variables from Copernicus CDS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Download single variable
        %(prog)s --variables 2m_temperature --year 2020 --month 1
        
        # Download multiple variables
        %(prog)s --variables 2m_temperature,surface_pressure --year 2020 --month 1
        
        # Using aliases
        %(prog)s --variables temp_2m,precip,wind_u_100m --year 2019 --month 12
        
        # Specify output directory
        %(prog)s --variables 2m_temperature --year 2020 --month 1 --output-dir /data/ERA5/

        Variable examples:
        2m_temperature, 2m_dewpoint_temperature, surface_pressure, total_precipitation,
        boundary_layer_height, 100m_u_component_of_wind, 100m_v_component_of_wind

        Use --list-variables to see all available variables and aliases.

        Requirements:
        - CDS API account and key setup
        - cdsapi library: pip install cdsapi
        - xarray library: pip install xarray (for verification)
                """
    )
    # Add version argument
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    
    parser.add_argument(
        '--variables', '--vars', '-v',
        type=str,
        help='Comma-separated list of variables to download',
        required=False
    )
    
    parser.add_argument(
        '-y', '--year',
        type=int,
        help='Year to download (1940-present)',
        required=False
    )
    
    parser.add_argument(
        '-m', '--month',
        type=int,
        choices=range(1, 13),
        help='Month to download (1-12)',
        required=False
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        help='Output directory for downloaded files',
        required=False
    )
    
    parser.add_argument(
        '--list-variables',
        action='store_true',
        help='List all available variables and their aliases'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle list variables request early (doesn't need cdsapi)
    if args.list_variables:
        list_available_variables()
        sys.exit(0)
    
    # Use command line args if provided, otherwise use defaults
    VARIABLES = args.variables.split(',') if args.variables else ['2m_temperature']
    YEAR = args.year if args.year else 2020
    MONTH = args.month if args.month else 1
    OUTPUT_DIR = args.output_dir if args.output_dir else "./data/raw/ERA5/"
    
    print("ERA5 Generic Variable Download Script")
    print("=" * 50)
    
    print(f"Configuration:")
    print(f"  Variables: {', '.join(VARIABLES)}")
    print(f"  Year: {YEAR}")
    print(f"  Month: {calendar.month_name[MONTH]} ({MONTH})")
    print(f"  Output directory: {OUTPUT_DIR}")
    print()
    
    # Validate inputs
    current_year = datetime.now().year
    if YEAR < 1940 or YEAR > current_year:
        print(f"✗ Error: Year must be between 1940 and {current_year}")
        sys.exit(1)
    
    if not VARIABLES or (len(VARIABLES) == 1 and not VARIABLES[0].strip()):
        print("✗ Error: At least one variable must be specified")
        print("Use --list-variables to see available options")
        sys.exit(1)
    
    # Download data
    output_file = download_era5_variables(
        variables=VARIABLES,
        year=YEAR, 
        month=MONTH, 
        output_dir=OUTPUT_DIR
    )
    
    # Verify download if successful
    if output_file and os.path.exists(output_file):
        verify_download(output_file, VARIABLES)
        print(f"\n✓ Process completed successfully!")
        print(f"✓ Downloaded variables: {', '.join(normalize_variables(VARIABLES))}")
        print(f"✓ Output file: {output_file}")
        print(f"✓ Ready for processing with appropriate processing script")
    else:
        print(f"\n✗ Download failed. Please check your CDS API setup and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()