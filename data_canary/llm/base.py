import json
from typing import Optional, Type, TypeVar
from google import genai
from pydantic import BaseModel, ValidationError
from data_canary.config import GEMINI_API_KEY, GEMINI_MODEL_NAME


# Generic type variable for Pydantic models
PydanticModel = TypeVar("PydanticModel", bound=BaseModel)


def run_structured_llm_check(
    prompt: str,
    response_model: Type[PydanticModel],
    model_name: str = GEMINI_MODEL_NAME,
) -> Optional[PydanticModel]:
    """
    Generalized function to call the Gemini API and enforce structured Pydantic output.

    Handles client initialization, API call, and structured JSON validation.
    
    Args:
        prompt: The full prompt string to send to the LLM.
        response_model: The Pydantic model class to enforce the output structure.
        model_name: The specific Gemini model to use.

    Returns:
        An instance of the Pydantic model if successful, otherwise None.
    """
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY environment variable is not set. Cannot run LLM checks.")

        return None
    
    try:
        client = genai.Client()
    except Exception as e:
        print(f"ERROR: Failed to initialize Gemini client: {e}")

        return None

    # Configuration to enforce JSON structure based on the Pydantic model
    config = {
        "response_mime_type": "application/json",
        "response_json_schema": response_model.model_json_schema(),
    }

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
    except Exception as e:
        print(f"ERROR: Gemini API call failed: {e}")

        return None

    # Parse and Validate the Structured Output using Pydantic
    try:
        report = response_model.model_validate_json(response.text)

        return report
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"ERROR: Failed to parse or validate LLM JSON response for {response_model.__name__}: {e}")
        print(f"Raw response text: {response.text}")
        
        return None