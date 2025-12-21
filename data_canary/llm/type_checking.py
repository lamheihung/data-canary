from typing import Dict, List, Any, Optional
from data_canary.llm.base import run_structured_llm_check
from data_canary.schemas.data_models import TypeCheckReport
from data_canary.llm.prompts import SYSTEM_PERSONA, TYPE_INSTRUCTION
import json


def get_type_check_prompt(schema: Dict[str, str], columns: List[Dict[str, Any]]) -> str:
    """
    Constructs the detailed system prompt for the Schema/Type check.
    """
    schema_str = json.dumps(schema, indent=4)
    columns_str = json.dumps(columns, indent=4)
    
    prompt = f"""
    {SYSTEM_PERSONA.strip()}

    {TYPE_INSTRUCTION.strip()}
    
    Data Schema and columns statistics:
    {schema_str}
    {columns_str}

    Strictly use the provided JSON schema for your output.
    """
    return prompt


def run_llm_type_check(schema: Dict[str, str], columns: List[Dict[str, Any]]) -> Optional[TypeCheckReport]:
    """
    Executes the LLM type check using the generalized base function.
    """
    prompt = get_type_check_prompt(schema, columns)
    
    return run_structured_llm_check(prompt, TypeCheckReport)