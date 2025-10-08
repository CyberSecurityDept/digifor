from pydantic import BaseModel
from typing import Optional

class GroupCreate(BaseModel):
    analytic_name: str
    type: Optional[str] = None
    notes: Optional[str] = None