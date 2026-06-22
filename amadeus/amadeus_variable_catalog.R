#!/usr/bin/env Rscript
# amadeus_variable_catalog.R
# Catalogs available variables for each amadeus download function dataset
# No data is downloaded - uses internal code tables and dataset metadata

library(amadeus)

output <- list()

# ===========================================================================
# 1. download_aqs -- EPA AQS parameter codes (no download needed)
# ===========================================================================
aqs_vars <- data.frame(
  code = c("44201", "42401", "42101", "42602", "88101", "88502",
           "81102", "14129", "85129"),
  description = c(
    "Ozone (O3)",
    "Sulfur dioxide (SO2)",
    "Carbon monoxide (CO)",
    "Nitrogen dioxide (NO2)",
    "PM2.5 - Local Conditions (FRM/FEM)",
    "PM2.5 - Speciation",
    "PM10 - Local Conditions",
    "Lead PM10 LC",
    "PM10 - Non-FRM/FEM Mass"
  )
)
output[["download_aqs"]] <- aqs_vars

# ===========================================================================
# 2. download_cropscape -- USDA CDL (raster crop categories, no variable list)
# ===========================================================================
cdl_vars <- data.frame(
  code = c("CDL_raster"),
  description = c(
    "Annual cropland raster with ~100 crop/land-use categories (e.g., corn, soybeans, developed, forest)"
  )
)
output[["download_cropscape"]] <- cdl_vars

# ===========================================================================
# 3. download_ecoregion -- EPA Ecoregions (implicit shapefile)
# ===========================================================================
eco_vars <- data.frame(
  code = c("NA_L1CODE", "NA_L2CODE", "US_L3CODE", "US_L4CODE"),
  description = c(
    "Level 1 Ecoregion code (continental scale)",
    "Level 2 Ecoregion code (sub-continental scale)",
    "Level 3 Ecoregion code (regional scale)",
    "Level 4 Ecoregion code (local scale)"
  )
)
output[["download_ecoregion"]] <- eco_vars

# ===========================================================================
# 4. download_edgar -- EDGAR emissions species
# ===========================================================================
edgar_vars <- data.frame(
  code = c("BC", "CO", "NH3", "NMVOC", "NOx", "OC", "PM10", "PM2.5", "SO2"),
  description = c(
    "Black Carbon",
    "Carbon Monoxide",
    "Ammonia",
    "Non-Methane Volatile Organic Compounds",
    "Nitrogen Oxides",
    "Organic Carbon",
    "Particulate Matter < 10 micrometers",
    "Particulate Matter < 2.5 micrometers",
    "Sulfur Dioxide"
  )
)
output[["download_edgar"]] <- edgar_vars

# ===========================================================================
# 5. download_geos -- NASA GEOS-CF collections
# ===========================================================================
geos_vars <- data.frame(
  code = c(
    "aqc_tavg_1hr_g1440x721_v1",
    "chm_tavg_1hr_g1440x721_v1",
    "met_tavg_1hr_g1440x721_x1",
    "xgc_tavg_1hr_g1440x721_x1",
    "chm_inst_1hr_g1440x721_p23",
    "met_inst_1hr_g1440x721_p23"
  ),
  description = c(
    "Air quality constituents (tavg, surface): O3, NO, NO2, CO, PM2.5, etc.",
    "Chemistry (tavg, surface): photolysis rates, aerosol species, oxidants",
    "Meteorology (tavg, surface): T2M, U10M, V10M, Q2M, PS, etc.",
    "Extended gas-phase chemistry (tavg, surface)",
    "Chemistry (instantaneous, pressure levels 23): aerosol/gas profiles",
    "Meteorology (instantaneous, pressure levels 23): T, U, V, Q profiles"
  )
)
output[["download_geos"]] <- geos_vars

# ===========================================================================
# 6. download_gmted -- USGS GMTED2010 elevation statistics
# ===========================================================================
gmted_vars <- data.frame(
  code = c("be", "ds", "md", "mi", "mn", "mx", "sd"),
  description = c(
    "Breakline Emphasis - preserves ridgelines and valleys",
    "Systematic Subsample - regular grid subsample of source elevation",
    "Median Statistic - median elevation within aggregation cell",
    "Minimum Statistic - minimum elevation within aggregation cell",
    "Mean Statistic - mean elevation within aggregation cell",
    "Maximum Statistic - maximum elevation within aggregation cell",
    "Standard Deviation Statistic - terrain roughness within cell"
  )
)
output[["download_gmted"]] <- gmted_vars

