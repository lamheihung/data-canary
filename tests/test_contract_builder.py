"""Unit tests for contract builder logic.

Tests cover schema transformation, physical schema building, contract creation,
and validation functionality for the human-in-the-loop workflow.
"""

import pytest

import polars as pl

from data_canary.core.contract_builder import (
    build_physical_schema,
    apply_schema_transform,
    create_metadata_contract,
    validate_contract,
)
from data_canary.schemas.data_models import (
    PhysicalColumn,
    MetadataContract,
    NamingViolation,
    NamingCheckReport,
    TypeSuggestion,
    TypeCheckReport,
    ColumnRole,
)


class TestBuildPhysicalSchema:
    """Tests for building physical schema from profiling data."""

    def test_build_physical_schema_basic(self):
        """Test building schema from basic column data only."""
        columns = [
            {"name": "user_id", "dtype": "Int64", "null_count_pct": 0.0},
            {"name": "amount", "dtype": "Float64", "null_count_pct": 5.2},
        ]

        physical_schema = build_physical_schema(columns)

        assert len(physical_schema) == 2
        assert physical_schema[0].source_name == "user_id"
        assert physical_schema[0].target_name == "user_id"  # No overrides
        assert physical_schema[0].target_type == "Int64"
        assert physical_schema[0].is_nullable is False
        assert physical_schema[1].column_index == 1

    def test_build_physical_schema_with_ai_naming(self):
        """Test building schema with AI naming suggestions."""
        columns = [
            {"name": "User ID", "dtype": "Int64", "null_count_pct": 0.0},
            {"name": "RevenueUSD", "dtype": "Float64", "null_count_pct": 0.0},
        ]

        naming_report = NamingCheckReport(
            summary="Found 2 naming issues",
            violations=[
                NamingViolation(
                    column_name="User ID",
                    violation_reason="Contains space",
                    suggested_name="user_id",
                ),
                NamingViolation(
                    column_name="RevenueUSD",
                    violation_reason="Not snake_case",
                    suggested_name="revenue_usd",
                ),
            ],
        )

        physical_schema = build_physical_schema(columns, naming_report=naming_report)

        assert physical_schema[0].ai_suggested_name == "user_id"
        assert physical_schema[0].target_name == "user_id"  # AI suggestion used
        assert physical_schema[1].ai_suggested_name == "revenue_usd"

    def test_build_physical_schema_with_ai_types(self):
        """Test building schema with AI type suggestions."""
        columns = [
            {"name": "user_id", "dtype": "Int64", "null_count_pct": 0.0},
            {"name": "amount", "dtype": "Float64", "null_count_pct": 0.0},
        ]

        type_report = TypeCheckReport(
            summary="Type optimizations suggested",
            suggestions=[
                TypeSuggestion(
                    column_name="user_id",
                    current_dtype="Int64",
                    suggested_logical_type="user_identifier",
                    suggested_polars_type="UInt32",
                    reasoning="IDs should be unsigned",
                ),
                TypeSuggestion(
                    column_name="amount",
                    current_dtype="Float64",
                    suggested_logical_type="currency",
                    suggested_polars_type="Decimal(10,2)",
                    reasoning="Currency needs precision",
                ),
            ],
        )

        physical_schema = build_physical_schema(columns, type_report=type_report)

        assert physical_schema[0].ai_suggested_type == "UInt32"
        assert physical_schema[0].target_type == "UInt32"  # AI suggestion used as default
        assert physical_schema[1].ai_suggested_type == "Decimal(10,2)"

    def test_build_physical_schema_with_user_overrides(self):
        """Test building schema with user overrides (takes precedence over AI)."""
        columns = [
            {"name": "User ID", "dtype": "Int64", "null_count_pct": 0.0},
            {"name": "Revenue", "dtype": "Float64", "null_count_pct": 0.0},
        ]

        naming_report = NamingCheckReport(
            summary="Found 2 naming issues",
            violations=[
                NamingViolation(
                    column_name="User ID",
                    violation_reason="Contains space",
                    suggested_name="user_id",
                ),
                NamingViolation(
                    column_name="Revenue",
                    violation_reason="Not snake_case",
                    suggested_name="revenue",
                ),
            ],
        )

        # User overrides AI suggestions
        user_overrides = {
            "User ID": {"name": "customer_id"},  # Override AI's "user_id"
            "Revenue": {"type": "Decimal(12,4)"},  # Override AI type suggestion
        }

        physical_schema = build_physical_schema(
            columns, naming_report=naming_report, user_overrides=user_overrides
        )

        # Check user override takes precedence for name
        assert physical_schema[0].ai_suggested_name == "user_id"
        assert physical_schema[0].user_override_name == "customer_id"
        assert physical_schema[0].target_name == "customer_id"  # User wins

        # Check default type when no AI or user type specified
        assert physical_schema[1].ai_suggested_type is None
        assert physical_schema[1].user_override_type == "Decimal(12,4)"
        assert physical_schema[1].target_type == "Decimal(12,4)"

    def test_build_physical_schema_with_roles(self):
        """Test building schema with column roles."""
        columns = [
            {"name": "user_id", "dtype": "Int64", "null_count_pct": 0.0, "role": "primary_key"},
            {
                "name": "event_timestamp",
                "dtype": "Datetime",
                "null_count_pct": 0.0,
                "role": "event_marker",
            },
            {"name": "amount", "dtype": "Float64", "null_count_pct": 0.0, "role": "metric"},
        ]

        physical_schema = build_physical_schema(columns)

        assert physical_schema[0].role == "primary_key"
        assert physical_schema[1].role == "event_marker"
        assert physical_schema[2].role == "metric"

    def test_build_physical_schema_error_empty_columns(self):
        """Test error handling for empty columns list."""
        with pytest.raises(ValueError, match="Columns list cannot be empty"):
            build_physical_schema([])

    def test_build_physical_schema_error_missing_name(self):
        """Test error handling for column without name."""
        columns = [{"dtype": "Int64", "null_count_pct": 0.0}]  # Missing 'name'

        with pytest.raises(ValueError, match="missing required 'name' field"):
            build_physical_schema(columns)

    def test_build_physical_schema_order_preservation(self):
        """Test that column_index preserves original order."""
        columns = [{"name": f"col_{i}", "dtype": "Int64", "null_count_pct": 0.0} for i in range(10)]

        physical_schema = build_physical_schema(columns)

        for i, col in enumerate(physical_schema):
            assert col.column_index == i
            assert col.source_name == f"col_{i}"


