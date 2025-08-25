# CAMS Air Pollution Processing Framework

**Version:** 1.3.0  
**Module:** CAMS  
**Last Updated:** August 25, 2025  
**Framework Compatibility:** GEOSPACE v1.3.0

A comprehensive framework for downloading and processing CAMS (Copernicus Atmosphere Monitoring Service) air pollution variables from the Copernicus Atmosphere Data Store with focus on air quality analysis for Continental United States (CONUS).

## Overview

This framework provides end-to-end processing of CAMS data from download through analysis-ready outputs:

- **Download**: Automated downloading from Copernicus ADS with variable packages and temporal selection
- **Processing**: Convert NetCDF files to analysis-ready GeoTIFF/NetCDF with unit conversions and spatial processing
- **Configuration**: Unified configuration system supporting all CAMS air pollution variables
- **Unit Conversion**: Automated conversions (kg/m³→μg/m³, mg/m³)
- **Flexibility**: Support for single variables, variable groups, and time-series stack creation

## Quick Start

### 1. Setup

```bash
# Clone or download the framework
git clone <repository-url>
cd CONUS/geospace

# Set up ADS API credentials (same as CDS credentials)
echo "url: https://ads.atmosphere.copernicus.eu/api/v2
key: YOUR_UID:YOUR_API_KEY" > ~/.adsapirc

# Install Python dependencies
pip install cdsapi xarray rioxarray numpy rasterio pandas psutil
```

### 2. Download CAMS Data

```bash
# Download PM2.5 data for January 2020
./cams_download_generic.sh --variables pm25 --year 2020 --month 1 --output-dir ./data/raw/CAMS/

# Download air quality package (PM2.5, PM10, NO2, O3)
./cams_download_generic.sh --variables air_quality --year 2020 --month 1 --output-dir ./data/raw/CAMS/

# Download multiple variables
./cams_download_generic.sh --variables pm25,no2,co --year 2020 --month 1 --output-dir ./data/raw/CAMS/
```

### 3. Process Data

```bash
# Process PM2.5 with daily aggregation
./cams_process_generic.sh --input-file ./data/raw/CAMS/cams_pm25_202001.nc --output-dir ./data/proc/CAMS/ --variables pm25

# Process all variables in file
./cams_process_generic.sh --input-file ./data/raw/CAMS/cams_data.nc --output-dir ./data/proc/CAMS/ --variables all

# Process with time-series stacks and both output formats
./cams_process_generic.sh --input-file ./data/raw/CAMS/cams_pm25_202001.nc --output-dir ./data/proc/CAMS/ --variables pm25 --create-stacks --output-format both
```

## Framework Components

### Download Scripts
- **`cams_download_generic.py`** - Python download engine with ADS API integration
- **`cams_download_generic.sh`** - Bash wrapper with argument parsing and validation

### Processing Scripts  
- **`cams_process_generic.py`** - Python processing engine with unit conversions
- **`cams_process_generic.sh`** - Bash wrapper with comprehensive options

### Configuration
- **Built-in variable mapping** - Automatic handling of CAMS variable names and NetCDF mappings
- **Unit conversion system** - Automatic conversions for air quality variables

## Supported CAMS Variables

### Particulate Matter
- **`pm25`** (pm2p5) - PM2.5 mass concentration
- **`pm10`** (pm10) - PM10 mass concentration
- **Output**: μg/m³ (converted from kg/m³)
- **Temporal Resolution**: Hourly from CAMS reanalysis/forecast
- **Data Structure**: 3D (time, latitude, longitude)

### Trace Gases
- **`no2`** (no2) - Nitrogen dioxide concentration
- **`so2`** (so2) - Sulfur dioxide concentration  
- **`o3`** (go3) - Ground-level ozone concentration
- **Output**: μg/m³ (converted from kg/m³)
- **Temporal Resolution**: Hourly
- **Data Structure**: Variable (3D or 4D with model levels)

### Carbon Compounds
- **`co`** (co) - Carbon monoxide concentration
- **Output**: mg/m³ (converted from kg/m³)
- **Temporal Resolution**: Hourly
- **Data Structure**: 4D (time, model_level, latitude, longitude)

