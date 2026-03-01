# GEOSPACE Framework - Agent Quick Start

> **Purpose**: This document enables rapid onboarding to the GEOSPACE geospatial data framework. Read this first before performing any task in this repository.

---

## TL;DR

This is a **geospatial data download and processing framework** that:
1. Downloads satellite, climate, and health data from official sources (NASA, ECMWF, EPA, CDC, etc.)
2. Processes raw data into analysis-ready formats (GeoTIFF, NetCDF, GeoPackage)
3. Provides standardized scripts for 10 different data modules

**Core tech**: Python, GDAL, XArray, rasterio, pandas

---

## 📁 Repository Layout

```
geospace_data/
├── version.py           # Central version management (check framework version)
├── README.md            # Project overview
├── CHANGELOG.md         # Version history
├── VARIABLE_CATALOG.md  # All variables across all modules
├── DEVELOPMENT_WORKFLOW.md  # How to add modules, release versions
│
├── modis/               # MODIS satellite: NDVI, EVI, LST, VCF
├── ecmwf/               # ERA5 reanalysis: temperature, wind, precipitation
├── gridmet/             # GridMET: high-res CONUS meteorology
├── cams/                # CAMS: air pollution (PM2.5, O3, NO2, etc.)
├── aqs/                 # EPA AQS: ground station air quality
├── svi/                 # CDC Social Vulnerability Index
├── coi/                 # Child Opportunity Index
├── places/              # CDC PLACES health outcomes at ZCTA level
├── firms/               # NASA FIRMS active fire detections
└── storms/              # NOAA Storm Events Database
```

Each module follows the **same structure**:
```
<module>/
├── <module>_download_generic.py   # Python download script
├── <module>_download_generic.sh   # Shell wrapper
├── <module>_process_generic.py    # Python processing script  
├── <module>_process_generic.sh    # Shell wrapper
└── <module>_README.md             # Module documentation
```

---

## 🎯 Common Tasks & Entry Points

### "I need to download data"

```bash
cd <module>/
./<module>_download_generic.sh --variables <VAR> --year <YEAR> --month <MONTH> --output-dir ./data/raw/
```

**Examples:**
```bash
# MODIS NDVI
./modis/modis_download_generic.sh --variables NDVI --year 2020 --month 1 --output-dir ./data/raw/

# ERA5 temperature
./ecmwf/era5_download_generic.sh --variables temperature --year 2020 --month 1 --output-dir ./data/raw/

# GridMET precipitation
./gridmet/gridmet_download_generic.sh --variables precipitation --year 2020 --month 1 --output-dir ./data/raw/
```

### "I need to process downloaded data"

```bash
cd <module>/
./<module>_process_generic.sh --input-dir ./data/raw/ --output-dir ./data/proc/ --date 2020-01-01
```

### "What variables are available?"
See [VARIABLE_CATALOG.md](VARIABLE_CATALOG.md) — complete reference of all variables and their aliases.

### "I need to check/update the framework version"
```bash
python3 version.py
```

---

## ⚙️ Key Concepts

### Module Pattern
All modules use the same `download → process` pattern:
1. **Download** fetches raw data from source APIs
2. **Process** converts to analysis-ready format (GeoTIFF, GeoPackage, CSV)

### Script Naming Convention
- `<module>_download_generic.py` / `.sh` — download scripts
- `<module>_process_generic.py` / `.sh` — processing scripts
- Use `--help` on any script to see available options
- Use `--version` to see module version

### Common Dependencies
```bash
pip install xarray rioxarray numpy rasterio pandas psutil beautifulsoup4 pyproj requests netcdf4
```

Some modules require additional:
- **MODIS**: NASA Earthdata account
- **ECMWF**: Copernicus CDS account
- **AQS**: EPA AQS API credentials

---

## 📊 Available Modules

| Module | Data Source | Variables | Resolution |
|--------|-------------|-----------|------------|
| **MODIS** | NASA satellites | NDVI, EVI, LST, VCF | 250m-1km |
| **ECMWF** | ERA5 reanalysis | 14 weather variables | 31km |
| **GridMET** | U. Idaho | 17 meteorology vars | 4km |
| **CAMS** | Copernicus | PM2.5, PM10, O3, NO2, SO2, CO | ~80km |
| **AQS** | EPA | Criteria pollutants | Point/station |
| **SVI** | CDC | Social vulnerability (20+ vars) | Census Tract |
| **COI** | CHI | Child opportunity (20+ vars) | Census Tract |
| **PLACES** | CDC | Health outcomes (30 vars) | ZCTA |
| **FIRMS** | NASA | Active fire detections | 375m-1km |
| **STORMS** | NOAA | Storm events (10+ vars) | Point/Polygon |

---

## ⚠️ Gotchas & Conventions

1. **Version import**: Python scripts import version from central `version.py`:
   ```python
   sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   from version import get_module_version
   ```

2. **CRS**: Most outputs use EPSG:5070 (CONUS Albers) unless otherwise specified

3. **API credentials**: Some modules require pre-registered accounts:
   - MODIS → NASA Earthdata
   - ECMWF → Copernicus CDS (`~/.cdsapirc`)
   - AQS → EPA API key

4. **Shell wrappers**: Always use `.sh` wrappers instead of calling `.py` directly — they handle environment setup

5. **Output formats**:
   - Raster data → GeoTIFF or NetCDF
   - Vector/tabular data → GeoPackage or CSV

---

## 🔧 When Modifying Code

### Adding a new module
See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for full instructions. Summary:
1. Create `<module>/` directory
2. Create `<module>_download_generic.py` with version import
3. Create shell wrappers
4. Create `<module>_README.md`
5. Update `version.py` with new module
6. Update main `README.md` module table
7. Update `CHANGELOG.md`

### Adding new variables to existing module
1. Update the download script with new variable aliases
2. Update processing logic if needed
3. Add to `VARIABLE_CATALOG.md`
4. Bump PATCH version

### Making a release
```bash
# Update version.py
sed -i 's/__version__ = "1.7.0"/__version__ = "1.8.0"/' version.py

# Update CHANGELOG.md (move Unreleased to new version)
# Commit and tag
git commit -m "Bump version to 1.8.0"
git tag -a v1.8.0 -m "Release v1.8.0 - Description"
git push origin main --tags
```

---

## 📚 Detailed Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview and quick start |
| [VARIABLE_CATALOG.md](VARIABLE_CATALOG.md) | All variables with aliases and metadata |
| [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) | Adding modules, versioning, releases |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| `<module>/<module>_README.md` | Module-specific documentation |

---

## 🗂️ File Patterns to Know

| Pattern | Meaning |
|---------|---------|
| `*_download_generic.py` | Download script (Python) |
| `*_download_generic.sh` | Download script (Shell wrapper) |
| `*_process_generic.py` | Processing script (Python) |
| `*_process_generic.sh` | Processing script (Shell wrapper) |
| `*_README.md` | Module documentation |
| `*_config.json` | Module configuration (if present) |
| `version.py` | Central version management |
