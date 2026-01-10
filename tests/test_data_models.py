"""Unit tests for Pydantic data models.

Tests cover the contract models for MVP0 including LLM usage tracking,
column roles, physical schema definitions, and metadata contracts.
"""

import pytest
from data_canary.schemas.data_models import (
    LLMUsage,
    ColumnRole,
    PhysicalColumn,
    MetadataContract,
)


class TestLLMUsage:
    """Test LLMUsage model for tracking API usage and costs."""

    def test_llm_usage_creation(self):
        """Test creating a valid LLMUsage instance."""
        usage = LLMUsage(
            tokens_prompt=150,
            tokens_completion=250,
            total_tokens=400,
            estimated_cost=0.006,
            model_name="kimi-k2-thinking",
        )

        assert usage.tokens_prompt == 150
        assert usage.tokens_completion == 250
        assert usage.total_tokens == 400
        assert usage.estimated_cost == 0.006
        assert usage.model_name == "kimi-k2-thinking"

    def test_llm_usage_default_values(self):
        """Test LLMUsage with default values."""
        usage = LLMUsage(model_name="test-model")

        assert usage.tokens_prompt == 0
        assert usage.tokens_completion == 0
        assert usage.total_tokens == 0
        assert usage.estimated_cost == 0.0
        assert usage.model_name == "test-model"

    def test_llm_usage_serialization(self):
        """Test LLMUsage JSON serialization."""
        usage = LLMUsage(
            tokens_prompt=100,
            tokens_completion=200,
            total_tokens=300,
            estimated_cost=0.0045,
            model_name="gpt-4",
        )

        json_str = usage.model_dump_json()
        assert "gpt-4" in json_str
        assert "300" in json_str

        # Test deserialization
        usage2 = LLMUsage.model_validate_json(json_str)
        assert usage2.total_tokens == 300
        assert usage2.estimated_cost == 0.0045


class TestColumnRole:
    """Test ColumnRole model for storing vendor metadata."""

    def test_column_role_with_all_fields(self):
        """Test ColumnRole with complete data."""
        role = ColumnRole(
            column_name="user_id",
            role_type="primary_key",
            description="Unique identifier from vendor's CRM system",
        )

        assert role.column_name == "user_id"
        assert role.role_type == "primary_key"
        assert "vendor's CRM" in role.description

    def test_column_role_without_description(self):
        """Test ColumnRole with optional description omitted."""
        role = ColumnRole(column_name="revenue", role_type="metric")

        assert role.column_name == "revenue"
        assert role.role_type == "metric"
        assert role.description is None

    def test_column_role_custom_type(self):
        """Test ColumnRole with custom vendor-specific role type."""
        role = ColumnRole(
            column_name="customer_segment",
            role_type="acme_crm_segment",
            description="Customer segment classification from Acme CRM v2.5",
        )

        assert role.role_type == "acme_crm_segment"
        assert "Acme CRM" in role.description

    def test_column_role_serialization(self):
        """Test ColumnRole JSON roundtrip."""
        role = ColumnRole(
            column_name="sale_date",
            role_type="event_marker",
            description="Timestamp when the sale was recorded",
        )

        json_str = role.model_dump_json()
        role2 = ColumnRole.model_validate_json(json_str)

        assert role2.column_name == role.column_name
        assert role2.role_type == role.role_type
        assert role2.description == role.description


