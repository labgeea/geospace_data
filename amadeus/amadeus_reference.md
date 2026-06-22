# `amadeus` Download Functions — Full Reference


This table outlines each download function available in the `amadeus` R package. It details the dataset descriptions, the exact variables or parameters it uses to generate datasets along with their descriptions, and additional context regarding how the data is extracted.

| Download Function | Associated Dataset | Exact Variables / Parameters Available | Additional Info |
| :--- | :--- | :--- | :--- |
| `download_aqs` | EPA Air Quality System (AQS)<br>_Accesses and downloads Air Quality System (AQS) data from the U.S. EPA's Pre-Generated Data Files._ | `parameter_code`: EPA pollutant parameter code. For details, refer to AQS parameter codes.<br>`resolution_temporal`: Temporal resolution. Currently, no value other than "daily" works. | Extracts specific parameter codes explicitly requested by the user. |
| `download_cropscape` | USDA CropScape (CDL)<br>_Accesses and downloads USDA CropScape Cropland Data Layer data from the USDA NASS or the George Mason University website._ | `source`: Data source, one of `"USDA"` or `"GMU"`. | Implicit extraction. Downloads full Cropland Data Layer (CDL) rasters for the specified years. Spatial extent depends on the source chosen. |
| `download_ecoregion` | EPA Ecoregions<br>_Accesses and downloads U.S. EPA's Ecoregions. Level 3 data, where all pieces of information in the higher levels are included, are downloaded._ | **None** | Implicit extraction. Downloads full shapefiles for Ecoregion levels 1-4. No specific variable selection available at download. |
| `download_edgar` | EDGAR Emissions<br>_Constructs and optionally downloads EDGAR emissions data URLs based on user-specified inputs including species, temporal resolution, emission sectors, and file formats._ | `species`: One or more species to download. Supported values: `"BC"`, `"CO"`, `"NH3"`, `"NMVOC"`, `"NOx"`, `"OC"`, `"PM10"`, `"PM2.5"`, `"SO2"`.<br>`sector_yearly`, `sector_monthly`, `sector_voc`: Emission sectors for data depending on temporal resolution. | Explicit extraction of particular atmospheric species and sectors as NetCDF or txt format. |
| `download_geos` | NASA GEOS-CF<br>_Accesses and downloads various atmospheric composition collections from NASA's Global Earth Observing System (GEOS) compositional forecast model._ | `collection`: GEOS-CF data collection file name. Supported values: `"aqc_tavg_1hr_g1440x721_v1"`, `"chm_tavg_1hr_g1440x721_v1"`, `"met_tavg_1hr_g1440x721_x1"`, `"xgc_tavg_1hr_g1440x721_x1"`, `"chm_inst_1hr_g1440x721_p23"`, `"met_inst_1hr_g1440x721_p23"`. | Explicit extraction of entire collections for specific dates. Requires NASA Earthdata token. |
| `download_gmted` | USGS GMTED2010<br>_Accesses and downloads Global Multi-resolution Terrain Elevation Data (GMTED2010) from U.S. Geological Survey and National Geospatial-Intelligence Agency._ | `statistic`: Available statistics include `"Breakline Emphasis"`, `"Systematic Subsample"`, `"Median Statistic"`, `"Minimum Statistic"`, `"Mean Statistic"`, `"Maximum Statistic"`, and `"Standard Deviation Statistic"`.<br>`resolution`: Available resolutions include `"7.5 arc-seconds"`, `"15 arc-seconds"`, and `"30 arc-seconds"`. | Explicit extraction of elevation statistics globally at specific resolutions. |
| `download_gridmet` | UC Merced gridMET<br>_Accesses and downloads gridded surface meteorological data from the University of California Merced Climatology Lab's gridMET dataset._ | `variables`: Variable name acronym codes (e.g., `"pr"`, `"tmmn"`, `"tmmx"`, `"bi"`, `"erc"`). Also accepts full names like `"Precipitation"`. | Explicit extraction of particular meteorological variables in NetCDF format. |
| `download_groads` | SEDAC gROADS<br>_Accesses and downloads roads data from NASA's Global Roads Open Access Data Set (gROADS), v1 (1980-2010)._ | `data_region`: Data can be downloaded for `"Global"`, `"Africa"`, `"Asia"`, `"Europe"`, `"Americas"`, `"Oceania East"`, and `"Oceania West"`.<br>`data_format`: `"Shapefile"` or `"Geodatabase"`. | Implicit extraction. Downloads complete road network geometries for requested regions. |
| `download_hms` | NOAA Hazard Mapping System<br>_Accesses and downloads wildfire smoke plume coverage data from NOAA's Hazard Mapping System Fire and Smoke Product._ | `data_format`: `"Shapefile"` or `"KML"`. | Implicit extraction. Downloads fire and smoke plume shapefiles based on the requested date. No individual variable selection. |
| `download_huc` | USGS Watershed Boundary (HUC)<br>_NHDPlus data provides the most comprehensive and high-resolution hydrography data. This function downloads national dataset from NHDPlus Version 2.1 on USGS Amazon S3 storage._ | `region`: One of `"Lower48"`, `"Islands"`.<br>`type`: One of `"Seamless"`, `"OceanCatchment"`. | Implicit extraction. Downloads comprehensive watershed boundaries based on the regional scope selected. |
| `download_koppen_geiger` | Koppen-Geiger Climate<br>_Accesses and downloads climate classification data from the Present and future Koppen-Geiger climate classification maps at 1-km resolution._ | `data_resolution`: Available resolutions are `"0.0083"` degrees, `"0.083"` degrees, and `"0.5"` degrees.<br>`time_period`: Available times are `"Present"` (1980-2016) and `"Future"` (2071-2100). | Explicit selection of climate classification scenarios and resolutions. |
| `download_merra2` | NASA MERRA-2<br>_Accesses and downloads various meteorological and atmospheric collections from NASA's Modern-Era Retrospective analysis for Research and Applications, Version 2 (MERRA-2) model._ | `collection`: MERRA-2 data collection file name. 39 collections including `"inst1_2d_asm_Nx"`, `"tavg1_2d_flx_Nx"`, `"tavg3_3d_aer_Nv"`, etc. | Explicit extraction of collections representing groups of atmospheric and meteorological variables. |
| `download_modis` | NASA MODIS<br>_Retrieves hdf download links and selects relevant tiles at queried horizontal-vertical tile number combinations for NASA MODIS products._ | `product`: One of 23 products including `"MOD09GA"`, `"MOD11A1"`, `"MOD13A1"`, `"MCD19A2"`, `"VNP46A2"`.<br>`version`: Product version (e.g., `"061"`). | Explicit extraction of MODIS data products spanning land surface, temperature, and vegetation. Spatial subsetting available. |
| `download_narr` | NOAA NARR<br>_Accesses and downloads daily meteorological data from NOAA's North American Regional Reanalysis (NARR) model._ | `variables`: Variable name acronyms (e.g., `"weasd"`, `"omega"`). "Pressure levels" variables contain variable values at 29 atmospheric levels. | Explicit extraction of specific meteorological and reanalysis parameters. |
| `download_nei` | EPA NEI<br>_Accesses and downloads road emissions data from the U.S. EPA's National Emissions Inventory (NEI)._ | **None** | Implicit extraction. Downloads comprehensive criteria and hazardous air pollutant emissions inventories based purely on the `year`. |
| `download_nlcd` | MRLC NLCD<br>_Accesses and downloads annual land cover data from the Multi-Resolution Land Characteristics (MRLC) Consortium's National Land Cover Database (NLCD) products data base._ | `product`: Product types including `"Land Cover"`, `"Land Cover Change"`, `"Land Cover Confidence"`, `"Fractional Impervious Surface"`, `"Impervious Descriptor"`, or `"Spectral Change Day of Year"`. | Explicit extraction of distinct land classification raster products. |
| `download_population` | SEDAC Population Density<br>_Accesses and downloads population density data from NASA's UN WPP-Adjusted Population Density, v4.11._ | `data_resolution`: Available resolutions are `"30 second"`, `"2.5 minute"`, `"15 minute"`, `"30 minute"`, and `"60 minute"`.<br>`data_format`: `"ASCII"`, `"GeoTIFF"`, or `"netCDF"`. | Explicit selection of Gridded Population of the World (GPW) resolutions. |
| `download_prism` | PRISM Climate<br>_Accesses and downloads Oregon State University's PRISM data from the PRISM Climate Group Web Service._ | `element`: Data element. One of `"ppt"`, `"tmin"`, `"tmax"`, `"tmean"`, `"tdmean"`, `"vpdmin"`, `"vpdmax"`, `"solslope"`, `"soltotal"`, `"solclear"`, `"soltrans"`.<br>`data_type`: Data type. `"ts"`, `"normals_800"`, `"normals"`. | Explicit extraction of foundational climate elements and specific data types. |
| `download_terraclimate`| TerraClimate<br>_Accesses and downloads climate and water balance data from the University of California Merced Climatology Lab's TerraClimate dataset._ | `variables`: Variable name acronym codes (e.g., `"aet"`, `"def"`, `"pdsi"`, `"pet"`, `"pr"`, `"ro"`, `"soil"`, `"srad"`, `"swe"`, `"tmax"`, `"tmin"`, `"vap"`, `"vpd"`). Also accepts full names like `"Precipitation"`. | Explicit extraction of high-resolution global terrestrial climate and water balance variables. |
| `download_tri` | EPA Toxics Release Inventory<br>_Accesses and downloads toxic release data from the U.S. EPA's Toxic Release Inventory (TRI) Program._ | **None** | Implicit extraction. Downloads comprehensive TRI basic data files based strictly on `year`. |

