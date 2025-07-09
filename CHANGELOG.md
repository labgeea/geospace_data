# Changelog

All notable changes to the GEOSPACE Geospatial Metadatabase Project Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [1.0.0] - 2025-07-08

### Added

- Initial stable release of GEOSPACE Geospatial Metadatabase Project Framework
- MODIS module with support for:
  - Vegetation indices (NDVI, EVI) from MOD13/MYD13 products
  - Land surface temperature (LST) from MOD11/MYD11 products  
  - Vegetation continuous fields (VCF) from MOD44/MYD44 products
  - Unified configuration system for all MODIS products
  - Quality control masking using MODIS QC flags
  - Automated tile mosaicking and reprojection to CONUS Albers
- ECMWF module with support for:
  - ERA5 reanalysis data download and processing
  - Multiple atmospheric and surface variables
  - Temporal and spatial subsetting capabilities
- GridMET module with support for:
  - High-resolution meteorological data for CONUS
  - Temperature, precipitation, humidity, wind variables
  - Daily time series processing
- Central version management system
- Comprehensive documentation for all modules
- Example workflows and troubleshooting guides
- Automated testing framework
- Cross-platform compatibility (Linux, macOS, Windows/WSL)

### Technical Details

- Python 3.8+ compatibility
- GDAL/OGR integration for spatial processing
- XArray/Rasterio for efficient data handling
- Parallel downloading capabilities
- Memory-efficient processing for large datasets
- Configurable quality control parameters
- Support for multiple output formats (GeoTIFF, NetCDF)

### Data Sources

- NASA Earthdata integration for MODIS products
- Copernicus Climate Data Store integration for ECMWF data
- University of Idaho GridMET data access
- Automated authentication handling
- Robust error handling and retry mechanisms

### Performance

- Optimized for CONUS-scale processing
- Configurable parallel processing
- Efficient memory management
- Tile-based processing for large datasets
- Compression and chunking optimizations

[Unreleased]: https://github.com/sandbox-msh/geospace_data/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/sandbox-msh/geospace_data/releases/tag/v1.0.0
