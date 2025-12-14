from typing import Any, Dict
import pandas as pd


def get_columns_stats(col: str, series: pd.Series) -> Dict[str, Any]:
    """
    Calculates fundamental statistics (nulls, distinct count, min/max) for a single column.
    
    Args:
        col: The name of the column.
        series: The pandas Series (column data) to analyze.
        
    Returns:
        A dictionary containing the column's profile statistics.
    """
    dtype = str(series.dtype)

    null_count = int(series.isna().sum())
    # Note: Use an explicit check for division by zero to prevent error on empty series
    null_ratio = float(null_count / len(series)) if len(series) > 0 else 0.0
    distinct_count = int(series.nunique(dropna=True))

    col_info = {
        "name": col,
        "dtype": dtype,
        "null_count": null_count,
        "null_ratio": null_ratio,
        "distinct_count": distinct_count,
    }

    if pd.api.types.is_numeric_dtype(series):
        # Use series.notna().any() to ensure min/max is only called on series with data
        if series.notna().any():
            col_info["min"] = float(series.min(skipna=True))
            col_info["max"] = float(series.max(skipna=True))
        else:
             col_info["min"] = None
             col_info["max"] = None


    return col_info


def run_basic_checks(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs basic data profiling checks (row count, duplicates, null ratios).
    
    Args:
        df: The input pandas DataFrame.
        
    Returns:
        A dictionary containing the full data profile and a list of issues found.
    """
    row_count = int(len(df))
    duplicate_rows = int(df.duplicated().sum())
    # Explicitly convert dtypes to strings for JSON serialization compatibility
    schema = {col: str(df[col].dtype) for col in df.columns}
    columns = [get_columns_stats(col, df[col]) for col in df.columns]
    issues = list()
    
    # Basic warning: Duplicate rows
    if duplicate_rows > 0:
        issues.append(
            {
                "severity": "warning",
                "type": "duplicate_rows",
                "message": f"There are {duplicate_rows} duplicate rows.",
            }
        )

    # Basic warning: High null ratio (over 30%)
    for col_info in columns:
        col = col_info["name"]
        null_ratio = col_info["null_ratio"]

        if null_ratio > 0.3:
            issues.append(
                {
                    "severity": "warning",
                    "type": "high_null_ratio",
                    "column": col,
                    "message": f"Column '{col}' has {null_ratio:.0%} missing values.",
                }
            )

    profile: Dict[str, Any] = {
        "row_count": row_count,
        "duplicate_rows": duplicate_rows,
        "schema": schema,
        "columns": columns,
        "issues": issues
    }

    return profile