#!/usr/bin/env python3
"""
SVI Data Processing Script
=========================

This script processes Social Vulnerability Index (SVI) data.
It merges SVI datasets with Census Tract geometries to create spatial datasets (GeoPackage).

Features:
- Loads SVI CSV data
- Fetches Census Tract geometry using pygris for relevant states
- Merges SVI attributes with Tract geometries
- Exports as GeoPackage

Usage:
    python svi_process_generic.py --svi-data-dir ./data/svi --output-dir ./output --year 2020
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
    __version__ = get_module_version("svi")
except ImportError:
    __version__ = "1.0.0"

__module__ = "SVI Processing"

# ----------------- Mappings -----------------
FORMAT_2010_MAPPING = {
    "overall_score": "S_PL_THEMES",
    "overall_rank": "R_PL_THEMES", 
    "theme1_score": "S_PL_THEME1",
    "theme1_rank": "R_PL_THEME1",
    "theme2_score": "S_PL_THEME2", 
    "theme2_rank": "R_PL_THEME2",
    "theme3_score": "S_PL_THEME3",
    "theme3_rank": "R_PL_THEME3", 
    "theme4_score": "S_PL_THEME4",
    "theme4_rank": "R_PL_THEME4",
    "pov_pctl": "E_PL_POV",
    "unemp_pctl": "E_PL_UNEMP", 
    "pci_pctl": "E_PL_PCI",
    "nohsdip_pctl": "E_PL_NOHSDIP",
    "age65_pctl": "PL_AGE65",
    "age17_pctl": "PL_AGE17", 
    "sngprnt_pctl": "PL_SNGPRNT",
    "minority_pctl": "PL_MINORITY",
    "limeng_pctl": "E_PL_LIMENG",
    "munit_pctl": "E_PL_MUNIT",
    "mobile_pctl": "E_PL_MOBILE", 
    "crowd_pctl": "E_PL_CROWD",
    "noveh_pctl": "E_PL_NOVEH",
    "groupq_pctl": "PL_GROUPQ",
    "flag_theme1": "F_PL_THEME1",
    "flag_theme2": "F_PL_THEME2",
    "flag_theme3": "F_PL_THEME3", 
    "flag_theme4": "F_PL_THEME4",
    "flag_total": "F_PL_TOTAL",
    "totpop": "E_TOTPOP"
}

FORMAT_2014_MAPPING = {
    "overall_score": "SPL_THEMES",
    "overall_rank": "RPL_THEMES",
    "theme1_score": "SPL_THEME1", 
    "theme1_rank": "RPL_THEME1",
    "theme2_score": "SPL_THEME2",
    "theme2_rank": "RPL_THEME2", 
    "theme3_score": "SPL_THEME3",
    "theme3_rank": "RPL_THEME3",
    "theme4_score": "SPL_THEME4", 
    "theme4_rank": "RPL_THEME4",
    "pov_pctl": "EPL_POV",        
    "unemp_pctl": "EPL_UNEMP",
    "pci_pctl": "EPL_PCI",        
    "nohsdip_pctl": "EPL_NOHSDP", 
    "age65_pctl": "EPL_AGE65",
    "age17_pctl": "EPL_AGE17",
    "disabl_pctl": "EPL_DISABL",
    "sngprnt_pctl": "EPL_SNGPNT", 
    "minority_pctl": "EPL_MINRTY",
    "limeng_pctl": "EPL_LIMENG",
    "munit_pctl": "EPL_MUNIT",
    "mobile_pctl": "EPL_MOBILE",
    "crowd_pctl": "EPL_CROWD", 
    "noveh_pctl": "EPL_NOVEH",
    "groupq_pctl": "EPL_GROUPQ",
    "uninsur_pctl": "EPL_UNINSUR",
    "flag_theme1": "F_THEME1", 
    "flag_theme2": "F_THEME2",
    "flag_theme3": "F_THEME3",
    "flag_theme4": "F_THEME4",
    "flag_total": "F_TOTAL",
    "totpop": "E_TOTPOP"
}

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
        description=f'{__module__} Framework v{__version__} - Process SVI Data to Spatial Format',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--output-dir', required=True, help='Directory to save output GeoPackage files')
    parser.add_argument('--svi-data-dir', required=True, help='Directory containing SVI data files')
    parser.add_argument('--year', type=int, help='Specific year to process (optional). If not specified, attempts to find all available SVI years.')
    
    return parser

def load_svi_data(svi_dir: str, year: int):
    """Load and standardize SVI data for a given year."""
    import pandas as pd
    
    patterns = [
        f"SVI_{year}_US.csv",
        f"SVI{year}_US.csv",
        f"SVI{year}_US_CNTY.csv" 
    ]
    
    file_path = None
    for pattern in patterns:
        path = os.path.join(svi_dir, pattern)
        if os.path.exists(path):
            file_path = path
            break
            
    if not file_path:
        print(f"  Warning: No SVI file found for year {year} in {svi_dir}")
        return None

    print(f"  Loading SVI data from: {file_path}")
    
    try:
        df = pd.read_csv(file_path, dtype={'FIPS': str, 'GEO_ID': str, 'ST': str, 'ST_ABBR': str})
    except Exception as e:
        print(f"  Error reading file: {e}")
        return None

    std_df = pd.DataFrame()
    std_df['year'] = [year] * len(df)
    
    # Handle State Abbreviation for spatial fetching
    # 2010 usually has ST_ABBR or similar?
    state_col = None
    for c in ['ST_ABBR', 'STATE_ABBR', 'ST']:
        if c in df.columns:
            state_col = c
            break
            
    if state_col:
        std_df['state_abbr'] = df[state_col]
        # Clean state abbr if numerical (ST FIPS)
        # But generally SVI files have 'ST_ABBR' like 'AL', 'AK'
    else:
        # Fallback?
        pass

    # Handle GEOID
    if year == 2010:
        if 'GEO_ID' in df.columns:
            std_df['tract_geoid'] = df['GEO_ID'].str.replace('1400000US', '', regex=False)
        elif 'FIPS' in df.columns:
            std_df['tract_geoid'] = df['FIPS']
        else:
            print("  Error: Could not find GEOID/FIPS column for 2010 data")
            return None
    else:
        if 'FIPS' in df.columns:
            std_df['tract_geoid'] = df['FIPS']
        elif 'GEOID' in df.columns:
             std_df['tract_geoid'] = df['GEOID']
        else:
             print(f"  Error: Could not find FIPS/GEOID column for {year} data")
             return None

    # Standardize Variables
    mapping = FORMAT_2010_MAPPING if year == 2010 else FORMAT_2014_MAPPING
    
    for std_name, raw_name in mapping.items():
        if raw_name in df.columns:
            cleaned_col = pd.to_numeric(df[raw_name], errors='coerce')
            cleaned_col = cleaned_col.replace(-999, float('nan'))
            std_df[std_name] = cleaned_col
        else:
             # Don't fill with NA if not strictly necessary, but good for consistency
             pass
            
    # Handle year-specific deviations
    if year >= 2020:
        if 'EPL_POV150' in df.columns:
             std_df['pov_pctl'] = pd.to_numeric(df['EPL_POV150'], errors='coerce').replace(-999, float('nan'))
        if 'EPL_HBURD' in df.columns:
             std_df['hburd_pctl'] = pd.to_numeric(df['EPL_HBURD'], errors='coerce').replace(-999, float('nan'))

    return std_df

def fetch_tracts_for_svi(svi_df, year):
    """Fetch census tracts corresponding to states in SVI data."""
    import pygris
    import pandas as pd
    import geopandas as gpd
    
    if 'state_abbr' not in svi_df.columns:
        print("  Warning: generating tracts requires 'state_abbr' column in SVI data. Attempting to infer from GEOID is expensive.")
        return None
        
    unique_states = svi_df['state_abbr'].dropna().unique()
    print(f"  Fetching tracts for {len(unique_states)} states...")
    
    tracts_list = []
    for st in unique_states:
        # Skip numeric states if they appear by mistake
        if str(st).isdigit(): 
            continue
            
        try:
            # We use 2021 TIGER lines as a good proxy for modern tracts. 
            # For 2010 we might want 2010-era shapes.
            # pygris allows year argument.
            shape_year = year
            if year > 2022: shape_year = 2022
            if year < 2010: shape_year = 2010 
            
            # Note: pygris defaults might need adjustment for older years
            # For simplicity using recent shapes for recent SVI
            t = pygris.tracts(state=st, cb=True, year=shape_year)
            tracts_list.append(t)
        except Exception as e:
            print(f"    Warning: Failed to fetch tracts for {st} ({year}): {e}")
            
    if not tracts_list:
        return None
        
    all_tracts = pd.concat(tracts_list)
    return all_tracts

def main():
    check_dependencies()
    import pandas as pd
    import geopandas as gpd
    
    parser = create_parser()
    args = parser.parse_args()
    
    print(f"Running {__module__} v{__version__}")
        
    if not os.path.exists(args.svi_data_dir):
        print(f"Error: SVI Data Dir {args.svi_data_dir} not found")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    
    # Determine years to process
    if args.year:
        years = [args.year]
    else:
        # Default set of years or scandir?
        years = [2010, 2014, 2016, 2018, 2020, 2022] 
    
    for y in years:
        print(f"\n=== Processing Year {y} ===")
        svi_df = load_svi_data(args.svi_data_dir, y)
        if svi_df is None:
            continue
            
        # Fetch Geometry
        tracts_gdf = fetch_tracts_for_svi(svi_df, y)
        if tracts_gdf is None or tracts_gdf.empty:
            print(f"  Error: Could not fetch geometries for {y}. Skipping.")
            continue
            
        # Align GEOID columns
        # pygris returns GEOID. svi_df has tract_geoid.
        if 'GEOID' in tracts_gdf.columns:
            tracts_gdf['tract_geoid'] = tracts_gdf['GEOID']
            
        # Merge
        # Inner join to only keep tracts we have data for? Or left on geometry?
        # Typically we want spatial file for all tracts, with data attached
        print("  Merging SVI attributes to geometry...")
        
        # Ensure string matching
        tracts_gdf['tract_geoid'] = tracts_gdf['tract_geoid'].astype(str)
        svi_df['tract_geoid'] = svi_df['tract_geoid'].astype(str)
        
        merged_gdf = tracts_gdf.merge(svi_df, on='tract_geoid', how='inner')
        
        print(f"  Result: {len(merged_gdf)} tracts with data")
        
        # Save
        if not merged_gdf.empty:
            output_filename = f"SVI_{y}_Spatial.gpkg"
            output_path = os.path.join(args.output_dir, output_filename)
            print(f"  Saving to {output_path}...")
            merged_gdf.to_file(output_path, driver="GPKG")
            print("  Done.")

if __name__ == "__main__":
    main()
