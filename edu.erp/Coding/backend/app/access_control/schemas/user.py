from pydantic import BaseModel, Field, field_serializer, ConfigDict
from typing import Optional, List
from datetime import datetime
from ..schemas.user_roles import UserRoleOut
DATETIME_PRINT_FORMAT = '%Y-%m-%d %H:%M:%S'


class UserCreateUpdatePass(BaseModel):
    id: Optional[int] = None
    org: list
    role: Optional[List[int]] = None
    email: Optional[str] = None
    department: Optional[int] = None
    user_type: Optional[str] = None
    first_name: str
    last_name: Optional[str]
    mobile: Optional[str] = None
    username: Optional[str] = None
    designation: Optional[int] = None
    is_system_pswd: int
    password: Optional[str] = None
    title: str


class LoginSchema(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: Optional[int] = None
    # user_id alias to output in the API
    user_id: Optional[int] = Field(None, alias="user_id")
    email: Optional[str] = None
    department: Optional[int] = None
    user_type: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None
    username: Optional[str] = None
    designation: Optional[int] = None
    title: Optional[str] = None
    user_dept_id: Optional[int] = None
    designation_id: Optional[int] = None
    org_id: Optional[int] = None
    student_id: Optional[int] = None
    create_date: Optional[datetime] = None
    modify_date: Optional[datetime] = None
    user_role_id: Optional[List[int]] = None
    user_roles: List[UserRoleOut] = []

    @field_serializer("create_date", "modify_date")
    def serialize_datetime(self, v: Optional[datetime]) -> Optional[str]:
        return v.strftime(DATETIME_PRINT_FORMAT) if v else None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True  # required for user_id alias
    )


class UserUpdate(BaseModel):
    email: Optional[str] = None
    title: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserResponseAll(BaseModel):
    id: Optional[int] = None
    email: Optional[str] = None
    department: Optional[int] = None
    user_type: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None
    username: Optional[str] = None
    designation: Optional[int] = None
    title: Optional[str] = None
    user_dept_id: Optional[int] = None
    designation_id: Optional[int] = None
    org_id: Optional[List[int]] = None
    student_id: Optional[int] = None
    create_date: Optional[datetime] = None
    modify_date: Optional[datetime] = None
    user_role_id: Optional[List[int]] = None
    user_roles: List[UserRoleOut] = []

    @field_serializer("create_date", "modify_date")
    def serialize_datetime(self, v: Optional[datetime]) -> Optional[str]:
        return v.strftime(DATETIME_PRINT_FORMAT) if v else None

    model_config = ConfigDict(from_attributes=True)
