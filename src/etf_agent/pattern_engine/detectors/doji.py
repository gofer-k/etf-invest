import pandas as pd

def detect_doji(data: pd.DataFrame, threshold: float = 0.001) -> pd.Series:
    """
    Detect Doji candlestick patterns in the given DataFrame.

    A Doji is identified when the opening and closing prices are very close to each other,
    indicating indecision in the market. This function adds a new column 'Doji' to the DataFrame,
    where a value of 1 indicates the presence of a Doji pattern, and 0 indicates its absence.

    Parameters:
    data (pd.DataFrame): DataFrame containing at least 'Open' and 'Close' price columns.

    Returns:
    pd.DataFrame: DataFrame with an additional 'Doji' column.
    """
    
    # Calculate the absolute difference between Open and Close prices
    body = (data['Close'] - data['Open']).abs()
    average_range = (data['High'] - data['Low']).rolling(window=14).mean()

    return body < (average_range * threshold)