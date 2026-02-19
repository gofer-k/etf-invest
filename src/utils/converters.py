def period_to_days(period: str) -> int:
    """Convert a period string to the number of days it represents."""
    if period.endswith('d'):
        return int(period[:-1])
    elif period.endswith('w'):
        return int(period[:-1]) * 7
    elif period.endswith('m'):
        return int(period[:-1]) * 30
    elif period.endswith('y'):
        return int(period[:-1]) * 365
    else:
        raise ValueError(f"Invalid period format: {period}")