from typing import Optional
from pydantic import BaseModel, EmailStr


class EmailSchema(BaseModel):
    message_id: str
    subject: str
    from_email: EmailStr
    body: str
    
    class Config:
        from_attributes = True