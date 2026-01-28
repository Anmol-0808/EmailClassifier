from pydantic import BaseModel,EmailStr
from datetime import datetime
from typing import Optional

class EmailResponse(BaseModel):
    id: int
    email: EmailStr
    body: str

    email_type: str
    ai_email_type: Optional[str]
    confidence_score: Optional[float]
    ai_reason: Optional[str]
    model_version: Optional[str]

    is_ai_generated: bool
    needs_review: bool
    is_active: bool

    created_at: datetime
    received_at: datetime

    class Config:
        orm_mode = True
