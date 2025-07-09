# ERA5 Processing Framework

**Version:** 1.0.0  
**Module:** ECMWF  
**Last Updated:** July 8, 2025  
**Framework Compatibility:** GEOSPACE v1.0.0

A comprehensive framework for downloading and processing ERA5 (ECMWF Reanalysis v5) single-level variables from the Copernicus Climate Data Store with focus on meteorological variables for Continental United States (CONUS) analysis.

## Overview

This framework provides end-to-end processing of ERA5 data from download through analysis-ready outputs:

- **Download**: Automated downloading from Copernicus CDS with variable packages and flexible time periods
- **Processing**: Convert NetCDF files to analysis-ready GeoTIFF/NetCDF with unit conversions and temporal aggregation
- **Configuration**: Automatic variable mapping with comprehensive unit conversions
- **Quality Control**: Data validation and range checking
- **Flexibility**: Support for single variables, variable groups, and custom processing workflows

## Quick Start

### 1. Setup

```bash
# Clone or download the framework
git clone <repository-url>
cd CONUS/geospace

# Set up CDS API credentials
echo "url: https://cds.climate.copernicus.eu/api/v2
key: YOUR_UID:YOUR_API_KEY" > ~/.cdsapirc

# Install Python dependencies
pip install cdsapi xarray rioxarray numpy rasterio pandas psutil
```

### 2. Download ERA5 Data

```bash
# Download temperature for January 2020
./era5_download_generic.sh --variables 2m_temperature --year 2020 --month 1 --output-dir ./data/raw/ERA5/

# Download weather package (temperature, pressure, precipitation)
./era5_download_generic.sh --variables weather --year 2020 --month 1 --output-dir ./data/raw/ERA5/

# Download multiple variables
./era5_download_generic.sh --variables 2m_temperature,surface_pressure,total_precipitation --year 2020 --month 1 --output-dir ./data/raw/ERA5/
```

### 3. Process Data

```bash
# Process single variable to daily averages
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_2m-temperature_202001.nc --output-dir ./data/proc/ERA5/ --variables 2m_temperature

# Process all variables in file
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_variables_202001.nc --output-dir ./data/proc/ERA5/ --variables all

# Process with custom aggregation and format
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_variables_202001.nc --output-dir ./data/proc/ERA5/ --variables weather --aggregation monthly --output-format both
```

## Framework Components

### Download Scripts

- **`era5_download_generic.py`** - Python download engine with CDS API integration
- **`era5_download_generic.sh`** - Bash wrapper with argument parsing and validation

### Processing Scripts

- **`era5_process_generic.py`** - Python processing engine with unit conversions and aggregation
- **`era5_process_generic.sh`** - Bash wrapper with comprehensive options

### Configuration

- **Built-in variable mapping** - Automatic handling of ERA5 variable names and aliases
- **Unit conversion system** - Automatic conversions (K→°C, Pa→hPa, m→mm, etc.)

## Supported ERA5 Variables

### Temperature Variables

- **`2m_temperature`** (t2m) - 2 metre temperature
- **`2m_dewpoint_temperature`** (d2m) - 2 metre dewpoint temperature  
- **`skin_temperature`** (skt) - Skin temperature
- **Output**: Degrees Celsius (converted from Kelvin)
- **Aggregation**: Daily/monthly means

### Pressure Variables

- **`surface_pressure`** (sp) - Surface pressure
- **`mean_sea_level_pressure`** (msl) - Mean sea level pressure
- **Output**: hectoPascals (converted from Pascals)
- **Aggregation**: Daily/monthly means

### Precipitation Variables

- **`total_precipitation`** (tp) - Total precipitation
- **Output**: Millimeters (converted from meters)
- **Aggregation**: Daily/monthly sums

### Wind Variables

