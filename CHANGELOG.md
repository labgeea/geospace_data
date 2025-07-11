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

## [1.2.0] - 2025-07-11
### Added
- Comprehensive metadata catalog system with 35 documented variables
- CSV-based catalog for version control and collaboration
- Automated Excel conversion script for Zenodo publishing
- Git-friendly catalog management with automated Excel generation
- Updated catalog with version-specific GitHub URLs
- Complete documentation for MODIS (4), ECMWF (14), and GridMET (17) variables
- Version tracking, script aliases, and processing status fields
- CATALOG_README.md with workflow documentation

### Changed
- All GitHub links in metadata now point to version-specific URLs (v1.2.0)
- Enhanced project documentation and citation capabilities

## [1.1.0] - 2025-07-10
### Added
- CMR API integration for MODIS downloads
- Enhanced error handling and metadata access
- Cloud-ready infrastructure support

### Changed
- MODIS download backend migrated from LP DAAC Data Pool to CMR API
- ECMWF download script had incorrect variable option (specific humidity)
- Improved reliability and performance for MODIS data access
- VARIABLE CATALOG updated with additional variables
  - Updated variable counts: MODIS (4), ECMWF (14), GridMET (17)

### Deprecated
- LP DAAC Data Pool access (retired by NASA on June 30, 2025)

### Removed
- Remove specific humidity (sp) in ECMWF download script and bash wrapper

## [1.0.1] - 2025-07-09
### Added
- DEVELOPMENT_WORKFLOW.md
  - Document semantic versioning process
  - Include step-by-step release workflow
  - Add guidelines for adding new modules
  - Provide troubleshooting and best practices
- VARIABLE_CATALOG.md
  - Document all 22+ variables across MODIS, ECMWF, and GridMET modules
  - Include technical specifications, usage examples, and processing details
  - Add variable packages and quality control information
  - Provide complete reference for framework capabilities

### Changed
- README.md
  - Added comments to directory structure description for readability
- modis_README.md
  - Changed default editor: vim --> nano
- modis_download_generic.py
  - Added month to date field (2025 --> July 2025)

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
- Python 3.8+ compatibility with GDAL/OGR integration
- XArray/Rasterio for efficient data handling
- Parallel downloading capabilities
- Memory-efficient processing for large datasets
- Configurable quality control parameters
- Support for multiple output formats (GeoTIFF, NetCDF)
- NASA Earthdata integration for MODIS products
- Copernicus Climate Data Store integration for ECMWF data
- University of Idaho GridMET data access
- Automated authentication handling
- Robust error handling and retry mechanisms
- Optimized performance for CONUS-scale processing
- Configurable parallel processing
- Efficient memory management
- Tile-based processing for large datasets
- Compression and chunking optimizations

[Unreleased]: https://github.com/sandbox-msh/geospace_data/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/sandbox-msh/geospace_data/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/sandbox-msh/geospace_data/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/sandbox-msh/geospace_data/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/sandbox-msh/geospace_data/releases/tag/v1.0.0