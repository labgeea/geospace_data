#!/usr/bin/env python3
"""
FIRMS Fire Data Processing Script
==================================

This script processes NASA FIRMS active fire data.
It can aggregate fire detections to geographic units (County, ZCTA) and 
calculate summary statistics.

Features:
- Aggregates point fire detections to polygons (County/ZCTA)
- Calculates fire count, total FRP, and detection days per polygon
- Supports temporal aggregation (daily, monthly, annual)
- Outputs as CSV or GeoPackage

Usage:
    python firms_process_generic.py --input-file ./data/firms_2023.csv \\
        --output-dir ./output --aggregation-level county --temporal monthly
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
import warnings

# Version information
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from version import get_module_version
    __version__ = get_module_version("firms")
except ImportError:
    __version__ = "1.0.0"

__module__ = "FIRMS Processing"

# Aggregation levels
AGGREGATION_LEVELS = ["none", "county", "zcta", "state"]
TEMPORAL_LEVELS = ["none", "daily", "monthly", "annual"]


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
        description=f'{__module__} Framework v{__version__} - Process NASA FIRMS Active Fire Data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic processing - just clean and standardize
  python firms_process_generic.py --input-file ./data/firms_2023.csv --output-dir ./output/

  # Aggregate to county level with monthly totals
  python firms_process_generic.py --input-file ./data/firms_2023.csv --output-dir ./output/ \\
      --aggregation-level county --temporal monthly

  # Aggregate to ZCTA level with annual totals
  python firms_process_generic.py --input-file ./data/firms_2023.csv --output-dir ./output/ \\
      --aggregation-level zcta --temporal annual --with-geometry

Output Variables:
  fire_count      - Number of fire detections
  frp_total       - Total Fire Radiative Power (MW)
  frp_mean        - Mean Fire Radiative Power (MW)
  fire_days       - Number of unique days with fire detections
  high_conf_count - Number of high-confidence detections
        """
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--input-file', required=True, 
                        help='Path to downloaded FIRMS CSV file')
    parser.add_argument('--output-dir', required=True, 
                        help='Directory to save processed output')
    parser.add_argument('--aggregation-level', choices=AGGREGATION_LEVELS, default='none',
                        help='Spatial aggregation level (default: none)')
    parser.add_argument('--temporal', choices=TEMPORAL_LEVELS, default='none',
                        help='Temporal aggregation level (default: none)')
    parser.add_argument('--with-geometry', action='store_true',
                        help='Include geometry in output (GeoPackage)')
    parser.add_argument('--min-confidence', type=int, default=0,
                        help='Minimum confidence threshold (0-100, default: 0)')
    parser.add_argument('--state-filter', 
                        help='Filter to specific state(s), comma-separated (e.g., CA,OR,WA)')
    
    return parser


def load_fire_data(input_file: str) -> 'pd.DataFrame':
    """Load and standardize FIRMS CSV data."""
    import pandas as pd
    
    print(f"  Loading: {input_file}")
    df = pd.read_csv(input_file)
    
    # Standardize column names (handle both MODIS and VIIRS)
    df.columns = df.columns.str.lower()
    
    # Ensure required columns exist
    required = ['latitude', 'longitude', 'acq_date']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Parse date
    df['acq_date'] = pd.to_datetime(df['acq_date'])
    df['year'] = df['acq_date'].dt.year
    df['month'] = df['acq_date'].dt.month
    df['day'] = df['acq_date'].dt.day
    
    # Standardize FRP column name
    if 'frp' not in df.columns:
        df['frp'] = 0.0
    
    # Standardize confidence (VIIRS uses low/nominal/high, MODIS uses 0-100)
    if 'confidence' in df.columns:
        # Convert string confidence to numeric
        conf_map = {'l': 30, 'low': 30, 'n': 50, 'nominal': 50, 'h': 80, 'high': 80}
        if df['confidence'].dtype == object:
            df['confidence'] = df['confidence'].str.lower().map(conf_map).fillna(50)
        df['confidence'] = pd.to_numeric(df['confidence'], errors='coerce').fillna(50)
    else:
        df['confidence'] = 50
    
    print(f"  Loaded {len(df):,} fire detections")
    print(f"  Date range: {df['acq_date'].min()} to {df['acq_date'].max()}")
    
    return df


