from sqlalchemy import (
    Column, Integer, ForeignKey, Index
)
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship
from ...core.database import Base


class UserRole(Base):
    __tablename__ = "iems_user_roles"
    __table_args__ = (
        Index(
            "ix_user_roles_user_role", "user_id", "user_role_id", unique=True
        ),
    )

    user_role_map_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        INTEGER(unsigned=True), ForeignKey("iems_users.id"), nullable=False
    )
    user_role_id = Column(
        INTEGER(unsigned=True),
        ForeignKey("iems_user_role_master.user_role_id"), nullable=False
    )
    org_id = Column(
        INTEGER(unsigned=True),
        ForeignKey("iems_organisation.org_id"), nullable=False
    )

    user = relationship("User", back_populates="user_roles")
    role = relationship(
        "UserRoleMaster",
        # foreign_keys=[user_role_id],
        back_populates="user_roles"
    )
    organisation = relationship("Organisation", back_populates="user_roles")

    @property
    def role_name(self):
        return self.role.role_name if self.role else None

    # def to_dict(self):
    #     data = {column.name: getattr(self, column.name)
    #             for column in self.__table__.columns}
    #     data["role_name"] = self.role.role_name if self.role else None
    #     return data
