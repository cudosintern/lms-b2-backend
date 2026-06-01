from pydantic import BaseModel
from typing import Optional

# --- Main Schema (Used for Saving & Editing) ---
class CurriculumDeliveryMethodSchema(BaseModel):
    crclm_dm_id: Optional[int] = None
    crclm_id: int
    
    # User Input Fields
    delivery_mtd_name: str
    delivery_mtd_desc: Optional[str] = None
    bloom_id: Optional[int] = None
    
    # Read-Only Field (for UI display)
    bloom_level_name: Optional[str] = None

    class Config:
        from_attributes = True

# --- Delete Schema ---
class DeliveryMethodDeleteSchema(BaseModel):
    crclm_dm_id: int