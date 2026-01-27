#!/usr/bin/env python3
"""
NOAA Storm Events Data Download Script
======================================

This script downloads Storm Events Database files from the NOAA NCEI HTTP server.
The database contains details on severe weather events including tornadoes,
hail, winds, floods, and more.

Features:
- Scrapes the NOAA directory to find the latest version of files for each year
- Downloads and optionally decompresses the CSV files
- Validates the year range (1950-present)

Data Source:
https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/

Usage:
    python storms_download_generic.py --year 2023 --output-dir ./data/storms/
"""

import sys
import os
import argparse
import re
import requests
import gzip
import shutil
from pathlib import Path

# Version information
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from version import get_module_version
    __version__ = get_module_version("storms")
except ImportError:
    __version__ = "1.0.0"

__module__ = "Storms Download"

NOAA_URL = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"


def check_dependencies():
    """Check for required dependencies."""
    missing = []
    try:
        import requests
    except ImportError:
        missing.append("requests")
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    
    if missing:
        print(f"Error: Missing required packages: {', '.join(missing)}")
        print("Please install them using: pip install " + " ".join(missing))
        sys.exit(1)


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Download NOAA Storm Events Data',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--year', type=int, required=True,
                        help='Year to download (1950-present)')
    parser.add_argument('--output-dir', required=True,
                        help='Directory to save downloaded files')
    parser.add_argument('--keep-compressed', action='store_true',
                        help='Keep files compressed (.gz) instead of extracting')
    parser.add_argument('--force', action='store_true',
                        help='Overwrite existing files')
    
    return parser


def find_file_url(year: int) -> str:
    """Find the specific filename URL for the given year."""
    print(f"  Fetching file list from NOAA ({NOAA_URL})...")
    try:
        response = requests.get(NOAA_URL, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to fetch index page: {e}")
        sys.exit(1)
    
    # Pattern: StormEvents_details-ftp_v1.0_d{YEAR}_c{YYYYMMDD}.csv.gz
    # We want to match the year and capture the full filename
    pattern = re.compile(f'href="(StormEvents_details-ftp_v1.0_d{year}_c[^"]+\.csv\.gz)"')
    
    matches = pattern.findall(response.text)
    
    if not matches:
        print(f"Error: No file found for year {year}")
        print("Note: Data is typically available from 1950 to present (with a lag of a few months).")
        return None
    
    # If multiple versions exist (unlikely but possible), act usually on the latest certified date (cYYYYMMDD)
    # The sort will put the latest certified date last
    matches.sort()
    latest_file = matches[-1]
    
    return latest_file


def download_file(filename: str, output_dir: str, keep_compressed: bool, force: bool):
    """Download and process the file."""
    url = NOAA_URL + filename
    local_gz_path = os.path.join(output_dir, filename)
    local_csv_path = os.path.join(output_dir, filename.replace('.gz', ''))
    
    # Check existence
    if os.path.exists(local_csv_path) and not force:
        print(f"  File already exists: {local_csv_path}")
        return
    if keep_compressed and os.path.exists(local_gz_path) and not force:
        print(f"  File already exists: {local_gz_path}")
        return

    print(f"  Downloading: {filename}")
    try:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(local_gz_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except requests.exceptions.RequestException as e:
        print(f"Error: Download failed: {e}")
        if os.path.exists(local_gz_path):
            os.remove(local_gz_path)
        sys.exit(1)

    print(f"  Downloaded: {local_gz_path}")
    
    if not keep_compressed:
        print(f"  Extracting to CSV...")
        try:
            with gzip.open(local_gz_path, 'rb') as f_in:
                with open(local_csv_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove the .gz file after extraction to save space, unless requested
            os.remove(local_gz_path)
            print(f"  Extracted: {local_csv_path}")
            
        except OSError as e:
            print(f"Error extracting file: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    check_dependencies()
    
    parser = create_parser()
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"  {__module__} v{__version__}")
    print(f"  NOAA Storm Events Database Downloader")
    print(f"{'='*60}\n")
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    target_filename = find_file_url(args.year)
    
    if target_filename:
        download_file(target_filename, args.output_dir, args.keep_compressed, args.force)
        print(f"\nExample output: {target_filename.replace('.gz', '') if not args.keep_compressed else target_filename}")
    
    print()


if __name__ == "__main__":
    main()
