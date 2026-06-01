from pydantic import BaseModel
from typing import Optional

# --- Main Schema (Used for Saving & Editing) ---
class BloomLevelSchema(BaseModel):
    bloom_id: Optional[int] = None 
    bld_id: int
    level: str 
    learning: str 
    description: Optional[str] = None
    bloom_actionverbs: Optional[str] = None

    class Config:
        from_attributes = True

# --- Delete Schema (Used for Deleting) ---
class BloomLevelDeleteSchema(BaseModel):
    bloom_id: int