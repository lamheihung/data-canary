import os
import json
from typing import List, Optional
from google import genai
from pydantic import ValidationError
from data_canary.check.schema import NamingCheckReport


MODEL_NAME = "gemini-2.5-flash" 

def get_naming_check_prompt(columns: List[str]) -> str:
    """
    Constructs the detailed system prompt for the Gemini LLM.

    Args:
        columns: A list of column names from the DataFrame.

    Returns:
        The complete prompt string.
    """
    column_list_str = "\\n- ".join(columns)
    
    # Use a clear persona and specific instructions in the prompt.
    prompt = f"""
    You are an expert Data Architect and Data Engineer specializing in Python and data warehousing best practices.
    Your task is to analyze a list of column names for a dataset and identify any that violate modern naming conventions.

    **Conventions to Enforce:**
    1.  **Format:** All names must be in `snake_case` (e.g., `user_id`, `total_amount`).
    2.  **Clarity:** Names should be descriptive and avoid abbreviations where a full word is clearer (e.g., use `identifier` instead of `id` unless contextually common).
    3.  **Case:** Avoid PascalCase (`OrderDate`), camelCase (`orderDate`), and ALL_CAPS (`ORDER_ID`).
    4.  **Special Characters:** Avoid spaces, hyphens, and other special characters.

    Analyze the following column names and provide your structured critique:

    Column Names:
    - {column_list_str}

    Strictly use the provided JSON schema for your output. If no violations are found, the `violations` list must be empty, and the `summary` must reflect a passing result.
    """
    return prompt

def run_llm_naming_check(columns: List[str]) -> Optional[NamingCheckReport]:
    """
    Calls the Gemini API to analyze column names and returns a structured report.

    Args:
        columns: A list of column names to check.

    Returns:
        A NamingCheckReport object if successful, otherwise None.
    """
    # 1. Environment Check and Client Initialization
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable is not set.")
        return None
    
    try:
        # Client automatically picks up the API key from environment
        client = genai.Client()
    except Exception as e:
        print(f"ERROR: Failed to initialize Gemini client: {e}")
        return None

    # 2. Get Prompt and Configuration
    prompt = get_naming_check_prompt(columns)
    
    # Create the configuration for structured JSON output
    config = {
        "response_mime_type": "application/json",
        "response_json_schema": NamingCheckReport.model_json_schema(),
    }

    # 3. Call the Gemini API
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=config,
        )
    except Exception as e:
        print(f"ERROR: Gemini API call failed: {e}")
        return None

    # 4. Parse and Validate the Structured Output
    try:
        # The model's response.text is a guaranteed JSON string due to the config.
        report = NamingCheckReport.model_validate_json(response.text)
        return report
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"ERROR: Failed to parse or validate LLM JSON response: {e}")
        print(f"Raw response text: {response.text}")
        return None