*Note: The `download_data()` function acts as the primary wrapper, routing execution to the functions above based on the `dataset_name` argument.*

---

# Variable Catalogs by Function

> The following sections list every variable available in each dataset, sourced from amadeus internal metadata and official dataset documentation.


# `amadeus` Download Functions — Variable Catalog

_Generated from amadeus internal metadata and dataset documentation._

---

## `download_aqs`

| Code / Variable | Description |
| :--- | :--- |
| `44201` | Ozone (O3) |
| `42401` | Sulfur dioxide (SO2) |
| `42101` | Carbon monoxide (CO) |
| `42602` | Nitrogen dioxide (NO2) |
| `88101` | PM2.5 - Local Conditions (FRM/FEM) |
| `88502` | PM2.5 - Speciation |
| `81102` | PM10 - Local Conditions |
| `14129` | Lead PM10 LC |
| `85129` | PM10 - Non-FRM/FEM Mass |

---

## `download_cropscape`

| Code / Variable | Description |
| :--- | :--- |
| `CDL_raster` | Annual cropland raster with ~100 crop/land-use categories (e.g., corn, soybeans, developed, forest) |

---

## `download_ecoregion`

| Code / Variable | Description |
| :--- | :--- |
| `NA_L1CODE` | Level 1 Ecoregion code (continental scale) |
| `NA_L2CODE` | Level 2 Ecoregion code (sub-continental scale) |
| `US_L3CODE` | Level 3 Ecoregion code (regional scale) |
| `US_L4CODE` | Level 4 Ecoregion code (local scale) |