class TestApplySchemaTransform:
    """Tests for applying schema transformations to DataFrames."""

    def test_apply_schema_transform_rename_only(self):
        """Test applying only column renames."""
        df = pl.DataFrame(
            {
                "User ID": [1, 2, 3],
                "Sale Date": ["2025-01-01", "2025-01-02", "2025-01-03"],
            }
        )

        physical_schema = [
            PhysicalColumn(
                source_name="User ID",
                target_name="user_id",
                source_type="Int64",
                target_type="Int64",
                is_nullable=False,
                column_index=0,
            ),
            PhysicalColumn(
                source_name="Sale Date",
                target_name="sale_date",
                source_type="String",
                target_type="String",
                is_nullable=False,
                column_index=1,
            ),
        ]

        transformed_df, log = apply_schema_transform(df, physical_schema)

        # Check columns were renamed
        assert "user_id" in transformed_df.columns
        assert "sale_date" in transformed_df.columns
        assert "User ID" not in transformed_df.columns
        assert "Sale Date" not in transformed_df.columns

        # Check data preserved
        assert transformed_df["user_id"][0] == 1

        # Check log
        assert len(log) == 2
        assert "RENAME: User ID -> user_id" in log[0]["actions"]

    def test_apply_schema_transform_type_cast(self):
        """Test applying type casts to columns."""
        df = pl.DataFrame(
            {
                "user_id": ["1", "2", "3"],  # String column
                "amount": ["10.5", "20.3", "15.7"],  # String amounts
            }
        )

        physical_schema = [
            PhysicalColumn(
                source_name="user_id",
                target_name="user_id",
                source_type="Int64",  # Cast to Int64
                target_type="Int64",
                is_nullable=False,
                column_index=0,
            ),
            PhysicalColumn(
                source_name="amount",
                target_name="amount",
                source_type="Float64",  # Cast to Float64
                target_type="Float64",
                is_nullable=False,
                column_index=1,
            ),
        ]

        transformed_df, log = apply_schema_transform(df, physical_schema)

        # Check types were cast
        assert str(transformed_df.schema["user_id"]) == "Int64"
        assert str(transformed_df.schema["amount"]) == "Float64"

        # Check data converted correctly
        assert transformed_df["user_id"][0] == 1
        assert transformed_df["amount"][0] == 10.5

    def test_apply_schema_transform_combined(self):
        """Test applying both renames and type casts."""
        df = pl.DataFrame(
            {
                "User ID": ["100", "200", "300"],
                "RevenueUSD": ["999.99", "888.88", "777.77"],
            }
        )

        physical_schema = [
            PhysicalColumn(
                source_name="User ID",
                target_name="user_id",
                source_type="Int64",
                target_type="Int64",
                is_nullable=False,
                column_index=0,
            ),
            PhysicalColumn(
                source_name="RevenueUSD",
                target_name="revenue_usd",
                source_type="Float64",
                target_type="Float64",
                is_nullable=False,
                column_index=1,
            ),
        ]

        transformed_df, log = apply_schema_transform(df, physical_schema)

        # Check final state
        assert transformed_df.columns == ["user_id", "revenue_usd"]
        assert str(transformed_df.schema["user_id"]) == "Int64"
        assert str(transformed_df.schema["revenue_usd"]) == "Float64"
        assert transformed_df["user_id"][0] == 100
        assert transformed_df["revenue_usd"][0] == 999.99

    def test_apply_schema_transform_empty_df_error(self):
        """Test error handling for empty DataFrame."""
        df = pl.DataFrame({})  # Empty DataFrame

        with pytest.raises(ValueError, match="DataFrame cannot be None or empty"):
            apply_schema_transform(df, [])

    def test_apply_schema_transform_none_df_error(self):
        """Test error handling for None DataFrame."""
        with pytest.raises(ValueError, match="DataFrame cannot be None or empty"):
            apply_schema_transform(None, [])

    def test_apply_schema_transform_missing_column(self):
        """Test handling when physical schema column not in DataFrame."""
        df = pl.DataFrame({"col_a": [1, 2, 3]})  # col_b is missing

        physical_schema = [
            PhysicalColumn(
                source_name="col_a",
                target_name="new_a",
                source_type="Int64",
                target_type="Int64",
                is_nullable=False,
                column_index=0,
            ),
            PhysicalColumn(
                source_name="col_b",  # This column doesn't exist
                target_name="new_b",
                source_type="Int64",
                target_type="Int64",
                is_nullable=False,
                column_index=1,
            ),
        ]

        transformed_df, log = apply_schema_transform(df, physical_schema)

        # Check that existing column still transformed
        assert "new_a" in transformed_df.columns

        # Check that missing column was skipped
        skip_actions = [action for entry in log for action in entry["actions"]]
        assert any("SKIP: Column 'col_b' not found" in action for action in skip_actions)


