#!/usr/bin/env python3
"""
EPA AQS Criteria Pollutants Download Script
==================================================

This script downloads EPA AQS criteria air pollutant data using the EPA AQS API.
Designed to work with the GEOSPACE framework for air quality data processing.

Requirements:
- requests, pandas, numpy
- EPA AQS API account (email and key)

Author: GEOSPACE Project
Date: September 2025
License: Public Domain

Usage:
    python aqs_download_fixed.py --variables PM25 --year 2023 --state CA
    python aqs_download_fixed.py --variables criteria --year 2023 --state 06 --county 037
"""

# Import version from framework
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_module_version

__version__ = get_module_version("aqs")
__module__ = "EPA AQS Download"

import time
import json
import argparse
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Optional, Tuple, Any

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)


# EPA AQS API Configuration
AQS_BASE_URL = 'https://aqs.epa.gov/data/api'
AQS_ENDPOINTS = {
    'sample_data': 'sampleData',
    'daily_data': 'dailyData', 
    'annual_data': 'annualData',
    'monitors': 'monitors',
    'lists': 'list'
}

# Criteria Air Pollutants (EPA National Ambient Air Quality Standards)
CRITERIA_POLLUTANTS = {
    'CO': {
        'parameter_code': '42101',
        'name': 'Carbon Monoxide',
        'units': 'ppm',
        'description': 'Carbon monoxide 1-hour average',
        'aliases': ['carbon_monoxide', 'co', '42101'],
        'typical_range': [0, 50],
        'naaqs_standard': '35 ppm (1-hour), 9 ppm (8-hour)'
    },
    'Pb': {
        'parameter_code': '12128',
        'name': 'Lead (TSP) LC',
        'units': 'μg/m³',
        'description': 'Lead (TSP) STP - Local Conditions',
        'aliases': ['lead', 'pb', 'lead_tsp', '12128'],
        'typical_range': [0, 1.5],
        'naaqs_standard': '0.15 μg/m³ (3-month rolling average)'
    },
    'NO2': {
        'parameter_code': '42602',
        'name': 'Nitrogen Dioxide',
        'units': 'ppb',
        'description': 'Nitrogen dioxide 1-hour average',
        'aliases': ['nitrogen_dioxide', 'no2', '42602'],
        'typical_range': [0, 200],
        'naaqs_standard': '100 ppb (1-hour), 53 ppb (annual)'
    },
    'Ozone': {
        'parameter_code': '44201',
        'name': 'Ozone',
        'units': 'ppm',
        'description': 'Ozone 8-hour maximum daily average',
        'aliases': ['ozone', 'o3', '44201'],
        'typical_range': [0, 0.2],
        'naaqs_standard': '0.070 ppm (8-hour)'
    },
    'PM10': {
        'parameter_code': '81102',
        'name': 'PM10 Local Conditions',
        'units': 'μg/m³',
        'description': 'PM10 Total 0-10 micrometers LC',
        'aliases': ['pm10', 'pm_10', 'particulate_10', '81102'],
        'typical_range': [0, 250],
        'naaqs_standard': '150 μg/m³ (24-hour)'
    },
    'PM25': {
        'parameter_code': '88101',
        'name': 'PM2.5 Local Conditions',
        'units': 'μg/m³',
        'description': 'PM2.5 - Local Conditions',
        'aliases': ['pm25', 'pm2.5', 'pm_25', 'particulate_25', '88101'],
        'typical_range': [0, 150],
        'naaqs_standard': '35 μg/m³ (24-hour), 12 μg/m³ (annual)'
    },
    'SO2': {
        'parameter_code': '42401',
        'name': 'Sulfur Dioxide',
        'units': 'ppb',
        'description': 'Sulfur dioxide 1-hour average',
        'aliases': ['sulfur_dioxide', 'so2', '42401'],
        'typical_range': [0, 1000],
        'naaqs_standard': '75 ppb (1-hour), 0.03 ppm (annual)'
    }
}

# Variable packages for convenient downloading
VARIABLE_PACKAGES = {
    'criteria': list(CRITERIA_POLLUTANTS.keys()),
    'pm': ['PM25', 'PM10'],
    'gases': ['CO', 'NO2', 'Ozone', 'SO2'],
    'all': list(CRITERIA_POLLUTANTS.keys())
}

