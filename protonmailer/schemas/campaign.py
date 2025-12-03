from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ScheduleType(str, Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"


class ScheduleConfig(BaseModel):
    freq: str
    hour: Optional[int] = None
    minute: Optional[int] = None
    day_of_week: Optional[str] = None
    day_of_month: Optional[int] = None
    timezone: Optional[str] = None


class CampaignBase(BaseModel):
    name: str
    account_id: int
    template_id: int
    schedule_type: ScheduleType
    schedule_config: Optional[ScheduleConfig] = None
    target_tags: Optional[str] = None
    active: bool = True


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    account_id: Optional[int] = None
    template_id: Optional[int] = None
    schedule_type: Optional[ScheduleType] = None
    schedule_config: Optional[ScheduleConfig] = None
    target_tags: Optional[str] = None
    active: Optional[bool] = None


class CampaignRead(CampaignBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
