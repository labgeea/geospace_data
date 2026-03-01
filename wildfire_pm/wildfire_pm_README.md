# Wildfire Smoke Reanalysis Module

Module to download and process standardized daily wildfire smoke PM2.5 estimates.

## Dataset
- **Canonical Source**: Childs et al., 2022 (Stanford ECHO Lab)
- **Temporal Extent**: 2006 to 2020 (Daily)
- **Spatial Resolution**: 10km grid, county, ZCTA, and census tract levels.
- **Reference**: [Harvard Dataverse DOI: 10.7910/DVN/DJVMTV](https://doi.org/10.7910/DVN/DJVMTV)

## Description
This module extracts daily smoke PM2.5 concentrations (measured in µg/m³) based on statistical machine learning models fusing ground monitoring with NOAA HMS and satellite inputs. 

The original datasets omit non-smoke days to preserve storage space. The `wildfire_pm_process_generic.py` script automatically standardizes these sparsely-populated CSV files into fully fleshed out, dense Parquet arrays by taking the Cartesian product of all dates and regions within a specific year, back-filling non-smoke days with exactly 0.0 µg/m³ as instructed by the canonical dataset author README.

## Usage

### 1. Download Data
Use the generic download script to fetch the canonical CSV files from the Dataverse API:
```bash
# Download a specific geography (e.g. county)
./wildfire_pm_download_generic.sh --geography county --output-dir ./raw

# Download all available geographies (10km, county, tract, zcta)
./wildfire_pm_download_generic.sh --geography all --output-dir ./raw
```

### 2. Process Data
Convert the raw CSV subsets into partitioned Parquet files for fast structured querying downstream across the framework:
```bash
# Process county-level data into year-specific parquets
./wildfire_pm_process_generic.sh --geography county --input-dir ./raw --output-dir ./proc

# Process specific years only
./wildfire_pm_process_generic.sh --geography county --input-dir ./raw --output-dir ./proc --years 2018 2019 2020
```