class TestCreateMetadataContract:
    """Tests for creating complete metadata contracts."""

    def test_create_metadata_contract_basic(self):
        """Test creating a minimal metadata contract."""
        physical_schema = [
            PhysicalColumn(
                source_name="user_id",
                target_name="user_id",
                source_type="Int64",
                target_type="Int64",
                is_nullable=False,
                column_index=0,
            ),
            PhysicalColumn(
                source_name="amount",
                target_name="amount",
                source_type="Float64",
                target_type="Float64",
                is_nullable=True,
                column_index=1,
            ),
        ]

        statistical_profile = {
            "row_count": 1000,
            "columns": {
                "user_id": {"null_count_pct": 0.0, "cardinality": 1000},
                "amount": {"null_count_pct": 0.05, "min": 0.0, "max": 999.99},
            },
        }

        contract = create_metadata_contract(
            table_name="test_data",
            version="1.0.0",
            source_path="/input/test.csv",
            target_path="/output/test.parquet",
            physical_schema=physical_schema,
            statistical_profile=statistical_profile,
            created_by="test@example.com",
        )

        # Verify contract structure
        assert contract.identity["table_name"] == "test_data"
        assert contract.identity["version"] == "1.0.0"
        assert contract.identity["source_path"] == "/input/test.csv"
        assert len(contract.physical_schema) == 2
        assert contract.statistical_profile["row_count"] == 1000

    def test_create_metadata_contract_with_column_roles(self):
        """Test creating contract with custom column roles."""
        physical_schema = [
            PhysicalColumn(
                source_name="user_id",
                target_name="user_id",
                source_type="Int64",
                target_type="Int64",
                is_nullable=False,
                column_index=0,
            ),
        ]

        statistical_profile = {"row_count": 1, "columns": {"user_id": {"null_count_pct": 0.0}}}

        column_roles = [
            ColumnRole(
                column_name="user_id",
                role_type="primary_key",
                description="Unique identifier from vendor CRM",
            )
        ]

        contract = create_metadata_contract(
            table_name="test",
            version="1.0.0",
            source_path="/in.csv",
            target_path="/out.parquet",
            physical_schema=physical_schema,
            statistical_profile=statistical_profile,
            created_by="test@example.com",
            column_roles=column_roles,
        )

        assert contract.column_roles is not None
        assert len(contract.column_roles) == 1
        assert contract.column_roles[0].role_type == "primary_key"

    def test_create_metadata_contract_with_additional_metadata(self):
        """Test creating contract with extra metadata fields."""
        physical_schema = [
            PhysicalColumn(
                source_name="id",
                target_name="id",
                source_type="Int64",
                target_type="Int64",
                is_nullable=False,
                column_index=0,
            ),
        ]

        statistical_profile = {"row_count": 1, "columns": {"id": {"null_count_pct": 0.0}}}

        additional_metadata = {
            "environment": "production",
            "team": "data-engineering",
            "project_id": "proj-12345",
        }

        contract = create_metadata_contract(
            table_name="test",
            version="1.0.0",
            source_path="/in.csv",
            target_path="/out.parquet",
            physical_schema=physical_schema,
            statistical_profile=statistical_profile,
            created_by="test@example.com",
            additional_metadata=additional_metadata,
        )

        assert contract.identity["environment"] == "production"
        assert contract.identity["team"] == "data-engineering"
        assert contract.identity["project_id"] == "proj-12345"


