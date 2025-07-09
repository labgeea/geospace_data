# GridMET Processing Framework

**Version:** 1.0.0  
**Module:** GridMET  
**Last Updated:** July 8, 2025  
**Framework Compatibility:** GEOSPACE v1.0.0

A comprehensive framework for downloading and processing GridMET (Gridded Surface Meteorological Dataset) variables with focus on climate variables, fire weather indices, and evapotranspiration for Continental United States (CONUS) analysis.

## Overview

This framework provides end-to-end processing of GridMET data from download through analysis-ready outputs:

- **Download**: Automated downloading from University of Idaho THREDDS server with variable packages and temporal selection
- **Processing**: Convert NetCDF files to analysis-ready GeoTIFF/NetCDF with unit conversions and spatial processing
- **Configuration**: Unified configuration system supporting all GridMET variables
- **Unit Conversion**: Automated conversions (K→°C, kg/kg→g/kg, Pa→kPa)
- **Flexibility**: Support for single variables, variable groups, and custom processing workflows

## Quick Start

### 1. Setup

```bash
# Clone or download the framework
git clone <repository-url>
cd CONUS/geospace

# Install Python dependencies
pip install xarray rioxarray numpy rasterio pandas psutil requests netcdf4

# Make scripts executable
chmod +x gridmet_download_generic.sh gridmet_process_generic.sh
```

### 2. Download GridMET Data

```bash
# Download precipitation data for January 2020
./gridmet_download_generic.sh --variables pr --year 2020 --month 1 --output-dir ./data/raw/GridMET/

# Download temperature data
./gridmet_download_generic.sh --variables tmmx,tmmn --year 2020 --month 1 --output-dir ./data/raw/GridMET/

# Download weather package (precipitation, max temp, min temp)
./gridmet_download_generic.sh --variables weather --year 2020 --month 1 --output-dir ./data/raw/GridMET/
```

### 3. Process Data

```bash
# Process precipitation for January 2020
./gridmet_process_generic.sh --input-file ./data/raw/GridMET/gridmet_pr_202001.nc --output-dir ./data/proc/GridMET/ --variables pr

# Process with monthly aggregation
./gridmet_process_generic.sh --input-file ./data/raw/GridMET/gridmet_pr_202001.nc --output-dir ./data/proc/GridMET/ --variables pr --aggregation monthly

# Process multiple variables with both output formats
./gridmet_process_generic.sh --input-file ./data/raw/GridMET/gridmet_tmmx_202001.nc --output-dir ./data/proc/GridMET/ --variables all --output-format both
```

## Framework Components

### Download Scripts

- **`gridmet_download_generic.py`** - Python download engine with OPeNDAP access
- **`gridmet_download_generic.sh`** - Bash wrapper with argument parsing

### Processing Scripts

- **`gridmet_process_generic.py`** - Python processing engine with unit conversions
- **`gridmet_process_generic.sh`** - Bash wrapper with multi-variable support

## Supported GridMET Variables

### Primary Climate Variables

- **Products**: Daily gridded meteorological data at ~4km resolution
- **Variables**: `pr`, `tmmx`, `tmmn`, `rmax`, `rmin`, `sph`, `srad`, `vs`, `th`
- **Temporal Resolution**: Daily from 1979-present
- **Spatial Coverage**: Continental United States (CONUS)
- **Unit Conversions**: Temperature (K→°C), humidity conversions as needed

### Fire Weather Variables

- **Variables**: `bi`, `fm100`, `fm1000`, `erc`
- **Output Units**: Dimensionless indices and percentages
- **Use Cases**: Fire danger assessment, fire behavior prediction
- **Temporal Resolution**: Daily

### Evapotranspiration Variables

- **Variables**: `etr`, `eto`, `vpd`
- **Output Units**: mm for ET, kPa for VPD
- **Use Cases**: Irrigation scheduling, water management, plant stress analysis
- **Unit Conversions**: VPD (Pa→kPa)

### Drought Indices

- **Variables**: `pdsi`
- **Output Units**: Dimensionless
- **Temporal Resolution**: Pentad (5-day) averages
- **Use Cases**: Drought monitoring, water resources management

## Detailed Usage

### Download Framework

#### Basic Download Commands

```bash
# Download specific variable for month
./gridmet_download_generic.sh --variables pr --year 2020 --month 1 --output-dir ./data/raw/GridMET/

# Download multiple variables
./gridmet_download_generic.sh --variables pr,tmmx,tmmn --year 2020 --month 1 --output-dir ./data/raw/GridMET/

# Download using variable aliases
./gridmet_download_generic.sh --variables precipitation,maximum_temperature --year 2020 --month 1 --output-dir ./data/raw/GridMET/
```