# State FIPS codes for common states (can be expanded)
STATE_CODES = {
    'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06', 'CO': '08',
    'CT': '09', 'DE': '10', 'FL': '12', 'GA': '13', 'HI': '15', 'ID': '16',
    'IL': '17', 'IN': '18', 'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22',
    'ME': '23', 'MD': '24', 'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28',
    'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33', 'NJ': '34',
    'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39', 'OK': '40',
    'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45', 'SD': '46', 'TN': '47',
    'TX': '48', 'UT': '49', 'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54',
    'WI': '55', 'WY': '56'
}

class AQSAPIClient:
    """Client for EPA AQS API with rate limiting and error handling"""
    
    def __init__(self, email=None, api_key=None):
        self.email = email or os.getenv('EPA_AQS_EMAIL')
        self.api_key = api_key or os.getenv('EPA_AQS_KEY')
        self.last_request_time = 0
        self.min_interval = 6  # 6 seconds between requests (10 per minute limit)
        self.session = requests.Session()
        
        if not self.email or not self.api_key:
            raise ValueError(
                "EPA AQS credentials not found. Set EPA_AQS_EMAIL and EPA_AQS_KEY "
                "environment variables or provide them as arguments."
            )
    
    def _wait_for_rate_limit(self):
        """Ensure rate limiting compliance"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            print(f"  Rate limiting: waiting {wait_time:.1f}s")
            time.sleep(wait_time)
    
    def make_request(self, endpoint, params, max_retries=3):
        """Make API request with rate limiting and error handling"""
        self._wait_for_rate_limit()
        
        # Add authentication
        params.update({
            'email': self.email,
            'key': self.api_key
        })
        
        url = f"{AQS_BASE_URL}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                print(f"  API request: {endpoint}")
                response = self.session.get(url, params=params, timeout=30)
                self.last_request_time = time.time()
                
                response.raise_for_status()
                
                data = response.json()
                
                # Check API-specific status
                if 'Header' in data and len(data['Header']) > 0:
                    status = data['Header'][0].get('status', '').lower()
                    if 'failed' in status:
                        errors = data['Header'][0].get('error', ['Unknown error'])
                        raise ValueError(f"API error: {'; '.join(errors)}")
                    elif 'no data matched' in status:
                        print("  No data found for request")
                        return {'Header': data['Header'], 'Data': []}
                
                # FIXED: EPA AQS API uses 'Data' key, not 'Body'
                records = data.get('Data', data.get('Body', []))
                print(f"  Retrieved {len(records)} records")
                
                # Standardize the response format
                return {'Header': data.get('Header', []), 'Data': records}
                
            except requests.exceptions.RequestException as e:
                print(f"  Request attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"  Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
        
        raise Exception(f"Failed to make request after {max_retries} attempts")

def normalize_state_code(state):
    """Convert state name/abbreviation to FIPS code"""
    if not state:
        return None
    
    state = str(state).strip().upper()
    
    # If already a FIPS code
    if state.isdigit() and len(state) in [1, 2]:
        return state.zfill(2)
    
    # If state abbreviation
    if state in STATE_CODES:
        return STATE_CODES[state]
    
    # Try to find by name
    for abbr, code in STATE_CODES.items():
        if state.startswith(abbr):
            return code
    
    raise ValueError(f"Unknown state: {state}")

def normalize_variables(variables):
    """Normalize variable names using aliases and packages"""
    normalized = []
    unknown_vars = []
    
    for var in variables:
        var_clean = var.strip()
        
        # Check if it's a package
        if var_clean.lower() in VARIABLE_PACKAGES:
            package_vars = VARIABLE_PACKAGES[var_clean.lower()]
            for pvar in package_vars:
                if pvar not in normalized:
                    normalized.append(pvar)
            continue
        
        # Check if it's a direct variable name
        if var_clean in CRITERIA_POLLUTANTS:
            if var_clean not in normalized:
                normalized.append(var_clean)
            continue
        
        # Check aliases and parameter codes
        found = False
        for pollutant_name, config in CRITERIA_POLLUTANTS.items():
            if (var_clean.lower() in [alias.lower() for alias in config.get('aliases', [])] or
                var_clean == config.get('parameter_code')):
                if pollutant_name not in normalized:
                    normalized.append(pollutant_name)
                found = True
                break
        
        if not found:
            unknown_vars.append(var)
    
    if unknown_vars:
        print(f"Warning: Unknown variable names: {unknown_vars}")
        print("Use --list-variables to see available options")
    
    return normalized

def list_available_variables():
    """List all available criteria pollutants and packages"""
    print("Available EPA AQS Criteria Pollutants:")
    print("=" * 60)
    
    for var_name, config in CRITERIA_POLLUTANTS.items():
        print(f"\n{var_name}: {config['description']}")
        print(f"  Parameter Code: {config['parameter_code']}")
        print(f"  Units: {config['units']}")
        print(f"  Range: {config['typical_range']}")
        print(f"  NAAQS: {config['naaqs_standard']}")
        if config.get('aliases'):
            aliases_str = ', '.join(config['aliases'])
            print(f"  Aliases: {aliases_str}")
    
    print("\nVariable Packages:")
    print("-" * 40)
    for package, vars_list in VARIABLE_PACKAGES.items():
        vars_str = ', '.join(vars_list)
        print(f"  {package}: {vars_str}")

def setup_output_directory(output_dir):
    """Create output directory if it doesn't exist"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return output_dir

