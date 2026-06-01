from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class DeliveryMethodBase(BaseModel):
    delivery_mtd_name: str
    delivery_mtd_desc: Optional[str] = None
    bloom_levels: Optional[List[str]] = None

class CreateDeliveryMethod(DeliveryMethodBase):
    pass

class UpdateDeliveryMethod(BaseModel):
    delivery_mtd_name: Optional[str] = None
    delivery_mtd_desc: Optional[str] = None
    bloom_levels: Optional[List[str]] = None

class DeliveryMethodInDB(DeliveryMethodBase):
    delivery_mtd_id: int
    created_by: Optional[int] = None
    created_date: Optional[date] = None
    modified_by: Optional[int] = None
    modified_date: Optional[date] = None

    class Config:
        from_attributes = True