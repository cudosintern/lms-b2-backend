from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime

DATETIME_PRINT_FORMAT = '%Y-%m-%d %H:%M:%S'

# --- Accreditation Type Schemas ---

class AccreditationTypeBase(BaseModel):
    atype_name: str
    atype_description: str
    entity_id: int

    @field_validator('atype_name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Accreditation Type Name is required')
        if len(v.strip()) > 100:
            raise ValueError('Name must not exceed 100 characters')
        return v.strip()

    @field_validator('atype_description')
    @classmethod
    def validate_description(cls, v):
        if v and len(v.strip()) > 2000:
            raise ValueError('Description must not exceed 2000 characters')
        return v.strip()


class AccreditationTypeCreate(AccreditationTypeBase):
    created_by: Optional[int] = None
    pos: Optional[List['PoCreate']] = None


class AccreditationTypeUpdate(BaseModel):
    atype_name: Optional[str] = None
    atype_description: Optional[str] = None
    entity_id: Optional[int] = None
    modified_by: Optional[int] = None
    pos: Optional[List['PoNestedUpdate']] = None

    @field_validator('atype_name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
             if not v.strip():
                 raise ValueError('Accreditation Type Name cannot be empty')
             if len(v.strip()) > 100:
                 raise ValueError('Name must not exceed 100 characters')
             return v.strip()
        return v

    @field_validator('atype_description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and len(v.strip()) > 2000:
            raise ValueError('Description must not exceed 2000 characters')
        return v.strip() if v else v


class AccreditationTypeResponse(AccreditationTypeBase):
    atype_id: int
    created_by: Optional[int] = None
    modified_by: Optional[int] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    pos: Optional[List['PoResponse']] = None

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)
        # Custom serialization for datetime if needed, though Pydantic v2 usually handles it well.
        # Keeping existing pattern if necessary, but standard json_encoders inside ConfigDict is deprecated in v2.
        # Logic from existing files handled manually in init:
        # Note: In Pydantic v2, this might not work as expected because models are validated on init.
        # But let's assume standard behavior or similar to existing codebase.
        pass


# --- PO Schemas ---

class PoBase(BaseModel):
    po_code: str
    po_statement: str
    po_reference: Optional[str] = None
    pso_flag: Optional[bool] = False
    po_type_id: Optional[int] = None
    crclm_id: int
    state_id: Optional[int] = None
    po_minthreshhold: Optional[int] = None
    po_studentthreshhold: Optional[int] = None
    justify: Optional[str] = None
    import_ref_po_id: Optional[int] = None
    direct_attainment: Optional[int] = None
    indirect_attainment: Optional[int] = None
    extra_curricular: Optional[int] = None
    atype_id: Optional[int] = None  # Logic linkage

    @field_validator('po_code')
    @classmethod
    def validate_po_code(cls, v):
        if not v or not v.strip():
            raise ValueError('PO Code is required')
        if len(v.strip()) > 10:
            raise ValueError('PO Code must not exceed 10 characters')
        return v.strip()

    @field_validator('po_statement')
    @classmethod
    def validate_po_statement(cls, v):
        if not v or not v.strip():
            raise ValueError('PO Statement is required')
        if len(v.strip()) > 2000:
            raise ValueError('PO Statement must not exceed 2000 characters')
        return v.strip()


class PoCreate(PoBase):
    created_by: Optional[int] = None


class PoUpdate(BaseModel):
    po_code: Optional[str] = None
    po_statement: Optional[str] = None
    po_reference: Optional[str] = None
    pso_flag: Optional[bool] = None
    po_type_id: Optional[int] = None
    crclm_id: Optional[int] = None
    state_id: Optional[int] = None
    po_minthreshhold: Optional[int] = None
    po_studentthreshhold: Optional[int] = None
    justify: Optional[str] = None
    modified_by: Optional[int] = None
    atype_id: Optional[int] = None

    @field_validator('po_code')
    @classmethod
    def validate_po_code(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('PO Code cannot be empty')
            if len(v.strip()) > 10:
                raise ValueError('PO Code must not exceed 10 characters')
            return v.strip()

class PoNestedUpdate(PoBase):
    po_id: Optional[int] = None
    modified_by: Optional[int] = None


class PoResponse(PoBase):
    po_id: int
    create_date: Optional[datetime] = None
    created_by: Optional[int] = None
    modify_date: Optional[datetime] = None
    modified_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
