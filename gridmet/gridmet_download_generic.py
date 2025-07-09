#!/usr/bin/env python3
"""
Generic GridMET Variable Download Script
=======================================

This script downloads GridMET variables from the University of Idaho's
Northwest Knowledge Network THREDDS server for specified time periods and
geographic regions (CONUS).

GridMET provides daily high-resolution (~4km) surface meteorological data
covering the contiguous US from 1979-present, updated daily.

Requirements:
- xarray, requests, pandas, netCDF4, numpy

Author: GEOSPACE Project
Date: July 2025
License: Public Domain

Usage:
    python gridmet_download_generic.py --variables pr --year 2020 --month 1
    python gridmet_download_generic.py --variables tmmx,pr --year 2020 --month 1

Output:
    - gridmet_<variable>_YYYYMM.nc (NetCDF file with daily data)
"""

# Version information
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_module_version

__version__ = get_module_version("gridmet")
__module__ = "GridMET Download"

from datetime import datetime, timedelta
import calendar
import argparse
import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
import requests
from urllib.parse import urljoin
import time
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# GridMET Variable Configuration
GRIDMET_VARIABLES = {
    # Primary Climate Variables
    'pr': {
        'name': 'precipitation_amount',
        'long_name': 'daily precipitation amount',
        'units': 'mm',
        'thredds_id': 'agg_met_pr_1979_CurrentYear_CONUS',
        'description': 'Daily total precipitation',
        'valid_range': (0, 1000),
        'aliases': ['precipitation', 'precip', 'rain']
    },
    'tmmx': {
        'name': 'air_temperature',
        'long_name': 'daily maximum temperature',
        'units': 'K',
        'thredds_id': 'agg_met_tmmx_1979_CurrentYear_CONUS',
        'description': 'Daily maximum air temperature',
        'valid_range': (200, 350),
        'aliases': ['tmax', 'maximum_temperature', 'temp_max']
    },
    'tmmn': {
        'name': 'air_temperature',
        'long_name': 'daily minimum temperature',
        'units': 'K',
        'thredds_id': 'agg_met_tmmn_1979_CurrentYear_CONUS',
        'description': 'Daily minimum air temperature',
        'valid_range': (200, 350),
        'aliases': ['tmin', 'minimum_temperature', 'temp_min']
    },
    'rmax': {
        'name': 'relative_humidity',
        'long_name': 'daily maximum relative humidity',
        'units': '%',
        'thredds_id': 'agg_met_rmax_1979_CurrentYear_CONUS',
        'description': 'Daily maximum relative humidity',
        'valid_range': (0, 100),
        'aliases': ['rh_max', 'humidity_max']
    },
    'rmin': {
        'name': 'relative_humidity',
        'long_name': 'daily minimum relative humidity',
        'units': '%',
        'thredds_id': 'agg_met_rmin_1979_CurrentYear_CONUS',
        'description': 'Daily minimum relative humidity',
        'valid_range': (0, 100),
        'aliases': ['rh_min', 'humidity_min']
    },
    'sph': {
        'name': 'specific_humidity',
        'long_name': 'daily mean specific humidity',
        'units': 'kg/kg',
        'thredds_id': 'agg_met_sph_1979_CurrentYear_CONUS',
        'description': 'Daily mean specific humidity',
        'valid_range': (0, 0.03),
        'aliases': ['specific_humidity', 'humidity_specific']
    },
    'srad': {
        'name': 'surface_downwelling_shortwave_flux_in_air',
        'long_name': 'daily mean downward shortwave radiation',
        'units': 'W/m2',
        'thredds_id': 'agg_met_srad_1979_CurrentYear_CONUS',
        'description': 'Daily mean surface downward shortwave radiation',
        'valid_range': (0, 500),
        'aliases': ['solar_radiation', 'shortwave_radiation', 'radiation']
    },
    'vs': {
        'name': 'wind_speed',
        'long_name': 'daily mean wind speed',
        'units': 'm/s',
        'thredds_id': 'agg_met_vs_1979_CurrentYear_CONUS',
        'description': 'Daily mean wind speed at 10m height',
        'valid_range': (0, 50),
        'aliases': ['wind_speed', 'wind_velocity', 'wind']
    },
    'th': {
        'name': 'wind_from_direction',
        'long_name': 'daily mean wind direction',
        'units': 'degrees',
        'thredds_id': 'agg_met_th_1979_CurrentYear_CONUS',
        'description': 'Daily mean wind direction',
        'valid_range': (0, 360),
        'aliases': ['wind_direction', 'wind_dir']
    },

    # Derived Fire Weather Variables
    'bi': {
        'name': 'burning_index',
        'long_name': 'daily burning index',
        'units': 'dimensionless',
        'thredds_id': 'agg_met_bi_1979_CurrentYear_CONUS',
        'description': 'Daily burning index (fire weather)',
        'valid_range': (0, 200),
        'aliases': ['burning_index', 'fire_index']
    },
    'fm100': {
        'name': 'dead_fuel_moisture_100hr',
        'long_name': '100-hour dead fuel moisture',
        'units': '%',
        'thredds_id': 'agg_met_fm100_1979_CurrentYear_CONUS',
        'description': '100-hour dead fuel moisture content',
        'valid_range': (0, 50),
        'aliases': ['fuel_moisture_100', 'fm_100hr']
    },
    'fm1000': {
        'name': 'dead_fuel_moisture_1000hr',
        'long_name': '1000-hour dead fuel moisture',
        'units': '%',
        'thredds_id': 'agg_met_fm1000_1979_CurrentYear_CONUS',
        'description': '1000-hour dead fuel moisture content',
        'valid_range': (0, 50),
        'aliases': ['fuel_moisture_1000', 'fm_1000hr']
    },
    'erc': {
        'name': 'energy_release_component',
        'long_name': 'daily energy release component',
        'units': 'dimensionless',
        'thredds_id': 'agg_met_erc_1979_CurrentYear_CONUS',
        'description': 'Daily energy release component (fire weather)',
        'valid_range': (0, 200),
        'aliases': ['energy_release', 'erc_index']
    },

    # Evapotranspiration Variables
    'etr': {
        'name': 'potential_evapotranspiration',
        'long_name': 'daily reference evapotranspiration (alfalfa)',
        'units': 'mm',
        'thredds_id': 'agg_met_etr_1979_CurrentYear_CONUS',
        'description': 'Daily reference evapotranspiration (alfalfa reference)',
        'valid_range': (0, 20),
        'aliases': ['evapotranspiration_alfalfa', 'et_alfalfa', 'pet_alfalfa']
    },
    'eto': {
        'name': 'potential_evapotranspiration',
        'long_name': 'daily reference evapotranspiration (grass)',
        'units': 'mm',
        'thredds_id': 'agg_met_eto_1979_CurrentYear_CONUS',
        'description': 'Daily reference evapotranspiration (grass reference)',
        'valid_range': (0, 15),
        'aliases': ['evapotranspiration_grass', 'et_grass', 'pet_grass']
    },
    'vpd': {
        'name': 'vapor_pressure_deficit',
        'long_name': 'daily mean vapor pressure deficit',
        'units': 'kPa',
        'thredds_id': 'agg_met_vpd_1979_CurrentYear_CONUS',
        'description': 'Daily mean vapor pressure deficit',
        'valid_range': (0, 8),
        'aliases': ['vapor_pressure_deficit', 'vpd_mean']
    },

    # Drought Indices (Pentad frequency)
    'pdsi': {
        'name': 'palmer_drought_severity_index',
        'long_name': 'Palmer Drought Severity Index',
        'units': 'dimensionless',
        'thredds_id': 'agg_met_pdsi_1979_CurrentYear_CONUS',
        'description': 'Palmer Drought Severity Index (5-day average)',
        'valid_range': (-10, 10),
        'aliases': ['palmer_drought', 'drought_index'],
        'frequency': 'pentad'
    }
}

