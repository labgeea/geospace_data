#!/usr/bin/env python3
"""
EPA AQS Criteria Pollutants Processing Script
============================================

This script processes EPA AQS criteria air pollutant data from JSON to analysis-ready formats.
Designed to work with the GEOSPACE framework for air quality data processing.

Requirements:
- pandas, numpy, geopandas (optional)
- JSON files from aqs_download_generic.py

Author: GEOSPACE Project
Date: September 2025
License: Public Domain

Usage:
    python aqs_process_generic.py --input-file aqs_pm25_daily_2023.json --output-dir processed/
    python aqs_process_generic.py --input-dir raw/AQS/ --output-dir processed/ --variables all
"""

# Import version from framework
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_module_version

__version__ = get_module_version("aqs")
__module__ = "EPA AQS Processing"

import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
from typing import Dict, List, Optional, Tuple, Any

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Quality control parameters
QC_CONFIG = {
    'PM25': {
        'valid_range': [-10, 1000],  # μg/m³
        'extreme_range': [-50, 5000],
        'units': 'μg/m³'
    },
    'PM10': {
        'valid_range': [-10, 2000],  # μg/m³
        'extreme_range': [-50, 10000],
        'units': 'μg/m³'
    },
    'Ozone': {
        'valid_range': [-0.010, 0.500],  # ppm
        'extreme_range': [-0.050, 1.000],
        'units': 'ppm'
    },
    'NO2': {
        'valid_range': [-10, 1000],  # ppb
        'extreme_range': [-50, 5000],
        'units': 'ppb'
    },
    'SO2': {
        'valid_range': [-10, 2000],  # ppb
        'extreme_range': [-50, 10000],
        'units': 'ppb'
    },
    'CO': {
        'valid_range': [-1, 100],  # ppm
        'extreme_range': [-5, 500],
        'units': 'ppm'
    },
    'Pb': {
        'valid_range': [-0.01, 5.0],  # μg/m³
        'extreme_range': [-0.1, 50.0],
        'units': 'μg/m³'
    }
}

