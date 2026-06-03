from typing import List, Optional
from pydantic import BaseModel


class ModuleRoutesdData(BaseModel):
    route_id: Optional[int] = None  # Now optional
    route_name: str
    route_path: str
    method: str
    module_id: int
    status: bool
    created_at: Optional[str] = None


class ModuleRoutesdDataForUpdate(BaseModel):
    route_id: int
    route_name: str
    route_path: str
    method: str
    module_id: int
    status: bool
    user_role_id: int
    created_at: Optional[str] = None
    permission_id: Optional[int]
    user_role_permission: Optional[int]


class BulkUserRolePermissionRequest(BaseModel):
    data: List[ModuleRoutesdDataForUpdate]
