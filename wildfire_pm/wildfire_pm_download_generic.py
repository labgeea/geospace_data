#!/usr/bin/env python3
"""
Wildfire Smoke Reanalysis (Stanford Smoke PM2.5) Download Script
Downloads the canonical dataset from Harvard Dataverse (Childs et al., 2022).
"""

import sys
import os
import argparse
import requests
import json
import logging
from pathlib import Path
from tqdm import tqdm

# Setup GEOSPACE framework version mapping
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from version import get_module_version
    __version__ = get_module_version("wildfire_pm")
except ImportError:
    __version__ = "1.0.0"

__module__ = "Wildfire Smoke Download"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Harvard Dataverse API endpoint for file downloads
DATAVERSE_BASE_URL = "https://dataverse.harvard.edu/api/access/datafile/"

# Mapping geographies to their Dataverse File IDs
FILE_MANIFEST = {
    "10km": {
        "data": {"id": "8550337", "name": "smokePM2pt5_predictions_daily_10km_20060101-20201231.csv"},
        "shapefile": [
            {"id": "8550317", "name": "10km_grid_wgs84.shp"},
            {"id": "8550318", "name": "10km_grid_wgs84.shx"},
            {"id": "8550315", "name": "10km_grid_wgs84.dbf"},
            {"id": "8550314", "name": "10km_grid_wgs84.prj"}
        ]
    },
    "county": {
        "data": {"id": "8550336", "name": "smokePM2pt5_predictions_daily_county_20060101-20201231.csv"},
        "shapefile": []
    },
    "tract": {
        "data": {"id": "8550341", "name": "smokePM2pt5_predictions_daily_tract_20060101-20201231.csv"},
        "shapefile": []
    },
    "zcta": {
        "data": {"id": "8550342", "name": "smokePM2pt5_predictions_daily_zcta_20060101-20201231.csv"},
        "shapefile": []
    }
}

def create_parser():
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Download Stanford Smoke PM2.5',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--geography', '-g', choices=['10km', 'county', 'tract', 'zcta', 'all'], 
                        default='county', help='Spatial resolution to download')
    parser.add_argument('--output-dir', '-o', type=Path, default=Path('./raw'), 
                        help='Output directory for downloaded files')
    parser.add_argument('--include-shapefiles', action='store_true', 
                        help='Also download corresponding geometry shapefiles (if applicable)')
    
    return parser

def download_file(file_id: str, output_path: Path):
    """Download a file from Harvard Dataverse using its File ID."""
    if output_path.exists():
        logger.info(f"File {output_path.name} already exists. Skipping download.")
        return

    url = f"{DATAVERSE_BASE_URL}{file_id}"
    logger.info(f"Downloading {output_path.name} from Dataverse...")
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            # Try to get file size from headers
            total_size = int(r.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f, tqdm(
                desc=output_path.name,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)
        logger.info(f"Successfully downloaded {output_path.name}")
    except Exception as e:
        logger.error(f"Failed to download {output_path.name}: {e}")
        if output_path.exists():
            output_path.unlink() # Clean up partial
        sys.exit(1)

def main():
    parser = create_parser()
    args = parser.parse_args()
    
    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    geos = list(FILE_MANIFEST.keys()) if args.geography == 'all' else [args.geography]
    
    logger.info(f"Starting {__module__} v{__version__}")
    logger.info(f"Target Geographies: {', '.join(geos)}")
    logger.info(f"Output Directory: {args.output_dir.absolute()}")
    
    for geo in geos:
        manifest = FILE_MANIFEST[geo]
        
        # Download main data CSV
        data_info = manifest["data"]
        download_file(data_info["id"], args.output_dir / data_info["name"])
        
        # Download shapefiles if requested
        if args.include_shapefiles and manifest["shapefile"]:
            logger.info(f"Downloading shapefiles for geometry: {geo}...")
            for shp_info in manifest["shapefile"]:
                download_file(shp_info["id"], args.output_dir / shp_info["name"])

if __name__ == "__main__":
    main()
