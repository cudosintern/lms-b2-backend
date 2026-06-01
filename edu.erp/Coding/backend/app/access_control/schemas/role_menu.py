from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class RoleMenuBase(BaseModel):
    user_role_id: int
    menu_id: int
    status: Optional[int] = None
    created_at: Optional[datetime] = None


class RoleMenuCreate(RoleMenuBase):
    pass


class RoleMenuUpdate(RoleMenuBase):
    pass


class RoleMenu(RoleMenuBase):
    role_menu_id: int

    model_config = ConfigDict(from_attributes=True)
