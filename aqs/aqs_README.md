# EPA AQS Processing Framework

A framework for downloading and processing EPA AQS (Air Quality System) criteria air pollutant data for Continental United States (CONUS) analysis.

## Overview

This framework provides end-to-end processing of EPA AQS data from download through analysis-ready outputs:

- **Download**: Automated downloading from EPA AQS API with geographic filtering
- **Processing**: Convert JSON files to analysis-ready CSV with quality control and standardization
- **Variables**: Support for all NAAQS criteria pollutants (PM2.5, PM10, Ozone, NO2, SO2, CO, Lead)

## Quick Start

### 1. Setup

```bash
# Set up EPA AQS API credentials
export EPA_AQS_EMAIL=your_email@example.com
export EPA_AQS_KEY=your_api_key

# Install Python dependencies
pip install requests pandas numpy geopandas
```

Get EPA AQS API credentials: https://aqs.epa.gov/aqsweb/documents/data_api.html#signup

### 2. Download EPA AQS Data

```bash
# Download PM2.5 data for Los Angeles County
./aqs_download_generic.sh --variables PM25 --year 2023 --state CA --county 037 --output-dir ./data/raw/AQS/

# Download all criteria pollutants for a county
./aqs_download_generic.sh --variables criteria --year 2023 --state CA --county 037 --output-dir ./data/raw/AQS/

# List available variables
./aqs_download_generic.sh --list-variables
```

### 3. Process Data

```bash
# Process all downloaded files
./aqs_process_generic.sh --input-dir ./data/raw/AQS/ --output-dir ./data/processed/AQS/ --output-formats csv

# Process specific pollutants with spatial output
./aqs_process_generic.sh --input-dir ./data/raw/AQS/ --output-dir ./data/processed/AQS/ --variables PM25,Ozone --output-formats csv,geojson
```

## Framework Components

### Download Scripts

- **`aqs_download_generic.py`** - Python download engine with EPA AQS API integration
- **`aqs_download_generic.sh`** - Bash wrapper with argument parsing

### Processing Scripts  

- **`aqs_process_generic.py`** - Python processing engine with quality control
- **`aqs_process_generic.sh`** - Bash wrapper with output format options

## Supported Variables

### Criteria Air Pollutants (NAAQS)

- **PM25** - PM2.5 mass concentration (μg/m³)
- **PM10** - PM10 mass concentration (μg/m³)
- **Ozone** - Ground-level ozone (ppm)
- **NO2** - Nitrogen dioxide (ppb)
- **SO2** - Sulfur dioxide (ppb)
- **CO** - Carbon monoxide (ppm)
- **Pb** - Lead (μg/m³)

### Variable Packages

- **criteria** - All criteria pollutants
- **pm** - PM2.5 and PM10
- **gases** - CO, NO2, Ozone, SO2
- **all** - All available pollutants

## Usage Examples

### Download Examples

```bash
# Download PM data for California counties (state-level often times out)
./aqs_download_generic.sh -v pm -y 2023 -s CA -c 037  # Los Angeles
./aqs_download_generic.sh -v pm -y 2023 -s CA -c 059  # Orange
./aqs_download_generic.sh -v pm -y 2023 -s CA -c 073  # San Diego

# Download ozone data for specific monitoring site
./aqs_download_generic.sh -v Ozone -y 2023 -s TX -c 201 --site 0024

# Download annual data instead of daily
./aqs_download_generic.sh -v PM25 -y 2023 -s CA -c 037 --data-type annual
```

### Processing Examples

```bash
# Basic CSV processing
./aqs_process_generic.sh -d ./data/raw/AQS/ -o ./data/processed/AQS/

# Process specific variables with spatial output
./aqs_process_generic.sh -d ./data/raw/AQS/ -o ./data/processed/AQS/ -v PM25,Ozone -f csv,geojson

# Process single file
./aqs_process_generic.sh -i aqs_pm25_daily_2023_state06_county037.json -o ./processed/
```

## Geographic Filtering

EPA AQS API supports three levels of geographic filtering:

- **State-level**: `--state CA`
- **County-level**: `--state CA --county 037`
- **Site-level**: `--state CA --county 037 --site 1103`

**Note**: State-level requests often timeout due to large dataset sizes. County-level requests are more reliable.

## Output Format

### Download Output

- **JSON files**: EPA AQS API response format
- **Naming**: `aqs_{pollutant}_{data_type}_{year}_state{XX}_county{XXX}.json`

### Processing Output

- **CSV files**: Analysis-ready tabular format with standardized columns
- **GeoJSON files**: Spatial data for mapping and GIS analysis (optional)
- **Summary files**: JSON files with dataset statistics and metadata

### CSV Column Structure

- **site_id** - 9-digit site identifier (state+county+site)
- **date_local** - Local date of measurement
- **value** - Pollutant concentration (standardized units)
- **latitude, longitude** - WGS84 coordinates
- **state_name, county_name** - Geographic names
- **parameter_code, parameter_name** - Pollutant identifiers
- **qc_flag** - Quality control flags

## License

Public Domain

---

*Version: 1.0*  
*Framework: GEOSPACE v1.3.0*  
*Validated with EPA AQS API data*