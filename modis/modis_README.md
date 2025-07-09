# MODIS Processing Framework

**Version:** 1.0.0  
**Module:** MODIS  
**Last Updated:** July 8, 2025  
**Framework Compatibility:** GEOSPACE v1.0.0

A comprehensive framework for downloading and processing MODIS (Moderate Resolution Imaging Spectroradiometer) satellite data with focus on vegetation indices, land surface temperature, and vegetation continuous fields for Continental United States (CONUS) analysis.

## Overview

This framework provides end-to-end processing of MODIS data from download through analysis-ready outputs:

- **Download**: Automated downloading from NASA Earthdata with variable packages and tile selection
- **Processing**: Convert HDF files to analysis-ready GeoTIFF/NetCDF with quality control and spatial processing
- **Configuration**: Unified configuration system supporting all MODIS products
- **Quality Control**: Automated quality masking using MODIS QC flags
- **Flexibility**: Support for single variables, variable groups, and custom processing workflows

## Quick Start

### 1. Setup

```bash
# Clone or download the framework
git clone <repository-url>
cd CONUS/geospace

# Set up NASA Earthdata credentials
export EARTHDATA_BEARER_TOKEN="your_token_here"

# Install Python dependencies
pip install xarray rioxarray numpy rasterio pandas psutil beautifulsoup4 pyproj requests
```

### 2. Download MODIS Data

```bash
# Download NDVI data for January 2020
./modis_download_generic.sh --variables NDVI --year 2020 --month 1 --output-dir ./data/raw/NDVI/

# Download LST data for specific date
./modis_download_generic.sh --variables LST --date 2020-01-15 --output-dir ./data/raw/LST/

# Download multiple variables
./modis_download_generic.sh --variables vegetation --year 2020 --month 1 --output-dir ./data/raw/
```

### 3. Process Data

```bash
# Process NDVI for a specific date
./modis_process_generic.sh --variable NDVI --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/NDVI/ --date 2020-01-01

# Process multiple variables
./modis_process_generic.sh --variable vegetation --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/ --date 2020-01-01

# Process with date range
./modis_process_generic.sh --variable LST_Day --input-dir ./data/raw/LST/ --output-dir ./data/proc/LST/ --start-date 2020-01-01 --end-date 2020-01-07
```

## Framework Components

### Download Scripts

- **`modis_download_generic.py`** - Python download engine
- **`modis_download_generic.sh`** - Bash wrapper with argument parsing

### Processing Scripts

- **`modis_process_generic.py`** - Python processing engine
- **`modis_process_generic.sh`** - Bash wrapper with multi-variable support

### Configuration

- **`modis_consolidated_config.json`** - Unified configuration for all supported products

## Supported MODIS Products

### Land Surface Temperature (LST)

- **Products**: MOD11A1/MYD11A1 (Terra/Aqua daily 1km)
- **Variables**: `LST_Day`, `LST_Night`
- **Output Units**: Degrees Celsius
- **Temporal Resolution**: Daily
- **Quality Control**: Mandatory QA flags, data quality flags

### Vegetation Indices (VI)

- **Products**: MOD13A1/MYD13A1 (16-day 500m), MOD13A2/MYD13A2 (16-day 1km), MOD13A3/MYD13A3 (monthly 1km)
- **Variables**: `NDVI`, `EVI`
- **Output Units**: Dimensionless (-1 to 1)
- **Temporal Resolution**: 16-day composites or monthly
- **Quality Control**: MODLAND QA, VI usefulness, cloud/aerosol screening

### Vegetation Continuous Fields (VCF)

- **Products**: MOD44B/MYD44B (annual 250m)
- **Variables**: `Percent_Tree_Cover`, `Percent_NonTree_Vegetation`, `Percent_NonVegetated`
- **Output Units**: Percent (0-100%)
- **Temporal Resolution**: Annual
- **Quality Control**: VCF quality flags, cloud/snow filtering

## Detailed Usage

### Download Framework

#### Basic Download Commands

```bash
# Download specific variable for month
./modis_download_generic.sh --variables NDVI --year 2020 --month 1 --output-dir ./data/raw/NDVI/

# Download for specific date
./modis_download_generic.sh --variables LST --date 2020-01-15 --output-dir ./data/raw/LST/

# Download from specific instrument
./modis_download_generic.sh --variables NDVI --year 2020 --month 1 --instrument Terra --output-dir ./data/raw/NDVI/
```

#### Variable Packages

Use predefined variable packages for convenience:

