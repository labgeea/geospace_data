#!/usr/bin/env python3
"""
Harvard Super-Learned PM2.5 Components Processing Script
========================================================

Processes downloaded Harvard Dataverse PM2.5 component predictions
(gridded 50-m urban / 1-km non-urban from doi:10.7910/DVN/3H7DNP and
geography-aggregated from doi:10.7910/DVN/F6PQAA) into annual Parquet
files and optional GeoPackage (.gpkg) spatial files.

Author: GEOSPACE Project
License: Public Domain
"""

import sys
import os
import argparse
import logging
import zipfile
import tempfile
import subprocess
from pathlib import Path

# Setup GEOSPACE framework version mapping
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from version import get_module_version
    __version__ = get_module_version("pm25_components_harvard")
except ImportError:
    __version__ = "1.0.0"

__module__ = "PM2.5 Components (Harvard) Processing"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Processing configuration for all 15 PM2.5 chemical components
PM25_COMPONENT_CONFIG = {
    # Major components (ug/m3)
    "ec": {
        "name": "Elemental Carbon",
        "formula": "EC",
        "category": "major",
        "input_units": "ug/m3",
        "output_units": "ug/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 elemental carbon concentration",
        "aliases": ["elemental_carbon", "black_carbon", "bc"],
    },
    "nh4": {
        "name": "Ammonium",
        "formula": "NH4+",
        "category": "major",
        "input_units": "ug/m3",
        "output_units": "ug/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 ammonium ion concentration",
        "aliases": ["ammonium", "nh4_ion"],
    },
    "no3": {
        "name": "Nitrate",
        "formula": "NO3-",
        "category": "major",
        "input_units": "ug/m3",
        "output_units": "ug/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 nitrate ion concentration",
        "aliases": ["nitrate", "no3_ion"],
    },
    "oc": {
        "name": "Organic Carbon",
        "formula": "OC",
        "category": "major",
        "input_units": "ug/m3",
        "output_units": "ug/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 organic carbon concentration",
        "aliases": ["organic_carbon", "om", "organic_matter"],
    },
    "so4": {
        "name": "Sulfate",
        "formula": "SO4(2-)",
        "category": "major",
        "input_units": "ug/m3",
        "output_units": "ug/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 sulfate ion concentration",
        "aliases": ["sulfate", "sulphate", "so4_ion"],
    },
    # Trace elements (ng/m3)
    "br": {
        "name": "Bromine",
        "formula": "Br",
        "category": "trace",
        "input_units": "ng/m3",
        "output_units": "ng/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 bromine (bromium) concentration",
        "aliases": ["bromine", "bromium"],
    },
    "ca": {
        "name": "Calcium",
        "formula": "Ca",
        "category": "trace",
        "input_units": "ng/m3",
        "output_units": "ng/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 calcium concentration",
        "aliases": ["calcium"],
    },
    "cu": {
        "name": "Copper",
        "formula": "Cu",
        "category": "trace",
        "input_units": "ng/m3",
        "output_units": "ng/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 copper concentration",
        "aliases": ["copper"],
    },
    "fe": {
        "name": "Iron",
        "formula": "Fe",
        "category": "trace",
        "input_units": "ng/m3",
        "output_units": "ng/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 iron concentration",
        "aliases": ["iron"],
    },
    "k": {
        "name": "Potassium",
        "formula": "K",
        "category": "trace",
        "input_units": "ng/m3",
        "output_units": "ng/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 potassium concentration",
        "aliases": ["potassium"],
    },
    "ni": {
        "name": "Nickel",
        "formula": "Ni",
        "category": "trace",
        "input_units": "ng/m3",
        "output_units": "ng/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 nickel concentration",
        "aliases": ["nickel"],
    },
    "pb": {
        "name": "Lead",
        "formula": "Pb",
        "category": "trace",
        "input_units": "ng/m3",
        "output_units": "ng/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 lead concentration",
        "aliases": ["lead"],
    },
    "si": {
        "name": "Silicon",
        "formula": "Si",
        "category": "trace",
        "input_units": "ng/m3",
        "output_units": "ng/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 silicon concentration",
        "aliases": ["silicon"],
    },
    "v": {
        "name": "Vanadium",
        "formula": "V",
        "category": "trace",
        "input_units": "ng/m3",
        "output_units": "ng/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 vanadium concentration",
        "aliases": ["vanadium"],
    },
    "zn": {
        "name": "Zinc",
        "formula": "Zn",
        "category": "trace",
        "input_units": "ng/m3",
        "output_units": "ng/m3",
        "conversion": "none",
        "valid_min": 0.0,
        "description": "Annual mean ambient PM2.5 zinc concentration",
        "aliases": ["zinc"],
    },
}

