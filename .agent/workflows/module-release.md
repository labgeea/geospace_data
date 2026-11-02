---
description: Full release workflow for adding a new GEOSPACE module (scripts → catalog → version → commit → tag → release notes → Zenodo)
---

# GEOSPACE Module Release Workflow

Repeatable process for releasing a new module into the GEOSPACE framework. Follow these steps in order.

## Prerequisites

- Module download and processing scripts are complete and tested on a feature branch
- The `xarray-env` and `geospatial` conda environments are available
- You have push access to `labgeea/geospace_data` on GitHub

## Step 0: Preflight

1. Check out the feature branch and confirm there are no uncommitted changes to tracked files:
   ```bash
   git switch feature/<module>-module
   git status --short | grep -v '^??'   # must print nothing
   git diff --cached --name-only        # must print nothing
   ```
2. List untracked files and show them to the user:
   ```bash
   git status --short | grep '^??'
   ```
3. Confirm none of the curation files will be staged. They are untracked work in progress: `dataverse_*`, `FAIR_DATA_STANDARDS.md`, `scratch/`. This check must print nothing, which means the branch doesn't bring them into `main`:
   ```bash
   git diff --name-only main...feature/<module>-module | grep -E '^(dataverse_|FAIR_DATA_STANDARDS\.md|scratch/)'
   ```
   Never use `git add .` or `git add -A` in this workflow. Stage explicit paths only (Step 9).

Stop and ask the user if any check fails.

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
- Shell wrappers check dependencies and credentials (they do not activate an environment)
- README documents usage, variables, and data source

## Step 2: Merge Feature Branch into Main

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

**Check the module key.** `get_module_version()` silently falls back to `__version__` for an unknown key, so a mismatch won't raise an error:
```bash
python3 -c "import version; k='<key>'; assert k in version.VERSION_INFO['modules'], f'{k} missing from VERSION_INFO'; print(k, version.get_module_version(k))"
grep -n 'get_module_version(' <module>/*.py   # every call must use '<key>'
```

**Check the wrappers read `version.py`.** This must print nothing:
```bash
grep -n '^VERSION=' <module>/*.sh
```
Wrappers should get the version from `version.py` via `python3 -c`, like `get_framework_version` in `aqs/aqs_download_generic.sh`.

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

Add rows for each new variable. Each row must have all 27 columns:

```
Domain,Dataset Name,Variable Description,Units,Source,Source URL,Source Documentation,Data Steward,Spatial Type,File Format,Download Script,Native Spatial Resolution,Spatial Extent,Coordinate System,Temporal Resolution,Temporal Extent,Processing Features,Processing Script,Dependencies,License,Attribution Requirements,Dataset Description,Version Added,Last Updated,Framework Compatibility,Script Alias,Processing Status
```

**Domain options:** `Built Environment`, `Weather`, `Air Quality`

**Tips:**
- Use a Python script to generate rows to avoid CSV formatting errors
- Verify Source URL and Source Documentation URLs are correct and stable
- `Download Script` and `Processing Script` must use the public `labgeea` repo, `blob/main`, and the `.sh` wrapper: `https://github.com/labgeea/geospace_data/blob/main/<module>/<prefix>_{download,process}_generic.sh` (never `sandbox-msh`, never a hardcoded `blob/vX.Y.Z`, and never `.py`)
- `Dataset Name` format: `<MODULE> <variable_alias>` (e.g., `FIRMS fire_count`)

**Verify** (from the repo root). This exits non-zero and lists the bad rows if any row doesn't have 27 columns, has a Domain outside the allowed list, or points to `sandbox-msh`:
```bash
python3 -c "import csv,sys; A={'Built Environment','Weather','Air Quality'}; r=list(csv.reader(open('catalog/geospace_metadata_catalog.csv',newline='',encoding='utf-8-sig'))); bad=[(i,len(x),x[0] if x else '') for i,x in enumerate(r[1:],1) if len(x)!=27 or x[0] not in A or 'sandbox-msh' in ','.join(x)]; print(f'{len(r)-1} rows, header has {len(r[0])} columns, {len(bad)} bad'); [print(f'row {i}: {n} columns, Domain={d!r}') for i,n,d in bad]; sys.exit(1 if bad or len(r[0])!=27 else 0)"
```

## Step 8: Generate Excel Catalog

// turbo
```bash
conda run -n geospatial --cwd catalog python3 convert_catalog.py
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

Write the release notes to `release_notes_v<VERSION>.md` at the repo root, under a `## GitHub release` heading, for the user to paste. **Do not publish the release** (no `gh release create`, no GitHub API or MCP release calls). Do not stage or commit this file.

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

- Full Changelog: https://github.com/labgeea/geospace_data/compare/v<PREV>...v<VERSION>
```

## Step 12: Draft Zenodo Entry

Append the Zenodo text to the same `release_notes_v<VERSION>.md` under a `## Zenodo` heading, for the user to paste. **Do not attempt to update Zenodo** or upload files. Draft:

1. **Title**: `GEOSPACE Geospatial Metadata Catalog v<VERSION>`
2. **Description**: Updated intro paragraph variable count, the new module's entry for the data source list, and the "Enhanced Features" section for the new version
3. **Upload**: Remind the user to upload `catalog/geospace_metadata_catalog_v<VERSION>.xlsx`
4. **Keywords**: Any new relevant keywords for the module

**Zenodo module entry format:**
```
<MODULE> – <Full Name> (N variables) <One-line description of what the data covers>
```

Then tell the user the file path.

## Step 13: Update the Repo Map

In `.agent/rules/repo_map.md`, update the "Checked against" line at the top to the new version, the release commit on `main` and today's date. Run this on `main` before committing the map change:

```bash
git rev-parse --short HEAD   # release commit on main (not the tag: v1.9.0 points at the feature-branch merge)
```

```
Checked against v<VERSION> (commit `<hash>`) on <YYYY-MM-DD>.
```

Commit only that file (`git add .agent/rules/repo_map.md`) with message `docs(agent): repo map checked against v<VERSION>`. It goes out with the next push.

## Version History

See `CHANGELOG.md`.
