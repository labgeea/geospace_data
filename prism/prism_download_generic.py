#!/usr/bin/env python3
"""
PRISM Climate Data Download Script
====================================

Downloads gridded climate data from the PRISM Climate Group Web Service
(Oregon State University) for specified elements, time periods, and data types.

URL logic ported directly from the amadeus R package (download_prism).
Source: https://github.com/NIEHS/amadeus

Data source: https://services.nacse.org/prism/data/public/
Coverage:    CONUS, 4km resolution (time series) or 800m (normals)
Period:      1895–present (historical), 1981–present (daily time series)

Elements (time series):
    ppt, tmin, tmax, tmean, tdmean, vpdmin, vpdmax

Elements (normals only):
    solslope, soltotal, solclear, soltrans

Data types:
    ts           4km daily/monthly/annual time series
    normals_800  800m 30-year normals
    normals      4km 30-year normals

Time format:
    YYYYMMDD  daily time series
    YYYYMM    monthly time series
    YYYY      annual time series
    MM        monthly normal (01-12, or 14 for annual normal)
    MMDD      daily normal

Requirements:
    requests, pathlib

Author: GEOSPACE Project
License: Public Domain

Usage:
    python prism_download_generic.py --element ppt --time 20200101 --data-type ts --output-dir ./raw/prism/
    python prism_download_generic.py --element tmax --time 202001 --data-type ts --output-dir ./raw/prism/
    python prism_download_generic.py --element tmean --time 2020 --data-type ts --output-dir ./raw/prism/
    python prism_download_generic.py --element ppt --time 04 --data-type normals_800 --output-dir ./raw/prism/
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_module_version

__version__ = get_module_version("prism")
__module__ = "PRISM Download"

import argparse
import requests
import re
import zipfile
import time
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Variable catalog
# ---------------------------------------------------------------------------

PRISM_ELEMENTS = {
    "ppt": {
        "long_name": "Precipitation",
        "units": "mm",
        "description": "Total accumulated precipitation",
        "data_types": ["ts", "normals_800", "normals"],
    },
    "tmin": {
        "long_name": "Minimum Temperature",
        "units": "degrees C",
        "description": "Daily/monthly minimum near-surface air temperature",
        "data_types": ["ts", "normals_800", "normals"],
    },
    "tmax": {
        "long_name": "Maximum Temperature",
        "units": "degrees C",
        "description": "Daily/monthly maximum near-surface air temperature",
        "data_types": ["ts", "normals_800", "normals"],
    },
    "tmean": {
        "long_name": "Mean Temperature",
        "units": "degrees C",
        "description": "Daily/monthly mean near-surface air temperature",
        "data_types": ["ts", "normals_800", "normals"],
    },
    "tdmean": {
        "long_name": "Mean Dew Point Temperature",
        "units": "degrees C",
        "description": "Daily/monthly mean dew point temperature",
        "data_types": ["ts", "normals_800", "normals"],
    },
    "vpdmin": {
        "long_name": "Minimum Vapor Pressure Deficit",
        "units": "hPa",
        "description": "Daily/monthly minimum vapor pressure deficit",
        "data_types": ["ts", "normals_800", "normals"],
    },
    "vpdmax": {
        "long_name": "Maximum Vapor Pressure Deficit",
        "units": "hPa",
        "description": "Daily/monthly maximum vapor pressure deficit",
        "data_types": ["ts", "normals_800", "normals"],
    },
    # Normals-only elements
    "solslope": {
        "long_name": "Sloped-Surface Solar Radiation",
        "units": "W/m^2",
        "description": "Mean annual solar radiation on sloped surface (normals only)",
        "data_types": ["normals_800", "normals"],
    },
    "soltotal": {
        "long_name": "Total Global Shortwave Solar Radiation on Slope",
        "units": "W/m^2",
        "description": "Total global shortwave solar radiation on slope (normals only)",
        "data_types": ["normals_800", "normals"],
    },
    "solclear": {
        "long_name": "Clearness Index",
        "units": "fraction (0-1)",
        "description": "Ratio of actual to extraterrestrial radiation (normals only)",
        "data_types": ["normals_800", "normals"],
    },
    "soltrans": {
        "long_name": "Atmospheric Transmittance",
        "units": "fraction (0-1)",
        "description": "Fraction of extraterrestrial radiation reaching surface (normals only)",
        "data_types": ["normals_800", "normals"],
    },
}

DATA_TYPES = {
    "ts":          "4km resolution daily/monthly/annual time series (1895–present)",
    "normals_800": "800m resolution 30-year climate normals",
    "normals":     "4km resolution 30-year climate normals",
}

FORMATS = ["nc", "asc", "grib2"]

BASE_URL = "https://services.nacse.org/prism/data/public"

# ---------------------------------------------------------------------------
# URL construction (mirrors amadeus download_prism logic)
# ---------------------------------------------------------------------------

def build_url(element: str, time: str, data_type: str, fmt: str = "nc") -> str:
    """
    Build a PRISM Web Service download URL.

    URL patterns (from amadeus R source):
        ts:          {BASE_URL}/4km/{element}/{time}?format={fmt}
        normals_800: {BASE_URL}/normals/800m/{element}/{time}
        normals:     {BASE_URL}/normals/4km/{element}/{time}
    """
    if data_type == "ts":
        return f"{BASE_URL}/4km/{element}/{time}?format={fmt}"
    elif data_type == "normals_800":
        return f"{BASE_URL}/normals/800m/{element}/{time}"
    elif data_type == "normals":
        return f"{BASE_URL}/normals/4km/{element}/{time}"
    else:
        raise ValueError(f"Unknown data_type: {data_type}. Choose from: {list(DATA_TYPES)}")


def validate_element(element: str, data_type: str):
    """Validate that element is available for the chosen data_type."""
    if element not in PRISM_ELEMENTS:
        valid = list(PRISM_ELEMENTS.keys())
        raise ValueError(f"Unknown element '{element}'. Valid options: {valid}")

    allowed_types = PRISM_ELEMENTS[element]["data_types"]
    if data_type not in allowed_types:
        raise ValueError(
            f"Element '{element}' is not available for data_type='{data_type}'. "
            f"Available data_types for '{element}': {allowed_types}"
        )


def validate_time(time: str, data_type: str):
    """Basic time format validation."""
    if data_type == "ts":
        if not re.match(r"^\d{4,8}$", time):
            raise ValueError(
                f"For data_type='ts', time must be YYYYMMDD (daily), YYYYMM (monthly), "
                f"or YYYY (annual). Got: '{time}'"
            )
    else:
        if not re.match(r"^\d{2,4}$", time):
            raise ValueError(
                f"For normals, time must be MM (monthly), MMDD (daily), "
                f"or 14 (annual normal). Got: '{time}'"
            )


# ---------------------------------------------------------------------------
# Download logic
# ---------------------------------------------------------------------------

def download_file(url: str, output_dir: Path, element: str, time: str,
                  data_type: str, unzip: bool = True, retries: int = 3) -> Path | None:
    """
    Download a single PRISM file from the Web Service.

    Returns the path to the saved file (zip or extracted), or None on failure.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Filename: PRISM will serve a zip with internal BIL/NC/ASC files
    fname_stem = f"prism_{element}_{data_type}_{time}"
    zip_path = output_dir / f"{fname_stem}.zip"

    print(f"  URL: {url}")

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, stream=True, timeout=60)
            resp.raise_for_status()

            # Detect content-disposition filename if available
            cd = resp.headers.get("content-disposition", "")
            if "filename=" in cd:
                served_name = cd.split("filename=")[-1].strip().strip('"')
                zip_path = output_dir / served_name

            with open(zip_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size_mb = zip_path.stat().st_size / (1024 ** 2)
            print(f"  ✓ Downloaded: {zip_path.name} ({file_size_mb:.1f} MB)")

            # Unzip if requested and file is a zip
            if unzip and zipfile.is_zipfile(zip_path):
                extract_dir = output_dir / fname_stem
                extract_dir.mkdir(exist_ok=True)
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(extract_dir)
                print(f"  ✓ Extracted to: {extract_dir}/")
                zip_path.unlink()  # remove zip after extraction
                return extract_dir

            return zip_path

        except requests.HTTPError as e:
            print(f"  ✗ HTTP {e.response.status_code} on attempt {attempt}/{retries}: {url}")
            if e.response.status_code == 404:
                print(f"    Data not available for element='{element}' time='{time}'")
                return None
        except requests.RequestException as e:
            print(f"  ✗ Request error on attempt {attempt}/{retries}: {e}")

        if attempt < retries:
            wait = 2 ** attempt
            print(f"  Retrying in {wait}s...")
            time_mod = __import__("time")
            time_mod.sleep(wait)

    return None


# ---------------------------------------------------------------------------
# Multi-element / multi-time batch download
# ---------------------------------------------------------------------------

def download_prism(
    elements: list[str],
    times: list[str],
    data_type: str = "ts",
    fmt: str = "nc",
    output_dir: str = "./raw/prism/",
    unzip: bool = True,
) -> dict:
    """
    Download PRISM data for one or more elements and time periods.

    Parameters
    ----------
    elements   : list of element codes (e.g. ['ppt', 'tmax'])
    times      : list of time strings (e.g. ['20200101', '20200102'])
    data_type  : 'ts', 'normals_800', or 'normals'
    fmt        : file format for ts downloads: 'nc', 'asc', or 'grib2'
    output_dir : root directory to save files
    unzip      : extract downloaded zip archives

    Returns
    -------
    dict mapping (element, time) -> Path or None
    """
    out = Path(output_dir)
    results = {}

    total = len(elements) * len(times)
    n = 0

    for element in elements:
        validate_element(element, data_type)
        for t in times:
            validate_time(t, data_type)
            n += 1
            print(f"\n[{n}/{total}] {element} | time={t} | type={data_type}")
            url = build_url(element, t, data_type, fmt)
            elem_dir = out / element
            path = download_file(url, elem_dir, element, t, data_type, unzip=unzip)
            results[(element, t)] = path

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def list_variables():
    print(f"\nPRISM Elements ({len(PRISM_ELEMENTS)} available):")
    print("=" * 60)
    for code, meta in PRISM_ELEMENTS.items():
        types_str = ", ".join(meta["data_types"])
        print(f"  {code:10s}  {meta['long_name']} ({meta['units']})")
        print(f"            {meta['description']}")
        print(f"            Available for: {types_str}")
        print()

    print("Data Types:")
    print("-" * 40)
    for dt, desc in DATA_TYPES.items():
        print(f"  {dt:12s}  {desc}")

    print("\nTime Format Guide:")
    print("-" * 40)
    print("  ts:          YYYYMMDD (daily), YYYYMM (monthly), YYYY (annual)")
    print("  normals:     MM (monthly normal), MMDD (daily normal), 14 (annual normal)")


def main():
    parser = argparse.ArgumentParser(
        description=f"{__module__} Framework v{__version__} — Download PRISM climate data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Daily precipitation for one day
  %(prog)s --element ppt --time 20200115 --data-type ts --output-dir ./raw/prism/

  # Monthly max temperature for a range of months
  %(prog)s --element tmax --time 202001,202002,202003 --data-type ts --output-dir ./raw/prism/

  # Annual time series
  %(prog)s --element tmean --time 2019,2020 --data-type ts --output-dir ./raw/prism/

  # Multiple elements, single time
  %(prog)s --element ppt,tmin,tmax --time 20200101 --data-type ts --output-dir ./raw/prism/

  # 800m monthly normals (April)
  %(prog)s --element ppt --time 04 --data-type normals_800 --output-dir ./raw/prism/

  # List all available elements
  %(prog)s --list-variables
        """,
    )

    parser.add_argument("--version", action="version", version=f"{__module__} v{__version__}")

    parser.add_argument(
        "--element", "-e",
        type=str,
        help="Comma-separated list of PRISM elements (e.g. ppt,tmax,tmin)",
    )
    parser.add_argument(
        "--time", "-t",
        type=str,
        help="Comma-separated time string(s). Format depends on --data-type.",
    )
    parser.add_argument(
        "--data-type", "-d",
        type=str,
        choices=list(DATA_TYPES.keys()),
        default="ts",
        help="Data type: ts (time series, default), normals_800, normals",
    )
    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=FORMATS,
        default="nc",
        help="File format for ts downloads (default: nc). Ignored for normals.",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="./raw/prism/",
        help="Output directory (default: ./raw/prism/)",
    )
    parser.add_argument(
        "--no-unzip",
        action="store_true",
        help="Keep downloaded zip files without extracting",
    )
    parser.add_argument(
        "--list-variables", "-l",
        action="store_true",
        help="List all available PRISM elements and exit",
    )

    args = parser.parse_args()

    if args.list_variables:
        list_variables()
        sys.exit(0)

    if not args.element or not args.time:
        parser.error("--element and --time are required unless using --list-variables")

    elements = [e.strip() for e in args.element.split(",")]
    times = [t.strip() for t in args.time.split(",")]

    print(f"PRISM Climate Data Download")
    print("=" * 50)
    print(f"  Module version : {__version__}")
    print(f"  Elements       : {', '.join(elements)}")
    print(f"  Times          : {', '.join(times)}")
    print(f"  Data type      : {args.data_type}  ({DATA_TYPES[args.data_type]})")
    if args.data_type == "ts":
        print(f"  Format         : {args.format}")
    print(f"  Output dir     : {args.output_dir}")
    print(f"  Unzip          : {not args.no_unzip}")

    results = download_prism(
        elements=elements,
        times=times,
        data_type=args.data_type,
        fmt=args.format,
        output_dir=args.output_dir,
        unzip=not args.no_unzip,
    )

    # Summary
    succeeded = sum(1 for v in results.values() if v is not None)
    failed = len(results) - succeeded
    print(f"\n{'='*50}")
    print(f"Download Summary:")
    print(f"  Total requested : {len(results)}")
    print(f"  Succeeded       : {succeeded}")
    print(f"  Failed          : {failed}")
    if failed > 0:
        print("  Failed items:")
        for (el, t), path in results.items():
            if path is None:
                print(f"    {el} / {t}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