```bash
# Vegetation package (NDVI, EVI, VCF)
./modis_download_generic.sh --variables vegetation --year 2020 --month 1 --output-dir ./data/raw/

# Temperature package (LST)
./modis_download_generic.sh --variables temperature --year 2020 --month 1 --output-dir ./data/raw/

# All variables
./modis_download_generic.sh --variables all --year 2020 --month 1 --output-dir ./data/raw/
```

#### Download Options

| Option | Description | Example |
|--------|-------------|---------|
| `--variables` | Variables to download | `NDVI`, `LST`, `vegetation` |
| `--year` | Year to download | `2020` |
| `--month` | Month to download | `1` |
| `--date` | Specific date | `2020-01-15` |
| `--instrument` | Satellite instrument | `Terra`, `Aqua`, `Both` |
| `--output-dir` | Output directory | `./data/raw/MODIS/` |
| `--workers` | Parallel downloads | `5` |
| `--list-variables` | List available variables | |

### Processing Framework

#### Basic Processing Commands

```bash
# Process single variable, single date
./modis_process_generic.sh --variable NDVI --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/NDVI/ --date 2020-01-01

# Process for entire month
./modis_process_generic.sh --variable NDVI --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/NDVI/ --year 2020 --month 1

# Process multiple variables
./modis_process_generic.sh --variable NDVI,EVI --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/ --date 2020-01-01
```

#### Variable Groups

Use predefined groups for efficient processing:

```bash
# Process vegetation indices (NDVI, EVI)
./modis_process_generic.sh --variable vegetation --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/ --date 2020-01-01

# Process temperature variables (LST_Day, LST_Night)
./modis_process_generic.sh --variable temperature --input-dir ./data/raw/LST/ --output-dir ./data/proc/LST/ --date 2020-01-15

# Process forest variables (tree cover, non-tree vegetation)
./modis_process_generic.sh --variable forest --input-dir ./data/raw/VCF/ --output-dir ./data/proc/VCF/ --date 2020-03-05
```

#### Date Range Processing

Process multiple dates automatically:

```bash
# Process week of data
./modis_process_generic.sh --variable NDVI --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/NDVI/ --start-date 2020-01-01 --end-date 2020-01-07

# Process month of LST data
./modis_process_generic.sh --variable LST_Day --input-dir ./data/raw/LST/ --output-dir ./data/proc/LST/ --start-date 2020-01-01 --end-date 2020-01-31
```

#### Processing Options

| Option | Description | Example |
|--------|-------------|---------|
| `--variable` | Variable(s) to process | `NDVI`, `vegetation`, `NDVI,EVI` |
| `--input-dir` | Input HDF directory | `./data/raw/NDVI/` |
| `--output-dir` | Output directory | `./data/proc/NDVI/` |
| `--date` | Single date | `2020-01-01` |
| `--start-date` | Start date for range | `2020-01-01` |
| `--end-date` | End date for range | `2020-01-07` |
| `--year` | Year (with month) | `2020` |
| `--month` | Month (with year) | `1` |
| `--product` | Filter by product | `MOD13A2` |
| `--config` | Custom config file | `custom.json` |
| `--no-quality-mask` | Disable quality masking | |
| `--verbose` | Verbose output | |
| `--dry-run` | Show what would run | |

### Configuration System

#### Using the Consolidated Configuration

The framework includes a unified configuration file (`modis_consolidated_config.json`) that supports all variables:

```bash
# Use with any variable
./modis_process_generic.sh --variable NDVI --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/NDVI/ --date 2020-01-01 --config modis_consolidated_config.json
```

#### Creating Custom Configurations

```bash
# Generate configuration template
./modis_process_generic.sh --create-config-template my_config.json

# Edit the configuration
vim my_config.json

# Use custom configuration
./modis_process_generic.sh --variable NDVI --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/NDVI/ --date 2020-01-01 --config my_config.json
```

#### Configuration Structure

```json
{
  "product_configs": {
    "MOD13A2": {
      "grid_name": "MODIS_Grid_16DAY_1km_VI",
      "variables": {
        "NDVI": {
          "sds_name": "1 km 16 days NDVI",
          "scale_factor": 0.0001,
          "valid_range": [-2000, 10000],
          "fill_value": -3000,
          "units": "dimensionless",
          "qc_sds": "1 km 16 days VI Quality"
        }
      }
    }
  },
  "processing": {
    "target_crs": "EPSG:5070",
    "target_resolution": 250,
    "output_format": "GeoTIFF"
  }
}
```

## Output Format

### File Naming Convention

- **Pattern**: `PRODUCT_VARIABLE_YYYYMMDD.tif`
- **Examples**:
  - `MODIS_NDVI_20200101.tif`
  - `MODIS_LST_Day_20200115.tif`
  - `MODIS_Percent_Tree_Cover_20200305.tif`

