from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime, date

DATETIME_PRINT_FORMAT = '%Y-%m-%d %H:%M:%S'


class PoTypeBase(BaseModel):
    """Base schema for Program Outcome Type"""
    po_type_name: str
    po_type_description: Optional[str] = None
    status: Optional[int] = 1

    @field_validator('po_type_name')
    @classmethod
    def validate_po_type_name(cls, v):
        """Validate Program Outcome Type Name field"""
        if not v or not v.strip():
            raise ValueError('Program Outcome Name is required')
        if len(v.strip()) > 255:
            raise ValueError('Program Outcome Name must not exceed 255 characters')
        return v.strip()

    @field_validator('po_type_description')
    @classmethod
    def validate_po_type_description(cls, v):
        """Validate Program Outcome Description field"""
        if v and len(v.strip()) > 1000:
            raise ValueError('Description must not exceed 1000 characters')
        return v.strip() if v else None


class PoTypeCreate(PoTypeBase):
    """Schema for creating a new Program Outcome Type"""
    pass


class PoTypeUpdate(PoTypeBase):
    """Schema for updating a Program Outcome Type"""
    po_type_name: Optional[str] = None  # Make optional for updates
    po_type_description: Optional[str] = None


class PoTypeResponse(PoTypeBase):
    """Schema for Program Outcome Type response"""
    po_type_id: int
    created_by: int
    created_date: Optional[datetime] = None
    modified_by: Optional[int] = None
    modified_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)
        if self.created_date and isinstance(self.created_date, datetime):
            self.created_date = self.created_date.strftime(DATETIME_PRINT_FORMAT)
        if self.modified_date and isinstance(self.modified_date, datetime):
            self.modified_date = self.modified_date.strftime(DATETIME_PRINT_FORMAT)