# Predefined variable packages
VARIABLE_PACKAGES = {
    'weather': ['pr', 'tmmx', 'tmmn'],
    'temperature': ['tmmx', 'tmmn'],
    'humidity': ['rmax', 'rmin', 'sph', 'vpd'],
    'fire': ['bi', 'fm100', 'fm1000', 'erc'],
    'evapotranspiration': ['etr', 'eto', 'vpd'],
    'radiation': ['srad'],
    'wind': ['vs', 'th'],
    'drought': ['pdsi'],
    'basic': ['pr', 'tmmx', 'tmmn', 'vs'],
    'all': list(GRIDMET_VARIABLES.keys())
}

# THREDDS Base URL
THREDDS_BASE_URL = "http://thredds.northwestknowledge.net:8080/thredds/dodsC/"

def setup_output_directory(output_dir):
    """Create output directory if it doesn't exist"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return output_dir

def normalize_variables(variables):
    """
    Normalize variable names using aliases and packages.

    Parameters:
    -----------
    variables : list
        List of variable names (user input)

    Returns:
    --------
    list
        List of normalized GridMET variable names
    """
    normalized = []
    unknown_vars = []

    for var in variables:
        var_clean = var.strip().lower()

        # Check if it's a package
        if var_clean in VARIABLE_PACKAGES:
            package_vars = VARIABLE_PACKAGES[var_clean]
            for pvar in package_vars:
                if pvar not in normalized:
                    normalized.append(pvar)
            continue

        # Check if it's a direct variable name
        if var_clean in GRIDMET_VARIABLES:
            if var_clean not in normalized:
                normalized.append(var_clean)
            continue

        # Check aliases
        found = False
        for gridmet_var, config in GRIDMET_VARIABLES.items():
            if var_clean in config.get('aliases', []):
                if gridmet_var not in normalized:
                    normalized.append(gridmet_var)
                found = True
                break

        if not found:
            unknown_vars.append(var)

    if unknown_vars:
        print(f"Warning: Unknown variable names: {unknown_vars}")
        print("Use --list-variables to see available options")

    return normalized

def list_available_variables():
    """List all available variables, aliases, and packages"""
    print("Available GridMET Variables:")
    print("=" * 60)

    # Group by category
    categories = {
        'Primary Climate': ['pr', 'tmmx', 'tmmn', 'rmax', 'rmin', 'sph', 'srad', 'vs', 'th'],
        'Fire Weather': ['bi', 'fm100', 'fm1000', 'erc'],
        'Evapotranspiration': ['etr', 'eto', 'vpd'],
        'Drought Indices': ['pdsi']
    }

    for category, vars_list in categories.items():
        print(f"\n{category}:")
        print("-" * 40)
        for var in vars_list:
            if var in GRIDMET_VARIABLES:
                config = GRIDMET_VARIABLES[var]
                print(f"  {var}: {config['description']}")
                if config.get('aliases'):
                    aliases_str = ', '.join(config['aliases'])
                    print(f"    Aliases: {aliases_str}")
                print(f"    Units: {config['units']}")
                print(f"    Range: {config['valid_range']}")
                if config.get('frequency', 'daily') != 'daily':
                    print(f"    Frequency: {config['frequency']}")
                print()

    print("Variable Packages:")
    print("-" * 40)
    for package, vars_list in VARIABLE_PACKAGES.items():
        vars_str = ', '.join(vars_list)
        print(f"  {package}: {vars_str}")
    print()

def build_opendap_url(variable, year, month):
    """
    Build OPeNDAP URL for downloading GridMET data.

    Parameters:
    -----------
    variable : str
        GridMET variable name
    year : int
        Year to download
    month : int
        Month to download

    Returns:
    --------
    str
        OPeNDAP URL for the variable and time period
    """
    if variable not in GRIDMET_VARIABLES:
        raise ValueError(f"Unknown variable: {variable}")

    config = GRIDMET_VARIABLES[variable]
    thredds_id = config['thredds_id']

    # Build the URL
    url = urljoin(THREDDS_BASE_URL, f"{thredds_id}.nc")

    return url

def get_conus_bbox():
    """Get CONUS bounding box coordinates"""
    # CONUS bounding box: [lon_min, lat_min, lon_max, lat_max]
    return {
        'lon_min': -125.0,
        'lat_min': 25.0,
        'lon_max': -66.0,
        'lat_max': 50.0
    }

def download_gridmet_variable(variable, year, month, output_dir):
    """
    Download a single GridMET variable for specified year and month.

    Parameters:
    -----------
    variable : str
        GridMET variable name
    year : int
        Year to download
    month : int
        Month to download
    output_dir : str
        Output directory path

    Returns:
    --------
    str or None
        Path to downloaded file if successful, None if failed
    """
    print(f"  Downloading {variable} for {calendar.month_name[month]} {year}")

    try:
        # Build OPeNDAP URL
        url = build_opendap_url(variable, year, month)
        print(f"    URL: {url}")

        # Generate date range for the month
        start_date = datetime(year, month, 1)
        days_in_month = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, days_in_month)

        # Get CONUS bounding box
        bbox = get_conus_bbox()

        # Open dataset via OPeNDAP
        print(f"    Opening dataset via OPeNDAP...")
        ds = xr.open_dataset(url, chunks={'day': 30})

        # Check if variable exists in dataset
        var_name = None
        for possible_name in [variable, GRIDMET_VARIABLES[variable]['name']]:
            if possible_name in ds.data_vars:
                var_name = possible_name
                break

        if var_name is None:
            # Try to find any variable that matches
            available_vars = list(ds.data_vars.keys())
            print(f"    Available variables in dataset: {available_vars}")
            if available_vars:
                var_name = available_vars[0]  # Use the first available variable
            else:
                raise ValueError(f"No data variables found in dataset")

        print(f"    Using variable name: {var_name}")

        # Select time range
        time_dim = None
        for dim in ['day', 'time']:
            if dim in ds.dims:
                time_dim = dim
                break

        if time_dim is None:
            raise ValueError("No time dimension found in dataset")

        # Convert dates to the dataset's time format
        time_coords = ds[time_dim]

        # Find the date range within the dataset
        if hasattr(time_coords, 'dt'):
            # If it's a datetime coordinate
            mask = (time_coords.dt.year == year) & (time_coords.dt.month == month)
        else:
            # If it's a different time format (e.g., days since epoch)
            start_time = pd.to_datetime(f"{year}-{month:02d}-01")
            end_time = pd.to_datetime(f"{year}-{month:02d}-{days_in_month}")

            # Convert to dataset time format
            try:
                time_vals = pd.to_datetime(time_coords.values)
                mask = (time_vals >= start_time) & (time_vals <= end_time)
            except:
                # Fallback: select by approximate indices
                print(f"    Warning: Using approximate time selection")
                total_days = (datetime.now() - datetime(1979, 1, 1)).days
                start_idx = (start_date - datetime(1979, 1, 1)).days
                end_idx = (end_date - datetime(1979, 1, 1)).days

                if start_idx >= 0 and end_idx < len(time_coords):
                    ds_subset = ds.isel({time_dim: slice(start_idx, end_idx + 1)})
                else:
                    raise ValueError(f"Time range {start_date} to {end_date} not available in dataset")

        if 'mask' in locals():
            ds_subset = ds.where(mask, drop=True)

        # Select CONUS region
        lat_dim = None
        lon_dim = None

        for dim in ['lat', 'latitude', 'y']:
            if dim in ds_subset.dims:
                lat_dim = dim
                break

        for dim in ['lon', 'longitude', 'x']:
            if dim in ds_subset.dims:
                lon_dim = dim
                break

        if lat_dim and lon_dim:
            lat_slice = slice(bbox['lat_min'], bbox['lat_max'])
            lon_slice = slice(bbox['lon_min'], bbox['lon_max'])

            # Handle different coordinate ordering
            if ds_subset[lat_dim][0] > ds_subset[lat_dim][-1]:
                lat_slice = slice(bbox['lat_max'], bbox['lat_min'])

            ds_subset = ds_subset.sel({lat_dim: lat_slice, lon_dim: lon_slice})

        # Select only the variable of interest
        if var_name in ds_subset.data_vars:
            ds_final = ds_subset[[var_name]]
        else:
            ds_final = ds_subset

        # Add metadata
        config = GRIDMET_VARIABLES[variable]
        if var_name in ds_final.data_vars:
            ds_final[var_name].attrs.update({
                'long_name': config['long_name'],
                'standard_name': config['name'],
                'units': config['units'],
                'description': config['description'],
                'valid_range': config['valid_range'],
                'source': 'GridMET - University of Idaho',
                'download_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'spatial_resolution': '~4km',
                'temporal_resolution': 'daily'
            })

        # Generate output filename
        output_file = os.path.join(output_dir, f"gridmet_{variable}_{year}{month:02d}.nc")

        # Save to NetCDF
        print(f"    Saving to: {output_file}")

        # Add global attributes
        ds_final.attrs.update({
            'title': f'GridMET {config["description"]} - {calendar.month_name[month]} {year}',
            'institution': 'University of Idaho',
            'source': 'GridMET dataset via THREDDS OPeNDAP',
            'references': 'Abatzoglou, J.T. (2013), Development of gridded surface meteorological data for ecological applications and modelling, Int. J. Climatol., 33: 121-131.',
            'download_url': url,
            'download_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'spatial_extent': 'CONUS',
            'spatial_resolution': '1/24 degree (~4km)',
            'temporal_resolution': config.get('frequency', 'daily'),
            'geospatial_lat_min': bbox['lat_min'],
            'geospatial_lat_max': bbox['lat_max'],
            'geospatial_lon_min': bbox['lon_min'],
            'geospatial_lon_max': bbox['lon_max'],
            'Conventions': 'CF-1.6'
        })

        # Compute and save
        ds_final.to_netcdf(output_file, mode='w')

        # Close datasets
        ds_final.close()
        ds_subset.close()
        ds.close()

        print(f"    ✓ Successfully downloaded {variable}")
        return output_file

    except Exception as e:
        print(f"    ✗ Failed to download {variable}: {e}")
        import traceback
        traceback.print_exc()
        return None

def verify_download(filepath, variable):
    """
    Verify the downloaded NetCDF file.
    """
    try:
        print(f"\nVerifying downloaded file: {os.path.basename(filepath)}")
        print("-" * 40)

        # Open dataset
        ds = xr.open_dataset(filepath)

        # Print basic info
        print(f"Variables: {list(ds.data_vars.keys())}")
        print(f"Dimensions: {dict(ds.dims)}")

        # Check temporal coverage
        time_coords = [coord for coord in ds.coords if 'time' in coord.lower() or 'day' in coord.lower()]
        if time_coords:
            time_coord = time_coords[0]
            time_data = ds[time_coord]
            print(f"Time range: {time_data.min().values} to {time_data.max().values}")
            print(f"Number of time steps: {len(time_data)}")

        # Check spatial coverage
        lat_coords = [coord for coord in ds.coords if 'lat' in coord.lower()]
        lon_coords = [coord for coord in ds.coords if 'lon' in coord.lower()]

        if lat_coords and lon_coords:
            lat_coord, lon_coord = lat_coords[0], lon_coords[0]
            print(f"Spatial extent:")
            print(f"  Latitude: {ds[lat_coord].min().values:.2f} to {ds[lat_coord].max().values:.2f}")
            print(f"  Longitude: {ds[lon_coord].min().values:.2f} to {ds[lon_coord].max().values:.2f}")
            print(f"  Grid size: {len(ds[lat_coord])} x {len(ds[lon_coord])}")

        # Check data quality for the variable
        var_names = list(ds.data_vars.keys())
        if var_names:
            var_name = var_names[0]
            var_data = ds[var_name]

            # Calculate statistics
            total_points = var_data.size
            valid_points = var_data.count().values
            completeness = 100 * valid_points / total_points

            if completeness > 0:
                data_min = float(var_data.min().values)
                data_max = float(var_data.max().values)
                data_mean = float(var_data.mean().values)

                print(f"Data quality:")
                print(f"  Valid points: {valid_points:,}/{total_points:,} ({completeness:.1f}%)")
                print(f"  Value range: {data_min:.3f} to {data_max:.3f}")
                print(f"  Mean value: {data_mean:.3f}")

                # Check against expected range
                if variable in GRIDMET_VARIABLES:
                    expected_range = GRIDMET_VARIABLES[variable]['valid_range']
                    if data_min >= expected_range[0] and data_max <= expected_range[1]:
                        print(f"  ✓ Values within expected range {expected_range}")
                    else:
                        print(f"  ⚠ Values outside expected range {expected_range}")
            else:
                print(f"  ✗ No valid data found")

        # Check file size
        file_size = os.path.getsize(filepath) / (1024**2)  # MB
        print(f"File size: {file_size:.1f} MB")

        ds.close()
        print("✓ File verification completed")

    except Exception as e:
        print(f"✗ File verification failed: {e}")

def download_gridmet_variables(variables, year=2020, month=1, output_dir="./data/raw/GridMET/"):
    """
    Download multiple GridMET variables for specified year and month.

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
    dict
        Dictionary mapping variable names to downloaded file paths
    """

    # Setup
    setup_output_directory(output_dir)

    # Normalize variable names
    variables = normalize_variables(variables)

    if not variables:
        print("✗ No valid variables specified")
        return {}

    print(f"Downloading GridMET variables for {calendar.month_name[month]} {year}")
    print(f"Variables: {', '.join(variables)}")
    print(f"Output directory: {output_dir}")
    print("-" * 60)

    downloaded_files = {}

    # Download each variable
    for i, variable in enumerate(variables):
        print(f"\nDownloading variable {i+1}/{len(variables)}: {variable}")

        try:
            output_file = download_gridmet_variable(variable, year, month, output_dir)

            if output_file and os.path.exists(output_file):
                downloaded_files[variable] = output_file

                # Verify the download
                verify_download(output_file, variable)

            else:
                print(f"  ✗ Download failed for {variable}")

        except Exception as e:
            print(f"  ✗ Error downloading {variable}: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"Download Summary:")
    print(f"  Requested variables: {len(variables)}")
    print(f"  Successfully downloaded: {len(downloaded_files)}")
    print(f"  Output directory: {output_dir}")

    if downloaded_files:
        print(f"  Downloaded files:")
        for var, filepath in downloaded_files.items():
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath) / (1024**2)  # MB
            print(f"    {var}: {filename} ({file_size:.1f} MB)")

    return downloaded_files

def main():
    """
    Main function to download GridMET variables.
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
    description=f'{__module__} Framework v{__version__} - Download GridMET meteorological data',
    formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Download single variable
        %(prog)s --variables pr --year 2020 --month 1

        # Download multiple variables
        %(prog)s --variables pr,tmmx --year 2020 --month 1

        # Download variable package
        %(prog)s --variables weather --year 2019 --month 12

        # Specify output directory
        %(prog)s --variables pr --year 2020 --month 1 --output-dir /data/GridMET/

        Variable examples:
        pr (precipitation), tmmx (max temp), tmmn (min temp), vs (wind speed),
        rmax (max humidity), srad (solar radiation), bi (burning index)

        Use --list-variables to see all available variables and packages.

        Requirements:
        - xarray, requests, pandas, netCDF4, numpy
        - Internet connection for THREDDS OPeNDAP access
                """
    )

    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    
    parser.add_argument(
        '--variables', '--vars', '-v',
        type=str,
        help='Comma-separated list of variables to download or variable package name',
        required=False
    )

    parser.add_argument(
        '-y', '--year',
        type=int,
        help='Year to download (1979-present)',
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

    # Handle list variables request
    if args.list_variables:
        list_available_variables()
        sys.exit(0)

    # Use command line args if provided, otherwise use defaults
    VARIABLES = args.variables.split(',') if args.variables else ['pr']
    YEAR = args.year if args.year else 2020
    MONTH = args.month if args.month else 1
    OUTPUT_DIR = args.output_dir if args.output_dir else "./data/raw/GridMET/"

    print("GridMET Generic Variable Download Script")
    print("=" * 50)

    print(f"Configuration:")
    print(f"  Variables: {', '.join(VARIABLES)}")
    print(f"  Year: {YEAR}")
    print(f"  Month: {calendar.month_name[MONTH]} ({MONTH})")
    print(f"  Output directory: {OUTPUT_DIR}")
    print()

    # Validate inputs
    current_year = datetime.now().year
    if YEAR < 1979 or YEAR > current_year:
        print(f"✗ Error: Year must be between 1979 and {current_year}")
        sys.exit(1)

    if not VARIABLES or (len(VARIABLES) == 1 and not VARIABLES[0].strip()):
        print("✗ Error: At least one variable must be specified")
        print("Use --list-variables to see available options")
        sys.exit(1)

    # Check required libraries
    required_packages = ['xarray', 'requests', 'pandas', 'numpy']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"✗ Missing required packages: {', '.join(missing_packages)}")
        print(f"Install with: pip install {' '.join(missing_packages)}")
        sys.exit(1)

    # Download data
    downloaded_files = download_gridmet_variables(
        variables=VARIABLES,
        year=YEAR,
        month=MONTH,
        output_dir=OUTPUT_DIR
    )

    # Final summary
    if downloaded_files:
        print(f"\n✓ Process completed successfully!")
        print(f"✓ Downloaded variables: {', '.join(downloaded_files.keys())}")
        print(f"✓ Output directory: {OUTPUT_DIR}")
        print(f"✓ Ready for processing with gridmet_process_generic.sh")
    else:
        print(f"\n✗ Download failed. Please check error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
