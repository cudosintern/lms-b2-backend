from pydantic import BaseModel
from typing import Optional

class FieldSettingCreate(BaseModel):
    field_setting_id: Optional[int] = None
    field_setting_desc: str