- **`10m_u_component_of_wind`** (u10) - 10 metre U wind component
- **`10m_v_component_of_wind`** (v10) - 10 metre V wind component
- **`100m_u_component_of_wind`** (u100) - 100 metre U wind component
- **`100m_v_component_of_wind`** (v100) - 100 metre V wind component
- **Output**: m/s (no conversion)
- **Aggregation**: Daily/monthly means

### Atmospheric Variables

- **`boundary_layer_height`** (blh) - Boundary layer height
- **`total_cloud_cover`** (tcc) - Total cloud cover
- **`relative_humidity`** - Relative humidity
- **`geopotential`** (z) - Geopotential
- **`specific_humidity`** (q) - Specific humidity
- **Output**: Various units with appropriate conversions
- **Aggregation**: Daily/monthly means

## Detailed Usage

### Download Framework

#### Basic Download Commands

```bash
# Download specific variable for month
./era5_download_generic.sh --variables 2m_temperature --year 2020 --month 1 --output-dir ./data/raw/ERA5/

# Download multiple variables
./era5_download_generic.sh --variables 2m_temperature,surface_pressure --year 2020 --month 1 --output-dir ./data/raw/ERA5/

# Download using aliases
./era5_download_generic.sh --variables temp_2m,sp,precip --year 2020 --month 1 --output-dir ./data/raw/ERA5/
```

#### Variable Packages

Use predefined variable packages for convenience:

```bash
# Weather package (temperature, pressure, precipitation)
./era5_download_generic.sh --variables weather --year 2020 --month 1 --output-dir ./data/raw/ERA5/

# Wind package (100m U and V components)
./era5_download_generic.sh --variables wind --year 2020 --month 1 --output-dir ./data/raw/ERA5/

# Basic package (temperature, dewpoint, pressure)
./era5_download_generic.sh --variables basic --year 2020 --month 1 --output-dir ./data/raw/ERA5/

# Full package (all common variables)
./era5_download_generic.sh --variables full --year 2020 --month 1 --output-dir ./data/raw/ERA5/
```

#### Download Options

| Option | Description | Example |
|--------|-------------|---------|
| `--variables` | Variables to download | `2m_temperature`, `weather` |
| `--year` | Year to download | `2020` |
| `--month` | Month to download | `1` |
| `--output-dir` | Output directory | `./data/raw/ERA5/` |
| `--list-variables` | List available variables | |

### Processing Framework

#### Basic Processing Commands

```bash
# Process single variable with default settings
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_2m-temperature_202001.nc --output-dir ./data/proc/ERA5/ --variables 2m_temperature

# Process all variables in file
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_variables_202001.nc --output-dir ./data/proc/ERA5/ --variables all

# Process specific variables only
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_variables_202001.nc --output-dir ./data/proc/ERA5/ --variables 2m_temperature,surface_pressure
```

#### Processing Options

| Option | Description | Values | Default |
|--------|-------------|--------|---------|
| `--input-file` | Input NetCDF file | file path | Required |
| `--output-dir` | Output directory | directory | Required |
| `--variables` | Variables to process | variable list, `all` | `all` |
| `--aggregation` | Temporal aggregation | `hourly`, `daily`, `monthly` | `daily` |
| `--output-format` | Output format | `geotiff`, `netcdf`, `both` | `geotiff` |
| `--target-crs` | Target coordinate system | EPSG:XXXX | `EPSG:5070` |
| `--chunk-size` | Memory management | integer | auto |
| `--list-config` | List variable configurations | | |
| `--debug` | Enable debug output | | |

#### Variable Groups

| Group | Variables | Description |
|-------|-----------|-------------|
| `weather` | 2m_temperature, surface_pressure, total_precipitation | Basic weather variables |
| `wind` | 100m_u_component_of_wind, 100m_v_component_of_wind | Wind components |
| `basic` | 2m_temperature, 2m_dewpoint_temperature, surface_pressure | Fundamental atmospheric state |
| `all` | All variables found in file | Complete dataset |

### Variable Aliases

The framework supports convenient aliases for common variables:

