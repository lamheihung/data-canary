"""Export functionality for generating Parquet files and metadata contracts.

This module handles the physical output generation for the human-in-the-loop workflow:
- Converting DataFrames to Parquet format with transformed schema
- Serializing metadata contracts to JSON files
- Managing file paths and ensuring output directory exists
"""

from pathlib import Path
from typing import Union, Dict

import polars as pl

from data_canary.schemas.data_models import MetadataContract


def generate_parquet(df: pl.DataFrame, output_path: Union[str, Path], **parquet_kwargs) -> Path:
    """Generates a Parquet file from a Polars DataFrame.

    Saves the transformed DataFrame to Parquet format at the specified path.
    Automatically creates parent directories if they don't exist.

    Args:
        df: The Polars DataFrame to save
        output_path: Path where Parquet file should be saved (e.g., "./output/data.parquet")
        **parquet_kwargs: Additional arguments passed to Polars write_parquet()

    Returns:
        Path to the generated Parquet file

    Raises:
        ValueError: If DataFrame is empty or None
        IOError: If unable to write to the specified path

    Example:
        # Basic usage
        parquet_path = generate_parquet(df, "./output/sales.parquet")

        # With compression
        parquet_path = generate_parquet(
            df,
            "./output/sales.parquet",
            compression="snappy",
            compression_level=12
        )
    """
    if df is None or df.is_empty():
        raise ValueError("DataFrame cannot be None or empty")

    # Ensure output path is Path object
    output_path = Path(output_path)

    # Create parent directories if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Write to Parquet using Polars
        df.write_parquet(output_path, **parquet_kwargs)
    except Exception as e:
        raise IOError(f"Failed to write Parquet file to {output_path}: {e}")

    return output_path


def save_metadata_contract(
    contract: MetadataContract, output_path: Union[str, Path], indent: int = 2, **json_kwargs
) -> Path:
    """Serializes a metadata contract to a JSON file.

    Saves the complete metadata contract as a JSON file, preserving all information
    needed for future validation and drift detection. Creates parent directories as needed.

    Args:
        contract: The MetadataContract object to serialize
        output_path: Path where JSON file should be saved (e.g., "./output/metadata.json")
        indent: Number of spaces to use for JSON indentation (default: 2)
        **json_kwargs: Additional arguments passed to json.dump()

    Returns:
        Path to the generated JSON file

    Raises:
        ValueError: If contract is None or invalid
        IOError: If unable to write to the specified path

    Example:
        # Basic usage
        metadata_path = save_metadata_contract(contract, "./output/metadata.json")

        # Compact JSON (no indentation)
        metadata_path = save_metadata_contract(
            contract,
            "./output/metadata.json",
            indent=None
        )
    """
    if contract is None:
        raise ValueError("Contract cannot be None")

    # Ensure output path is Path object
    output_path = Path(output_path)

    # Create parent directories if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Convert to JSON and save
        json_data = contract.model_dump_json(indent=indent, **json_kwargs)
        output_path.write_text(json_data, encoding="utf-8")
    except Exception as e:
        raise IOError(f"Failed to write JSON to {output_path}: {e}")

    return output_path


def generate_outputs(
    df: pl.DataFrame, contract: MetadataContract, output_prefix: Union[str, Path], **kwargs
) -> Dict[str, Path]:
    """Generates all output files (Parquet and metadata contract) in a single call.

    Convenience function that calls both generate_parquet() and save_metadata_contract()
    using a consistent output prefix. Automatically handles file naming.

    Args:
        df: The transformed DataFrame to save as Parquet
        contract: The MetadataContract to save as JSON
        output_prefix: Base path for output files (e.g., "./output/sales_data")
                      Will generate:
                      - {prefix}.parquet
                      - {prefix}_metadata.json
        **kwargs: Additional arguments passed to underlying functions

    Returns:
        Dictionary with paths to generated files:
        {
            "parquet": Path,
            "metadata": Path
        }

    Raises:
        ValueError: If df or contract is None/invalid
        IOError: If unable to write to output paths

    Example:
        outputs = generate_outputs(df, contract, "./output/sales_data")
        print(f"Parquet: {outputs['parquet']}")
        print(f"Metadata: {outputs['metadata']}")

        # Results in:
        # - ./output/sales_data.parquet
        # - ./output/sales_data_metadata.json
    """
    if df is None or contract is None:
        raise ValueError("DataFrame and contract cannot be None")

    # Ensure prefix is Path
    output_prefix = Path(output_prefix)

    # Generate file paths
    parquet_path = output_prefix.with_suffix(".parquet")
    metadata_path = output_prefix.parent / f"{output_prefix.name}_metadata.json"

    # Generate Parquet file
    parquet_result = generate_parquet(df, parquet_path, **kwargs.get("parquet_kwargs", {}))

    # Generate metadata contract
    metadata_result = save_metadata_contract(
        contract, metadata_path, **kwargs.get("json_kwargs", {})
    )

    return {
        "parquet": parquet_result,
        "metadata": metadata_result,
    }


def load_metadata_contract(input_path: Union[str, Path]) -> MetadataContract:
    """Loads a metadata contract from a JSON file.

    Deserializes a previously saved metadata contract from JSON format. Useful for
    loading contracts during delta ingestion to validate against new data.

    Args:
        input_path: Path to the JSON file containing the metadata contract

    Returns:
        Deserialized MetadataContract object

    Raises:
        ValueError: If contract data is invalid or corrupted
        IOError: If unable to read from the specified path

    Example:
        contract = load_metadata_contract("./contracts/sales_metadata.json")
        print(f"Table: {contract.identity['table_name']}")
        print(f"Columns: {len(contract.physical_schema)}")
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise IOError(f"Metadata contract file not found: {input_path}")

    try:
        json_data = input_path.read_text(encoding="utf-8")
        contract = MetadataContract.model_validate_json(json_data)
    except Exception as e:
        raise ValueError(f"Failed to parse metadata contract from {input_path}: {e}")

    return contract


def get_output_summary(output_paths: Dict[str, Path]) -> str:
    """Generates a human-readable summary of generated outputs.

    Creates a formatted summary showing what files were created and their sizes.
    Useful for displaying to users after the export process completes.

    Args:
        output_paths: Dictionary with 'parquet' and 'metadata' keys from generate_outputs()

    Returns:
        Formatted string summary of the outputs

    Example:
        outputs = generate_outputs(df, contract, "./output/sales")
        summary = get_output_summary(outputs)
        print(summary)
        # Output:
        # Generated Files:
        #   ✓ sales.parquet (2.3 MB)
        #   ✓ sales_metadata.json (8.4 KB)
    """
    lines = ["Generated Files:", ""]

    parquet_path = output_paths.get("parquet")
    if parquet_path and parquet_path.exists():
        size_mb = parquet_path.stat().st_size / (1024 * 1024)
        lines.append(f"  ✓ {parquet_path.name} ({size_mb:.2f} MB)")

    metadata_path = output_paths.get("metadata")
    if metadata_path and metadata_path.exists():
        size_kb = metadata_path.stat().st_size / 1024
        lines.append(f"  ✓ {metadata_path.name} ({size_kb:.2f} KB)")

    return "\n".join(lines)


__all__ = [
    "generate_parquet",
    "save_metadata_contract",
    "generate_outputs",
    "load_metadata_contract",
    "get_output_summary",
]