class TestPhysicalColumn:
    """Test PhysicalColumn model for schema with override tracking."""

    def test_physical_column_no_overrides(self):
        """Test PhysicalColumn with no user overrides."""
        col = PhysicalColumn(
            source_name="User ID",
            target_name="user_id",
            data_type="UInt32",
            is_nullable=False,
            ai_suggested_name="user_id",
            ai_suggested_type="UInt32",
            column_index=0,
        )

        assert col.source_name == "User ID"
        assert col.target_name == "user_id"
        assert col.data_type == "UInt32"
        assert col.is_nullable is False
        assert col.user_override_name is None
        assert col.user_override_type is None
        assert col.column_index == 0

    def test_physical_column_with_name_override(self):
        """Test PhysicalColumn with user name override."""
        col = PhysicalColumn(
            source_name="CustomerID",
            target_name="customer_id_override",
            data_type="UInt64",
            is_nullable=False,
            ai_suggested_name="customer_id",
            user_override_name="customer_id_override",
            column_index=1,
        )

        assert col.user_override_name == "customer_id_override"
        assert col.target_name == "customer_id_override"  # Should match override

    def test_physical_column_with_type_override(self):
        """Test PhysicalColumn with user type override."""
        col = PhysicalColumn(
            source_name="Revenue",
            target_name="revenue",
            data_type="Decimal(10,2)",  # User override
            is_nullable=True,
            ai_suggested_type="Float64",  # AI suggested different type
            user_override_type="Decimal(10,2)",
            column_index=2,
        )

        assert col.user_override_type == "Decimal(10,2)"
        assert col.ai_suggested_type == "Float64"
        assert col.data_type == "Decimal(10,2)"  # Final type is override

    def test_physical_column_with_role(self):
        """Test PhysicalColumn with column role assigned."""
        col = PhysicalColumn(
            source_name="user_id",
            target_name="user_id",
            data_type="UInt32",
            is_nullable=False,
            role="primary_key",
            column_index=0,
        )

        assert col.role == "primary_key"

    def test_physical_column_order_preservation(self):
        """Test that column_index preserves original order."""
        columns = [
            PhysicalColumn(
                source_name=f"col_{i}",
                target_name=f"col_{i}",
                data_type="Int64",
                is_nullable=True,
                column_index=i,
            )
            for i in range(5)
        ]

        # Verify order is preserved
        for i, col in enumerate(columns):
            assert col.column_index == i
            assert col.source_name == f"col_{i}"

    def test_physical_column_override_detection(self):
        """Test detection of whether column has overrides."""
        col_without_override = PhysicalColumn(
            source_name="name",
            target_name="name",
            data_type="String",
            is_nullable=True,
            column_index=0,
        )

        col_with_override = PhysicalColumn(
            source_name="name",
            target_name="customer_name",
            data_type="String",
            is_nullable=True,
            user_override_name="customer_name",
            column_index=1,
        )

        assert col_without_override.user_override_name is None
        assert col_with_override.user_override_name is not None