#### Variable Packages

Use predefined variable packages for convenience:

```bash
# Weather package (pr, tmmx, tmmn)
./gridmet_download_generic.sh --variables weather --year 2020 --month 1 --output-dir ./data/raw/GridMET/

# Fire weather package (bi, fm100, fm1000, erc)
./gridmet_download_generic.sh --variables fire --year 2020 --month 6 --output-dir ./data/raw/GridMET/

# Evapotranspiration package (etr, eto, vpd)
./gridmet_download_generic.sh --variables evapotranspiration --year 2020 --month 7 --output-dir ./data/raw/GridMET/

# All variables
./gridmet_download_generic.sh --variables all --year 2020 --month 1 --output-dir ./data/raw/GridMET/
```

#### Download Options

| Option | Description | Example |
|--------|-------------|---------|
| `--variables` | Variables to download | `pr`, `weather`, `all` |
| `--year` | Year to download | `2020` |
| `--month` | Month to download | `1` |
| `--output-dir` | Output directory | `./data/raw/GridMET/` |
| `--list-variables` | List available variables | |
| `--help` | Show help | |

### Processing Framework

#### Basic Processing Commands

```bash
# Process single variable
./gridmet_process_generic.sh --input-file ./data/raw/GridMET/gridmet_pr_202001.nc --output-dir ./data/proc/GridMET/ --variables pr

# Process all variables in file
./gridmet_process_generic.sh --input-file ./data/raw/GridMET/gridmet_pr_202001.nc --output-dir ./data/proc/GridMET/ --variables all

# Process with custom options
./gridmet_process_generic.sh --input-file ./data/raw/GridMET/gridmet_tmmx_202001.nc --output-dir ./data/proc/GridMET/ --variables tmmx --aggregation monthly --output-format both
```

#### Variable Groups

Process related variables together:

```bash
# Process temperature variables (automatic K→°C conversion)
./gridmet_process_generic.sh --input-file ./data/raw/GridMET/gridmet_tmmx_202001.nc --output-dir ./data/proc/GridMET/ --variables temperature

# Process fire weather variables
./gridmet_process_generic.sh --input-file ./data/raw/GridMET/gridmet_bi_202006.nc --output-dir ./data/proc/GridMET/ --variables fire

# Process evapotranspiration variables (automatic Pa→kPa conversion for VPD)
./gridmet_process_generic.sh --input-file ./data/raw/GridMET/gridmet_eto_202007.nc --output-dir ./data/proc/GridMET/ --variables evapotranspiration
```

#### Processing Options

| Option | Description | Example |
|--------|-------------|---------|
| `--input-file` | Input NetCDF file | `gridmet_pr_202001.nc` |
| `--output-dir` | Output directory | `./data/proc/GridMET/` |
| `--variables` | Variable(s) to process | `pr`, `all`, `weather` |
| `--aggregation` | Temporal aggregation | `daily`, `monthly` |
| `--output-format` | Output format | `geotiff`, `netcdf`, `both` |
| `--target-crs` | Target coordinate system | `EPSG:5070`, `EPSG:4326` |
| `--chunk-size` | Memory management | `15` |
| `--list-config` | List variable configurations | |
| `--debug` | Debug output | |

### Variable Configurations

#### Primary Climate Variables

| Variable | Name | Output Unit | Conversion | Aliases |
|----------|------|-------------|------------|---------|
| `pr` | Precipitation | mm | None | `precipitation`, `precip`, `rain` |
| `tmmx` | Max Temperature | °C | K→°C | `tmax`, `maximum_temperature` |
| `tmmn` | Min Temperature | °C | K→°C | `tmin`, `minimum_temperature` |
| `rmax` | Max Humidity | % | None | `rh_max`, `humidity_max` |
| `rmin` | Min Humidity | % | None | `rh_min`, `humidity_min` |
| `sph` | Specific Humidity | g/kg | kg/kg→g/kg | `specific_humidity` |
| `srad` | Solar Radiation | W/m2 | None | `solar_radiation`, `radiation` |
| `vs` | Wind Speed | m/s | None | `wind_speed`, `wind` |
| `th` | Wind Direction | degrees | None | `wind_direction`, `wind_dir` |

#### Fire Weather Variables

| Variable | Name | Output Unit | Conversion | Description |
|----------|------|-------------|------------|-------------|
| `bi` | Burning Index | dimensionless | None | Fire danger assessment |
| `fm100` | 100-hr Fuel Moisture | % | None | Fire behavior prediction |
| `fm1000` | 1000-hr Fuel Moisture | % | None | Fire behavior prediction |
| `erc` | Energy Release Component | dimensionless | None | Fire intensity potential |

