# GEOSPACE Variable Catalog

**Version:** 1.8.0 | **Last Updated:** January 26, 2026

Quick reference catalog of all variables supported by the GEOSPACE Framework.

## Summary

| Module | Variables | Resolution | Temporal | Data Source |
|--------|-----------|------------|----------|-------------|
| **MODIS** | 4 variables | 250m-1km | Daily-Annual | NASA Satellites |
| **ECMWF** | 14 variables | 31km | Hourly | ERA5 Reanalysis |
| **GridMET** | 17 variables | 4km | Daily | University of Idaho |
| **CAMS**   | 6 variables | ~80km (0.75°)    | Hourly–Daily | Copernicus Atmosphere Monitoring Service (ECMWF) |
| **AQS**    | 6 variables | 31km | Hourly | US Environmental Protection Agency (EPA) |
| **SVI**    | 20+ variables | Census Tract | 2000-2022 (Bi-annual) | CDC / ATSDR |
| **COI**    | 20+ variables | Census Tract | 2012-2023 (Annual) | Child Opportunity Project |
| **PLACES** | 30+ variables | County/Place/Tract/ZCTA | 2020-2025 (Annual releases) | CDC PLACES |
| **FIRMS** | 6 variables | Point/Polygon | 2000-present (Daily) | NASA FIRMS |
| **STORMS** | 10+ variables | Point/Polygon | 1950-present (Event) | NOAA NCEI |

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

## CAMS Variables

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **PM2.5** | Fine particulate matter (≤2.5µm) mass concentration | ~80km | Hourly / Daily aggregated | `pm25` |
| **PM10**  | Coarse particulate matter (≤10µm) mass concentration | ~80km | Hourly / Daily aggregated | `pm10` |
| **NO₂**   | Nitrogen dioxide concentration | ~80km | Hourly / Daily aggregated | `no2` |
| **SO₂**   | Sulfur dioxide concentration | ~80km | Hourly / Daily aggregated | `so2` |
| **O₃**    | Ground-level ozone concentration | ~80km | Hourly / Daily aggregated | `o3` |
| **CO**    | Carbon monoxide concentration | ~80km | Hourly / Daily aggregated | `co` |

---

## AQS Variables

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **PM2.5** | Fine particulate matter (≤2.5µm) mass concentration | 31km | Hourly | `pm25` |
| **PM10**  | Coarse particulate matter (≤10µm) mass concentration | 31km | Hourly | `pm10` |
| **NO₂**   | Nitrogen dioxide concentration | 31km | Hourly | `no2` |
| **SO₂**   | Sulfur dioxide concentration | 31km | Hourly | `so2` |
| **O₃**    | Ground-level ozone concentration | 31km | Hourly | `o3` |
| **CO**    | Carbon monoxide concentration | 31km | Hourly | `co` |

---

