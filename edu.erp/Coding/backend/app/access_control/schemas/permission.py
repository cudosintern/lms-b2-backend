from pydantic import BaseModel, ConfigDict, Field, field_serializer
from datetime import datetime
from typing import Optional
DATETIME_PRINT_FORMAT = '%Y-%m-%d %H:%M:%S'


class PermissionCreate(BaseModel):
    permission_name: str
    method: Optional[str] = None
    description: Optional[str] = None
    status: bool = Field(True)


class PermissionResponse(PermissionCreate):
    permission_id: int
    created_at: Optional[datetime] = None

    @field_serializer("created_at")
    def serialize_datetime(self, v: Optional[datetime]) -> Optional[str]:
        return v.strftime(DATETIME_PRINT_FORMAT) if v else None

    model_config = ConfigDict(from_attributes=True)
