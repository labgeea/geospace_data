#!/usr/bin/env python3
"""
NOAA Storm Events Processing Script
===================================

This script processes NOAA Storm Events Database CSV files.
It standardizes columns, parses financial damage fields, creates geometries,
and can output both CSV and GeoPackage formats.

Features:
- Parses "DAMAGE_PROPERTY" and "DAMAGE_CROPS" (e.g., "2.5K" -> 2500)
- Standardizes timestamps
- Creates Point geometries from BEGIN_LAT/BEGIN_LON
- Filters by State or Event Type

Usage:
    python storms_process_generic.py --input-file data/storms/raw.csv --output-dir data/storms/proc/
"""

import sys
import os
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Version information
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from version import get_module_version
    __version__ = get_module_version("storms")
except ImportError:
    __version__ = "1.0.0"

__module__ = "Storms Processing"


def check_dependencies():
    """Check for required dependencies."""
    missing = []
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    try:
        import geopandas
    except ImportError:
        missing.append("geopandas")
    
    if missing:
        print(f"Error: Missing required packages: {', '.join(missing)}")
        print("Please install them using: mamba install " + " ".join(missing))
        sys.exit(1)


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Process NOAA Storm Events',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--input-file', required=True,
                        help='Path to downloaded NOAA Storm Events CSV')
    parser.add_argument('--output-dir', required=True,
                        help='Directory to save processed output')
    parser.add_argument('--state', 
                        help='Filter by State Name (e.g., "CALIFORNIA")')
    parser.add_argument('--event-types',
                        help='Filter by Event Types (comma-separated, e.g., "Flood,Tornado")')
    parser.add_argument('--geo', action='store_true',
                        help='Save as GeoPackage (requires active lat/lon in data)')
    
    return parser


def parse_damage_amount(value):
    """
    Parse damage amount strings like '2.50K', '5M', '0' into floats.
    suffixes: K=10^3, M=10^6, B=10^9
    """
    if pd.isna(value) or value == "":
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
        
    value = str(value).upper().strip()
    if value == "0":
        return 0.0
        
    multiplier = 1.0
    if value.endswith('K'):
        multiplier = 1000.0
        value = value[:-1]
    elif value.endswith('M'):
        multiplier = 1000000.0
        value = value[:-1]
    elif value.endswith('B'):
        multiplier = 1000000000.0
        value = value[:-1]
        
    try:
        return float(value) * multiplier
    except ValueError:
        return 0.0


def load_and_clean_data(input_file):
    """Load CSV and clean columns."""
    print(f"  Loading: {input_file}")
    # Low_memory=False to handle mixed types in some optional columns
    df = pd.read_csv(input_file, low_memory=False)
    
    # Standardize headers to lowercase
    df.columns = df.columns.str.lower()
    
    # Parse damage columns
    print("  Parsing damage estimates...")
    df['damage_property_num'] = df['damage_property'].apply(parse_damage_amount)
    df['damage_crops_num'] = df['damage_crops'].apply(parse_damage_amount)
    
    # Parse dates
    # format is typically "DD-MMM-YY HH:MM:SS" (e.g. 25-OCT-23 02:30:00)
    print("  Parsing dates...")
    # Format matches "25-OCT-23 02:30:00"
    df['begin_timestamp'] = pd.to_datetime(df['begin_date_time'], format='%d-%b-%y %H:%M:%S', errors='coerce')
    
    return df


def main():
    check_dependencies()
    import geopandas as gpd
    from shapely.geometry import Point
    
    parser = create_parser()
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"  {__module__} v{__version__}")
    print(f"  NOAA Storm Events Processor")
    print(f"{'='*60}\n")
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    df = load_and_clean_data(args.input_file)
    print(f"  Loaded {len(df):,} records")
    
    # Filtering
    if args.state:
        target_state = args.state.upper()
        print(f"  Filtering by state: {target_state}")
        df = df[df['state'] == target_state]
        print(f"  -> {len(df):,} records remaining")
        
    if args.event_types:
        types = [t.strip().upper() for t in args.event_types.split(',')]
        print(f"  Filtering by events: {types}")
        # Event type in CSV is often mixed case or upper, standardize to check
        df = df[df['event_type'].str.upper().isin(types)]
        print(f"  -> {len(df):,} records remaining")
        
    # Output name
    base_name = Path(args.input_file).stem.replace('.csv', '')
    if args.state:
        base_name += f"_{args.state}"
    
    # Save results
    if args.geo:
        # Create GeoDataFrame
        # Must have valid coordinates. Filter for them.
        valid_coords = df.dropna(subset=['begin_lat', 'begin_lon'])
        dropped = len(df) - len(valid_coords)
        if dropped > 0:
            print(f"  Note: Dropped {dropped:,} records missing coordinates for GeoPackage")
            
        geometry = [Point(xy) for xy in zip(valid_coords['begin_lon'], valid_coords['begin_lat'])]
        gdf = gpd.GeoDataFrame(valid_coords, geometry=geometry, crs="EPSG:4326")
        
        out_file = os.path.join(args.output_dir, f"{base_name}_spatial.gpkg")
        print(f"  Saving GeoPackage: {out_file}")
        gdf.to_file(out_file, driver="GPKG")
    else:
        out_file = os.path.join(args.output_dir, f"{base_name}_processed.csv")
        print(f"  Saving CSV: {out_file}")
        df.to_csv(out_file, index=False)
        
    print(f"\nProcessing Complete!")


if __name__ == "__main__":
    main()
