from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class ContactBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    tags: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    tags: Optional[str] = None


class ContactRead(ContactBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
