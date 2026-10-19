from datetime import datetime
from pydantic import BaseModel, EmailStr


class EmailSchema(BaseModel):
    message_id: str
    subject: str
    from_email: EmailStr
    body: str
    date: datetime

    class Config:
        from_attributes = True
