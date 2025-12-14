import polars as pl
from typing import Any, Dict


def get_columns_stats(col: str, series: pl.Series, top_n: int=5) -> Dict[str, Any]:
    """
    Calculates fundamental statistics (nulls, distinct count, min/max, top values) 
    for a single column using Polars.
    
    Args:
        col: The name of the column.
        series: The Polars Series (column data) to analyze.
        
    Returns:
        A dictionary containing the column's profile statistics and sample data.
    """
    dtype_str = str(series.dtype)
    # Standard column checking
    null_count = series.null_count()
    row_count = len(series)
    null_ratio = float(null_count / row_count) if row_count > 0 else 0.0
    distinct_count = series.n_unique()
    # Show the top N value for exploration and provide type checking context for LLM
    if row_count > 0 and distinct_count > 0:
        value_counts = (
            series.value_counts(sort=True, name="count")
            .head(top_n)
            .to_dicts()
        )
        # Format the top values for the prompt (e.g., ["value1 (20)", "value2 (15)"])
        top_values_list = [f"{item[col]} ({item['count']})" for item in value_counts]
    else:
        top_values_list = []
    
    col_info = {
        "name": col,
        "dtype": dtype_str,
        "null_count": null_count,
        "null_ratio": null_ratio,
        "distinct_count": distinct_count,
        "top_values_sample": top_values_list,
    }

    # Calculate min max value for numerical value
    if series.dtype.is_numeric():
        if null_count < row_count:
            col_info["min"] = series.min()
            col_info["max"] = series.max()
        else:
             col_info["min"] = None
             col_info["max"] = None

    return col_info


def run_basic_checks(df: pl.DataFrame) -> Dict[str, Any]:
    """
    Runs basic data profiling checks (row count, duplicates, null ratios) using Polars.
    
    Args:
        df: The input Polars DataFrame.
        
    Returns:
        A dictionary containing the full data profile and a list of issues found.
    """
    row_count = len(df)
    
    # Calculate duplicate rows
    duplicate_rows = df.filter(df.is_duplicated()).height
    
    # Extract schema
    schema = {col: str(df.dtypes[i]) for i, col in enumerate(df.columns)}
    
    # Calculate stats for all columns
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