## Detailed Usage

### Download Framework

#### Basic Download Commands

```bash
# Download specific variable for month
./cams_download_generic.sh --variables pm25 --year 2020 --month 1 --output-dir ./data/raw/CAMS/

# Download multiple variables
./cams_download_generic.sh --variables pm25,no2,co --year 2020 --month 1 --output-dir ./data/raw/CAMS/

# Download with custom spatial extent
./cams_download_generic.sh --variables pm25 --year 2020 --month 1 --bbox "42,-125,32,-114" --output-dir ./data/raw/CAMS/
```

#### Variable Packages

Use predefined variable packages for convenience:

```bash
# Air quality package (PM2.5, PM10, NO2, O3)
./cams_download_generic.sh --variables air_quality --year 2020 --month 1 --output-dir ./data/raw/CAMS/

# Particulate matter package (PM2.5, PM10)
./cams_download_generic.sh --variables particulates --year 2020 --month 1 --output-dir ./data/raw/CAMS/

# Trace gases package (NO2, SO2, CO)
./cams_download_generic.sh --variables trace_gases --year 2020 --month 1 --output-dir ./data/raw/CAMS/

# All available variables
./cams_download_generic.sh --variables all --year 2020 --month 1 --output-dir ./data/raw/CAMS/
```

#### Download Options

| Option | Description | Example |
|--------|-------------|---------|
| `--variables` | Variables to download | `pm25`, `air_quality`, `all` |
| `--year` | Year to download | `2020` |
| `--month` | Month to download | `1` |
| `--data-type` | Dataset type | `reanalysis`, `forecast` |
| `--bbox` | Bounding box | `"50,-125,24,-66"` (CONUS) |
| `--output-dir` | Output directory | `./data/raw/CAMS/` |
| `--list-variables` | List available variables | |

### Processing Framework

#### Basic Processing Commands

```bash
# Process single variable with default settings
./cams_process_generic.sh --input-file ./data/raw/CAMS/cams_pm25_202001.nc --output-dir ./data/proc/CAMS/ --variables pm25

# Process all variables in file
./cams_process_generic.sh --input-file ./data/raw/CAMS/cams_data.nc --output-dir ./data/proc/CAMS/ --variables all

# Process with custom aggregation and format
./cams_process_generic.sh --input-file ./data/raw/CAMS/cams_pm25_202001.nc --output-dir ./data/proc/CAMS/ --variables pm25 --aggregation monthly --output-format both
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
| `--create-stacks` | Create time-series stacks | flag | disabled |
| `--chunk-size` | Memory management | integer | auto |
| `--list-config` | List variable configurations | | |
| `--debug` | Enable debug output | | |

#### Variable Groups

| Group | Variables | Description |
|-------|-----------|-------------|
| `air_quality` | pm25, pm10, no2, o3 | Primary air quality indicators |
| `particulates` | pm25, pm10 | Particulate matter analysis |
| `trace_gases` | no2, so2, co | Gaseous pollutants |
| `all` | All variables found in file | Complete dataset |

## Output Format

### File Naming Convention
**Download Output:**
- **Single variable**: `cams_<variable>_YYYYMM.nc`
- **Multiple variables**: `cams_variables_YYYYMM.nc`

**Processing Output:**
- **Individual files**: `cams_<variable>_<aggregation>_YYYYMMDD.tif`
- **Time-series stacks**: `cams_<variable>_<aggregation>_stack.tif`
- **NetCDF**: `cams_<variable>_<aggregation>.nc`

**Examples:**
```
# Download outputs
cams_pm25_202001.nc
cams_variables_202001.nc

# Processing outputs (individual files)
cams_pm25_daily_20200101.tif
cams_no2_daily_20200115.tif