## SVI Variables

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **overall_score** | Overall Social Vulnerability Index Score | Census Tract | Bi-annual | `overall_score` (SPL_THEMES) |
| **overall_rank** | Overall Social Vulnerability Index Rank | Census Tract | Bi-annual | `overall_rank` (RPL_THEMES) |
| **theme1_score** | Socioeconomic Status Score | Census Tract | Bi-annual | `theme1_score` (SPL_THEME1) |
| **theme1_rank** | Socioeconomic Status Rank | Census Tract | Bi-annual | `theme1_rank` (RPL_THEME1) |
| **theme2_score** | Household Composition & Disability Score | Census Tract | Bi-annual | `theme2_score` (SPL_THEME2) |
| **theme2_rank** | Household Composition & Disability Rank | Census Tract | Bi-annual | `theme2_rank` (RPL_THEME2) |
| **theme3_score** | Minority Status & Language Score | Census Tract | Bi-annual | `theme3_score` (SPL_THEME3) |
| **theme3_rank** | Minority Status & Language Rank | Census Tract | Bi-annual | `theme3_rank` (RPL_THEME3) |
| **theme4_score** | Housing Type & Transportation Score | Census Tract | Bi-annual | `theme4_score` (SPL_THEME4) |
| **theme4_rank** | Housing Type & Transportation Rank | Census Tract | Bi-annual | `theme4_rank` (RPL_THEME4) |
| **pov_pctl** | Percentile: Below Poverty | Census Tract | Bi-annual | `pov_pctl` (EPL_POV) |
| **unemp_pctl** | Percentile: Unemployed | Census Tract | Bi-annual | `unemp_pctl` (EPL_UNEMP) |
| **pci_pctl** | Percentile: Per Capita Income | Census Tract | Bi-annual | `pci_pctl` (EPL_PCI) |
| **nohsdip_pctl** | Percentile: No High School Diploma | Census Tract | Bi-annual | `nohsdip_pctl` (EPL_NOHSDP) |
| **age65_pctl** | Percentile: Aged 65 or Older | Census Tract | Bi-annual | `age65_pctl` (EPL_AGE65) |
| **age17_pctl** | Percentile: Aged 17 or Younger | Census Tract | Bi-annual | `age17_pctl` (EPL_AGE17) |
| **disabl_pctl** | Percentile: Civilian with a Disability | Census Tract | Bi-annual | `disabl_pctl` (EPL_DISABL) |
| **sngprnt_pctl** | Percentile: Single-Parent Households | Census Tract | Bi-annual | `sngprnt_pctl` (EPL_SNGPNT) |
| **minority_pctl** | Percentile: Minority | Census Tract | Bi-annual | `minority_pctl` (EPL_MINRTY) |
| **limeng_pctl** | Percentile: Speaks English "Less than Well" | Census Tract | Bi-annual | `limeng_pctl` (EPL_LIMENG) |
| **munit_pctl** | Percentile: Multi-Unit Structures | Census Tract | Bi-annual | `munit_pctl` (EPL_MUNIT) |
| **mobile_pctl** | Percentile: Mobile Homes | Census Tract | Bi-annual | `mobile_pctl` (EPL_MOBILE) |
| **crowd_pctl** | Percentile: Crowding | Census Tract | Bi-annual | `crowd_pctl` (EPL_CROWD) |
| **noveh_pctl** | Percentile: No Vehicle | Census Tract | Bi-annual | `noveh_pctl` (EPL_NOVEH) |
| **groupq_pctl** | Percentile: Group Quarters | Census Tract | Bi-annual | `groupq_pctl` (EPL_GROUPQ) |
| **uninsur_pctl** | Percentile: Uninsured | Census Tract | Bi-annual | `uninsur_pctl` (EPL_UNINSUR) |

---

