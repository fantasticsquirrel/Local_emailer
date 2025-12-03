from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr


class QueuedEmailStatus(str, Enum):
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueuedEmailRead(BaseModel):
    id: int
    campaign_id: Optional[int] = None
    account_id: int
    from_address: EmailStr
    to_address: str
    subject: str
    body_html: str
    body_text: Optional[str] = None
    scheduled_for: datetime
    status: QueuedEmailStatus
    last_error: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
