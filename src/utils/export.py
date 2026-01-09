import pandas as pd
import gzip
import json
import re

def export_report_to_json(df: pd.DataFrame, filename: str = "report_data.json"):
    """
    Export the full stock analysis DataFrame to a JSON file.

    Parameters:
    - df: pandas DataFrame containing Close, Volume, Bollinger Bands, RSI, MACD, etc.
    - filename: output filename (default: 'report_data.json')
    """
    try:
        # df_to_export = df.copy()
        # df_to_export.index = df_to_export.index.strftime('%Y-%m-%d')  # Convert datetime index to string
        # json_text = df_to_export.to_json(orient="index", indent=2)
        json_text = df_to_json(df)
        with open(filename, "w", encoding="utf-8") as f: f.write(json_text)        
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
        df = df.where(pd.notnull(df), None) # convert NaN -> None
        json_data = df_to_export.to_dict(orient="index")
        with gzip.open(filename, "wt", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        print(f"[INFO] Compressed JSON saved to {filename}")
        return filename
    except Exception as e:
        print(f"[ERROR] Failed to export compressed JSON: {e}")
        return None

def collect_group_array_from_row_modified(row, prefix, expected_fields=None):
    """
    Collect groups for arrays where columns use mixed conventions:
      - prefix_index_field  (e.g., SMA_0)
      - fieldNameIndex       (e.g., SMA_BB_upper0, SMA_rolling_std0)
      - prefixIndex or prefixIndex_field (e.g., EMA0 or EMA0_value)
    Returns an ordered list of dicts (one dict per index) or [] if none found.
    """
    expected_fields = expected_fields or []
    groups = {}

    # Pattern A: prefix_index_field  -> captures index and field
    pat_a = re.compile(rf'^{re.escape(prefix)}_(\d+)_(.+)$')

    # Pattern B: fieldNameIndex  -> captures field and index (e.g., BB_upper0)
    pat_b = re.compile(r'^(.+?)(\d+)$')

    # Pattern C: prefixIndex(_field)? -> captures index and optional field (e.g., EMA0 or EMA0_value)
    pat_c = re.compile(rf'^{re.escape(prefix)}(\d+)(?:_(.+))?$')

    for col in row.index:
        val = row[col]
        m = pat_a.match(col)
        if m:
            idx = int(m.group(1))
            field = m.group(2)
            groups.setdefault(idx, {})[field] = val
            continue
        m = pat_c.match(col)
        if m:
            idx = int(m.group(1))
            field = m.group(2) or None
            if field:
                groups.setdefault(idx, {})[field] = val
            else:
                # column like 'EMA0' — treat as 'value' if expected_fields contains 'value', else store under prefix
                if 'value' in expected_fields:
                    groups.setdefault(idx, {})['value'] = val
                else:
                    groups.setdefault(idx, {})[prefix] = val
            continue
        # Pattern B: fieldNameIndex (only accept if fieldName is in expected_fields or looks like BB_*)
        m = pat_b.match(col)
        if m:
            field = m.group(1)
            idx = int(m.group(2))
            # Only accept these if field looks like a group field (heuristic)
            if expected_fields and field in expected_fields:
                groups.setdefault(idx, {})[field] = val
            else:
                # Accept common BB/rolling names even if not in expected_fields
                if re.match(r'^(rolling_std|BB_upper|BB_lower|BB_width|BB_percent|value)$', field):
                    groups.setdefault(idx, {})[field] = val

    if not groups:
        return []

    # Ensure each group contains expected fields (if provided) and convert NaN -> None
    result = []
    for idx in sorted(groups.keys()):
        g = groups[idx]
        # normalize keys: convert pandas NaN to None
        normalized = {k: (None if (pd.isna(v) if not isinstance(v, (list, dict)) else False) else v) for k, v in g.items()}
        # fill missing expected fields with None
        for ef in expected_fields:
            if ef not in normalized:
                normalized[ef] = None
        result.append(normalized)
    return result

def df_to_json(df, date_col='Date'):
    df_to_export = df.copy()
    df_to_export.index = df_to_export.index.strftime('%Y-%m-%d') 
    # df_to_export[date_col] = pd.to_datetime(df_to_export[date_col]).dt.strftime('%Y-%m-%d')
    df_to_export = df_to_export.where(pd.notnull(df_to_export), None)

    out = {"respond": {}}
    for idx, row in df_to_export.iterrows():
      # idx is a Timestamp (or string); format to YYYY-MM-DD
      if pd.isna(idx): continue # skip rows with invalid index date_str = idx.strftime('%Y-%m-%d')
      
      metadata = {
          "Open": row.get("Open"),
          "High": row.get("High"),
          "Low": row.get("Low"),
          "Close": row.get("Close"),
          "Volume": row.get("Volume"),
          "return": row.get("return")
      }

      # expected fields for each group type (helps the collector normalize missing keys)
      sma_fields = ["window", "rolling_std", "BB_upper", "BB_lower", "BB_width", "BB_percent", "value"]
      ema_fields = ["window", "value"]
      
      indicators = {
        "rolling_mean": row.get("rolling_mean"),
        "rolling_std": row.get("rolling_std"),
        "volatility": row.get("volatility"),
        "max_drawdown": row.get("max_drawdown"),
        "price_above_ma": row.get("price_above_ma"),
        "SMA": collect_group_array_from_row_modified(row, "SMA", expected_fields=sma_fields),
        "golden_cross": row.get("golden_cross"),
        "death_cross": row.get("death_cross"),
        "EMA": collect_group_array_from_row_modified(row, "EMA", expected_fields=ema_fields),
        "MACD_12_26": {
            "value": df_to_export["MACD_12_26"].loc[idx],
            "signal": df_to_export["MACD_signal_12_26"].loc[idx],
            "hist": df_to_export["MACD_hist_12_26"].loc[idx]
        },
        "MACD_50_200": {
          "value": df_to_export["MACD_50_200"].loc[idx],
          "signal": df_to_export["MACD_signal_50_200"].loc[idx],
          "hist": df_to_export["MACD_hist_50_200"].loc[idx]
        },
        "RSI": row.get("RSI")
      }

      # If you prefer null instead of empty arrays, change [] -> None here
      for k in ["SMA", "EMA"]:
          if indicators[k] == []:
              indicators[k] = []

      candlestick = {}
      for pattern in ["hammer","inverted_hammer","shooting_star","engulfing","morning_star","harami"]:
        candlestick[pattern] = {
            "price": row.get(f"{pattern}_price"),
            "strength": row.get(f"{pattern}_strength")
        }

      out["respond"][idx] = {"metadata": metadata, "indicators": indicators, "candlestick": candlestick}

    return json.dumps(out, indent=2, ensure_ascii=False)