---

## `download_edgar`

| Code / Variable | Description |
| :--- | :--- |
| `BC` | Black Carbon |
| `CO` | Carbon Monoxide |
| `NH3` | Ammonia |
| `NMVOC` | Non-Methane Volatile Organic Compounds |
| `NOx` | Nitrogen Oxides |
| `OC` | Organic Carbon |
| `PM10` | Particulate Matter < 10 micrometers |
| `PM2.5` | Particulate Matter < 2.5 micrometers |
| `SO2` | Sulfur Dioxide |

---

## `download_geos`

| Code / Variable | Description |
| :--- | :--- |
| `aqc_tavg_1hr_g1440x721_v1` | Air quality constituents (tavg, surface): O3, NO, NO2, CO, PM2.5, etc. |
| `chm_tavg_1hr_g1440x721_v1` | Chemistry (tavg, surface): photolysis rates, aerosol species, oxidants |
| `met_tavg_1hr_g1440x721_x1` | Meteorology (tavg, surface): T2M, U10M, V10M, Q2M, PS, etc. |
| `xgc_tavg_1hr_g1440x721_x1` | Extended gas-phase chemistry (tavg, surface) |
| `chm_inst_1hr_g1440x721_p23` | Chemistry (instantaneous, pressure levels 23): aerosol/gas profiles |
| `met_inst_1hr_g1440x721_p23` | Meteorology (instantaneous, pressure levels 23): T, U, V, Q profiles |