VARIABLE_PACKAGES = {
    "major": ["ec", "nh4", "no3", "oc", "so4"],
    "trace": ["br", "ca", "cu", "fe", "k", "ni", "pb", "si", "v", "zn"],
    "all": [
        "ec", "nh4", "no3", "oc", "so4",
        "br", "ca", "cu", "fe", "k", "ni", "pb", "si", "v", "zn",
    ],
}

GEOGRAPHY_CONFIG = {
    "state": {
        "type": "census_bundle",
        "csv_prefix": "states",
        "zfill": 2,
        "description": "U.S. Census TIGER/Line States (2000 or 2010 boundaries)",
    },
    "county": {
        "type": "census_bundle",
        "csv_prefix": "counties",
        "zfill": 5,
        "description": "U.S. Census TIGER/Line Counties (2000 or 2010 boundaries)",
    },
    "tract": {
        "type": "census_bundle",
        "csv_prefix": "tracts",
        "zfill": 11,
        "description": "U.S. Census TIGER/Line Census Tracts (2000 or 2010 boundaries)",
    },
    "zcta": {
        "type": "census_bundle",
        "csv_prefix": "zctas",
        "zfill": 5,
        "description": "U.S. Census TIGER/Line ZIP Code Tabulation Areas (2000 or 2010 boundaries)",
    },
    "block_group": {
        "type": "census_bundle",
        "csv_prefix": "block-groups",
        "zfill": 12,
        "description": "U.S. Census TIGER/Line Block Groups (2000 or 2010 boundaries)",
    },
    "esri_zip": {
        "type": "esri_zip",
        "csv_prefix": "zip-code-areas",
        "zfill": 5,
        "description": "Annual TomTom / ESRI ZIP Code Areas (2000-2019)",
    },
    "block": {
        "type": "block",
        "csv_prefix": "blocks",
        "zfill": 15,
        "description": "U.S. Census TIGER/Line Census Blocks (2000 or 2010 boundaries)",
    },
    "grid_non_urban": {
        "type": "grid",
        "grid_tag": "non-urban",
        "resolution": "1km",
        "description": "1-km non-urban prediction grid by Census division (NE1-P9)",
    },
    "grid_urban": {
        "type": "grid",
        "grid_tag": "urban",
        "resolution": "50m",
        "description": "50-m urban prediction grid by Census division (NE1-P9)",
    },
}

CENSUS_REGIONS = ["NE1", "MA2", "ENC3", "WNC4", "SA5", "ESC6", "WSC7", "M8", "P9"]