#### Evapotranspiration Variables

| Variable | Name | Output Unit | Conversion | Description |
|----------|------|-------------|------------|-------------|
| `etr` | Reference ET (Alfalfa) | mm | None | Irrigation scheduling |
| `eto` | Reference ET (Grass) | mm | None | Water management |
| `vpd` | Vapor Pressure Deficit | kPa | Pa→kPa | Plant stress analysis |

### Variable Packages Available

| Package | Variables | Description |
|---------|-----------|-------------|
| `weather` | pr, tmmx, tmmn | Basic meteorological variables |
| `temperature` | tmmx, tmmn | Temperature analysis |
| `humidity` | rmax, rmin, sph, vpd | Humidity and moisture variables |
| `fire` | bi, fm100, fm1000, erc | Fire weather indices |
| `evapotranspiration` | etr, eto, vpd | Water balance variables |
| `wind` | vs, th | Wind analysis |
| `all` | All supported variables | Complete dataset |

## Output Format

### File Naming Convention

- **Pattern**: `gridmet_<variable>_<aggregation>.{tif|nc}`
- **Examples**:
  - `gridmet_pr_daily.tif`
  - `gridmet_tmmx_monthly.nc`
  - `gridmet_bi_daily.tif`

### File Properties

- **Format**: GeoTIFF (default) or NetCDF with LZW compression
- **Coordinate System**: EPSG:5070 (CONUS Albers) by default
- **Resolution**: ~4km (original GridMET resolution preserved)
- **NoData Value**: -9999.0
- **Tiling**: 512×512 pixel tiles for efficient access

### Directory Structure

```bash
data/
├── raw/                          # Downloaded NetCDF files
│   └── GridMET/
│       ├── gridmet_pr_202001.nc
│       ├── gridmet_tmmx_202001.nc
│       └── gridmet_tmmn_202001.nc
└── proc/                        # Processed outputs
    └── GridMET/
        ├── gridmet_pr_daily.tif
        ├── gridmet_tmmx_daily.tif
        ├── processing_report.json
        └── processing_report.txt
```

## Processing Features

### Unit Conversions

Automatic unit conversions for scientific consistency:

- **Temperature**: Kelvin → Celsius (T_C = T_K - 273.15)
- **Specific Humidity**: kg/kg → g/kg (multiply by 1000)
- **Vapor Pressure Deficit**: Pascals → kiloPascals (divide by 1000)
- **Other Variables**: No conversion (already in appropriate units)

### Temporal Aggregation

- **Daily**: Preserve original temporal resolution (default)
- **Monthly**: Calculate monthly statistics
  - Mean for most variables (temperature, humidity, wind, etc.)
  - Sum for accumulating variables (precipitation, ET)

### Spatial Processing

- **Coordinate System**: Convert from WGS84 to target CRS
- **Resampling**: Bilinear resampling by default
- **Extent**: CONUS coverage preserved
- **Resolution**: Maintain ~4km native resolution

### Variable-Specific Processing

| Variable Type | Aggregation Method | Valid Range | Quality Checks |
|---------------|-------------------|-------------|----------------|
| **Temperature** | Mean | -50 to 60°C | Range validation |
| **Precipitation** | Sum | 0 to 1000mm | Non-negative check |
| **Humidity** | Mean | 0 to 100% | Percentage bounds |
| **Wind** | Mean | 0 to 50 m/s | Physical limits |
| **Fire Weather** | Mean | Variable ranges | Index-specific bounds |

## Common Workflows

### Workflow 1: Climate Analysis

```bash
#!/bin/bash
# Download and process basic climate variables for 2020

# Download weather package for each month
for month in {1..12}; do
    echo "Downloading month $month"
    ./gridmet_download_generic.sh --variables weather --year 2020 --month $month --output-dir ./data/raw/GridMET/
done

# Process each variable with both daily and monthly aggregations
variables=("pr" "tmmx" "tmmn")
for var in "${variables[@]}"; do
    for month in {01..12}; do
        # Daily processing
        ./gridmet_process_generic.sh --input-file ./data/raw/GridMET/gridmet_${var}_2020${month}.nc \
                                     --output-dir ./data/proc/GridMET/daily/ --variables $var
        
        # Monthly processing
        ./gridmet_process_generic.sh --input-file ./data/raw/GridMET/gridmet_${var}_2020${month}.nc \
                                     --output-dir ./data/proc/GridMET/monthly/ --variables $var --aggregation monthly
    done
done
```

