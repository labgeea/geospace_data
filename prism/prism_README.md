# PRISM Module

Downloads and processes PRISM gridded climate data from the PRISM Climate Group (Oregon State University) for the contiguous United States.

**Version:** 1.9.0 | **Source:** Oregon State University | **Coverage:** CONUS | **CRS Output:** EPSG:5070

---

## Overview

PRISM (Parameter-elevation Regressions on Independent Slopes Model) produces high-quality spatial climate datasets incorporating station data, a digital elevation model, and a knowledge base of local effects for the contiguous US.

- **Daily/monthly time series:** 4km resolution (1895–present)
- **30-year climate normals:** 4km (standard) or 800m (high-resolution)

---

## Elements (Variables)

| Code | Long Name | Units | Time Series | Normals |
| :--- | :--- | :--- | :---: | :---: |
| `ppt` | Precipitation | mm | ✓ | ✓ |
| `tmin` | Minimum Temperature | °C | ✓ | ✓ |
| `tmax` | Maximum Temperature | °C | ✓ | ✓ |
| `tmean` | Mean Temperature | °C | ✓ | ✓ |
| `tdmean` | Mean Dew Point Temperature | °C | ✓ | ✓ |
| `vpdmin` | Minimum Vapor Pressure Deficit | hPa | ✓ | ✓ |
| `vpdmax` | Maximum Vapor Pressure Deficit | hPa | ✓ | ✓ |
| `solslope` | Sloped-Surface Solar Radiation | W/m² | — | ✓ |
| `soltotal` | Total Global Shortwave Radiation on Slope | W/m² | — | ✓ |
| `solclear` | Clearness Index | fraction | — | ✓ |
| `soltrans` | Atmospheric Transmittance | fraction | — | ✓ |

---

## Data Types

| Code | Description | Resolution |
| :--- | :--- | :--- |
| `ts` | Daily / monthly / annual time series | 4km |
| `normals_800` | 30-year climate normals (high-res) | 800m |
| `normals` | 30-year climate normals (standard) | 4km |

---

## Time String Format

| Data Type | Period | Time Format | Example |
| :--- | :--- | :--- | :--- |
| `ts` | Daily | `YYYYMMDD` | `20200115` |
| `ts` | Monthly | `YYYYMM` | `202001` |
| `ts` | Annual | `YYYY` | `2020` |
| `normals` / `normals_800` | Monthly normal | `MM` | `04` |
| `normals` / `normals_800` | Daily normal | `MMDD` | `0415` |
| `normals` / `normals_800` | Annual normal | `14` | `14` |

---

## Usage

### Download

```bash
# Daily precipitation
./prism/prism_download_generic.sh --element ppt --time 20200115 --output-dir ./raw/prism/

# Monthly max temperature for Q1 2020
./prism/prism_download_generic.sh --element tmax --time 202001,202002,202003 --output-dir ./raw/prism/

# Full year (annual time series)
./prism/prism_download_generic.sh --element tmean --time 2020 --output-dir ./raw/prism/

# Multiple elements, single day
./prism/prism_download_generic.sh --element ppt,tmin,tmax --time 20200101 --output-dir ./raw/prism/

# 800m monthly normals — April precipitation
./prism/prism_download_generic.sh --element ppt --time 04 --data-type normals_800 --output-dir ./raw/prism/

# List available elements
./prism/prism_download_generic.sh --list-variables
```

### Process

```bash
# Process all elements (reproject to EPSG:5070 GeoTIFF)
./prism/prism_process_generic.sh --input-dir ./raw/prism/ --output-dir ./proc/prism/

# Process precipitation only
./prism/prism_process_generic.sh --input-dir ./raw/prism/ --output-dir ./proc/prism/ --element ppt
```

### Python API

```python
from prism.prism_download_generic import download_prism

results = download_prism(
    elements=["ppt", "tmax"],
    times=["20200101", "20200102"],
    data_type="ts",
    fmt="nc",
    output_dir="./raw/prism/",
)

from prism.prism_process_generic import process_prism

stats = process_prism(
    input_dir="./raw/prism/",
    output_dir="./proc/prism/",
    element="ppt",
)
```

---

## Output Structure

```
raw/prism/
└── {element}/
    └── {PRISM_source_filename}/     ← extracted zip contents (BIL, HDR, PRJ…)

proc/prism/
└── {element}/
    └── {PRISM_source_filename}.tif  ← EPSG:5070 GeoTIFF, LZW, float32
prism_processing_report.json
```

---

## Dependencies

| Package | Purpose |
| :--- | :--- |
| `requests` | HTTP downloads from PRISM Web Service |
| `rasterio` | Raster I/O and reprojection |
| `numpy` | Array operations |

Install: `pip install requests rasterio numpy`

---

## Data Source & Citation

- **Provider:** PRISM Climate Group, Oregon State University
- **Web Service:** https://services.nacse.org/prism/data/public/
- **Website:** https://prism.oregonstate.edu/
- **License:** Freely available for non-commercial use; see [PRISM terms](https://prism.oregonstate.edu/terms/)

**Citation:**  
PRISM Climate Group, Oregon State University, https://prism.oregonstate.edu, data created 4 Feb 2004.

---

## Notes

- `solslope`, `soltotal`, `solclear`, `soltrans` are **normals only** and will fail if requested with `data_type=ts`.
- PRISM serves files as zip archives containing BIL (binary interleaved by line) rasters plus ancillary files. The download script automatically extracts them.
- The NetCDF format option (`--format nc`) is available for time-series downloads only.
- Normals datasets do not accept a file format argument; the service determines the format.
