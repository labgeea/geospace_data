#!/usr/bin/env python3
"""
PLACES Data Download Script
===========================

This script downloads CDC PLACES data from the Socrata Open Data API.
It supports bulk CSV downloads for all available release years (2020-2025)
at four geographic levels: county, place, census tract, and ZCTA.

IMPORTANT: Release Year vs. Data Year
    The --year argument selects the CDC PLACES *release* year, NOT the
    underlying BRFSS survey data year. The 'Year' column in downloaded CSVs
    reflects the BRFSS data vintage, which typically lags 2-4 years behind
    the release. For example:
        - PLACES 2025 release contains data from BRFSS 2022-2023
        - PLACES 2024 release contains data from BRFSS 2021-2022
        - PLACES 2023 release contains data from BRFSS 2020-2021
        - PLACES 2022 release contains data from BRFSS 2019-2020
        - PLACES 2021 release contains data from BRFSS 2018-2019
        - PLACES 2020 release contains data from BRFSS 2017-2018

Usage:
    python places_download_generic.py --year 2024 --output-dir ./data/places/
    python places_download_generic.py --year 2025 --geo-level zcta --output-dir ./data/
    python places_download_generic.py --year 2023 --geo-level county --output-dir ./data/
"""

import sys
import os
import argparse
from pathlib import Path
import requests

# Version information
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from version import get_module_version
    __version__ = get_module_version("places")
except ImportError:
    __version__ = "1.0.0"

__module__ = "PLACES Download"

# Supported geographic levels
GEO_LEVELS = ["county", "place", "tract", "zcta"]

# Socrata dataset IDs keyed by (release_year, geo_level).
# Verified against the Socrata Discovery API (February 2025).
# Note: Release year != data year. The 'Year' column in the CSV reflects
# the BRFSS survey vintage, which lags 2-4 years behind the release.
DATASET_IDS = {
    # 2025 release (BRFSS 2022-2023)
    (2025, "county"): "swc5-untb",
    (2025, "place"):  "eav7-hnsx",
    (2025, "tract"):  "cwsq-ngmh",
    (2025, "zcta"):   "qnzd-25i4",
    # 2024 release (BRFSS 2021-2022) — no ZCTA dataset available
    (2024, "county"): "fu4u-a9bh",
    (2024, "place"):  "sd8v-uq83",
    (2024, "tract"):  "ai6z-tcin",
    # (2024, "zcta"): not available
    # 2023 release (BRFSS 2020-2021)
    (2023, "county"): "h3ej-a9ec",
    (2023, "place"):  "krqc-563j",
    (2023, "tract"):  "em5e-5hvn",
    (2023, "zcta"):   "9umn-c3jf",
    # 2022 release (BRFSS 2019-2020)
    (2022, "county"): "duw2-7jbt",
    (2022, "place"):  "epbn-9bv3",
    (2022, "tract"):  "nw2y-v4gm",
    (2022, "zcta"):   "gd4x-jyhw",
    # 2021 release (BRFSS 2018-2019)
    (2021, "county"): "pqpp-u99h",
    (2021, "place"):  "q8ig-wwk9",
    (2021, "tract"):  "373s-ayzu",
    (2021, "zcta"):   "s85h-9xpy",
    # 2020 release (BRFSS 2017-2018)
    (2020, "county"): "dv4u-3x3q",
    (2020, "place"):  "q8xq-ygsk",
    (2020, "tract"):  "4ai3-zynv",
    (2020, "zcta"):   "fbbf-hgkc",
}

# Derived constants
SUPPORTED_YEARS = sorted({year for year, _ in DATASET_IDS})

GEO_LEVEL_LABELS = {
    "county": "County",
    "place":  "Place (City/Town)",
    "tract":  "Census Tract",
    "zcta":   "ZCTA",
}


def get_available_geo_levels(year: int) -> list:
    """Return geo levels available for a given release year."""
    return [geo for (y, geo) in DATASET_IDS if y == year]


def check_dependencies():
    """Check for required dependencies."""
    missing = []
    try:
        import requests
    except ImportError:
        missing.append("requests")
    try:
        import pandas
    except ImportError:
        missing.append("pandas")

    if missing:
        print(f"Error: Missing required packages: {', '.join(missing)}")
        print("Please install them using: pip install " + " ".join(missing))
        sys.exit(1)