# ===========================================================================
# 7. download_gridmet -- gridMET (from internal code table)
# ===========================================================================
gm_raw <- process_gridmet_codes("all")
gridmet_vars <- data.frame(
  code        = gm_raw[, 2],
  description = gm_raw[, 1]
)
output[["download_gridmet"]] <- gridmet_vars

# ===========================================================================
# 8. download_groads -- SEDAC gROADS regions
# ===========================================================================
groads_vars <- data.frame(
  code = c("Americas", "Global", "Africa", "Asia", "Europe",
           "Oceania East", "Oceania West"),
  description = c(
    "Road network geometry for North and South America",
    "Global road network geometry (Geodatabase only)",
    "Road network geometry for Africa",
    "Road network geometry for Asia",
    "Road network geometry for Europe",
    "Road network geometry for Eastern Oceania",
    "Road network geometry for Western Oceania"
  )
)
output[["download_groads"]] <- groads_vars

# ===========================================================================
# 9. download_hms -- NOAA HMS fire/smoke plumes
# ===========================================================================
hms_vars <- data.frame(
  code = c("Smoke", "Fire"),
  description = c(
    "Daily smoke plume polygons with density categories: Light, Medium, Heavy",
    "Active fire point locations detected by NOAA GOES and MODIS"
  )
)
output[["download_hms"]] <- hms_vars

# ===========================================================================
# 10. download_huc -- USGS NHDPlus Watershed Boundary Dataset
# ===========================================================================
huc_vars <- data.frame(
  code = c("HUC2", "HUC4", "HUC6", "HUC8", "HUC10", "HUC12"),
  description = c(
    "Region (2-digit Hydrologic Unit Code) - largest watershed unit",
    "Subregion (4-digit HUC)",
    "Basin (6-digit HUC)",
    "Subbasin (8-digit HUC)",
    "Watershed (10-digit HUC)",
    "Subwatershed (12-digit HUC) - smallest unit"
  )
)
output[["download_huc"]] <- huc_vars

# ===========================================================================
# 11. download_koppen_geiger -- Koppen-Geiger climate classes
# ===========================================================================
kg_vars <- data.frame(
  code = c(
    "Af","Am","Aw","BSh","BSk","BWh","BWk",
    "Cfa","Cfb","Cfc","Csa","Csb","Cwa","Cwb",
    "Dfa","Dfb","Dfc","Dfd","Dsa","Dsb","Dsc","Dwa","Dwb","Dwc","Dwd",
    "EF","ET"
  ),
  description = c(
    "Tropical rainforest", "Tropical monsoon", "Tropical savanna",
    "Hot semi-arid (steppe)", "Cold semi-arid (steppe)",
    "Hot desert", "Cold desert",
    "Humid subtropical (no dry season, hot summer)",
    "Oceanic (no dry season, warm summer)",
    "Subpolar oceanic",
    "Hot-summer Mediterranean", "Warm-summer Mediterranean",
    "Monsoon-influenced humid subtropical (hot summer)",
    "Monsoon-influenced oceanic (warm summer)",
    "Hot-summer humid continental",
    "Warm-summer humid continental",
    "Subarctic (cool summer)", "Subarctic (very cold winter)",
    "Mediterranean-influenced hot-summer humid continental",
    "Mediterranean-influenced warm-summer humid continental",
    "Mediterranean-influenced subarctic",
    "Monsoon-influenced hot-summer humid continental",
    "Monsoon-influenced warm-summer humid continental",
    "Monsoon-influenced subarctic",
    "Monsoon-influenced extremely cold subarctic",
    "Ice cap", "Tundra"
  )
)
output[["download_koppen_geiger"]] <- kg_vars

