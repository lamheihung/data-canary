from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


class NamingViolation(BaseModel):
    """Details for a single column that violates naming conventions.

    Attributes:
        column_name: The name of the column that violates conventions.
        violation_reason: A clear, concise reason why the column name is poor or violates convention.
        suggested_name: The recommended name for the column following best practices (e.g., snake_case).
    """

    column_name: str = Field(description="The name of the column that violates conventions.")
    violation_reason: str = Field(
        description="A clear, concise reason why the column name is poor or violates convention."
    )
    suggested_name: str = Field(
        description="The recommended name for the column following best practices (e.g., snake_case)."
    )


class NamingCheckReport(BaseModel):
    """The complete report of naming convention violations across a dataset.

    Attributes:
        summary: A brief, encouraging summary of the naming check results, including the total number of violations found.
        violations: A list of specific naming violations found in the dataset's columns.
    """

    summary: str = Field(
        description="A brief, encouraging summary of the naming check results, including the total number of violations found."
    )
    violations: List[NamingViolation] = Field(
        description="A list of specific naming violations found in the dataset's columns."
    )


class TypeSuggestion(BaseModel):
    """Details for a single column's type suggestion.

    Attributes:
        column_name: The name of the column being analyzed.
        current_dtype: The current data type as inferred by Polars (e.g., 'Int8', 'Float64').
        suggested_logical_type: The suggested, precise logical data type (e.g., 'UUID', 'ISO_DATE', 'CURRENCY_USD', 'CATEGORY').
        suggested_polars_type: The suggested Python/Polars dtype for coersion (e.g., 'UInt64', 'Date').
        reasoning: The reasoning behind the type suggestion, based on column name or sample data.
    """

    column_name: str = Field(description="The name of the column being analyzed.")
    current_dtype: str = Field(
        description="The current data type as inferred by Polars (e.g., 'Int8', 'Float64')."
    )
    suggested_logical_type: str = Field(
        description="The suggested, precise logical data type (e.g., 'UUID', 'ISO_DATE', 'CURRENCY_USD', 'CATEGORY')."
    )
    suggested_polars_type: str = Field(
        description="The suggested Python/Polars dtype for coersion (e.g., 'UInt64', 'Date')."
    )
    reasoning: str = Field(
        description="The reasoning behind the type suggestion, based on column name or sample data."
    )


class TypeCheckReport(BaseModel):
    """The complete report of data type suggestions across a dataset.

    Attributes:
        summary: A brief summary of the type check results.
        suggestions: A list of specific type suggestions found in the dataset's columns.
    """

    summary: str = Field(description="A brief summary of the type check results.")
    suggestions: List[TypeSuggestion] = Field(
        description="A list of specific type suggestions found in the dataset's columns."
    )


class ColumnRole(BaseModel):
    """Custom column roles for storing vendor-provided metadata.

    Allows storing arbitrary metadata about columns to avoid checking data dictionaries
    repeatedly. Supports both predefined roles (PK, Metric, Event, Category) and
    custom roles for vendor-specific metadata.

    Attributes:
        column_name: Name of the column this role applies to.
        role_type: Type of role (e.g., PK, Metric, Event, Category, or custom vendor-specific).
        description: Optional description explaining the role or providing context.

    Example:
        ColumnRole(
            column_name="user_id",
            role_type="primary_key",
            description="Unique identifier from authentication system"
        )
    """

    column_name: str = Field(description="Name of the column this role applies to.")
    role_type: str = Field(
        description="Type of role (e.g., PK, Metric, Event, Category, or custom vendor-specific)."
    )
    description: Optional[str] = Field(
        default=None, description="Optional description explaining the role or providing context."
    )


class PhysicalColumn(BaseModel):
    """Physical schema definition for a single column with override tracking.

    Stores both the original source information and any user overrides, enabling
    complete traceability from raw data to transformed output. Preserves the
    source-to-target mapping for auditability.

    Attributes:
        source_name: Original column name from the source file.
        target_name: Final column name after user overrides (defaults to source_name).
        source_type: Original data type from the source file.
        target_type: Final data type after user overrides.
        is_nullable: Whether the column allows null values.
        role: Optional semantic role for the column (e.g., PK, Metric).
        ai_suggested_name: AI-suggested column name (if available).
        user_override_name: User-provided override for column name.
        ai_suggested_type: AI-suggested data type (if available).
        user_override_type: User-provided override for data type.
        column_index: Original column order index to maintain order.
    """

    source_name: str = Field(description="Original column name from the source file.")
    target_name: str = Field(
        description="Final column name after user overrides (defaults to source_name)."
    )
    source_type: str = Field(description="Original data type from the source file.")
    target_type: str = Field(description="Final data type after user overrides.")
    is_nullable: bool = Field(description="Whether the column allows null values.")
    role: Optional[str] = Field(
        default=None,
        description="Optional semantic role for the column (e.g., PK, Metric, Event, Category).",
    )
    ai_suggested_name: Optional[str] = Field(
        default=None, description="AI-suggested column name (if available)."
    )
    user_override_name: Optional[str] = Field(
        default=None, description="User-provided override for column name."
    )
    ai_suggested_type: Optional[str] = Field(
        default=None, description="AI-suggested data type (if available)."
    )
    user_override_type: Optional[str] = Field(
        default=None, description="User-provided override for data type."
    )
    column_index: int = Field(
        description="Original column order index to maintain source column order."
    )


class MetadataContract(BaseModel):
    """Complete metadata contract defining a dataset's schema and characteristics.

    Serves as the "single source of truth" for a dataset, containing everything
    needed to validate future data ingestions and track schema evolution. Inspired
    by software engineering's contract testing pattern applied to data engineering.

    The contract consists of three main components:
    1. Identity: Table metadata (name, version, paths, timestamps)
    2. Physical Schema: Column definitions with source-to-target mapping
    3. Statistical Profile: Baseline statistics for drift detection

    Attributes:
        identity: Table metadata including name, version, paths, and timestamps.
        physical_schema: List of column definitions with source-to-target mapping.
        statistical_profile: Baseline statistics for drift detection and quality monitoring.
        column_roles: Optional custom column roles for vendor-provided metadata.

    Example:
        contract = MetadataContract(
            identity={
                "table_name": "user_events",
                "version": "1.0.0",
                "created_at": "2026-01-10T10:30:00Z"
            },
            physical_schema=[
                PhysicalColumn(
                    source_name="User ID",
                    target_name="user_id",
                    data_type="UInt32",
                    is_nullable=False,
                    role="primary_key",
                    column_index=0
                )
            ],
            statistical_profile={
                "row_count": 10000,
                "columns": {"user_id": {"null_count_pct": 0.0, "cardinality": 10000}}
            }
        )
    """

    identity: Dict[str, Any] = Field(
        description="Table metadata including name, version, paths, and timestamps."
    )
    physical_schema: List[PhysicalColumn] = Field(
        description="List of column definitions with source-to-target mapping."
    )
    statistical_profile: Dict[str, Any] = Field(
        description="Baseline statistics for drift detection and quality monitoring."
    )
    column_roles: Optional[List[ColumnRole]] = Field(
        default=None,
        description="Optional custom column roles for vendor-provided metadata.",
    )

