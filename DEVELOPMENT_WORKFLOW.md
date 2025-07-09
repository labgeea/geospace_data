# GEOSPACE Framework Development Workflow

**Version:** 1.0.0  
**Last Updated:** July 8, 2025  
**Framework:** GEOSPACE v1.0.0

This document outlines the development workflow for the GEOSPACE Framework, including how to make changes, add features, and manage semantic versioning.

## Overview

The GEOSPACE Framework uses [Semantic Versioning](https://semver.org/) with the format `MAJOR.MINOR.PATCH`:

- **MAJOR**: Incompatible API changes (1.0.0 → 2.0.0)
- **MINOR**: New functionality, backwards compatible (1.0.0 → 1.1.0)  
- **PATCH**: Bug fixes, backwards compatible (1.0.0 → 1.0.1)

## Daily Development Workflow

### 1. Making Code Changes

```bash
# Work on feature or bug fix
nano modis/modis_download_generic.py
nano ecmwf/era5_process_generic.py

# Test changes
python3 modis/modis_download_generic.py --help
./ecmwf/era5_process_generic.sh --version
```

### 2. Update Documentation as You Go

**Always update CHANGELOG.md during development:**

```bash
nano CHANGELOG.md
```

Add entries under the `[Unreleased]` section:

```markdown
## [Unreleased]
### Added
- Support for MOD15 LAI/FPAR products
- Batch processing for multiple dates
- New variable package: 'forest_detailed'

### Fixed
- Memory leak in MODIS tile processing
- Date parsing bug for leap years
- Download timeout issues for large files

### Changed
- Improved error messages for failed downloads
- Updated NASA Earthdata authentication method
- Enhanced quality control parameters

### Deprecated
- Old configuration format (will be removed in v2.0.0)

### Removed
- (Nothing in this release)

### Security
- Updated authentication tokens handling
```

### 3. Commit Changes Regularly

```bash
# Commit individual features/fixes
git add .
git commit -m "Add MOD15 LAI/FPAR product support

- Implement download logic for LAI/FPAR products
- Add configuration for MOD15A2H/MYD15A2H
- Update variable aliases and help text
- Add unit tests for new functionality"
```

## Release Workflow

### Step 1: Prepare for Release

**Before releasing, ensure:**

- [ ] All changes are committed
- [ ] CHANGELOG.md is updated
- [ ] Tests pass
- [ ] Documentation is current
- [ ] Version bump is appropriate

### Step 2: Update Version Numbers

**For Bug Fixes (PATCH: 1.0.0 → 1.0.1):**

```bash
# Update central version
sed -i 's/__version__ = "1.0.0"/__version__ = "1.0.1"/' version.py

# Verify the change
grep "__version__" version.py
```

**For New Features (MINOR: 1.0.0 → 1.1.0):**

```bash
sed -i 's/__version__ = "1.0.0"/__version__ = "1.1.0"/' version.py
```

**For Breaking Changes (MAJOR: 1.0.0 → 2.0.0):**

```bash
sed -i 's/__version__ = "1.0.0"/__version__ = "2.0.0"/' version.py
```

### Step 3: Update CHANGELOG.md

Move entries from `[Unreleased]` to new version section:

```markdown
## [Unreleased]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [1.0.1] - 2025-07-15
### Fixed
- Memory leak in MODIS tile processing for large datasets
- Date parsing bug for February 29th in leap years
- Download timeout issues for large files

### Changed
- Improved error messages for failed downloads

## [1.0.0] - 2025-07-08
### Added
- Initial stable release...
```

### Step 4: Commit Version Bump

```bash
git add .
git commit -m "Bump version to 1.0.1

- Fix memory leak in MODIS processing
- Improve date parsing for edge cases
- Enhance error handling for downloads"
```

### Step 5: Create Release Tag

**For Bug Fix Release:**

```bash
git tag -a v1.0.1 -m "Release v1.0.1 - Bug fixes

Fixed:
- Memory leak in MODIS tile processing for large datasets
- Date parsing bug for February 29th in leap years
- Download timeout issues for large files

Changed:
- Improved error messages for failed downloads"
```

**For Feature Release:**

```bash
git tag -a v1.1.0 -m "Release v1.1.0 - New features

Added:
- Support for MOD15 LAI/FPAR products
- Batch processing for multiple dates
- New 'forest_detailed' variable package

Fixed:
- Memory leak in MODIS processing
- Date parsing edge cases"
```

### Step 6: Push Release

```bash
# Push commits and tags
git push origin main --tags

# Verify release
git log --oneline --decorate -3
git tag -l
```

## Adding New Modules

### 1. Create Module Structure

```bash
# Create new module directory (example: sentinel)
mkdir sentinel/
cd sentinel/
```

### 2. Create Module Scripts

**Python Download Script:**

```bash
cat > sentinel_download_generic.py << 'EOF'
#!/usr/bin/env python3
"""
Sentinel satellite data download script
"""

# Version information
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_module_version

__version__ = get_module_version("sentinel")
__module__ = "Sentinel Download"

import argparse

def create_parser():
    parser = argparse.ArgumentParser(
        description=f'{__module__} Framework v{__version__} - Download Sentinel satellite data',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add version argument
    parser.add_argument('--version', action='version', version=f'{__module__} v{__version__}')
    
    # Add your arguments here...
    
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()
    
    # Your download logic here...
    print(f"Running {__module__} v{__version__}")

if __name__ == "__main__":
    main()
EOF

chmod +x sentinel_download_generic.py
```

**Shell Wrapper Script:**

```bash
cat > sentinel_download_generic.sh << 'EOF'
#!/bin/bash

# Version information
VERSION="1.1.0"
MODULE_NAME="Sentinel Download"

# Version display function
show_version() {
    echo "$MODULE_NAME Framework v$VERSION"
    exit 0
}

# Check for version argument
if [[ "$1" == "--version" || "$1" == "-V" ]]; then
    show_version
fi

# Your shell script logic here...
PYTHON_SCRIPT="$(dirname "$0")/sentinel_download_generic.py"
python3 "$PYTHON_SCRIPT" "$@"
EOF

chmod +x sentinel_download_generic.sh
```

**Create similar processing scripts** (`sentinel_process_generic.py` and `sentinel_process_generic.sh`)

### 3. Create Module Documentation

```bash
cat > sentinel_README.md << 'EOF'
# Sentinel Processing Framework

**Version:** 1.1.0  
**Module:** Sentinel  
**Last Updated:** July 15, 2025  
**Framework Compatibility:** GEOSPACE v1.1.0

A comprehensive framework for downloading and processing Sentinel satellite data for Continental United States (CONUS) analysis.

## Overview

This framework provides end-to-end processing of Sentinel data from download through analysis-ready outputs.

## Supported Products

- **Sentinel-1**: SAR data for land and ocean monitoring
- **Sentinel-2**: Multispectral imagery for land monitoring

## Quick Start

```bash
# Download Sentinel-2 data
./sentinel_download_generic.sh --product S2 --date 2020-01-15 --output-dir ./data/

# Process to analysis-ready format
./sentinel_process_generic.sh --input-dir ./data/ --output-dir ./processed/ --date 2020-01-15

EOF
```

### 4. Update Framework Files

**Update version.py:**

```bash
cd ..
nano version.py
```

Add the new module:

```python
# Module versions (all sync with main version for now)
MODIS_VERSION = __version__
ECMWF_VERSION = __version__
GRIDMET_VERSION = __version__
SENTINEL_VERSION = __version__  # Add this line

# Version info
VERSION_INFO = {
    "version": __version__,
    "modules": {
        "modis": MODIS_VERSION,
        "ecmwf": ECMWF_VERSION,
        "gridmet": GRIDMET_VERSION,
        "sentinel": SENTINEL_VERSION  # Add this line
    },
    # ... rest unchanged
}
```

**Update main README.md:**

```bash
nano README.md
```

Add new module to the modules table:

```markdown
| Module | Description | Version | Documentation |
|--------|-------------|---------|---------------|
| **MODIS** | Satellite vegetation indices, land surface temperature, forest cover | 1.1.0 | [modis/modis_README.md](modis/modis_README.md) |
| **ECMWF** | ERA5 reanalysis weather and climate data | 1.1.0 | [ecmwf/era5_README.md](ecmwf/era5_README.md) |
| **GridMET** | High-resolution meteorological data for CONUS | 1.1.0 | [gridmet/gridmet_README.md](gridmet/gridmet_README.md) |
| **Sentinel** | SAR and multispectral satellite imagery | 1.1.0 | [sentinel/sentinel_README.md](sentinel/sentinel_README.md) |
```

### 5. Test New Module

```bash
# Test version information
python3 version.py
python3 sentinel/sentinel_download_generic.py --version
./sentinel/sentinel_download_generic.sh --version
```

### 6. Update CHANGELOG.md

```bash
nano CHANGELOG.md
```

Add under `[Unreleased]`:

```markdown
### Added
- New Sentinel satellite data processing module
- Support for Sentinel-1 SAR and Sentinel-2 multispectral data
- Unified processing workflow for Sentinel products
```

### 7. Commit New Module

```bash
git add .
git commit -m "Add Sentinel satellite data processing module

- Implement Sentinel-1/2 download and processing scripts
- Add module documentation and version integration
- Update framework to support Sentinel products
- Add examples and configuration templates"
```

### 8. Release as Minor Version

When ready to release:

```bash
# Bump minor version (new feature)
sed -i 's/__version__ = "1.0.0"/__version__ = "1.1.0"/' version.py

# Update CHANGELOG.md (move Unreleased to 1.1.0)
# Commit and tag
git commit -m "Bump version to 1.1.0 - Add Sentinel module"
git tag -a v1.1.0 -m "Release v1.1.0 - Sentinel module support"
git push origin main --tags
```

## Version Bump Quick Reference

| Change Type | Version Change | Command | Use When |
|-------------|----------------|---------|----------|
| **Bug Fix** | 1.0.0 → 1.0.1 | `sed -i 's/1.0.0/1.0.1/' version.py` | Fix bugs, improve performance |
| **New Feature** | 1.0.0 → 1.1.0 | `sed -i 's/1.0.0/1.1.0/' version.py` | Add products, modules, options |
| **Breaking Change** | 1.0.0 → 2.0.0 | `sed -i 's/1.0.0/2.0.0/' version.py` | Change APIs, remove features |

## Testing Before Release

Always test the version system before releasing:

```bash
# Test central version system
python3 version.py

# Test all module versions
echo "=== Module Version Test ==="
python3 modis/modis_download_generic.py --version
python3 ecmwf/era5_process_generic.py --version
python3 gridmet/gridmet_download_generic.py --version

# Test shell scripts
./modis/modis_download_generic.sh --version
./ecmwf/era5_download_generic.sh --version
./gridmet/gridmet_download_generic.sh --version

# Test help displays version
python3 modis/modis_download_generic.py --help | head -5
```

## File Checklist

Before releasing, ensure these files are updated:

### Always Update

- [ ] `version.py` - Central version number
- [ ] `CHANGELOG.md` - Move unreleased entries to new version
- [ ] Module README files (if adding modules)

### For New Modules

- [ ] Create module directory and scripts
- [ ] Add version imports to Python scripts
- [ ] Add version variables to shell scripts
- [ ] Create module README with version header
- [ ] Update main `README.md` modules table
- [ ] Update `version.py` VERSION_INFO

### For Breaking Changes

- [ ] Update migration guide in README
- [ ] Consider deprecation warnings in previous version
- [ ] Update all documentation examples

## Common Commands

```bash
# Quick version check
python3 version.py

# Update version for patch release
sed -i 's/__version__ = "1.0.0"/__version__ = "1.0.1"/' version.py

# Update version for minor release  
sed -i 's/__version__ = "1.0.0"/__version__ = "1.1.0"/' version.py

# Update version for major release
sed -i 's/__version__ = "1.0.0"/__version__ = "2.0.0"/' version.py

# Create and push release
git commit -m "Bump version to X.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z - Description"
git push origin main --tags

# View recent releases
git tag -l
git log --oneline --decorate -5
```

## Best Practices

1. **Commit early and often** - Don't wait to commit changes
2. **Update CHANGELOG.md as you go** - Don't wait until release
3. **Test before releasing** - Always verify version system works
4. **Use descriptive commit messages** - Help future you understand changes
5. **Tag every release** - Provides clear release history
6. **Follow semantic versioning** - Users can predict compatibility
7. **Document breaking changes** - Help users migrate
8. **Keep releases focused** - Don't mix bug fixes with new features

## Troubleshooting

### Version Not Updating

```bash
# Check if version.py was updated
grep "__version__" version.py

# Verify module can import version
python3 -c "from version import get_module_version; print(get_module_version('modis'))"
```

### Git Tag Issues

```bash
# List all tags
git tag -l

# Delete a tag (if needed)
git tag -d v1.0.1
git push origin :refs/tags/v1.0.1

# Push tags separately if needed
git push origin --tags
```

### Module Import Errors

```bash
# Check Python path in module
python3 -c "import sys; print(sys.path)"

# Test module version import directly
cd modis/
python3 -c "import sys, os; sys.path.append('..'); from version import get_module_version; print(get_module_version('modis'))"
```

---