# ===========================================================================
# 12. download_merra2 -- NASA MERRA-2 collections
# ===========================================================================
merra2_vars <- data.frame(
  code = c(
    "inst1_2d_asm_Nx", "inst1_2d_int_Nx", "inst1_2d_lfo_Nx",
    "inst3_3d_asm_Np", "inst3_3d_aer_Nv", "inst3_3d_asm_Nv",
    "inst3_3d_chm_Nv", "inst3_3d_gas_Nv", "inst3_2d_gas_Nx",
    "inst6_3d_ana_Np", "inst6_3d_ana_Nv", "statD_2d_slv_Nx",
    "tavg1_2d_adg_Nx", "tavg1_2d_aer_Nx", "tavg1_2d_chm_Nx",
    "tavg1_2d_csp_Nx", "tavg1_2d_flx_Nx", "tavg1_2d_int_Nx",
    "tavg1_2d_lfo_Nx", "tavg1_2d_lnd_Nx", "tavg1_2d_ocn_Nx",
    "tavg1_2d_rad_Nx", "tavg1_2d_slv_Nx",
    "tavg3_3d_mst_Ne", "tavg3_3d_trb_Ne", "tavg3_3d_nav_Ne",
    "tavg3_3d_cld_Np", "tavg3_3d_mst_Np", "tavg3_3d_rad_Np",
    "tavg3_3d_tdt_Np", "tavg3_3d_trb_Np", "tavg3_3d_udt_Np",
    "tavg3_3d_odt_Np", "tavg3_3d_qdt_Np",
    "tavg3_3d_asm_Nv", "tavg3_3d_cld_Nv", "tavg3_3d_mst_Nv",
    "tavg3_3d_rad_Nv", "tavg3_2d_glc_Nx"
  ),
  description = c(
    "Single-level assimilation: SLP, PS, T2M, U10M, V10M, Q2M (1-hr inst)",
    "Single-level vertically integrated diagnostics (1-hr inst)",
    "Single-level land surface forcings (1-hr inst)",
    "3D assimilation on pressure levels: T, U, V, Q, H (3-hr inst)",
    "3D aerosol mixing ratios on model levels: SO4, BC, OC, DU, SS (3-hr inst)",
    "3D assimilation on model levels: T, U, V, Q (3-hr inst)",
    "3D chemistry mixing ratios on model levels (3-hr inst)",
    "3D gas-phase species on model levels (3-hr inst)",
    "Single-level gas-phase species (3-hr inst)",
    "3D analysis increment on pressure levels (6-hr inst)",
    "3D analysis increment on model levels (6-hr inst)",
    "Single-level daily statistics: T2M, U10M, V10M, etc.",
    "Single-level aerosol diagnostics, gridded (1-hr avg)",
    "Single-level aerosol optical depth and surface PM (1-hr avg)",
    "Single-level chemistry diagnostics (1-hr avg)",
    "Single-level cloud microphysics (1-hr avg)",
    "Single-level surface turbulent fluxes: HLML, TLML, QVML (1-hr avg)",
    "Single-level vertically integrated diagnostics (1-hr avg)",
    "Single-level land surface forcing (1-hr avg)",
    "Single-level land surface diagnostics (1-hr avg)",
    "Single-level ocean surface diagnostics (1-hr avg)",
    "Single-level radiation diagnostics: SWGNT, LWGNT, SWTNT (1-hr avg)",
    "Single-level meteorology: T2M, QV2M, U10M, V10M, etc. (1-hr avg)",
    "3D moist processes on eta levels (3-hr avg)",
    "3D turbulence on eta levels (3-hr avg)",
    "3D navigation/trajectory on eta levels (3-hr avg)",
    "3D cloud parameters on pressure levels (3-hr avg)",
    "3D moist processes on pressure levels (3-hr avg)",
    "3D radiative fluxes and heating on pressure levels (3-hr avg)",
    "3D temperature tendency from physics on pressure levels (3-hr avg)",
    "3D turbulent tendencies on pressure levels (3-hr avg)",
    "3D wind tendencies on pressure levels (3-hr avg)",
    "3D ozone tendencies on pressure levels (3-hr avg)",
    "3D water vapor tendencies on pressure levels (3-hr avg)",
    "3D assimilation on model levels (3-hr avg)",
    "3D cloud parameters on model levels (3-hr avg)",
    "3D moist processes on model levels (3-hr avg)",
    "3D radiative fluxes on model levels (3-hr avg)",
    "Single-level glaciology (3-hr avg)"
  )
)
output[["download_merra2"]] <- merra2_vars