### Workflow 2: Fire Weather Analysis

```bash
#!/bin/bash
# Download and process fire weather variables for fire season

# Download fire weather package for fire season months
for month in {5..9}; do
    echo "Downloading fire weather data for month $month"
    ./gridmet_download_generic.sh --variables fire --year 2020 --month $month --output-dir ./data/raw/GridMET/fire/
done

# Process fire weather variables
fire_vars=("bi" "fm100" "fm1000" "erc")
for var in "${fire_vars[@]}"; do
    for month in {05..09}; do
        ./gridmet_process_generic.sh --input-file ./data/raw/GridMET/fire/gridmet_${var}_2020${month}.nc \
                                     --output-dir ./data/proc/GridMET/fire/ --variables $var --output-format both
    done
done
```

### Workflow 3: Evapotranspiration Analysis

```bash
#!/bin/bash
# Process ET variables for growing season

# Download ET variables for growing season
for month in {4..10}; do
    ./gridmet_download_generic.sh --variables evapotranspiration --year 2020 --month $month --output-dir ./data/raw/GridMET/et/
done

# Process with both daily and monthly aggregations
et_vars=("etr" "eto" "vpd")
for var in "${et_vars[@]}"; do
    for month in {04..10}; do
        # Daily (for detailed water management)
        ./gridmet_process_generic.sh --input-file ./data/raw/GridMET/et/gridmet_${var}_2020${month}.nc \
                                     --output-dir ./data/proc/GridMET/et/daily/ --variables $var
        
        # Monthly (for seasonal analysis)
        ./gridmet_process_generic.sh --input-file ./data/raw/GridMET/et/gridmet_${var}_2020${month}.nc \
                                     --output-dir ./data/proc/GridMET/et/monthly/ --variables $var --aggregation monthly
    done
done
```

### Workflow 4: Multi-Year Climate Trend Analysis

```bash
#!/bin/bash
# Multi-year temperature trend analysis

# Download temperature data for multiple years
for year in {2018..2022}; do
    for month in {1..12}; do
        ./gridmet_download_generic.sh --variables temperature --year $year --month $month --output-dir ./data/raw/GridMET/trends/
    done
done

# Process with consistent settings
for year in {2018..2022}; do
    for month in {01..12}; do
        for var in tmmx tmmn; do
            ./gridmet_process_generic.sh --input-file ./data/raw/GridMET/trends/gridmet_${var}_${year}${month}.nc \
                                         --output-dir ./data/proc/GridMET/trends/ --variables $var --target-crs EPSG:5070
        done
    done
done
```

## Troubleshooting

### Common Issues

#### Download Issues

##### **"Connection timeout to THREDDS server"**

```bash
# Check server connectivity
curl -I "http://thredds.northwestknowledge.net:8080/thredds/"

# Test with reduced variables
./gridmet_download_generic.sh --variables pr --year 2020 --month 1 --output-dir ./data/test/
```

##### **"Variable not found"**

```bash
# List all available variables and aliases
./gridmet_download_generic.sh --list-variables

# Check for typos in variable names
./gridmet_download_generic.sh --variables precipitation --year 2020 --month 1 --output-dir ./data/test/
```

##### **"No data for requested time period"**

- Verify date range (GridMET: 1979-present)
- Check if data is available for the specific month
- Some variables may have different temporal coverage

#### Processing Issues

##### **"Input file not found"**

```bash
# Check downloaded files
ls -la ./data/raw/GridMET/

# Verify file naming convention
ls gridmet_*_YYYYMM.nc
```

##### **"Unit conversion failed"**

```bash
# Check variable configuration
./gridmet_process_generic.sh --list-config

# Process with debug output
./gridmet_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables pr --debug
```

##### **"Out of memory errors"**

```bash
# Use smaller chunk sizes
./gridmet_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --chunk-size 10

# Process variables separately
./gridmet_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables pr
```

##### **"Projection failed"**

```bash
# Keep original projection
./gridmet_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --target-crs EPSG:4326

# Use common CONUS projection
./gridmet_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --target-crs EPSG:5070
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Debug processing
./gridmet_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables pr --debug

# Check individual Python script
python3 gridmet_process_generic.py --input-file ./data/input.nc --output-dir ./data/output/ --variables pr --debug
```

## Advanced Usage

### Custom Variable Processing

Create custom processing workflows:

