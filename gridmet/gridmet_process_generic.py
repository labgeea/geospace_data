#!/usr/bin/env python3
"""
Generic GridMET Variable Processing Script
=========================================

This script processes any GridMET variable from NetCDF files downloaded from the
University of Idaho's THREDDS server and converts them to analysis-ready formats.

Features:
- Processes any GridMET variable
- Automatic unit conversions (K->°C, etc.)
- Flexible temporal aggregation (daily, monthly)
- Multiple output formats (GeoTIFF, NetCDF)
- Coordinate system reprojection
- Memory-efficient processing with chunking
- Comprehensive validation and reporting

Requirements:
- xarray, rioxarray, numpy, rasterio, pandas, psutil

Author: GEOSPACE Project
Date: July2025
License: Public Domain

Usage:
    python gridmet_process_generic.py --input-file gridmet_data.nc --output-dir processed/ --variables pr
    python gridmet_process_generic.py --input-file gridmet_data.nc --output-dir processed/ --variables all --aggregation monthly
"""
# Version information (same as above)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_module_version

__version__ = get_module_version("gridmet")
__module__ = "GridMET Processing"

import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import calendar
import argparse
import re
import gc
import psutil
import time
import warnings
from typing import Dict, List, Optional, Tuple, Any
import json

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# GridMET Variable processing configuration
GRIDMET_VARIABLE_CONFIG = {
    # Primary Climate Variables
    'pr': {
        'name': 'precipitation_amount', # Actual variable name in GridMET NetCDF files
        'unit_conversion': 'none',
        'output_unit': 'mm',
        'long_name': 'daily precipitation amount',
        'standard_name': 'precipitation_amount',
        'valid_range': (0, 1000),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'sum'
    },
    'tmmx': {
        'unit_conversion': 'kelvin_to_celsius',
        'output_unit': 'degrees_Celsius',
        'long_name': 'daily maximum temperature',
        'standard_name': 'air_temperature',
        'valid_range': (-50, 60),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },
    'tmmn': {
        'unit_conversion': 'kelvin_to_celsius',
        'output_unit': 'degrees_Celsius',
        'long_name': 'daily minimum temperature',
        'standard_name': 'air_temperature',
        'valid_range': (-50, 60),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },
    'rmax': {
        'unit_conversion': 'none',
        'output_unit': '%',
        'long_name': 'daily maximum relative humidity',
        'standard_name': 'relative_humidity',
        'valid_range': (0, 100),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },
    'rmin': {
        'unit_conversion': 'none',
        'output_unit': '%',
        'long_name': 'daily minimum relative humidity',
        'standard_name': 'relative_humidity',
        'valid_range': (0, 100),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },
    'sph': {
        'unit_conversion': 'kg_per_kg_to_g_per_kg',
        'output_unit': 'g/kg',
        'long_name': 'daily mean specific humidity',
        'standard_name': 'specific_humidity',
        'valid_range': (0, 30),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },
    'srad': {
        'unit_conversion': 'none',
        'output_unit': 'W/m2',
        'long_name': 'daily mean downward shortwave radiation',
        'standard_name': 'surface_downwelling_shortwave_flux_in_air',
        'valid_range': (0, 500),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },
    'vs': {
        'unit_conversion': 'none',
        'output_unit': 'm/s',
        'long_name': 'daily mean wind speed',
        'standard_name': 'wind_speed',
        'valid_range': (0, 50),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },
    'th': {
        'unit_conversion': 'none',
        'output_unit': 'degrees',
        'long_name': 'daily mean wind direction',
        'standard_name': 'wind_from_direction',
        'valid_range': (0, 360),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },

    # Fire Weather Variables
    'bi': {
        'unit_conversion': 'none',
        'output_unit': 'dimensionless',
        'long_name': 'daily burning index',
        'standard_name': 'burning_index',
        'valid_range': (0, 200),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },
    'fm100': {
        'unit_conversion': 'none',
        'output_unit': '%',
        'long_name': '100-hour dead fuel moisture',
        'standard_name': 'dead_fuel_moisture_100hr',
        'valid_range': (0, 50),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },
    'fm1000': {
        'unit_conversion': 'none',
        'output_unit': '%',
        'long_name': '1000-hour dead fuel moisture',
        'standard_name': 'dead_fuel_moisture_1000hr',
        'valid_range': (0, 50),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },
    'erc': {
        'unit_conversion': 'none',
        'output_unit': 'dimensionless',
        'long_name': 'daily energy release component',
        'standard_name': 'energy_release_component',
        'valid_range': (0, 200),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },

    # Evapotranspiration Variables
    'etr': {
        'unit_conversion': 'none',
        'output_unit': 'mm',
        'long_name': 'daily reference evapotranspiration (alfalfa)',
        'standard_name': 'potential_evapotranspiration',
        'valid_range': (0, 20),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'sum'
    },
    'eto': {
        'unit_conversion': 'none',
        'output_unit': 'mm',
        'long_name': 'daily reference evapotranspiration (grass)',
        'standard_name': 'potential_evapotranspiration',
        'valid_range': (0, 15),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'sum'
    },
    'vpd': {
        'unit_conversion': 'pa_to_kpa',
        'output_unit': 'kPa',
        'long_name': 'daily mean vapor pressure deficit',
        'standard_name': 'vapor_pressure_deficit',
        'valid_range': (0, 8),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    },

    # Drought Indices
    'pdsi': {
        'unit_conversion': 'none',
        'output_unit': 'dimensionless',
        'long_name': 'Palmer Drought Severity Index',
        'standard_name': 'palmer_drought_severity_index',
        'valid_range': (-10, 10),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    }
}

