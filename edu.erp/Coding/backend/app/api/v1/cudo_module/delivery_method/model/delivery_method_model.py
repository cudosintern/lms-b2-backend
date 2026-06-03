from sqlalchemy import Column, Integer, String, Date
from app.db.models import Base

class CudosDeliveryMethod(Base):
    __tablename__ = 'cudos_delivery_method'

    delivery_mtd_id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_mtd_name = Column(String(800), nullable=False)
    delivery_mtd_desc = Column(String(2000))
    bloom_level = Column(String(500), nullable=True) # Increased size for list
    created_by = Column(Integer)
    created_date = Column(Date)
    modified_by = Column(Integer)
    modified_date = Column(Date)

    @property
    def bloom_levels(self):
        if not self.bloom_level:
            return []
        return [x.strip() for x in self.bloom_level.split(',') if x.strip()]

    @bloom_levels.setter
    def bloom_levels(self, value):
        if isinstance(value, list):
            self.bloom_level = ','.join(value)
        elif value is None:
            self.bloom_level = None
        else:
            self.bloom_level = str(value)