# Processing outputs (time-series stacks)
cams_pm25_daily_stack.tif
cams_co_monthly_stack.nc
```

### File Properties
- **Input Format**: NetCDF4 from CAMS ADS
- **Output Format**: GeoTIFF (default) with LZW compression or NetCDF4
- **Coordinate System**: EPSG:5070 (CONUS Albers) by default
- **Spatial Resolution**: 0.75° (~80km) preserved or resampled  
- **NoData Value**: -9999.0
- **Tiling**: 512x512 pixel tiles for efficient access

### Directory Structure
```
data/
├── raw/                          # Downloaded NetCDF files
│   └── CAMS/
│       ├── cams_pm25_202001.nc
│       ├── cams_co_202001.nc
│       └── cams_variables_202001.nc
└── proc/                        # Processed outputs
    └── CAMS/
        ├── cams_pm25_daily_stack.tif
        ├── cams_no2_daily_stack.tif
        └── cams_co_daily_stack.tif
```

## Processing Features

### Automatic Unit Conversions
Air quality specific conversions for scientific consistency:

- **Particulate Matter**: kg/m³ → μg/m³ (multiply by 1×10⁹)
- **Trace Gases**: kg/m³ → μg/m³ (multiply by 1×10⁹)
- **Carbon Monoxide**: kg/m³ → mg/m³ (multiply by 1×10⁶)

### Multi-Dimensional Data Handling
- **3D Data** (PM2.5, PM10): `(time, latitude, longitude)` - processed directly
- **4D Data** (CO, trace gases): `(time, model_level, latitude, longitude)` - automatically reduces to 3D by selecting surface level (index 0)

### Temporal Aggregation
- **Daily**: Mean of hourly values
- **Monthly**: Mean of daily values  
- **Hourly**: No aggregation (preserve original resolution)

### Spatial Processing
- **Coordinate System**: Convert from WGS84 to target CRS
- **Resampling**: Bilinear resampling for continuous variables
- **Extent**: CONUS coverage with spatial subsetting
- **Resolution**: Preserve native resolution where possible

### Time-Series Options
- **Individual Files**: Separate file for each time step (default)
- **Time-Series Stacks**: Single multi-band file with `--create-stacks` option

## Troubleshooting

### Common Issues

#### Download Issues

**"ADS API key not found"**
```bash
# Check API key setup
ls -la ~/.adsapirc
cat ~/.adsapirc

# Test ADS connection
python3 -c "import cdsapi; c = cdsapi.Client(); print('ADS connection successful')"
```

**"Variable not found"**
```bash
# List available variables
./cams_download_generic.sh --list-variables

