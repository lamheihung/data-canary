from typing import List, Optional
from data_canary.llm.base import run_structured_llm_check
from data_canary.schemas.data_models import NamingCheckReport
from data_canary.llm.prompts import SYSTEM_PERSONA, NAMING_INSTRUCTION


def get_naming_check_prompt(columns: List[str]) -> str:
    """
    Constructs the detailed system prompt for the Naming check.
    """
    column_list_str = "\n- ".join(columns)
    
    # Combined, clean prompt using the new constants
    prompt = f"""
    {SYSTEM_PERSONA.strip()}
    
    {NAMING_INSTRUCTION.strip()}

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