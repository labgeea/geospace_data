#!/usr/bin/env python3
"""
FIRMS Fire Data Download Script
================================

This script downloads NASA FIRMS (Fire Information for Resource Management System) 
active fire data via the FIRMS REST API.

Features:
- Downloads active fire detections by bounding box and date range
- Supports multiple sensors: MODIS, VIIRS S-NPP, VIIRS NOAA-20/21
- Outputs CSV format for easy processing
- Handles API rate limiting and pagination

Data Sources:
- MODIS: 1km resolution, 2000-present
- VIIRS S-NPP: 375m resolution, 2012-present
- VIIRS NOAA-20: 375m resolution, 2018-present
- VIIRS NOAA-21: 375m resolution, 2024-present

Usage:
    python firms_download_generic.py --map-key YOUR_KEY --sensor VIIRS_SNPP_NRT \\
        --bbox -125,24,-66,50 --start-date 2024-01-01 --end-date 2024-01-31 \\
        --output-dir ./data/firms/

API Documentation:
    https://firms.modaps.eosdis.nasa.gov/api/area/
"""

import sys
import os
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta
import requests

# Version information
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from version import get_module_version
    __version__ = get_module_version("firms")
except ImportError:
    __version__ = "1.0.0"

__module__ = "FIRMS Download"

# FIRMS API base URL
FIRMS_API_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Available data sources
VALID_SOURCES = [
    "LANDSAT_NRT",       # Landsat NRT (US/Canada only), 30m
    "MODIS_NRT",         # MODIS Near Real-Time, 1km
    "MODIS_SP",          # MODIS Standard Processing, 1km
    "VIIRS_SNPP_NRT",    # VIIRS Suomi-NPP NRT, 375m
    "VIIRS_SNPP_SP",     # VIIRS Suomi-NPP Standard, 375m
    "VIIRS_NOAA20_NRT",  # VIIRS NOAA-20 NRT, 375m
    "VIIRS_NOAA20_SP",   # VIIRS NOAA-20 Standard, 375m
    "VIIRS_NOAA21_NRT",  # VIIRS NOAA-21 NRT, 375m
]

# Predefined bounding boxes
BBOX_PRESETS = {
    "conus": "-125,24,-66,50",
    "california": "-125,32,-114,42",
    "world": "-180,-90,180,90",
}


def check_dependencies():
    """Check for required dependencies."""
    missing = []
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
        description=f'{__module__} Framework v{__version__} - Download NASA FIRMS Active Fire Data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download VIIRS S-NPP data for CONUS, January 2024
  python firms_download_generic.py --map-key YOUR_KEY --sensor VIIRS_SNPP_NRT \\
      --bbox conus --start-date 2024-01-01 --end-date 2024-01-31 --output-dir ./data/

  # Download MODIS data for California, specific dates
  python firms_download_generic.py --map-key YOUR_KEY --sensor MODIS_NRT \\
      --bbox -125,32,-114,42 --start-date 2024-06-01 --end-date 2024-06-30 --output-dir ./output/

Sensors:
  MODIS_NRT       - MODIS Near Real-Time (1km, 2000-present)
  MODIS_SP        - MODIS Standard Processing (1km, science quality)
  VIIRS_SNPP_NRT  - VIIRS Suomi-NPP NRT (375m, 2012-present)
  VIIRS_SNPP_SP   - VIIRS Suomi-NPP Standard (375m, science quality)
  VIIRS_NOAA20_NRT - VIIRS NOAA-20 NRT (375m, 2018-present)
  VIIRS_NOAA21_NRT - VIIRS NOAA-21 NRT (375m, 2024-present)
  LANDSAT_NRT     - Landsat NRT (30m, US/Canada only, 2022-present)

