#!/usr/bin/env python3
"""
GEOSPACE Framework Version Management
Central version file for all modules
"""

__version__ = "1.5.0"
__author__ = "GEOSPACE Project"
__license__ = "Public Domain"
__description__ = "Comprehensive framework for downloading and processing satellite and climate data"

# Module versions (all sync with main version for now)
MODIS_VERSION = __version__
ECMWF_VERSION = __version__
GRIDMET_VERSION = __version__
CAMS_VERSION = __version__
AQS_VERSION = __version__
SVI_VERSION = "1.0.0"
COI_VERSION = "1.0.0"

# Version info
VERSION_INFO = {
    "version": __version__,
    "modules": {
        "modis": MODIS_VERSION,
        "ecmwf": ECMWF_VERSION,
        "gridmet": GRIDMET_VERSION,
        "cams": CAMS_VERSION,
        "aqs": AQS_VERSION,
        "svi": SVI_VERSION,
        "coi": COI_VERSION
    },
    "description": __description__,
    "author": __author__,
    "license": __license__
}

def get_version():
    """Return the current version string."""
    return __version__

def get_module_version(module_name):
    """Return version for a specific module."""
    return VERSION_INFO["modules"].get(module_name.lower(), __version__)

def print_version():
    """Print version information."""
    print(f"GEOSPACE Framework v{__version__}")
    print(f"Author: {__author__}")
    print(f"License: {__license__}")
    print(f"Description: {__description__}")
    print("\nModule Versions:")
    for module, version in VERSION_INFO["modules"].items():
        print(f"  {module.upper()}: v{version}")

if __name__ == "__main__":
    print_version()