class TestValidateContract:
    """Tests for contract validation."""

    def test_validate_contract_valid(self):
        """Test validating a correct contract."""
        contract = MetadataContract(
            identity={
                "table_name": "test",
                "version": "1.0.0",
                "created_at": "2026-01-10T12:00:00Z",
                "source_path": "/input.csv",
                "target_path": "/output.parquet",
            },
            physical_schema=[
                PhysicalColumn(
                    source_name="col_a",
                    target_name="col_a",
                    source_type="Int64",
                    target_type="Int64",
                    is_nullable=False,
                    column_index=0,
                ),
            ],
            statistical_profile={"row_count": 100},
        )

        is_valid, issues = validate_contract(contract)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_contract_empty_schema_error(self):
        """Test validation error for empty physical schema."""
        contract = MetadataContract(
            identity={"table_name": "test", "version": "1.0.0"},
            physical_schema=[],
            statistical_profile={},
        )

        is_valid, issues = validate_contract(contract)

        assert is_valid is False
        assert any("Physical schema is empty" in issue for issue in issues)

    def test_validate_contract_duplicate_target_names_error(self):
        """Test validation error for duplicate target names."""
        contract = MetadataContract(
            identity={"table_name": "test", "version": "1.0.0"},
            physical_schema=[
                PhysicalColumn(
                    source_name="col_a",
                    target_name="same_name",
                    source_type="Int64",
                    target_type="Int64",
                    is_nullable=False,
                    column_index=0,
                ),
                PhysicalColumn(
                    source_name="col_b",
                    target_name="same_name",
                    source_type="Int64",
                    target_type="Int64",
                    is_nullable=False,
                    column_index=1,
                ),
            ],
            statistical_profile={},
        )

        is_valid, issues = validate_contract(contract)

        assert is_valid is False
        assert any("Duplicate target names" in issue for issue in issues)

    def test_validate_contract_missing_identity_fields_error(self):
        """Test validation error for missing identity fields."""
        contract = MetadataContract(
            identity={"table_name": "test"},  # Missing version, paths
            physical_schema=[
                PhysicalColumn(
                    source_name="col",
                    target_name="col",
                    source_type="Int64",
                    target_type="Int64",
                    is_nullable=False,
                    column_index=0,
                ),
            ],
            statistical_profile={},
        )

        is_valid, issues = validate_contract(contract)

        assert is_valid is False
        assert any("Identity missing required field" in issue for issue in issues)

    def test_validate_contract_sequential_index_error(self):
        """Test validation error for non-sequential column indices."""
        contract = MetadataContract(
            identity={"table_name": "test", "version": "1.0.0"},
            physical_schema=[
                PhysicalColumn(
                    source_name="col_0",
                    target_name="col_0",
                    source_type="Int64",
                    target_type="Int64",
                    is_nullable=False,
                    column_index=0,
                ),
                PhysicalColumn(
                    source_name="col_1",
                    target_name="col_1",
                    source_type="Int64",
                    target_type="Int64",
                    is_nullable=False,
                    column_index=5,  # Gap!
                ),
            ],
            statistical_profile={},
        )

        is_valid, issues = validate_contract(contract)

        assert is_valid is False
        assert any("non-sequential index" in issue for issue in issues)


