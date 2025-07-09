#!/usr/bin/env python3
"""
Generic MODIS Variable Processing Script
=======================================

This script provides a generic framework for processing any MODIS variable
downloaded using the modis_download_generic.sh script. It serves as a template
and example for creating specific processing workflows.

Features:
- Configurable for any MODIS product and variable
- Extracts Science Datasets (SDS) from HDF files
- Applies scale factors and quality masks
- Mosaics tiles for spatial coverage
- Reprojects to target coordinate systems
- Resamples to target resolutions
- Supports temporal aggregation
- Exports to standard formats (GeoTIFF, NetCDF)

Supported Products (examples):
- MOD11A1/MYD11A1: Land Surface Temperature
- MOD13A1/MYD13A1: Vegetation Indices (NDVI, EVI)
- MOD13A3/MYD13A3: Monthly Vegetation Indices
- MOD44B: Vegetation Continuous Fields
- MOD09A1/MYD09A1: Surface Reflectance
- MOD15A2H/MYD15A2H: Leaf Area Index

Requirements:
- xarray, rioxarray, numpy, rasterio, pandas, psutil
- GDAL command-line tools

Author: GEOSPACE Project
Date: 2025
License: Public Domain

Usage:
    python modis_process_generic.py --config config.json \
                                   --input-dir /data/raw/MODIS/ \
                                   --output-dir /data/processed/MODIS/ \
                                   --year 2020 --month 1
"""

# Version information
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_module_version

__version__ = get_module_version("modis")
__module__ = "MODIS Processing"


import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
import os
import sys
from datetime import datetime, timedelta
import calendar
import argparse
import re
import gc
import psutil
import time
import warnings
from typing import Dict, List, Optional, Tuple, Any, Union
import json
import glob
import rioxarray
from rasterio.enums import Resampling
import yaml

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=xr.SerializationWarning)