### File Properties

- **Format**: GeoTIFF (default) with LZW compression
- **Coordinate System**: EPSG:5070 (CONUS Albers) by default
- **Resolution**: 250m by default
- **NoData Value**: -9999.0
- **Tiling**: 256x256 pixel tiles for efficient access

### Directory Structure

```bash
data/
├── raw/                          # Downloaded HDF files
│   ├── NDVI/                    # MOD13*/MYD13* files
│   ├── LST/                     # MOD11*/MYD11* files
│   └── VCF/                     # MOD44*/MYD44* files
└── proc/                        # Processed outputs
    ├── NDVI/
    │   ├── MODIS_NDVI_20200101.tif
    │   └── MODIS_NDVI_20200117.tif
    ├── LST/
    │   ├── MODIS_LST_Day_20200115.tif
    │   └── MODIS_LST_Night_20200115.tif
    └── VCF/
        └── MODIS_Percent_Tree_Cover_20200305.tif
```

## Processing Features

### Quality Control

Automatic quality masking using MODIS QC flags:

- **LST**: Mandatory QA flags, data quality assessment
- **VI**: MODLAND QA, VI usefulness, cloud/aerosol screening  
- **VCF**: Quality flags, snow/cloud filtering

Disable with `--no-quality-mask` for exploratory analysis.

### Spatial Processing

- **Mosaicking**: Automatic combination of MODIS tiles
- **Reprojection**: Convert from MODIS Sinusoidal to target CRS
- **Resampling**: Bilinear resampling by default
- **Clipping**: CONUS extent by default

### Variable Groups Available

| Group | Variables | Description |
|-------|-----------|-------------|
| `vegetation` | NDVI, EVI | Vegetation indices |
| `temperature` | LST_Day, LST_Night | Land surface temperature |
| `forest` | Percent_Tree_Cover, Percent_NonTree_Vegetation | Forest characteristics |
| `all` | All supported variables | Complete dataset |

## Common Workflows

### Workflow 1: NDVI Time Series

```bash
#!/bin/bash
# Process NDVI time series for 2020

# Download data for each month
for month in {1..12}; do
    echo "Downloading month $month"
    ./modis_download_generic.sh --variables NDVI --year 2020 --month $month --output-dir ./data/raw/NDVI/
done

# Process each month
for month in {1..12}; do
    echo "Processing month $month"
    ./modis_process_generic.sh --variable NDVI --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/NDVI/ --year 2020 --month $month
done
```

### Workflow 2: Multi-Variable Analysis

```bash
#!/bin/bash
# Download and process multiple variables for same period

# Download all data
./modis_download_generic.sh --variables vegetation --year 2020 --month 1 --output-dir ./data/raw/
./modis_download_generic.sh --variables temperature --date 2020-01-15 --output-dir ./data/raw/

# Process vegetation indices
./modis_process_generic.sh --variable vegetation --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/ --year 2020 --month 1

# Process temperature
./modis_process_generic.sh --variable temperature --input-dir ./data/raw/LST/ --output-dir ./data/proc/LST/ --date 2020-01-15
```

### Workflow 3: Custom Processing

```bash
#!/bin/bash
# Custom processing with specific parameters

# Create custom configuration
./modis_process_generic.sh --create-config-template custom_config.json

# Edit configuration for specific needs
# - Change target projection
# - Adjust quality thresholds  
# - Modify output format

# Process with custom settings
./modis_process_generic.sh --variable NDVI --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/NDVI/ --date 2020-01-01 --config custom_config.json
```

## Troubleshooting

### Common Issues

#### Download Issues

##### **"EARTHDATA_BEARER_TOKEN not set"**

```bash
# Get token from https://urs.earthdata.nasa.gov/
export EARTHDATA_BEARER_TOKEN="your_token_here"
```

##### **"No files found for date"**

- Check date format (YYYY-MM-DD)
- Verify data availability for the requested date
- Some products have different temporal coverage

##### **"Connection timeout"**

- Check internet connection
- NASA servers may be busy - retry later
- Reduce number of parallel workers: `--workers 2`

#### Processing Issues

##### **"Python script not found"**

```bash
# Check script location
ls -la modis_process_generic.py

# Update path in wrapper script if needed
PYTHON_SCRIPT="/full/path/to/modis_process_generic.py"
```

##### **"No HDF files found"**

- Verify input directory path
- Check file naming (should be `M*D*.hdf`)
- Ensure files downloaded successfully

##### **"Variable not found in configuration"**