class TestIntegration:
    """Integration tests for complete workflow."""

    def test_full_workflow_with_overrides(self):
        """Test complete workflow: profile → AI suggestions → user overrides → transform → contract."""
        # Start with sample data
        df = pl.DataFrame(
            {
                "User ID": [1, 2, 3],
                "Transaction Date": ["2025-01-01", "2025-01-02", "2025-01-03"],
                "RevenueUSD": [100.5, 200.75, 150.0],
            }
        )

        # Simulate profiling results
        columns = [
            {"name": "User ID", "dtype": "Int64", "null_count_pct": 0.0},
            {"name": "Transaction Date", "dtype": "String", "null_count_pct": 0.0},
            {"name": "RevenueUSD", "dtype": "Float64", "null_count_pct": 0.0},
        ]

        # Simulate AI naming suggestions
        naming_report = NamingCheckReport(
            summary="Found 3 naming issues",
            violations=[
                NamingViolation(
                    column_name="User ID", violation_reason="space", suggested_name="user_id"
                ),
                NamingViolation(
                    column_name="Transaction Date",
                    violation_reason="space",
                    suggested_name="transaction_date",
                ),
                NamingViolation(
                    column_name="RevenueUSD", violation_reason="case", suggested_name="revenue_usd"
                ),
            ],
        )

        # Simulate AI type suggestions
        type_report = TypeCheckReport(
            summary="Type optimizations suggested",
            suggestions=[
                TypeSuggestion(
                    column_name="User ID",
                    current_dtype="Int64",
                    suggested_logical_type="user_id",
                    suggested_polars_type="UInt32",
                    reasoning="IDs should be unsigned",
                ),
                TypeSuggestion(
                    column_name="RevenueUSD",
                    current_dtype="Float64",
                    suggested_logical_type="currency",
                    suggested_polars_type="Decimal(10,2)",
                    reasoning="Currency needs precision",
                ),
            ],
        )

        # User overrides (prefers their own naming/type over AI)
        user_overrides = {
            "User ID": {"name": "customer_id", "type": "Int64"},  # Keep as Int64
            "RevenueUSD": {"name": "revenue_amount", "type": "Decimal(12,4)"},  # More precision
        }

        # Build physical schema with AI suggestions and user overrides
        physical_schema = build_physical_schema(
            columns,
            naming_report=naming_report,
            type_report=type_report,
            user_overrides=user_overrides,
        )

        # Verify user overrides took precedence
        user_id_col = next(col for col in physical_schema if col.source_name == "User ID")
        assert user_id_col.ai_suggested_name == "user_id"  # AI said "user_id"
        assert user_id_col.user_override_name == "customer_id"  # User chose "customer_id"
        assert user_id_col.target_name == "customer_id"  # User wins

        revenue_col = next(col for col in physical_schema if col.source_name == "RevenueUSD")
        assert revenue_col.ai_suggested_type == "Decimal(10,2)"  # AI suggested
        assert revenue_col.user_override_type == "Decimal(12,4)"  # User override
        assert revenue_col.target_type == "Decimal(12,4)"  # User wins

        # Apply schema to transform DataFrame
        transformed_df, transform_log = apply_schema_transform(df, physical_schema)

        # Verify transformations applied
        assert "customer_id" in transformed_df.columns  # Renamed
        assert "customer_id" in [log["target_name"] for log in transform_log]
        assert "revenue_amount" in transformed_df.columns  # Renamed

        # Build metadata contract
        contract = create_metadata_contract(
            table_name="user_transactions",
            version="1.0.0",
            source_path="/data/raw/transactions.csv",
            target_path="/data/processed/transactions.parquet",
            physical_schema=physical_schema,
            statistical_profile={"row_count": 3, "columns": {}},
            created_by="data-engineer@example.com",
        )

        # Validate contract
        is_valid, issues = validate_contract(contract)
        assert is_valid is True
        assert len(issues) == 0

        print("✓ Full workflow completed successfully")
        print(
            f"  - AI suggestions: {len(naming_report.violations)} naming, {len(type_report.suggestions)} type"
        )
        print("  - User overrides: 2 columns modified")
        print(
            f"  - Transformations: {len([log for log in transform_log if 'RENAME' in str(log)])} renames"
        )
        print(f"  - Contract valid: {is_valid}")