| Canonical Name | Aliases | NetCDF Name |
|----------------|---------|-------------|
| `2m_temperature` | `temp_2m`, `temperature_2m`, `t2m` | `t2m` |
| `2m_dewpoint_temperature` | `dewpoint_2m`, `dewpoint_temperature_2m`, `d2m` | `d2m` |
| `surface_pressure` | `surface_press`, `sp`, `press_surface` | `sp` |
| `total_precipitation` | `precipitation`, `precip`, `tp` | `tp` |
| `boundary_layer_height` | `blh`, `pbl_height` | `blh` |
| `100m_u_component_of_wind` | `u_wind_100m`, `u100`, `wind_u_100m` | `u100` |
| `100m_v_component_of_wind` | `v_wind_100m`, `v100`, `wind_v_100m` | `v100` |

## Output Format

### File Naming Convention

#### **Download Output:**

- **Single variable**: `era5_<variable-name>_YYYYMM.nc`
- **Multiple variables**: `era5_variables_YYYYMM.nc`

#### **Processing Output:**

- **GeoTIFF**: `era5_<variable>_<aggregation>.tif`
- **NetCDF**: `era5_<variable>_<aggregation>.nc`

**Examples:**

```bash
# Download outputs
era5_2m-temperature_202001.nc
era5_variables_202001.nc

# Processing outputs
era5_2m_temperature_daily.tif
era5_surface_pressure_monthly.nc
era5_total_precipitation_daily_20200115.tif  # When multiple time steps
```

### File Properties

- **Input Format**: NetCDF4 with CF conventions
- **Output Format**: GeoTIFF (default) with LZW compression or NetCDF4
- **Coordinate System**: EPSG:5070 (CONUS Albers) by default
- **Spatial Resolution**: 0.25° (~28km) preserved or resampled
- **NoData Value**: -9999.0
- **Tiling**: 512x512 pixel tiles for efficient access

### Directory Structure

```bash
data/
├── raw/                          # Downloaded NetCDF files
│   └── ERA5/
│       ├── era5_2m-temperature_202001.nc
│       ├── era5_variables_202001.nc
│       └── era5_total-precipitation_202001.nc
└── proc/                        # Processed outputs
    └── ERA5/
        ├── era5_2m_temperature_daily.tif
        ├── era5_surface_pressure_daily.tif
        ├── era5_total_precipitation_daily.tif
        ├── processing_report.json
        └── processing_report.txt
```

## Processing Features

### Automatic Unit Conversions

- **Temperature**: Kelvin → Celsius (T_C = T_K - 273.15)
- **Pressure**: Pascals → hectoPascals (P_hPa = P_Pa ÷ 100)
- **Precipitation**: meters → millimeters (P_mm = P_m × 1000)
- **Cloud cover**: fraction → percentage (% = fraction × 100)
- **Wind**: m/s → m/s (no conversion)
- **Height**: meters → meters (no conversion)

### Temporal Aggregation

- **Daily**: Mean of 24 hourly values (sum for precipitation)
- **Monthly**: Mean of daily values (sum for precipitation)
- **Hourly**: No aggregation (preserve original resolution)

### Spatial Processing

- **Mosaicking**: Automatic for multi-file datasets
- **Reprojection**: Convert from WGS84 to target CRS
- **Resampling**: Bilinear resampling for continuous variables
- **Clipping**: CONUS extent with buffer

## Common Workflows

### Workflow 1: Temperature Analysis

```bash
#!/bin/bash
# Complete temperature analysis workflow

# Download temperature data
./era5_download_generic.sh --variables 2m_temperature --year 2020 --month 1 --output-dir ./data/raw/ERA5/

# Process to daily averages in Celsius
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_2m-temperature_202001.nc --output-dir ./data/proc/ERA5/temperature/ --variables 2m_temperature

# Process to monthly averages
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_2m-temperature_202001.nc --output-dir ./data/proc/ERA5/temperature/ --variables 2m_temperature --aggregation monthly --output-format both
```

