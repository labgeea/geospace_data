# GEOSPACE Geospatial Metadatabase Project

**Version:** 1.10.0  
**Author:** GEOSPACE Project  
**License:** Public Domain

A comprehensive framework for cataloguing satellite and climate data for the Continental United States (CONUS), as well as, providing downloading and processing scripts.

## Overview

The GEOSPACE project provides metadata and unified tools for accessing and processing multiple Earth observation and climate datasets:

- **MODIS** - Moderate Resolution Imaging Spectroradiometer satellite data
- **ECMWF** - European Centre for Medium-Range Weather Forecasts reanalysis data  
- **GridMET** - Gridded meteorological data for the United States
- **CAMS** - Copernicus Atmosphere Monitoring Service air pollution data
- **AQS** - US Environmental Protection Agency air quality data

## Quick Start

```bash
# Check framework version
python3 version.py

# MODIS example
cd modis/
./modis_download_generic.sh --variables NDVI --year 2020 --month 1 --output-dir ./data/raw/
./modis_process_generic.sh --variable NDVI --input-dir ./data/raw/ --output-dir ./data/proc/ --date 2020-01-01

# ECMWF example  
cd ecmwf/
./era5_download_generic.sh --variables temperature --year 2020 --month 1 --output-dir ./data/raw/
./era5_process_generic.sh --variable temperature --input-dir ./data/raw/ --output-dir ./data/proc/ --date 2020-01-01

# GridMET example
cd gridmet/
./gridmet_download_generic.sh --variables precipitation --year 2020 --month 1 --output-dir ./data/raw/
./gridmet_process_generic.sh --variable precipitation --input-dir ./data/raw/ --output-dir ./data/proc/ --date 2020-01-01

# CAMS example
cd cams/
./cams_download_generic.sh --variables pm25 --year 2020 --month 1 --output-dir ./data/raw/
./cams_process_generic.sh --input-file cams_pm25_202001.nc --output-dir ./data/proc/ --variables pm25

# AQS example
cd aqs/
./aqs_download_generic.sh --variables ozone --year 2020 --month 1 --output-dir ./data/raw/
./aqs_process_generic.sh --input-file aqs_ozone_202001.nc --output-dir ./data/proc/ --variables ozone
```

## Modules

| Module | Description | Version | Documentation |
|--------|-------------|---------|---------------|
| **MODIS** | Satellite vegetation indices, land surface temperature, forest cover | 1.2.0 | [modis/modis_README.md](modis/modis_README.md) |
| **ECMWF** | ERA5 reanalysis weather and climate data | 1.2.0 | [ecmwf/era5_README.md](ecmwf/era5_README.md) |
| **GridMET** | High-resolution meteorological data for CONUS | 1.2.0 | [gridmet/gridmet_README.md](gridmet/gridmet_README.md) |
| **CAMS** | Air pollution data from Copernicus Atmosphere Monitoring Service | 1.3.0 | [cams/cams_README.md](cams/cams_README.md) |
| **AQS** | Air quality data from US EPA | 1.4.0 | [aqs/aqs_README.md](aqs/aqs_README.md) |
| **SVI** | Social Vulnerability Index data | 1.0.0 | [svi/svi_README.md](svi/svi_README.md) |
| **COI** | Child Opportunity Index data | 1.0.0 | [coi/coi_README.md](coi/coi_README.md) |
| **PLACES** | CDC PLACES health outcomes and prevention data | 1.0.0 | [places/places_README.md](places/places_README.md) |
| **FIRMS** | NASA FIRMS active fire data | 1.0.0 | [firms/firms_README.md](firms/firms_README.md) |
| **STORMS** | NOAA Storm Events Database | 1.0.0 | [storms/storms_README.md](storms/storms_README.md) |
| **WILDFIRE_SMOKE** | Stanford Smoke PM2.5 Reanalysis | 1.0.0 | [wildfire_pm/wildfire_pm_README.md](wildfire_pm/wildfire_pm_README.md) |
| **PRISM** | PRISM gridded climate data (4km/800m, 1895–present) | 1.0.0 | [prism/prism_README.md](prism/prism_README.md) |
| **PM25_COMPONENTS_HARVARD** | Harvard super-learned annual PM2.5 chemical components (50m/1km grid & Census geographies, 2000–2019) | 1.0.0 | [pm25_components_harvard/pm25_components_README.md](pm25_components_harvard/pm25_components_README.md) |

## Installation

### Prerequisites

