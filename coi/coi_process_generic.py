#!/usr/bin/env python3
"""
COI Data Processing Script
=========================

This script processes Child Opportunity Index (COI) data.
It filters COI data by year and merges it with Census Tract geometries to create spatial datasets (GeoPackage).

Features:
- Loads unified COI CSV data
- Filters by specified year
- Fetches Census Tract geometry (2020 baseline) using pygris
- Merges COI attributes with Tract geometries
- Exports as GeoPackage

Usage:
    python coi_process_generic.py --coi-data-file ./data/coi/coi_tract_2k23.csv --output-dir ./output --year 2020
"""

import sys
import os
import argparse
from pathlib import Path
import warnings

# Version information
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from version import get_module_version
    __version__ = get_module_version("coi")
except ImportError:
    __version__ = "1.0.0"

__module__ = "COI Processing"

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
    try:
        import pygris
    except ImportError:
        missing.append("pygris")
    
    if missing:
        print(f"Error: Missing required packages: {', '.join(missing)}")
        print("Please install them using: mamba install " + " ".join(missing))
        sys.exit(1)

def create_parser():
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Process COI Data to Spatial Format',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--coi-data-file', required=True, help='Path to the unified COI CSV file')
    parser.add_argument('--output-dir', required=True, help='Directory to save output GeoPackage files')
    parser.add_argument('--year', type=int, help='Specific year to process. If omitted, processes all years in the file.')
    
    return parser

def fetch_tracts_for_states(states, year_hint=2020):
    """Fetch census tracts for a list of states."""
    import pygris
    import pandas as pd
    
    # COI 2.0+ usually uses 2010 boundaries (prior to 2020 Census releases) but 2.0.2 might use 2020?
    # The reference script uses 'geoid20' which implies 2020 Census geography.
    # So we should fetch 2020 tracts.
    target_year = 2020
    
    print(f"  Fetching {target_year} Census Tracts for {len(states)} states...")
    
    tracts_list = []
    for st in states:
        if str(st).isdigit(): continue
        
        try:
            # CB=True for lighter files (cartographic boundary)
            t = pygris.tracts(state=st, cb=True, year=target_year)
            tracts_list.append(t)
        except Exception as e:
            print(f"    Warning: Failed to fetch tracts for {st}: {e}")
            
    if not tracts_list:
        return None
        
    return pd.concat(tracts_list)

def main():
    check_dependencies()
    import pandas as pd
    import geopandas as gpd
    
    parser = create_parser()
    args = parser.parse_args()
    
    print(f"Running {__module__} v{__version__}")
    
    if not os.path.exists(args.coi_data_file):
        print(f"Error: COI Data File {args.coi_data_file} not found")
        sys.exit(1)
        
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("\n=== Loading COI Data ===")
    try:
        # Load all logic from CSV
        # geoid20 should be string
        df = pd.read_csv(args.coi_data_file, dtype={'geoid20': str, 'state_fips': str, 'county_fips': str})
    except Exception as e:
        print(f"Error reading COI file: {e}")
        sys.exit(1)
        
    print(f"  Loaded {len(df)} rows. Years found: {sorted(df['year'].unique())}")
    
    # Determine years to process
    if args.year:
        years_to_process = [args.year]
    else:
        years_to_process = sorted(df['year'].unique())
        
    for y in years_to_process:
        print(f"\n=== Processing Year {y} ===")
        
        # Filter data
        year_df = df[df['year'] == y].copy()
        
        if year_df.empty:
            print(f"  No data for year {y}")
            continue
            
        print(f"  Found {len(year_df)} records")
        
        # Identify states
        # The COI file usually has 'state_usps' or 'state_name'
        if 'state_usps' in year_df.columns:
            states = year_df['state_usps'].dropna().unique()
        elif 'state_name' in year_df.columns:
            states = year_df['state_name'].dropna().unique()
        else:
            print("  Warning: Could not identify state column (state_usps/state_name). Cannot fetch tracts efficiently.")
            # Fallback?
            continue
            
        # Fetch Geometry
        tracts_gdf = fetch_tracts_for_states(states)
        
        if tracts_gdf is None or tracts_gdf.empty:
            print("  Error: Could not fetch tract geometry. Skipping.")
            continue
            
        print("  Merging COI attributes to geometry...")
        
        # Ensure GEOID match
        # pygris 2020 tracts usually 'GEOID' column
        if 'GEOID' in tracts_gdf.columns:
            tracts_gdf['geoid20'] = tracts_gdf['GEOID']
        
        # Merge
        # We output everything in the COI file attached to geometry
        merged_gdf = tracts_gdf.merge(year_df, on='geoid20', how='inner')
        
        print(f"  Result: {len(merged_gdf)} tracts with data")
        
        if not merged_gdf.empty:
            output_filename = f"COI_{y}_Spatial.gpkg"
            output_path = os.path.join(args.output_dir, output_filename)
            print(f"  Saving to {output_path}...")
            merged_gdf.to_file(output_path, driver="GPKG")
            print("  Done.")

if __name__ == "__main__":
    main()
