# SVI Processing Framework

**Version:** 1.0.0
**Module:** SVI (Social Vulnerability Index)
**Last Updated:** January 2026
**Framework Compatibility:** GEOSPACE v1.5.0

This module processes Social Vulnerability Index (SVI) data by merging CSV attributes with Census Tract geometries to create spatially-enabled datasets (GeoPackage).

## Overview

The SVI module links tabular SVI data to 2021 Census Tract polygons (fetched via `pygris`) to facilitate spatial analysis.

## Supported Years

- 2000, 2010, 2014, 2016, 2018, 2020, 2022

## Requirements

- **Python Environment**: `geospatial` (or equivalent with `geopandas`, `pygris`, `pandas` installed)
- **Data**: You must have the raw SVI CSV files (e.g., `SVI_2020_US.csv`) available in a directory. This can be downloaded from the [SVI website](https://www.svi.umd.edu/).

## Usage

```bash
./svi_process_generic.sh \
  --svi-data-dir /path/to/svi_raw_data/ \
  --output-dir /path/to/output/ \
  --year 2020
```

### Arguments

- `--svi-data-dir`: Directory containing downloaded SVI CSV files.
- `--output-dir`: Where to save the processed GeoPackage files.
- `--year`: (Optional) Specific year to process. If omitted, attempts to process all supported years found in the data directory.

## Output

The script generates `.gpkg` files (e.g., `SVI_2020_Spatial.gpkg`) containing Census Tract polygons with SVI attributes attached.

## Standardized Variables

The script maps SVI variables to standardized names (e.g., `SPL_THEMES` -> `overall_score`, `RPL_THEMES` -> `overall_rank`). See `VARIABLE_CATALOG.md` for full list.
