from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base

# class LabCategory(Base):
#     __tablename__ = "cudos_lab_category"

#     lab_cat_id = Column(Integer, primary_key=True, autoincrement=True)
#     lab_cat_name = Column(String(100), nullable=False)
#     lab_cat_description = Column(String(2000), nullable=True)
#     created_by = Column(Integer, nullable=True)
#     modified_by = Column(Integer, nullable=True)
#     created_date = Column(DateTime, nullable=True, default=func.now())
#     modified_date = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())

class LabCategory(Base):
    __tablename__ = "cudos_master_type_details"

    lab_cat_id = Column("mt_details_id", Integer, primary_key=True, autoincrement=True)
    master_type_id = Column(Integer, default=9)
    lab_cat_name = Column("mt_details_name", String(100), nullable=False)
    org_type = Column(String(100), nullable=True)
    parent_id = Column(Integer, default=0, nullable=False)
    master_type_details_alias_name = Column(String(100), nullable=True)
    lab_cat_description = Column("mt_details_name_desc", String(2000), nullable=True)
    mtd_status = Column(Integer, default=0)
    created_by = Column(Integer, nullable=True)
    created_date = Column(DateTime, nullable=True, default=func.now())
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())
