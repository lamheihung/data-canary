from typing import Dict, Optional
from data_canary.llm.base import run_structured_llm_check
from data_canary.schemas.data_models import TypeCheckReport
import json


def get_type_check_prompt(schema: Dict[str, str]) -> str:
    """
    Constructs the detailed system prompt for the Schema/Type check.
    """
    schema_str = json.dumps(schema, indent=4)
    
    prompt = f"""
    You are a professional Data Engineer and schema expert. Your task is to review a dataset's existing Pandas schema and suggest a more precise, target logical type and the corresponding target Pandas dtype for efficient storage and analysis.

    **Instructions for Analysis:**
    1.  **Analyze Context:** Use the column name to infer the *intent* (e.g., 'date', 'currency', 'identifier').
    2.  **Suggest Logical Type:** Provide a descriptive logical type (e.g., 'UUID', 'ISO_DATE', 'CURRENCY_USD', 'CATEGORY').
    3.  **Suggest Pandas Dtype:** Provide the best corresponding, efficient Pandas type (e.g., 'datetime64[ns]', 'string[pyarrow]', 'Int64').
    4.  **Provide Reasoning:** Explain *why* you are suggesting the change or confirming the existing type.

    Analyze the following schema:
    {schema_str}

    Strictly use the provided JSON schema for your output.
    """

    return prompt


def run_llm_type_check(schema: Dict[str, str]) -> Optional[TypeCheckReport]:
    """
    Executes the LLM type check using the generalized base function.
    """
    prompt = get_type_check_prompt(schema)
    
    return run_structured_llm_check(prompt, TypeCheckReport)