# --- Default Configuration ---
DEFAULT_CONFIG = {
    "product_configs": {
        # Land Surface Temperature
        "MOD11A1": {
            "grid_name": "MODIS_Grid_Daily_1km_LST",
            "variables": {
                "LST_Day": {
                    "sds_name": "LST_Day_1km",
                    "scale_factor": 0.02,
                    "add_offset": 0.0,
                    "valid_range": (7500, 65535),
                    "fill_value": 0,
                    "units": "Kelvin",
                    "convert_to_celsius": True,
                    "qc_sds": "QC_Day"
                },
                "LST_Night": {
                    "sds_name": "LST_Night_1km",
                    "scale_factor": 0.02,
                    "add_offset": 0.0,
                    "valid_range": (7500, 65535),
                    "fill_value": 0,
                    "units": "Kelvin",
                    "convert_to_celsius": True,
                    "qc_sds": "QC_Night"
                }
            },
            "temporal_resolution": "daily",
            "spatial_resolution": 1000
        },

        # Vegetation Indices - 16-day 500m
        "MOD13A1": {
            "grid_name": "MOD_Grid_16DAY_500m_VI",
            "variables": {
                "NDVI": {
                    "sds_name": "500m 16 days NDVI",
                    "scale_factor": 0.0001,
                    "valid_range": (-2000, 10000),
                    "fill_value": -3000,
                    "units": "dimensionless",
                    "qc_sds": "500m 16 days VI Quality"
                },
                "EVI": {
                    "sds_name": "500m 16 days EVI",
                    "scale_factor": 0.0001,
                    "valid_range": (-2000, 10000),
                    "fill_value": -3000,
                    "units": "dimensionless",
                    "qc_sds": "500m 16 days VI Quality"
                }
            },
            "temporal_resolution": "16-day",
            "spatial_resolution": 500
        },

        # Vegetation Indices - 16-day 1km
        "MOD13A2": {
            "grid_name": "MODIS_Grid_16DAY_1km_VI",
            "variables": {
                "NDVI": {
                    "sds_name": "1 km 16 days NDVI",
                    "scale_factor": 0.0001,
                    "valid_range": (-2000, 10000),
                    "fill_value": -3000,
                    "units": "dimensionless",
                    "qc_sds": "1 km 16 days VI Quality"
                },
                "EVI": {
                    "sds_name": "1 km 16 days EVI",
                    "scale_factor": 0.0001,
                    "valid_range": (-2000, 10000),
                    "fill_value": -3000,
                    "units": "dimensionless",
                    "qc_sds": "1 km 16 days VI Quality"
                }
            },
            "temporal_resolution": "16-day",
            "spatial_resolution": 1000
        },

        # Vegetation Indices - Monthly 1km
        "MOD13A3": {
            "grid_name": "MOD_Grid_monthly_1km_VI",
            "variables": {
                "NDVI": {
                    "sds_name": "1 km monthly NDVI",
                    "scale_factor": 0.0001,
                    "valid_range": (-2000, 10000),
                    "fill_value": -3000,
                    "units": "dimensionless",
                    "qc_sds": "1 km monthly VI Quality"
                },
                "EVI": {
                    "sds_name": "1 km monthly EVI",
                    "scale_factor": 0.0001,
                    "valid_range": (-2000, 10000),
                    "fill_value": -3000,
                    "units": "dimensionless",
                    "qc_sds": "1 km monthly VI Quality"
                }
            },
            "temporal_resolution": "monthly",
            "spatial_resolution": 1000
        },

        # Aqua equivalents
        "MYD13A1": {
            "grid_name": "MOD_Grid_16DAY_500m_VI",
            "variables": {
                "NDVI": {
                    "sds_name": "500m 16 days NDVI",
                    "scale_factor": 0.0001,
                    "valid_range": (-2000, 10000),
                    "fill_value": -3000,
                    "units": "dimensionless",
                    "qc_sds": "500m 16 days VI Quality"
                },
                "EVI": {
                    "sds_name": "500m 16 days EVI",
                    "scale_factor": 0.0001,
                    "valid_range": (-2000, 10000),
                    "fill_value": -3000,
                    "units": "dimensionless",
                    "qc_sds": "500m 16 days VI Quality"
                }
            },
            "temporal_resolution": "16-day",
            "spatial_resolution": 500
        },

        "MYD13A2": {
            "grid_name": "MODIS_Grid_16DAY_1km_VI",
            "variables": {
                "NDVI": {
                    "sds_name": "1 km 16 days NDVI",
                    "scale_factor": 0.0001,
                    "valid_range": (-2000, 10000),
                    "fill_value": -3000,
                    "units": "dimensionless",
                    "qc_sds": "1 km 16 days VI Quality"
                },
                "EVI": {
                    "sds_name": "1 km 16 days EVI",
                    "scale_factor": 0.0001,
                    "valid_range": (-2000, 10000),
                    "fill_value": -3000,
                    "units": "dimensionless",
                    "qc_sds": "1 km 16 days VI Quality"
                }
            },
            "temporal_resolution": "16-day",
            "spatial_resolution": 1000
        },

        "MYD13A3": {
            "grid_name": "MOD_Grid_monthly_1km_VI",
            "variables": {
                "NDVI": {
                    "sds_name": "1 km monthly NDVI",
                    "scale_factor": 0.0001,
                    "valid_range": (-2000, 10000),
                    "fill_value": -3000,
                    "units": "dimensionless",
                    "qc_sds": "1 km monthly VI Quality"
                },
                "EVI": {
                    "sds_name": "1 km monthly EVI",
                    "scale_factor": 0.0001,
                    "valid_range": (-2000, 10000),
                    "fill_value": -3000,
                    "units": "dimensionless",
                    "qc_sds": "1 km monthly VI Quality"
                }
            },
            "temporal_resolution": "monthly",
            "spatial_resolution": 1000
        },

        "MYD11A1": {
            "grid_name": "MODIS_Grid_Daily_1km_LST",
            "variables": {
                "LST_Day": {
                    "sds_name": "LST_Day_1km",
                    "scale_factor": 0.02,
                    "add_offset": 0.0,
                    "valid_range": (7500, 65535),
                    "fill_value": 0,
                    "units": "Kelvin",
                    "convert_to_celsius": True,
                    "qc_sds": "QC_Day"
                },
                "LST_Night": {
                    "sds_name": "LST_Night_1km",
                    "scale_factor": 0.02,
                    "add_offset": 0.0,
                    "valid_range": (7500, 65535),
                    "fill_value": 0,
                    "units": "Kelvin",
                    "convert_to_celsius": True,
                    "qc_sds": "QC_Night"
                }
            },
            "temporal_resolution": "daily",
            "spatial_resolution": 1000
        },

        # Vegetation Continuous Fields
        "MOD44B": {
            "grid_name": "MOD44B_250m_GRID",
            "variables": {
                "Percent_Tree_Cover": {
                    "sds_name": "Percent_Tree_Cover",
                    "scale_factor": 1.0,
                    "valid_range": (0, 100),
                    "fill_value": 200,
                    "units": "percent",
                    "qc_sds": "Quality"
                },
                "Percent_NonTree_Vegetation": {
                    "sds_name": "Percent_NonTree_Vegetation",
                    "scale_factor": 1.0,
                    "valid_range": (0, 100),
                    "fill_value": 200,
                    "units": "percent",
                    "qc_sds": "Quality"
                }
            },
            "temporal_resolution": "annual",
            "spatial_resolution": 250
        }
    },

    "processing": {
        "default_nodata": -9999.0,
        "target_crs": "EPSG:5070",
        "target_resolution": 250,
        "resampling_method": "bilinear",
        "output_format": "GeoTIFF",
        "compression": "lzw",
        "tiled": True,
        "blocksize": 256
    },

    "quality_masks": {
        # Quality bit interpretations for different products
        "MOD11_QC": {
            "mandatory_qa_bits": [0, 1],  # Bits 0-1
            "good_quality_values": [0],   # 00 = good quality
            "data_quality_bits": [2, 3],  # Bits 2-3
            "error_bits": [6, 7]          # Bits 6-7
        },
        "MOD13_VI_Quality": {
            "modland_qa_bits": [0, 1],    # Bits 0-1
            "good_quality_values": [0],   # 00 = good quality
            "vi_usefulness_bits": [2, 5], # Bits 2-5
            "aerosol_bits": [6, 7],       # Bits 6-7
            "cloud_bits": [10, 11, 12, 13] # Bits 10-13
        }
    }
}