# Unit conversion functions
def kelvin_to_celsius(data):
    """Convert temperature from Kelvin to Celsius"""
    return data - 273.15

def pa_to_kpa(data):
    """Convert pressure from Pascals to kiloPascals"""
    return data / 1000.0

def kg_per_kg_to_g_per_kg(data):
    """Convert kg/kg to g/kg"""
    return data * 1000.0

def no_conversion(data):
    """No unit conversion"""
    return data

# Mapping of conversion function names to actual functions
CONVERSION_FUNCTIONS = {
    'kelvin_to_celsius': kelvin_to_celsius,
    'pa_to_kpa': pa_to_kpa,
    'kg_per_kg_to_g_per_kg': kg_per_kg_to_g_per_kg,
    'none': no_conversion
}

def setup_output_directory(output_dir):
    """Create output directory if it doesn't exist"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return output_dir

def print_memory_usage():
    """Print current memory usage"""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    print(f"  Memory usage: {mem_info.rss / 1024**2:.1f} MB RSS, {mem_info.vms / 1024**2:.1f} MB VMS")

def identify_variables_and_dimensions(ds):
    """
    Identify available variables and their dimensions in the dataset.

    Returns:
        dict: Mapping of variable names to their information
    """
    variables_info = {}

    # Find time dimension
    time_dims = ['day', 'time']
    time_dim = None
    for dim in time_dims:
        if dim in ds.dims:
            time_dim = dim
            break

    # Find spatial dimensions
    lat_dims = ['lat', 'latitude', 'y']
    lon_dims = ['lon', 'longitude', 'x']

    lat_dim = None
    lon_dim = None

    for dim in lat_dims:
        if dim in ds.dims:
            lat_dim = dim
            break

    for dim in lon_dims:
        if dim in ds.dims:
            lon_dim = dim
            break

    # Identify data variables
    for var_name in ds.data_vars:
        var_data = ds[var_name]
        variables_info[var_name] = {
            'dims': var_data.dims,
            'shape': var_data.shape,
            'dtype': var_data.dtype,
            'attrs': dict(var_data.attrs),
            'time_dim': time_dim,
            'lat_dim': lat_dim,
            'lon_dim': lon_dim
        }

    return variables_info

def get_variable_config(var_name):
    """
    Get processing configuration for a variable.

    Args:
        var_name (str): Variable name

    Returns:
        tuple: (config_dict, mapped_name) - Configuration and the mapped variable name
    """
    # Attempt 1: Direct match with a canonical short key
    if var_name in GRIDMET_VARIABLE_CONFIG:
        print(f"    Direct match with canonical key: {var_name}")
        return GRIDMET_VARIABLE_CONFIG[var_name], var_name

    # Attempt 2: Check if var_name is an alias for a canonical short key
    for short_key, config_data in GRIDMET_VARIABLE_CONFIG.items():
        if var_name.lower() in [alias.lower() for alias in config_data.get('aliases', [])]:
            print(f"    Alias match: {var_name} -> {short_key}")
            return config_data, short_key

    # Attempt 3: Check if var_name matches the 'name' field (NetCDF name) in any config
    for short_key, config_data in GRIDMET_VARIABLE_CONFIG.items():
        if config_data.get('name') == var_name:
            print(f"    NetCDF name match: {var_name} -> {short_key}")
            return config_data, short_key

    # Attempt 4: (Less precise) Try to match by partial name for common abbreviations if no exact match found yet
    # This is kept from previous logic but should be hit less often now.
    for config_name_key, config_data_val in GRIDMET_VARIABLE_CONFIG.items():
        # Check against the key itself (e.g., 'tmmx')
        if var_name.lower() in config_name_key.lower() or config_name_key.lower() in var_name.lower():
            print(f"    Partial key match: {var_name} -> {config_name_key}")
            return config_data_val, config_name_key
        # Check against the 'name' field in the config (e.g., 'air_temperature')
        if 'name' in config_data_val and (var_name.lower() in config_data_val['name'].lower() or config_data_val['name'].lower() in var_name.lower()):
            print(f"    Partial name field match: {var_name} -> {config_name_key} (via {config_data_val['name']})")
            return config_data_val, config_name_key


    # Default configuration for unknown variables
    print(f"    Using default config for unknown variable: {var_name}")
    default_config = {
        'unit_conversion': 'none',
        'output_unit': 'unknown',
        'long_name': var_name,
        'standard_name': var_name,
        'valid_range': (None, None),
        'nodata_value': -9999.0,
        'dtype': 'float32',
        'aggregation_method': 'mean'
    }
    return default_config, var_name # var_name itself is used as the key here

def apply_unit_conversion(data, conversion_type):
    """Apply unit conversion to data"""
    if conversion_type in CONVERSION_FUNCTIONS:
        return CONVERSION_FUNCTIONS[conversion_type](data)
    else:
        print(f"Warning: Unknown conversion type '{conversion_type}', no conversion applied")
        return data

def validate_data_range(data, valid_range, var_name):
    """Validate data is within expected range"""
    if valid_range[0] is None or valid_range[1] is None:
        return True

    min_val = np.nanmin(data.values)
    max_val = np.nanmax(data.values)

    if min_val < valid_range[0] or max_val > valid_range[1]:
        print(f"Warning: {var_name} values ({min_val:.2f} to {max_val:.2f}) outside expected range {valid_range}")
        return False

    return True

def aggregate_temporal(data, time_dim, aggregation='daily', method='mean'):
    """
    Aggregate data temporally.

    Args:
        data: xarray DataArray
        time_dim: Time dimension name
        aggregation: 'daily', 'monthly'
        method: 'mean', 'sum', 'min', 'max'

    Returns:
        xarray DataArray: Aggregated data
    """
    if aggregation == 'daily':
        return data  # No aggregation needed for daily data

    # Use xarray's resample for proper temporal aggregation
    if aggregation == 'monthly':
        # Resample to monthly frequency
        resampler = data.resample({time_dim: 'M'})
    else:
        raise ValueError(f"Unknown aggregation: {aggregation}")

    # Apply aggregation method
    if method == 'mean':
        result = resampler.mean(skipna=True)
    elif method == 'sum':
        result = resampler.sum(skipna=True)
    elif method == 'min':
        result = resampler.min(skipna=True)
    elif method == 'max':
        result = resampler.max(skipna=True)
    else:
        raise ValueError(f"Unknown aggregation method: {method}")

    return result

def process_variable(ds, var_name, var_info, config, mapped_name, aggregation='daily', target_crs='EPSG:5070'):
    """
    Process a single variable.

    Args:
        ds: xarray Dataset
        var_name: Variable name
        var_info: Variable information from identification
        config: Variable configuration
        mapped_name: Mapped variable name for configuration
        aggregation: Temporal aggregation
        target_crs: Target coordinate reference system

    Returns:
        xarray DataArray: Processed variable data
    """
    print(f"  Processing variable: {var_name} -> {mapped_name}")

    # Extract variable data
    var_data = ds[var_name]

    # Apply unit conversion
    print(f"    Applying unit conversion: {config['unit_conversion']} -> {config['output_unit']}")
    var_data = apply_unit_conversion(var_data, config['unit_conversion'])

    # Set spatial dimensions for rioxarray
    if var_info['lat_dim'] and var_info['lon_dim']:
        var_data = var_data.rio.set_spatial_dims(x_dim=var_info['lon_dim'], y_dim=var_info['lat_dim'])
        var_data = var_data.rio.write_crs('EPSG:4326')

    # Temporal aggregation
    if var_info['time_dim'] and aggregation == 'monthly':
        print(f"    Applying temporal aggregation: {aggregation}")

        # Use the configured aggregation method for the variable
        method = config.get('aggregation_method', 'mean')
        var_data = aggregate_temporal(var_data, var_info['time_dim'], aggregation, method)

    # Validate data range
    validate_data_range(var_data, config['valid_range'], var_name)

    # Update attributes
    var_data.attrs.update({
        'long_name': config['long_name'],
        'standard_name': config['standard_name'],
        'units': config['output_unit'],
        'processing': f'{aggregation} data from GridMET',
        'source': 'GridMET - University of Idaho',
        'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'original_crs': 'EPSG:4326',
        'target_crs': target_crs,
        'nodata_value': config['nodata_value']
    })

    # Reproject if target CRS is different
    if target_crs != 'EPSG:4326' and var_info['lat_dim'] and var_info['lon_dim']:
        print(f"    Reprojecting to {target_crs}")
        var_data = var_data.rio.reproject(
            target_crs,
            resampling=1,  # Bilinear
            nodata=config['nodata_value']
        )

    # Convert to specified dtype
    var_data = var_data.astype(config['dtype'])

    return var_data

def save_as_geotiff(data, output_path, var_name, config):
    """Save processed data as GeoTIFF files"""
    print(f"    Saving as GeoTIFF: {output_path}")

    # Handle time dimension if present
    if 'day' in data.dims or 'time' in data.dims:
        time_dim = 'day' if 'day' in data.dims else 'time'
        # Save each time step as separate file
        time_values = data[time_dim].values
        for i, time_val in enumerate(time_values):
            time_data = data.isel({time_dim: i})
            date_str = pd.to_datetime(time_val).strftime('%Y%m%d')
            time_output_path = output_path.replace('.tif', f'_{date_str}.tif')

            time_data.rio.to_raster(
                time_output_path,
                compress='lzw',
                tiled=True,
                blockxsize=512,
                blockysize=512,
                dtype=config['dtype'],
                nodata=config['nodata_value']
            )
    else:
        # Single time step or already aggregated
        data.rio.to_raster(
            output_path,
            compress='lzw',
            tiled=True,
            blockxsize=512,
            blockysize=512,
            dtype=config['dtype'],
            nodata=config['nodata_value']
        )

def save_as_netcdf(data, output_path, var_name, config):
    """Save processed data as NetCDF file"""
    print(f"    Saving as NetCDF: {output_path}")

    # Clean attributes that conflict with encoding
    data_clean = data.copy()
    if '_FillValue' in data_clean.attrs:
        del data_clean.attrs['_FillValue']
    if 'missing_value' in data_clean.attrs:
        del data_clean.attrs['missing_value']

    # Create dataset with proper encoding
    encoding = {
        var_name: {
            'dtype': config['dtype'],
            'zlib': True,
            'complevel': 4,
            '_FillValue': config['nodata_value']
        }
    }

    # Convert to dataset
    ds_out = data_clean.to_dataset(name=var_name)

    # Save to NetCDF
    ds_out.to_netcdf(output_path, encoding=encoding)

def create_processing_report(processed_vars, output_dir, input_file, processing_config):
    """Create detailed processing report"""
    report_path = os.path.join(output_dir, "processing_report.json")

    report = {
        'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'input_file': input_file,
        'output_directory': output_dir,
        'processing_config': processing_config,
        'processed_variables': {},
        'summary': {
            'total_variables': len(processed_vars),
            'total_output_files': 0,
            'total_output_size_mb': 0
        }
    }

    total_size = 0
    total_files = 0

    for var_name, file_paths in processed_vars.items():
        var_info = {
            'variable_name': var_name,
            'output_files': [],
            'total_size_mb': 0
        }

        for file_path in file_paths:
            if os.path.exists(file_path):
                file_size_mb = os.path.getsize(file_path) / (1024**2)
                var_info['output_files'].append({
                    'path': file_path,
                    'size_mb': round(file_size_mb, 2)
                })
                var_info['total_size_mb'] += file_size_mb
                total_size += file_size_mb
                total_files += 1

        var_info['total_size_mb'] = round(var_info['total_size_mb'], 2)
        report['processed_variables'][var_name] = var_info

    report['summary']['total_output_files'] = total_files
    report['summary']['total_output_size_mb'] = round(total_size, 2)

    # Save report
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Also create human-readable version
    txt_report_path = os.path.join(output_dir, "processing_report.txt")
    with open(txt_report_path, 'w') as f:
        f.write("GridMET Generic Variable Processing Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Processing Date: {report['processing_date']}\n")
        f.write(f"Input File: {report['input_file']}\n")
        f.write(f"Output Directory: {report['output_directory']}\n")
        f.write(f"Total Variables Processed: {report['summary']['total_variables']}\n")
        f.write(f"Total Output Files: {report['summary']['total_output_files']}\n")
        f.write(f"Total Output Size: {report['summary']['total_output_size_mb']:.2f} MB\n\n")

        f.write("Processing Configuration:\n")
        for key, value in processing_config.items():
            f.write(f"  {key}: {value}\n")
        f.write("\n")

        f.write("Processed Variables:\n")
        for var_name, var_info in report['processed_variables'].items():
            f.write(f"\n{var_name}:\n")
            f.write(f"  Total Size: {var_info['total_size_mb']:.2f} MB\n")
            f.write(f"  Output Files ({len(var_info['output_files'])}):\n")
            for file_info in var_info['output_files']:
                filename = os.path.basename(file_info['path'])
                f.write(f"    {filename} ({file_info['size_mb']:.2f} MB)\n")

    print(f"✓ Processing reports saved:")
    print(f"  JSON: {report_path}")
    print(f"  Text: {txt_report_path}")

def process_gridmet_variables(input_file, output_dir="./data/processed/GridMET/",
                              variables=None, aggregation='daily', output_format='geotiff',
                              target_crs="EPSG:5070", chunk_size=None):
    """
    Main processing function for GridMET variables.

    Args:
        input_file: Path to input NetCDF file
        output_dir: Output directory
        variables: List of variables to process ('all' for all variables)
        aggregation: Temporal aggregation ('daily', 'monthly')
        output_format: Output format ('geotiff', 'netcdf', 'both')
        target_crs: Target coordinate reference system
        chunk_size: Chunk size for memory management

    Returns:
        dict: Processed variables and their output files
    """
    print(f"Processing GridMET variables")
    print(f"Input file: {input_file}")
    print(f"Output directory: {output_dir}")
    print(f"Target CRS: {target_crs}")
    print(f"Aggregation: {aggregation}")
    print(f"Output format: {output_format}")
    print("-" * 60)

    setup_output_directory(output_dir)

    try:
        print("Loading NetCDF data...")
        print_memory_usage()

        # Open dataset with optimal chunking
        if chunk_size:
            print(f"Using custom chunking: {chunk_size}")
            ds = xr.open_dataset(input_file, chunks=chunk_size)
        else:
            ds = xr.open_dataset(input_file)
            # Auto-chunk for better performance
            time_coords = [coord for coord in ds.coords if 'time' in coord.lower() or 'day' in coord.lower()]
            if time_coords:
                ds = ds.chunk({time_coords[0]: 30})  # Process one month at a time

        print("✓ Dataset opened successfully")
        print_memory_usage()

        # Identify variables and dimensions
        variables_info = identify_variables_and_dimensions(ds)
        print(f"✓ Found {len(variables_info)} data variables")

        # Determine which variables to process
        vars_to_process_map = []  # List of (user_key_for_config, actual_ds_var_name)
        dataset_actual_var_names = list(variables_info.keys())

        if variables is None or variables == ['all']:
            # User wants all variables from the file
            for actual_ds_var_name in dataset_actual_var_names:
                # Try to map the actual_ds_var_name back to a short_key from config
                # get_variable_config will return (config, short_key_if_mapped_else_actual_name)
                _, short_key_for_this_ds_var = get_variable_config(actual_ds_var_name)
                vars_to_process_map.append((short_key_for_this_ds_var, actual_ds_var_name))
        else:
            # User specified a list of variables (e.g., ['pr', 'tmmx'])
            for user_var_request in variables: # user_var_request could be 'pr' or 'precipitation_amount' or an alias
                # First, get the canonical short key and its config for this user request
                # This handles if user_var_request is an alias, a short key, or a long NetCDF name.
                resolved_config, canonical_short_key = get_variable_config(user_var_request)

                actual_ds_var_name_to_use = None
                # Determine the actual variable name to look for in the dataset
                # Prefer the 'name' field from config if available (this is the typical NetCDF name)
                expected_netcdf_name_from_config = resolved_config.get('name')

                if expected_netcdf_name_from_config and expected_netcdf_name_from_config in dataset_actual_var_names:
                    actual_ds_var_name_to_use = expected_netcdf_name_from_config
                elif canonical_short_key in dataset_actual_var_names: # Fallback: maybe short key is the actual NetCDF var name
                    actual_ds_var_name_to_use = canonical_short_key
                elif user_var_request in dataset_actual_var_names: # Fallback: user provided the exact NetCDF name not in our short_keys
                    actual_ds_var_name_to_use = user_var_request
                    # In this case, canonical_short_key might be user_var_request if get_variable_config defaulted

                if actual_ds_var_name_to_use:
                    # Ensure we use the canonical_short_key for config/output naming consistency
                    if not any(item[0] == canonical_short_key and item[1] == actual_ds_var_name_to_use for item in vars_to_process_map):
                        vars_to_process_map.append((canonical_short_key, actual_ds_var_name_to_use))
                else:
                    print(f"Warning: Variable '{user_var_request}' (resolved to canonical key '{canonical_short_key}') could not be matched to any variable in the dataset: {dataset_actual_var_names}")

        if not vars_to_process_map:
            raise ValueError("No valid variables to process after mapping.")

        # Remove duplicates that might arise if user specifies 'pr' and 'precipitation_amount'
        # and both map to ('pr', 'precipitation_amount')
        unique_vars_to_process_map = []
        seen_keys = set()
        for item_tuple in vars_to_process_map:
            if item_tuple not in seen_keys:
                unique_vars_to_process_map.append(item_tuple)
                seen_keys.add(item_tuple)
        vars_to_process_map = unique_vars_to_process_map

        print(f"✓ Processing {len(vars_to_process_map)} mapped variables (user_key, netcdf_name): {vars_to_process_map}")

        processed_variables = {}

        # Process each variable
        for i, (user_key_for_config, actual_ds_var_name) in enumerate(vars_to_process_map):
            start_time = time.time()
            print(f"\nProcessing variable {i+1}/{len(vars_to_process_map)}: '{user_key_for_config}' (from NetCDF variable '{actual_ds_var_name}')")

            try:
                var_info = variables_info[actual_ds_var_name]
                # config and mapped_name (short_key) are based on user_key_for_config
                config, short_key_for_output = get_variable_config(user_key_for_config)

                print(f"  Configuration for '{short_key_for_output}': {config['unit_conversion']} -> {config['output_unit']}")

                # Process the variable using actual_ds_var_name from NetCDF
                # but use short_key_for_output for metadata matching in process_variable if it relies on it.
                processed_data = process_variable(
                    ds, actual_ds_var_name, var_info, config, short_key_for_output, aggregation, target_crs
                )

                # Generate output file paths
                output_files = []

                # Determine base filename using the canonical short key (short_key_for_output)
                if aggregation == 'daily':
                    base_filename = f"gridmet_{short_key_for_output}_daily"
                elif aggregation == 'monthly':
                    base_filename = f"gridmet_{short_key_for_output}_monthly"
                else: # Should not happen with current GridMET aggregation options
                    base_filename = f"gridmet_{short_key_for_output}"

                # Save in requested format(s)
                if output_format in ['geotiff', 'both']:
                    tiff_path = os.path.join(output_dir, f"{base_filename}.tif")
                    save_as_geotiff(processed_data, tiff_path, short_key_for_output, config)
                    output_files.append(tiff_path)

                if output_format in ['netcdf', 'both']:
                    nc_path = os.path.join(output_dir, f"{base_filename}.nc")
                    save_as_netcdf(processed_data, nc_path, short_key_for_output, config)
                    output_files.append(nc_path)

                processed_variables[short_key_for_output] = output_files

                # Print statistics
                if hasattr(processed_data, 'values'):
                    valid_pixels = (~np.isnan(processed_data.values)).sum()
                    total_pixels = processed_data.size
                    data_min = np.nanmin(processed_data.values)
                    data_max = np.nanmax(processed_data.values)
                    data_mean = np.nanmean(processed_data.values)

                    processing_time = time.time() - start_time
                    print(f"  ✓ Valid pixels: {valid_pixels:,}/{total_pixels:,} ({100*valid_pixels/total_pixels:.1f}%)")
                    print(f"  ✓ Data range for '{actual_ds_var_name}': {data_min:.3f} to {data_max:.3f} {config['output_unit']} (mean: {data_mean:.3f})")
                    print(f"  ✓ Processing time: {processing_time:.1f}s")

                # Memory cleanup
                del processed_data
                if (i + 1) % 5 == 0:  # Clean up every 5 variables
                    gc.collect()
                    print_memory_usage()

            except Exception as e:
                print(f"  ✗ Error processing {actual_ds_var_name}: {e}")
                import traceback
                traceback.print_exc()
                continue

        ds.close()
        gc.collect()

        print(f"\n✓ Processing completed successfully!")
        print(f"✓ Processed {len(processed_variables)} variables")
        print(f"✓ Output directory: {output_dir}")

        # Create processing report
        processing_config = {
            'aggregation': aggregation,
            'output_format': output_format,
            'target_crs': target_crs,
            'variables_processed': list(processed_variables.keys())
        }

        create_processing_report(processed_variables, output_dir, input_file, processing_config)

        return processed_variables

    except Exception as e:
        print(f"✗ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
    description=f'{__module__} Framework v{__version__} - Process GridMET data to analysis-ready formats',
    formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Process all variables with daily aggregation (default)
        %(prog)s --input-file gridmet_data.nc --output-dir processed/ --variables all

        # Process specific variables
        %(prog)s --input-file gridmet_data.nc --output-dir processed/ --variables pr,tmmx

        # Process with monthly aggregation and NetCDF output
        %(prog)s --input-file gridmet_data.nc --output-dir processed/ --variables pr --aggregation monthly --output-format netcdf

        # Process with custom CRS
        %(prog)s --input-file gridmet_data.nc --output-dir processed/ --variables all --target-crs EPSG:4326

        Supported Variables:
        Climate: pr, tmmx, tmmn, rmax, rmin, sph, srad, vs, th
        Fire Weather: bi, fm100, fm1000, erc
        Evapotranspiration: etr, eto, vpd
        Drought: pdsi
                """
    )

    # Add version argument
    parser.add_argument(
        '--version',
        action='version',
        version=f'{__module__} v{__version__}'
    )
    
    parser.add_argument(
        '--input-file', '-i',
        required=True,
        help='Input NetCDF file path'
    )

    parser.add_argument(
        '--output-dir', '-o',
        required=True,
        help='Directory to save processed files'
    )

    parser.add_argument(
        '--variables', '-v',
        default='all',
        help='Comma-separated list of variables to process, or "all" for all variables (default: all)'
    )

    parser.add_argument(
        '--aggregation', '-a',
        choices=['daily', 'monthly'],
        default='daily',
        help='Temporal aggregation (default: daily)'
    )

    parser.add_argument(
        '--output-format', '-f',
        choices=['geotiff', 'netcdf', 'both'],
        default='geotiff',
        help='Output format (default: geotiff)'
    )

    parser.add_argument(
        '--target-crs', '-c',
        default='EPSG:5070',
        help='Target CRS for reprojection (default: EPSG:5070)'
    )

    parser.add_argument(
        '--chunk-size',
        type=int,
        help='Chunk size for memory management (optional)'
    )

    parser.add_argument(
        '--list-config',
        action='store_true',
        help='List variable configurations and exit'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )

    args = parser.parse_args()

    # Handle list config request
    if args.list_config:
        print("GridMET Variable Processing Configurations:")
        print("=" * 50)
        for var_name, config in GRIDMET_VARIABLE_CONFIG.items():
            print(f"\n{var_name}:")
            for key, value in config.items():
                print(f"  {key}: {value}")
        sys.exit(0)

    # Validate inputs
    if not os.path.exists(args.input_file):
        print(f"✗ Input file does not exist: {args.input_file}")
        sys.exit(1)

    if not re.match(r'^EPSG:\d+$', args.target_crs):
        print(f"✗ Invalid CRS format: {args.target_crs}")
        sys.exit(1)

    # Check required libraries
    required_packages = ['xarray', 'rioxarray', 'numpy', 'rasterio', 'pandas', 'psutil']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"✗ Missing required packages: {', '.join(missing_packages)}")
        print(f"Install with: pip install {' '.join(missing_packages)}")
        sys.exit(1)

    # Parse variables
    if args.variables.lower() == 'all':
        variables = None  # Will process all variables found
    else:
        variables = [v.strip() for v in args.variables.split(',') if v.strip()]

    # Set chunk size if provided
    chunk_config = None
    if args.chunk_size:
        chunk_config = {'day': args.chunk_size}

    print("GridMET Generic Variable Processor")
    print("=" * 40)
    print(f"Input file: {args.input_file}")
    print(f"Output directory: {args.output_dir}")
    print(f"Variables: {args.variables}")
    print(f"Aggregation: {args.aggregation}")
    print(f"Output format: {args.output_format}")
    print(f"Target CRS: {args.target_crs}")
    if chunk_config:
        print(f"Chunk size: {args.chunk_size}")
    print()

    try:
        result = process_gridmet_variables(
            input_file=args.input_file,
            output_dir=args.output_dir,
            variables=variables,
            aggregation=args.aggregation,
            output_format=args.output_format,
            target_crs=args.target_crs,
            chunk_size=chunk_config
        )

        if result is None:
            sys.exit(1)

        print(f"\n✓ Successfully processed {len(result)} variables")
        print(f"✓ Output files saved to: {args.output_dir}")

    except KeyboardInterrupt:
        print("\n✗ Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
