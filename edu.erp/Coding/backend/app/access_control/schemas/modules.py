from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime
DATETIME_PRINT_FORMAT = '%Y-%m-%d %H:%M:%S'


class ModulesData(BaseModel):
    module_id: int
    module_name: str
    module_type: int
    code: str
    url: Optional[str] = None
    icon_name: Optional[str] = None
    description: Optional[str] = None
    status: bool
    created_at: Optional[datetime] = None

    @field_serializer("created_at")
    def serialize_datetime(self, v: Optional[datetime]) -> Optional[str]:
        return v.strftime(DATETIME_PRINT_FORMAT) if v else None

    model_config = ConfigDict(from_attributes=True)
