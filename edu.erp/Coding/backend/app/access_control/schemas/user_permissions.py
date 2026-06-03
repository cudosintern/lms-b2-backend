from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class UserPermissionBase(BaseModel):
    user_id: int
    route_id: int
    permission_id: Optional[int] = None
    status: Optional[int] = None
    org_id: Optional[int] = None
    created_at: Optional[datetime] = None


class UserPermissionCreate(UserPermissionBase):
    pass


class UserPermissionUpdate(UserPermissionBase):
    pass


class UserPermissionResponse(UserPermissionBase):
    user_permission_id: int

    model_config = ConfigDict(from_attributes=True)


class ModuleRoutesDataForUpdate(BaseModel):
    route_id: int
    route_name: str
    route_path: str
    method: str
    module_id: int
    status: bool
    user_id: int
    created_at: Optional[str] = None
    permission_id: Optional[int]
    user_permission_id: Optional[int]
