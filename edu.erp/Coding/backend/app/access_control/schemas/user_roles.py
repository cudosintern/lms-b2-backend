from pydantic import BaseModel, ConfigDict
from typing import Optional


class UserRoleBase(BaseModel):
    user_id: int
    user_role_id: int
    org_id: int
    role_name: Optional[str] = None


class UserRoleCreate(UserRoleBase):
    pass


class UserRoleUpdate(BaseModel):
    org_id: Optional[int] = None


class UserRoleOut(UserRoleBase):
    user_role_map_id: int

    model_config = ConfigDict(from_attributes=True)
