#!/usr/bin/env python3
"""
MODIS Variable Download Script
==================================================

This script downloads MODIS variables using NASA's Common Metadata Repository (CMR) API
and NASA Earthdata Cloud infrastructure. This approach is recommended after the
LP DAAC Data Pool retirement on June 30, 2025.

Requirements:
- requests, pyproj, pandas, numpy
- EARTHDATA_BEARER_TOKEN environment variable

Author: GEOSPACE Project
Date: July 2025
License: Public Domain

Usage:
    python modis_download_cmr_api.py --variables LST --year 2020 --month 1
    python modis_download_cmr_api.py --variables NDVI,LST --year 2020 --month 1
"""

# Version information
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_module_version
__version__ = get_module_version("modis")
__module__ = "Modis Download"

# Standard library imports
import math
from datetime import datetime, timedelta
import calendar
import argparse
import requests
import pandas as pd
import numpy as np
from pathlib import Path
import time
import warnings
from pyproj import Proj
import concurrent.futures
from typing import Dict, List, Optional, Tuple, Any
import json
import re

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# MODIS Variable Configuration
MODIS_VARIABLES = {
    'LST': {
        'name': 'Land Surface Temperature',
        'long_name': 'MODIS Land Surface Temperature',
        'products': {
            'Terra': 'MOD11A1.061',
            'Aqua': 'MYD11A1.061'
        },
        'temporal_resolution': 'daily',
        'spatial_resolution': '1km',
        'description': 'Daily land surface temperature and emissivity',
        'units': 'Kelvin',
        'valid_range': (200, 370),
        'aliases': ['land_surface_temperature', 'temperature', 'temp', 'sst'],
        'start_day': '01'
    },
    'NDVI': {
        'name': 'Normalized Difference Vegetation Index',
        'long_name': 'MODIS Vegetation Indices',
        'products': {
            'Terra': 'MOD13A2.061',
            'Aqua': 'MYD13A2.061'
        },
        'temporal_resolution': 'monthly',
        'spatial_resolution': '1km',
        'description': '16-day composite vegetation indices',
        'units': 'dimensionless',
        'valid_range': (-2000, 10000),
        'aliases': ['vegetation_index', 'ndvi', 'vi', 'vegetation'],
        'start_day': '01'
    },
    'VCF': {
        'name': 'Vegetation Continuous Fields',
        'long_name': 'MODIS Vegetation Continuous Fields',
        'products': {
            'Terra': 'MOD44B.061'
        },
        'temporal_resolution': 'yearly',
        'spatial_resolution': '250m',
        'description': 'Annual vegetation continuous fields (tree cover, non-tree vegetation)',
        'units': 'percent',
        'valid_range': (0, 100),
        'aliases': ['tree_cover', 'vegetation_cover', 'forest_cover', 'vcf'],
        'start_day': '03.06'
    },
    'EVI': {
        'name': 'Enhanced Vegetation Index',
        'long_name': 'MODIS Enhanced Vegetation Index',
        'products': {
            'Terra': 'MOD13A2.061',
            'Aqua': 'MYD13A2.061'
        },
        'temporal_resolution': 'monthly',
        'spatial_resolution': '1km',
        'description': '16-day composite enhanced vegetation index',
        'units': 'dimensionless',
        'valid_range': (-2000, 10000),
        'aliases': ['enhanced_vegetation_index', 'evi'],
        'start_day': '01'
    }
}

# Predefined variable packages
VARIABLE_PACKAGES = {
    'vegetation': ['NDVI', 'EVI', 'VCF'],
    'temperature': ['LST'],
    'land': ['LST', 'NDVI', 'VCF'],
    'all': list(MODIS_VARIABLES.keys())
}

# NASA CMR API Configuration
CMR_BASE_URL = 'https://cmr.earthdata.nasa.gov/search/granules.json'
CMR_COLLECTIONS_URL = 'https://cmr.earthdata.nasa.gov/search/collections.json'

