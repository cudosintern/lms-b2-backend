from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class BloomDomain(Base):
    __tablename__ = 'cudos_bloom_domain'

    bld_id = Column(Integer, primary_key=True, autoincrement=True)
    bld_name = Column(String(100), nullable=False)
    bld_acronym = Column(String(50), nullable=False)
    bld_description = Column(Text, nullable=True)
    status = Column(Integer, default=1)
    bld_code = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    create_date= Column(DateTime, default=func.current_timestamp())
    modify_date= Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())