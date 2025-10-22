from pydantic import BaseModel, Field
from typing import Optional

class PlagiarismCheckRequest(BaseModel):
    original_text: Optional[str] = Field(None, description="Original Turkmen text")
    suspect_text: Optional[str] = Field(None, description="Suspect Turkmen text")
    original_file: Optional[bytes] = Field(None, description="Original file (PDF/DOCX) as bytes")
    suspect_file: Optional[bytes] = Field(None, description="Suspect file (PDF/DOCX) as bytes")