from typing import Optional
from pydantic import BaseModel, ConfigDict


class RoleCreate(BaseModel):
    role_name: str
    description: str
    inherits_from: Optional[int] = None
    status: bool = True


class RoleResponse(RoleCreate):
    user_role_id: int

    model_config = ConfigDict(from_attributes=True)


class UserMenuRoleRequest(BaseModel):
    role_id: Optional[int] = None
    user_role_id: Optional[int] = None
