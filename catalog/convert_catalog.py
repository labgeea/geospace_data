#!/usr/bin/env python3
"""
GEOSPACE Catalog Converter
Converts CSV metadata catalog to formatted Excel file for Zenodo publishing.

Usage:
    python3 convert_catalog.py
    python3 convert_catalog.py --version 1.1.0
"""

import pandas as pd
import argparse
import sys
import os
from datetime import datetime

# Version information
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import get_version

def create_parser():
    parser = argparse.ArgumentParser(
        description=f'GEOSPACE Catalog Converter v{get_version()}',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--version', action='version', version=f'Catalog Converter v{get_version()}')
    parser.add_argument('--input', '-i', default='geospace_metadata_catalog.csv',
                       help='Input CSV file (default: geospace_metadata_catalog.csv)')
    parser.add_argument('--output', '-o', 
                       help='Output Excel file (default: auto-generated with version)')
    parser.add_argument('--framework-version', 
                       help='Framework version for filename (default: from version.py)')
    
    return parser

def format_excel_file(df, output_file, framework_version):
    """Format the Excel file with professional styling."""
    
    # Create Excel writer with xlsxwriter engine for formatting
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        # Write main data
        df.to_excel(writer, sheet_name='Metadata_Catalog', index=False, startrow=4)
        
        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Metadata_Catalog']
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'left'
        })
        
        metadata_format = workbook.add_format({
            'bold': True,
            'font_size': 11
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'top',
            'text_wrap': True
        })
        
        url_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'top',
            'font_color': 'blue',
            'underline': True
        })
        
        # Add title and metadata
        worksheet.write('A1', 'GEOSPACE Metadata Catalog', title_format)
        worksheet.write('A2', f'Version: {framework_version}', metadata_format)
        worksheet.write('A3', f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', metadata_format)
        
        # Format headers
        for col, header in enumerate(df.columns):
            worksheet.write(4, col, header, header_format)
        
        # Format data cells
        for row in range(len(df)):
            for col, column in enumerate(df.columns):
                cell_value = df.iloc[row, col]
                if pd.isna(cell_value):
                    cell_value = ""
                
                # Use URL format for GitHub links
                if isinstance(cell_value, str) and 'github.com' in cell_value:
                    worksheet.write(row + 5, col, cell_value, url_format)
                else:
                    worksheet.write(row + 5, col, cell_value, cell_format)
        
        # Auto-adjust column widths
        for i, column in enumerate(df.columns):
            max_length = max(
                df[column].astype(str).map(len).max(),
                len(column)
            )
            # Cap at reasonable width
            width = min(max_length + 2, 50)
            worksheet.set_column(i, i, width)
        
        # Set row height for data rows
        worksheet.set_default_row(25)
        
        print(f"✓ Created formatted Excel file: {output_file}")
        print(f"  - {len(df)} variables cataloged")
        print(f"  - {len(df.columns)} metadata fields")

def validate_csv(df):
    """Validate the CSV data for completeness."""
    
    required_columns = [
        'Domain', 'Dataset Name', 'Variable Names', 'Source', 
        'Download Script', 'Processing Script'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ Missing required columns: {missing_columns}")
        return False
    
    # Check for empty critical fields
    critical_fields = ['Dataset Name', 'Source', 'Download Script']
    for field in critical_fields:
        empty_count = df[field].isna().sum()
        if empty_count > 0:
            print(f"⚠️  Warning: {empty_count} entries missing {field}")
    
    print(f"✓ CSV validation passed")
    return True

def update_github_links(df, framework_version):
    """Update GitHub links to use version-specific URLs."""
    
    github_columns = ['Download Script', 'Processing Script']
    updates_made = 0
    
    for column in github_columns:
        if column in df.columns:
            # Update GitHub URLs to use version-specific links
            mask = df[column].str.contains('github.com.*blob/main', na=False)
            if mask.any():
                df.loc[mask, column] = df.loc[mask, column].str.replace(
                    'blob/main', f'blob/v{framework_version}', regex=False
                )
                updates_made += mask.sum()
    
    if updates_made > 0:
        print(f"✓ Updated {updates_made} GitHub links to v{framework_version}")
    
    return df

def main():
    parser = create_parser()
    args = parser.parse_args()
    
    # Get framework version
    framework_version = args.framework_version or get_version()
    
    # Generate output filename if not provided
    if not args.output:
        args.output = f'geospace_metadata_catalog_v{framework_version}.xlsx'
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        print("   Create the CSV file first or specify correct path with --input")
        sys.exit(1)
    
    try:
        # Read CSV
        print(f"📖 Reading CSV: {args.input}")
        df = pd.read_csv(args.input)
        
        # Validate data
        if not validate_csv(df):
            sys.exit(1)
        
        # Update GitHub links to version-specific URLs
        df = update_github_links(df, framework_version)
        
        # Create formatted Excel file
        print(f"📝 Creating Excel file: {args.output}")
        format_excel_file(df, args.output, framework_version)
        
        print(f"\n✅ File generation complete!")
        print(f"  Excel file ready for Zenodo: {args.output}")
        print(f"  All GitHub links point to v{framework_version}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()