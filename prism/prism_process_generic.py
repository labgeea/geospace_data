#!/usr/bin/env python3
"""
PRISM Climate Data Processing Script
======================================

Converts PRISM BIL/ASC/NetCDF files (downloaded from the PRISM Web Service)
into analysis-ready GeoTIFFs reprojected to EPSG:5070 (CONUS Albers).

Handles:
  - BIL format (most common for daily/normals downloads)
  - NetCDF format (available for some products)
  - ASC (ASCII grid) format

Processing steps:
  1. Discover input files recursively under --input-dir
  2. Read each raster with rasterio
  3. Reproject to EPSG:5070
  4. Write Cloud-Optimised GeoTIFF (LZW, tiled, float32, nodata=-9999)
  5. Emit per-file processing summary

Requirements:
    rasterio, numpy, pathlib

Author: GEOSPACE Project
License: Public Domain

Usage:
    python prism_process_generic.py --input-dir ./raw/prism/ --output-dir ./proc/prism/
    python prism_process_generic.py --input-dir ./raw/prism/ppt/ --output-dir ./proc/prism/ --element ppt
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_module_version

__version__ = get_module_version("prism")
__module__ = "PRISM Processing"

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.warp import calculate_default_transform, reproject, Resampling

# ---------------------------------------------------------------------------
# Variable metadata (units, valid range, aggregation method)
# ---------------------------------------------------------------------------

PRISM_VARIABLE_CONFIG = {
    "ppt": {
        "long_name": "Precipitation",
        "units": "mm",
        "valid_range": (0, 2000),
        "nodata": -9999.0,
        "aggregation": "sum",
    },
    "tmin": {
        "long_name": "Minimum Temperature",
        "units": "degrees C",
        "valid_range": (-60, 60),
        "nodata": -9999.0,
        "aggregation": "mean",
    },
    "tmax": {
        "long_name": "Maximum Temperature",
        "units": "degrees C",
        "valid_range": (-60, 60),
        "nodata": -9999.0,
        "aggregation": "mean",
    },
    "tmean": {
        "long_name": "Mean Temperature",
        "units": "degrees C",
        "valid_range": (-60, 60),
        "nodata": -9999.0,
        "aggregation": "mean",
    },
    "tdmean": {
        "long_name": "Mean Dew Point Temperature",
        "units": "degrees C",
        "valid_range": (-60, 40),
        "nodata": -9999.0,
        "aggregation": "mean",
    },
    "vpdmin": {
        "long_name": "Minimum Vapor Pressure Deficit",
        "units": "hPa",
        "valid_range": (0, 200),
        "nodata": -9999.0,
        "aggregation": "mean",
    },
    "vpdmax": {
        "long_name": "Maximum Vapor Pressure Deficit",
        "units": "hPa",
        "valid_range": (0, 200),
        "nodata": -9999.0,
        "aggregation": "mean",
    },
    "solslope": {
        "long_name": "Sloped-Surface Solar Radiation",
        "units": "W/m^2",
        "valid_range": (0, 500),
        "nodata": -9999.0,
        "aggregation": "mean",
    },
    "soltotal": {
        "long_name": "Total Global Shortwave Solar Radiation",
        "units": "W/m^2",
        "valid_range": (0, 500),
        "nodata": -9999.0,
        "aggregation": "mean",
    },
    "solclear": {
        "long_name": "Clearness Index",
        "units": "fraction",
        "valid_range": (0, 1),
        "nodata": -9999.0,
        "aggregation": "mean",
    },
    "soltrans": {
        "long_name": "Atmospheric Transmittance",
        "units": "fraction",
        "valid_range": (0, 1),
        "nodata": -9999.0,
        "aggregation": "mean",
    },
}

TARGET_CRS = "EPSG:5070"
NODATA = -9999.0

# File extensions to process
RASTER_EXTENSIONS = {".bil", ".asc", ".nc", ".tif", ".tiff"}


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def find_raster_files(input_dir: Path, element: str | None = None) -> list[Path]:
    """
    Recursively find all PRISM raster files under input_dir.
    If element is specified, only files whose name contains that element code.
    """
    candidates = []
    for ext in RASTER_EXTENSIONS:
        candidates.extend(input_dir.rglob(f"*{ext}"))

    if element:
        candidates = [f for f in candidates if element.lower() in f.name.lower()]

    # Skip header/metadata files
    candidates = [
        f for f in candidates
        if not any(f.name.endswith(s) for s in [".hdr", ".prj", ".stx", ".xml", ".aux.xml"])
    ]

    return sorted(candidates)


def infer_element(filepath: Path) -> str:
    """
    Infer the PRISM element from a filename.
    PRISM filenames follow: PRISM_{element}_{stability}_{grid}_{time}_bil.zip
    or PRISM_{element}_{type}_{time}.bil
    """
    name = filepath.stem.lower()
    for elem in PRISM_VARIABLE_CONFIG:
        # Match element token surrounded by underscores or at start
        if f"_{elem}_" in name or name.startswith(f"prism_{elem}_"):
            return elem
    return "unknown"


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

def get_config(element: str) -> dict:
    return PRISM_VARIABLE_CONFIG.get(element, {
        "long_name": element,
        "units": "unknown",
        "valid_range": (None, None),
        "nodata": NODATA,
        "aggregation": "mean",
    })


def process_raster(
    src_path: Path,
    dst_path: Path,
    element: str,
    target_crs: str = TARGET_CRS,
) -> dict:
    """
    Reproject a single PRISM raster to target_crs and save as GeoTIFF.

    Returns a stats dict.
    """
    cfg = get_config(element)
    nodata = cfg["nodata"]

    with rasterio.open(src_path) as src:
        src_crs = src.crs or CRS.from_epsg(4326)  # PRISM native is WGS84
        transform, width, height = calculate_default_transform(
            src_crs, CRS.from_string(target_crs),
            src.width, src.height,
            *src.bounds
        )

        profile = src.profile.copy()
        profile.update({
            "driver":    "GTiff",
            "crs":       target_crs,
            "transform": transform,
            "width":     width,
            "height":    height,
            "dtype":     "float32",
            "nodata":    nodata,
            "compress":  "lzw",
            "tiled":     True,
            "blockxsize": 512,
            "blockysize": 512,
            "count":     src.count,
        })

        dst_path.parent.mkdir(parents=True, exist_ok=True)

        with rasterio.open(dst_path, "w", **profile) as dst:
            for band_idx in range(1, src.count + 1):
                data = src.read(band_idx).astype("float32")

                # Mask nodata from source
                src_nodata = src.nodata
                if src_nodata is not None:
                    data[data == src_nodata] = np.nan

                reprojected = np.empty((height, width), dtype="float32")

                reproject(
                    source=data,
                    destination=reprojected,
                    src_transform=src.transform,
                    src_crs=src_crs,
                    dst_transform=transform,
                    dst_crs=CRS.from_string(target_crs),
                    resampling=Resampling.bilinear,
                    src_nodata=np.nan,
                    dst_nodata=nodata,
                )

                # Validate range
                vmin, vmax = cfg["valid_range"]
                valid_mask = reprojected != nodata
                if vmin is not None and valid_mask.any():
                    out_of_range = valid_mask & ((reprojected < vmin) | (reprojected > vmax))
                    if out_of_range.any():
                        n = int(out_of_range.sum())
                        print(f"    ⚠ {n} pixels outside valid range [{vmin}, {vmax}] set to nodata")
                        reprojected[out_of_range] = nodata

                dst.write(reprojected, band_idx)

            # Write metadata tags
            dst.update_tags(
                element=element,
                long_name=cfg["long_name"],
                units=cfg["units"],
                source="PRISM Climate Group, Oregon State University",
                source_url="https://prism.oregonstate.edu/",
                original_crs=str(src_crs),
                target_crs=target_crs,
                processing_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                geospace_version=__version__,
            )

    # Compute output stats
    with rasterio.open(dst_path) as dst:
        arr = dst.read(1).astype("float64")
        valid = arr[arr != nodata]
        stats = {
            "file": str(dst_path),
            "element": element,
            "valid_pixels": int(valid.size),
            "total_pixels": int(arr.size),
            "min": float(valid.min()) if valid.size else None,
            "max": float(valid.max()) if valid.size else None,
            "mean": float(valid.mean()) if valid.size else None,
            "size_mb": round(dst_path.stat().st_size / (1024 ** 2), 2),
        }

    return stats


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def process_prism(
    input_dir: str,
    output_dir: str,
    element: str | None = None,
    target_crs: str = TARGET_CRS,
) -> list[dict]:
    """
    Process all PRISM rasters found under input_dir.

    Returns list of per-file stats dicts.
    """
    in_path = Path(input_dir)
    out_path = Path(output_dir)

    files = find_raster_files(in_path, element=element)
    if not files:
        print(f"No PRISM raster files found under {in_path}")
        return []

    print(f"Found {len(files)} file(s) to process")
    all_stats = []

    for i, src_file in enumerate(files, 1):
        elem = element or infer_element(src_file)
        # Preserve subdirectory structure under output_dir
        rel = src_file.relative_to(in_path)
        dst_file = out_path / rel.with_suffix(".tif")

        print(f"\n[{i}/{len(files)}] {src_file.name}")
        print(f"  Element  : {elem}")
        print(f"  Output   : {dst_file}")

        try:
            stats = process_raster(src_file, dst_file, elem, target_crs)
            all_stats.append(stats)
            print(f"  ✓ {stats['valid_pixels']:,}/{stats['total_pixels']:,} valid pixels | "
                  f"range [{stats['min']:.3f}, {stats['max']:.3f}] | "
                  f"{stats['size_mb']} MB")
        except Exception as exc:
            print(f"  ✗ Failed: {exc}")
            all_stats.append({"file": str(src_file), "error": str(exc)})

    return all_stats


def write_report(stats: list[dict], output_dir: str):
    """Write JSON processing report."""
    report_path = Path(output_dir) / "prism_processing_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "geospace_version": __version__,
        "total_files": len(stats),
        "succeeded": sum(1 for s in stats if "error" not in s),
        "failed": sum(1 for s in stats if "error" in s),
        "files": stats,
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n✓ Report written: {report_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=f"{__module__} Framework v{__version__} — Process PRISM climate rasters to EPSG:5070 GeoTIFFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all elements under raw/prism/
  %(prog)s --input-dir ./raw/prism/ --output-dir ./proc/prism/

  # Process only precipitation files
  %(prog)s --input-dir ./raw/prism/ --output-dir ./proc/prism/ --element ppt

  # Keep native PRISM CRS (skip reprojection)
  %(prog)s --input-dir ./raw/prism/ --output-dir ./proc/prism/ --crs EPSG:4326
        """,
    )

    parser.add_argument("--version", action="version", version=f"{__module__} v{__version__}")
    parser.add_argument(
        "--input-dir", "-i",
        required=True,
        help="Directory containing downloaded PRISM files (searched recursively)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        required=True,
        help="Output directory for processed GeoTIFFs",
    )
    parser.add_argument(
        "--element", "-e",
        help="Filter processing to a specific PRISM element (e.g. ppt, tmax)",
    )
    parser.add_argument(
        "--crs",
        default=TARGET_CRS,
        help=f"Target CRS (default: {TARGET_CRS})",
    )

    args = parser.parse_args()

    print(f"PRISM Climate Data Processing")
    print("=" * 50)
    print(f"  Module version : {__version__}")
    print(f"  Input dir      : {args.input_dir}")
    print(f"  Output dir     : {args.output_dir}")
    print(f"  Element filter : {args.element or 'all'}")
    print(f"  Target CRS     : {args.crs}")

    stats = process_prism(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        element=args.element,
        target_crs=args.crs,
    )

    write_report(stats, args.output_dir)

    succeeded = sum(1 for s in stats if "error" not in s)
    failed = len(stats) - succeeded
    print(f"\n{'='*50}")
    print(f"Processing Summary:")
    print(f"  Total files  : {len(stats)}")
    print(f"  Succeeded    : {succeeded}")
    print(f"  Failed       : {failed}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