CONUS_STATES = [
    "AL", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA",
    "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
    "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM",
    "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD",
    "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]


def resolve_variables(var_arg: str):
    """Resolve package names, aliases, or comma-separated variable codes."""
    alias_map = {}
    for code, meta in PM25_COMPONENT_CONFIG.items():
        alias_map[code] = code
        for alias in meta.get("aliases", []):
            alias_map[alias.lower()] = code

    tokens = [t.strip().lower() for t in var_arg.split(",") if t.strip()]
    resolved = []
    for tok in tokens:
        if tok in VARIABLE_PACKAGES:
            for v in VARIABLE_PACKAGES[tok]:
                if v not in resolved:
                    resolved.append(v)
        elif tok in alias_map:
            canon = alias_map[tok]
            if canon not in resolved:
                resolved.append(canon)
        else:
            raise ValueError(
                f"Unknown variable or package '{tok}'. Use --list-config to see valid options."
            )
    return resolved


def parse_years(years_arg):
    """Parse --years argument (supports space-separated or comma-separated integers/ranges)."""
    if not years_arg:
        return list(range(2000, 2020))
    years = []
    for item in years_arg:
        for part in str(item).split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                start_s, end_s = part.split("-", 1)
                for y in range(int(start_s), int(end_s) + 1):
                    if y not in years:
                        years.append(y)
            else:
                y = int(part)
                if y not in years:
                    years.append(y)
    for y in years:
        if y < 2000 or y > 2019:
            raise ValueError(f"Year {y} is outside valid dataset range (2000-2019).")
    return sorted(years)


def list_config():
    """Print variable configurations, packages, and geographies."""
    print(f"\n{__module__} v{__version__}")
    print("=" * 80)
    print("\nVariable Configurations (PM25_COMPONENT_CONFIG):")
    print("-" * 80)
    print(f"{'Code':<6} {'Name':<20} {'Formula':<10} {'Category':<8} {'Units':<8} {'Description'}")
    print("-" * 80)
    for code, cfg in PM25_COMPONENT_CONFIG.items():
        print(
            f"{code:<6} {cfg['name']:<20} {cfg['formula']:<10} "
            f"{cfg['category']:<8} {cfg['output_units']:<8} {cfg['description']}"
        )

    print("\nVariable Packages:")
    print("-" * 80)
    for pkg, members in VARIABLE_PACKAGES.items():
        print(f"  {pkg:<8} : {', '.join(members)}")

    print("\nGeography Configurations (GEOGRAPHY_CONFIG):")
    print("-" * 80)
    for gname, gcfg in GEOGRAPHY_CONFIG.items():
        print(f"  {gname:<16} : {gcfg['description']}")
    print()


def find_file(input_dir: Path, relative_candidates):
    """Find the first existing file among candidate relative paths under input_dir."""
    for rel in relative_candidates:
        cand = input_dir / rel
        if cand.exists():
            return cand
    return None


def find_zip_member(zf: zipfile.ZipFile, target_suffix: str):
    """Find a member in a ZipFile whose name ends with target_suffix (case-insensitive)."""
    target_lower = target_suffix.lower()
    for name in zf.namelist():
        if name.lower().endswith(target_lower):
            return name
    return None


def fetch_census_geometry(geo: str, boundary_year: str, df_ids=None):
    """Fetch Census TIGER/Line polygon geometries via pygris without reprojecting."""
    import pygris
    import pandas as pd

    yr = int(boundary_year)
    logger.info(f"Fetching {yr} Census TIGER/Line geometries for '{geo}' via pygris...")
    try:
        if geo == "state":
            gdf = pygris.states(cb=True, year=yr)
        elif geo == "county":
            gdf = pygris.counties(cb=True, year=yr)
        elif geo == "zcta":
            gdf = pygris.zctas(cb=True, year=yr)
        elif geo in ("tract", "block_group"):
            # Determine state FIPS codes present in the data (or CONUS states)
            state_fips = None
            if df_ids is not None and len(df_ids) > 0:
                state_fips = sorted({str(x)[:2] for x in df_ids if len(str(x)) >= 2})
            states_to_fetch = state_fips if state_fips else CONUS_STATES
            parts = []
            for st in states_to_fetch:
                try:
                    if geo == "tract":
                        part = pygris.tracts(state=st, cb=True, year=yr)
                    else:
                        part = pygris.block_groups(state=st, cb=True, year=yr)
                    parts.append(part)
                except Exception as e:
                    logger.warning(f"Could not fetch {geo} for state {st} ({yr}): {e}")
            gdf = pd.concat(parts, ignore_index=True) if parts else None
        else:
            logger.warning(f"Automatic pygris geometry fetch is not supported for '{geo}'.")
            return None
        return gdf
    except Exception as e:
        logger.warning(f"Failed to fetch geometry via pygris for {geo} ({yr}): {e}")
        return None


def export_census_gpkg(df_year, id_col: str, gdf, geo: str, out_gpkg: Path):
    """Merge annual DataFrame with Census GeoDataFrame and write GeoPackage."""
    if gdf is None or gdf.empty:
        return
    geom_id_col = None
    for cand in [
        id_col, "GEOID", "GEOID10", "GEOID00", "GEOID20",
        "ZCTA5CE10", "ZCTA5CE00", "ZCTA5CE20", "STATEFP10", "STATEFP00", "STATEFP", "FIPS",
    ]:
        if cand in gdf.columns:
            geom_id_col = cand
            break
    if not geom_id_col:
        logger.warning(f"Could not find matching GEOID column in pygris geometry (columns: {list(gdf.columns)})")
        return

    gdf_copy = gdf.copy()
    zfill_len = GEOGRAPHY_CONFIG[geo].get("zfill", 0)
    gdf_copy["_join_id"] = gdf_copy[geom_id_col].astype(str).str.zfill(zfill_len)
    df_copy = df_year.copy()
    df_copy["_join_id"] = df_copy[id_col].astype(str).str.zfill(zfill_len)

    merged = gdf_copy.merge(df_copy, on="_join_id", how="inner").drop(columns=["_join_id"])
    if merged.empty:
        logger.warning(f"No rows matched between {geo} data and geometry for {out_gpkg.name}.")
        return
    out_gpkg.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving GeoPackage {out_gpkg} ({len(merged)} features, CRS={merged.crs})...")
    merged.to_file(out_gpkg, driver="GPKG")


def process_census_bundle(geo: str, args, variables, years):
    """Process state, county, tract, zcta, or block_group from F6PQAA CSV bundle."""
    import pandas as pd
    import numpy as np

    cfg = GEOGRAPHY_CONFIG[geo]
    csv_name = f"{cfg['csv_prefix']}-{args.boundary_year}.csv"
    bundle_name = "block-groups-tracts-counties-states-zctas-2000-2010.zip"

    direct_csv = find_file(args.input_dir, [csv_name, f"aggregates-csv/{csv_name}"])
    bundle_zip = find_file(args.input_dir, [f"aggregates-csv/{bundle_name}", bundle_name])

    if direct_csv is not None:
        logger.info(f"Reading {direct_csv}...")
        header_df = pd.read_csv(direct_csv, nrows=1)
        id_col = header_df.columns[0]
        usecols = [id_col, "year"] + [v for v in variables if v in header_df.columns]
        dtype_map = {id_col: str, "year": np.int32}
        for v in variables:
            dtype_map[v] = np.float32
        df = pd.read_csv(direct_csv, usecols=usecols, dtype=dtype_map)
    elif bundle_zip is not None:
        logger.info(f"Reading {csv_name} from {bundle_zip}...")
        with zipfile.ZipFile(bundle_zip, "r") as zf:
            member = find_zip_member(zf, csv_name)
            if not member:
                logger.error(f"Could not find {csv_name} inside {bundle_zip}")
                sys.exit(1)
            with zf.open(member) as f_in:
                header_df = pd.read_csv(f_in, nrows=1)
                id_col = header_df.columns[0]
            usecols = [id_col, "year"] + [v for v in variables if v in header_df.columns]
            dtype_map = {id_col: str, "year": np.int32}
            for v in variables:
                dtype_map[v] = np.float32
            with zf.open(member) as f_in:
                df = pd.read_csv(f_in, usecols=usecols, dtype=dtype_map)
    else:
        logger.error(
            f"Could not find {csv_name} or {bundle_name} in {args.input_dir}. "
            f"Run pm25_components_download_generic.py --geography {geo} first."
        )
        sys.exit(1)

    zfill_len = cfg.get("zfill", 0)
    if zfill_len:
        df[id_col] = df[id_col].astype(str).str.zfill(zfill_len)

    want_parquet = args.output_format in ("parquet", "both")
    want_gpkg = args.output_format in ("gpkg", "both") or args.include_gpkg

    gdf = None
    if want_gpkg:
        gdf = fetch_census_geometry(geo, args.boundary_year, df_ids=df[id_col].unique())

    avail_years = sorted(df["year"].unique())
    target_years = [y for y in years if y in avail_years]
    logger.info(f"Processing {geo} ({args.boundary_year} boundaries) for {len(target_years)} year(s)...")

    for yr in target_years:
        df_yr = df[df["year"] == yr].copy()
        if want_parquet:
            out_pq = (
                args.output_dir
                / geo
                / f"pm25_components_{geo}_{args.boundary_year}_{yr}.parquet"
            )
            out_pq.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Saving {out_pq} ({len(df_yr)} rows)...")
            df_yr.to_parquet(out_pq, engine="pyarrow", index=False, compression="snappy")

        if want_gpkg and gdf is not None:
            out_gpkg = (
                args.output_dir
                / geo
                / f"pm25_components_{geo}_{args.boundary_year}_{yr}_Spatial.gpkg"
            )
            export_census_gpkg(df_yr, id_col, gdf, geo, out_gpkg)


def process_esri_zip(args, variables, years):
    """Process annual TomTom/ESRI ZIP code areas from esri-zip-codes-2000-to-2019.zip."""
    import pandas as pd
    import numpy as np

    bundle_name = "esri-zip-codes-2000-to-2019.zip"
    bundle_zip = find_file(args.input_dir, [f"aggregates-csv/{bundle_name}", bundle_name])
    if bundle_zip is None:
        logger.error(f"Could not find {bundle_name} in {args.input_dir}.")
        sys.exit(1)

    with zipfile.ZipFile(bundle_zip, "r") as zf:
        for yr in years:
            target_csv = f"zip-code-areas-{yr}.csv"
            member = find_zip_member(zf, target_csv)
            if not member:
                logger.warning(f"Member {target_csv} not found in {bundle_zip}; skipping {yr}.")
                continue
            with zf.open(member) as f_in:
                header_df = pd.read_csv(f_in, nrows=1)
                id_col = header_df.columns[0]
            has_year = "year" in header_df.columns
            usecols = ([id_col, "year"] if has_year else [id_col]) + [
                v for v in variables if v in header_df.columns
            ]
            dtype_map = {id_col: str}
            if has_year:
                dtype_map["year"] = np.int32
            for v in variables:
                dtype_map[v] = np.float32
            with zf.open(member) as f_in:
                df_yr = pd.read_csv(f_in, usecols=usecols, dtype=dtype_map)
            df_yr[id_col] = df_yr[id_col].astype(str).str.zfill(5)
            if not has_year:
                df_yr.insert(1, "year", np.int32(yr))

            out_pq = args.output_dir / "esri_zip" / f"pm25_components_esri_zip_{yr}.parquet"
            out_pq.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Saving {out_pq} ({len(df_yr)} rows)...")
            df_yr.to_parquet(out_pq, engine="pyarrow", index=False, compression="snappy")


def process_block(args, variables, years):
    """Process Census block predictions from aggregates-csv/blocks-<boundary_year>/<var>.csv.zip."""
    import pandas as pd
    import numpy as np

    byr = args.boundary_year
    for yr in years:
        merged_df = None
        id_col = None
        for var in variables:
            zip_cand = find_file(
                args.input_dir,
                [f"aggregates-csv/blocks-{byr}/{var}.csv.zip", f"blocks-{byr}/{var}.csv.zip", f"{var}.csv.zip"],
            )
            if zip_cand is None:
                logger.error(f"Missing block archive for '{var}' ({byr}) in {args.input_dir}.")
                sys.exit(1)
            with zipfile.ZipFile(zip_cand, "r") as zf:
                csv_members = [m for m in zf.namelist() if m.endswith(".csv")]
                if not csv_members:
                    logger.error(f"No CSV member inside {zip_cand}")
                    sys.exit(1)
                member = csv_members[0]
                with zf.open(member) as f_in:
                    header_df = pd.read_csv(f_in, nrows=1)
                    id_col = header_df.columns[0]
                chunks = []
                with zf.open(member) as f_in:
                    for chunk in pd.read_csv(
                        f_in,
                        dtype={id_col: str, "year": np.int32, var: np.float32},
                        chunksize=2_000_000,
                    ):
                        sub = chunk[chunk["year"] == yr]
                        if not sub.empty:
                            chunks.append(sub)
                df_var = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=[id_col, "year", var])
            if merged_df is None:
                merged_df = df_var
            else:
                merged_df = merged_df.merge(df_var, on=[id_col, "year"], how="outer")

        if merged_df is not None and not merged_df.empty:
            out_pq = args.output_dir / "block" / f"pm25_components_block_{byr}_{yr}.parquet"
            out_pq.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Saving {out_pq} ({len(merged_df)} rows)...")
            merged_df.to_parquet(out_pq, engine="pyarrow", index=False, compression="snappy")