DEFAULT_TARGET_CRS = "EPSG:5070"  # CONUS Albers
DEFAULT_TARGET_RESOLUTION = 250   # meters

# --- Utility Functions ---

def setup_output_directory(output_dir: str) -> Path:
    """Create output directory if it doesn't exist."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def print_progress(current: int, total: int, item_name: str = "items"):
    """Print progress indicator."""
    percentage = (current / total) * 100
    bar_length = 30
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f"\r  Progress: |{bar}| {percentage:.1f}% ({current}/{total} {item_name})", end='', flush=True)
    if current == total:
        print()  # New line when complete

def load_config(config_path: Optional[Path] = None) -> Dict:
    """Load processing configuration from file or return default."""
    if config_path and config_path.exists():
        print(f"Loading configuration from: {config_path}")

        if config_path.suffix.lower() == '.json':
            with open(config_path, 'r') as f:
                config = json.load(f)
        elif config_path.suffix.lower() in ['.yml', '.yaml']:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")

        # Merge with defaults
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        return merged_config
    else:
        print("Using default configuration")
        return DEFAULT_CONFIG

def save_config_template(output_path: Path):
    """Save a configuration template file."""
    print(f"Saving configuration template to: {output_path}")

    with open(output_path, 'w') as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)

    print("Edit this configuration file to customize processing parameters")

def parse_modis_filename(filename: str) -> Optional[Dict[str, str]]:
    """Parse MODIS HDF filename to extract metadata."""
    # Example: MOD11A1.A2020001.h10v05.061.2021002030405.hdf
    match = re.match(
        r'(?P<product>\w+)\.A(?P<year>\d{4})(?P<doy>\d{3})\.(?P<tile>h\d{2}v\d{2})\.(?P<collection>\d{3})\.(?P<prod_datetime>\d+)\.hdf',
        Path(filename).name
    )

    if match:
        data = match.groupdict()
        # Convert Julian day to calendar date
        date_obj = datetime.strptime(f"{data['year']}{data['doy']}", '%Y%j')
        data['date'] = date_obj.strftime('%Y-%m-%d')
        data['base_product'] = data['product']  # Use full product name for configuration lookup
        return data
    return None

def find_modis_files(input_dir: Path, product_filter: Optional[str] = None,
                    date_filter: Optional[str] = None, year: Optional[int] = None,
                    month: Optional[int] = None) -> List[Path]:
    """Find MODIS HDF files matching criteria."""
    print(f"Searching for MODIS files in: {input_dir}")

    hdf_files = list(input_dir.rglob("*.hdf"))
    filtered_files = []

    for hdf_file in hdf_files:
        file_info = parse_modis_filename(hdf_file.name)
        if not file_info:
            continue

        # Apply filters
        if product_filter and not file_info['product'].startswith(product_filter):
            continue

        if date_filter:
            if file_info['date'] != date_filter:
                continue

        if year and int(file_info['year']) != year:
            continue

        if month:
            file_date = datetime.strptime(file_info['date'], '%Y-%m-%d')
            if file_date.month != month:
                continue

        filtered_files.append(hdf_file)

    print(f"Found {len(filtered_files)} matching files")
    return sorted(filtered_files)

def extract_bits(data: xr.DataArray, bit_range: List[int]) -> xr.DataArray:
    """Extract specific bits from data array."""
    if len(bit_range) == 2:
        start_bit, end_bit = bit_range
        mask = (1 << (end_bit - start_bit + 1)) - 1
        return (data >> start_bit) & mask
    else:
        # Single bit
        return (data >> bit_range[0]) & 1

def apply_quality_mask(data: xr.DataArray, qc_data: xr.DataArray,
                      qc_config: Dict, product_type: str) -> xr.DataArray:
    """Apply quality mask based on QC configuration."""

    if product_type.startswith('MOD11') and 'MOD11_QC' in qc_config:
        config = qc_config['MOD11_QC']
        mandatory_qa = extract_bits(qc_data, config['mandatory_qa_bits'])
        good_mask = np.isin(mandatory_qa, config['good_quality_values'])

    elif product_type.startswith('MOD13') and 'MOD13_VI_Quality' in qc_config:
        config = qc_config['MOD13_VI_Quality']
        modland_qa = extract_bits(qc_data, config['modland_qa_bits'])
        good_mask = np.isin(modland_qa, config['good_quality_values'])

        # Additional VI usefulness check
        if 'vi_usefulness_bits' in config:
            vi_usefulness = extract_bits(qc_data, config['vi_usefulness_bits'])
            good_mask = good_mask & (vi_usefulness <= 1)  # Keep highest quality

    else:
        return data

    masked_data = data.where(good_mask)
    valid_pixels = good_mask.sum().item()
    print(f"      Quality filtered: {valid_pixels:,} valid pixels")

    return masked_data

def process_single_tile(hdf_file_path: Path, variable: str, config: Dict,
                       apply_quality_mask_flag: bool = True) -> Optional[xr.DataArray]:
    """Process a single MODIS HDF tile."""
    # This function is now more concise and has been removed from the main output
    # print(f"    Processing tile: {hdf_file_path.name} for variable: {variable}")

    if not hdf_file_path.exists():
        print(f"      Error: Input file not found: {hdf_file_path}")
        return None

    try:
        # Parse filename
        file_info = parse_modis_filename(hdf_file_path.name)
        if not file_info:
            return None

        base_product = file_info['base_product']

        if base_product not in config['product_configs']:
            return None

        product_config = config['product_configs'][base_product]

        # Handle LST alias
        if variable == 'LST':
            variable = 'LST_Day'  # Default to LST_Day if 'LST' is used

        if variable not in product_config['variables']:
            # Provide a more helpful error message
            if "LST" in variable and ("LST_Day" in product_config['variables'] or "LST_Night" in product_config['variables']):
                 print(f"      Error: '{variable}' is not a valid variable. Did you mean 'LST_Day' or 'LST_Night'?")
            else:
                 print(f"      Error: Variable '{variable}' not found in configuration for product '{base_product}'.")
            return None

        var_config = product_config['variables'][variable]

        # Construct SDS URI with absolute path
        abs_path = hdf_file_path.resolve()
        sds_uri = f'HDF4_EOS:EOS_GRID:"{str(abs_path)}":{product_config["grid_name"]}:{var_config["sds_name"]}'

        # Removed verbose SDS opening message

        # Open data
        da_raw = rioxarray.open_rasterio(sds_uri, masked=True).squeeze()

        # Handle fill values
        if 'fill_value' in var_config:
            da_raw = da_raw.where(da_raw != var_config['fill_value'])

        # Apply valid range
        if 'valid_range' in var_config:
            min_val, max_val = var_config['valid_range']
            da_raw = da_raw.where((da_raw >= min_val) & (da_raw <= max_val))

        # Apply scaling
        da_scaled = da_raw * var_config['scale_factor']
        if 'add_offset' in var_config:
            da_scaled = da_scaled + var_config['add_offset']

        # Convert temperature to Celsius if specified
        if var_config.get('convert_to_celsius', False):
            da_scaled = da_scaled - 273.15
            units = 'degrees_Celsius'
        else:
            units = var_config.get('units', 'unknown')

        # Set attributes
        da_scaled.attrs.update({
            'units': units,
            'long_name': f'{variable} from MODIS {base_product}',
            'scale_factor': var_config['scale_factor'],
            'source_file': hdf_file_path.name,
            'product': file_info['product'],
            'date': file_info['date'],
            'tile': file_info['tile']
        })

        # Set nodata
        nodata_value = config['processing']['default_nodata']
        da_scaled = da_scaled.rio.write_nodata(nodata_value, encoded=True, inplace=True)


        # Apply quality mask if requested and available
        if apply_quality_mask_flag and 'qc_sds' in var_config:
            qc_uri = f'HDF4_EOS:EOS_GRID:"{str(abs_path)}":{product_config["grid_name"]}:{var_config["qc_sds"]}'

            try:
                da_qc = rioxarray.open_rasterio(qc_uri, masked=False).squeeze()
                da_scaled = apply_quality_mask(
                    da_scaled, da_qc, config['quality_masks'], base_product
                )
            except Exception as e:
                print(f"      Warning: Could not apply quality mask: {str(e)}")

        return da_scaled

    except Exception as e:
        print(f"      Error processing {hdf_file_path.name}: {str(e)}")
        return None

def mosaic_tiles(tiles: List[xr.DataArray], method: str = 'mean') -> xr.DataArray:
    """Mosaic multiple tiles into a single array."""
    print(f"  Mosaicking {len(tiles)} tiles...")

    if len(tiles) == 1:
        return tiles[0]

    # Combine tiles along a new dimension
    combined = xr.concat(tiles, dim='tile')

    if method == 'mean':
        mosaicked = combined.mean(dim='tile', skipna=True)
    elif method == 'max':
        mosaicked = combined.max(dim='tile', skipna=True)
    elif method == 'min':
        mosaicked = combined.min(dim='tile', skipna=True)
    elif method == 'first':
        mosaicked = combined.isel(tile=0)
    else:
        mosaicked = combined.mean(dim='tile', skipna=True)

    # Preserve attributes from first tile
    mosaicked.attrs.update(tiles[0].attrs)
    mosaicked.attrs['tiles_mosaicked'] = len(tiles)
    mosaicked.attrs['mosaic_method'] = method

    return mosaicked

def reproject_data(data: xr.DataArray, target_crs: str, target_resolution: float,
                  resampling_method: str = 'bilinear', nodata: float = -9999.0) -> xr.DataArray:
    """Reproject data to target CRS and resolution."""
    current_crs = data.rio.crs
    current_res = abs(data.rio.resolution()[0])

    if str(current_crs) == target_crs and abs(current_res - target_resolution) < 0.1:
        return data

    print(f"  Reprojecting to {target_crs} at {target_resolution}m resolution...")

    # Map resampling method names
    resampling_map = {
        'nearest': Resampling.nearest,
        'bilinear': Resampling.bilinear,
        'cubic': Resampling.cubic,
        'average': Resampling.average,
        'mode': Resampling.mode
    }

    resampling_enum = resampling_map.get(resampling_method, Resampling.bilinear)

    reprojected = data.rio.reproject(
        target_crs,
        resolution=target_resolution,
        resampling=resampling_enum,
        nodata=nodata
    )

    reprojected.attrs.update(data.attrs)
    reprojected.attrs['target_crs'] = target_crs
    reprojected.attrs['target_resolution_m'] = target_resolution
    reprojected.attrs['resampling_method'] = resampling_method

    return reprojected

def save_output(data: xr.DataArray, output_path: Path, config: Dict):
    """Save processed data to file."""
    proc_config = config['processing']

    if proc_config['output_format'].upper() == 'GEOTIFF':
        print(f"  Saving: {output_path.name}")

        # Prepare save options
        save_options = {
            'compress': proc_config.get('compression', 'lzw'),
            'tiled': proc_config.get('tiled', True),
        }

        if proc_config.get('blocksize'):
            save_options['blockxsize'] = proc_config['blocksize']
            save_options['blockysize'] = proc_config['blocksize']

        data.rio.to_raster(output_path, **save_options)

    elif proc_config['output_format'].upper() == 'NETCDF':
        print(f"  Saving: {output_path.name}")
        data.to_netcdf(output_path, encoding={data.name: {'zlib': True, 'complevel': 4}})

    else:
        raise ValueError(f"Unsupported output format: {proc_config['output_format']}")

def process_time_period(input_dir: Path, output_dir: Path, config: Dict,
                       variable: str, date_str: Optional[str] = None,
                       year: Optional[int] = None, month: Optional[int] = None,
                       product_filter: Optional[str] = None,
                       apply_quality_mask: bool = True) -> List[Path]:
    """Process MODIS data for a time period."""
    print(f"\nProcessing {variable} data")

    # Find files
    files = find_modis_files(
        input_dir,
        product_filter=product_filter,
        date_filter=date_str,
        year=year,
        month=month
    )

    if not files:
        print("No files found matching criteria")
        return []

    # Group files by date
    files_by_date = {}
    for file_path in files:
        file_info = parse_modis_filename(file_path.name)
        if file_info:
            date_key = file_info['date']
            if date_key not in files_by_date:
                files_by_date[date_key] = []
            files_by_date[date_key].append(file_path)

    output_files = []
    proc_config = config['processing']
    total_dates = len(files_by_date)

    # Process each date
    for date_idx, date_key in enumerate(sorted(files_by_date.keys()), 1):
        date_files = files_by_date[date_key]
        print(f"\n  Processing date: {date_key} ({len(date_files)} tiles)")

        # Show progress for multiple dates
        if total_dates > 1:
            print_progress(date_idx, total_dates, "dates")

        # Process each tile
        processed_tiles = []
        for tile_idx, hdf_file in enumerate(date_files, 1):
            tile_data = process_single_tile(
                hdf_file, variable, config, apply_quality_mask
            )
            if tile_data is not None:
                processed_tiles.append(tile_data)

            # Show tile progress for large numbers of tiles
            if len(date_files) > 5:
                print_progress(tile_idx, len(date_files), "tiles")

        if not processed_tiles:
            print(f"  ✗ No valid tiles for {date_key}")
            continue

        print(f"  ✓ Processed {len(processed_tiles)}/{len(date_files)} tiles successfully")

        # Mosaic tiles
        mosaicked = mosaic_tiles(processed_tiles)


        # Reproject if needed
        reprojected = reproject_data(
            mosaicked,
            proc_config['target_crs'],
            proc_config['target_resolution'],
            proc_config['resampling_method'],
            proc_config['default_nodata']
        )


        # Generate output filename
        date_obj = datetime.strptime(date_key, '%Y-%m-%d')
        product_prefix = product_filter if product_filter else "MODIS"

        if proc_config['output_format'].upper() == 'GEOTIFF':
            ext = 'tif'
        elif proc_config['output_format'].upper() == 'NETCDF':
            ext = 'nc'
        else:
            ext = 'tif'

        output_filename = f"{product_prefix}_{variable}_{date_obj.strftime('%Y%m%d')}.{ext}"
        output_path = output_dir / output_filename

        # Add processing metadata
        reprojected.attrs.update({
            'processing_date': datetime.now().isoformat(),
            'processing_config': 'generic_modis_processing',
            'tiles_processed': len(processed_tiles),
            'quality_mask_applied': apply_quality_mask
        })

        # Save output
        save_output(reprojected, output_path, config)

        # Print statistics
        valid_pixels = reprojected.where(reprojected != proc_config['default_nodata']).count()
        file_size_mb = output_path.stat().st_size / 1024**2
        print(f"  ✓ Saved: {output_filename} ({valid_pixels.item():,} pixels, {file_size_mb:.1f} MB)")

        output_files.append(output_path)

        # Clean up memory
        del mosaicked, reprojected, processed_tiles
        gc.collect()


    return output_files

def test_vcf_config():
    """Verify that the VCF configuration is correct."""
    print("\n=== Verifying VCF Configuration ===")
    config = load_config()
    if 'MOD44B' in config['product_configs']:
        vcf_config = config['product_configs']['MOD44B']
        print("✓ MOD44B product found in configuration.")
        if 'Percent_Tree_Cover' in vcf_config['variables']:
            print("✓ Percent_Tree_Cover variable found.")
            tree_cover_config = vcf_config['variables']['Percent_Tree_Cover']
            if tree_cover_config['sds_name'] == 'Percent_Tree_Cover' and vcf_config['grid_name'] == 'MOD_Grid_MOD44B':
                print("✓ SDS name and grid name are correct.")
                print("✓ VCF configuration appears to be correct.")
                return True
            else:
                print("✗ VCF SDS name or grid name is incorrect.")
                return False
        else:
            print("✗ Percent_Tree_Cover variable not found in MOD44B config.")
            return False
    else:
        print("✗ MOD44B product not found in configuration.")
        return False

def main():
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Process MODIS HDF files to analysis-ready formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Process NDVI for January 2020
        python modis_process_generic.py --variable NDVI --input-dir ./data --output-dir ./processed --year 2020 --month 1

        # Process LST for specific date
        python modis_process_generic.py --variable LST_Day --input-dir ./data --output-dir ./processed --date 2020-01-15

        # Use custom configuration
        python modis_process_generic.py --config custom_config.json --variable NDVI --input-dir ./data --output-dir ./processed --year 2020 --month 1

        # Generate configuration template
        python modis_process_generic.py --create-config-template config_template.json
                """
    )

    # Configuration
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--config', type=str, help='Configuration file (JSON or YAML)')
    parser.add_argument('--create-config-template', type=str,
                       help='Create configuration template file and exit')
    parser.add_argument('--test-vcf', action='store_true', help='Test VCF configuration')

    # Required arguments
    parser.add_argument('--variable', type=str, required=False,
                       help='Variable to process (e.g., NDVI, LST_Day, Percent_Tree_Cover)')
    parser.add_argument('--input-dir', type=str, required=False,
                       help='Directory containing raw MODIS HDF files')
    parser.add_argument('--output-dir', type=str, required=False,
                       help='Directory for processed output files')

    # Time selection
    time_group = parser.add_mutually_exclusive_group()
    time_group.add_argument('--date', type=str, help='Process specific date (YYYY-MM-DD)')
    time_group.add_argument('--year-month', nargs=2, type=int, metavar=('YEAR', 'MONTH'),
                           help='Process entire month')

    # Optional arguments
    parser.add_argument('--product', type=str, help='Filter by product (e.g., MOD11A1, MOD13A1)')
    parser.add_argument('--no-quality-mask', action='store_true',
                       help='Disable quality masking')

    args = parser.parse_args()

    # Handle config template creation
    if args.create_config_template:
        save_config_template(Path(args.create_config_template))
        return

    # Handle VCF test
    if args.test_vcf:
        if test_vcf_config():
            sys.exit(0)
        else:
            sys.exit(1)

    # Validate required arguments
    if not all([args.variable, args.input_dir, args.output_dir]):
        parser.error("--variable, --input-dir, and --output-dir are required")

    if not (args.date or args.year_month):
        parser.error("Either --date or --year-month must be specified")

    # Load configuration
    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)

    # Setup paths
    input_dir = Path(args.input_dir)
    output_dir = setup_output_directory(args.output_dir)

    if not input_dir.exists():
        print(f"Error: Input directory does not exist: {input_dir}")
        sys.exit(1)

    print("Generic MODIS Processing")
    print("=" * 30)
    print(f"Variable: {args.variable}")
    print(f"Quality masking: {'disabled' if args.no_quality_mask else 'enabled'}")

    try:
        # Process data
        apply_quality_mask = not args.no_quality_mask

        if args.date:
            output_files = process_time_period(
                input_dir, output_dir, config,
                args.variable,
                date_str=args.date,
                product_filter=args.product,
                apply_quality_mask=apply_quality_mask
            )
        else:
            year, month = args.year_month
            output_files = process_time_period(
                input_dir, output_dir, config,
                args.variable,
                year=year,
                month=month,
                product_filter=args.product,
                apply_quality_mask=apply_quality_mask
            )

        if output_files:
            print(f"\n🎉 Processing completed successfully!")
            total_size = sum(f.stat().st_size for f in output_files) / 1024**2

            if len(output_files) == 1:
                print(f"Generated: {output_files[0].name} ({total_size:.1f} MB)")
            else:
                print(f"Generated {len(output_files)} files ({total_size:.1f} MB total):")
                for output_file in output_files:
                    file_size = output_file.stat().st_size / 1024**2
                    print(f"  ✓ {output_file.name} ({file_size:.1f} MB)")
        else:
            print("\n❌ No files were processed")
            sys.exit(1)

    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
