from sqlalchemy.orm import Session
from ..models.user_role import UserRole
from ..models.user_role_master import UserRoleMaster
from ..models.user_permission import UserPermission
from ..models.user_role_permission import UserRolePermission


# def has_module_access(
#     db: Session, user_id: int, module_id: int
# ) -> bool:
#     """Check if a user role has access to a module."""
#     return db.query(IEMSRoleModule).filter(
#         IEMSRoleModule.role_id == user_role_id,
#         IEMSRoleModule.module_id == module_id,
#         IEMSRoleModule.status.is_(True)
#     ).first() is not None


def has_direct_permission(
    db: Session, user_id: int, route_id: int
) -> bool:
    return db.query(UserPermission).filter_by(
        user_id=user_id,
        route_id=route_id, status=1
    ).first() is not None


def has_role_permission(
    db: Session, user_id: int, route_id
) -> bool:
    roles = db.query(UserRole).filter_by(user_id=user_id).all()
    role_ids = [r.user_role_id for r in roles]
    if not role_ids:
        return False

    return db.query(UserRolePermission).filter(
        UserRolePermission.user_role_id.in_(role_ids),
        UserRolePermission.route_id == route_id,
        UserRolePermission.status.is_(True)
    ).first() is not None


def has_role(
    db: Session, user_id: int, *roles
) -> bool:
    roles = db.query(UserRole).join(UserRole.role).filter(
        UserRole.user_id == user_id,
        UserRoleMaster.role_name.in_(roles)
    ).all()

    return roles is not None