def spatial_join_to_polygons(df: 'pd.DataFrame', level: str) -> 'gpd.GeoDataFrame':
    """Join fire points to polygon geometries."""
    import geopandas as gpd
    from shapely.geometry import Point
    import pygris
    
    print(f"  Performing spatial join to {level} polygons...")
    
    # Create point geometries
    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    
    # Fetch appropriate polygons
    if level == 'county':
        print("  Fetching county boundaries...")
        polygons = pygris.counties(cb=True, year=2020)
        id_col = 'GEOID'
        name_col = 'NAME'
    elif level == 'zcta':
        print("  Fetching ZCTA boundaries...")
        polygons = pygris.zctas(cb=True, year=2020)
        id_col = 'ZCTA5CE20'
        name_col = 'ZCTA5CE20'
    elif level == 'state':
        print("  Fetching state boundaries...")
        polygons = pygris.states(cb=True, year=2020)
        id_col = 'GEOID'
        name_col = 'NAME'
    else:
        raise ValueError(f"Unknown aggregation level: {level}")
    
    # Ensure same CRS
    polygons = polygons.to_crs("EPSG:4326")
    
    print(f"  Fetched {len(polygons):,} polygons")
    
    # Spatial join
    joined = gpd.sjoin(gdf, polygons[[id_col, name_col, 'geometry']], 
                       how='left', predicate='within')
    
    # Rename columns
    joined = joined.rename(columns={id_col: 'polygon_id', name_col: 'polygon_name'})
    
    # Remove fires that didn't fall in any polygon
    n_outside = joined['polygon_id'].isna().sum()
    if n_outside > 0:
        print(f"  Note: {n_outside:,} fires outside polygon boundaries")
        joined = joined.dropna(subset=['polygon_id'])
    
    print(f"  Joined {len(joined):,} fires to polygons")
    
    return joined, polygons


def aggregate_fires(df: 'pd.DataFrame', spatial_level: str, 
                    temporal_level: str) -> 'pd.DataFrame':
    """Aggregate fire data by space and time."""
    import pandas as pd
    
    # Build groupby columns
    group_cols = []
    
    if spatial_level != 'none':
        group_cols.extend(['polygon_id', 'polygon_name'])
    
    if temporal_level == 'annual':
        group_cols.append('year')
    elif temporal_level == 'monthly':
        group_cols.extend(['year', 'month'])
    elif temporal_level == 'daily':
        group_cols.append('acq_date')
    
    if not group_cols:
        # No aggregation - return basic summary
        return df
    
    print(f"  Aggregating by: {', '.join(group_cols)}")
    
    # Aggregate
    agg_df = df.groupby(group_cols).agg(
        fire_count=('latitude', 'count'),
        frp_total=('frp', 'sum'),
        frp_mean=('frp', 'mean'),
        frp_max=('frp', 'max'),
        fire_days=('acq_date', 'nunique'),
        high_conf_count=('confidence', lambda x: (x >= 80).sum()),
        lat_centroid=('latitude', 'mean'),
        lon_centroid=('longitude', 'mean'),
    ).reset_index()
    
    # Round numeric columns
    for col in ['frp_total', 'frp_mean', 'frp_max', 'lat_centroid', 'lon_centroid']:
        if col in agg_df.columns:
            agg_df[col] = agg_df[col].round(2)
    
    print(f"  Aggregated to {len(agg_df):,} rows")
    
    return agg_df


def main():
    """Main entry point."""
    check_dependencies()
    import pandas as pd
    import geopandas as gpd
    
    parser = create_parser()
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"  {__module__} v{__version__}")
    print(f"  NASA FIRMS Active Fire Data Processor")
    print(f"{'='*60}\n")
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load data
    print("=== Loading Fire Data ===")
    df = load_fire_data(args.input_file)
    
    # Apply filters
    if args.min_confidence > 0:
        print(f"\n=== Filtering by Confidence ≥ {args.min_confidence} ===")
        before = len(df)
        df = df[df['confidence'] >= args.min_confidence]
        print(f"  Filtered: {before:,} → {len(df):,} detections")
    
    # Spatial join if aggregating
    polygons = None
    if args.aggregation_level != 'none':
        print(f"\n=== Spatial Aggregation: {args.aggregation_level} ===")
        df, polygons = spatial_join_to_polygons(df, args.aggregation_level)
    
    # Aggregate
    if args.aggregation_level != 'none' or args.temporal != 'none':
        print(f"\n=== Aggregating Data ===")
        result_df = aggregate_fires(df, args.aggregation_level, args.temporal)
    else:
        result_df = df
    
    # Generate output filename
    input_name = Path(args.input_file).stem
    suffix_parts = []
    if args.aggregation_level != 'none':
        suffix_parts.append(args.aggregation_level)
    if args.temporal != 'none':
        suffix_parts.append(args.temporal)
    suffix = '_' + '_'.join(suffix_parts) if suffix_parts else ''
    
    # Save output
    print(f"\n=== Saving Output ===")
    
    if args.with_geometry and args.aggregation_level != 'none' and polygons is not None:
        # Merge with polygon geometries
        result_gdf = polygons.merge(
            result_df, 
            left_on=('GEOID' if 'GEOID' in polygons.columns else 
                    'ZCTA5CE20' if 'ZCTA5CE20' in polygons.columns else polygons.columns[0]),
            right_on='polygon_id',
            how='inner'
        )
        
        output_file = os.path.join(args.output_dir, f"{input_name}{suffix}.gpkg")
        print(f"  Saving GeoPackage: {output_file}")
        result_gdf.to_file(output_file, driver="GPKG")
        print(f"  Saved {len(result_gdf):,} features")
    else:
        output_file = os.path.join(args.output_dir, f"{input_name}{suffix}.csv")
        print(f"  Saving CSV: {output_file}")
        result_df.to_csv(output_file, index=False)
        print(f"  Saved {len(result_df):,} rows")
    
    print(f"\n{'='*60}")
    print(f"  Processing Complete!")
    print(f"  Output: {output_file}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