# MODIS tiling system constants
EARTH_RADIUS = 6371007.181  # in meters
EARTH_WIDTH = 2 * math.pi * EARTH_RADIUS
VERTICAL_TILES = 18
HORIZONTAL_TILES = 36
TILE_WIDTH = EARTH_WIDTH / HORIZONTAL_TILES
TILE_HEIGHT = TILE_WIDTH
MODIS_GRID = Proj(f"+proj=sinu +R={EARTH_RADIUS} +nadgrids=@null +wktext")

def setup_output_directory(output_dir):
    """Create output directory if it doesn't exist"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return output_dir

def get_authenticated_session():
    """Set up authenticated session using Bearer token"""
    token = os.getenv("EARTHDATA_BEARER_TOKEN")
    if not token:
        raise ValueError(
            "EARTHDATA_BEARER_TOKEN environment variable is not set. "
            "Please obtain a bearer token from NASA Earthdata and set it as an environment variable."
        )

    session = requests.Session()
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "MODIS-Download-CMR/3.0.0"
    }
    session.headers.update(headers)
    return session

def lat_lon_to_modis_tile(lat, lon):
    """Convert latitude/longitude to MODIS tile coordinates"""
    x, y = MODIS_GRID(lon, lat)
    h = int((x + EARTH_WIDTH / 2) / TILE_WIDTH)
    v = int((EARTH_WIDTH / 4 - y) / TILE_HEIGHT)
    return f"h{h:02d}v{v:02d}"

def get_conus_tiles():
    """Get MODIS tiles covering CONUS"""
    bbox = {
        'lower_left_lat': 24.5285,
        'lower_left_lon': -124.7625,
        'upper_right_lat': 49.34895,
        'upper_right_lon': -66.93796
    }

    # Generate points across CONUS
    points = []
    step = 0.5
    lat = bbox['lower_left_lat']
    while lat <= bbox['upper_right_lat']:
        lon = bbox['lower_left_lon']
        while lon <= bbox['upper_right_lon']:
            points.append((lat, lon))
            lon += step
        lat += step

    # Get unique tiles
    tiles = set(lat_lon_to_modis_tile(lat, lon) for lat, lon in points)
    return sorted(list(tiles))

def search_cmr_granules(product, start_date, end_date, tiles, session):
    """
    Search for MODIS granules using NASA CMR API
    
    Parameters:
    -----------
    product : str
        MODIS product identifier (e.g., 'MOD11A1.061')
    start_date : str
        Start date in YYYY-MM-DD format
    end_date : str
        End date in YYYY-MM-DD format
    tiles : list
        List of MODIS tiles (e.g., ['h08v04', 'h09v04'])
    session : requests.Session
        Authenticated session
    
    Returns:
    --------
    list
        List of granule information dictionaries
    """
    
    # Build the search parameters
    params = {
        'short_name': product.split('.')[0],  # e.g., MOD11A1
        'version': product.split('.')[1],     # e.g., 061
        'temporal': f"{start_date}T00:00:00Z,{end_date}T23:59:59Z",
        'page_size': 2000,
        'sort_key': 'start_date',
        'scroll': 'true'
    }
    
    # Add bounding box for CONUS
    params['bounding_box'] = '-125,24,-66,50'
    
    granules = []
    
    try:
        print(f"    Searching CMR for {product} granules...")
        response = session.get(CMR_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'feed' in data and 'entry' in data['feed']:
            for entry in data['feed']['entry']:
                granule_info = {
                    'id': entry.get('id'),
                    'title': entry.get('title'),
                    'updated': entry.get('updated'),
                    'dataset_id': entry.get('dataset_id'),
                    'data_center': entry.get('data_center'),
                    'links': entry.get('links', [])
                }
                
                # Filter for relevant tiles
                title = granule_info['title']
                if any(tile in title for tile in tiles):
                    granules.append(granule_info)
        
        print(f"    Found {len(granules)} granules for {product}")
        
    except Exception as e:
        print(f"    Error searching CMR for {product}: {e}")
        return []
    
    return granules

def get_download_urls(granule_info, session):
    """
    Extract download URLs from granule information
    
    Parameters:
    -----------
    granule_info : dict
        Granule information from CMR API
    session : requests.Session
        Authenticated session
    
    Returns:
    --------
    list
        List of download URLs
    """
    download_urls = []
    
    for link in granule_info.get('links', []):
        if link.get('rel') == 'http://esipfed.org/ns/fedsearch/1.1/data#':
            href = link.get('href')
            if href and href.endswith('.hdf'):
                download_urls.append(href)
    
    return download_urls

def download_file_from_url(url, target_dir, session, max_retries=3):
    """Download a single file from URL with error handling"""
    filename = url.split("/")[-1]
    file_path = os.path.join(target_dir, filename)
    temp_file_path = file_path + ".part"

    # Check if file already exists
    if os.path.exists(file_path):
        print(f"  ✓ File already exists: {filename}")
        return file_path

    # Download with retries
    for attempt in range(max_retries):
        try:
            print(f"  → Downloading {filename} (attempt {attempt + 1}/{max_retries})")

            with session.get(url, stream=True, timeout=60) as response:
                response.raise_for_status()

                file_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0

                with open(temp_file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                # Verify download
                if file_size > 0 and downloaded != file_size:
                    raise ValueError(f"Download incomplete: {downloaded}/{file_size} bytes")

                # Move completed file
                os.rename(temp_file_path, file_path)
                print(f"  ✓ Download completed: {filename} ({downloaded / (1024**2):.1f} MB)")
                return file_path

        except Exception as e:
            print(f"  ✗ Download attempt {attempt + 1} failed for {filename}: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"  ⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

    print(f"  ✗ Failed to download {filename} after {max_retries} attempts")
    return None

def normalize_variables(variables):
    """Normalize variable names using aliases and packages"""
    normalized = []
    unknown_vars = []

    for var in variables:
        var_clean = var.strip().upper()

        # Check if it's a package
        if var_clean.lower() in VARIABLE_PACKAGES:
            package_vars = VARIABLE_PACKAGES[var_clean.lower()]
            for pvar in package_vars:
                if pvar not in normalized:
                    normalized.append(pvar)
            continue

        # Check if it's a direct variable name
        if var_clean in MODIS_VARIABLES:
            if var_clean not in normalized:
                normalized.append(var_clean)
            continue

        # Check aliases
        found = False
        for modis_var, config in MODIS_VARIABLES.items():
            if var_clean.lower() in [alias.lower() for alias in config.get('aliases', [])]:
                if modis_var not in normalized:
                    normalized.append(modis_var)
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
    print("Available MODIS Variables:")
    print("=" * 60)

    for var_name, config in MODIS_VARIABLES.items():
        print(f"\n{var_name}: {config['description']}")
        print(f"  Products: {', '.join(f'{k}({v})' for k, v in config['products'].items())}")
        print(f"  Resolution: {config['spatial_resolution']} spatial, {config['temporal_resolution']} temporal")
        print(f"  Units: {config['units']}")
        print(f"  Range: {config['valid_range']}")
        if config.get('aliases'):
            aliases_str = ', '.join(config['aliases'])
            print(f"  Aliases: {aliases_str}")

    print("\nVariable Packages:")
    print("-" * 40)
    for package, vars_list in VARIABLE_PACKAGES.items():
        vars_str = ', '.join(vars_list)
        print(f"  {package}: {vars_str}")

def download_modis_variables_cmr(variables, year=None, month=None, date=None, instrument='Both',
                                output_dir="./data/raw/MODIS/", max_workers=5):
    """
    Download multiple MODIS variables using NASA CMR API
    
    Parameters:
    -----------
    variables : list
        List of variable names to download
    year : int, optional
        Year to download
    month : int, optional
        Month to download
    date : str, optional
        Specific date to download (YYYY-MM-DD)
    instrument : str
        Satellite instrument ('Terra', 'Aqua', 'Both')
    output_dir : str
        Directory to save downloaded files
    max_workers : int
        Number of parallel downloads
    
    Returns:
    --------
    dict
        Dictionary with download results
    """
    
    # Setup
    setup_output_directory(output_dir)
    session = get_authenticated_session()
    
    # Normalize variable names
    variables = normalize_variables(variables)
    
    if not variables:
        print("✗ No valid variables specified")
        return {}
    
    # Get CONUS tiles
    tiles = get_conus_tiles()
    print(f"Using {len(tiles)} MODIS tiles for CONUS coverage")
    
    # Set up date range
    if date:
        start_date = date
        end_date = date
        print(f"Downloading MODIS variables for {date}")
    else:
        start_date = f"{year}-{month:02d}-01"
        days_in_month = calendar.monthrange(year, month)[1]
        end_date = f"{year}-{month:02d}-{days_in_month:02d}"
        print(f"Downloading MODIS variables for {calendar.month_name[month]} {year}")
    
    print(f"Variables: {', '.join(variables)}")
    print(f"Instrument: {instrument}")
    print(f"Output directory: {output_dir}")
    print(f"Max workers: {max_workers}")
    print("-" * 60)
    
    results = {}
    total_downloaded = 0
    total_failed = 0
    
    # Download each variable
    for i, variable in enumerate(variables):
        print(f"\nDownloading variable {i+1}/{len(variables)}: {variable}")
        
        config = MODIS_VARIABLES[variable]
        
        # Determine which instruments to use
        if instrument == 'Both':
            instruments = [inst for inst in ['Terra', 'Aqua'] if inst in config['products']]
        else:
            if instrument not in config['products']:
                print(f"  ✗ {variable} not available for {instrument}")
                results[variable] = {'downloaded': 0, 'failed': 0, 'files': []}
                continue
            instruments = [instrument]
        
        downloaded_files = []
        variable_downloaded = 0
        variable_failed = 0
        
        for inst in instruments:
            product = config['products'][inst]
            print(f"  Processing {inst} {variable} ({product})")
            
            # Search for granules
            granules = search_cmr_granules(product, start_date, end_date, tiles, session)
            
            if not granules:
                print(f"  ⚠ No granules found for {inst} {variable}")
                continue
            
            # Extract download URLs
            download_urls = []
            for granule in granules:
                urls = get_download_urls(granule, session)
                download_urls.extend(urls)
            
            print(f"  Found {len(download_urls)} files to download")
            
            # Download files in parallel
            if download_urls:
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_url = {
                        executor.submit(download_file_from_url, url, output_dir, session): url
                        for url in download_urls
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_url):
                        url = future_to_url[future]
                        try:
                            result = future.result()
                            if result:
                                downloaded_files.append(result)
                                variable_downloaded += 1
                                total_downloaded += 1
                            else:
                                variable_failed += 1
                                total_failed += 1
                        except Exception as e:
                            print(f"  ✗ Error downloading {url}: {e}")
                            variable_failed += 1
                            total_failed += 1
        
        results[variable] = {
            'downloaded': variable_downloaded,
            'failed': variable_failed,
            'files': downloaded_files
        }
        
        print(f"  ✓ {variable}: {variable_downloaded} files downloaded, {variable_failed} failed")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  Download Summary:")
    print(f"  Requested variables: {len(variables)}")
    print(f"  Total files downloaded: {total_downloaded}")
    print(f"  Total files failed: {total_failed}")
    print(f"  Output directory: {output_dir}")
    
    return {
        'variables': results,
        'summary': {
            'total_downloaded': total_downloaded,
            'total_failed': total_failed
        }
    }

def main():
    """Main function to download MODIS variables using CMR API"""
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Download MODIS variables using NASA CMR API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
# Download single variable
%(prog)s --variables LST --year 2020 --month 1

# Download multiple variables
%(prog)s --variables LST,NDVI --year 2020 --month 1

# Download variable package
%(prog)s --variables vegetation --year 2019 --month 12

# Download specific date
%(prog)s --variables LST --date 2020-01-15

Note: This script uses NASA's CMR API and is designed to work with the 
new NASA Earthdata Cloud infrastructure (post June 30, 2025).

Requirements:
- NASA Earthdata account and bearer token
- EARTHDATA_BEARER_TOKEN environment variable
- requests, pyproj, pandas, numpy
        """
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--variables', '--vars', '-v', type=str, help='Comma-separated list of variables', required=False)
    
    time_group = parser.add_mutually_exclusive_group(required=False)
    time_group.add_argument('-d', '--date', type=str, help='Download specific date (YYYY-MM-DD)')
    time_group.add_argument('--year-month', nargs=2, metavar=('YEAR', 'MONTH'), type=int, help='Download specific year and month')
    
    parser.add_argument('-i', '--instrument', type=str, choices=['Terra', 'Aqua', 'Both'], help='Satellite instrument (default: Both)', required=False)
    parser.add_argument('-o', '--output-dir', type=str, help='Output directory for downloaded files', required=False)
    parser.add_argument('-w', '--workers', type=int, help='Number of parallel downloads (default: 5)', required=False)
    parser.add_argument('--list-variables', action='store_true', help='List all available variables and their aliases')
    
    args = parser.parse_args()
    
    # Handle list variables request
    if args.list_variables:
        list_available_variables()
        sys.exit(0)
    
    # Use command line args if provided, otherwise use defaults
    VARIABLES = args.variables.split(',') if args.variables else ['LST']
    INSTRUMENT = args.instrument if args.instrument else 'Both'
    OUTPUT_DIR = args.output_dir if args.output_dir else "./data/raw/MODIS/"
    MAX_WORKERS = args.workers if args.workers else 5
    
    # Handle date/year/month logic
    YEAR, MONTH, DATE = None, None, None
    if args.date:
        try:
            datetime.strptime(args.date, '%Y-%m-%d')
            DATE = args.date
        except ValueError:
            print("✗ Error: Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    elif args.year_month:
        YEAR, MONTH = args.year_month
    else:
        YEAR = 2020
        MONTH = 1
    
    print("MODIS Variable Download Script - Using NASA CMR API")
    print("=" * 60)
    
    # Check bearer token
    if not os.getenv("EARTHDATA_BEARER_TOKEN"):
        print("✗ Error: EARTHDATA_BEARER_TOKEN environment variable not set")
        print("Please obtain a bearer token from NASA Earthdata:")
        print("1. Visit: https://urs.earthdata.nasa.gov/")
        print("2. Login and generate a bearer token")
        print("3. Set environment variable: export EARTHDATA_BEARER_TOKEN=your_token")
        sys.exit(1)
    
    # Download data
    results = download_modis_variables_cmr(
        variables=VARIABLES,
        year=YEAR,
        month=MONTH,
        date=DATE,
        instrument=INSTRUMENT,
        output_dir=OUTPUT_DIR,
        max_workers=MAX_WORKERS
    )
    
    # Final summary
    if results and results['summary']['total_downloaded'] > 0:
        print(f"\n✓ Process completed successfully!")
        print(f"✓ Downloaded variables: {', '.join([v for v in results['variables'].keys() if results['variables'][v]['downloaded'] > 0])}")
        print(f"✓ Output directory: {OUTPUT_DIR}")
        print(f"✓ Ready for processing with modis_process_generic.sh")
    else:
        print(f"\n✗ Download failed. Please check error messages above.")
        print(f"\nRecommendations:")
        print(f"1. Use NASA Earthdata Search: https://search.earthdata.nasa.gov/")
        print(f"2. Use AppEEARS: https://appeears.earthdatacloud.nasa.gov/")
        print(f"3. Check NASA Earthdata status at https://earthdata.nasa.gov/")
        sys.exit(1)

if __name__ == "__main__":
    main()