- Check variable name spelling
- Use `--list-variables` to see available options
- Create custom configuration if needed

##### **"Out of memory"**

- Process smaller date ranges
- Reduce target resolution
- Process fewer tiles simultaneously

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Verbose processing
./modis_process_generic.sh --variable NDVI --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/NDVI/ --date 2020-01-01 --verbose

# Dry run to see commands
./modis_process_generic.sh --variable NDVI --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/NDVI/ --date 2020-01-01 --dry-run

# Check individual files
python3 modis_process_generic.py --variable NDVI --input-dir ./data/raw/NDVI/ --output-dir ./data/proc/NDVI/ --date 2020-01-01
```

## Advanced Usage

### Custom Quality Control

Create configuration with strict quality control:

```json
{
  "quality_masks": {
    "MOD13_VI_Quality": {
      "modland_qa_bits": [0, 1],
      "good_quality_values": [0],
      "vi_usefulness_bits": [2, 5],
      "max_usefulness": 1,
      "cloud_bits": [10, 13],
      "reject_cloudy": true
    }
  }
}
```

### Alternative Projections

Process to different coordinate systems:

```json
{
  "processing": {
    "target_crs": "EPSG:4326",    # Geographic WGS84
    "target_resolution": 1000,    # 1km resolution
    "resampling_method": "nearest"
  }
}
```

### Batch Processing with Python

```python
import subprocess
from pathlib import Path

# Define processing parameters
base_dir = Path('./data/')
variables = ['NDVI', 'EVI', 'LST_Day']
dates = ['2020-01-01', '2020-01-17', '2020-02-02']

for variable in variables:
    for date in dates:
        cmd = [
            './modis_process_generic.sh',
            '--variable', variable,
            '--input-dir', str(base_dir / 'raw' / variable.split('_')[0]),
            '--output-dir', str(base_dir / 'proc' / variable),
            '--date', date
        ]
        
        print(f"Processing {variable} for {date}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Success: {variable} {date}")
        else:
            print(f"✗ Failed: {variable} {date}")
            print(result.stderr)
```

## Installation Requirements

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: Sufficient space for data (MODIS files can be large)
- **Network**: Internet connection for downloads

### Python Dependencies

```bash
# Required packages
pip install xarray rioxarray numpy rasterio pandas psutil beautifulsoup4 pyproj requests

# Optional for enhanced functionality
pip install netcdf4 pyhdf PyYAML
```

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get install gdal-bin libgdal-dev

# CentOS/RHEL  
sudo yum install gdal gdal-devel

# macOS
brew install gdal

# Conda (all platforms)
conda install -c conda-forge gdal rasterio xarray
```

### NASA Earthdata Setup

1. Create account: [NASA Earthdata](https://earthdata.nasa.gov/)
2. Generate bearer token in profile settings
3. Set environment variable:

   ```bash
   export EARTHDATA_BEARER_TOKEN="your_token_here"
   ```

## Performance Tips

### Download Optimization

- Use appropriate number of workers (`--workers 5-10`)
- Download during off-peak hours for better speeds
- Check NASA server status if downloads fail

### Processing Optimization

- Process data on local storage (not network drives)
- Use SSD storage for better I/O performance
- Monitor memory usage with large datasets
- Process in temporal chunks for long time series

### Storage Management

- Use compression (enabled by default)
- Clean up intermediate files
- Consider archiving processed data
- Monitor disk space usage

## Contributing

### Reporting Issues

- Provide specific error messages
- Include command that failed
- Specify system information
- Share sample data if possible

### Feature Requests

- Describe use case
- Provide examples of desired functionality
- Consider backwards compatibility

## References

### MODIS Documentation

- [MODIS Overview](https://modis.gsfc.nasa.gov/)
- [Land Products Quality Assessment](https://modis-land.gsfc.nasa.gov/MODLAND_QA.html)
- [Collection 6.1 Documentation](https://modis.gsfc.nasa.gov/data/dataprod/)

### Technical Resources

- [NASA Earthdata](https://earthdata.nasa.gov/)
- [MODIS Sinusoidal Projection](https://modis-land.gsfc.nasa.gov/MODLAND_grid.html)
- [GDAL MODIS Documentation](https://gdal.org/drivers/raster/hdf4.html)

## License

This framework is released under the Public Domain license. Individual components may have different licenses - see source files for details.

## Support

For questions or issues:

1. Check this documentation
2. Review troubleshooting section
3. Submit issues with detailed information
4. Contact the GEOSPACE Project team

---

*Last updated: June 2025*  
*Version: 1.0*  
*Framework validated with MODIS Collection 6.1 data*