Bounding Box Presets:
  conus      - Continental US (-125,24,-66,50)
  california - California (-125,32,-114,42)
  world      - Global (-180,-90,180,90)
        """
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--map-key', required=True, 
                        help='FIRMS MAP_KEY (get one at https://firms.modaps.eosdis.nasa.gov/api/)')
    parser.add_argument('--sensor', required=True, choices=VALID_SOURCES,
                        help='Data source/sensor to download')
    parser.add_argument('--bbox', required=True,
                        help='Bounding box as "west,south,east,north" or preset name (conus, california, world)')
    parser.add_argument('--start-date', required=True,
                        help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True,
                        help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', required=True,
                        help='Directory to save downloaded CSV files')
    parser.add_argument('--chunk-days', type=int, default=5,
                        help='Number of days per API request (max 10, default: 5)')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between API requests in seconds (default: 1.0)')
    parser.add_argument('--force', action='store_true',
                        help='Overwrite existing files')
    
    return parser


def parse_bbox(bbox_str: str) -> str:
    """Parse bounding box string or return preset."""
    if bbox_str.lower() in BBOX_PRESETS:
        return BBOX_PRESETS[bbox_str.lower()]
    
    # Validate format
    parts = bbox_str.split(',')
    if len(parts) != 4:
        raise ValueError(f"Invalid bbox format: {bbox_str}. Expected 'west,south,east,north'")
    
    try:
        west, south, east, north = [float(p) for p in parts]
        if not (-180 <= west <= 180 and -180 <= east <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if not (-90 <= south <= 90 and -90 <= north <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if west >= east:
            raise ValueError("West must be less than East")
        if south >= north:
            raise ValueError("South must be less than North")
    except ValueError as e:
        raise ValueError(f"Invalid bbox: {e}")
    
    return bbox_str


def download_firms_data(map_key: str, source: str, bbox: str, 
                        date: str, day_range: int = 1) -> tuple:
    """
    Download FIRMS data via API.
    
    Args:
        map_key: FIRMS API key
        source: Data source (e.g., VIIRS_SNPP_NRT)
        bbox: Bounding box as "west,south,east,north"
        date: Date in YYYY-MM-DD format
        day_range: Number of days to request (1-10)
    
    Returns:
        Tuple of (csv_content, row_count) or (None, 0) on error
    """
    # Build API URL
    # Format: /api/area/csv/[MAP_KEY]/[SOURCE]/[AREA]/[DAYS]/[DATE]
    url = f"{FIRMS_API_BASE}/{map_key}/{source}/{bbox}/{day_range}/{date}"
    
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        
        content = response.text
        
        # Check for error responses
        if "Error" in content[:100] or "Invalid" in content[:100]:
            print(f"    API Error: {content[:200]}")
            return None, 0
        
        # Count rows (subtract 1 for header)
        lines = content.strip().split('\n')
        row_count = max(0, len(lines) - 1)
        
        return content, row_count
        
    except requests.exceptions.RequestException as e:
        print(f"    Request failed: {e}")
        return None, 0


def main():
    """Main entry point."""
    check_dependencies()
    import pandas as pd
    
    parser = create_parser()
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"  {__module__} v{__version__}")
    print(f"  NASA FIRMS Active Fire Data Downloader")
    print(f"{'='*60}\n")
    
    # Parse dates
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError as e:
        print(f"Error: Invalid date format. Use YYYY-MM-DD. {e}")
        sys.exit(1)
    
    if start_date > end_date:
        print("Error: Start date must be before or equal to end date")
        sys.exit(1)
    
    # Parse bbox
    try:
        bbox = parse_bbox(args.bbox)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Calculate date chunks
    total_days = (end_date - start_date).days + 1
    chunk_days = min(args.chunk_days, 10)  # API max is 10 days
    
    print(f"=== Download Configuration ===")
    print(f"  Sensor: {args.sensor}")
    print(f"  Bounding Box: {bbox}")
    print(f"  Date Range: {args.start_date} to {args.end_date} ({total_days} days)")
    print(f"  Chunk Size: {chunk_days} days per request")
    print(f"  Output: {args.output_dir}")
    print()
    
    # Download in chunks
    all_data = []
    total_fires = 0
    current_date = start_date
    request_count = 0
    
    print("=== Downloading Data ===")
    
    while current_date <= end_date:
        # Calculate chunk end
        chunk_end = min(current_date + timedelta(days=chunk_days-1), end_date)
        days_in_chunk = (chunk_end - current_date).days + 1
        
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"  Requesting {date_str} ({days_in_chunk} days)...", end=" ", flush=True)
        
        content, row_count = download_firms_data(
            args.map_key, args.sensor, bbox, date_str, days_in_chunk
        )
        
        if content and row_count > 0:
            print(f"{row_count} fire detections")
            total_fires += row_count
            
            # Parse CSV and append
            from io import StringIO
            df = pd.read_csv(StringIO(content))
            all_data.append(df)
        elif content:
            print("0 fire detections")
        else:
            print("failed")
        
        # Move to next chunk
        current_date = chunk_end + timedelta(days=1)
        request_count += 1
        
        # Rate limiting
        if current_date <= end_date:
            time.sleep(args.delay)
    
    print()
    
    # Combine and save
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Generate output filename
        date_range = f"{args.start_date}_to_{args.end_date}".replace('-', '')
        output_file = os.path.join(
            args.output_dir, 
            f"FIRMS_{args.sensor}_{date_range}.csv"
        )
        
        # Check for existing file
        if os.path.exists(output_file) and not args.force:
            print(f"Warning: Output file exists. Use --force to overwrite.")
            output_file = output_file.replace('.csv', f'_{int(time.time())}.csv')
        
        combined_df.to_csv(output_file, index=False)
        
        print(f"=== Download Complete ===")
        print(f"  Total Fire Detections: {total_fires:,}")
        print(f"  API Requests: {request_count}")
        print(f"  Output File: {output_file}")
        print(f"  File Size: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
        print(f"\nColumns: {', '.join(combined_df.columns[:8])}...")
        
    else:
        print("=== No Data Downloaded ===")
        print("  No fire detections found for the specified parameters.")
        print("  Try a different date range or check your MAP_KEY.")
    
    print()


if __name__ == "__main__":
    main()
