#!/usr/bin/env python3
"""
Generic MODIS Variable Download Script
=====================================

This script downloads MODIS variables from NASA Earthdata repository for specified
time periods and geographic regions (CONUS), supporting LST, NDVI, and VCF products.

MODIS provides high-quality satellite observations for land surface analysis
from Terra and Aqua satellites with different spatial and temporal resolutions.

Requirements:
- requests, beautifulsoup4, pyproj, pandas, numpy
- EARTHDATA_BEARER_TOKEN environment variable

Author: GEOSPACE Project
Date: July 2025
License: Public Domain

Usage:
    python modis_download_generic.py --variables LST --year 2020 --month 1
    python modis_download_generic.py --variables NDVI,LST --year 2020 --month 1

Output:
    - MODIS HDF files organized by product and date
"""

# Version information
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_module_version

__version__ = get_module_version("modis")
__module__ = "MODIS Download"

# Import modules
import math
from datetime import datetime, timedelta
import calendar
import argparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from pathlib import Path
import time
import warnings
from pyproj import Proj
import concurrent.futures
from typing import Dict, List, Optional, Tuple, Any
import json
import re # Import re for regex

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

# MODIS tiling system constants
EARTH_RADIUS = 6371007.181  # in meters
EARTH_WIDTH = 2 * math.pi * EARTH_RADIUS
VERTICAL_TILES = 18
HORIZONTAL_TILES = 36
TILE_WIDTH = EARTH_WIDTH / HORIZONTAL_TILES
TILE_HEIGHT = TILE_WIDTH
MODIS_GRID = Proj(f"+proj=sinu +R={EARTH_RADIUS} +nadgrids=@null +wktext")