# ===========================================================================
# 13. download_modis -- NASA MODIS products
# ===========================================================================
modis_vars <- data.frame(
  code = c(
    "MOD09GA","MYD09GA","MOD09GQ","MYD09GQ",
    "MOD09A1","MYD09A1","MOD09Q1","MYD09Q1",
    "MOD11A1","MYD11A1","MOD11A2","MYD11A2",
    "MOD11B1","MYD11B1","MOD13A1","MYD13A1",
    "MOD13A2","MYD13A2","MOD13A3","MYD13A3",
    "MOD06_L2","MCD19A2","VNP46A2"
  ),
  description = c(
    "Terra Surface Reflectance Daily 500m",
    "Aqua Surface Reflectance Daily 500m",
    "Terra Surface Reflectance Daily 250m",
    "Aqua Surface Reflectance Daily 250m",
    "Terra Surface Reflectance 8-Day 500m",
    "Aqua Surface Reflectance 8-Day 500m",
    "Terra Surface Reflectance 8-Day 250m",
    "Aqua Surface Reflectance 8-Day 250m",
    "Terra Land Surface Temperature & Emissivity Daily 1km",
    "Aqua Land Surface Temperature & Emissivity Daily 1km",
    "Terra Land Surface Temperature & Emissivity 8-Day 1km",
    "Aqua Land Surface Temperature & Emissivity 8-Day 1km",
    "Terra Land Surface Temperature & Emissivity Daily 6km",
    "Aqua Land Surface Temperature & Emissivity Daily 6km",
    "Terra Vegetation Indices 16-Day 500m (NDVI, EVI)",
    "Aqua Vegetation Indices 16-Day 500m (NDVI, EVI)",
    "Terra Vegetation Indices 16-Day 1km (NDVI, EVI)",
    "Aqua Vegetation Indices 16-Day 1km (NDVI, EVI)",
    "Terra Vegetation Indices Monthly 1km (NDVI, EVI)",
    "Aqua Vegetation Indices Monthly 1km (NDVI, EVI)",
    "Terra Atmosphere Cloud Properties L2 (5-min swath)",
    "MAIAC Land Aerosol Optical Depth Daily 1km",
    "VIIRS/NPP Daily Lunar Reflectance (Black Marble, night lights)"
  )
)
output[["download_modis"]] <- modis_vars

# ===========================================================================
# 14. download_narr -- NOAA NARR variables
# ===========================================================================
narr_vars <- data.frame(
  code = c(
    "air", "apcp", "dswrf", "lhtfl", "omega",
    "pottmp", "pr_wtr", "pres", "rhum", "shum",
    "skt", "slp", "snod", "snom", "soill",
    "tsoil", "uswrf", "uwnd", "vwnd", "weasd",
    "veg", "albedo"
  ),
  description = c(
    "Air temperature (K) at surface/pressure levels",
    "Total precipitation (kg/m^2) - accumulated",
    "Downward shortwave radiation flux (W/m^2)",
    "Latent heat net flux (W/m^2)",
    "Vertical velocity (pressure) (Pa/s) - pressure levels",
    "Potential temperature (K) - pressure levels",
    "Precipitable water (kg/m^2)",
    "Surface pressure (Pa)",
    "Relative humidity (%) at surface/pressure levels",
    "Specific humidity (kg/kg) - pressure levels",
    "Skin temperature (K)",
    "Sea-level pressure (Pa)",
    "Snow depth (m)",
    "Snow melt (kg/m^2)",
    "Soil moisture content (fraction) by layer",
    "Soil temperature (K) by layer",
    "Upward shortwave radiation flux (W/m^2)",
    "U-component of wind (m/s)",
    "V-component of wind (m/s)",
    "Water equivalent of accumulated snow depth (kg/m^2)",
    "Vegetation fraction",
    "Surface albedo"
  )
)
output[["download_narr"]] <- narr_vars

# ===========================================================================
# 15. download_nei -- EPA NEI (comprehensive emissions inventory)
# ===========================================================================
nei_vars <- data.frame(
  code = c(
    "NOx", "SO2", "VOC", "CO", "NH3",
    "PM10", "PM2.5", "Pb"
  ),
  description = c(
    "Nitrogen Oxides - criteria pollutant emissions by source",
    "Sulfur Dioxide - criteria pollutant emissions by source",
    "Volatile Organic Compounds - criteria pollutant",
    "Carbon Monoxide - criteria pollutant",
    "Ammonia - criteria pollutant",
    "Particulate Matter < 10 micrometers",
    "Particulate Matter < 2.5 micrometers",
    "Lead - criteria pollutant"
  )
)
output[["download_nei"]] <- nei_vars

