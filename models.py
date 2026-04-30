from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class IntakeRecord(BaseModel):
    id: Optional[int] = None
    full_name: str
    first_name: str
    last_name: str
    date_of_birth: str
    a_number: str = Field(..., description="Exact match A#")
    intake_date: str
    phone_number: Optional[str] = None
    case_summary: Optional[str] = None

class LegalServerExport(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    case_summary_custom_99: str
    a_number_internal: str