---

## `download_gmted`

| Code / Variable | Description |
| :--- | :--- |
| `be` | Breakline Emphasis - preserves ridgelines and valleys |
| `ds` | Systematic Subsample - regular grid subsample of source elevation |
| `md` | Median Statistic - median elevation within aggregation cell |
| `mi` | Minimum Statistic - minimum elevation within aggregation cell |
| `mn` | Mean Statistic - mean elevation within aggregation cell |
| `mx` | Maximum Statistic - maximum elevation within aggregation cell |
| `sd` | Standard Deviation Statistic - terrain roughness within cell |

---

## `download_gridmet`

| Code / Variable | Description |
| :--- | :--- |
| `sph` | near-surface specific humidity |
| `vpd` | mean vapor pressure deficit |
| `pr` | precipitation |
| `rmin` | minimum near-surface relative humidity |
| `rmax` | maximum near-surface relative humidity |
| `srad` | surface downwelling solar radiation |
| `tmmn` | minimum near-surface air temperature |
| `tmmx` | maximum near-surface air temperature |
| `vs` | wind speed at 10 m |
| `th` | wind direction at 10 m |
| `pdsi` | palmer drought severity index |
| `pet` | reference grass evaportranspiration |
| `etr` | reference alfalfa evaportranspiration |
| `ERC` | energy release component |
| `BI` | burning index |
| `FM100` | 100-hour dead fuel moisture |
| `FM1000` | 1000-hour dead fuel moisture |

---

## `download_groads`

| Code / Variable | Description |
| :--- | :--- |
| `Americas` | Road network geometry for North and South America |
| `Global` | Global road network geometry (Geodatabase only) |
| `Africa` | Road network geometry for Africa |
| `Asia` | Road network geometry for Asia |
| `Europe` | Road network geometry for Europe |
| `Oceania East` | Road network geometry for Eastern Oceania |
| `Oceania West` | Road network geometry for Western Oceania |

---

## `download_hms`

| Code / Variable | Description |
| :--- | :--- |
| `Smoke` | Daily smoke plume polygons with density categories: Light, Medium, Heavy |
| `Fire` | Active fire point locations detected by NOAA GOES and MODIS |

---

## `download_huc`

| Code / Variable | Description |
| :--- | :--- |
| `HUC2` | Region (2-digit Hydrologic Unit Code) - largest watershed unit |
| `HUC4` | Subregion (4-digit HUC) |
| `HUC6` | Basin (6-digit HUC) |
| `HUC8` | Subbasin (8-digit HUC) |
| `HUC10` | Watershed (10-digit HUC) |
| `HUC12` | Subwatershed (12-digit HUC) - smallest unit |

---

## `download_koppen_geiger`

| Code / Variable | Description |
| :--- | :--- |
| `Af` | Tropical rainforest |
| `Am` | Tropical monsoon |
| `Aw` | Tropical savanna |
| `BSh` | Hot semi-arid (steppe) |
| `BSk` | Cold semi-arid (steppe) |
| `BWh` | Hot desert |
| `BWk` | Cold desert |
| `Cfa` | Humid subtropical (no dry season, hot summer) |
| `Cfb` | Oceanic (no dry season, warm summer) |
| `Cfc` | Subpolar oceanic |
| `Csa` | Hot-summer Mediterranean |
| `Csb` | Warm-summer Mediterranean |
| `Cwa` | Monsoon-influenced humid subtropical (hot summer) |
| `Cwb` | Monsoon-influenced oceanic (warm summer) |
| `Dfa` | Hot-summer humid continental |
| `Dfb` | Warm-summer humid continental |
| `Dfc` | Subarctic (cool summer) |
| `Dfd` | Subarctic (very cold winter) |
| `Dsa` | Mediterranean-influenced hot-summer humid continental |
| `Dsb` | Mediterranean-influenced warm-summer humid continental |
| `Dsc` | Mediterranean-influenced subarctic |
| `Dwa` | Monsoon-influenced hot-summer humid continental |
| `Dwb` | Monsoon-influenced warm-summer humid continental |
| `Dwc` | Monsoon-influenced subarctic |
| `Dwd` | Monsoon-influenced extremely cold subarctic |
| `EF` | Ice cap |
| `ET` | Tundra |

