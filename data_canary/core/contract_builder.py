"""Contract builder logic for creating metadata contracts and applying schema transformations.

This module handles the core logic for building metadata contracts from data profiling
results and user overrides, then applying those contracts to transform data and generate
outputs (Parquet files and metadata.json contracts).
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import polars as pl

from data_canary.schemas.data_models import (
    PhysicalColumn,
    MetadataContract,
    NamingCheckReport,
    TypeCheckReport,
    LLMUsage,
    ColumnRole,
)


def build_physical_schema(
    columns: List[Dict[str, Any]],
    naming_report: Optional[NamingCheckReport] = None,
    type_report: Optional[TypeCheckReport] = None,
    user_overrides: Optional[Dict[str, Dict[str, str]]] = None,
) -> List[PhysicalColumn]:
    """Builds a list of PhysicalColumn definitions from profiling data and user overrides.

    Creates a PhysicalColumn for each column in the dataset, incorporating AI suggestions
    from naming and type checks, and applying any user-provided overrides. Preserves the
    original column order using column_index.

    Args:
        columns: List of column statistics from basic profiling (name, dtype, nulls, etc.)
        naming_report: AI naming suggestions (optional)
        type_report: AI type optimization suggestions (optional)
        user_overrides: User-provided overrides for column names and types (optional).
                       Format: {"column_name": {"name": "new_name", "type": "new_type"}}

    Returns:
        List of PhysicalColumn objects ready for contract assembly

    Raises:
        ValueError: If column data is malformed or missing required fields

    Example:
        # With AI suggestions and user overrides
        physical_columns = build_physical_schema(
            columns=[
                {"name": "User ID", "dtype": "Int64", "null_count_pct": 0.0},
                {"name": "RevenueUSD", "dtype": "Float64", "null_count_pct": 0.05}
            ],
            naming_report=naming_check_report,
            type_report=type_check_report,
            user_overrides={
                "RevenueUSD": {"name": "revenue_usd", "type": "Decimal(10,2)"}
            }
        )
    """
    if not columns:
        raise ValueError("Columns list cannot be empty")

    physical_columns = []
    naming_suggestions = {}
    type_suggestions = {}

    # Build lookup maps for AI suggestions
    if naming_report and naming_report.violations:
        for violation in naming_report.violations:
            naming_suggestions[violation.column_name] = violation.suggested_name

    if type_report and type_report.suggestions:
        for suggestion in type_report.suggestions:
            type_suggestions[suggestion.column_name] = suggestion.suggested_polars_type

    # Process each column
    for idx, col_data in enumerate(columns):
        col_name = col_data.get("name")
        if not col_name:
            raise ValueError(f"Column at index {idx} missing required 'name' field")

        # Get AI suggestions
        ai_suggested_name = naming_suggestions.get(col_name)
        ai_suggested_type = type_suggestions.get(col_name)

        # Get user overrides
        user_override = user_overrides.get(col_name) if user_overrides else None
        user_override_name = user_override.get("name") if user_override else None
        user_override_type = user_override.get("type") if user_override else None

        # Determine final target values (user override takes precedence over AI)
        target_name = user_override_name or ai_suggested_name or col_name
        target_type = user_override_type or ai_suggested_type or col_data.get("dtype", "String")

        # Include semantic role if provided in column data
        role = col_data.get("role")  # Could be provided by future column role detection

        physical_column = PhysicalColumn(
            source_name=col_name,  # Original name from source file
            target_name=target_name,  # Final name after overrides (default to source)
            data_type=target_type,  # Final data type after overrides
            is_nullable=col_data.get("null_count_pct", 100) > 0,  # Nullable if any nulls
            role=role,
            ai_suggested_name=ai_suggested_name,
            user_override_name=user_override_name,
            ai_suggested_type=ai_suggested_type,
            user_override_type=user_override_type,
            column_index=idx,  # Preserve original order
        )
        physical_columns.append(physical_column)

    return physical_columns


def _get_polars_dtype(dtype_str: str):
    """Convert string representation to Polars dtype object.

    Maps common string representations (e.g., 'Int64', 'Float64', 'String') to their
    corresponding Polars dtype objects for use in casting operations.

    Args:
        dtype_str: String representation of the Polars data type

    Returns:
        Polars dtype object

    Raises:
        ValueError: If dtype_str is not recognized

    Example:
        dtype = _get_polars_dtype("Int64")
        # Returns: pl.Int64
    """
    # Dictionary mapping string types to Polars dtype objects
    dtype_map = {
        # Integer types
        "Int8": pl.Int8,
        "Int16": pl.Int16,
        "Int32": pl.Int32,
        "Int64": pl.Int64,
        "UInt8": pl.UInt8,
        "UInt16": pl.UInt16,
        "UInt32": pl.UInt32,
        "UInt64": pl.UInt64,
        # Float types
        "Float32": pl.Float32,
        "Float64": pl.Float64,
        # String and binary
        "String": pl.Utf8,  # Polars uses Utf8 for strings
        "Utf8": pl.Utf8,
        "Binary": pl.Binary,
        # Boolean
        "Boolean": pl.Boolean,
        "Bool": pl.Boolean,
        # Date and time
        "Date": pl.Date,
        "Datetime": pl.Datetime,
        "Time": pl.Time,
        # Other common types
        "Categorical": pl.Categorical,
        "Object": pl.Object,
    }

    if dtype_str in dtype_map:
        return dtype_map[dtype_str]

    # Handle Decimal with precision/scale (e.g., "Decimal(10,2)")
    if dtype_str.startswith("Decimal"):
        try:
            import re

            match = re.match(r"Decimal\((\d+),\s*(\d+)\)", dtype_str)
            if match:
                precision = int(match.group(1))
                scale = int(match.group(2))
                return pl.Decimal(precision, scale)
            else:
                # Default Decimal if parsing fails
                return pl.Decimal
        except Exception:
            return pl.Decimal

    # Unknown type - default to String/Utf8
    return pl.Utf8


def apply_schema_transform(
    df: pl.DataFrame, physical_schema: List[PhysicalColumn]
) -> Tuple[pl.DataFrame, List[Dict[str, Any]]]:
    """Applies the physical schema to transform the DataFrame.

    Performs two transformations:
    1. Renames columns to target names from physical schema
    2. Casts columns to target data types when specified

    Args:
        df: The original Polars DataFrame
        physical_schema: List of PhysicalColumn definitions with target names/types

    Returns:
        Tuple of (transformed_df, transformation_log)
        transformation_log contains details of what was changed

    Raises:
        ValueError: If schema cannot be applied (e.g., type cast fails)

    Example:
        transformed_df, log = apply_schema_transform(df, physical_columns)
        # transformed_df has renamed and type-cast columns
        # log contains details of changes applied
    """
    if df is None or df.is_empty():
        raise ValueError("DataFrame cannot be None or empty")

    if not physical_schema:
        raise ValueError("Physical schema cannot be empty")

    df_transformed = df.clone()
    transformation_log: List[Dict[str, Any]] = []

    for physical_col in physical_schema:
        col_name = physical_col.source_name
        target_name = physical_col.target_name
        target_type = physical_col.data_type

        # Build transformation record
        transform_record: Dict[str, Any] = {
            "column": col_name,
            "target_name": target_name,
            "target_type": target_type,
            "actions": [],  # type: ignore
        }

        # Check if column exists
        if col_name not in df_transformed.columns:
            transform_record["actions"].append(  # type: ignore
                f"SKIP: Column '{col_name}' not found in DataFrame"
            )
            transformation_log.append(transform_record)
            continue

        # Rename column if name differs
        if col_name != target_name:
            df_transformed = df_transformed.rename({col_name: target_name})
            transform_record["actions"].append(f"RENAME: {col_name} -> {target_name}")  # type: ignore

        # Cast to target type if different from current
        try:
            current_type = str(df_transformed.schema[target_name])
            if current_type != target_type:
                # Get Polars dtype object
                target_dtype = _get_polars_dtype(target_type)

                # Apply the cast
                df_transformed = df_transformed.with_columns(pl.col(target_name).cast(target_dtype))
                transform_record["actions"].append(f"CAST: {current_type} -> {target_type}")  # type: ignore
        except Exception as e:
            transform_record["actions"].append(f"CAST_ERROR: Failed to cast to {target_type}: {e}")  # type: ignore

        if not transform_record["actions"]:  # type: ignore
            transform_record["actions"].append("NO_CHANGE: No transformations applied")  # type: ignore

        transformation_log.append(transform_record)

    return df_transformed, transformation_log
    # Dictionary mapping string types to Polars dtype objects
    dtype_map = {
        # Integer types
        "Int8": pl.Int8,
        "Int16": pl.Int16,
        "Int32": pl.Int32,
        "Int64": pl.Int64,
        "UInt8": pl.UInt8,
        "UInt16": pl.UInt16,
        "UInt32": pl.UInt32,
        "UInt64": pl.UInt64,
        # Float types
        "Float32": pl.Float32,
        "Float64": pl.Float64,
        # String and binary
        "String": pl.Utf8,  # Polars uses Utf8 for strings
        "Utf8": pl.Utf8,
        "Binary": pl.Binary,
        # Boolean
        "Boolean": pl.Boolean,
        "Bool": pl.Boolean,
        # Date and time
        "Date": pl.Date,
        "Datetime": pl.Datetime,
        "Time": pl.Time,
        # Other common types
        "Categorical": pl.Categorical,
        "Object": pl.Object,
    }

    if dtype_str in dtype_map:
        return dtype_map[dtype_str]

    # Handle Decimal with precision/scale (e.g., "Decimal(10,2)")
    if dtype_str.startswith("Decimal"):
        try:
            import re

            match = re.match(r"Decimal\((\d+),\s*(\d+)\)", dtype_str)
            if match:
                precision = int(match.group(1))
                scale = int(match.group(2))
                return pl.Decimal(precision, scale)
            else:
                # Default Decimal if parsing fails
                return pl.Decimal
        except Exception:
            return pl.Decimal

    # Unknown type - default to String/Utf8
    return pl.Utf8


def apply_schema_transform(
    df: pl.DataFrame, physical_schema: List[PhysicalColumn]
) -> Tuple[pl.DataFrame, List[Dict[str, Any]]]:
    """Applies the physical schema to transform the DataFrame.

    Performs two transformations:
    1. Renames columns to target names from physical schema
    2. Casts columns to target data types when specified

    Args:
        df: The original Polars DataFrame
        physical_schema: List of PhysicalColumn definitions with target names/types

    Returns:
        Tuple of (transformed_df, transformation_log)
        transformation_log contains details of what was changed

    Raises:
        ValueError: If schema cannot be applied (e.g., type cast fails)

    Example:
        transformed_df, log = apply_schema_transform(df, physical_columns)
        # transformed_df has renamed and type-cast columns
        # log contains details of changes applied
    """
    if df is None or df.is_empty():
        raise ValueError("DataFrame cannot be None or empty")

    if not physical_schema:
        raise ValueError("Physical schema cannot be empty")

    df_transformed = df.clone()
    transformation_log = []

    for physical_col in physical_schema:
        col_name = physical_col.source_name
        target_name = physical_col.target_name
        target_type = physical_col.data_type

        # Build transformation record
        transform_record = {
            "column": col_name,
            "target_name": target_name,
            "target_type": target_type,
            "actions": [],
        }

        # Check if column exists
        if col_name not in df_transformed.columns:
            transform_record["actions"].append(f"SKIP: Column '{col_name}' not found in DataFrame")
            transformation_log.append(transform_record)
            continue

        # Rename column if name differs
        if col_name != target_name:
            df_transformed = df_transformed.rename({col_name: target_name})
            transform_record["actions"].append(f"RENAME: {col_name} -> {target_name}")

        # Cast to target type if different from current
        try:
            current_type = str(df_transformed.schema[target_name])
            if current_type != target_type:
                # Get Polars dtype object
                target_dtype = _get_polars_dtype(target_type)

                # Apply the cast
                df_transformed = df_transformed.with_columns(pl.col(target_name).cast(target_dtype))
                transform_record["actions"].append(f"CAST: {current_type} -> {target_type}")
        except Exception as e:
            transform_record["actions"].append(f"CAST_ERROR: Failed to cast to {target_type}: {e}")

        if not transform_record["actions"]:
            transform_record["actions"].append("NO_CHANGE: No transformations applied")

        transformation_log.append(transform_record)

    return df_transformed, transformation_log


def create_metadata_contract(
    table_name: str,
    version: str,
    source_path: str,
    target_path: str,
    physical_schema: List[PhysicalColumn],
    statistical_profile: Dict[str, Any],
    created_by: str,
    llm_usage: Optional[LLMUsage] = None,
    column_roles: Optional[List[ColumnRole]] = None,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> MetadataContract:
    """Creates a complete metadata contract from all components.

    Assembles the complete metadata contract that serves as the "single source of truth"
    for a dataset, including identity, physical schema, statistical profile, and optional
    tracking information.

    Args:
        table_name: Human-readable table name
        version: Semantic version (e.g., "1.0.0")
        source_path: Path to original source file
        target_path: Path where Parquet output will be saved
        physical_schema: List of PhysicalColumn definitions
        statistical_profile: Statistical baseline from profiling
        created_by: Email or identifier of person who approved the contract
        llm_usage: Optional LLM usage tracking
        column_roles: Optional custom column roles
        additional_metadata: Optional extra metadata to include

    Returns:
        Complete MetadataContract object ready for serialization

    Example:
        contract = create_metadata_contract(
            table_name="user_events_2025",
            version="1.0.0",
            source_path="/data/raw/events.csv",
            target_path="/data/processed/user_events_2025.parquet",
            physical_schema=physical_columns,
            statistical_profile=profile,
            created_by="data-engineer@company.com",
            llm_usage=llm_usage,
            column_roles=custom_roles
        )
    """
    # Build identity section
    identity = {
        "table_name": table_name,
        "version": version,
        "created_at": datetime.utcnow().isoformat(),  # ISO 8601 format
        "source_path": source_path,
        "target_path": target_path,
        "created_by": created_by,
    }

    # Add any additional metadata to identity
    if additional_metadata:
        identity.update(additional_metadata)

    return MetadataContract(
        identity=identity,
        physical_schema=physical_schema,
        statistical_profile=statistical_profile,
        llm_usage=llm_usage,
        column_roles=column_roles,
    )


def validate_contract(contract: MetadataContract) -> Tuple[bool, List[str]]:
    """Validates a metadata contract for correctness and completeness.

    Checks for common issues:
    - Duplicate target column names
    - Missing required fields
    - Target names that are not valid identifiers
    - Data types that are not valid Polars types

    Args:
        contract: The MetadataContract to validate

    Returns:
        Tuple of (is_valid, list_of_issues) where is_valid is True if no issues found

    Example:
        is_valid, issues = validate_contract(contract)
        if not is_valid:
            for issue in issues:
                print(f"Validation issue: {issue}")
    """
    issues = []
    target_names = []

    # Check physical schema
    if not contract.physical_schema:
        issues.append("Physical schema is empty")
        return False, issues

    for idx, col in enumerate(contract.physical_schema):
        # Check required fields
        if not col.source_name:
            issues.append(f"Column {idx} missing source_name")
        if not col.target_name:
            issues.append(f"Column {idx} missing target_name")
        if not col.data_type:
            issues.append(f"Column {idx} missing data_type")

        # Track target names for duplicate check
        if col.target_name:
            target_names.append(col.target_name)

        # Validate column index is sequential (no gaps)
        if col.column_index != idx:
            issues.append(
                f"Column {col.source_name} has non-sequential index: {col.column_index} != {idx}"
            )

    # Check for duplicate target names
    duplicates = [name for name in target_names if target_names.count(name) > 1]
    if duplicates:
        issues.append(f"Duplicate target names found: {set(duplicates)}")

    # Check identity section has required fields
    required_identity = ["table_name", "version", "created_at", "source_path", "target_path"]
    for field in required_identity:
        if field not in contract.identity or not contract.identity.get(field):
            issues.append(f"Identity missing required field: {field}")

    # Check statistical profile
    if not contract.statistical_profile:
        issues.append("Statistical profile is empty")

    is_valid = len(issues) == 0
    return is_valid, issues