### Workflow 2: Precipitation Analysis

```bash
#!/bin/bash
# Complete precipitation analysis workflow

# Download precipitation data
./era5_download_generic.sh --variables total_precipitation --year 2020 --month 1 --output-dir ./data/raw/ERA5/

# Process to daily totals in millimeters
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_total-precipitation_202001.nc --output-dir ./data/proc/ERA5/precipitation/ --variables total_precipitation

# Process to monthly totals
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_total-precipitation_202001.nc --output-dir ./data/proc/ERA5/precipitation/ --variables total_precipitation --aggregation monthly
```

### Workflow 3: Multi-Variable Analysis

```bash
#!/bin/bash
# Download and process multiple variables

# Download weather package
./era5_download_generic.sh --variables weather --year 2020 --month 1 --output-dir ./data/raw/ERA5/

# Process all variables with both output formats
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_variables_202001.nc --output-dir ./data/proc/ERA5/complete/ --variables all --output-format both

# Process with geographic coordinates (for global analysis)
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_variables_202001.nc --output-dir ./data/proc/ERA5/geographic/ --variables all --target-crs EPSG:4326
```

### Workflow 4: Wind Analysis

```bash
#!/bin/bash
# Wind energy analysis workflow

# Download wind components
./era5_download_generic.sh --variables wind --year 2020 --month 1 --output-dir ./data/raw/ERA5/

# Process wind components
./era5_process_generic.sh --input-file ./data/raw/ERA5/era5_variables_202001.nc --output-dir ./data/proc/ERA5/wind/ --variables wind

# Calculate wind speed and direction (post-processing example)
python3 -c "
import xarray as xr
import numpy as np

# Load wind components
u = xr.open_dataset('./data/proc/ERA5/wind/era5_100m_u_component_of_wind_daily.nc')['100m_u_component_of_wind']
v = xr.open_dataset('./data/proc/ERA5/wind/era5_100m_v_component_of_wind_daily.nc')['100m_v_component_of_wind']

# Calculate wind speed and direction
wind_speed = np.sqrt(u**2 + v**2)
wind_direction = np.arctan2(v, u) * 180 / np.pi

# Save results
wind_speed.to_netcdf('./data/proc/ERA5/wind/wind_speed_daily.nc')
wind_direction.to_netcdf('./data/proc/ERA5/wind/wind_direction_daily.nc')

print('Wind speed and direction calculated')
"
```

## Troubleshooting

### Common Issues

#### Download Issues

##### **"CDS API key not found"**

```bash
# Check API key setup
ls -la ~/.cdsapirc
cat ~/.cdsapirc

# Test CDS connection
python3 -c "import cdsapi; c = cdsapi.Client(); print('CDS connection successful')"
```

##### **"Variable not found"**

```bash
# List available variables
./era5_download_generic.sh --list-variables

# Check CDS documentation
# Visit: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels
```

##### **"Download request failed"**

- CDS servers may be busy - retry later
- Check that you've accepted CDS license terms
- Verify year/month are within available range (1940-present)

#### Processing Issues

##### **"Input file not found"**

```bash
# Check file exists and has .nc extension
ls -la ./data/raw/ERA5/*.nc

# Verify NetCDF structure
ncdump -h ./data/raw/ERA5/era5_variables_202001.nc
```

##### **"Variable not found in file"**

```bash
# List variables in NetCDF file
python3 -c "
import xarray as xr
ds = xr.open_dataset('./data/raw/ERA5/era5_variables_202001.nc')
print('Variables in file:', list(ds.data_vars.keys()))
"

# Check variable configuration
./era5_process_generic.sh --list-config
```

##### **"Out of memory"**

```bash
# Use smaller chunks
./era5_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --chunk-size 6

# Process variables separately
./era5_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables 2m_temperature
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Debug processing
./era5_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --debug

# Check processing reports
cat ./data/output/processing_report.txt
```

