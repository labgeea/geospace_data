#!/usr/bin/env python3
"""
PLACES Data Download Script
===========================

This script downloads CDC PLACES data at the ZCTA (ZIP Code Tabulation Area) level.
It supports bulk CSV downloads for all available years (2020-2025).

Features:
- Downloads ZCTA-level health data from CDC PLACES
- Supports year selection (2020-2025)
- Optional state filtering
- Uses Socrata Open Data API for direct CSV download

Usage:
    python places_download_generic.py --year 2024 --output-dir ./data/places/
    python places_download_generic.py --year 2024 --output-dir ./data/places/ --state CA
"""

import sys
import os
import argparse
from pathlib import Path
import requests

# Version information
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from version import get_module_version
    __version__ = get_module_version("places")
except ImportError:
    __version__ = "1.0.0"

__module__ = "PLACES Download"

# Dataset IDs for ZCTA-level data by release year
# These are Socrata dataset identifiers from data.cdc.gov
DATASET_IDS = {
    2025: "cwsq-ngmh",  # PLACES 2025 release
    2024: "gd4x-jyhw",  # PLACES 2024 release
    2023: "swc5-untb",  # PLACES 2023 release
    2022: "bdcs-8k6j",  # PLACES 2022 release
    2021: "xgsh-4g3c",  # PLACES 2021 release
    2020: "373s-ayzu",  # PLACES 2020 release
}

# Supported years
SUPPORTED_YEARS = sorted(DATASET_IDS.keys())


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
        description=f'{__module__} Framework v{__version__} - Download CDC PLACES ZCTA Data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Download 2024 data
  python places_download_generic.py --year 2024 --output-dir ./data/

  # Download all available years
  for year in 2020 2021 2022 2023 2024 2025; do
    python places_download_generic.py --year $year --output-dir ./data/
  done

Supported years: {', '.join(map(str, SUPPORTED_YEARS))}

Note: ZCTA data covers all US ZCTAs. State-level filtering can be done 
during processing using the processing script.
        """
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--year', type=int, required=True, 
                        choices=SUPPORTED_YEARS,
                        help=f'Release year to download ({min(SUPPORTED_YEARS)}-{max(SUPPORTED_YEARS)})')
    parser.add_argument('--output-dir', required=True, 
                        help='Directory to save downloaded CSV files')
    parser.add_argument('--force', action='store_true',
                        help='Overwrite existing files')
    
    return parser


def get_download_url(year: int) -> str:
    """
    Construct the download URL for a given year.
    
    Args:
        year: Release year
        
    Returns:
        Download URL string
    """
    dataset_id = DATASET_IDS.get(year)
    if not dataset_id:
        raise ValueError(f"No dataset ID found for year {year}")
    
    # Use bulk download endpoint for full dataset
    url = f"https://data.cdc.gov/api/views/{dataset_id}/rows.csv?accessType=DOWNLOAD"
    return url


def download_places_data(year: int, output_dir: str, force: bool = False) -> str:
    """
    Download PLACES ZCTA data for a given year.
    
    Args:
        year: Release year
        output_dir: Directory to save the file
        force: Overwrite existing files
        
    Returns:
        Path to downloaded file
    """
    import pandas as pd
    
    # Construct output filename
    output_filename = f"places_zcta_{year}.csv"
    output_path = os.path.join(output_dir, output_filename)
    
    # Check if file exists
    if os.path.exists(output_path) and not force:
        print(f"  File already exists: {output_path}")
        print("  Use --force to overwrite")
        return output_path
    
    # Get download URL
    url = get_download_url(year)
    
    print(f"  Downloading from: data.cdc.gov (dataset: {DATASET_IDS[year]})")
    print(f"  This may take a few minutes for large files...")
    
    
    
    try:
        # Stream download for large files
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Get content length if available
        total_size = int(response.headers.get('content-length', 0))
        
        # Write to file with progress
        downloaded = 0
        chunk_size = 8192
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        print(f"\r  Progress: {pct:.1f}% ({downloaded / 1024 / 1024:.1f} MB)", end='')
        
        print()  # Newline after progress
        
        # Verify the download
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"  Downloaded: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
            
            # Quick validation - read first few rows
            try:
                df = pd.read_csv(output_path, nrows=5)
                print(f"  Columns: {len(df.columns)}")
                print(f"  Sample columns: {', '.join(df.columns[:5])}...")
            except Exception as e:
                print(f"  Warning: Could not validate CSV: {e}")
        
        return output_path
        
    except requests.exceptions.RequestException as e:
        print(f"  Error downloading data: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)  # Clean up partial download
        sys.exit(1)


def main():
    """Main entry point."""
    check_dependencies()
    
    parser = create_parser()
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"  {__module__} v{__version__}")
    print(f"  CDC PLACES ZCTA Data Downloader")
    print(f"{'='*60}\n")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"=== Downloading PLACES {args.year} ZCTA Data ===")
    
    # Download the data
    output_file = download_places_data(
        year=args.year,
        output_dir=args.output_dir,
        force=args.force
    )
    
    print(f"\n=== Download Complete ===")
    print(f"  Output: {output_file}")
    print(f"\nNext step: Process with places_process_generic.py")


if __name__ == "__main__":
    main()