def read_rds_vector_from_bytes(raw_bytes: bytes):
    """Read a 1D numeric vector from an R .rds file using pyreadr or Rscript fallback."""
    import numpy as np

    with tempfile.NamedTemporaryFile(suffix=".rds", delete=False) as tmp:
        tmp.write(raw_bytes)
        tmp_path = tmp.name

    try:
        try:
            import pyreadr
            res = pyreadr.read_r(tmp_path)
            first_obj = next(iter(res.values()))
            return np.asarray(first_obj).ravel().astype(np.float32)
        except ImportError:
            pass

        # Fallback to Rscript if pyreadr is not installed
        out_txt = tmp_path + ".txt"
        cmd = [
            "Rscript", "-e",
            f"x <- readRDS('{tmp_path}'); write(as.numeric(x), file='{out_txt}', ncolumns=1)"
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        vec = np.loadtxt(out_txt, dtype=np.float32)
        if os.path.exists(out_txt):
            os.remove(out_txt)
        return vec
    except Exception as e:
        raise RuntimeError(
            f"Reading M8 non-urban .rds files requires 'pyreadr' (pip install pyreadr) or Rscript: {e}"
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def read_grid_vector(input_dir: Path, reg: str, grid_tag: str, var: str, year: int):
    """Read the 1D prediction vector for (region, grid_tag, variable, year)."""
    import numpy as np

    dat_suffix = f"{reg}-{grid_tag}-{var}-{year}.dat"
    rds_suffix = f"{reg}-{grid_tag}-{var}-{year}.rds"

    if grid_tag == "non-urban":
        dat_zip = find_file(input_dir, [f"non-urban-dat/{reg}.zip", f"{reg}.zip"])
        if dat_zip is not None:
            with zipfile.ZipFile(dat_zip, "r") as zf:
                member = find_zip_member(zf, dat_suffix)
                if not member:
                    raise FileNotFoundError(f"Member *{dat_suffix} not found in {dat_zip}")
                raw = zf.read(member)
                return np.fromstring(raw.decode("ascii"), dtype=np.float32, sep="\n")

        if reg == "M8":
            cat = PM25_COMPONENT_CONFIG[var]["category"]
            rds_zip_name = "M8-major-components.zip" if cat == "major" else "M8-trace-elements.zip"
            rds_zip = find_file(input_dir, [f"non-urban-rds/{rds_zip_name}", rds_zip_name])
            if rds_zip is not None:
                with zipfile.ZipFile(rds_zip, "r") as zf:
                    member = find_zip_member(zf, rds_suffix)
                    if not member:
                        raise FileNotFoundError(f"Member *{rds_suffix} not found in {rds_zip}")
                    return read_rds_vector_from_bytes(zf.read(member))

        raise FileNotFoundError(
            f"Could not find non-urban archive for region {reg} in {input_dir}."
        )
    else:
        var_zip = find_file(input_dir, [f"urban-dat/{reg}/{var}.zip", f"{reg}/{var}.zip", f"{var}.zip"])
        if var_zip is None:
            raise FileNotFoundError(
                f"Could not find urban archive urban-dat/{reg}/{var}.zip in {input_dir}."
            )
        with zipfile.ZipFile(var_zip, "r") as zf:
            member = find_zip_member(zf, dat_suffix)
            if not member:
                raise FileNotFoundError(f"Member *{dat_suffix} not found in {var_zip}")
            raw = zf.read(member)
            return np.fromstring(raw.decode("ascii"), dtype=np.float32, sep="\n")


def process_grid(geo: str, args, variables, years):
    """Process 1-km non-urban or 50-m urban gridded predictions and join with grid coordinates."""
    import pandas as pd
    import numpy as np

    grid_tag = GEOGRAPHY_CONFIG[geo]["grid_tag"]
    if args.region and args.region.lower() != "all":
        regions = [r.strip().upper() for r in args.region.split(",") if r.strip()]
    else:
        # Auto-detect regions that have grid CSVs present in input_dir
        regions = [
            reg for reg in CENSUS_REGIONS
            if find_file(args.input_dir, [f"grids/{reg}-{grid_tag}.csv", f"{reg}-{grid_tag}.csv"]) is not None
        ]
        if not regions:
            logger.error(
                f"No grid CSV files (*-{grid_tag}.csv) found in {args.input_dir}. "
                f"Run pm25_components_download_generic.py --geography {geo} first."
            )
            sys.exit(1)

    want_parquet = args.output_format in ("parquet", "both")
    want_gpkg = args.output_format in ("gpkg", "both") or args.include_gpkg

    for reg in regions:
        grid_csv = find_file(args.input_dir, [f"grids/{reg}-{grid_tag}.csv", f"{reg}-{grid_tag}.csv"])
        if grid_csv is None:
            logger.error(f"Grid file grids/{reg}-{grid_tag}.csv not found in {args.input_dir}.")
            sys.exit(1)

        logger.info(f"Loading grid coordinates from {grid_csv}...")
        grid_df = pd.read_csv(
            grid_csv,
            dtype={"idx": np.int32, "lon": np.float32, "lat": np.float32},
        )
        n_pts = len(grid_df)
        logger.info(f"Loaded {n_pts:,} grid points for {reg} ({grid_tag}).")

        for yr in years:
            df_yr = grid_df.copy()
            df_yr["year"] = np.int32(yr)

            for var in variables:
                vec = read_grid_vector(args.input_dir, reg, grid_tag, var, yr)
                if len(vec) != n_pts:
                    raise ValueError(
                        f"Length mismatch for {reg} {grid_tag} {var} {yr}: "
                        f"expected {n_pts} points from {grid_csv.name}, got {len(vec)} values."
                    )
                df_yr[var] = vec

            if want_parquet:
                out_pq = (
                    args.output_dir
                    / geo
                    / reg
                    / f"pm25_components_{geo}_{reg}_{yr}.parquet"
                )
                out_pq.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Saving {out_pq} ({len(df_yr):,} rows)...")
                df_yr.to_parquet(out_pq, engine="pyarrow", index=False, compression="snappy")

            if want_gpkg:
                import geopandas as gpd

                out_gpkg = (
                    args.output_dir
                    / geo
                    / reg
                    / f"pm25_components_{geo}_{reg}_{yr}_Spatial.gpkg"
                )
                out_gpkg.parent.mkdir(parents=True, exist_ok=True)
                gdf = gpd.GeoDataFrame(
                    df_yr,
                    geometry=gpd.points_from_xy(df_yr["lon"], df_yr["lat"]),
                    crs="EPSG:4326",
                )
                logger.info(f"Saving GeoPackage {out_gpkg} ({len(gdf):,} features, CRS=EPSG:4326)...")
                gdf.to_file(out_gpkg, driver="GPKG")


def create_parser():
    parser = argparse.ArgumentParser(
        description=f"{__module__} Framework v{__version__} - Process Harvard Super-Learned PM2.5 Components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all 15 component variable configurations and geographies
  python3 pm25_components_process_generic.py --list-config

  # Process county-level predictions for 2010-2019 to Parquet
  python3 pm25_components_process_generic.py --input-dir ./data/raw/pm25_components_harvard --output-dir ./data/proc/pm25_components_harvard --geography county --years 2010-2019

  # Process county-level predictions for 2015 with both Parquet and GeoPackage outputs
  python3 pm25_components_process_generic.py --input-dir ./data/raw/pm25_components_harvard --output-dir ./data/proc/pm25_components_harvard --geography county --years 2015 --output-format both

  # Process 1-km non-urban grid for New England (NE1) for 2010
  python3 pm25_components_process_generic.py --input-dir ./data/raw/pm25_components_harvard --output-dir ./data/proc/pm25_components_harvard --geography grid_non_urban --region NE1 --years 2010
        """,
    )

    parser.add_argument("--version", "-V", action="version", version=f"{__module__} v{__version__}")
    parser.add_argument(
        "--list-config", action="store_true",
        help="List all variable configurations, packages, and geographies and exit"
    )
    parser.add_argument(
        "--input-dir", "-i", type=Path,
        help="Input directory containing downloaded files from pm25_components_download_generic.py"
    )
    parser.add_argument(
        "--output-dir", "-o", type=Path, default=Path("./data/proc/pm25_components_harvard"),
        help="Output directory for processed Parquet / GeoPackage files"
    )
    parser.add_argument(
        "--geography", "-g",
        choices=list(GEOGRAPHY_CONFIG.keys()) + ["all_aggregated"],
        default="county",
        help="Spatial geography to process (default: county)"
    )
    parser.add_argument(
        "--variables", "-v", default="all",
        help="Variables to process: 'all', 'major', 'trace', or comma-separated list (default: all)"
    )
    parser.add_argument(
        "--years", "-y", nargs="+",
        help="Specific years or range (e.g. 2010 2015 or 2010-2019; default: all 2000-2019)"
    )
    parser.add_argument(
        "--region", "-r", default="all",
        help="Census division(s) for grid_non_urban / grid_urban (default: all available in --input-dir)"
    )
    parser.add_argument(
        "--boundary-year", "-b", choices=["2000", "2010"], default="2010",
        help="Census TIGER/Line boundary vintage for aggregated Census geographies (default: 2010)"
    )
    parser.add_argument(
        "--output-format", "-f", choices=["parquet", "gpkg", "both"], default="parquet",
        help="Output format: parquet, gpkg, or both (default: parquet)"
    )
    parser.add_argument(
        "--include-gpkg", action="store_true",
        help="Also export GeoPackage (.gpkg) spatial files alongside Parquet"
    )

    return parser


def check_dependencies(need_gpkg: bool = False):
    missing = []
    for pkg in ("pandas", "numpy", "pyarrow"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if need_gpkg:
        for pkg in ("geopandas",):
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
    if missing:
        logger.error(f"Missing required Python packages: {', '.join(missing)}")
        logger.error("Activate the environment first (e.g., conda activate xarray-env).")
        sys.exit(1)


def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.list_config:
        list_config()
        sys.exit(0)

    if args.input_dir is None:
        parser.error("--input-dir / -i is required unless --list-config is specified.")
    if not args.input_dir.exists():
        logger.error(f"Input directory does not exist: {args.input_dir}")
        sys.exit(1)

    try:
        variables = resolve_variables(args.variables)
        years = parse_years(args.years)
    except ValueError as err:
        logger.error(str(err))
        sys.exit(1)

    need_gpkg = args.output_format in ("gpkg", "both") or args.include_gpkg
    check_dependencies(need_gpkg=need_gpkg)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting {__module__} v{__version__}")
    logger.info(f"Input Directory: {args.input_dir.resolve()}")
    logger.info(f"Output Directory: {args.output_dir.resolve()}")
    logger.info(f"Geography: {args.geography}")
    logger.info(f"Variables ({len(variables)}): {', '.join(variables)}")
    logger.info(f"Years ({len(years)}): {years[0]}..{years[-1]}" if len(years) > 1 else f"Year: {years[0]}")

    geos = (
        ["state", "county", "tract", "zcta", "block_group", "esri_zip"]
        if args.geography == "all_aggregated"
        else [args.geography]
    )

    for geo in geos:
        gtype = GEOGRAPHY_CONFIG[geo]["type"]
        if gtype == "census_bundle":
            process_census_bundle(geo, args, variables, years)
        elif gtype == "esri_zip":
            process_esri_zip(args, variables, years)
        elif gtype == "block":
            process_block(args, variables, years)
        elif gtype == "grid":
            process_grid(geo, args, variables, years)

    logger.info("Processing completed successfully.")


if __name__ == "__main__":
    main()