# Base URLs for different satellites
BASE_URLS = {
    'Terra': 'https://e4ftl01.cr.usgs.gov/MOLT/',
    'Aqua': 'https://e4ftl01.cr.usgs.gov/MOLA/'
}

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
    # Add a common browser User-Agent
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    session.headers.update(headers)
    return session

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
        List of normalized MODIS variable names
    """
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
        print()

    print("Variable Packages:")
    print("-" * 40)
    for package, vars_list in VARIABLE_PACKAGES.items():
        vars_str = ', '.join(vars_list)
        print(f"  {package}: {vars_str}")
    print()

def lat_lon_to_modis_tile(lat, lon):
    """Convert latitude/longitude to MODIS tile coordinates"""
    x, y = MODIS_GRID(lon, lat)
    h = int((x + EARTH_WIDTH / 2) / TILE_WIDTH)
    v = int((EARTH_WIDTH / 4 - y) / TILE_HEIGHT)
    return f"h{h:02d}v{v:02d}"

def get_conus_tiles():
    """Get MODIS tiles covering CONUS"""
    # CONUS bounding box
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

def get_available_files(url, session, max_retries=3, very_long_timeout=300):
    """Get list of available HDF files from a URL using BeautifulSoup with a long timeout and retries."""
    for attempt in range(max_retries):
        try:
            print(f"    Attempt {attempt + 1}/{max_retries} to list files from {url} (timeout: {very_long_timeout}s)")
            response = session.get(url, timeout=very_long_timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            files = []
            for link in soup.find_all("a"):
                href = link.get("href", "")
                if href.endswith(".hdf") and not href.endswith(".hdf.xml"):
                    files.append(href.split('/')[-1]) # Get only the filename

            if files:
                print(f"    Found {len(files)} HDF files in {url} on attempt {attempt + 1}.")
                return files
            else:
                print(f"    No HDF files found in {url} on attempt {attempt + 1}, though page loaded.")
                # If page loaded but no files, it's unlikely retrying will help unless it was a partial load
                # but we'll let the retry loop handle it.

        except requests.exceptions.HTTPError as e:
            print(f"    HTTP error accessing {url} (attempt {attempt + 1}): {e.response.status_code} - {e.response.reason}")
            if e.response.status_code == 404: # Not found, no point retrying
                print(f"    URL {url} not found (404). No files available.")
                return []
        except requests.exceptions.RequestException as e: # Includes timeouts
            print(f"    Request error accessing {url} (attempt {attempt + 1}): {e}")
        except Exception as e:
            print(f"    Unexpected error accessing {url} (attempt {attempt + 1}): {e}")

        if attempt < max_retries - 1:
            wait_time = 5 * (2 ** attempt) # Exponential backoff, starting a bit longer
            print(f"    Waiting {wait_time}s before retry for {url}...")
            time.sleep(wait_time)
        else:
            print(f"    Failed to list files from {url} after {max_retries} attempts.")

    return [] # Return empty list if all retries fail

def is_download_complete(file_path, expected_size):
    """Check if download is complete by comparing file sizes"""
    if not os.path.exists(file_path):
        return False
    return os.path.getsize(file_path) == expected_size

def download_file(file_url, target_dir, session, max_retries=3):
    """Download a single file with error handling and resume capability"""
    filename = file_url.split("/")[-1]
    file_path = os.path.join(target_dir, filename)
    temp_file_path = file_path + ".part"

    # Check if file already exists and is complete
    if os.path.exists(file_path):
        try:
            response = session.head(file_url, allow_redirects=True, timeout=30)
            expected_size = int(response.headers.get("Content-Length", 0))
            if expected_size > 0 and is_download_complete(file_path, expected_size):
                print(f"  ✓ File already exists: {filename}")
                return file_path
            else:
                print(f"  ⚠ Incomplete download detected for {filename}. Redownloading...")
                os.remove(file_path)
        except Exception as e:
            print(f"  ⚠ Error checking existing file {filename}: {e}")

    # Download with retries
    for attempt in range(max_retries):
        try:
            print(f"  → Downloading {filename} (attempt {attempt + 1}/{max_retries})")

            with session.get(file_url, stream=True, timeout=60) as response:
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
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"  ⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

    print(f"  ✗ Failed to download {filename} after {max_retries} attempts")
    return None

def get_formatted_date(date, variable):
    """Get formatted date string for MODIS product URLs"""
    config = MODIS_VARIABLES[variable]

    if config['temporal_resolution'] == 'daily':
        return date.strftime("%Y.%m.%d")
    elif config['temporal_resolution'] == 'monthly':
        return date.strftime(f"%Y.%m.{config['start_day']}")
    elif config['temporal_resolution'] == 'yearly':
        # Handle leap years for VCF
        if date.year % 4 == 0 and (date.year % 100 != 0 or date.year % 400 == 0):
            return f"{date.year}.03.05"
        else:
            return f"{date.year}.{config['start_day']}"

def download_modis_variable(variable, year, month, date, instrument, output_dir, session, max_workers=5):
    """
    Download a single MODIS variable for specified year and month.

    Parameters:
    -----------
    variable : str
        MODIS variable name
    year : int
        Year to download
    month : int
        Month to download
    date : str
        Specific date to download (YYYY-MM-DD)
    instrument : str
        Satellite instrument ('Terra', 'Aqua', 'Both')
    output_dir : str
        Output directory path
    session : requests.Session
        Authenticated session
    max_workers : int
        Number of parallel downloads

    Returns:
    --------
    dict
        Dictionary with download statistics
    """
    config = MODIS_VARIABLES[variable]

    # Determine which instruments to use
    if instrument == 'Both':
        instruments = [inst for inst in ['Terra', 'Aqua'] if inst in config['products']]
    else:
        if instrument not in config['products']:
            print(f"  ✗ {variable} not available for {instrument}")
            return {'downloaded': 0, 'failed': 0, 'files': []}
        instruments = [instrument]

    # Get CONUS tiles
    tiles = get_conus_tiles()
    print(f"  Using {len(tiles)} MODIS tiles for CONUS coverage")

    downloaded_files = []
    total_downloaded = 0
    total_failed = 0

    for inst in instruments:
        product_id = config['products'][inst]
        base_url = BASE_URLS[inst] + product_id

        print(f"  Processing {inst} {variable} ({product_id})")

        # Generate dates based on provided arguments
        dates = []
        if date:
            dates.append(datetime.strptime(date, '%Y-%m-%d'))
        else:
            if config['temporal_resolution'] == 'daily':
                days_in_month = calendar.monthrange(year, month)[1]
                for day in range(1, days_in_month + 1):
                    dates.append(datetime(year, month, day))
            elif config['temporal_resolution'] == 'monthly':
                dates.append(datetime(year, month, 1))
            elif config['temporal_resolution'] == 'yearly':
                if month == 1:  # Only download yearly data in January
                    dates.append(datetime(year, 1, 1))

        # Download files for each date
        for date_obj in dates:
            formatted_date = get_formatted_date(date_obj, variable)
            directory_url = f"{base_url}/{formatted_date}/"

            print(f"    Checking: {directory_url}")
            available_files = get_available_files(directory_url, session)

            if not available_files:
                print(f"    ⚠ No files found for {formatted_date}")
                continue

            # Filter files for CONUS tiles
            matching_files = []
            for file in available_files:
                if any(tile in file for tile in tiles):
                    matching_files.append(directory_url + file)

            print(f"    Found {len(matching_files)} files for CONUS tiles")

            # Download files in parallel
            if matching_files:
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_url = {
                        executor.submit(download_file, url, output_dir, session): url
                        for url in matching_files
                    }

                    for future in concurrent.futures.as_completed(future_to_url):
                        url = future_to_url[future]
                        try:
                            result = future.result()
                            if result:
                                downloaded_files.append(result)
                                total_downloaded += 1
                            else:
                                total_failed += 1
                        except Exception as e:
                            print(f"    ✗ Error downloading {url}: {e}")
                            total_failed += 1

    return {
        'downloaded': total_downloaded,
        'failed': total_failed,
        'files': downloaded_files
    }

def verify_downloads(output_dir, variables):
    """Verify downloaded files and generate summary"""
    print(f"\nVerifying downloads in: {output_dir}")
    print("-" * 60)

    total_files = 0
    total_size = 0
    variables_found = {}

    for file_path in Path(output_dir).glob("*.hdf"):
        total_files += 1
        file_size = file_path.stat().st_size
        total_size += file_size

        # Identify variable from filename
        filename = file_path.name
        for var in variables:
            config = MODIS_VARIABLES[var]
            for inst, product in config['products'].items():
                product_code = product.split('.')[0]  # e.g., MOD11A1
                if product_code in filename:
                    if var not in variables_found:
                        variables_found[var] = {'files': 0, 'size': 0}
                    variables_found[var]['files'] += 1
                    variables_found[var]['size'] += file_size

    print(f"Total files: {total_files}")
    print(f"Total size: {total_size / (1024**3):.2f} GB")

    for var, stats in variables_found.items():
        print(f"{var}: {stats['files']} files, {stats['size'] / (1024**2):.1f} MB")

    return {
        'total_files': total_files,
        'total_size_gb': total_size / (1024**3),
        'variables': variables_found
    }

def download_modis_variables(variables, year=None, month=None, date=None, instrument='Both',
                           output_dir="./data/raw/MODIS/", max_workers=5):
    """
    Download multiple MODIS variables for specified time period.

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

    if date:
        print(f"Downloading MODIS variables for {date}")
    else:
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

        try:
            result = download_modis_variable(
                variable, year, month, date, instrument, output_dir, session, max_workers
            )

            results[variable] = result
            total_downloaded += result['downloaded']
            total_failed += result['failed']

            print(f"  ✓ {variable}: {result['downloaded']} files downloaded, {result['failed']} failed")

        except Exception as e:
            print(f"  ✗ Error downloading {variable}: {e}")
            results[variable] = {'downloaded': 0, 'failed': 0, 'files': [], 'error': str(e)}
            continue

    # Verify downloads
    verification = verify_downloads(output_dir, variables)

    print(f"\n{'='*60}")
    print(f"  Download Summary:")
    print(f"  Requested variables: {len(variables)}")
    print(f"  Total files downloaded: {total_downloaded}")
    print(f"  Total files failed: {total_failed}")
    print(f"  Total files verified: {verification['total_files']}")
    print(f"  Total size: {verification['total_size_gb']:.2f} GB")
    print(f"  Output directory: {output_dir}")

    return {
        'variables': results,
        'summary': {
            'total_downloaded': total_downloaded,
            'total_failed': total_failed,
            'verification': verification
        }
    }