## COI Variables

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **z_COI_nat** | Overall COI Z-Score (National Norm) | Census Tract | Annual | `z_COI_nat` |
| **c5_COI_nat** | Overall COI Quintile (National Norm) | Census Tract | Annual | `c5_COI_nat` |
| **r_COI_nat** | Overall COI Rank (National Norm) | Census Tract | Annual | `r_COI_nat` |
| **z_COI_stt** | Overall COI Z-Score (State Norm) | Census Tract | Annual | `z_COI_stt` |
| **c5_COI_stt** | Overall COI Quintile (State Norm) | Census Tract | Annual | `c5_COI_stt` |
| **r_COI_stt** | Overall COI Rank (State Norm) | Census Tract | Annual | `r_COI_stt` |
| **z_COI_met** | Overall COI Z-Score (Metro Norm) | Census Tract | Annual | `z_COI_met` |
| **c5_COI_met** | Overall COI Quintile (Metro Norm) | Census Tract | Annual | `c5_COI_met` |
| **r_COI_met** | Overall COI Rank (Metro Norm) | Census Tract | Annual | `r_COI_met` |
| **z_ED_nat** | Education Domain Z-Score (National Norm) | Census Tract | Annual | `z_ED_nat` |
| **c5_ED_nat** | Education Domain Quintile (National Norm) | Census Tract | Annual | `c5_ED_nat` |
| **r_ED_nat** | Education Domain Rank (National Norm) | Census Tract | Annual | `r_ED_nat` |
| **z_ED_stt** | Education Domain Z-Score (State Norm) | Census Tract | Annual | `z_ED_stt` |
| **c5_ED_stt** | Education Domain Quintile (State Norm) | Census Tract | Annual | `c5_ED_stt` |
| **r_ED_stt** | Education Domain Rank (State Norm) | Census Tract | Annual | `r_ED_stt` |
| **z_ED_met** | Education Domain Z-Score (Metro Norm) | Census Tract | Annual | `z_ED_met` |
| **c5_ED_met** | Education Domain Quintile (Metro Norm) | Census Tract | Annual | `c5_ED_met` |
| **r_ED_met** | Education Domain Rank (Metro Norm) | Census Tract | Annual | `r_ED_met` |
| **z_HE_nat** | Health/Environment Domain Z-Score (National Norm) | Census Tract | Annual | `z_HE_nat` |
| **c5_HE_nat** | Health/Environment Domain Quintile (National Norm) | Census Tract | Annual | `c5_HE_nat` |
| **r_HE_nat** | Health/Environment Domain Rank (National Norm) | Census Tract | Annual | `r_HE_nat` |
| **z_HE_stt** | Health/Environment Domain Z-Score (State Norm) | Census Tract | Annual | `z_HE_stt` |
| **c5_HE_stt** | Health/Environment Domain Quintile (State Norm) | Census Tract | Annual | `c5_HE_stt` |
| **r_HE_stt** | Health/Environment Domain Rank (State Norm) | Census Tract | Annual | `r_HE_stt` |
| **z_HE_met** | Health/Environment Domain Z-Score (Metro Norm) | Census Tract | Annual | `z_HE_met` |
| **c5_HE_met** | Health/Environment Domain Quintile (Metro Norm) | Census Tract | Annual | `c5_HE_met` |
| **r_HE_met** | Health/Environment Domain Rank (Metro Norm) | Census Tract | Annual | `r_HE_met` |
| **z_SE_nat** | Social/Economic Domain Z-Score (National Norm) | Census Tract | Annual | `z_SE_nat` |
| **c5_SE_nat** | Social/Economic Domain Quintile (National Norm) | Census Tract | Annual | `c5_SE_nat` |
| **r_SE_nat** | Social/Economic Domain Rank (National Norm) | Census Tract | Annual | `r_SE_nat` |
| **z_SE_stt** | Social/Economic Domain Z-Score (State Norm) | Census Tract | Annual | `z_SE_stt` |
| **c5_SE_stt** | Social/Economic Domain Quintile (State Norm) | Census Tract | Annual | `c5_SE_stt` |
| **r_SE_stt** | Social/Economic Domain Rank (State Norm) | Census Tract | Annual | `r_SE_stt` |
| **z_SE_met** | Social/Economic Domain Z-Score (Metro Norm) | Census Tract | Annual | `z_SE_met` |
| **c5_SE_met** | Social/Economic Domain Quintile (Metro Norm) | Census Tract | Annual | `c5_SE_met` |
| **r_SE_met** | Social/Economic Domain Rank (Metro Norm) | Census Tract | Annual | `r_SE_met` |

---

## PLACES Variables

CDC PLACES provides small-area estimates for health outcomes, prevention, and risk behaviors at County, Place, Census Tract, and ZCTA levels. Each variable includes `_lo` and `_hi` suffixes for 95% confidence intervals. Release years 2020-2025 are available; all geo levels are supported except ZCTA for 2024.

