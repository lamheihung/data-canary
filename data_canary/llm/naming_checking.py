from typing import List, Optional
from data_canary.llm.base import run_structured_llm_check
from data_canary.schemas.data_models import NamingCheckReport
from data_canary.llm.prompts import NAMING_INSTRUCTION


def get_naming_check_prompt(columns: List[str]) -> str:
    """Constructs the user prompt for the Naming check.

    Takes a list of column names and constructs a formatted prompt for the LLM
    to analyze naming convention violations.

    Args:
        columns: List of column names to analyze.

    Returns:
        Formatted prompt string for the LLM naming check.
    """
    column_list_str = "\n- ".join(columns)

    # User prompt with task instructions and data
    prompt = f"""{NAMING_INSTRUCTION.strip()}

    Column Names:
    - {column_list_str}

    Strictly use the provided JSON schema for your output. If no violations are found, the `violations` list must be empty, and the `summary` must reflect a passing result.
    Before giving the result, think step by step, and check the `column_name` and `suggested_name` value of each item in `violations` list to see if it meets all the conventions.
    """
    return prompt


def run_llm_naming_check(columns: List[str]) -> Optional[NamingCheckReport]:
    """Executes the LLM naming check using the generalized base function.

    Takes column names, constructs a prompt, and calls the LLM to analyze
    naming convention violations.

    Args:
        columns: List of column names from the dataset.

    Returns:
        NamingCheckReport with violation details, or None if the check fails.
    """
    prompt = get_naming_check_prompt(columns)

    return run_structured_llm_check(prompt, NamingCheckReport)
