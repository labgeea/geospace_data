#!/usr/bin/env python3
"""
Generic CAMS Air Pollution Processing Script
===========================================

This script processes CAMS air pollution variables from NetCDF files downloaded from the
Copernicus Atmosphere Data Store (ADS) and converts them to analysis-ready formats.

Features:
- Processes any CAMS air pollution variable
- Automatic unit conversions (kg/m³->μg/m³, etc.)
- Flexible temporal aggregation (hourly, daily, monthly)
- Multiple output formats (GeoTIFF, NetCDF)
- Coordinate system reprojection
- Memory-efficient processing with chunking
- Comprehensive validation and reporting

Requirements:
- xarray, rioxarray, numpy, rasterio, pandas, psutil

Author: GEOSPACE Project
Date: 2025
License: Public Domain

Usage:
    python cams_process_generic.py --input-file cams_pm25_202001.nc --output-dir processed/ --variables pm25
    python cams_process_generic.py --input-file cams_data.nc --output-dir processed/ --variables all --aggregation daily
"""

# Version information
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from version import get_module_version, VERSION_INFO
    __version__ = get_module_version("cams")
    __author__ = VERSION_INFO["author"]
    __license__ = VERSION_INFO["license"]
except ImportError:
    __version__ = "1.2.0"
    __author__ = "GEOSPACE Project"
    __license__ = "Public Domain"

__module__ = "CAMS Processing"

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

# CAMS Variable processing configuration
VARIABLE_CONFIG = {
    # Particulate Matter
    'pm25': {
        'name': 'pm2p5',  # NetCDF variable name in CAMS files
        'unit_conversion': 'kg_m3_to_ug_m3',
        'output_unit': 'μg/m³',
        'long_name': 'PM2.5 mass concentration',
        'standard_name': 'mass_concentration_of_pm2p5_ambient_aerosol_particles_in_air',
        'valid_range': (0, 500),  # μg/m³
        'nodata_value': -9999.0,
        'dtype': 'float32'
    },
    'pm10': {
        'name': 'pm10',  # NetCDF variable name in CAMS files
        'unit_conversion': 'kg_m3_to_ug_m3',
        'output_unit': 'μg/m³',
        'long_name': 'PM10 mass concentration',
        'standard_name': 'mass_concentration_of_pm10_ambient_aerosol_particles_in_air',
        'valid_range': (0, 1000),  # μg/m³
        'nodata_value': -9999.0,
        'dtype': 'float32'
    },

    # Trace Gases
    'no2': {
        'name': 'no2',   # NetCDF variable name in CAMS files
        'unit_conversion': 'kg_m3_to_ug_m3',
        'output_unit': 'μg/m³',
        'long_name': 'Nitrogen dioxide concentration',
        'standard_name': 'mass_concentration_of_nitrogen_dioxide_in_air',
        'valid_range': (0, 200),  # μg/m³
        'nodata_value': -9999.0,
        'dtype': 'float32'
    },
    'so2': {
        'name': 'so2',   # NetCDF variable name in CAMS files
        'unit_conversion': 'kg_m3_to_ug_m3',
        'output_unit': 'μg/m³',
        'long_name': 'Sulfur dioxide concentration',
        'standard_name': 'mass_concentration_of_sulfur_dioxide_in_air',
        'valid_range': (0, 100),  # μg/m³
        'nodata_value': -9999.0,
        'dtype': 'float32'
    },
    'co': {
        'name': 'co',    # NetCDF variable name in CAMS files
        'unit_conversion': 'kg_m3_to_mg_m3',
        'output_unit': 'mg/m³',
        'long_name': 'Carbon monoxide concentration',
        'standard_name': 'mass_concentration_of_carbon_monoxide_in_air',
        'valid_range': (0, 50),   # mg/m³
        'nodata_value': -9999.0,
        'dtype': 'float32'
    },
    'o3': {
        'name': 'go3',   # NetCDF variable name in CAMS files (ground-level ozone)
        'unit_conversion': 'kg_m3_to_ug_m3',
        'output_unit': 'μg/m³',
        'long_name': 'Ground-level ozone concentration',
        'standard_name': 'mass_concentration_of_ozone_in_air',
        'valid_range': (0, 300),  # μg/m³
        'nodata_value': -9999.0,
        'dtype': 'float32'
    }
}

