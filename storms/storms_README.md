# NOAA Storm Events Module

**Version:** 1.0.0  
**Module:** STORMS  
**Last Updated:** January 2026  
**Framework Compatibility:** GEOSPACE v1.7.0+

This module downloads and processes the NOAA National Centers for Environmental Information (NCEI) Storm Events Database.

## Overview

The Storm Events Database contains records of significant weather phenomena having sufficient intensity to cause loss of life, injuries, significant property damage, and/or disruption to commerce.

### Data Source

- **Provider**: NOAA NCEI
- **URL**: [Storm Events Database CSV Files](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/)
- **Period**: 1950 - Present

## Usage

### Step 1: Download Data

Download the comprehensive "details" CSV for a specific year.

```bash
# Download 2023 data
./storms_download_generic.sh --year 2023 --output-dir ./data/storms/
```

### Step 2: Process Data

Clean the data, parse damage estimates ($K/M/B), and optionally filter or create a GeoPackage.

```bash
# Basic processing (CSV output)
./storms_process_generic.sh \
  --input-file ./data/storms/StormEvents_details-ftp_v1.0_d2023_c20260116.csv \
  --output-dir ./output/

# Filter by state and save as GeoPackage (points)
./storms_process_generic.sh \
  --input-file ./data/storms/StormEvents_details-ftp_v1.0_d2023_c20260116.csv \
  --output-dir ./output/ \
  --state TEXAS \
  --geo

# Filter by event type
./storms_process_generic.sh \
  --input-file ./data/storms/StormEvents_details-ftp_v1.0_d2023_c20260116.csv \
  --output-dir ./output/ \
  --event-types "Tornado,Hail"
```

## Generated Variables

| Variable | Description | Type |
|----------|-------------|------|
| `event_type` | Type of storm event (e.g., Flood, Tornado) | String |
| `begin_timestamp` | Event start time | Datetime |
| `begin_lat`/`lon` | Start location | Float |
| `damage_property_num`| Property damage in USD | Float |
| `damage_crops_num` | Crop damage in USD | Float |
| `deaths_direct` | Number of direct fatalities | Integer |
| `injuries_direct` | Number of direct injuries | Integer |
| `magnitude` | Magnitude (e.g., wind speed, hail size) | Float |
| `state` | State name | String |
| `cz_name` | County/Zone name | String |

## Notes

- **Spatial Coverage**: Events like Tornadoes and Hail usually have specific Lat/Lon coordinates. Broad events like Heat, Drought, or Winter Storms often lack specific coordinates and use Zone centroids or have N/A coordinates.
- **GeoPackage Output**: When using `--geo`, records without `begin_lat`/`begin_lon` are **dropped**. Use CSV output to retain all records.