### Health Outcomes

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **arthritis_pct** | Arthritis among adults aged ≥18 years | County/Place/Tract/ZCTA | Annual release | `arthritis_pct` |
| **asthma_current_pct** | Current asthma among adults aged ≥18 years | County/Place/Tract/ZCTA | Annual release | `asthma_current_pct` |
| **high_bp_pct** | High blood pressure among adults aged ≥18 years | County/Place/Tract/ZCTA | Annual release | `high_bp_pct` |
| **cancer_pct** | Cancer (excluding skin cancer) among adults aged ≥18 years | County/Place/Tract/ZCTA | Annual release | `cancer_pct` |
| **high_cholesterol_pct** | High cholesterol (screened in past 5 years) | County/Place/Tract/ZCTA | Annual release | `high_cholesterol_pct` |
| **kidney_disease_pct** | Chronic kidney disease among adults aged ≥18 years | County/Place/Tract/ZCTA | Annual release | `kidney_disease_pct` |
| **copd_pct** | Chronic obstructive pulmonary disease | County/Place/Tract/ZCTA | Annual release | `copd_pct` |
| **heart_disease_pct** | Coronary heart disease among adults aged ≥18 years | County/Place/Tract/ZCTA | Annual release | `heart_disease_pct` |
| **depression_pct** | Depression among adults aged ≥18 years | County/Place/Tract/ZCTA | Annual release | `depression_pct` |
| **diabetes_pct** | Diagnosed diabetes among adults aged ≥18 years | County/Place/Tract/ZCTA | Annual release | `diabetes_pct` |
| **obesity_pct** | Obesity among adults aged ≥18 years | County/Place/Tract/ZCTA | Annual release | `obesity_pct` |
| **stroke_pct** | Stroke among adults aged ≥18 years | County/Place/Tract/ZCTA | Annual release | `stroke_pct` |

### Prevention

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **dental_visit_pct** | Visits to dentist or dental clinic | County/Place/Tract/ZCTA | Annual release | `dental_visit_pct` |
| **checkup_pct** | Routine checkup within the past year | County/Place/Tract/ZCTA | Annual release | `checkup_pct` |
| **cholesterol_screening_pct** | Cholesterol screening among adults | County/Place/Tract/ZCTA | Annual release | `cholesterol_screening_pct` |
| **colorectal_screening_pct** | Colorectal cancer screening (ages 50-75) | County/Place/Tract/ZCTA | Annual release | `colorectal_screening_pct` |
| **mammography_pct** | Mammography use among women aged 50-74 | County/Place/Tract/ZCTA | Annual release | `mammography_pct` |
| **cervical_screening_pct** | Cervical cancer screening (women 21-65) | County/Place/Tract/ZCTA | Annual release | `cervical_screening_pct` |
| **bp_medication_pct** | Taking BP medication among adults with high BP | County/Place/Tract/ZCTA | Annual release | `bp_medication_pct` |
| **preventive_men65_pct** | Men ≥65 up to date on preventive services | County/Place/Tract/ZCTA | Annual release | `preventive_men65_pct` |
| **preventive_women65_pct** | Women ≥65 up to date on preventive services | County/Place/Tract/ZCTA | Annual release | `preventive_women65_pct` |

### Health Risk Behaviors

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **binge_drinking_pct** | Binge drinking among adults aged ≥18 years | County/Place/Tract/ZCTA | Annual release | `binge_drinking_pct` |
| **smoking_pct** | Current smoking among adults aged ≥18 years | County/Place/Tract/ZCTA | Annual release | `smoking_pct` |
| **physical_inactivity_pct** | No leisure-time physical activity | County/Place/Tract/ZCTA | Annual release | `physical_inactivity_pct` |
| **short_sleep_pct** | Sleeping less than 7 hours | County/Place/Tract/ZCTA | Annual release | `short_sleep_pct` |

### Health Status

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **health_poor_pct** | Fair or poor self-rated health status | County/Place/Tract/ZCTA | Annual release | `health_poor_pct` |
| **physical_distress_pct** | Physical health not good for ≥14 days | County/Place/Tract/ZCTA | Annual release | `physical_distress_pct` |
| **mental_distress_pct** | Mental health not good for ≥14 days | County/Place/Tract/ZCTA | Annual release | `mental_distress_pct` |

