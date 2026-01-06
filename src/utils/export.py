import pandas as pd
import gzip
import json

def export_report_to_json(df: pd.DataFrame, filename: str = "report_data.json"):
    """
    Export the full stock analysis DataFrame to a JSON file.

    Parameters:
    - df: pandas DataFrame containing Close, Volume, Bollinger Bands, RSI, MACD, etc.
    - filename: output filename (default: 'report_data.json')
    """
    try:
        df_to_export = df.copy()
        df_to_export.index = df_to_export.index.strftime('%Y-%m-%d')  # Convert datetime index to string
        df_to_export.to_json(filename, orient="index", indent=2)
        print(f"[INFO] Report data exported to {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to export report: {e}")


def export_compressed_json(df: pd.DataFrame, filename: str = "report_data.json.gz"):
    """
    Export a DataFrame to a compressed JSON (.json.gz) file.

    Parameters:
    - df: pandas DataFrame to export
    - filename: output filename (default: 'report_data.json.gz')
    """
    try:
        df_to_export = df.copy()
        df_to_export.index = df_to_export.index.strftime('%Y-%m-%d')  # Convert datetime index to string
        json_data = df_to_export.to_dict(orient="index")

        with gzip.open(filename, "wt", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        print(f"[INFO] Compressed JSON saved to {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to export compressed JSON: {e}")
