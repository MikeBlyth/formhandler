from pydantic import BaseModel
from typing import Optional, Any

class IntakeRecord(BaseModel):
    """
    Flexible model to consume the entire JSON data block from the forms app.
    """
    id: Optional[int] = None
    action: str = "LegalServer"  # Default action
    data: dict[str, Any]  # The full JSON data block from the forms app
