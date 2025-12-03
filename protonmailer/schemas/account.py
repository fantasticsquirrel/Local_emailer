from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class AccountBase(BaseModel):
    display_name: str
    email_address: EmailStr
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password_encrypted: str
    use_ssl: bool = False
    use_tls: bool = True


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    display_name: Optional[str] = None
    email_address: Optional[EmailStr] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password_encrypted: Optional[str] = None
    use_ssl: Optional[bool] = None
    use_tls: Optional[bool] = None


class AccountRead(AccountBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
