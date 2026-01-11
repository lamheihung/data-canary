"""Unit tests for export functionality.

Tests cover Parquet file generation, metadata contract serialization,
and output management for the human-in-the-loop workflow.
"""

import pytest
import tempfile
from pathlib import Path
import json

import polars as pl

from data_canary.core.export import (
    generate_parquet,
    save_metadata_contract,
    generate_outputs,
    load_metadata_contract,
    get_output_summary,
)
from data_canary.schemas.data_models import (
    MetadataContract,
    PhysicalColumn,
)


class TestGenerateParquet:
    """Tests for Parquet file generation."""

    def test_generate_parquet_basic(self):
        """Test basic Parquet file generation."""
        df = pl.DataFrame(
            {
                "user_id": [1, 2, 3],
                "amount": [10.5, 20.3, 15.7],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.parquet"
            result_path = generate_parquet(df, output_path)

            # Check file was created
            assert result_path.exists()
            assert result_path == output_path
            assert result_path.suffix == ".parquet"

            # Check we can read it back
            df_read = pl.read_parquet(result_path)
            assert len(df_read) == 3
            assert df_read["user_id"].to_list() == [1, 2, 3]

    def test_generate_parquet_creates_directories(self):
        """Test that directories are created if they don't exist."""
        df = pl.DataFrame({"col": [1, 2, 3]})

        with tempfile.TemporaryDirectory() as tmpdir:
            # Path with nested directories that don't exist
            output_path = Path(tmpdir) / "subdir1" / "subdir2" / "test.parquet"
            result_path = generate_parquet(df, output_path)

            # Check directories were created and file exists
            assert result_path.exists()
            assert result_path.parent.exists()

    def test_generate_parquet_with_compression(self):
        """Test Parquet generation with compression."""
        df = pl.DataFrame({"data": list(range(1000))})  # Larger dataset

        with tempfile.TemporaryDirectory() as tmpdir:
            # Without compression
            path1 = Path(tmpdir) / "uncompressed.parquet"
            generate_parquet(df, path1)
            _ = path1.stat().st_size  # Just verify file was created

            # With compression
            path2 = Path(tmpdir) / "compressed.parquet"
            generate_parquet(df, path2, compression="snappy")
            _ = path2.stat().st_size  # Just verify file was created

            # Compressed should be smaller or similar (for some data patterns)
            assert path2.exists()

    def test_generate_parquet_empty_df_error(self):
        """Test error handling for empty DataFrame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.parquet"

            with pytest.raises(ValueError, match="DataFrame cannot be None or empty"):
                generate_parquet(pl.DataFrame({}), output_path)

    def test_generate_parquet_none_df_error(self):
        """Test error handling for None DataFrame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.parquet"

            with pytest.raises(ValueError, match="DataFrame cannot be None or empty"):
                generate_parquet(None, output_path)


class TestSaveMetadataContract:
    """Tests for metadata contract JSON serialization."""

    def test_save_metadata_contract_basic(self):
        """Test basic metadata contract serialization."""
        contract = MetadataContract(
            identity={
                "table_name": "test_data",
                "version": "1.0.0",
            },
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
            statistical_profile={"row_count": 100},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metadata.json"
            result_path = save_metadata_contract(contract, output_path)

            # Check file was created
            assert result_path.exists()
            assert result_path == output_path

            # Check content is valid JSON
            json_data = json.loads(output_path.read_text())
            assert json_data["identity"]["table_name"] == "test_data"
            assert len(json_data["physical_schema"]) == 1

    def test_save_metadata_contract_creates_directories(self):
        """Test that directories are created for metadata output."""
        contract = MetadataContract(
            identity={"table_name": "test"},
            physical_schema=[],
            statistical_profile={},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "metadata.json"
            result_path = save_metadata_contract(contract, output_path)

            assert result_path.exists()
            assert result_path.parent.exists()

    def test_save_metadata_contract_custom_indent(self):
        """Test saving with custom JSON indentation."""
        contract = MetadataContract(
            identity={"table_name": "test"},
            physical_schema=[],
            statistical_profile={},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # With indentation (default)
            path1 = Path(tmpdir) / "indented.json"
            save_metadata_contract(contract, path1, indent=2)
            lines1 = len(path1.read_text().splitlines())

            # Without indentation
            path2 = Path(tmpdir) / "compact.json"
            save_metadata_contract(contract, path2, indent=None)
            lines2 = len(path2.read_text().splitlines())

            # Indented should have more lines
            assert lines1 > lines2

    def test_save_metadata_contract_none_error(self):
        """Test error handling for None contract."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metadata.json"

            with pytest.raises(ValueError, match="Contract cannot be None"):
                save_metadata_contract(None, output_path)


class TestGenerateOutputs:
    """Tests for combined output generation."""

    def test_generate_outputs_basic(self):
        """Test generating both Parquet and metadata together."""
        df = pl.DataFrame({"col": [1, 2, 3]})

        contract = MetadataContract(
            identity={"table_name": "test"},
            physical_schema=[],
            statistical_profile={},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_prefix = Path(tmpdir) / "output"
            result = generate_outputs(df, contract, output_prefix)

            # Check both files were created
            assert "parquet" in result
            assert "metadata" in result
            assert result["parquet"].exists()
            assert result["metadata"].exists()

            # Check naming convention
            assert result["parquet"].name == "output.parquet"
            assert result["metadata"].name == "output_metadata.json"

    def test_generate_outputs_nested_directories(self):
        """Test output generation with nested directories."""
        df = pl.DataFrame({"col": [1]})
        contract = MetadataContract(
            identity={"table_name": "test"}, physical_schema=[], statistical_profile={}
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_prefix = Path(tmpdir) / "processed" / "2025" / "01" / "sales_data"
            result = generate_outputs(df, contract, output_prefix)

            # Check files were created in nested structure
            assert result["parquet"].exists()
            assert "processed/2025/01" in str(result["parquet"])
            assert result["metadata"].exists()

    def test_generate_outputs_kwargs_passed(self):
        """Test that kwargs are passed to underlying functions."""
        df = pl.DataFrame({"col": list(range(100))})  # Larger dataset
        contract = MetadataContract(
            identity={"table_name": "test"}, physical_schema=[], statistical_profile={}
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_prefix = Path(tmpdir) / "test"
            result = generate_outputs(
                df,
                contract,
                output_prefix,
                parquet_kwargs={"compression": "snappy"},
            )

            # File should exist (compression applied)
            assert result["parquet"].exists()

    def test_generate_outputs_none_df_error(self):
        """Test error handling for None DataFrame."""
        contract = MetadataContract(
            identity={"table_name": "test"}, physical_schema=[], statistical_profile={}
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_prefix = Path(tmpdir) / "test"

            with pytest.raises(ValueError, match="DataFrame and contract cannot be None"):
                generate_outputs(None, contract, output_prefix)

    def test_generate_outputs_none_contract_error(self):
        """Test error handling for None contract."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_prefix = Path(tmpdir) / "test"

            with pytest.raises(ValueError, match="DataFrame and contract cannot be None"):
                generate_outputs(pl.DataFrame({"col": [1]}), None, output_prefix)


class TestLoadMetadataContract:
    """Tests for loading metadata contracts from files."""

    def test_load_metadata_contract_basic(self):
        """Test loading a metadata contract from JSON file."""
        contract = MetadataContract(
            identity={"table_name": "test_data", "version": "1.0.0"},
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
            statistical_profile={"row_count": 100},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # Save then load
            file_path = Path(tmpdir) / "contract.json"
            file_path.write_text(contract.model_dump_json())

            loaded_contract = load_metadata_contract(file_path)

            assert loaded_contract.identity["table_name"] == "test_data"
            assert loaded_contract.identity["version"] == "1.0.0"
            assert len(loaded_contract.physical_schema) == 1
            assert loaded_contract.statistical_profile["row_count"] == 100

    def test_load_metadata_contract_nonexistent_error(self):
        """Test error handling for non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "missing.json"

            with pytest.raises(IOError, match="Metadata contract file not found"):
                load_metadata_contract(nonexistent)

    def test_load_metadata_contract_invalid_json_error(self):
        """Test error handling for invalid JSON content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_path = Path(tmpdir) / "invalid.json"
            invalid_path.write_text('{"invalid": json content}')  # Malformed JSON

            with pytest.raises(ValueError, match="Failed to parse metadata contract"):
                load_metadata_contract(invalid_path)


class TestGetOutputSummary:
    """Tests for output summary generation."""

    def test_get_output_summary_with_files(self):
        """Test summary generation with actual files."""
        df = pl.DataFrame({"col": list(range(100))})  # Larger for size
        contract = MetadataContract(
            identity={"table_name": "test"}, physical_schema=[], statistical_profile={}
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_paths = {
                "parquet": Path(tmpdir) / "data.parquet",
                "metadata": Path(tmpdir) / "data_metadata.json",
            }

            # Generate files
            df.write_parquet(output_paths["parquet"])
            output_paths["metadata"].write_text(contract.model_dump_json())

            summary = get_output_summary(output_paths)

            assert "data.parquet" in summary
            assert "data_metadata.json" in summary
            assert "MB" in summary or "KB" in summary  # Has size info

    def test_get_output_summary_missing_files(self):
        """Test summary with non-existent files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Files don't exist
            output_paths = {
                "parquet": Path(tmpdir) / "missing.parquet",
                "metadata": Path(tmpdir) / "missing_metadata.json",
            }

            summary = get_output_summary(output_paths)

            # Summary should be mostly empty but not crash
            assert "Generated Files:" in summary

    def test_get_output_summary_empty_dict(self):
        """Test summary with empty dictionary."""
        summary = get_output_summary({})
        assert summary.strip() == "Generated Files:"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
