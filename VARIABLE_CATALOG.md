# GEOSPACE Variable Catalog

**Version:** 1.0.0 | **Last Updated:** July 8, 2025

Quick reference catalog of all variables supported by the GEOSPACE Framework.

## Summary

| Module | Variables | Resolution | Temporal | Data Source |
|--------|-----------|------------|----------|-------------|
| **MODIS** | 6 variables | 250m-1km | Daily-Annual | NASA Satellites |
| **ECMWF** | 7 variables | 31km | Daily | ERA5 Reanalysis |
| **GridMET** | 9 variables | 4km | Daily | University of Idaho |

---

## MODIS Variables

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **LST_Day** | Land surface temperature (day) | 1km | Daily | `LST` |
| **LST_Night** | Land surface temperature (night) | 1km | Daily | `LST` |
| **NDVI** | Vegetation index | 500m-1km | 16-day/Monthly | `NDVI` |
| **EVI** | Enhanced vegetation index | 500m-1km | 16-day/Monthly | `EVI` |
| **Percent_Tree_Cover** | Tree cover percentage | 250m | Annual | `VCF` |
| **Percent_NonTree_Vegetation** | Non-tree vegetation percentage | 250m | Annual | `VCF` |

---

## ECMWF Variables

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|--------------|--------------|--------------|
| **Temperature 2m** | Air temperature at 2m height | 31km | Hourly | `temperature_2m` |
| **Dewpoint 2m** | Dewpoint temperature at 2m | 31km | Hourly |`dewpoint_2m` |
| **Precipitation** | Daily total precipitation | 31km | Hourly | `total_precipitation` |
| **Surface Pressure** | Atmospheric pressure | 31km | Hourly | `surface_pressure` |
| **Boundary Layer Height** | Atmospheric mixing height | 31km | Hourly | `boundary_layer_height` |
| **Wind U 100m** | Eastward wind component | 31km | Hourly | `u_component_100m` |
| **Wind V 100m** | Northward wind component | 31km | Hourly | `v_component_100m` |

---

## GridMET Variables

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|--------------|--------------|--------------|
| **Maximum Temperature** | Daily maximum temperature | 31km | Hourly | `tmax` |
| **Minimum Temperature** | Daily minimum temperature | 31km | Hourly | `tmin` |
| **Mean Temperature** | Daily mean temperature | 31km | Hourly |`tmean` |
| **Precipitation** | Daily precipitation | 31km | Hourly | `pr` |
| **Relative Humidity** | Daily relative humidity | 31km | Hourly | `rh` |
| **Vapor Pressure Deficit** | Daily VPD | 31km | Hourly | `vpd` |
| **Specific Humidity** | Daily specific humidity | 31km | Hourly | `sph` |
| **Wind Speed** | Wind speed at 10m | 31km | Hourly | `vs` |
| **Wind Direction** | Wind direction at 10m | 31km | Hourly | `th` |

---

*For detailed usage and configuration options, see module-specific README files.*
