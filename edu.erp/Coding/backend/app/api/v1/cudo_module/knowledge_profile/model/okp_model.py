from sqlalchemy import Column, Integer, String, Date
from app.core.database import Base


class OrgKnowledgeProfile(Base):
    __tablename__ = "cudos_org_knowledge_profiles"

    okp_id = Column(Integer, primary_key=True, index=True)
    okp_attr_code = Column(String(10), nullable=False)
    okp_attr_description = Column(String(5000), nullable=False)

    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=True)
    modified_date = Column(Date, nullable=True)