### Disabilities (Available in some releases)

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **disability_any_pct** | Any disability among adults | County/Place/Tract/ZCTA | Annual release | `disability_any_pct` |
| **disability_cognitive_pct** | Cognitive disability | County/Place/Tract/ZCTA | Annual release | `disability_cognitive_pct` |
| **disability_hearing_pct** | Hearing disability | County/Place/Tract/ZCTA | Annual release | `disability_hearing_pct` |
| **disability_mobility_pct** | Mobility disability | County/Place/Tract/ZCTA | Annual release | `disability_mobility_pct` |
| **disability_vision_pct** | Vision disability | County/Place/Tract/ZCTA | Annual release | `disability_vision_pct` |
| **disability_selfcare_pct** | Self-care disability | County/Place/Tract/ZCTA | Annual release | `disability_selfcare_pct` |
| **disability_independent_pct** | Independent living disability | County/Place/Tract/ZCTA | Annual release | `disability_independent_pct` |

## FIRMS Variables

NASA FIRMS active fire data. Raw data is point-based; processing can aggregate to polygons.

### Raw Fire Detection Variables

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **latitude** | Fire pixel center latitude | Point | Instantaneous | `latitude` |
| **longitude** | Fire pixel center longitude | Point | Instantaneous | `longitude` |
| **brightness** | Brightness temperature (MODIS) | 1km | Instantaneous | `brightness` |
| **bright_ti4** | I-4 channel brightness temp (VIIRS) | 375m | Instantaneous | `bright_ti4` |
| **frp** | Fire Radiative Power (MW) | 375m-1km | Instantaneous | `frp` |
| **confidence** | Detection confidence (0-100 or low/nominal/high) | 375m-1km | Instantaneous | `confidence` |
| **acq_date** | Acquisition date | - | Daily | `acq_date` |
| **acq_time** | Acquisition time (UTC, HHMM) | - | Instantaneous | `acq_time` |
| **satellite** | Satellite name (Terra, Aqua, S-NPP, NOAA-20/21) | - | - | `satellite` |
| **daynight** | Day (D) or Night (N) detection | - | - | `daynight` |

### Aggregated Variables (from Processing Script)

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **fire_count** | Number of fire detections | County/ZCTA/State | Daily-Annual | `fire_count` |
| **frp_total** | Total Fire Radiative Power (MW) | County/ZCTA/State | Daily-Annual | `frp_total` |
| **frp_mean** | Mean Fire Radiative Power (MW) | County/ZCTA/State | Daily-Annual | `frp_mean` |
| **frp_max** | Maximum Fire Radiative Power (MW) | County/ZCTA/State | Daily-Annual | `frp_max` |
| **fire_days** | Number of unique days with detections | County/ZCTA/State | Monthly-Annual | `fire_days` |
| **high_conf_count** | Count of high-confidence (≥80) detections | County/ZCTA/State | Daily-Annual | `high_conf_count` |

---

## STORMS Variables

NOAA Storm Events Database. Event-based data.

| Variable | Description | Resolution | Temporal | Script Alias |
|----------|-------------|------------|----------|--------------|
| **event_type** | Type of storm event (e.g., Flood, Tornado) | - | Event | `event_type` |
| **begin_timestamp** | Date and time event started | - | Instantaneous | `begin_timestamp` |
| **begin_lat** | Start latitude (if available) | Point | - | `begin_lat` |
| **begin_lon** | Start longitude (if available) | Point | - | `begin_lon` |
| **damage_property_num**| Estimated property damage in USD | - | Event | `damage_property_num` |
| **damage_crops_num** | Estimated crop damage in USD | - | Event | `damage_crops_num` |
| **deaths_direct** | Number of direct fatalities | - | Event | `deaths_direct` |
| **injuries_direct** | Number of direct injuries | - | Event | `injuries_direct` |
| **magnitude** | Magnitude value (wind speed, hail size, etc.) | - | Event | `magnitude` |
| **magnitude_type** | Units for magnitude (e.g., knots, inches) | - | Event | `magnitude_type` |
| **state** | State name (upper case) | Polygon | - | `state` |
| **cz_name** | County or Zone name | Polygon | - | `cz_name` |


*For detailed usage and configuration options, see module-specific README files.*

---