#!/usr/bin/env python3
"""
Script to reverse CSV data, remove the last line, and save to target file.
Handles CSV files with proper parsing to avoid syntax errors.
"""

import sys
import os
import csv

def reverse_csv(input_file, target_file):
    # Read all rows from input CSV
    with open(input_file, 'r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # remove the header (the first row of file)
    rows.remove(rows[0])
      # Reverse the rows
    reversed_rows = rows[::-1]


  
    # Write to target CSV (append mode)    
    with open(target_file, 'a', newline='') as f:
        for i, row in enumerate(reversed_rows):
            if row:
                if i == 0:  # Header row, no quotes
                    f.write(','.join(row) + '\n')
                else:  # Data rows, first column unquoted, others quoted
                    quoted_row = [row[0]] + [f'"{field}"' for field in row[1:]]
                    f.write(','.join(quoted_row) + '\n')


    print(f"Processed {input_file} -> {target_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 reverse_csv.py <input_file> <target_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    target_file = sys.argv[2]

    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist")
        sys.exit(1)

    reverse_csv(input_file, target_file)