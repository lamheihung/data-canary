from pydantic import BaseModel, Field
from typing import List


# --- Naming Check Models ---
class NamingViolation(BaseModel):
    """Details for a single column that violates naming conventions."""
    column_name: str = Field(description="The name of the column that violates conventions.")
    violation_reason: str = Field(description="A clear, concise reason why the column name is poor or violates convention.")
    suggested_name: str = Field(description="The recommended name for the column following best practices (e.g., snake_case).")


class NamingCheckReport(BaseModel):
    """The complete report of naming convention violations across a dataset."""
    summary: str = Field(description="A brief, encouraging summary of the naming check results, including the total number of violations found.")
    violations: List[NamingViolation] = Field(description="A list of specific naming violations found in the dataset's columns.")


# --- Type Check Models ---
class TypeSuggestion(BaseModel):
    """Details for a single column's type suggestion.""" 
    column_name: str = Field(description="The name of the column being analyzed.")
    current_dtype: str = Field(description="The current data type as inferred by Polars (e.g., 'Int8', 'Float64').")
    suggested_logical_type: str = Field(description="The suggested, precise logical data type (e.g., 'UUID', 'ISO_DATE', 'CURRENCY_USD', 'CATEGORY').")
    suggested_polars_type: str = Field(description="The suggested Python/Polars dtype for coersion (e.g., 'UInt64', 'Date').")
    reasoning: str = Field(description="The reasoning behind the type suggestion, based on column name or sample data.")


class TypeCheckReport(BaseModel):
    """The complete report of data type suggestions across a dataset."""
    summary: str = Field(description="A brief summary of the type check results.")
    suggestions: List[TypeSuggestion] = Field(description="A list of specific type suggestions found in the dataset's columns.")