import json
from typing import Optional, Type, TypeVar, List, Dict, Any
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from data_canary.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL_NAME
from data_canary.llm.prompts import SYSTEM_PERSONA


# Generic type variable for Pydantic models
PydanticModel = TypeVar("PydanticModel", bound=BaseModel)


def run_structured_llm_check(
    user_prompt: str,
    response_model: Type[PydanticModel],
    model_name: str = OPENAI_MODEL_NAME,
) -> Optional[PydanticModel]:
    """
    Generalized function to call the OpenAI API and enforce structured Pydantic output.

    Handles client initialization, API call, and structured JSON validation.

    Args:
        user_prompt: The user prompt string to send to the LLM.
        response_model: The Pydantic model class to enforce the output structure.
        model_name: The specific OpenAI-compatible model to use.

    Returns:
        An instance of the Pydantic model if successful, otherwise None.
    """
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY environment variable is not set. Cannot run LLM checks.")
        return None

    try:
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
        )
    except Exception as e:
        print(f"ERROR: Failed to initialize OpenAI client: {e}")
        return None

    # Include both persona and schema enforcement in system message
    schema_json = json.dumps(response_model.model_json_schema(), indent=2)
    system_prompt = f"""{SYSTEM_PERSONA.strip()}

    IMPORTANT: You MUST respond with a JSON object that strictly follows this schema:
    {schema_json}

    Do not include any explanatory text outside the JSON structure.
    """

    # Prepare messages with system persona + schema enforcement and user prompt
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            response_format={"type": "json_object"}
        )
    except Exception as e:
        print(f"ERROR: OpenAI API call failed: {e}")
        return None

    # Parse and Validate the Structured Output using Pydantic
    try:
        # Extract the content from the response
        content = response.choices[0].message.content
        if not content:
            print("ERROR: No content in response from OpenAI API")
            return None

        report = response_model.model_validate_json(content)
        return report
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"ERROR: Failed to parse or validate LLM JSON response for {response_model.__name__}: {e}")
        if 'content' in locals():
            print(f"Raw response text: {content}")

        return None