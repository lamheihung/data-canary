from typing import Dict, Optional
from data_canary.llm.base import run_structured_llm_check
from data_canary.schemas.data_models import TypeCheckReport
from data_canary.llm.prompts import SYSTEM_PERSONA, TYPE_INSTRUCTION
import json


def get_type_check_prompt(schema: Dict[str, str]) -> str:
    """
    Constructs the detailed system prompt for the Schema/Type check.
    """
    schema_str = json.dumps(schema, indent=4)
    
    prompt = f"""
    {SYSTEM_PERSONA.strip()}

    {TYPE_INSTRUCTION.strip()}
    
    Data Schema and Context:
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