# ===========================================================================
# 16. download_nlcd -- MRLC NLCD products
# ===========================================================================
nlcd_vars <- data.frame(
  code = c(
    "Land Cover",
    "Land Cover Change",
    "Land Cover Confidence",
    "Fractional Impervious Surface",
    "Impervious Descriptor",
    "Spectral Change Day of Year"
  ),
  description = c(
    "Annual land cover classification (~20 classes: water, forest, developed, etc.) 30m",
    "Binary map of pixels that changed land cover class between two years",
    "Per-pixel confidence of land cover classification (0-100%)",
    "Sub-pixel impervious surface fraction (0-100%) at 30m",
    "Type of impervious surface: primary/secondary roads vs. urban",
    "Day of year when spectral change was first detected (change driver timing)"
  )
)
output[["download_nlcd"]] <- nlcd_vars

# ===========================================================================
# 17. download_population -- SEDAC GPW population density
# ===========================================================================
pop_vars <- data.frame(
  code = c("UN_WPP_pop_density"),
  description = c(
    "UN WPP-adjusted population density (persons/km^2), available at 30 arc-sec, 2.5 min, 15 min, 30 min, 60 min resolution for years 2000, 2005, 2010, 2015, 2020"
  )
)
output[["download_population"]] <- pop_vars

# ===========================================================================
# 18. download_prism -- PRISM climate elements
# ===========================================================================
prism_vars <- data.frame(
  code = c(
    "ppt", "tmin", "tmax", "tmean",
    "tdmean", "vpdmin", "vpdmax",
    "solslope", "soltotal", "solclear", "soltrans"
  ),
  description = c(
    "Precipitation (mm)",
    "Minimum temperature (degrees C)",
    "Maximum temperature (degrees C)",
    "Mean temperature (degrees C)",
    "Mean dew point temperature (degrees C)",
    "Minimum vapor pressure deficit (hPa)",
    "Maximum vapor pressure deficit (hPa)",
    "Sloped-surface solar radiation (W/m^2) - normals only",
    "Total global shortwave solar radiation on slope (W/m^2) - normals only",
    "Clearness index (0-1) - normals only",
    "Atmospheric transmittance (0-1) - normals only"
  )
)
output[["download_prism"]] <- prism_vars

# ===========================================================================
# 19. download_terraclimate -- TerraClimate (from internal code table)
# ===========================================================================
tc_raw <- process_terraclimate_codes("all")
terraclimate_vars <- data.frame(
  code        = tc_raw[, 2],
  description = tc_raw[, 1]
)
output[["download_terraclimate"]] <- terraclimate_vars

# ===========================================================================
# 20. download_tri -- EPA TRI (Toxics Release Inventory)
# ===========================================================================
tri_vars <- data.frame(
  code = c(
    "chemical_name", "total_releases",
    "fugitive_air", "stack_air",
    "water_discharge", "underground_injection",
    "landfills", "on_site_release", "off_site_transfer"
  ),
  description = c(
    "Chemical name from TRI-listed substances (>700 chemicals)",
    "Total on- and off-site releases (lbs/year) per facility",
    "Fugitive or non-point air emissions (lbs/year)",
    "Point source air emissions (stack/vent) (lbs/year)",
    "Surface water discharge (lbs/year)",
    "Underground injection (Class I-V wells) (lbs/year)",
    "Land disposal: landfills (lbs/year)",
    "Total on-site environmental release (lbs/year)",
    "Total off-site transfer for disposal/treatment (lbs/year)"
  )
)
output[["download_tri"]] <- tri_vars

# ===========================================================================
# Output: print markdown tables for each function
# ===========================================================================
md_output <- character(0)

md_output <- c(md_output, "# `amadeus` Download Functions — Variable Catalog\n")
md_output <- c(md_output, "_Generated from amadeus internal metadata and dataset documentation._\n\n")

for (fn_name in names(output)) {
  df <- output[[fn_name]]
  md_output <- c(md_output, sprintf("---\n\n## `%s`\n\n", fn_name))
  md_output <- c(md_output, "| Code / Variable | Description |\n")
  md_output <- c(md_output, "| :--- | :--- |\n")
  for (i in seq_len(nrow(df))) {
    row_str <- sprintf("| `%s` | %s |\n", df$code[i], df$description[i])
    md_output <- c(md_output, row_str)
  }
  md_output <- c(md_output, "\n")
}

out_file <- file.path(dirname(normalizePath(commandArgs()[4])),
                      "amadeus_variable_catalog_output.md")
# fallback path
out_file <- "amadeus_variable_catalog_output.md"

writeLines(md_output, out_file)
cat(sprintf("\nDone. Output written to: %s\n", out_file))
cat(paste(md_output, collapse = ""))
