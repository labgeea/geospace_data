# FIRMS Processing Framework

**Version:** 1.0.0  
**Module:** FIRMS (Fire Information for Resource Management System)  
**Last Updated:** January 2026  
**Framework Compatibility:** GEOSPACE v1.6.0+

This module downloads and processes NASA FIRMS active fire data, providing satellite-detected fire locations and fire radiative power measurements.

## Overview

NASA FIRMS distributes near real-time and archived active fire data from multiple satellite instruments. This module supports downloading point-based fire detections and aggregating them to geographic units for exposure analysis.

### Data Source

- **Provider**: NASA Land, Atmosphere Near real-time Capability for EOS (LANCE)
- **Portal**: [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/)
- **API**: [FIRMS REST API](https://firms.modaps.eosdis.nasa.gov/api/)

### Sensors

| Sensor | Resolution | Coverage | Start Date |
|--------|------------|----------|------------|
| **MODIS** (Terra/Aqua) | 1 km | Global | Nov 2000 |
| **VIIRS S-NPP** | 375 m | Global | Jan 2012 |
| **VIIRS NOAA-20** | 375 m | Global | Apr 2018 |
| **VIIRS NOAA-21** | 375 m | Global | Jan 2024 |
| **Landsat** | 30 m | US/Canada only | Jun 2022 |

## Requirements

- **Python Environment**: `xarray-env` or equivalent with:
  - `pandas`, `geopandas`, `pygris`, `requests`
- **FIRMS MAP_KEY**: Free API key from [FIRMS API](https://firms.modaps.eosdis.nasa.gov/api/)
- **Internet Connection**: Required for data download and geometry fetching

## Usage

### Step 1: Get API Key

1. Visit https://firms.modaps.eosdis.nasa.gov/api/
2. Enter your email to receive a free MAP_KEY
3. Save the key for use with the download script

### Step 2: Download Data

```bash
# Download VIIRS data for California, August 2023
./firms_download_generic.sh \
  --map-key YOUR_MAP_KEY \
  --sensor VIIRS_SNPP_SP \
  --bbox california \
  --start-date 2023-08-01 \
  --end-date 2023-08-31 \
  --output-dir ./data/firms/

# Download MODIS data for CONUS, full year
./firms_download_generic.sh \
  --map-key YOUR_MAP_KEY \
  --sensor MODIS_SP \
  --bbox conus \
  --start-date 2023-01-01 \
  --end-date 2023-12-31 \
  --output-dir ./data/firms/
```

#### Download Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--map-key` | Yes | FIRMS API key |
| `--sensor` | Yes | Data source (see sensors table) |
| `--bbox` | Yes | Bounding box or preset (conus, california, world) |
| `--start-date` | Yes | Start date (YYYY-MM-DD) |
| `--end-date` | Yes | End date (YYYY-MM-DD) |
| `--output-dir` | Yes | Directory for output CSV |
| `--chunk-days` | No | Days per API request (default: 5, max: 10) |
| `--delay` | No | Seconds between requests (default: 1.0) |

#### Sensor Options

| Sensor Code | Description |
|-------------|-------------|
| `MODIS_NRT` | MODIS Near Real-Time (last ~7 days) |
| `MODIS_SP` | MODIS Standard Processing (historical, science quality) |
| `VIIRS_SNPP_NRT` | VIIRS S-NPP Near Real-Time |
| `VIIRS_SNPP_SP` | VIIRS S-NPP Standard Processing |
| `VIIRS_NOAA20_NRT` | VIIRS NOAA-20 Near Real-Time |
| `VIIRS_NOAA20_SP` | VIIRS NOAA-20 Standard Processing |
| `VIIRS_NOAA21_NRT` | VIIRS NOAA-21 Near Real-Time |
| `LANDSAT_NRT` | Landsat Near Real-Time (US/Canada only) |

#### Bounding Box Presets

| Preset | Coordinates (W,S,E,N) |
|--------|----------------------|
| `conus` | -125,24,-66,50 |
| `california` | -125,32,-114,42 |
| `world` | -180,-90,180,90 |

### Step 3: Process Data (Optional)

```bash
# Basic processing - clean and standardize
./firms_process_generic.sh \
  --input-file ./data/firms/FIRMS_VIIRS_SNPP_SP_20230801_to_20230831.csv \
  --output-dir ./output/

# Aggregate to county level with monthly totals
./firms_process_generic.sh \
  --input-file ./data/firms/FIRMS_VIIRS_SNPP_SP_20230801_to_20230831.csv \
  --output-dir ./output/ \
  --aggregation-level county \
  --temporal monthly \
  --with-geometry

# High-confidence fires only, aggregated to ZCTA
./firms_process_generic.sh \
  --input-file ./data/firms/FIRMS_VIIRS_SNPP_SP_20230801_to_20230831.csv \
  --output-dir ./output/ \
  --aggregation-level zcta \
  --temporal annual \
  --min-confidence 80 \
  --with-geometry
```

#### Processing Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--input-file` | Yes | Path to downloaded FIRMS CSV |
| `--output-dir` | Yes | Directory for output files |
| `--aggregation-level` | No | Spatial level: none, county, zcta, state |
| `--temporal` | No | Time level: none, daily, monthly, annual |
| `--with-geometry` | No | Output GeoPackage with polygons |
| `--min-confidence` | No | Minimum confidence (0-100) |

## Output

### Raw Download Format

| Column | Description |
|--------|-------------|
| `latitude` | Fire pixel center latitude |
| `longitude` | Fire pixel center longitude |
| `brightness` / `bright_ti4` | Brightness temperature (K) |
| `acq_date` | Acquisition date |
| `acq_time` | Acquisition time (UTC) |
| `satellite` | Terra, Aqua, S-NPP, NOAA-20, NOAA-21 |
| `instrument` | MODIS or VIIRS |
| `confidence` | Detection confidence (0-100 or low/nominal/high) |
| `frp` | Fire Radiative Power (MW) |
| `daynight` | D=Day, N=Night |

### Aggregated Output Variables

| Variable | Description |
|----------|-------------|
| `fire_count` | Number of fire detections |
| `frp_total` | Total Fire Radiative Power (MW) |
| `frp_mean` | Mean Fire Radiative Power (MW) |
| `frp_max` | Maximum Fire Radiative Power (MW) |
| `fire_days` | Number of unique days with detections |
| `high_conf_count` | Count of high-confidence (≥80) detections |

## Notes

- **NRT vs SP Data**: Near Real-Time (NRT) data is available within hours but only for recent dates (~7 days). Standard Processing (SP) data has a ~5 month lag but is science-quality processed.
- **Rate Limits**: API allows 5,000 requests per 10-minute interval. The download script includes automatic delays.
- **Fire Pixel Size**: MODIS pixels are 1km, VIIRS pixels are 375m. Multiple detections may represent the same fire.
- **Confidence**: VIIRS uses categorical (low/nominal/high); MODIS uses numeric (0-100). Processing script standardizes both.

## See Also

- [VARIABLE_CATALOG.md](../VARIABLE_CATALOG.md) - Full variable catalog
- [NASA FIRMS FAQ](https://www.earthdata.nasa.gov/data/tools/firms/faq)
- [MODIS Active Fire User Guide](https://modis-fire.umd.edu/files/MODIS_C6_Fire_User_Guide_C.pdf)
- [VIIRS Active Fire User Guide](https://viirsland.gsfc.nasa.gov/PDF/VIIRS_activefire_User_Guide.pdf)
