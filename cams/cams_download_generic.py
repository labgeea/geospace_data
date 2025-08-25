#!/usr/bin/env python3
"""
CAMS Air Pollution Download Script
==================================

Downloads CAMS air pollution variables from the Copernicus Atmosphere Data Store (ADS).

Requirements:
- cdsapi, xarray, pandas, numpy
- ADS API credentials in ~/.adsapirc (or ~/.cdsapirc pointing to ADS)

Author: GEOSPACE Project
Date: August 2025
License: Public Domain

Usage:
    python cams_download_generic.py --variables pm25 --year 2020 --month 1
    python cams_download_generic.py --variables air_quality --year 2020 --month 1
    python cams_download_generic.py --list-variables
"""

import sys
import os

# Import version from framework
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from version import get_module_version, VERSION_INFO
    __version__ = get_module_version("cams")
    __author__ = VERSION_INFO["author"]
    __license__ = VERSION_INFO["license"]
except ImportError:
    # Fallback if version module not found
    __version__ = "1.2.0"
    __author__ = "GEOSPACE Project"
    __license__ = "Public Domain"

__module__ = "CAMS Download"

import calendar
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import time
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Import CDS API
try:
    import cdsapi
except ImportError:
    print("Error: cdsapi not found. Install with: pip install cdsapi")
    sys.exit(1)
    
# CONUS bounding box [north, west, south, east] for CDS API
DEFAULT_CONUS_BBOX = [50, -125, 24, -66]    

# CAMS Variable Configuration
CAMS_VARIABLES = {
    'pm25': {
        'name': 'Particulate matter d < 2.5 µm',
        'long_name': 'PM2.5 mass concentration',
        'cds_name': 'particulate_matter_2.5um',
        'units': 'kg m**-3',
        'output_units': 'μg/m³',
        'conversion_factor': 1e9,
        'description': 'Fine particulate matter concentration',
        'aliases': ['pm25', 'pm2.5', 'fine_particles', 'fine_pm', 'pm25'],
        'temporal_resolution': 'hourly'
    },
    'pm10': {
        'name': 'Particulate matter d < 10 µm',
        'long_name': 'PM10 mass concentration', 
        'cds_name': 'particulate_matter_10um',
        'units': 'kg m**-3',
        'output_units': 'μg/m³',
        'conversion_factor': 1e9,
        'description': 'Coarse particulate matter concentration',
        'aliases': ['pm10', 'coarse_particles', 'coarse_pm'],
        'temporal_resolution': 'hourly'
    },
    'no2': {
        'name': 'Nitrogen dioxide',
        'long_name': 'NO2 mass concentration',
        'cds_name': 'nitrogen_dioxide',
        'units': 'kg m**-3',
        'output_units': 'μg/m³',
        'conversion_factor': 1e9,
        'molecular_weight': 46.0055,
        'description': 'Nitrogen dioxide concentration',
        'aliases': ['no2', 'nitrogen_dioxide'],
        'temporal_resolution': 'hourly'
    },
    'so2': {
        'name': 'Sulphur dioxide',
        'long_name': 'SO2 mass concentration',
        'cds_name': 'sulphur_dioxide',
        'units': 'kg m**-3',
        'output_units': 'μg/m³',
        'conversion_factor': 1e9,
        'molecular_weight': 64.066,
        'description': 'Sulfur dioxide concentration',
        'aliases': ['so2', 'sulfur_dioxide', 'sulphur_dioxide'],
        'temporal_resolution': 'hourly'
    },
    'co': {
        'name': 'Carbon monoxide',
        'long_name': 'CO mass concentration',
        'cds_name': 'carbon_monoxide',
        'units': 'kg m**-3',
        'output_units': 'mg/m³',
        'conversion_factor': 1e6,
        'molecular_weight': 28.01,
        'description': 'Carbon monoxide concentration',
        'aliases': ['co', 'carbon_monoxide'],
        'temporal_resolution': 'hourly'
    },
    'o3': {
        'name': 'Ozone',
        'long_name': 'Ground-level ozone concentration',
        'cds_name': 'ozone',
        'units': 'kg m**-3',
        'output_units': 'μg/m³',
        'conversion_factor': 1e9,
        'molecular_weight': 47.998,
        'description': 'Ground-level ozone concentration',
        'aliases': ['o3', 'ozone', 'ground_ozone'],
        'temporal_resolution': 'hourly'
    }
}

