import os
import json
from typing import List, Dict, Any, Optional
from google import genai
from pydantic import ValidationError
from data_canary.check.schema import TypeCheckReport


MODEL_NAME = "gemini-2.5-flash" 

def get_type_check_prompt(schema: Dict[str, str]) -> str:
    """
    Constructs the detailed system prompt for the Gemini LLM for type checking.

    Args:
        schema: A dictionary of column names and their current Pandas dtypes.

    Returns:
        The complete prompt string.
    """
    schema_str = json.dumps(schema, indent=4)
    
    prompt = f"""
    You are a professional Data Engineer and schema expert. Your task is to review a dataset's existing Pandas schema and suggest a more precise, target logical type and the corresponding target Pandas dtype for efficient storage and analysis.

    **Instructions for Analysis:**
    1.  **Analyze Context:** Use the column name to infer the *intent* (e.g., 'date', 'currency', 'identifier').
    2.  **Suggest Logical Type:** Provide a descriptive logical type (e.g., 'UUID', 'ISO_DATE', 'CURRENCY_USD', 'CATEGORY').
    3.  **Suggest Pandas Dtype:** Provide the best corresponding, efficient Pandas type (e.g., 'string', 'datetime64[ns]', 'Int64').
    4.  **Provide Reasoning:** Explain *why* you are suggesting the change or confirming the existing type.

    Analyze the following schema:
    {schema_str}

    Strictly use the provided JSON schema for your output.
    """
    return prompt

def run_llm_type_check(schema: Dict[str, str]) -> Optional[TypeCheckReport]:
    """
    Calls the Gemini API to analyze the current schema and suggest optimized types.

    Args:
        schema: A dictionary of column names and their current Pandas dtypes.

    Returns:
        A TypeCheckReport object if successful, otherwise None.
    """
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable is not set.")
        return None
    
    try:
        client = genai.Client()
    except Exception as e:
        print(f"ERROR: Failed to initialize Gemini client: {e}")
        return None

    prompt = get_type_check_prompt(schema)
    
    config = {
        "response_mime_type": "application/json",
        "response_json_schema": TypeCheckReport.model_json_schema(),
    }

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=config,
        )
    except Exception as e:
        print(f"ERROR: Gemini API call failed: {e}")
        return None

    try:
        report = TypeCheckReport.model_validate_json(response.text)
        return report
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"ERROR: Failed to parse or validate LLM JSON response for Type Check: {e}")
        print(f"Raw response text: {response.text}")
        return None