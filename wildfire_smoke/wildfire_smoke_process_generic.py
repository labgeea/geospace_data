#!/usr/bin/env python3
"""
Wildfire Smoke Reanalysis Processing Script
Reads canonical Stanford CSVs, generates the full sequence of dates, 
fills 0s for missing (non-smoke) days, and partitions by year as Parquet files.
"""

import sys
import os
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Setup GEOSPACE framework version mapping
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from version import get_module_version
    __version__ = get_module_version("wildfire_smoke")
except ImportError:
    __version__ = "1.0.0"

__module__ = "Wildfire Smoke Processing"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GEO_COLS = {
    '10km': 'grid_id_10km',
    'county': 'GEOID',
    'tract': 'GEOID',
    'zcta': 'GEOID10'
}

def create_parser():
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Process Stanford Smoke PM2.5'
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--geography', '-g', choices=['10km', 'county', 'tract', 'zcta', 'all'], 
                        required=True, help='Spatial resolution to process')
    parser.add_argument('--input-dir', '-i', type=Path, required=True, 
                        help='Input directory containing the downloaded Stanford Smoke CSVs')
    parser.add_argument('--output-dir', '-o', type=Path, default=Path('./proc'), 
                        help='Output directory to save processed Parquet files')
    parser.add_argument('--years', '-y', nargs='+', type=int, 
                        help='Specific years to process (default: all available 2006-2020)')
    
    return parser

def process_geography(geo: str, args):
    id_col = GEO_COLS[geo]
    
    # Identify the CSV
    csv_file = list(args.input_dir.glob(f"smokePM2pt5_predictions_daily_{geo}_*.csv"))
    if not csv_file:
        logger.error(f"Could not find input CSV for {geo} in {args.input_dir}")
        sys.exit(1)
    csv_file = csv_file[0]
    
    # Sniff the delimiter (10km is comma-separated, county is tab-separated)
    with open(csv_file, 'r') as f:
        first_line = f.readline()
        delimiter = '\t' if '\t' in first_line else ','
        
    logger.info(f"Loading raw data from {csv_file.name} with delimiter '{repr(delimiter)}'...")
    # Load raw data - specifying types for speed
    df_raw = pd.read_csv(csv_file, sep=delimiter, dtype={id_col: str, 'smokePM_pred': np.float32})
    df_raw['date'] = pd.to_datetime(df_raw['date'].astype(str), format='%Y%m%d')
    
    # The unique values across 15 years in the CSV are highly likely to contain the full set of regions.
    unique_ids = df_raw[id_col].unique()
    logger.info(f"Found {len(unique_ids)} unique regions for {geo}.")
    
    years_to_process = args.years if args.years else sorted(df_raw['date'].dt.year.unique())
    
    for year in years_to_process:
        logger.info(f"Processing Year {year}...")
        
        # 1. Filter raw data to year
        df_year = df_raw[df_raw['date'].dt.year == year].copy()
        
        # 2. Build full Cartesian product of (unique_ids x all_dates_in_year)
        dates_in_year = pd.date_range(start=f"{year}-01-01", end=f"{year}-12-31", freq='D')
        
        logger.info(f"Building full structural index for {len(unique_ids)} regions and {len(dates_in_year)} days...")
        idx = pd.MultiIndex.from_product([unique_ids, dates_in_year], names=[id_col, 'date'])
        df_full = pd.DataFrame(index=idx).reset_index()
        
        # 3. Merge with actual data
        df_merged = pd.merge(df_full, df_year, on=[id_col, 'date'], how='left')
        
        # 4. Fill missing non-smoke days with 0.0
        df_merged['smokePM_pred'] = df_merged['smokePM_pred'].fillna(0.0)
        
        # 5. Export to Parquet
        out_file = args.output_dir / f"{geo}" / f"smokePM25_{geo}_{year}.parquet"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving {out_file} ({len(df_merged)} rows)...")
        # Ensure optimal datatypes for compression
        df_merged['smokePM_pred'] = df_merged['smokePM_pred'].astype(np.float32)
        df_merged.to_parquet(out_file, engine='pyarrow', index=False, compression='snappy')
        
    logger.info(f"Completed processing for all selected years.")

def main():
    parser = create_parser()
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    geos = list(GEO_COLS.keys()) if args.geography == 'all' else [args.geography]
    
    logger.info(f"Target Geographies: {', '.join(geos)}")
    for geo in geos:
        process_geography(geo, args)

if __name__ == "__main__":
    main()