# Predefined variable packages
VARIABLE_PACKAGES = {
    'air_quality': ['pm25', 'pm10', 'no2', 'o3'],
    'particulates': ['pm25', 'pm10'],
    'trace_gases': ['no2', 'so2', 'co'],
    'pollution_full': list(CAMS_VARIABLES.keys()),
    'all': list(CAMS_VARIABLES.keys())
}

# CAMS Dataset Configuration - Updated for ADS
CAMS_DATASETS = {
    'reanalysis': {
        'name': 'cams-global-reanalysis-eac4',
        'description': 'CAMS global reanalysis (EAC4)',
        'temporal_coverage': '2003-present',
        'delay': '2-3 months',
        'api_url': 'https://ads.atmosphere.copernicus.eu/api'
    },
    'forecast': {
        'name': 'cams-global-atmospheric-composition-forecasts', 
        'description': 'CAMS global atmospheric composition forecasts',
        'temporal_coverage': '2016-present',
        'delay': 'Near real-time',
        'api_url': 'https://ads.atmosphere.copernicus.eu/api'
    }
}

def setup_output_directory(output_dir):
    """Create output directory if it doesn't exist"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return output_dir

def get_cds_client():
    """Set up CDS API client for ADS"""
    try:
        # Check if we have ADS credentials
        import os
        ads_rc_path = os.path.expanduser('~/.adsapirc')
        cds_rc_path = os.path.expanduser('~/.cdsapirc')
        
        if os.path.exists(ads_rc_path):
            # Use ADS credentials
            os.environ['CDSAPI_RC'] = ads_rc_path
            print("Using ADS credentials from ~/.adsapirc")
        elif os.path.exists(cds_rc_path):
            # Check if CDS credentials point to ADS
            with open(cds_rc_path, 'r') as f:
                content = f.read()
            if 'ads.atmosphere.copernicus.eu' in content:
                # CDS file has ADS URL, use it
                print("Using ADS credentials from ~/.cdsapirc")
                pass
            else:
                # Need to create ADS config
                print("Warning: CAMS data requires ADS access. Creating ADS configuration...")
                with open(cds_rc_path, 'r') as f:
                    lines = f.readlines()
                
                # Create ADS config from CDS config
                ads_content = []
                for line in lines:
                    if line.startswith('url:'):
                        ads_content.append('url: https://ads.atmosphere.copernicus.eu/api\n')
                    else:
                        ads_content.append(line)
                
                with open(ads_rc_path, 'w') as f:
                    f.writelines(ads_content)
                
                os.environ['CDSAPI_RC'] = ads_rc_path
                print(f"Created ADS configuration: {ads_rc_path}")
        else:
            raise FileNotFoundError("No CDS/ADS credentials found")
        
        client = cdsapi.Client()
        return client
    except Exception as e:
        print(f"Error: Failed to initialize ADS API client: {e}")
        print("Please set up your ~/.adsapirc file with ADS credentials")
        print("Visit: https://ads.atmosphere.copernicus.eu/ to get your credentials")
        sys.exit(1)

def normalize_variables(variables):
    """Normalize variable names using aliases and packages"""
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
        if var_clean in CAMS_VARIABLES:
            if var_clean not in normalized:
                normalized.append(var_clean)
            continue

        # Check aliases
        found = False
        for cams_var, config in CAMS_VARIABLES.items():
            if var_clean in [alias.lower() for alias in config.get('aliases', [])]:
                if cams_var not in normalized:
                    normalized.append(cams_var)
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
    print("Available CAMS Air Pollution Variables:")
    print("=" * 70)

    for var_name, config in CAMS_VARIABLES.items():
        print(f"\n{var_name}: {config['description']}")
        print(f"  Output units: {config['output_units']}")
        print(f"  Temporal resolution: {config['temporal_resolution']}")
        
        if config.get('aliases'):
            aliases_str = ', '.join(config['aliases'])
            print(f"  Aliases: {aliases_str}")

    print("\nVariable Packages:")
    print("-" * 40)
    for package, vars_list in VARIABLE_PACKAGES.items():
        vars_str = ', '.join(vars_list)
        print(f"  {package}: {vars_str}")

    print("\nDataset Types:")
    print("-" * 40)
    for dataset_type, config in CAMS_DATASETS.items():
        print(f"  {dataset_type}: {config['description']}")
        print(f"    Coverage: {config['temporal_coverage']}")
        print(f"    Delay: {config['delay']}")
        print(f"    API: {config['api_url']}")
        

def download_cams_variables(variables, year, month, data_type='reanalysis',
                           bbox=None, output_dir="./data/raw/CAMS/"):
    """
    Download CAMS air pollution variables from ADS
    
    Parameters:
    -----------
    variables : list
        List of variable names to download
    year : int
        Year to download
    month : int
        Month to download
    data_type : str
        Dataset type ('reanalysis' or 'forecast')
    output_dir : str
        Directory to save downloaded files
    
    Returns:
    --------
    dict
        Dictionary with download results
    """
    
    # Setup
    setup_output_directory(output_dir)
    client = get_cds_client()
    
    # Handle bbox - default to CONUS
    if bbox is None:
        bbox = DEFAULT_CONUS_BBOX
        bbox_name = "CONUS"
    else:
        bbox_name = "custom"
    
    print(f"Spatial subset: {bbox_name} [{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}]")
    
    # Normalize variable names
    variables = normalize_variables(variables)
    
    if not variables:
        print("✗ No valid variables specified")
        return {}
    
    # Get dataset configuration
    if data_type not in CAMS_DATASETS:
        print(f"✗ Invalid data type: {data_type}")
        print(f"Available types: {', '.join(CAMS_DATASETS.keys())}")
        return {}
    
    dataset_config = CAMS_DATASETS[data_type]
    dataset_name = dataset_config['name']
    
    print(f"Downloading CAMS air pollution variables for {calendar.month_name[month]} {year}")
    print(f"Dataset: {dataset_config['description']}")
    print(f"API: {dataset_config['api_url']}")
    print(f"Variables: {', '.join(variables)}")
    print(f"Output directory: {output_dir}")
    print("-" * 60)
    
    results = {}
    total_downloaded = 0
    total_failed = 0
    
    # Generate time range for the month
    days_in_month = calendar.monthrange(year, month)[1]
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{days_in_month:02d}"
    
    # Generate day list
    day_list = [f"{day:02d}" for day in range(1, days_in_month + 1)]
    
    # Download variables (can be done together or separately)
    try:
        # Get CDS variable names
        cds_variables = []
        for var in variables:
            if var in CAMS_VARIABLES:
                cds_name = CAMS_VARIABLES[var]['cds_name']
                cds_variables.append(cds_name)
        
        # Determine output filename
        if len(variables) == 1:
            output_filename = f"cams_{variables[0].replace('_', '-')}_{year}{month:02d}.nc"
        else:
            output_filename = f"cams_{'_'.join(variables)}_{year}{month:02d}.nc"
        
        output_path = os.path.join(output_dir, output_filename)
        
        # Check if file already exists
        if os.path.exists(output_path):
            print(f"✓ File already exists: {output_filename}")
            return {
                'variables': {var: {'downloaded': 1, 'failed': 0, 'files': [output_path]} for var in variables},
                'summary': {'total_downloaded': len(variables), 'total_failed': 0}
            }
        
        print(f"Downloading: {output_filename}")
        print(f"ADS variables: {', '.join(cds_variables)}")
        
        # Build request parameters based on dataset type
        if data_type == 'reanalysis':
            request_params = {
                'variable': cds_variables,
                'model_level': ['60'],
                'date': f"{year}-{month:02d}-01/{year}-{month:02d}-{days_in_month:02d}",
                'time': [f"{hour:02d}:00" for hour in range(0, 24, 3)],
                'area': bbox,
                'format': 'netcdf'
            }
        if data_type == 'forecast':
            request_params = {
                'variable': cds_variables,
                'model_level': ['60'],
                'date': f"{year}-{month:02d}-01/{year}-{month:02d}-{days_in_month:02d}",
                'time': [f"{hour:02d}:00" for hour in range(0, 24, 3)],
                'leadtime_hour': ['0', '3', '6', '9', '12'],
                'area': bbox,
                'format': 'netcdf'
            }
        
        # Submit download request
        print(f"Submitting request to ADS...")
        print(f"Request may be queued - this is normal for CAMS data")
        
        start_time = time.time()
        client.retrieve(dataset_name, request_params, output_path)
        download_time = time.time() - start_time
        
        # Verify download
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024**2)  # MB
            print(f"✓ Download completed: {output_filename}")
            print(f"  File size: {file_size:.1f} MB")
            print(f"  Download time: {download_time:.1f} seconds")
            
            # Update results
            for var in variables:
                results[var] = {
                    'downloaded': 1,
                    'failed': 0,
                    'files': [output_path]
                }
            total_downloaded = len(variables)
        else:
            print(f"✗ Download failed: {output_filename}")
            for var in variables:
                results[var] = {
                    'downloaded': 0,
                    'failed': 1,
                    'files': []
                }
            total_failed = len(variables)
            
    except Exception as e:
        print(f"✗ Download error: {e}")
        for var in variables:
            results[var] = {
                'downloaded': 0,
                'failed': 1,
                'files': []
            }
        total_failed = len(variables)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Download Summary:")
    print(f"  Requested variables: {len(variables)}")
    print(f"  Successfully downloaded: {total_downloaded}")
    print(f"  Failed downloads: {total_failed}")
    print(f"  Output directory: {output_dir}")
    
    if total_downloaded > 0:
        print(f"\n✓ Ready for processing with cams_process_generic.sh")
    
    return {
        'variables': results,
        'summary': {
            'total_downloaded': total_downloaded,
            'total_failed': total_failed
        }
    }

def main():
    """Main function to download CAMS air pollution variables"""
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Download CAMS air pollution variables from ADS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
# Download PM2.5 concentration
%(prog)s --variables pm25 --year 2020 --month 1

# Download air quality package
%(prog)s --variables air_quality --year 2020 --month 1

# Download multiple variables
%(prog)s --variables pm25,no2,o3 --year 2020 --month 1

# Download with forecast data
%(prog)s --variables pm25 --year 2024 --month 12 --data-type forecast

# Subset spatial extent
%(prog)s --variables pm25 --year 2020 --month 1 --bbox -180,-90,180,90

Note: This script uses the Atmosphere Data Store (ADS) API for CAMS data.
Set up your ~/.adsapirc file or ensure ~/.cdsapirc points to ADS.

Requirements:
- ADS account and API key (same as CDS credentials)
- ADS API credentials in ~/.adsapirc or ~/.cdsapirc  
- cdsapi, xarray, pandas, numpy
        """
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--variables', '--vars', '-v', type=str, help='Comma-separated list of variables', required=False)
    parser.add_argument('--year', '-y', type=int, help='Year to download', required=False)
    parser.add_argument('--month', '-m', type=int, help='Month to download (1-12)', required=False)
    parser.add_argument('--data-type', '-t', type=str, choices=['reanalysis', 'forecast'], 
                        help='Dataset type (default: reanalysis)', default='reanalysis', required=False)
    parser.add_argument('--bbox', type=str, help='Bounding box as "north,west,south,east" (default: CONUS)', required=False)
    parser.add_argument('-o', '--output-dir', type=str, help='Output directory for downloaded files', required=False)
    parser.add_argument('--list-variables', action='store_true', help='List all available variables, aliases, and health guidelines')
    
    args = parser.parse_args()
    
    # Handle list variables request
    if args.list_variables:
        list_available_variables()
        sys.exit(0)
    
    # Use command line args if provided, otherwise use defaults
    VARIABLES = args.variables.split(',') if args.variables else ['pm25']
    YEAR = args.year if args.year else 2020
    MONTH = args.month if args.month else 1
    DATA_TYPE = args.data_type
    # Parse bbox
    BBOX = None
    if args.bbox:
        try:
            bbox_parts = [float(x.strip()) for x in args.bbox.split(',')]
            if len(bbox_parts) != 4:
                raise ValueError("Bbox must have exactly 4 values")
            BBOX = bbox_parts
            # Validate bbox
            if not (-90 <= bbox_parts[2] <= bbox_parts[0] <= 90):
                raise ValueError("Invalid latitude values")
            if not (-180 <= bbox_parts[1] <= bbox_parts[3] <= 180):
                raise ValueError("Invalid longitude values")
        except Exception as e:
            print(f"✗ Error: Invalid bbox format: {e}")
            print("Use format: 'north,west,south,east' (e.g., '50,-125,24,-66')")
            sys.exit(1)
    OUTPUT_DIR = args.output_dir if args.output_dir else "./data/raw/CAMS/"
    
    # Validate inputs
    if not (1 <= MONTH <= 12):
        print("✗ Error: Month must be between 1 and 12")
        sys.exit(1)
    
    if not (2003 <= YEAR <= datetime.now().year):
        print("✗ Error: Year must be between 2003 and current year")
        sys.exit(1)
    
    print("CAMS Air Pollution Download Script - Corrected Version")
    print("=" * 60)
    
    # Check ADS API setup
    try:
        import cdsapi
        client = get_cds_client()  # Handle ADS setup
    except Exception as e:
        print("✗ Error: ADS API not properly configured")
        print("Please set up your ADS credentials:")
        print("1. Visit: https://ads.atmosphere.copernicus.eu/")
        print("2. Create account and get API key (same as CDS)") 
        print("3. Create ~/.adsapirc with your credentials")
        print("4. Accept CAMS dataset license terms")
        sys.exit(1)
    
    # Download data
    results = download_cams_variables(
        variables=VARIABLES,
        year=YEAR,
        month=MONTH,
        data_type=DATA_TYPE,
        bbox=BBOX,
        output_dir=OUTPUT_DIR
    )
    
    # Final summary
    if results and results['summary']['total_downloaded'] > 0:
        print(f"\n✓ Process completed successfully!")
        successful_vars = [v for v in results['variables'].keys() 
                          if results['variables'][v]['downloaded'] > 0]
        print(f"✓ Downloaded variables: {', '.join(successful_vars)}")
        print(f"✓ Output directory: {OUTPUT_DIR}")
        print(f"✓ Ready for processing with cams_process_generic.sh")
        
    else:
        print(f"\n✗ Download failed. Please check error messages above.")
        print(f"\nRecommendations:")
        print(f"1. Check ADS service status at https://ads.atmosphere.copernicus.eu/")
        print(f"2. Verify ADS credentials and license acceptance")
        print(f"3. Try downloading a single variable first")
        print(f"4. Check if dataset is available for the requested date")
        sys.exit(1)

if __name__ == "__main__":
    main()