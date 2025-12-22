from typing import Dict, List, Any, Optional
from data_canary.llm.base import run_structured_llm_check
from data_canary.schemas.data_models import TypeCheckReport
from data_canary.llm.prompts import SYSTEM_PERSONA, TYPE_INSTRUCTION, JUDGE_INSTRUCTION
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


def run_llm_type_judge_prompt(report: TypeCheckReport, columns: List[Dict[str, Any]]) -> str:
    """
    Takes the initial suggestions and raw stats, and returns a refined set of suggestions.
    """
    judge_payload_str = json.dumps({
        "generator_output": [s.model_dump() for s in report.suggestions],
        "raw_stats": json.dumps(columns, indent=4)
    }, indent=4)

    prompt = f"""
    {JUDGE_INSTRUCTION}

    INPUT DATA:
    {judge_payload_str}
    """
    
    return prompt


def run_llm_type_judge(report: TypeCheckReport, columns: List[Dict[str, Any]]) -> Optional[TypeCheckReport]:
    """
    Executes the LLM type check using the generalized base function.
    """
    prompt = run_llm_type_judge_prompt(report, columns)
    
    return run_structured_llm_check(prompt, TypeCheckReport)