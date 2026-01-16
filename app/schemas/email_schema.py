from pydantic import BaseModel,EmailStr
from datetime import datetime


class EmailResponse(BaseModel):
    id:int
    email:EmailStr
    created_at:datetime

    class Config:
        orm_mode=True