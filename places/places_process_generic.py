#!/usr/bin/env python3
"""
PLACES Data Processing Script
==============================

This script processes CDC PLACES ZCTA data.
It transforms data from long format to wide format, merges with ZCTA geometries,
and exports as GeoPackage for spatial analysis.

Features:
- Pivots long-format PLACES data to wide format (one column per measure)
- Standardizes variable names to GEOSPACE conventions
- Includes confidence intervals (low/high) for each measure
- Fetches ZCTA geometry using pygris
- Merges PLACES attributes with ZCTA geometries
- Exports as GeoPackage

Usage:
    python places_process_generic.py --input-file ./data/places_zcta_2024.csv --output-dir ./output --year 2024
"""

import sys
import os
import argparse
import re
from pathlib import Path
import warnings

# Version information
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from version import get_module_version
    __version__ = get_module_version("places")
except ImportError:
    __version__ = "1.0.0"

__module__ = "PLACES Processing"

# Variable name mapping: CDC measure names -> standardized GEOSPACE names
# Format: { "CDC Measure Name": "geospace_variable_name" }
MEASURE_NAME_MAPPING = {
    # Health Outcomes
    "Arthritis among adults aged >=18 years": "arthritis_pct",
    "Current asthma among adults aged >=18 years": "asthma_current_pct",
    "High blood pressure among adults aged >=18 years": "high_bp_pct",
    "Cancer (excluding skin cancer) among adults aged >=18 years": "cancer_pct",
    "High cholesterol among adults aged >=18 years who have been screened in the past 5 years": "high_cholesterol_pct",
    "Chronic kidney disease among adults aged >=18 years": "kidney_disease_pct",
    "Chronic obstructive pulmonary disease among adults aged >=18 years": "copd_pct",
    "Coronary heart disease among adults aged >=18 years": "heart_disease_pct",
    "Depression among adults aged >=18 years": "depression_pct",
    "Diagnosed diabetes among adults aged >=18 years": "diabetes_pct",
    "Obesity among adults aged >=18 years": "obesity_pct",
    "Stroke among adults aged >=18 years": "stroke_pct",
    
    # Prevention
    "Visits to dentist or dental clinic among adults aged >=18 years": "dental_visit_pct",
    "Visits to doctor for routine checkup within the past year among adults aged >=18 years": "checkup_pct",
    "Cholesterol screening among adults aged >=18 years": "cholesterol_screening_pct",
    "Fecal occult blood test, sigmoidoscopy, or colonoscopy among adults aged 50-75 years": "colorectal_screening_pct",
    "Mammography use among women aged 50-74 years": "mammography_pct",
    "Cervical cancer screening among adult women aged 21-65 years": "cervical_screening_pct",
    "Taking medicine for high blood pressure control among adults aged >=18 years with high blood pressure": "bp_medication_pct",
    "Older adult men aged >=65 years who are up to date on a core set of clinical preventive services": "preventive_men65_pct",
    "Older adult women aged >=65 years who are up to date on a core set of clinical preventive services": "preventive_women65_pct",
    
    # Health Risk Behaviors
    "Binge drinking among adults aged >=18 years": "binge_drinking_pct",
    "Current smoking among adults aged >=18 years": "smoking_pct",
    "No leisure-time physical activity among adults aged >=18 years": "physical_inactivity_pct",
    "Sleeping less than 7 hours among adults aged >=18 years": "short_sleep_pct",
    
    # Disabilities
    "Cognitive disability among adults aged >=18 years": "disability_cognitive_pct",
    "Hearing disability among adults aged >=18 years": "disability_hearing_pct",
    "Mobility disability among adults aged >=18 years": "disability_mobility_pct",
    "Vision disability among adults aged >=18 years": "disability_vision_pct",
    "Self-care disability among adults aged >=18 years": "disability_selfcare_pct",
    "Independent living disability among adults aged >=18 years": "disability_independent_pct",
    "Any disability among adults aged >=18 years": "disability_any_pct",
    
    # Health Status
    "Fair or poor self-rated health status among adults aged >=18 years": "health_poor_pct",
    "Physical health not good for >=14 days among adults aged >=18 years": "physical_distress_pct",
    "Mental health not good for >=14 days among adults aged >=18 years": "mental_distress_pct",
    
    # Health-Related Social Needs
    "Food insecurity among adults aged >=18 years": "food_insecurity_pct",
    "Housing insecurity among adults aged >=18 years": "housing_insecurity_pct",
    "Transportation barriers among adults aged >=18 years": "transport_barrier_pct",
    "Utility service threat among adults aged >=18 years": "utility_insecurity_pct",
    "Lack of social and emotional support among adults aged >=18 years": "social_support_lack_pct",
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
    
    # Check for spatial file reading capability
    has_pyogrio = False
    has_fiona = False
    try:
        import pyogrio
        has_pyogrio = True
    except ImportError:
        pass
    try:
        import fiona
        has_fiona = True
    except ImportError:
        pass
    
    if not has_pyogrio and not has_fiona:
        missing.append("pyogrio (or fiona)")
    
    if missing:
        print(f"Error: Missing required packages: {', '.join(missing)}")
        print("Please install them using: mamba install " + " ".join(missing))
        sys.exit(1)


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Process CDC PLACES ZCTA Data to Spatial Format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process 2024 data
  python places_process_generic.py --input-file ./places_zcta_2024.csv --output-dir ./output --year 2024
  
  # Process without fetching geometry (tabular output only)
  python places_process_generic.py --input-file ./places_zcta_2024.csv --output-dir ./output --year 2024 --no-geometry
        """
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--input-file', required=True, help='Path to the downloaded PLACES CSV file')
    parser.add_argument('--output-dir', required=True, help='Directory to save output files')
    parser.add_argument('--year', type=int, required=True, help='Data release year (for output naming)')
    parser.add_argument('--no-geometry', action='store_true', 
                        help='Skip geometry merge (output CSV only, no GeoPackage)')
    parser.add_argument('--include-raw-names', action='store_true',
                        help='Also include original CDC measure names in output')
    
    return parser


def standardize_measure_name(measure: str) -> str:
    """
    Convert CDC measure name to standardized GEOSPACE variable name.
    Falls back to a generated name if not in mapping.
    
    Args:
        measure: Original CDC measure name
        
    Returns:
        Standardized variable name
    """
    # Check explicit mapping first
    if measure in MEASURE_NAME_MAPPING:
        return MEASURE_NAME_MAPPING[measure]
    
    # Generate a name if not in mapping
    # Convert to lowercase, replace spaces/special chars with underscores
    name = measure.lower()
    name = re.sub(r'[^a-z0-9]+', '_', name)
    name = re.sub(r'_+', '_', name)  # Replace multiple underscores
    name = name.strip('_')
    
    # Truncate if too long
    if len(name) > 50:
        name = name[:50].rsplit('_', 1)[0]
    
    return f"{name}_pct"


def pivot_places_data(df, include_ci: bool = True):
    """
    Pivot PLACES data from long format to wide format.
    
    Args:
        df: DataFrame in long format (one row per measure per ZCTA)
        include_ci: Include confidence interval columns
        
    Returns:
        DataFrame in wide format (one row per ZCTA)
    """
    import pandas as pd
    
    print("  Pivoting data to wide format...")
    
    # Identify key columns
    # PLACES typically has: Year, StateAbbr, StateDesc, LocationName (ZCTA), 
    # Category, Measure, Data_Value_Type, Data_Value, Low_Confidence_Limit, High_Confidence_Limit, TotalPopulation
    
    id_cols = ['Year', 'StateAbbr', 'StateDesc', 'LocationName', 'TotalPopulation']
    id_cols = [c for c in id_cols if c in df.columns]
    
    # Determine the actual column names (may vary by year)
    measure_col = 'Measure' if 'Measure' in df.columns else 'MeasureId'
    value_col = 'Data_Value' if 'Data_Value' in df.columns else 'data_value'
    low_ci_col = 'Low_Confidence_Limit' if 'Low_Confidence_Limit' in df.columns else 'low_confidence_limit'
    high_ci_col = 'High_Confidence_Limit' if 'High_Confidence_Limit' in df.columns else 'high_confidence_limit'
    
    # Get unique measures
    measures = df[measure_col].unique()
    print(f"  Found {len(measures)} unique measures")
    
    # Create standardized names mapping
    name_map = {m: standardize_measure_name(m) for m in measures}
    
    # Pivot for main values
    pivot_value = df.pivot_table(
        index=id_cols,
        columns=measure_col,
        values=value_col,
        aggfunc='first'
    ).reset_index()
    
    # Rename columns to standardized names
    rename_dict = {m: name_map[m] for m in measures if m in pivot_value.columns}
    pivot_value = pivot_value.rename(columns=rename_dict)
    
    if include_ci and low_ci_col in df.columns and high_ci_col in df.columns:
        # Pivot for low CI
        pivot_low = df.pivot_table(
            index=id_cols,
            columns=measure_col,
            values=low_ci_col,
            aggfunc='first'
        ).reset_index()
        
        # Pivot for high CI
        pivot_high = df.pivot_table(
            index=id_cols,
            columns=measure_col,
            values=high_ci_col,
            aggfunc='first'
        ).reset_index()
        
        # Rename CI columns
        low_rename = {m: f"{name_map[m]}_lo" for m in measures if m in pivot_low.columns}
        high_rename = {m: f"{name_map[m]}_hi" for m in measures if m in pivot_high.columns}
        
        pivot_low = pivot_low.rename(columns=low_rename)
        pivot_high = pivot_high.rename(columns=high_rename)
        
        # Merge CI columns with main values
        # Drop duplicate ID columns before merge
        ci_cols_low = [c for c in pivot_low.columns if c.endswith('_lo')]
        ci_cols_high = [c for c in pivot_high.columns if c.endswith('_hi')]
        
        pivot_value = pivot_value.merge(
            pivot_low[id_cols + ci_cols_low], 
            on=id_cols, 
            how='left'
        )
        pivot_value = pivot_value.merge(
            pivot_high[id_cols + ci_cols_high], 
            on=id_cols, 
            how='left'
        )
    
    print(f"  Pivoted to {len(pivot_value)} ZCTAs with {len(pivot_value.columns)} columns")
    
    return pivot_value


def fetch_zcta_geometry(states=None, year=2020):
    """
    Fetch ZCTA geometries using pygris.
    
    Args:
        states: Optional list of state abbreviations to filter
        year: Census year for ZCTA boundaries (default: 2020)
        
    Returns:
        GeoDataFrame with ZCTA polygons
    """
    import pygris
    import geopandas as gpd
    
    print(f"  Fetching {year} ZCTA geometries...")
    
    try:
        # pygris.zctas() fetches all ZCTAs nationally
        # We can filter by state afterwards if needed
        zctas = pygris.zctas(cb=True, year=year)
        print(f"  Fetched {len(zctas)} ZCTA polygons")
        
        return zctas
        
    except Exception as e:
        print(f"  Error fetching ZCTA geometry: {e}")
        return None


def main():
    """Main entry point."""
    check_dependencies()
    import pandas as pd
    import geopandas as gpd
    
    parser = create_parser()
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"  {__module__} v{__version__}")
    print(f"  CDC PLACES ZCTA Data Processor")
    print(f"{'='*60}\n")
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load data
    print("=== Loading PLACES Data ===")
    try:
        # Read CSV with LocationName (ZCTA) as string to preserve leading zeros
        df = pd.read_csv(args.input_file, dtype={'LocationName': str, 'locationname': str})
        
        # Normalize column names to title case for consistency
        df.columns = [c.title() if c.islower() else c for c in df.columns]
        
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    print(f"  Loaded {len(df)} rows")
    print(f"  Columns: {len(df.columns)}")
    
    # Show data summary
    if 'Category' in df.columns:
        categories = df['Category'].unique()
        print(f"  Categories: {', '.join(categories)}")
    
    if 'Measure' in df.columns:
        print(f"  Unique measures: {df['Measure'].nunique()}")
    
    # Pivot data to wide format
    print("\n=== Processing Data ===")
    wide_df = pivot_places_data(df, include_ci=True)
    
    # Save intermediate CSV (wide format)
    csv_output = os.path.join(args.output_dir, f"PLACES_{args.year}_ZCTA_wide.csv")
    wide_df.to_csv(csv_output, index=False)
    print(f"  Saved wide-format CSV: {csv_output}")
    
    if not args.no_geometry:
        print("\n=== Merging with Geometry ===")
        
        # Get states from data for potentially filtering geometry
        states = None
        if 'Stateabbr' in wide_df.columns:
            states = wide_df['Stateabbr'].unique().tolist()
        elif 'StateAbbr' in wide_df.columns:
            states = wide_df['StateAbbr'].unique().tolist()
        
        # Fetch ZCTA geometry
        zctas_gdf = fetch_zcta_geometry(states=states, year=2020)
        
        if zctas_gdf is not None and not zctas_gdf.empty:
            # Determine ZCTA ID column names
            # pygris typically uses 'ZCTA5CE20' or similar
            zcta_geom_col = None
            for col in ['ZCTA5CE20', 'ZCTA5CE10', 'GEOID20', 'GEOID']:
                if col in zctas_gdf.columns:
                    zcta_geom_col = col
                    break
            
            zcta_data_col = 'Locationname' if 'Locationname' in wide_df.columns else 'LocationName'
            
            if zcta_geom_col:
                print(f"  Joining on: {zcta_data_col} = {zcta_geom_col}")
                
                # Ensure both columns are strings
                zctas_gdf[zcta_geom_col] = zctas_gdf[zcta_geom_col].astype(str)
                wide_df[zcta_data_col] = wide_df[zcta_data_col].astype(str)
                
                # Merge
                merged_gdf = zctas_gdf.merge(
                    wide_df,
                    left_on=zcta_geom_col,
                    right_on=zcta_data_col,
                    how='inner'
                )
                
                print(f"  Merged: {len(merged_gdf)} ZCTAs with geometry")
                
                if not merged_gdf.empty:
                    # Save as GeoPackage
                    gpkg_output = os.path.join(args.output_dir, f"PLACES_{args.year}_ZCTA_Spatial.gpkg")
                    print(f"  Saving GeoPackage: {gpkg_output}")
                    merged_gdf.to_file(gpkg_output, driver="GPKG")
                    print("  Done!")
                else:
                    print("  Warning: No ZCTAs matched between data and geometry")
            else:
                print("  Warning: Could not identify ZCTA ID column in geometry data")
        else:
            print("  Warning: Could not fetch ZCTA geometry")
    
    print(f"\n{'='*60}")
    print("  Processing Complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
