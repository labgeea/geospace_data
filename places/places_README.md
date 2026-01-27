# PLACES Processing Framework

**Version:** 1.0.0  
**Module:** PLACES (Population Level Analysis and Community Estimates)  
**Last Updated:** January 2026  
**Framework Compatibility:** GEOSPACE v1.5.0+

This module downloads and processes CDC PLACES data by merging health outcome estimates with ZCTA (ZIP Code Tabulation Area) geometries to create spatially-enabled datasets (GeoPackage).

## Overview

The PLACES module provides small-area estimates for chronic disease measures, health risk behaviors, prevention practices, and social determinants of health. Data is available at the ZCTA level for the entire United States.

### Data Source

- **Provider**: Centers for Disease Control and Prevention (CDC)
- **Portal**: [CDC PLACES Data Portal](https://www.cdc.gov/places/tools/data-portal.html)
- **API**: [Socrata Open Data API](https://data.cdc.gov/browse?category=500+Cities+%26+Places)

## Supported Years

- 2020, 2021, 2022, 2023, 2024, 2025

## Measure Categories

| Category | Description | Example Measures |
|----------|-------------|------------------|
| **Health Outcomes** | Chronic disease prevalence | Arthritis, asthma, diabetes, obesity, stroke |
| **Prevention** | Preventive service utilization | Dental visits, cancer screenings, checkups |
| **Health Risk Behaviors** | Behavioral risk factors | Smoking, binge drinking, physical inactivity |
| **Disabilities** | Disability prevalence | Cognitive, mobility, vision, hearing |
| **Health Status** | General health indicators | Poor health, mental/physical distress |
| **Health-Related Social Needs** | Social vulnerability | Food/housing insecurity, transportation barriers |

## Requirements

- **Python Environment**: `geospatial` or equivalent with:
  - `pandas`, `geopandas`, `pygris`, `requests`
  - `pyogrio` or `fiona` (for reading shapefiles)
- **Internet Connection**: Required for data download and geometry fetching

## Usage

### Step 1: Download Data

```bash
# Download 2024 data
./places_download_generic.sh --year 2024 --output-dir ./data/places/

# Download all available years
for year in 2020 2021 2022 2023 2024 2025; do
  ./places_download_generic.sh --year $year --output-dir ./data/places/
done
```

#### Download Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--year` | Yes | Release year (2020-2025) |
| `--output-dir` | Yes | Directory to save downloaded CSV |
| `--force` | No | Overwrite existing files |

### Step 2: Process Data

```bash
# Process downloaded data to GeoPackage
./places_process_generic.sh \
  --input-file ./data/places/places_zcta_2024.csv \
  --output-dir ./output/ \
  --year 2024
```

#### Processing Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--input-file` | Yes | Path to downloaded PLACES CSV |
| `--output-dir` | Yes | Directory to save processed output |
| `--year` | Yes | Data year (for output naming) |
| `--no-geometry` | No | Skip geometry merge (CSV output only) |

## Output

### Files Generated

| File | Description |
|------|-------------|
| `PLACES_{year}_ZCTA_wide.csv` | Wide-format tabular data (one row per ZCTA) |
| `PLACES_{year}_ZCTA_Spatial.gpkg` | GeoPackage with ZCTA polygons and PLACES attributes |

### Variable Naming Convention

Original CDC measure names are standardized to GEOSPACE conventions:

| Original Measure | Standardized Name |
|------------------|-------------------|
| `Current asthma among adults aged >=18 years` | `asthma_current_pct` |
| `Obesity among adults aged >=18 years` | `obesity_pct` |
| `Binge drinking among adults aged >=18 years` | `binge_drinking_pct` |
| `Current smoking among adults aged >=18 years` | `smoking_pct` |

For each measure, confidence interval columns are also included:
- `{measure}_lo` - Lower 95% confidence limit
- `{measure}_hi` - Upper 95% confidence limit

## Notes

- PLACES uses model-based small area estimation (SAE) techniques applied to BRFSS data
- Data is typically released annually in Q4/Q1
- ZCTA geometries are based on 2020 Census boundaries
- See [PLACES Methodology](https://www.cdc.gov/places/methodology/index.html) for technical details

## See Also

- [VARIABLE_CATALOG.md](../VARIABLE_CATALOG.md) - Full variable catalog
- [CDC PLACES FAQ](https://www.cdc.gov/places/faqs/index.html)
- [Measure Definitions](https://www.cdc.gov/places/measure-definitions/index.html)