# Unit conversion functions
def kg_m3_to_ug_m3(data):
    """Convert kg/m³ to μg/m³"""
    return data * 1e9

def kg_m3_to_mg_m3(data):
    """Convert kg/m³ to mg/m³"""
    return data * 1e6

def no_conversion(data):
    """No unit conversion"""
    return data

# Mapping of conversion function names to actual functions
CONVERSION_FUNCTIONS = {
    'kg_m3_to_ug_m3': kg_m3_to_ug_m3,
    'kg_m3_to_mg_m3': kg_m3_to_mg_m3,
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

    # Find time dimension (CAMS uses 'valid_time')
    time_dims = ['valid_time', 'time']
    time_dim = None
    for dim in time_dims:
        if dim in ds.dims:
            time_dim = dim
            break

    # Find spatial dimensions
    lat_dims = ['latitude', 'lat', 'y']
    lon_dims = ['longitude', 'lon', 'x']

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
    # Direct match with canonical key
    if var_name in VARIABLE_CONFIG:
        print(f"    Direct match with canonical key: {var_name}")
        return VARIABLE_CONFIG[var_name], var_name

    # Check if var_name matches the 'name' field (NetCDF name) in any config
    for canonical_key, config_data in VARIABLE_CONFIG.items():
        if config_data.get('name') == var_name:
            print(f"    NetCDF name match: {var_name} -> {canonical_key}")
            return config_data, canonical_key

    # Partial matches
    for config_key, config_value in VARIABLE_CONFIG.items():
        if var_name.lower() in config_key.lower() or config_key.lower() in var_name.lower():
            print(f"    Partial key match: {var_name} -> {config_key}")
            return config_value, config_key

    # Default configuration for unknown variables
    print(f"    Using default config for unknown variable: {var_name}")
    default_config = {
        'unit_conversion': 'none',
        'output_unit': 'unknown',
        'long_name': var_name,
        'standard_name': var_name,
        'valid_range': (None, None),
        'nodata_value': -9999.0,
        'dtype': 'float32'
    }
    return default_config, var_name

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
        aggregation: 'hourly', 'daily', 'monthly'
        method: 'mean', 'max', 'min'

    Returns:
        xarray DataArray: Aggregated data
    """
    if aggregation == 'hourly':
        return data  # No aggregation needed

    # Use xarray's resample for proper temporal aggregation
    if aggregation == 'daily':
        resampler = data.resample({time_dim: 'D'})
    elif aggregation == 'monthly':
        resampler = data.resample({time_dim: 'M'})
    else:
        raise ValueError(f"Unknown aggregation: {aggregation}")

    # Apply aggregation method (typically mean for air quality)
    if method == 'mean':
        result = resampler.mean(skipna=True)
    elif method == 'max':
        result = resampler.max(skipna=True)
    elif method == 'min':
        result = resampler.min(skipna=True)
    else:
        raise ValueError(f"Unknown aggregation method: {method}")

    return result

def process_variable(ds, var_name, var_info, config, mapped_name, aggregation='daily', target_crs='EPSG:5070'):
    """
    Process a single CAMS air pollution variable.

    Args:
        ds: xarray Dataset
        var_name: Variable name in NetCDF
        var_info: Variable information from identification
        config: Variable configuration
        mapped_name: Mapped variable name for output
        aggregation: Temporal aggregation
        target_crs: Target coordinate reference system

    Returns:
        xarray DataArray: Processed variable data
    """
    print(f"  Processing variable: {var_name} -> {mapped_name}")

    # # Extract variable data
    var_data = ds[var_name]
    # print(f"    DEBUG: Variable extracted successfully")
    # print(f"    Original data dimensions: {var_data.dims}")
    # print(f"    Original data shape: {var_data.shape}")
    
    # # Handle extra dimensions (like model_level for CO) BEFORE any other processing
    # print(f"    Expected time_dim: {var_info['time_dim']}")
    # print(f"    Expected lat_dim: {var_info['lat_dim']}")
    # print(f"    Expected lon_dim: {var_info['lon_dim']}")
    
    extra_dims = []
    expected_dims = [var_info['time_dim'], var_info['lat_dim'], var_info['lon_dim']]
    print(f"    Expected dimensions: {expected_dims}")
    
    for dim in var_data.dims:
        if dim not in expected_dims:
            extra_dims.append(dim)
    
    print(f"    Found extra dimensions: {extra_dims}")
    
    # If there are extra dimensions, select the first element (typically model_level=0)
    if extra_dims:
        # print(f"    Processing {len(extra_dims)} extra dimensions...")
        for extra_dim in extra_dims:
            print(f"    Handling extra dimension '{extra_dim}': selecting index 0")
            var_data = var_data.isel({extra_dim: 0})
        # print(f"    Data shape after removing extra dimensions: {var_data.shape}")
        # print(f"    Data dimensions after removing extra dimensions: {var_data.dims}")
    else:
        print("    No extra dimensions found, proceeding with original data")

    print("    About to apply unit conversion...")
    # Apply unit conversion
    print(f"    Converting units: {config['unit_conversion']} -> {config['output_unit']}")
    var_data = apply_unit_conversion(var_data, config['unit_conversion'])

    # Set spatial dimensions for rioxarray
    if var_info['lat_dim'] and var_info['lon_dim']:
        var_data = var_data.rio.set_spatial_dims(x_dim=var_info['lon_dim'], y_dim=var_info['lat_dim'])
        var_data = var_data.rio.write_crs('EPSG:4326')

    # Temporal aggregation
    if var_info['time_dim'] and aggregation != 'hourly':
        print(f"    Applying temporal aggregation: {aggregation}")
        # Air quality typically uses mean aggregation
        var_data = aggregate_temporal(var_data, var_info['time_dim'], aggregation, 'mean')

    # Validate data range
    validate_data_range(var_data, config['valid_range'], mapped_name)

    # Update attributes
    var_data.attrs.update({
        'long_name': config['long_name'],
        'standard_name': config['standard_name'],
        'units': config['output_unit'],
        'processing': f'{aggregation} mean from hourly CAMS data',
        'source': 'CAMS reanalysis/forecast',
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

def print_processing_summary(processed_vars, output_dir, input_file):
    """Print simple processing summary to stdout"""
    total_files = 0
    total_size = 0
    
    print(f"\n{'='*60}")
    print("CAMS Processing Summary")
    print(f"{'='*60}")
    print(f"Input file: {input_file}")
    print(f"Output directory: {output_dir}")
    print(f"Variables processed: {len(processed_vars)}")
    
    for var_name, file_paths in processed_vars.items():
        print(f"\n{var_name.upper()}:")
        for file_path in file_paths:
            if os.path.exists(file_path):
                file_size_mb = os.path.getsize(file_path) / (1024**2)
                filename = os.path.basename(file_path)
                print(f"  {filename} ({file_size_mb:.1f} MB)")
                total_files += 1
                total_size += file_size_mb
    
    print(f"\nTotal output files: {total_files}")
    print(f"Total output size: {total_size:.1f} MB")
    print(f"{'='*60}")

def save_as_geotiff(data, output_path, var_name, config, create_stacks=False):
    """Save processed data as GeoTIFF files"""
    print(f"    Saving as GeoTIFF: {output_path}")

    # Handle time dimension if present
    time_dim = None
    for dim in ['valid_time', 'time']:
        if dim in data.dims:
            time_dim = dim
            break
    
    if time_dim and not create_stacks:
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
        # Single time step, already aggregated, or creating stacks
        data.rio.to_raster(
            output_path,
            compress='lzw',
            tiled=True,
            blockxsize=512,
            blockysize=512,
            dtype=config['dtype'],
            nodata=config['nodata_value']
        )

def save_as_netcdf(data, output_path, var_name, config, create_stacks=False):
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
    ds_out.to_netcdf(output_path, encoding=encoding)

def create_processing_report(processed_vars, output_dir, input_file, processing_config):
    """Create detailed processing report with air quality focus"""
    report_path = os.path.join(output_dir, "processing_report.json")

    report = {
        'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'input_file': input_file,
        'output_directory': output_dir,
        'processing_config': processing_config,
        'data_source': 'CAMS (Copernicus Atmosphere Monitoring Service)',
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

    # Human-readable version
    txt_report_path = os.path.join(output_dir, "processing_report.txt")
    with open(txt_report_path, 'w') as f:
        f.write("CAMS Air Pollution Processing Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Processing Date: {report['processing_date']}\n")
        f.write(f"Data Source: {report['data_source']}\n")
        f.write(f"Input File: {report['input_file']}\n")
        f.write(f"Output Directory: {report['output_directory']}\n")
        f.write(f"Total Variables Processed: {report['summary']['total_variables']}\n")
        f.write(f"Total Output Files: {report['summary']['total_output_files']}\n")
        f.write(f"Total Output Size: {report['summary']['total_output_size_mb']:.2f} MB\n\n")

        f.write("Processing Configuration:\n")
        for key, value in processing_config.items():
            f.write(f"  {key}: {value}\n")
        f.write("\n")

        f.write("Processed Air Pollution Variables:\n")
        for var_name, var_info in report['processed_variables'].items():
            f.write(f"\n{var_name.upper()}:\n")
            f.write(f"  Type: {var_info['pollutant_type']}\n")
            f.write(f"  WHO Guideline: {var_info['who_guideline']}\n")
            f.write(f"  Total Size: {var_info['total_size_mb']:.2f} MB\n")
            f.write(f"  Output Files ({len(var_info['output_files'])}):\n")
            for file_info in var_info['output_files']:
                filename = os.path.basename(file_info['path'])
                f.write(f"    {filename} ({file_info['size_mb']:.2f} MB)\n")

    print("✓ Processing reports saved:")
    print(f"  JSON: {report_path}")
    print(f"  Text: {txt_report_path}")

def process_cams_variables(input_file, output_dir="./data/processed/CAMS/",
                          variables=None, aggregation='daily', output_format='geotiff',
                          target_crs="EPSG:5070", chunk_size=None, create_stacks=False):
    """
    Main processing function for CAMS air pollution variables.

    Args:
        input_file: Path to input NetCDF file
        output_dir: Output directory
        variables: List of variables to process ('all' for all variables)
        aggregation: Temporal aggregation ('hourly', 'daily', 'monthly')
        output_format: Output format ('geotiff', 'netcdf', 'both')
        target_crs: Target coordinate reference system
        chunk_size: Chunk size for memory management

    Returns:
        dict: Processed variables and their output files
    """
    print("Processing CAMS air pollution variables")
    print(f"Input file: {input_file}")
    print(f"Output directory: {output_dir}")
    print(f"Target CRS: {target_crs}")
    print(f"Aggregation: {aggregation}")
    print(f"Output format: {output_format}")
    print("-" * 60)

    setup_output_directory(output_dir)

    try:
        print("Loading CAMS NetCDF data...")
        print_memory_usage()

        # Open dataset with optimal chunking
        if chunk_size:
            print(f"Using custom chunking: {chunk_size}")
            ds = xr.open_dataset(input_file, chunks=chunk_size)
        else:
            ds = xr.open_dataset(input_file)
            # Auto-chunk for CAMS data (typically valid_time dimension)
            time_coords = [coord for coord in ds.coords if 'time' in coord.lower()]
            if time_coords:
                ds = ds.chunk({time_coords[0]: 24})

        print("✓ CAMS dataset opened successfully")
        print_memory_usage()

        # Identify variables and dimensions
        variables_info = identify_variables_and_dimensions(ds)
        print(f"✓ Found {len(variables_info)} data variables: {list(variables_info.keys())}")

        # Determine which variables to process
        vars_to_process_map = []
        dataset_actual_var_names = list(variables_info.keys())

        if variables is None or variables == ['all']:
            for actual_ds_var_name in dataset_actual_var_names:
                resolved_config, canonical_key = get_variable_config(actual_ds_var_name)
                vars_to_process_map.append((canonical_key, actual_ds_var_name))
        else:
            for user_var_request in variables:
                resolved_config, canonical_key = get_variable_config(user_var_request)
                expected_netcdf_name = resolved_config.get('name')

                actual_ds_var_name_to_use = None
                if expected_netcdf_name and expected_netcdf_name in dataset_actual_var_names:
                    actual_ds_var_name_to_use = expected_netcdf_name
                elif canonical_key in dataset_actual_var_names:
                    actual_ds_var_name_to_use = canonical_key
                elif user_var_request in dataset_actual_var_names:
                    actual_ds_var_name_to_use = user_var_request

                if actual_ds_var_name_to_use:
                    vars_to_process_map.append((canonical_key, actual_ds_var_name_to_use))
                else:
                    print(f"Warning: Variable '{user_var_request}' not found in dataset")

        if not vars_to_process_map:
            raise ValueError("No valid variables to process")

        # Remove duplicates
        vars_to_process_map = list(set(vars_to_process_map))
        print(f"✓ Processing {len(vars_to_process_map)} variables: {[x[0] for x in vars_to_process_map]}")

        processed_variables = {}

        # Process each variable
        for i, (canonical_key, actual_ds_var_name) in enumerate(vars_to_process_map):
            start_time = time.time()
            print(f"\nProcessing air pollution variable {i+1}/{len(vars_to_process_map)}: '{canonical_key}' (NetCDF: '{actual_ds_var_name}')")

            try:
                var_info = variables_info[actual_ds_var_name]
                config, short_key = get_variable_config(canonical_key)

                print(f"  Configuration: {config['unit_conversion']} -> {config['output_unit']}")

                # Process the variable
                processed_data = process_variable(
                    ds, actual_ds_var_name, var_info, config, short_key, 
                    aggregation=aggregation, target_crs=target_crs
                )

                # Generate output file paths
                output_files = []
                if create_stacks:
                    base_filename = f"cams_{short_key}_{aggregation}_stack"
                else:
                    base_filename = f"cams_{short_key}_{aggregation}"

                # Save in requested format(s)
                if output_format in ['geotiff', 'both']:
                    tiff_path = os.path.join(output_dir, f"{base_filename}.tif")
                    save_as_geotiff(processed_data, tiff_path, short_key, config, create_stacks)
                    output_files.append(tiff_path)

                if output_format in ['netcdf', 'both']:
                    nc_path = os.path.join(output_dir, f"{base_filename}.nc")
                    save_as_netcdf(processed_data, nc_path, short_key, config, create_stacks)
                    output_files.append(nc_path)

                processed_variables[short_key] = output_files

                # Print statistics
                if hasattr(processed_data, 'values'):
                    valid_pixels = (~np.isnan(processed_data.values)).sum()
                    total_pixels = processed_data.size
                    data_min = np.nanmin(processed_data.values)
                    data_max = np.nanmax(processed_data.values)
                    data_mean = np.nanmean(processed_data.values)

                    processing_time = time.time() - start_time
                    print(f"  ✓ Valid pixels: {valid_pixels:,}/{total_pixels:,} ({100*valid_pixels/total_pixels:.1f}%)")
                    print(f"  ✓ Concentration range: {data_min:.3f} to {data_max:.3f} {config['output_unit']} (mean: {data_mean:.3f})")
                    print(f"  ✓ Processing time: {processing_time:.1f}s")

                # Memory cleanup
                del processed_data
                if (i + 1) % 3 == 0:  # Clean up every 3 variables
                    gc.collect()
                    print_memory_usage()

            except Exception as e:
                print(f"  ✗ Error processing {actual_ds_var_name}: {e}")
                import traceback
                traceback.print_exc()
                continue

        ds.close()
        gc.collect()

        print("\n✓ CAMS processing completed successfully!")
        print(f"✓ Processed {len(processed_variables)} air pollution variables")
        print(f"✓ Output directory: {output_dir}")

        # Print processing summary
        print_processing_summary(processed_variables, output_dir, input_file)

        return processed_variables

    except Exception as e:
        print(f"✗ CAMS processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Process CAMS air pollution data to analysis-ready formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Process all variables with daily aggregation
        %(prog)s --input-file cams_pm25_202001.nc --output-dir processed/ --variables all

        # Process specific air pollution variables
        %(prog)s --input-file cams_data.nc --output-dir processed/ --variables pm25,no2,o3

        # Process with monthly aggregation and NetCDF output
        %(prog)s --input-file cams_data.nc --output-dir processed/ --variables pm25 --aggregation monthly --output-format netcdf

        # Process with custom CRS for regional analysis
        %(prog)s --input-file cams_data.nc --output-dir processed/ --variables all --target-crs EPSG:4326

        Supported Air Pollution Variables:
        Particulates: pm25, pm10
        Trace Gases: no2, so2, co, o3
                """
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')

    parser.add_argument('--input-file', '-i', required=True, help='Input CAMS NetCDF file path')
    parser.add_argument('--output-dir', '-o', required=True, help='Directory to save processed files')
    parser.add_argument('--variables', '-v', default='all', help='Comma-separated list of variables to process, or "all" (default: all)')
    parser.add_argument('--aggregation', '-a', choices=['hourly', 'daily', 'monthly'], default='daily', help='Temporal aggregation (default: daily)')
    parser.add_argument('--output-format', '-f', choices=['geotiff', 'netcdf', 'both'], default='geotiff', help='Output format (default: geotiff)')
    parser.add_argument('--target-crs', '-c', default='EPSG:5070', help='Target CRS for reprojection (default: EPSG:5070)')
    parser.add_argument('--chunk-size', type=int, help='Chunk size for memory management (optional)')
    parser.add_argument('--create-stacks', action='store_true', help='Create time-series raster stacks instead of individual files')
    parser.add_argument('--list-config', action='store_true', help='List variable configurations and exit')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')

    args = parser.parse_args()

    # Handle list config request
    if args.list_config:
        print("CAMS Air Pollution Variable Configurations:")
        print("=" * 60)
        for var_name, config in VARIABLE_CONFIG.items():
            print(f"\n{var_name.upper()}:")
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

    # Parse variables
    if args.variables.lower() == 'all':
        variables = None
    else:
        variables = [v.strip() for v in args.variables.split(',') if v.strip()]

    chunk_config = None
    if args.chunk_size:
        chunk_config = {'valid_time': args.chunk_size}

    print("CAMS Air Pollution Variable Processor")
    print("=" * 45)
    print(f"Input file: {args.input_file}")
    print(f"Output directory: {args.output_dir}")
    print(f"Variables: {args.variables}")
    print(f"Aggregation: {args.aggregation}")
    print(f"Output format: {args.output_format}")
    print(f"Target CRS: {args.target_crs}")
    if args.create_stacks:
        print("Create stacks: Yes")
    if chunk_config:
        print(f"Chunk size: {args.chunk_size}")
    print()

    try:
        result = process_cams_variables(
            input_file=args.input_file,
            output_dir=args.output_dir,
            variables=variables,
            aggregation=args.aggregation,
            output_format=args.output_format,
            target_crs=args.target_crs,
            chunk_size=chunk_config,
            create_stacks=args.create_stacks
        )

        if result is None:
            sys.exit(1)

        print(f"\n✓ Successfully processed {len(result)} air pollution variables")
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