def download_aqs_data(variables, year, state=None, county=None, site=None, 
                     data_type='daily', output_dir="./data/raw/AQS/"):
    """
    Download EPA AQS criteria pollutant data
    
    Parameters:
    -----------
    variables : list
        List of pollutant names to download
    year : int
        Year to download
    state : str, optional
        State FIPS code or abbreviation
    county : str, optional
        County FIPS code (3 digits)
    site : str, optional
        Site number (4 digits)
    data_type : str
        Type of data ('sample', 'daily', 'annual')
    output_dir : str
        Directory to save downloaded files
    
    Returns:
    --------
    dict
        Results of download operation
    """
    
    # Setup
    setup_output_directory(output_dir)
    client = AQSAPIClient()
    
    # Normalize variables
    variables = normalize_variables(variables)
    if not variables:
        print("✗ No valid variables specified")
        return {}
    
    # Normalize state
    if state:
        state = normalize_state_code(state)
    
    print(f"Downloading EPA AQS {data_type} data for {year}")
    print(f"Variables: {', '.join(variables)}")
    if state:
        print(f"State: {state}")
    if county:
        print(f"County: {county}")
    if site:
        print(f"Site: {site}")
    print(f"Output directory: {output_dir}")
    print("-" * 60)
    
    results = {}
    total_records = 0
    
    # Download each variable
    for i, variable in enumerate(variables):
        print(f"\nDownloading variable {i+1}/{len(variables)}: {variable}")
        
        config = CRITERIA_POLLUTANTS[variable]
        param_code = config['parameter_code']
        
        # Set up date range (full year)
        bdate = f"{year}0101"
        edate = f"{year}1231"
        
        # Build request parameters
        params = {
            'param': param_code,
            'bdate': bdate,
            'edate': edate
        }
        
        # Add geographic filters
        if site and county and state:
            endpoint = f"{AQS_ENDPOINTS[data_type + '_data']}/bySite"
            params.update({
                'state': state,
                'county': county.zfill(3),
                'site': site.zfill(4)
            })
        elif county and state:
            endpoint = f"{AQS_ENDPOINTS[data_type + '_data']}/byCounty"
            params.update({
                'state': state,
                'county': county.zfill(3)
            })
        elif state:
            endpoint = f"{AQS_ENDPOINTS[data_type + '_data']}/byState"
            params.update({
                'state': state
            })
        else:
            # If no geographic filter, get data for major states
            print("  No geographic filter specified, downloading for major states")
            endpoint = f"{AQS_ENDPOINTS[data_type + '_data']}/byState"
            params.update({
                'state': '06'  # California as example
            })
        
        try:
            # Make API request
            data = client.make_request(endpoint, params)
            
            # FIXED: Check for 'Data' key instead of 'Body'
            if data and 'Data' in data and len(data['Data']) > 0:
                # Save raw JSON
                filename = f"aqs_{variable.lower()}_{data_type}_{year}"
                if state:
                    filename += f"_state{state}"
                if county:
                    filename += f"_county{county}"
                if site:
                    filename += f"_site{site}"
                filename += ".json"
                
                output_file = Path(output_dir) / filename
                
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                record_count = len(data['Data'])
                total_records += record_count
                
                results[variable] = {
                    'records': record_count,
                    'file': str(output_file),
                    'parameter_code': param_code
                }
                
                print(f"  ✓ {variable}: {record_count} records saved to {filename}")
                
            else:
                results[variable] = {
                    'records': 0,
                    'file': None,
                    'parameter_code': param_code
                }
                print(f"  ⚠ {variable}: No data found")
        
        except Exception as e:
            print(f"  ✗ {variable}: Download failed - {e}")
            results[variable] = {
                'records': 0,
                'file': None,
                'parameter_code': param_code,
                'error': str(e)
            }
    
    # Summary
    print(f"\n{'='*60}")
    print("Download Summary:")
    print(f"  Variables processed: {len(variables)}")
    print(f"  Total records: {total_records}")
    print(f"  Output directory: {output_dir}")
    
    return {
        'variables': results,
        'summary': {
            'total_records': total_records,
            'year': year,
            'data_type': data_type
        }
    }