# Check ADS documentation
# Visit: https://ads.atmosphere.copernicus.eu/datasets/
```

**"Download request failed"**
- ADS servers may be busy - retry later
- Check that you've accepted CAMS dataset license terms
- Verify year/month are within available range (2003-present for reanalysis)

#### Processing Issues

**"Input file not found"**
```bash
# Check file exists and has .nc extension
ls -la ./data/raw/CAMS/*.nc

# Verify NetCDF structure
ncdump -h ./data/raw/CAMS/cams_pm25_202001.nc
```

**"TooManyDimensions error"**
- This is automatically handled for 4D data (like CO)
- If persists, check that the processing script correctly identifies extra dimensions

**"Variable not found in file"**
```bash
# List variables in NetCDF file
python3 -c "
import xarray as xr
ds = xr.open_dataset('./data/raw/CAMS/cams_variables_202001.nc')
print('Variables in file:', list(ds.data_vars.keys()))
"

# Check variable configuration
./cams_process_generic.sh --list-config
```

**"Out of memory"**
```bash
# Use smaller chunks
./cams_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --chunk-size 12

# Process variables separately
./cams_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables pm25
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Debug processing
./cams_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables pm25 --debug

# Check individual Python script
python3 cams_process_generic.py --input-file ./data/input.nc --output-dir ./data/output/ --variables pm25 --debug
```

## Advanced Usage

### Custom Projections

```bash
# Keep original WGS84 coordinates
./cams_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --target-crs EPSG:4326

# Use Web Mercator for web mapping
./cams_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --target-crs EPSG:3857

# Use UTM for regional analysis
./cams_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --target-crs EPSG:32612
```

### Batch Processing with Python

```python
import subprocess
from pathlib import Path

# Process multiple pollutants and months
base_dir = Path('./data/')
variables = ['pm25', 'no2', 'co']
months = range(1, 13)
year = 2020

for variable in variables:
    for month in months:
        # Download
        download_cmd = [
            './cams_download_generic.sh',
            '--variables', variable,
            '--year', str(year),
            '--month', str(month),
            '--output-dir', str(base_dir / 'raw' / 'CAMS')
        ]
        
        print(f"Downloading {variable} for {year}-{month:02d}")
        subprocess.run(download_cmd, check=True)
        
        # Process
        input_file = base_dir / 'raw' / 'CAMS' / f'cams_{variable}_{year}{month:02d}.nc'
        process_cmd = [
            './cams_process_generic.sh',
            '--input-file', str(input_file),
            '--output-dir', str(base_dir / 'proc' / 'CAMS' / variable),
            '--variables', variable,
            '--create-stacks'
        ]
        
        print(f"Processing {variable} for {year}-{month:02d}")
        subprocess.run(process_cmd, check=True)
```

### Memory Management

For large files or limited memory systems:

```bash
# Process with smaller chunks
./cams_process_generic.sh --input-file ./data/large_file.nc --output-dir ./data/output/ --chunk-size 10

# Process variables individually
for var in pm25 no2 co; do
    ./cams_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/$var/ --variables $var
done

# Use hourly processing to avoid aggregation overhead
./cams_process_generic.sh --input-file ./data/input.nc --output-dir ./data/output/ --variables all --aggregation hourly
```

## Installation Requirements

### System Requirements
- **OS**: Linux, macOS, or Windows with WSL
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: Sufficient space for data (CAMS files: ~50-200MB per variable per month)
- **Network**: Internet connection for ADS downloads

### Python Dependencies
```bash
# Required packages
pip install cdsapi xarray rioxarray numpy rasterio pandas psutil

# Optional for enhanced functionality
pip install matplotlib cartopy netcdf4
```

### ADS API Setup
1. Create account: https://ads.atmosphere.copernicus.eu/
2. Get API key from profile (same as CDS credentials)
3. Accept license terms for CAMS datasets
4. Set up credentials:
   ```bash
   echo "url: https://ads.atmosphere.copernicus.eu/api/v2
   key: YOUR_UID:YOUR_API_KEY" > ~/.adsapirc
   ```

## Performance Tips

### Download Optimization
- Download during off-peak hours for better speeds
- Use variable packages for efficiency  
- Check ADS service status if downloads fail
- CAMS requests may be queued - be patient

### Processing Optimization  
- Use daily aggregation for most air quality applications
- Process variables separately for very large datasets
- Use SSD storage for better I/O performance
- Create time-series stacks for temporal analysis workflows
- Monitor memory usage with `htop` or `free -h`

### Storage Management
- CAMS raw files: ~50-200MB per variable per month
- Processed daily files: varies by temporal extent and format
- Use compression (enabled by default)
- Time-series stacks are more efficient for multi-temporal analysis
- Clean up raw files after processing if space is limited

## Contributing

### Reporting Issues
- Provide specific error messages
- Include command that failed
- Share sample data if possible
- Specify air quality variable and time period
- Include system information

### Feature Requests
- Describe air quality use case
- Provide examples of desired functionality
- Consider compatibility with existing workflows

## References

### CAMS Documentation
- [CAMS Homepage](https://atmosphere.copernicus.eu/catalogue)
- [Atmosphere Data Store](https://ads.atmosphere.copernicus.eu/)
- [CAMS Data Documentation](https://confluence.ecmwf.int/display/CKB/CAMS)

### Technical Resources
- [Copernicus Atmosphere Data Store](https://ads.atmosphere.copernicus.eu/)
- [CAMS Air Quality Forecasts](https://atmosphere.copernicus.eu/charts/cams/particulate-matter-forecasts)
- [NetCDF Climate and Forecast Conventions](http://cfconventions.org/)

## License

This framework is released under the Public Domain license. Individual components may have different licenses - see source files for details.

## Support

For questions or issues:
1. Check this documentation
2. Review troubleshooting section
3. Check CAMS data availability and ADS service status
4. Submit issues with detailed information
5. Contact the GEOSPACE Project team

---

*Last updated: August 2025*  
*Version: 1.2.0*  
*Framework validated with CAMS air pollution data from ADS*