```python
# Custom Python processing script
import xarray as xr
from gridmet_process_generic import process_gridmet_variables

# Process with custom settings
result = process_gridmet_variables(
    input_file='./data/raw/gridmet_pr_202001.nc',
    output_dir='./data/custom/',
    variables=['pr'],
    aggregation='monthly',
    output_format='both',
    target_crs='EPSG:4326'
)
```

### Batch Processing with Custom Scripts

```python
import subprocess
from pathlib import Path

# Define processing parameters
base_dir = Path('./data/')
variables = ['pr', 'tmmx', 'tmmn']
years = [2019, 2020, 2021]
months = range(1, 13)

for variable in variables:
    for year in years:
        for month in months:
            # Download
            download_cmd = [
                './gridmet_download_generic.sh',
                '--variables', variable,
                '--year', str(year),
                '--month', str(month),
                '--output-dir', str(base_dir / 'raw' / 'GridMET')
            ]
            
            # Process
            process_cmd = [
                './gridmet_process_generic.sh',
                '--input-file', str(base_dir / 'raw' / 'GridMET' / f'gridmet_{variable}_{year}{month:02d}.nc'),
                '--output-dir', str(base_dir / 'proc' / 'GridMET' / variable),
                '--variables', variable,
                '--output-format', 'both'
            ]
            
            print(f"Processing {variable} for {year}-{month:02d}")
            subprocess.run(download_cmd)
            subprocess.run(process_cmd)
```

### Alternative Output Projections

```bash
# Geographic coordinates (WGS84)
./gridmet_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --target-crs EPSG:4326

# Web Mercator (for web mapping)
./gridmet_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --target-crs EPSG:3857

# UTM Zone 12N (for regional analysis)
./gridmet_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --target-crs EPSG:32612
```

## Installation Requirements

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: Sufficient space for data (each month ~15-50MB per variable)
- **Network**: Internet connection for THREDDS OPeNDAP access

### Python Dependencies

```bash
# Required packages
pip install xarray rioxarray numpy rasterio pandas psutil requests netcdf4

# Optional for enhanced functionality
pip install matplotlib cartopy  # For visualization
pip install dask  # For improved performance with large datasets
```

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get install gdal-bin libgdal-dev netcdf-bin

# CentOS/RHEL  
sudo yum install gdal gdal-devel netcdf

# macOS
brew install gdal netcdf

# Conda (all platforms)
conda install -c conda-forge gdal rasterio xarray netcdf4
```

### THREDDS Access

- **No authentication required** (GridMET is publicly available)
- **Server**: http://thredds.northwestknowledge.net:8080/thredds/
- **Protocol**: OPeNDAP for efficient data access

## Performance Tips

### Download Optimization

- Download during off-peak hours for better speeds
- Use appropriate variable packages to minimize requests
- Monitor University of Idaho server status

### Processing Optimization

- Process data on local storage (not network drives)
- Use SSD storage for better I/O performance
- Process variables separately for large datasets
- Use monthly aggregation to reduce file sizes

### Storage Management

- **Raw files**: ~15-50MB per variable per month
- **Processed files**: Similar size, varies by format and compression
- Clean up intermediate files regularly
- Consider archiving older processed data

## Contributing

### Reporting Issues

- Provide specific error messages
- Include command that failed
- Specify GridMET variable and time period
- Share sample data if possible

### Feature Requests

- Describe use case and application
- Provide examples of desired functionality
- Consider compatibility with existing workflows

## References

### GridMET Documentation

- [GridMET Homepage](http://www.climatologylab.org/gridmet.html)
- [University of Idaho THREDDS Server](http://thredds.northwestknowledge.net:8080/thredds/)
- [GridMET on Climate.gov](https://www.climate.gov/news-features/understanding-climate/climate-change-atmospheric-carbon-dioxide)

### Technical Resources

- [THREDDS Data Server](https://www.unidata.ucar.edu/software/tds/)
- [OPeNDAP Protocol](https://www.opendap.org/)
- [NetCDF Climate and Forecast Conventions](http://cfconventions.org/)

### Research Citation

```bash
Abatzoglou, J.T. (2013), Development of gridded surface meteorological data 
for ecological applications and modelling, Int. J. Climatol., 33: 121-131. 
doi:10.1002/joc.3413
```

## License

This framework is released under the Public Domain license. Individual components may have different licenses - see source files for details.

## Support

For questions or issues:

1. Check this documentation
2. Review troubleshooting section
3. Check GridMET data availability and server status
4. Submit issues with detailed information
5. Contact the GEOSPACE Project team

---

*Last updated: January 2025*  
*Version: 1.0*  
*Framework validated with GridMET data from University of Idaho THREDDS server*