- Python 3.8+
- GDAL/OGR
- Internet connection for data downloads

### Dependencies

```bash
pip install xarray rioxarray numpy rasterio pandas psutil beautifulsoup4 pyproj requests netcdf4
```

### Setup

```bash
git clone <repository-url>
cd geospace/
python3 version.py  # Verify installation
```

## Data Sources

The framework interfaces with official data providers:

- **NASA Earthdata** (MODIS) - Requires free registration
- **Copernicus Climate Data Store** (ECMWF) - Requires free registration  
- **University of Idaho** (GridMET) - Open access
- **Copernicus Atmosphere Monitoring Service** (CAMS) - Open access
- **US EPA Air Quality System** (AQS) - Open access

## Directory Structure

```bash
geospace/
├── version.py                    # Central version management
├── README.md                     # This file
├── CHANGELOG.md                  # Version history
├── modis/                        # MODIS data tools
│   ├── modis_download_generic.py
│   ├── modis_download_generic.sh
│   ├── modis_process_generic.py
│   ├── modis_process_generic.sh
│   ├── modis_proc_config.json
│   └── modis_README.md
├── ecmwf/                        # ECMWF data tools
│   ├── era5_download_generic.py
│   ├── era5_download_generic.sh
│   ├── era5_process_generic.py
│   ├── era5_process_generic.sh
│   └── era5_README.md
├── cams/                         # CAMS data tools
│   ├── cams_download_generic.py
│   ├── cams_download_generic.sh
│   ├── cams_process_generic.py
│   ├── cams_process_generic.sh
│   └── cams_README.md
├── gridmet/                      # GridMET data tools
│   ├── gridmet_download_generic.py
│   ├── gridmet_download_generic.sh
│   ├── gridmet_process_generic.py
│   ├── gridmet_process_generic.sh
│   └── gridmet_README.md
├── aqs/                          # AQS data tools
│   ├── aqs_download_generic.py
│   ├── aqs_download_generic.sh
│   ├── aqs_process_generic.py
│   ├── aqs_process_generic.sh
│   └── aqs_README.md
├── svi/                          # SVI data tools
│   ├── svi_process_generic.py
│   ├── svi_process_generic.sh
│   └── svi_README.md
├── coi/                          # COI data tools
│   ├── coi_process_generic.py
│   ├── coi_process_generic.sh
│   └── coi_README.md
├── places/                       # PLACES data tools
│   ├── places_download_generic.py
│   ├── places_download_generic.sh
│   ├── places_process_generic.py
│   ├── places_process_generic.sh
│   └── places_README.md
├── firms/                        # FIRMS data tools
│   ├── firms_download_generic.py
│   ├── firms_download_generic.sh
│   ├── firms_process_generic.py
│   ├── firms_process_generic.sh
│   └── firms_README.md
├── storms/                       # STORMS data tools
│   ├── storms_download_generic.py
│   ├── storms_download_generic.sh
│   ├── storms_process_generic.py
│   ├── storms_process_generic.sh
│   └── storms_README.md
├── wildfire_pm/               # Wildfire PM data tools
│   ├── wildfire_pm_download_generic.py
│   ├── wildfire_pm_download_generic.sh
│   ├── wildfire_pm_process_generic.py
│   ├── wildfire_pm_process_generic.sh
│   └── wildfire_pm_README.md
├── prism/                        # PRISM climate data tools
│   ├── prism_download_generic.py
│   ├── prism_download_generic.sh
│   ├── prism_process_generic.py
│   ├── prism_process_generic.sh
│   └── prism_README.md
├── pm25_components_harvard/      # Harvard PM2.5 components data tools
│   ├── pm25_components_download_generic.py
│   ├── pm25_components_download_generic.sh
│   ├── pm25_components_process_generic.py
│   ├── pm25_components_process_generic.sh
│   └── pm25_components_README.md
├── catalog/                      # Metadata catalog tools
│   ├── convert_catalog.py
│   └── CATALOG_README.md
```

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.0.0)
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and test thoroughly
4. Update version following semantic versioning
5. Update CHANGELOG.md
6. Submit pull request

## Support

For questions or issues:

1. Check module-specific documentation
2. Review [CHANGELOG.md](CHANGELOG.md) for known issues
3. Submit issues with detailed information

## License

This framework is released under the Public Domain license. Individual components may have different licenses - see source files for details.

---

**Current Version:** 1.10.0  
**Last Updated:** November 2026  
**Framework Status:** Stable Release