def main():
    """Main function to download EPA AQS criteria pollutant data"""
    parser = argparse.ArgumentParser(
        description=f'{__module__} v{__version__} - Download EPA AQS criteria pollutant data (FIXED)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
# Download PM2.5 data for California in 2023
%(prog)s --variables PM25 --year 2023 --state CA

# Download all criteria pollutants for a specific county
%(prog)s --variables criteria --year 2023 --state 06 --county 037

# Download ozone data for a specific site
%(prog)s --variables Ozone --year 2023 --state TX --county 201 --site 0024

# Download PM suite for multiple states
%(prog)s --variables pm --year 2023 --state CA,TX,NY

Requirements:
- EPA AQS API account and credentials
- EPA_AQS_EMAIL and EPA_AQS_KEY environment variables
- requests, pandas, numpy
        """
    )
    
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    parser.add_argument('--variables', '--vars', '-v', type=str, 
                       help='Comma-separated list of variables or packages', required=False)
    parser.add_argument('--year', '-y', type=int, help='Year to download', required=False)
    parser.add_argument('--state', '-s', type=str, help='State FIPS code or abbreviation', required=False)
    parser.add_argument('--county', '-c', type=str, help='County FIPS code (3 digits)', required=False)
    parser.add_argument('--site', type=str, help='Site number (4 digits)', required=False)
    parser.add_argument('--data-type', type=str, choices=['sample', 'daily', 'annual'], 
                       help='Type of data to download (default: daily)', default='daily')
    parser.add_argument('-o', '--output-dir', type=str, 
                       help='Output directory for downloaded files', required=False)
    parser.add_argument('--list-variables', action='store_true', 
                       help='List all available variables and their aliases')
    
    args = parser.parse_args()
    
    # Handle list variables request
    if args.list_variables:
        list_available_variables()
        sys.exit(0)
    
    # Use command line args or defaults
    VARIABLES = args.variables.split(',') if args.variables else ['PM25']
    YEAR = args.year if args.year else 2023
    STATE = args.state
    COUNTY = args.county
    SITE = args.site
    DATA_TYPE = args.data_type
    OUTPUT_DIR = args.output_dir if args.output_dir else "./data/raw/AQS/"
    
    print("EPA AQS Criteria Pollutant Download Script (FIXED)")
    print("============================================================")
    
    # Check credentials
    if not (os.getenv('EPA_AQS_EMAIL') and os.getenv('EPA_AQS_KEY')):
        print("✗ Error: EPA AQS credentials not found")
        print("Please set environment variables:")
        print("  export EPA_AQS_EMAIL=your_email@example.com")
        print("  export EPA_AQS_KEY=your_api_key")
        print("Register at: https://aqs.epa.gov/aqsweb/documents/data_api.html#signup")
        sys.exit(1)
    
    # Download data
    results = download_aqs_data(
        variables=VARIABLES,
        year=YEAR,
        state=STATE,
        county=COUNTY,
        site=SITE,
        data_type=DATA_TYPE,
        output_dir=OUTPUT_DIR
    )
    
    # Final summary
    if results and results['summary']['total_records'] > 0:
        print("\n✓ Process completed successfully!")
        print(f"✓ Downloaded {results['summary']['total_records']} records")
        print(f"✓ Output directory: {OUTPUT_DIR}")
        print("✓ Ready for processing with aqs_process_generic.py")
    else:
        print("\n⚠ No data downloaded")
        print("Check geographic filters and date range")
        print("Use --list-variables to see available pollutants")

if __name__ == "__main__":
    main()