class TestMetadataContract:
    """Test MetadataContract model for complete schema definition."""

    @pytest.fixture
    def sample_contract(self):
        """Create a sample metadata contract for testing."""
        return MetadataContract(
            identity={
                "table_name": "sales_data",
                "version": "1.0.0",
                "created_at": "2026-01-10T10:30:00Z",
                "source_path": "/data/raw/sales.csv",
                "target_path": "/data/processed/sales.parquet",
                "created_by": "data-engineer@company.com",
            },
            physical_schema=[
                PhysicalColumn(
                    source_name="User ID",
                    target_name="user_id",
                    data_type="UInt32",
                    is_nullable=False,
                    role="primary_key",
                    column_index=0,
                ),
                PhysicalColumn(
                    source_name="Sale Date",
                    target_name="sale_date",
                    data_type="Date",
                    is_nullable=False,
                    role="event_marker",
                    column_index=1,
                ),
            ],
            statistical_profile={
                "row_count": 10000,
                "columns": {
                    "user_id": {"null_count_pct": 0.0, "cardinality": 89234},
                    "sale_date": {"null_count_pct": 0.0, "min": "2025-01-01"},
                },
            },
        )

    def test_metadata_contract_creation(self, sample_contract):
        """Test creating a valid MetadataContract."""
        assert sample_contract.identity["table_name"] == "sales_data"
        assert sample_contract.identity["version"] == "1.0.0"
        assert len(sample_contract.physical_schema) == 2
        assert sample_contract.statistical_profile["row_count"] == 10000

    def test_metadata_contract_with_llm_usage(self, sample_contract):
        """Test MetadataContract with LLM usage tracking."""
        llm_usage = LLMUsage(
            tokens_prompt=450,
            tokens_completion=380,
            total_tokens=830,
            estimated_cost=0.012,
            model_name="kimi-k2-thinking",
        )

        contract_with_usage = MetadataContract(
            identity=sample_contract.identity,
            physical_schema=sample_contract.physical_schema,
            statistical_profile=sample_contract.statistical_profile,
            llm_usage=llm_usage,
        )

        assert contract_with_usage.llm_usage is not None
        assert contract_with_usage.llm_usage.total_tokens == 830
        assert contract_with_usage.llm_usage.estimated_cost == 0.012

    def test_metadata_contract_with_column_roles(self, sample_contract):
        """Test MetadataContract with custom column roles."""
        roles = [
            ColumnRole(
                column_name="user_id",
                role_type="primary_key",
                description="Unique identifier from vendor CRM",
            ),
            ColumnRole(column_name="sale_date", role_type="event", description="Sale timestamp"),
        ]

        contract_with_roles = MetadataContract(
            identity=sample_contract.identity,
            physical_schema=sample_contract.physical_schema,
            statistical_profile=sample_contract.statistical_profile,
            column_roles=roles,
        )

        assert contract_with_roles.column_roles is not None
        assert len(contract_with_roles.column_roles) == 2
        assert contract_with_roles.column_roles[0].role_type == "primary_key"

    def test_metadata_contract_with_overrides(self, sample_contract):
        """Test MetadataContract tracking column overrides."""
        # Create columns with different override patterns
        columns = [
            PhysicalColumn(
                source_name="User ID",
                target_name="user_id",
                data_type="UInt32",
                is_nullable=False,
                column_index=0,
            ),
            PhysicalColumn(
                source_name="RevenueUSD",
                target_name="revenue_override",
                data_type="Decimal(10,2)",
                is_nullable=False,
                user_override_name="revenue_override",
                column_index=1,
            ),
        ]

        contract = MetadataContract(
            identity=sample_contract.identity,
            physical_schema=columns,
            statistical_profile=sample_contract.statistical_profile,
        )

        # Count columns with overrides
        columns_with_overrides = [col for col in contract.physical_schema if col.user_override_name]
        assert len(columns_with_overrides) == 1
        assert columns_with_overrides[0].user_override_name == "revenue_override"

    def test_metadata_contract_serialization(self, sample_contract):
        """Test MetadataContract JSON serialization/deserialization."""
        # Serialize
        json_str = sample_contract.model_dump_json()
        assert "sales_data" in json_str
        assert "1.0.0" in json_str

        # Deserialize
        contract2 = MetadataContract.model_validate_json(json_str)
        assert contract2.identity["table_name"] == "sales_data"
        assert len(contract2.physical_schema) == len(sample_contract.physical_schema)

    def test_metadata_contract_order_preservation(self):
        """Test that column_index preserves original column order."""
        columns = [
            PhysicalColumn(
                source_name=f"col_{i}",
                target_name=f"col_{i}",
                data_type="Int64",
                is_nullable=True,
                column_index=i,
            )
            for i in range(10)
        ]

        contract = MetadataContract(
            identity={"table_name": "test", "version": "1.0"},
            physical_schema=columns,
            statistical_profile={"row_count": 100},
        )

        # Verify order is maintained
        for i, col in enumerate(contract.physical_schema):
            assert col.column_index == i


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_full_contract_with_all_features(self):
        """Test a complete contract using all features together."""
        # Create LLM usage tracking
        llm_usage = LLMUsage(
            tokens_prompt=1500,
            tokens_completion=1200,
            total_tokens=2700,
            estimated_cost=0.040,
            model_name="kimi-k2-thinking",
        )

        # Create column roles
        roles = [
            ColumnRole(
                column_name="user_id", role_type="primary_key", description="PK from vendor"
            ),
            ColumnRole(column_name="event_timestamp", role_type="event", description="Event time"),
        ]

        # Create physical schema with overrides
        columns = [
            PhysicalColumn(
                source_name="User ID",
                target_name="user_id",
                data_type="UInt32",
                is_nullable=False,
                role="primary_key",
                ai_suggested_name="user_id",
                column_index=0,
            ),
            PhysicalColumn(
                source_name="EventTS",
                target_name="event_timestamp",
                data_type="Datetime",
                is_nullable=False,
                role="event_marker",
                ai_suggested_name="event_timestamp",
                column_index=1,
            ),
            PhysicalColumn(
                source_name="RevenueUSD",
                target_name="revenue_usd_override",
                data_type="Decimal(10,2)",
                is_nullable=True,
                role="metric",
                ai_suggested_name="revenue_usd",
                ai_suggested_type="Float64",
                user_override_name="revenue_usd_override",
                user_override_type="Decimal(10,2)",
                column_index=2,
            ),
        ]

        # Create complete metadata contract
        contract = MetadataContract(
            identity={
                "table_name": "user_events_2025",
                "version": "1.0.0",
                "created_at": "2026-01-10T12:00:00Z",
                "source_path": "/data/raw/events.csv",
                "target_path": "/data/processed/user_events_2025.parquet",
                "created_by": "data-engineer@company.com",
            },
            physical_schema=columns,
            statistical_profile={
                "row_count": 50000,
                "columns": {
                    "user_id": {"null_count_pct": 0.0, "cardinality": 50000},
                    "event_timestamp": {"null_count_pct": 0.0},
                    "revenue_usd_override": {"null_count_pct": 0.15},
                },
            },
            llm_usage=llm_usage,
            column_roles=roles,
        )

        # Verify all components
        assert contract.llm_usage.total_tokens == 2700
        assert len(contract.column_roles) == 2
        assert len(contract.physical_schema) == 3

        # Check overrides
        columns_with_overrides = [
            col
            for col in contract.physical_schema
            if col.user_override_name or col.user_override_type
        ]
        assert len(columns_with_overrides) == 1
        assert columns_with_overrides[0].user_override_name == "revenue_usd_override"

        # Verify serialization preserves all data
        json_str = contract.model_dump_json()
        assert "user_events_2025" in json_str
        assert "revenue_usd_override" in json_str
        assert "Decimal(10,2)" in json_str
        assert "2700" in json_str  # Token count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
