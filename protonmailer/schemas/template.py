from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TemplateBase(BaseModel):
    name: str
    subject: str
    body_html: str
    body_text: Optional[str] = None


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None


class TemplateRead(TemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
