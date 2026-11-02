# PM2.5 Components (Harvard Super-Learned) Module

Module to download and process annual predictions of 15 ambient $\text{PM}_{2.5}$ chemical components (5 major components and 10 trace elements) across the contiguous United States (2000–2019).

## Dataset Overview

- **Canonical Sources (Harvard T.H. Chan School of Public Health / NSAPH / CAFE):**
  - **Gridded (50-m Urban / 1-km Non-Urban):** [Harvard Dataverse `doi:10.7910/DVN/3H7DNP`](https://doi.org/10.7910/DVN/3H7DNP) (Version 2.0)
  - **Geography-Aggregated (State, County, Tract, ZCTA, Block Group, ESRI ZIP, Block):** [Harvard Dataverse `doi:10.7910/DVN/F6PQAA`](https://doi.org/10.7910/DVN/F6PQAA) (Version 2.0)
- **Temporal Extent & Resolution:** 2000–2019 (Annual)
- **Spatial Coverage:** Contiguous United States (CONUS)
- **Spatial Resolutions / Geographies:**
  - `grid_urban` (50-m grid within 1-km buffer of 2010 Census TIGER/Line Urban Areas)
  - `grid_non_urban` (1-km grid outside urban areas)
  - `state`, `county`, `tract`, `zcta`, `block_group`, `block` (2000 and 2010 Census TIGER/Line boundary vintages, population-weighted from block-level assignments)
  - `esri_zip` (Annual TomTom / ESRI ZIP code areas, 2000–2019)
- **License:** CC0 1.0 (Public Domain Dedication)
- **Credentials Required:** None

---

## Variables (15 Components)

| Script Alias | Component Name | Formula | Category | Units | Urban $R^2$ | Non-Urban $R^2$ | Additional Aliases |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | :--- |
| `ec` | Elemental Carbon | $\text{EC}$ | `major` | `ug/m3` | 0.910 | 0.913 | `elemental_carbon`, `black_carbon`, `bc` |
| `nh4` | Ammonium | $\text{NH}_4^+$ | `major` | `ug/m3` | 0.910 | 0.918 | `ammonium`, `nh4_ion` |
| `no3` | Nitrate | $\text{NO}_3^-$ | `major` | `ug/m3` | 0.879 | 0.878 | `nitrate`, `no3_ion` |
| `oc` | Organic Carbon | $\text{OC}$ | `major` | `ug/m3` | 0.856 | 0.857 | `organic_carbon`, `om`, `organic_matter` |
| `so4` | Sulfate | $\text{SO}_4^{2-}$ | `major` | `ug/m3` | 0.952 | 0.957 | `sulfate`, `sulphate`, `so4_ion` |
| `br` | Bromine | $\text{Br}$ | `trace` | `ng/m3` | 0.859 | 0.863 | `bromine`, `bromium` |
| `ca` | Calcium | $\text{Ca}$ | `trace` | `ng/m3` | 0.865 | 0.875 | `calcium` |
| `cu` | Copper | $\text{Cu}$ | `trace` | `ng/m3` | 0.797 | 0.787 | `copper` |
| `fe` | Iron | $\text{Fe}$ | `trace` | `ng/m3` | 0.875 | 0.875 | `iron` |
| `k` | Potassium | $\text{K}$ | `trace` | `ng/m3` | 0.868 | 0.866 | `potassium` |
| `ni` | Nickel | $\text{Ni}$ | `trace` | `ng/m3` | 0.848 | 0.850 | `nickel` |
| `pb` | Lead | $\text{Pb}$ | `trace` | `ng/m3` | 0.833 | 0.843 | `lead` |
| `si` | Silicon | $\text{Si}$ | `trace` | `ng/m3` | 0.851 | 0.857 | `silicon` |
| `v` | Vanadium | $\text{V}$ | `trace` | `ng/m3` | 0.838 | 0.841 | `vanadium` |
| `zn` | Zinc | $\text{Zn}$ | `trace` | `ng/m3` | 0.878 | 0.881 | `zinc` |

### Variable Packages (`--variables`)
- `major`: `ec,nh4,no3,oc,so4` (units: $\mu\text{g/m}^3$)
- `trace`: `br,ca,cu,fe,k,ni,pb,si,v,zn` (units: $\text{ng/m}^3$)
- `all`: all 15 components

---

## Census Divisions for Gridded Data (`--region`)

The gridded dataset (`doi:10.7910/DVN/3H7DNP`) partitions CONUS into 9 Census Divisions:

| Code | Census Division | States Included | Urban Grid Points (50-m) | Non-Urban Grid Points (1-km) |
| :--- | :--- | :--- | ---: | ---: |
| `NE1` | New England | CT, MA, ME, NH, RI, VT | 10,750,894 | 176,590 |
| `MA2` | Middle Atlantic | NJ, NY, PA | 21,308,981 | 195,225 |
| `ENC3` | East North Central | IL, IN, MI, OH, WI | 29,712,644 | 529,891 |
| `WNC4` | West North Central | IA, KS, MN, MO, ND, NE, SD | 13,431,160 | 1,228,700 |
| `SA5` | South Atlantic | DC, DE, FL, GA, MD, NC, SC, VA, WV | 44,100,142 | 565,638 |
| `ESC6` | East South Central | AL, KY, MS, TN | 15,769,846 | 407,153 |
| `WSC7` | West South Central | AR, LA, OK, TX | 24,000,000 | 1,012,195 |
| `M8` | Mountain | AZ, CO, ID, MT, NM, NV, UT, WY | 13,668,782 | 2,074,693 |
| `P9` | Pacific (CONUS) | CA, OR, WA | 20,021,752 | 738,363 |

> **Note on `M8` non-urban:** Upstream `3H7DNP` omits `non-urban-dat/M8.zip` and instead provides `non-urban-rds/M8-major-components.zip` and `non-urban-rds/M8-trace-elements.zip`. `pm25_components_download_generic.py` automatically downloads the `.rds` archives for `M8`, and `pm25_components_process_generic.py` reads them using `pyreadr` (or `Rscript` fallback).

---

## Usage

### 1. List Variables & Configuration
```bash
conda run -n xarray-env ./pm25_components_harvard/pm25_components_download_generic.sh --list-variables
conda run -n xarray-env ./pm25_components_harvard/pm25_components_process_generic.sh --list-config
```

### 2. Download Data
```bash
# Download aggregated Census geographies bundle (state, county, tract, zcta, block_group; ~931 MB)
conda run -n xarray-env ./pm25_components_harvard/pm25_components_download_generic.sh \
  --geography county \
  --output-dir ./data/raw/pm25_components_harvard/

# Download 1-km non-urban grid for New England (NE1; ~159 MB)
conda run -n xarray-env ./pm25_components_harvard/pm25_components_download_generic.sh \
  --geography grid_non_urban \
  --region NE1 \
  --output-dir ./data/raw/pm25_components_harvard/

# Download 50-m urban grid for major components in New England (NE1)
conda run -n xarray-env ./pm25_components_harvard/pm25_components_download_generic.sh \
  --geography grid_urban \
  --region NE1 \
  --variables major \
  --output-dir ./data/raw/pm25_components_harvard/
```

### 3. Process Data
```bash
# Process county-level data (2010 Census boundaries) into annual Parquet files
conda run -n xarray-env ./pm25_components_harvard/pm25_components_process_generic.sh \
  --geography county \
  --input-dir ./data/raw/pm25_components_harvard/ \
  --output-dir ./data/proc/pm25_components_harvard/ \
  --years 2010-2019

# Process county-level data for 2015 and also export a GeoPackage (.gpkg) via pygris
conda run -n xarray-env ./pm25_components_harvard/pm25_components_process_generic.sh \
  --geography county \
  --input-dir ./data/raw/pm25_components_harvard/ \
  --output-dir ./data/proc/pm25_components_harvard/ \
  --years 2015 \
  --output-format both

# Process 1-km non-urban grid for New England (NE1) for 2010 (joins .dat vectors with grid lon/lat)
conda run -n xarray-env ./pm25_components_harvard/pm25_components_process_generic.sh \
  --geography grid_non_urban \
  --region NE1 \
  --variables major \
  --years 2010 \
  --input-dir ./data/raw/pm25_components_harvard/ \
  --output-dir ./data/proc/pm25_components_harvard/
```

---

## Output File Naming

- **Aggregated Census (`state`, `county`, `tract`, `zcta`, `block_group`, `block`):**
  - Parquet: `<output-dir>/<geography>/pm25_components_<geography>_<boundary_year>_<year>.parquet`
  - GeoPackage (optional): `<output-dir>/<geography>/pm25_components_<geography>_<boundary_year>_<year>_Spatial.gpkg`
- **Aggregated `esri_zip`:**
  - Parquet: `<output-dir>/esri_zip/pm25_components_esri_zip_<year>.parquet`
- **Gridded (`grid_non_urban`, `grid_urban`):**
  - Parquet: `<output-dir>/<geography>/<REGION>/pm25_components_<geography>_<REGION>_<year>.parquet`
  - GeoPackage (optional): `<output-dir>/<geography>/<REGION>/pm25_components_<geography>_<REGION>_<year>_Spatial.gpkg`

---

## Citations

When using this dataset, cite the Dataverse datasets and the methodology preprints:

1. Amini, H., Castro, E., Danesh-Yazdi, M., Di, Q., Requia, W. J., Wei, Y., Abu Awad, Y., Shi, L., Franklin, M., Kang, C.-M., Wolfson, J. M., James, P., Habre, R., Zhu, Q., Apte, J. S., Andersen, Z. J., Xing, X., Hultquist, C., Kloog, I., Dominici, F., Koutrakis, P., & Schwartz, J. (2025). *Annual PM2.5 Component Concentrations for the Contiguous United States, 50-m Urban Grid and 1-km Non-Urban Grid (2000-2019)* (Version 2.0) [Dataset]. Harvard Dataverse. https://doi.org/10.7910/DVN/3H7DNP
2. Castro, E., Amini, H., Wei, Y., Shtein, A., & Schwartz, J. (2025). *Annual PM2.5 Component Concentrations for the Contiguous United States, aggregated to common geographies (2000-2019)* (Version 2.0) [Dataset]. Harvard Dataverse. https://doi.org/10.7910/DVN/F6PQAA
3. Amini, H., Danesh-Yazdi, M., Di, Q., Requia, W., Wei, Y., Abu-Awad, Y., Shi, L., Franklin, M., Kang, C.-M., Wolfson, J., James, P., Habre, R., Zhu, Q., Apte, J., Andersen, Z., Kloog, I., Dominici, F., Koutrakis, P., & Schwartz, J. (2022). *Hyperlocal super-learned PM2.5 components across the contiguous US.* Research Square. https://doi.org/10.21203/rs.3.rs-1745433/v1
4. Amini, H., Danesh-Yazdi, M., Di, Q., Requia, W., Wei, Y., Abu-Awad, Y., Shi, L., Franklin, M., Kang, C.-M., Wolfson, J., James, P., Habre, R., Zhu, Q., Apte, J., Andersen, Z., Xing, X., Hultquist, C., Kloog, I., Dominici, F., Koutrakis, P., & Schwartz, J. (2022). *Hyperlocal US PM2.5 Trace Elements Super-learned.* Research Square. https://doi.org/10.21203/rs.3.rs-2052258/v1

