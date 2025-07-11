# GEOSPACE Metadata Catalog

This directory contains the GEOSPACE metadata catalog in both CSV (version-controlled) and Excel (Zenodo-ready) formats.

## Files

- **`geospace_metadata_catalog.csv`** - Git-friendly version (edit this one)
- **`geospace_metadata_catalog_v{X.Y.Z}.xlsx`** - Generated Excel for Zenodo publishing
- **`convert_catalog.py`** - Conversion script
- **`CATALOG_README.md`** - This documentation

## Workflow

### 1. Edit the CSV File

```bash
# Edit the git-tracked CSV file
nano geospace_metadata_catalog.csv
git add geospace_metadata_catalog.csv
git commit -m "Add new datasets to catalog"
