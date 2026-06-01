from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class UserRolePermissionBase(BaseModel):
    user_role_id: int
    route_id: int
    permission_id: Optional[int] = None
    status: Optional[int] = None
    org_id: Optional[int] = None
    created_at: Optional[datetime] = None


class UserRolePermissionCreate(UserRolePermissionBase):
    pass


class UserRolePermissionUpdate(BaseModel):
    permission_id: Optional[int] = None
    status: Optional[int] = None
    org_id: Optional[int] = None


class UserRolePermissionOut(UserRolePermissionBase):
    user_role_permission_id: int

    model_config = ConfigDict(from_attributes=True)
