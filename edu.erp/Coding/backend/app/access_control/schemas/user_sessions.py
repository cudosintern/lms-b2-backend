from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class SessionBase(BaseModel):
    user_id: int
    access_token: str
    refresh_token: str
    created_at: Optional[datetime] = None
    expires_at: datetime
    last_active_at: Optional[datetime] = None
    ip_address: str
    user_agent: str


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    last_active_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SessionOut(SessionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