def setup_output_directory(output_dir):
    """Create output directory if it doesn't exist"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return output_dir

def identify_pollutant_from_filename(filename):
    """Identify pollutant type from filename"""
    filename_lower = str(filename).lower()
    
    if 'pm25' in filename_lower or 'pm2.5' in filename_lower:
        return 'PM25'
    elif 'pm10' in filename_lower:
        return 'PM10'
    elif 'ozone' in filename_lower or 'o3' in filename_lower:
        return 'Ozone'
    elif 'no2' in filename_lower:
        return 'NO2'
    elif 'so2' in filename_lower:
        return 'SO2'
    elif '_co_' in filename_lower:  # More specific pattern?...I am loosing 'co'
        return 'CO'
    elif 'pb' in filename_lower or 'lead' in filename_lower:
        return 'Pb'
    else:
        return 'Unknown'

def load_aqs_json(file_path):
    """Load AQS JSON data and convert to DataFrame"""
    print(f"  Loading: {Path(file_path).name}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # FIXED: Handle both 'Data' and 'Body' keys (EPA AQS API uses 'Data')
        if 'Data' not in data and 'Body' not in data:
            print(f"  ⚠ No data found in {file_path}")
            print(f"  Available keys: {list(data.keys())}")
            return None
        
        # EPA AQS API uses 'Data' key (newer format) or 'Body' key (older format)
        records = data.get('Data', data.get('Body', []))
        if not records:
            print(f"  ⚠ No data records found in {file_path}")
            return None
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Add metadata from header if available
        if 'Header' in data and data['Header']:
            header_info = data['Header'][0]
            df.attrs['request_time'] = header_info.get('request_time')
            df.attrs['api_url'] = header_info.get('url')
        
        print(f"  ✓ Loaded {len(df)} records")
        return df
        
    except Exception as e:
        print(f"  ✗ Error loading {file_path}: {e}")
        return None

def standardize_columns(df):
    """Standardize column names and data types"""
    # FIXED: Updated column mapping to handle EPA AQS API field names
    column_mapping = {
        'state_code': 'state_code',
        'county_code': 'county_code', 
        'site_number': 'site_number',
        'parameter_code': 'parameter_code',
        'parameter': 'parameter_name',  # EPA AQS uses 'parameter'
        'parameter_name': 'parameter_name',  # Also handle if it's 'parameter_name'
        'latitude': 'latitude',
        'longitude': 'longitude',
        'datum': 'datum',
        'date_local': 'date_local',
        'time_local': 'time_local',
        'sample_measurement': 'value',
        'arithmetic_mean': 'value',  # For daily/annual data
        'units_of_measure': 'units',
        'unit_of_measure': 'units',  # Handle both variations
        'detection_limit': 'detection_limit',
        'uncertainty': 'uncertainty',
        'qualifiers': 'qualifiers',
        'method_type': 'method_type',
        'method_code': 'method_code',
        'method': 'method_name',  # EPA AQS uses 'method'
        'state': 'state_name',  # EPA AQS uses 'state'
        'state_name': 'state_name',  # Also handle if it's 'state_name'
        'county': 'county_name',  # EPA AQS uses 'county'
        'county_name': 'county_name',  # Also handle if it's 'county_name'
        'date_of_last_change': 'date_of_last_change'
    }
    
    # Rename columns that exist
    existing_columns = {old: new for old, new in column_mapping.items() if old in df.columns}
    df = df.rename(columns=existing_columns)
    
    # Convert data types
    if 'latitude' in df.columns:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    if 'longitude' in df.columns:
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    if 'value' in df.columns:
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
    if 'date_local' in df.columns:
        df['date_local'] = pd.to_datetime(df['date_local'], errors='coerce')
    
    # Create site identifier
    if all(col in df.columns for col in ['state_code', 'county_code', 'site_number']):
        df['site_id'] = (df['state_code'].astype(str).str.zfill(2) + 
                        df['county_code'].astype(str).str.zfill(3) + 
                        df['site_number'].astype(str).str.zfill(4))
    
    return df

def apply_quality_control(df, pollutant):
    """Apply basic quality control filters"""
    print(f"  Applying QC for {pollutant}")
    
    initial_count = len(df)
    
    if pollutant not in QC_CONFIG:
        print(f"  ⚠ No QC config for {pollutant}, skipping QC")
        return df
    
    qc_config = QC_CONFIG[pollutant]
    
    # Filter by valid range
    if 'value' in df.columns:
        valid_mask = (
            (df['value'] >= qc_config['valid_range'][0]) & 
            (df['value'] <= qc_config['valid_range'][1])
        )
        df = df[valid_mask].copy()
        
        removed_count = initial_count - len(df)
        if removed_count > 0:
            print(f"  Removed {removed_count} records outside valid range "
                  f"({qc_config['valid_range']})")
    
    # Flag extreme values (but don't remove)
    if 'value' in df.columns:
        extreme_mask = (
            (df['value'] < qc_config['extreme_range'][0]) | 
            (df['value'] > qc_config['extreme_range'][1])
        )
        df.loc[extreme_mask, 'qc_flag'] = 'extreme_value'
    
    # Flag missing coordinates
    if 'latitude' in df.columns and 'longitude' in df.columns:
        missing_coords = df['latitude'].isna() | df['longitude'].isna()
        df.loc[missing_coords, 'qc_flag'] = 'missing_coordinates'
    
    # Flag missing values
    if 'value' in df.columns:
        missing_values = df['value'].isna()
        df.loc[missing_values, 'qc_flag'] = 'missing_value'
    
    print(f"  ✓ QC complete: {len(df)} records retained")
    return df

def generate_summary_stats(df, pollutant):
    """Generate summary statistics for the dataset"""
    summary = {
        'pollutant': pollutant,
        'total_records': len(df),
        'date_range': None,
        'spatial_extent': None,
        'value_stats': None,
        'site_count': None,
        'qc_flags': None
    }
    
    # Date range
    if 'date_local' in df.columns and not df['date_local'].isna().all():
        summary['date_range'] = {
            'start': df['date_local'].min().strftime('%Y-%m-%d'),
            'end': df['date_local'].max().strftime('%Y-%m-%d')
        }
    
    # Spatial extent
    if 'latitude' in df.columns and 'longitude' in df.columns:
        valid_coords = df.dropna(subset=['latitude', 'longitude'])
        if len(valid_coords) > 0:
            summary['spatial_extent'] = {
                'north': valid_coords['latitude'].max(),
                'south': valid_coords['latitude'].min(),
                'east': valid_coords['longitude'].max(),
                'west': valid_coords['longitude'].min()
            }
    
    # Value statistics
    if 'value' in df.columns:
        values = df['value'].dropna()
        if len(values) > 0:
            summary['value_stats'] = {
                'count': len(values),
                'mean': values.mean(),
                'median': values.median(),
                'std': values.std(),
                'min': values.min(),
                'max': values.max(),
                'percentile_25': values.quantile(0.25),
                'percentile_75': values.quantile(0.75),
                'percentile_95': values.quantile(0.95)
            }
    
    # Site count
    if 'site_id' in df.columns:
        summary['site_count'] = df['site_id'].nunique()
    
    # QC flags
    if 'qc_flag' in df.columns:
        summary['qc_flags'] = df['qc_flag'].value_counts().to_dict()
    
    return summary

def save_processed_data(df, pollutant, output_dir, output_formats=['csv']):
    """Save processed data in specified formats"""
    base_filename = f"aqs_{pollutant.lower()}_processed"
    saved_files = []
    
    # CSV format (always)
    if 'csv' in output_formats or True:  # Always save CSV
        csv_file = Path(output_dir) / f"{base_filename}.csv"
        df.to_csv(csv_file, index=False)
        saved_files.append(str(csv_file))
        print(f"  ✓ Saved CSV: {csv_file.name}")
    
    # GeoJSON format (if coordinates available)
    if 'geojson' in output_formats and all(col in df.columns for col in ['latitude', 'longitude']):
        try:
            import geopandas as gpd
            from shapely.geometry import Point
            
            # Remove records with missing coordinates
            geo_df = df.dropna(subset=['latitude', 'longitude']).copy()
            
            if len(geo_df) > 0:
                # Create geometry
                geometry = [Point(xy) for xy in zip(geo_df['longitude'], geo_df['latitude'])]
                gdf = gpd.GeoDataFrame(geo_df, geometry=geometry, crs='EPSG:4326')
                
                geojson_file = Path(output_dir) / f"{base_filename}.geojson"
                gdf.to_file(geojson_file, driver='GeoJSON')
                saved_files.append(str(geojson_file))
                print(f"  ✓ Saved GeoJSON: {geojson_file.name}")
            
        except ImportError:
            print("  ⚠ geopandas not available, skipping GeoJSON export")
        except Exception as e:
            print(f"  ⚠ Error saving GeoJSON: {e}")
    
    return saved_files

def process_aqs_file(input_file, output_dir, output_formats=['csv']):
    """Process a single AQS JSON file"""
    print(f"\nProcessing: {Path(input_file).name}")
    
    # Identify pollutant
    pollutant = identify_pollutant_from_filename(input_file)
    if pollutant == 'Unknown':
        print("  ⚠ Could not identify pollutant from filename")
        return None
    
    print(f"  Detected pollutant: {pollutant}")
    
    # Load data
    df = load_aqs_json(input_file)
    if df is None or len(df) == 0:
        return None
    
    # Standardize columns
    df = standardize_columns(df)
    
    # Apply quality control
    df = apply_quality_control(df, pollutant)
    
    if len(df) == 0:
        print("  ⚠ No data remaining after QC")
        return None
    
    # Generate summary
    summary = generate_summary_stats(df, pollutant)
    
    # Save processed data
    saved_files = save_processed_data(df, pollutant, output_dir, output_formats)
    
    # Save summary
    summary_file = Path(output_dir) / f"aqs_{pollutant.lower()}_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"  ✓ Processing complete: {len(df)} records, {len(saved_files)} output files")
    
    return {
        'pollutant': pollutant,
        'input_file': str(input_file),
        'output_files': saved_files,
        'record_count': len(df),
        'summary': summary
    }

def process_multiple_files(input_dir, output_dir, variables=None, output_formats=['csv']):
    """Process multiple AQS files in a directory"""
    setup_output_directory(output_dir)
    
    # Find JSON files
    input_path = Path(input_dir)
    json_files = list(input_path.glob("aqs_*.json"))
    
    if not json_files:
        print(f"No AQS JSON files found in {input_dir}")
        return {}
    
    print(f"Found {len(json_files)} AQS files to process")
    
    # Filter by variables if specified
    if variables and variables != ['all']:
        filtered_files = []
        for file in json_files:
            pollutant = identify_pollutant_from_filename(file)
            if pollutant in variables or pollutant.lower() in [v.lower() for v in variables]:
                filtered_files.append(file)
        json_files = filtered_files
        print(f"Filtered to {len(json_files)} files matching specified variables")
    
    results = {}
    total_records = 0
    
    # Process each file
    for file in json_files:
        try:
            result = process_aqs_file(file, output_dir, output_formats)
            if result:
                pollutant = result['pollutant']
                results[pollutant] = result
                total_records += result['record_count']
        except Exception as e:
            print(f"  ✗ Error processing {file.name}: {e}")
    
    # Generate overall summary
    overall_summary = {
        'processed_files': len(results),
        'total_records': total_records,
        'pollutants': list(results.keys()),
        'output_directory': str(output_dir),
        'processing_time': datetime.now().isoformat()
    }
    
    summary_file = Path(output_dir) / "aqs_processing_summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'overall': overall_summary,
            'by_pollutant': results
        }, f, indent=2, default=str)
    
    return results

def main():
    """Main function to process EPA AQS data"""
    parser = argparse.ArgumentParser(
        description=f'{__module__} v{__version__} - Process EPA AQS criteria pollutant data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Process single file
        %(prog)s --input-file aqs_pm25_daily_2023.json --output-dir processed/

        # Process all files in directory
        %(prog)s --input-dir raw/AQS/ --output-dir processed/

        # Process specific pollutants with multiple output formats
        %(prog)s --input-dir raw/AQS/ --output-dir processed/ --variables PM25,Ozone --output-formats csv,geojson

        Features:
        - Converts JSON to analysis-ready CSV format
        - Basic quality control filtering
        - Summary statistics generation
        - Optional GeoJSON output for spatial analysis
        - Site-level data aggregation
                """
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input-file', type=str, help='Single AQS JSON file to process')
    input_group.add_argument('--input-dir', type=str, help='Directory containing AQS JSON files')
    
    parser.add_argument('-o', '--output-dir', type=str, help='Output directory for processed files', 
                       required=True)
    parser.add_argument('--variables', type=str, help='Comma-separated list of pollutants to process')
    parser.add_argument('--output-formats', type=str, help='Output formats (csv,geojson)', 
                       default='csv')
    
    args = parser.parse_args()
    
    print("EPA AQS Criteria Pollutant Processing Script")
    print("=" * 60)
    
    # Parse arguments
    OUTPUT_DIR = args.output_dir
    OUTPUT_FORMATS = args.output_formats.split(',')
    VARIABLES = args.variables.split(',') if args.variables else ['all']
    
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Output formats: {', '.join(OUTPUT_FORMATS)}")
    if VARIABLES != ['all']:
        print(f"Processing variables: {', '.join(VARIABLES)}")
    
    # Process data
    if args.input_file:
        # Single file processing
        result = process_aqs_file(args.input_file, OUTPUT_DIR, OUTPUT_FORMATS)
        if result:
            print("\n✓ Processing completed successfully!")
            print(f"✓ Processed {result['record_count']} records")
            print(f"✓ Output files: {len(result['output_files'])}")
        else:
            print("\n✗ Processing failed")
            sys.exit(1)
    
    else:
        # Multiple file processing
        results = process_multiple_files(args.input_dir, OUTPUT_DIR, VARIABLES, OUTPUT_FORMATS)
        
        if results:
            total_records = sum(r['record_count'] for r in results.values())
            print("\n✓ Processing completed successfully!")
            print(f"✓ Processed {len(results)} pollutants")
            print(f"✓ Total records: {total_records}")
            print(f"✓ Output directory: {OUTPUT_DIR}")
        else:
            print("\n⚠ No files processed successfully")
            sys.exit(1)

if __name__ == "__main__":
    main()