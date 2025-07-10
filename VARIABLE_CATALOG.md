# GEOSPACE Variable Catalog

**Version:** 1.1.0 | **Last Updated:** July 10, 2025

Quick reference catalog of all variables supported by the GEOSPACE Framework.

## Summary

| Module | Variables | Resolution | Temporal | Data Source |
|--------|-----------|------------|----------|-------------|
| **MODIS** | 4 variables | 250m-1km | Daily-Annual | NASA Satellites |
| **ECMWF** | 14 variables | 31km | Hourly | ERA5 Reanalysis |
| **GridMET** | 17 variables | 4km | Daily | University of Idaho |

---

## MODIS Variables

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **LST** | Land surface temperature | 1km | Daily | `LST` |
| **NDVI** | Normalized Difference Vegetation Index | 1km | Monthly | `NDVI` |
| **EVI** | Enhanced Vegetation Index | 1km | Monthly | `EVI` |
| **VCF** | Vegetation Continuous Fields (tree cover, non-tree vegetation) | 250m | Annual | `VCF` |

---

## ECMWF Variables

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **Temperature 2m** | Air temperature at 2m height | 31km | Hourly | `2m_temperature` |
| **Dewpoint 2m** | Dewpoint temperature at 2m | 31km | Hourly | `2m_dewpoint_temperature` |
| **Total Precipitation** | Daily total precipitation | 31km | Hourly | `total_precipitation` |
| **Surface Pressure** | Atmospheric surface pressure | 31km | Hourly | `surface_pressure` |
| **Sea Level Pressure** | Mean sea level pressure | 31km | Hourly | `mean_sea_level_pressure` |
| **Boundary Layer Height** | Atmospheric mixing height | 31km | Hourly | `boundary_layer_height` |
| **Wind U 100m** | Eastward wind component at 100m | 31km | Hourly | `100m_u_component_of_wind` |
| **Wind V 100m** | Northward wind component at 100m | 31km | Hourly | `100m_v_component_of_wind` |
| **Wind U 10m** | Eastward wind component at 10m | 31km | Hourly | `10m_u_component_of_wind` |
| **Wind V 10m** | Northward wind component at 10m | 31km | Hourly | `10m_v_component_of_wind` |
| **Relative Humidity** | Relative humidity | 31km | Hourly | `relative_humidity` |
| **Skin Temperature** | Surface skin temperature | 31km | Hourly | `skin_temperature` |
| **Total Cloud Cover** | Total cloud cover fraction | 31km | Hourly | `total_cloud_cover` |
| **Geopotential** | Geopotential height | 31km | Hourly | `geopotential` |

---

## GridMET Variables

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **Precipitation** | Daily total precipitation | 4km | Daily | `pr` |
| **Max Temperature** | Daily maximum air temperature | 4km | Daily | `tmmx` |
| **Min Temperature** | Daily minimum air temperature | 4km | Daily | `tmmn` |
| **Max Humidity** | Daily maximum relative humidity | 4km | Daily | `rmax` |
| **Min Humidity** | Daily minimum relative humidity | 4km | Daily | `rmin` |
| **Specific Humidity** | Daily mean specific humidity | 4km | Daily | `sph` |
| **Solar Radiation** | Daily mean surface downward shortwave radiation | 4km | Daily | `srad` |
| **Wind Speed** | Daily mean wind speed at 10m | 4km | Daily | `vs` |
| **Wind Direction** | Daily mean wind direction | 4km | Daily | `th` |
| **Vapor Pressure Deficit** | Daily mean vapor pressure deficit | 4km | Daily | `vpd` |
| **Burning Index** | Daily burning index | 4km | Daily | `bi` |
| **100-hr Fuel Moisture** | 100-hour dead fuel moisture | 4km | Daily | `fm100` |
| **1000-hr Fuel Moisture** | 1000-hour dead fuel moisture | 4km | Daily | `fm1000` |
| **Energy Release Component** | Daily energy release component | 4km | Daily | `erc` |
| **Reference ET (Alfalfa)** | Daily reference evapotranspiration (alfalfa) | 4km | Daily | `etr` |
| **Reference ET (Grass)** | Daily reference evapotranspiration (grass) | 4km | Daily | `eto` |
| **Palmer Drought Index** | Palmer Drought Severity Index (5-day average) | 4km | Pentad | `pdsi` |

---

*For detailed usage and configuration options, see module-specific README files.*
