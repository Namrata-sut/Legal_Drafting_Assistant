from typing import List, Optional
from pydantic import BaseModel, Field

# Pydantic Schemas for AI Structured Output and API Validation ---
class ExtractedVariable(BaseModel):
    key: str = Field(..., description="The snake_case variable name, e.g., 'claimant_full_name'")
    label: str = Field(..., description="A human-readable label for the variable, e.g., 'Claimant's Full Name'")
    description: str = Field(..., description="A brief explanation of what this variable represents")
    example: Optional[str] = Field(None, description="A clear example value found in the text, e.g., 'John Doe'")
    required: bool = Field(..., description="Whether this variable is mandatory for the document")

class DocumentTemplate(BaseModel):
    title: str = Field(..., description="A concise, descriptive title for the legal document")
    description: str = Field(..., description="A one-sentence description of the document's purpose.")
    similaritytags: List[str] = Field(..., description="A list of 5-7 relevant keywords for vector search")
    variables: List[ExtractedVariable]
    bodymd: str = Field(..., description="The full document as Markdown with placeholders like {{key}}")

    class Config:
        orm_mode = True