## Advanced Usage

### Custom Projections

```bash
# Keep original WGS84 coordinates
./era5_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --target-crs EPSG:4326

# Use Web Mercator for web mapping
./era5_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --target-crs EPSG:3857

# Use UTM for regional analysis
./era5_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --target-crs EPSG:32612
```

### Batch Processing with Python

```python
import subprocess
from pathlib import Path

# Process multiple months
base_dir = Path('./data/')
variables = ['2m_temperature', 'surface_pressure', 'total_precipitation']
months = range(1, 13)
year = 2020

for month in months:
    # Download
    download_cmd = [
        './era5_download_generic.sh',
        '--variables', ','.join(variables),
        '--year', str(year),
        '--month', str(month),
        '--output-dir', str(base_dir / 'raw' / 'ERA5')
    ]
    
    print(f"Downloading month {month}")
    subprocess.run(download_cmd, check=True)
    
    # Process
    input_file = base_dir / 'raw' / 'ERA5' / f'era5_variables_{year}{month:02d}.nc'
    process_cmd = [
        './era5_process_generic.sh',
        '--input-file', str(input_file),
        '--output-dir', str(base_dir / 'proc' / 'ERA5' / f'month_{month:02d}'),
        '--variables', 'all'
    ]
    
    print(f"Processing month {month}")
    subprocess.run(process_cmd, check=True)
```

### Memory Management

For large files or limited memory systems:

```bash
# Process with smaller chunks
./era5_process_generic.sh --input-file ./data/large_file.nc --output-dir ./data/output/ --chunk-size 6

# Process variables individually
for var in 2m_temperature surface_pressure total_precipitation; do
    ./era5_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/$var/ --variables $var
done

# Use hourly processing to avoid aggregation overhead
./era5_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --aggregation hourly
```

## Installation Requirements

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: Sufficient space for data (ERA5 files: ~50MB per variable per month)
- **Network**: Internet connection for downloads

### Python Dependencies

```bash
# Required packages
pip install cdsapi xarray rioxarray numpy rasterio pandas psutil

# Optional for enhanced functionality
pip install matplotlib cartopy netcdf4
```

### CDS API Setup

1. Create account: https://cds.climate.copernicus.eu/
2. Get API key from profile: https://cds.climate.copernicus.eu/user
3. Accept license terms for ERA5 dataset
4. Set up credentials:

   ```bash
   echo "url: https://cds.climate.copernicus.eu/api/v2
   key: YOUR_UID:YOUR_API_KEY" > ~/.cdsapirc
   ```

## Performance Tips

### Download Optimization

- Download during off-peak hours for better speeds
- Use variable packages for efficiency
- Check CDS service status if downloads fail
- Large requests may be queued - be patient

### Processing Optimization

- Use daily aggregation for most applications (much smaller files)
- Process variables separately for very large datasets
- Use SSD storage for better I/O performance
- Monitor memory usage with `htop` or `free -h`

### Storage Management

- ERA5 raw files: ~50MB per variable per month
- Processed daily files: ~5MB per variable per month  
- Use compression (enabled by default)
- Clean up raw files after processing if space is limited

## Contributing

### Reporting Issues

- Provide specific error messages
- Include command that failed
- Share sample data if possible
- Specify system information

### Feature Requests

- Describe use case
- Provide examples of desired functionality
- Consider backwards compatibility

## References

### ERA5 Documentation

- [ERA5 Dataset Description](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels)
- [CDS API Documentation](https://cds.climate.copernicus.eu/api-how-to)
- [ERA5 Technical Documentation](https://confluence.ecmwf.int/display/CKB/ERA5)

### Technical Resources

- [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/)
- [ECMWF ERA5 Documentation](https://www.ecmwf.int/en/forecasts/datasets/reanalysis-datasets/era5)
- [NetCDF Climate and Forecast Conventions](http://cfconventions.org/)

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
*Framework validated with ERA5 reanalysis data from CDS*
