---
description: Full release workflow for adding a new GEOSPACE module (scripts → catalog → version → commit → tag → release notes → Zenodo)
---

# GEOSPACE Module Release Workflow

Repeatable process for releasing a new module into the GEOSPACE framework. Follow these steps in order.

## Prerequisites

- Module download and processing scripts are complete and tested on a feature branch
- The `geospatial` conda environment is available (`mamba activate geospatial`)
- You have push access to `sandbox-msh/geospace_data` on GitHub

## Step 1: Finalize Module Scripts

Ensure the feature branch (`feature/<module>-module`) contains:

```
<module>/
├── <module>_download_generic.py   # Download script with version import
├── <module>_download_generic.sh   # Shell wrapper
├── <module>_process_generic.py    # Processing script with version import
├── <module>_process_generic.sh    # Shell wrapper
└── <module>_README.md             # Module documentation
```

**Verify:**
- Scripts import version from central `version.py`
- Shell wrappers handle environment activation
- README documents usage, variables, and data source

## Step 2: Merge Feature Branch into Main

// turbo
1. Check current branch state: `git branch && git log --oneline main..feature/<module>-module`
2. Merge with: `git merge feature/<module>-module --no-commit --no-ff`
3. Resolve any merge conflicts (common in `README.md`, `VARIABLE_CATALOG.md`, `CHANGELOG.md`, `version.py`)
4. When resolving conflicts, keep content from **both** sides — existing main content plus new module additions

## Step 3: Update `version.py`

Bump `__version__` to the new version (e.g., `"1.X.0"`). Add the new module version constant:

```python
<MODULE>_VERSION = "1.0.0"
```

**Verify:** The feature branch may already have this done. If so, just confirm the version is correct after merge.

## Step 4: Update `VARIABLE_CATALOG.md`

1. **Summary table** (top of file): Add a row for the new module with variable count, resolution, temporal extent, and source
2. **Variables section**: Add a new `## <Module> Variables` section at the end with subsections as needed
3. Use the same table format: `| Variable | Description | Resolution | Temporal | Script Alias |`

**Source of truth:** The variable list should match the processing script's variable mappings/column definitions exactly.

## Step 5: Update `README.md`

1. Bump the **header version** (`**Version:** X.Y.Z`)
2. Add the new module to the **module table** if not already present
3. Bump the **footer version** (`**Current Version:** X.Y.Z`)

## Step 6: Update `CHANGELOG.md`

Add a new version section at the top following the existing format. Include:
- New module name and description
- Variable count and categories
- Any bug fixes or catalog changes

## Step 7: Update `catalog/geospace_metadata_catalog.csv`

Add rows for each new variable. Each row must have all 26 columns:

```
Domain, Dataset Name, Variable Names, Source, Source URL, Source Documentation,
Data Steward, Data Type, File Format, Download Script, Native Spatial Resolution,
Spatial Extent, Coordinate System, Temporal Resolution, Temporal Extent,
Processing Features, Processing Script, Dependencies, License,
Attribution Requirements, Dataset Description, Version Added, Last Updated,
Framework Compatibility, Script Alias, Processing Status
```

**Domain options:** `Built Environment`, `Weather`, `Air Quality`

**Tips:**
- Use a Python script to generate rows to avoid CSV formatting errors
- Verify Source URL and Source Documentation URLs are correct and stable
- `Dataset Name` format: `<MODULE> <variable_alias>` (e.g., `FIRMS fire_count`)

## Step 8: Generate Excel Catalog

// turbo
```bash
cd catalog/
python convert_catalog.py
```

This produces `geospace_metadata_catalog_v<VERSION>.xlsx` for Zenodo.

**Verify:** Script should report total variables cataloged and no errors.

## Step 9: Commit and Tag

1. Stage all changes:
   ```bash
   git add README.md VARIABLE_CATALOG.md CHANGELOG.md version.py \
     catalog/geospace_metadata_catalog.csv \
     catalog/geospace_metadata_catalog_v<VERSION>.xlsx \
     <module>/
   ```

2. Commit with conventional format:
   ```
   Merge branch 'feature/<module>-module' - Add <Module Name> module v<VERSION>

   - <Module description>
   - <Variable count> variables added to metadata catalog
   - Generated v<VERSION> Excel catalog for Zenodo
   ```

3. Tag:
   ```bash
   git tag -a v<VERSION> -m "Release v<VERSION> - <Module Name>

   New module: <MODULE> (<Full Name>)
   - <Key features>
   - <Variable summary>"
   ```

## Step 10: Push to GitHub

```bash
git push origin main --tags
```

## Step 11: Draft GitHub Release Notes

Follow the established format (see previous releases for reference):

```
What's New in v<VERSION>

<Module Category> (<Module Name>)

- New <MODULE> Module
  - <Feature list>
  - <Variable categories and counts>

- Catalog Updates
  - Updated geospace_metadata_catalog.csv with N new variables (M total)
  - Generated v<VERSION> Excel catalog for Zenodo

- Breaking Changes
  - None – fully backward compatible.

- Full Dataset Coverage
  - <List all modules with variable counts, mark new one as NEW>

- Full Changelog: https://github.com/sandbox-msh/geospace_data/compare/v<PREV>...v<VERSION>
```

## Step 12: Update Zenodo Entry

Update the Zenodo dataset description:

1. **Title**: `GEOSPACE Geospatial Metadata Catalog v<VERSION>`
2. **Description**: Update the intro paragraph variable count, add the new module's entry to the data source list, and update the "Enhanced Features" section for the new version
3. **Upload**: Add the new `geospace_metadata_catalog_v<VERSION>.xlsx` file
4. **Keywords**: Add any new relevant keywords for the module

**Zenodo module entry format:**
```
<MODULE> – <Full Name> (N variables) <One-line description of what the data covers>
```

## Quick Reference: Version History

| Version | Module | Variables Added |
|---------|--------|-----------------|
| 1.0.0–1.4.0 | MODIS, ECMWF, GridMET, CAMS, AQS | 48 |
| 1.5.0 | SVI, COI | 63 |
| 1.6.0 | PLACES | 40 |
| 1.7.0 | FIRMS | 16 |
