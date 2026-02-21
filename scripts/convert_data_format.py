#!/usr/bin/env python3
"""
Script to change date format in CSV from dd/mm/YYYY to mm/dd/YYYY.

Python Date Format Codes:
    %Y - Year with century (e.g., 2024)
    %y - Year without century (e.g., 24)
    %m - Month as zero-padded decimal (01-12)
    %B - Full month name (e.g., January)
    %b - Abbreviated month name (e.g., Jan)
    %d - Day of the month as zero-padded decimal (01-31)
    %e - Day of the month as decimal number (1-31, space-padded)
    %H - Hour (24-hour) as zero-padded decimal (00-23)
    %I - Hour (12-hour) as zero-padded decimal (01-12)
    %M - Minute as zero-padded decimal (00-59)
    %S - Second as zero-padded decimal (00-59)
    %p - AM or PM
    %A - Full weekday name (e.g., Monday)
    %a - Abbreviated weekday name (e.g., Mon)

Examples:
    %d.%m.%Y  (e.g., 25.12.2024)
    %m/%d/%Y  (e.g., 12/25/2024)
    %d/%m/%Y  (e.g., 25/12/2024)
    %Y-%m-%d  (e.g., 2024-12-25)
    %m-%d-%y  (e.g., 12-25-24)
"""

import sys
import os
import csv
from datetime import datetime
    
def is_valid_date(date_string, format):
    try:
        datetime.strptime(date_string, format)
        return True
    except ValueError:
        return False
    
def to_DOHLCV_format(input_header):
    header_idx = {}

    if len(input_header) < 6:
        return False

    for i, item in enumerate(input_header):
        item_norm = item.strip().lower()
        if item_norm in ("data", "date"):
            header_idx[0] = i
        elif item_norm in ("otwarcie", "open"):
            header_idx[1] = i
        elif item_norm in ("max", "max.", "high"):
            header_idx[2] = i
        elif item_norm in ("min", "min.", "low"):
            header_idx[3] = i
        elif item_norm in ("ostatnio", "closed", "close", "last"):
            header_idx[4] = i
        elif item_norm in ("wol.", "wolumen", "volume"):
            header_idx[5] = i

    # Ensure we found all required columns: Date, Open, High, Low, Close, Volume
    required_keys = set(range(6))
    if not required_keys.issubset(set(header_idx.keys())):
        return False

    return header_idx
     
def convert_to_ohlcv(input_file, output_file=None, input_data=None):
    if output_file is None:
        output_file = input_file  # Overwrite if no output specified

    # Read all rows from input CSV (use utf-8-sig to strip BOM if present)
    with open(input_file, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Process each row
    column_mapping = to_DOHLCV_format(rows[0])
    if column_mapping is False:
        print("Error: Unrecognized header format")
        sys.exit(1)

    # Replace header with standardized DOHLCV names
    rows[0] = ["Date", "Open", "High", "Low", "Close", "Volume"]

    # Build new rows in DOHLCV order and format volume
    for i, row in enumerate(rows):
        if i == 0:
            continue

        new_row = []
        for k in range(6):
            src_idx = column_mapping.get(k)
            val = ''
            if src_idx is not None and src_idx < len(row):
                val = row[src_idx]
            new_row.append(val)

        # Format volume (index 5) with thousands separator if numeric
        try:
            v = new_row[5].replace(',', '').replace('"', '').strip()
            if v:
                # allow floats by converting to float then int if needed
                if '.' in v:
                    num = float(v)
                    # keep as-is if fractional, otherwise format as int
                    if num.is_integer():
                        new_row[5] = f"{int(num):,}"
                    else:
                        new_row[5] = f"{num:,.2f}"
                else:
                    new_row[5] = f"{int(v):,}"
        except Exception:
            pass

        rows[i] = new_row

    # Write to output CSV (skip quoting for header, quote all except first for data)
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        for i, row in enumerate(rows):
            if not row:
                continue
            if i == 0:  # Header row, no quotes
                f.write(','.join(row) + '\n')
            else:  # Data rows, first column unquoted, others quoted
                quoted_row = [row[0]] + [f'"{field}"' for field in row[1:]]
                f.write(','.join(quoted_row) + '\n')

    print(f"Reformatted dates in {input_file} -> {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 5:
        print("Usage: python3 convert_data_format.py <input_file> <output_file>")
        print("If output_file is not specified, input_file will be overwritten.")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) == 3 else None

    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist")
        sys.exit(1)

    convert_to_ohlcv(input_file, output_file)