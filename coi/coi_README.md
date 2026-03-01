# COI Processing Framework

**Version:** 1.0.0
**Module:** COI (Child Opportunity Index)
**Last Updated:** January 2026
**Framework Compatibility:** GEOSPACE v1.5.0

This module processes Child Opportunity Index (COI) data by merging unified CSV attributes with Census Tract geometries to create spatially-enabled datasets (GeoPackage).

## Overview

The COI module links tabular COI data (covering multiple years) to 2020 Census Tract polygons (fetched via `pygris`) to facilitate spatial analysis.

## Supported Years

- All years present in the source CSV (typically 2012-2023 for COI 2.0+).

## Requirements

- **Python Environment**: `geospatial` (or equivalent with `geopandas`, `pygris`, `pandas` installed)
- **Data**: You must have the raw unified COI CSV file (e.g., `coi_tract_2k23.csv`). This can be downloaded from the [COI website](https://www.childopportunityindex.org/).

## Usage

```bash
./coi_process_generic.sh \
  --coi-data-file /path/to/coi_data.csv \
  --output-dir /path/to/output/ \
  --year 2020
```

### Arguments

- `--coi-data-file`: Path to the unified COI CSV file.
- `--output-dir`: Where to save the processed GeoPackage files.
- `--year`: (Optional) Specific year to process. If omitted, attempts to process all years found in the CSV.

## Output

The script generates `.gpkg` files (e.g., `COI_2020_Spatial.gpkg`) containing Census Tract polygons with COI attributes attached.

## Variables

Key variables included (names subject to version of COI data):
- `z_COI_nat`: Overall COI z-score (National)
- `c5_COI_nat`: Overall COI quintile (National)
- Domain specific scores (`ED`=Education, `HE`=Health/Environment, `SE`=Social/Economic)


Notes (for Zenodo metadata for COI upload):
COI - Child Opportunity Index (36 variables) Multi-scalar opportunity metrics including Z-scores, quintiles, and ranks for National, State, and Metro norms across Education, Health/Environment, and Social/Economic domains. 