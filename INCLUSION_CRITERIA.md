# GEOSPACE Data Catalog — Inclusion Criteria

**Version:** 1.0.0 (Draft)
**Last Updated:** March 30, 2026

This document defines the five criteria a dataset must satisfy to be included in the GEOSPACE data catalog.

---

## Criterion 1: Spatially Referenced for CONUS

The dataset must be geographically referenced to the contiguous United States (CONUS) — either as gridded raster data, georeferenced point locations, or linked to a standard US geographic unit (Census Tract, ZCTA, County, State). The spatial reference must be sufficient to support linkage with other GEOSPACE datasets at a common geographic level.

---

## Criterion 2: Relevant to Exposome-Informed Health Research

The dataset must contain variables that represent components of the human exposome — the totality of environmental exposures that influence human health across the lifespan (Wild, 2005; Rappaport & Smith, 2010). This includes, but is not limited to:

- **External specific exposures:** Chemical agents (air pollutants, water contaminants), physical agents (temperature, radiation, noise), and biological agents measured or modeled at a population-relevant spatial scale.

- **External general exposures:** Social and structural determinants of health — including socioeconomic conditions, neighborhood opportunity, educational access, housing quality, and social vulnerability — that characterize the contextual environment in which health outcomes arise.

- **Health outcomes and indicators:** Population-level measures of disease prevalence, morbidity, health behaviors, and health service utilization that serve as endpoints in exposure-outcome analyses.

- **Natural hazard events:** Acute environmental events (wildfires, storms, floods) and their measurable characteristics (intensity, frequency, duration, spatial extent) that represent episodic exposures with health consequences.

A dataset does not need to represent a direct chemical or physical agent to qualify. Under the exposome framework, the determination of whether a specific variable functions as an exposure, outcome, covariate, or effect modifier is made by the downstream researcher in the context of their study design — not by the data catalog.

> **Rationale:** The exposome framework (Wild, 2005) recognizes that health is shaped by the full spectrum of environmental conditions — from air pollution to neighborhood deprivation to green space access. Restricting "exposure" to the classical toxicological definition (a measurable agent contacting a biological receptor) would exclude social and structural determinants that are widely used in contemporary environmental epidemiology, public health, and pediatric health research. GEOSPACE explicitly serves this broader research community.

---

## Criterion 3: From an Authoritative, Citable Source

The dataset must be produced or curated by a recognized scientific agency, government body, academic institution, or established research program (e.g., NASA, ECMWF, EPA, CDC, NOAA, university research groups with DOIs). The source must have published methodology that documents how the data was collected, modeled, or derived.

---

## Criterion 4: Publicly Accessible and Reproducibly Retrievable

The dataset must be available through a public or free-registration data portal with a stable API, download URL, or data repository (e.g., Zenodo, Harvard Dataverse, government data portals). Access must be scriptable — a GEOSPACE download or processing script must be able to retrieve the data without manual intervention beyond initial credential setup.

---

## Criterion 5: Documented Spatial and Temporal Coverage

The dataset must have clearly documented spatial extent, spatial resolution or geographic unit, temporal resolution, and temporal extent. These metadata must be sufficient to populate all required fields in the GEOSPACE metadata catalog.

---

## References

- Wild, C. P. (2005). Complementing the genome with an "exposome": The outstanding challenge of environmental exposure measurement in molecular epidemiology. *Cancer Epidemiology, Biomarkers & Prevention*, 14(8), 1847–1850.
- Rappaport, S. M., & Smith, M. T. (2010). Environment and disease risks. *Science*, 330(6003), 460–461.
