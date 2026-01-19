#!/usr/bin/env python3
"""
Script to change date format in CSV from MM/DD/YYYY to DD/MM/YYYY.
"""

import sys
import os
import csv
from datetime import datetime

def is_valid_date(date_string, format='%Y-%m-%d'):
    try:
        datetime.strptime(date_string, format)
        return True
    except ValueError:
        return False
    
def reformat_dates(input_file, output_file=None):
    if output_file is None:
        output_file = input_file  # Overwrite if no output specified

    # Read all rows from input CSV
    with open(input_file, 'r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Process each row
    for i, row in enumerate(rows):
        if i == 0:  # Skip header
            continue
        if row and row[0]:  # Date is in first column
            if is_valid_date(row[0], '%Y-%m-%d'):
                date_obj = datetime.strptime(row[0], '%Y-%m-%d')
                row[0] = date_obj.strftime('%d/%m/%Y')
            else:
                print(f"Skipping invalid date '{row[0]}' in row {i+1}")
                continue  # Skip this row
        
        # Format last column (Volume) with thousands separator
        if len(row) > 1:
            try:
                volume = int(row[-1].replace(',', ''))
                row[-1] = f"{volume:,}"
            except ValueError:
                pass  # If not a number, leave as is
        

    # Write to output CSV (skip quoting for header, quote all except first for data)
    with open(output_file, 'w', newline='') as f:
        for i, row in enumerate(rows):
            if row:
                if i == 0:  # Header row, no quotes
                    f.write(','.join(row) + '\n')
                else:  # Data rows, first column unquoted, others quoted
                    quoted_row = [row[0]] + [f'"{field}"' for field in row[1:]]
                    f.write(','.join(quoted_row) + '\n')

    print(f"Reformatted dates in {input_file} -> {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 reformat_dates.py <input_file> [output_file]")
        print("If output_file is not specified, input_file will be overwritten.")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) == 3 else None

    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist")
        sys.exit(1)

    reformat_dates(input_file, output_file)