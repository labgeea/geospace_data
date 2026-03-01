---
trigger: always_on
glob:
description: GEOSPACE geospatial data download and processing framework
---

# GEOSPACE Framework Context

Geospatial data download and processing framework for satellite, climate, and health data from official sources (NASA, ECMWF, EPA, CDC, etc.).

## Repository Layout

```
geospace_data/
├── version.py           # Central version management
├── VARIABLE_CATALOG.md  # All variables across all modules
├── modis/              # NDVI, EVI, LST, VCF (250m-1km)
├── ecmwf/              # ERA5 reanalysis (31km)
├── gridmet/            # High-res CONUS meteorology (4km)
├── cams/               # Air pollution PM2.5, O3, NO2 (~80km)
├── aqs/                # EPA ground station data (point)
├── svi/                # CDC Social Vulnerability (tract)
├── coi/                # Child Opportunity Index (tract)
├── places/             # CDC PLACES health outcomes (ZCTA)
├── firms/              # NASA active fire (375m-1km)
└── storms/             # NOAA Storm Events (point/polygon)
```

## Module Pattern

All modules follow the same structure:
```
<module>/
├── <module>_download_generic.py   # Download script
├── <module>_download_generic.sh   # Shell wrapper
├── <module>_process_generic.py    # Processing script
├── <module>_process_generic.sh    # Shell wrapper
└── <module>_README.md             # Documentation
```

## Common Tasks

| Task | Command |
|------|---------|
| Download data | `./<module>/<module>_download_generic.sh --variables VAR --year YYYY --month MM` |
| Process data | `./<module>/<module>_process_generic.sh --input-dir ./raw/ --output-dir ./proc/` |
| Check version | `python3 version.py` |
| List variables | See `VARIABLE_CATALOG.md` |

## API Credentials Required

| Module | Account |
|--------|---------|
| MODIS | NASA Earthdata |
| ECMWF | Copernicus CDS (`~/.cdsapirc`) |
| AQS | EPA API key |

## Conventions

1. Always use `.sh` wrappers (handle environment setup)
2. Use `--help` on any script for options
3. Use `--version` for module version
4. CRS: EPSG:5070 (CONUS Albers) unless specified
5. Outputs: GeoTIFF/NetCDF (raster), GeoPackage/CSV (vector)

## Version Management

Python scripts import from central `version.py`:
```python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_module_version
```

## Adding New Modules

1. Create `<module>/` directory
2. Create download/process scripts with version import
3. Create shell wrappers and README
4. Update `version.py`, main `README.md`, `CHANGELOG.md`

See `DEVELOPMENT_WORKFLOW.md` for full instructions.