def main():
    """
    Main function to download MODIS variables.
    """
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Download MODIS variables from NASA Earthdata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Download single variable
        %(prog)s --variables LST --year 2020 --month 1

        # Download multiple variables
        %(prog)s --variables LST,NDVI --year 2020 --month 1

        # Download variable package
        %(prog)s --variables vegetation --year 2019 --month 12

        # Specify output directory and instrument
        %(prog)s --variables LST --year 2020 --month 1 --output-dir /data/MODIS/ --instrument Terra

        Variable examples:
        LST (land surface temperature), NDVI (vegetation index), VCF (vegetation continuous fields)

        Use --list-variables to see all available variables and packages.

        Requirements:
        - NASA Earthdata account and bearer token
        - EARTHDATA_BEARER_TOKEN environment variable
        - requests, beautifulsoup4, pyproj, pandas, numpy
                """
    )
    
    # Add version argument
    parser.add_argument(
        '--version',
        action='version',
        version=f'{__module__} v{__version__}'
    )

    parser.add_argument(
        '--variables', '--vars', '-v',
        type=str,
        help='Comma-separated list of variables to download or variable package name',
        required=False
    )

    time_group = parser.add_mutually_exclusive_group(required=False)
    time_group.add_argument(
        '-d', '--date',
        type=str,
        help='Download specific date (YYYY-MM-DD)'
    )
    time_group.add_argument(
        '--year-month',
        nargs=2,
        metavar=('YEAR', 'MONTH'),
        type=int,
        help='Download specific year and month'
    )

    parser.add_argument(
        '-i', '--instrument',
        type=str,
        choices=['Terra', 'Aqua', 'Both'],
        help='Satellite instrument (default: Both)',
        required=False
    )

    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        help='Output directory for downloaded files',
        required=False
    )

    parser.add_argument(
        '-w', '--workers',
        type=int,
        help='Number of parallel downloads (default: 5)',
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
        # Default to January 2020 if no time is specified
        YEAR = 2020
        MONTH = 1

    print("MODIS Generic Variable Download Script")
    print("=" * 50)

    print(f"  Configuration:")
    print(f"  Variables: {', '.join(VARIABLES)}")
    if DATE:
        print(f"  Date: {DATE}")
    else:
        print(f"  Year: {YEAR}")
        print(f"  Month: {calendar.month_name[MONTH]} ({MONTH})")
    print(f"  Instrument: {INSTRUMENT}")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"  Max workers: {MAX_WORKERS}")
    print()

    # Validate inputs
    if YEAR:
        current_year = datetime.now().year
        if YEAR < 2000 or YEAR > current_year:
            print(f"✗ Error: Year must be between 2000 and {current_year}")
            sys.exit(1)

    if not VARIABLES or (len(VARIABLES) == 1 and not VARIABLES[0].strip()):
        print("✗ Error: At least one variable must be specified")
        print("Use --list-variables to see available options")
        sys.exit(1)

    # Check bearer token
    if not os.getenv("EARTHDATA_BEARER_TOKEN"):
        print("✗ Error: EARTHDATA_BEARER_TOKEN environment variable not set")
        print("Please obtain a bearer token from NASA Earthdata:")
        print("1. Visit: https://urs.earthdata.nasa.gov/")
        print("2. Login and generate a bearer token")
        print("3. Set environment variable: export EARTHDATA_BEARER_TOKEN=your_token")
        sys.exit(1)

    # Check required libraries
    required_packages = ['requests', 'bs4', 'pyproj', 'pandas', 'numpy']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"✗ Missing required packages: {', '.join(missing_packages)}")
        print(f"Install with: pip install {' '.join(missing_packages)}")
        if 'bs4' in missing_packages:
            print("Note: bs4 is installed as 'beautifulsoup4'")
        sys.exit(1)

    # Download data
    # Download data
    results = download_modis_variables(
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
        sys.exit(1)


if __name__ == "__main__":
    main()
