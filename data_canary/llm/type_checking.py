from typing import Dict, List, Any, Optional
from data_canary.llm.base import run_structured_llm_check
from data_canary.schemas.data_models import TypeCheckReport
from data_canary.llm.prompts import TYPE_INSTRUCTION
import json


def get_type_check_prompt(schema: Dict[str, str], columns: List[Dict[str, Any]]) -> str:
    """Constructs the user prompt for the Schema/Type check.

    Takes schema and column statistics and constructs a formatted prompt for the LLM
    to analyze type optimization suggestions.

    Args:
        schema: Dictionary mapping column names to their current data types.
        columns: List of column statistics including null counts, min/max values, etc.

    Returns:
        Formatted prompt string for the LLM type check.
    """
    schema_str = json.dumps(schema, indent=4)
    columns_str = json.dumps(columns, indent=4)

    prompt = f"""{TYPE_INSTRUCTION.strip()}

    Data Schema and columns statistics:
    {schema_str}
    {columns_str}

    Strictly use the provided JSON schema for your output.
    Before giving the result, think step by step, and check the `suggested_logical_type` and `suggested_polars_type` value of each item in the array to see if it meets all the instructions.
    """
    return prompt


def run_llm_type_check(
    schema: Dict[str, str], columns: List[Dict[str, Any]]
) -> Optional[TypeCheckReport]:
    """Executes the LLM type check using the generalized base function.

    Takes schema and column statistics, constructs a prompt, and calls the LLM
    to analyze type optimization suggestions.

    Args:
        schema: Dictionary mapping column names to their current data types.
        columns: List of column statistics including null counts, min/max values, etc.

    Returns:
        TypeCheckReport with optimization suggestions, or None if the check fails.
    """
    prompt = get_type_check_prompt(schema, columns)

    return run_structured_llm_check(prompt, TypeCheckReport)