---

## `download_merra2`

| Code / Variable | Description |
| :--- | :--- |
| `inst1_2d_asm_Nx` | Single-level assimilation: SLP, PS, T2M, U10M, V10M, Q2M (1-hr inst) |
| `inst1_2d_int_Nx` | Single-level vertically integrated diagnostics (1-hr inst) |
| `inst1_2d_lfo_Nx` | Single-level land surface forcings (1-hr inst) |
| `inst3_3d_asm_Np` | 3D assimilation on pressure levels: T, U, V, Q, H (3-hr inst) |
| `inst3_3d_aer_Nv` | 3D aerosol mixing ratios on model levels: SO4, BC, OC, DU, SS (3-hr inst) |
| `inst3_3d_asm_Nv` | 3D assimilation on model levels: T, U, V, Q (3-hr inst) |
| `inst3_3d_chm_Nv` | 3D chemistry mixing ratios on model levels (3-hr inst) |
| `inst3_3d_gas_Nv` | 3D gas-phase species on model levels (3-hr inst) |
| `inst3_2d_gas_Nx` | Single-level gas-phase species (3-hr inst) |
| `inst6_3d_ana_Np` | 3D analysis increment on pressure levels (6-hr inst) |
| `inst6_3d_ana_Nv` | 3D analysis increment on model levels (6-hr inst) |
| `statD_2d_slv_Nx` | Single-level daily statistics: T2M, U10M, V10M, etc. |
| `tavg1_2d_adg_Nx` | Single-level aerosol diagnostics, gridded (1-hr avg) |
| `tavg1_2d_aer_Nx` | Single-level aerosol optical depth and surface PM (1-hr avg) |
| `tavg1_2d_chm_Nx` | Single-level chemistry diagnostics (1-hr avg) |
| `tavg1_2d_csp_Nx` | Single-level cloud microphysics (1-hr avg) |
| `tavg1_2d_flx_Nx` | Single-level surface turbulent fluxes: HLML, TLML, QVML (1-hr avg) |
| `tavg1_2d_int_Nx` | Single-level vertically integrated diagnostics (1-hr avg) |
| `tavg1_2d_lfo_Nx` | Single-level land surface forcing (1-hr avg) |
| `tavg1_2d_lnd_Nx` | Single-level land surface diagnostics (1-hr avg) |
| `tavg1_2d_ocn_Nx` | Single-level ocean surface diagnostics (1-hr avg) |
| `tavg1_2d_rad_Nx` | Single-level radiation diagnostics: SWGNT, LWGNT, SWTNT (1-hr avg) |
| `tavg1_2d_slv_Nx` | Single-level meteorology: T2M, QV2M, U10M, V10M, etc. (1-hr avg) |
| `tavg3_3d_mst_Ne` | 3D moist processes on eta levels (3-hr avg) |
| `tavg3_3d_trb_Ne` | 3D turbulence on eta levels (3-hr avg) |
| `tavg3_3d_nav_Ne` | 3D navigation/trajectory on eta levels (3-hr avg) |
| `tavg3_3d_cld_Np` | 3D cloud parameters on pressure levels (3-hr avg) |
| `tavg3_3d_mst_Np` | 3D moist processes on pressure levels (3-hr avg) |
| `tavg3_3d_rad_Np` | 3D radiative fluxes and heating on pressure levels (3-hr avg) |
| `tavg3_3d_tdt_Np` | 3D temperature tendency from physics on pressure levels (3-hr avg) |
| `tavg3_3d_trb_Np` | 3D turbulent tendencies on pressure levels (3-hr avg) |
| `tavg3_3d_udt_Np` | 3D wind tendencies on pressure levels (3-hr avg) |
| `tavg3_3d_odt_Np` | 3D ozone tendencies on pressure levels (3-hr avg) |
| `tavg3_3d_qdt_Np` | 3D water vapor tendencies on pressure levels (3-hr avg) |
| `tavg3_3d_asm_Nv` | 3D assimilation on model levels (3-hr avg) |
| `tavg3_3d_cld_Nv` | 3D cloud parameters on model levels (3-hr avg) |
| `tavg3_3d_mst_Nv` | 3D moist processes on model levels (3-hr avg) |
| `tavg3_3d_rad_Nv` | 3D radiative fluxes on model levels (3-hr avg) |
| `tavg3_2d_glc_Nx` | Single-level glaciology (3-hr avg) |