def create_parser():
    """Create argument parser."""
    # Build availability summary for help text
    avail_lines = []
    for year in SUPPORTED_YEARS:
        levels = get_available_geo_levels(year)
        avail_lines.append(f"    {year}: {', '.join(levels)}")
    avail_text = "\n".join(avail_lines)

    parser = argparse.ArgumentParser(
        description=f'{__module__} v{__version__} - Download CDC PLACES Data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Download 2025 ZCTA data (default geo level)
  python places_download_generic.py --year 2025 --output-dir ./data/

  # Download 2024 county data
  python places_download_generic.py --year 2024 --geo-level county --output-dir ./data/

  # Download 2023 census tract data
  python places_download_generic.py --year 2023 --geo-level tract --output-dir ./data/

Available year + geo-level combinations:
{avail_text}

Note: Release year != data year. The 'Year' column in the CSV reflects the
BRFSS survey data vintage, which lags 2-4 years behind the release.
        """
    )

    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--year', type=int, required=True,
                        choices=SUPPORTED_YEARS,
                        help=f'Release year ({min(SUPPORTED_YEARS)}-{max(SUPPORTED_YEARS)})')
    parser.add_argument('--geo-level', default='zcta', choices=GEO_LEVELS,
                        help='Geographic level: county, place, tract, zcta (default: zcta)')
    parser.add_argument('--output-dir', required=True,
                        help='Directory to save downloaded CSV files')
    parser.add_argument('--force', action='store_true',
                        help='Overwrite existing files')

    return parser


def get_download_url(year: int, geo_level: str) -> str:
    """
    Construct the download URL for a given year and geographic level.

    Args:
        year: Release year
        geo_level: Geographic level (county, place, tract, zcta)

    Returns:
        Download URL string
    """
    dataset_id = DATASET_IDS.get((year, geo_level))
    if not dataset_id:
        available = get_available_geo_levels(year)
        raise ValueError(
            f"No dataset available for {GEO_LEVEL_LABELS[geo_level]} in "
            f"{year} release. Available levels for {year}: {', '.join(available)}"
        )

    url = f"https://data.cdc.gov/api/views/{dataset_id}/rows.csv?accessType=DOWNLOAD"
    return url


def download_places_data(year: int, geo_level: str, output_dir: str,
                         force: bool = False) -> str:
    """
    Download PLACES data for a given year and geographic level.

    Args:
        year: Release year
        geo_level: Geographic level (county, place, tract, zcta)
        output_dir: Directory to save the file
        force: Overwrite existing files

    Returns:
        Path to downloaded file
    """
    import pandas as pd

    dataset_id = DATASET_IDS.get((year, geo_level))
    if not dataset_id:
        available = get_available_geo_levels(year)
        print(f"  Error: No {GEO_LEVEL_LABELS[geo_level]} dataset for {year} release.")
        print(f"  Available geo levels for {year}: {', '.join(available)}")
        sys.exit(1)

    # Construct output filename
    output_filename = f"places_{geo_level}_{year}.csv"
    output_path = os.path.join(output_dir, output_filename)

    # Check if file exists
    if os.path.exists(output_path) and not force:
        print(f"  File already exists: {output_path}")
        print("  Use --force to overwrite")
        return output_path

    # Get download URL
    url = get_download_url(year, geo_level)

    print(f"  Downloading from: data.cdc.gov (dataset: {dataset_id})")
    print(f"  Geographic level: {GEO_LEVEL_LABELS[geo_level]}")
    print(f"  Note: Release year ({year}) differs from BRFSS data year in CSV")
    print(f"  This may take a few minutes for large files...")

    try:
        # Stream download for large files
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        # Get content length if available
        total_size = int(response.headers.get('content-length', 0))

        # Write to file with progress
        downloaded = 0
        chunk_size = 8192

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        print(f"\r  Progress: {pct:.1f}% ({downloaded / 1024 / 1024:.1f} MB)", end='')

        print()  # Newline after progress

        # Verify the download
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"  Downloaded: {output_path} ({file_size / 1024 / 1024:.1f} MB)")

            # Quick validation - read first few rows
            try:
                df = pd.read_csv(output_path, nrows=5)
                print(f"  Columns: {len(df.columns)}")
                print(f"  Sample columns: {', '.join(df.columns[:5])}...")
            except Exception as e:
                print(f"  Warning: Could not validate CSV: {e}")

        return output_path

    except requests.exceptions.RequestException as e:
        print(f"  Error downloading data: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)  # Clean up partial download
        sys.exit(1)


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    check_dependencies()

    geo_label = GEO_LEVEL_LABELS[args.geo_level]

    print(f"\n{'='*60}")
    print(f"  {__module__} v{__version__}")
    print(f"  CDC PLACES Data Downloader")
    print(f"{'='*60}\n")

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"=== Downloading PLACES {args.year} {geo_label} Data ===")

    # Download the data
    output_file = download_places_data(
        year=args.year,
        geo_level=args.geo_level,
        output_dir=args.output_dir,
        force=args.force
    )

    print(f"\n=== Download Complete ===")
    print(f"  Output: {output_file}")
    print(f"\nNext step: Process with places_process_generic.py")


if __name__ == "__main__":
    main()
