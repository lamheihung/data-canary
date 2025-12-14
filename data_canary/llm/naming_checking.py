from typing import List, Optional
from data_canary.llm.base import run_structured_llm_check
from data_canary.schemas.data_models import NamingCheckReport


def get_naming_check_prompt(columns: List[str]) -> str:
    column_list_str = "\n- ".join(columns)
    
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
    Executes the LLM naming check using the generalized base function.
    """
    prompt = get_naming_check_prompt(columns)
    
    return run_structured_llm_check(prompt, NamingCheckReport)