---

## `download_modis`

| Code / Variable | Description |
| :--- | :--- |
| `MOD09GA` | Terra Surface Reflectance Daily 500m |
| `MYD09GA` | Aqua Surface Reflectance Daily 500m |
| `MOD09GQ` | Terra Surface Reflectance Daily 250m |
| `MYD09GQ` | Aqua Surface Reflectance Daily 250m |
| `MOD09A1` | Terra Surface Reflectance 8-Day 500m |
| `MYD09A1` | Aqua Surface Reflectance 8-Day 500m |
| `MOD09Q1` | Terra Surface Reflectance 8-Day 250m |
| `MYD09Q1` | Aqua Surface Reflectance 8-Day 250m |
| `MOD11A1` | Terra Land Surface Temperature & Emissivity Daily 1km |
| `MYD11A1` | Aqua Land Surface Temperature & Emissivity Daily 1km |
| `MOD11A2` | Terra Land Surface Temperature & Emissivity 8-Day 1km |
| `MYD11A2` | Aqua Land Surface Temperature & Emissivity 8-Day 1km |
| `MOD11B1` | Terra Land Surface Temperature & Emissivity Daily 6km |
| `MYD11B1` | Aqua Land Surface Temperature & Emissivity Daily 6km |
| `MOD13A1` | Terra Vegetation Indices 16-Day 500m (NDVI, EVI) |
| `MYD13A1` | Aqua Vegetation Indices 16-Day 500m (NDVI, EVI) |
| `MOD13A2` | Terra Vegetation Indices 16-Day 1km (NDVI, EVI) |
| `MYD13A2` | Aqua Vegetation Indices 16-Day 1km (NDVI, EVI) |
| `MOD13A3` | Terra Vegetation Indices Monthly 1km (NDVI, EVI) |
| `MYD13A3` | Aqua Vegetation Indices Monthly 1km (NDVI, EVI) |
| `MOD06_L2` | Terra Atmosphere Cloud Properties L2 (5-min swath) |
| `MCD19A2` | MAIAC Land Aerosol Optical Depth Daily 1km |
| `VNP46A2` | VIIRS/NPP Daily Lunar Reflectance (Black Marble, night lights) |

---

## `download_narr`

| Code / Variable | Description |
| :--- | :--- |
| `air` | Air temperature (K) at surface/pressure levels |
| `apcp` | Total precipitation (kg/m^2) - accumulated |
| `dswrf` | Downward shortwave radiation flux (W/m^2) |
| `lhtfl` | Latent heat net flux (W/m^2) |
| `omega` | Vertical velocity (pressure) (Pa/s) - pressure levels |
| `pottmp` | Potential temperature (K) - pressure levels |
| `pr_wtr` | Precipitable water (kg/m^2) |
| `pres` | Surface pressure (Pa) |
| `rhum` | Relative humidity (%) at surface/pressure levels |
| `shum` | Specific humidity (kg/kg) - pressure levels |
| `skt` | Skin temperature (K) |
| `slp` | Sea-level pressure (Pa) |
| `snod` | Snow depth (m) |
| `snom` | Snow melt (kg/m^2) |
| `soill` | Soil moisture content (fraction) by layer |
| `tsoil` | Soil temperature (K) by layer |
| `uswrf` | Upward shortwave radiation flux (W/m^2) |
| `uwnd` | U-component of wind (m/s) |
| `vwnd` | V-component of wind (m/s) |
| `weasd` | Water equivalent of accumulated snow depth (kg/m^2) |
| `veg` | Vegetation fraction |
| `albedo` | Surface albedo |

---

## `download_nei`

| Code / Variable | Description |
| :--- | :--- |
| `NOx` | Nitrogen Oxides - criteria pollutant emissions by source |
| `SO2` | Sulfur Dioxide - criteria pollutant emissions by source |
| `VOC` | Volatile Organic Compounds - criteria pollutant |
| `CO` | Carbon Monoxide - criteria pollutant |
| `NH3` | Ammonia - criteria pollutant |
| `PM10` | Particulate Matter < 10 micrometers |
| `PM2.5` | Particulate Matter < 2.5 micrometers |
| `Pb` | Lead - criteria pollutant |

---

## `download_nlcd`

| Code / Variable | Description |
| :--- | :--- |
| `Land Cover` | Annual land cover classification (~20 classes: water, forest, developed, etc.) 30m |
| `Land Cover Change` | Binary map of pixels that changed land cover class between two years |
| `Land Cover Confidence` | Per-pixel confidence of land cover classification (0-100%) |
| `Fractional Impervious Surface` | Sub-pixel impervious surface fraction (0-100%) at 30m |
| `Impervious Descriptor` | Type of impervious surface: primary/secondary roads vs. urban |
| `Spectral Change Day of Year` | Day of year when spectral change was first detected (change driver timing) |

---

## `download_population`

| Code / Variable | Description |
| :--- | :--- |
| `UN_WPP_pop_density` | UN WPP-adjusted population density (persons/km^2), available at 30 arc-sec, 2.5 min, 15 min, 30 min, 60 min resolution for years 2000, 2005, 2010, 2015, 2020 |

---

## `download_prism`

| Code / Variable | Description |
| :--- | :--- |
| `ppt` | Precipitation (mm) |
| `tmin` | Minimum temperature (degrees C) |
| `tmax` | Maximum temperature (degrees C) |
| `tmean` | Mean temperature (degrees C) |
| `tdmean` | Mean dew point temperature (degrees C) |
| `vpdmin` | Minimum vapor pressure deficit (hPa) |
| `vpdmax` | Maximum vapor pressure deficit (hPa) |
| `solslope` | Sloped-surface solar radiation (W/m^2) - normals only |
| `soltotal` | Total global shortwave solar radiation on slope (W/m^2) - normals only |
| `solclear` | Clearness index (0-1) - normals only |
| `soltrans` | Atmospheric transmittance (0-1) - normals only |

---

## `download_terraclimate`

| Code / Variable | Description |
| :--- | :--- |
| `aet` | actual evapotranspiration |
| `def` | climate water deficit |
| `pet` | potential evapotranspiration |
| `ppt` | precipitation |
| `q` | runoff |
| `soil` | soil moisture |
| `srad` | downward surface shortwave radiation |
| `swe` | snow water equivalent - at end of month |
| `tmax` | max temperature |
| `tmin` | min temperature |
| `vap` | vapor pressure |
| `ws` | wind speed |
| `vpd` | vapor pressure deficit |
| `PDSI` | palmer drought severity index |

---

## `download_tri`

| Code / Variable | Description |
| :--- | :--- |
| `chemical_name` | Chemical name from TRI-listed substances (>700 chemicals) |
| `total_releases` | Total on- and off-site releases (lbs/year) per facility |
| `fugitive_air` | Fugitive or non-point air emissions (lbs/year) |
| `stack_air` | Point source air emissions (stack/vent) (lbs/year) |
| `water_discharge` | Surface water discharge (lbs/year) |
| `underground_injection` | Underground injection (Class I-V wells) (lbs/year) |
| `landfills` | Land disposal: landfills (lbs/year) |
| `on_site_release` | Total on-site environmental release (lbs/year) |
| `off_site_transfer` | Total off-site transfer for disposal/treatment (lbs/year) |
