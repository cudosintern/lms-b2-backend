from fastapi import APIRouter, Depends, HTTPException, Form
from typing import Optional
from ..utils.response_utils import ResponseUtils
from sqlalchemy.orm import Session
from datetime import datetime
from ..models.permission import Permission
from ..models.user_role_permission import UserRolePermission
from ...core.database import get_db
from ..schemas.permission import PermissionCreate, PermissionResponse

router = APIRouter(prefix="/permission", tags=["Permissions"])


def get_permission_form_data(
    permission_name: str = Form(...),
    method: str = Form(...),
    description: Optional[str] = Form(None),
    status: bool = Form(True),
) -> PermissionCreate:
    return PermissionCreate(
        permission_name=permission_name,
        method=method,
        description=description,
        status=status,
    )


# Get all permissions
@router.get("/get_all")
def get_all_permissions(
    permission_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    query = db.query(Permission).filter_by(status=True)
    if permission_id and permission_id.strip():
        query = query.filter(
            Permission.permission_id == int(permission_id)
        )
    result = query.all()

    permissions = [
        PermissionResponse.model_validate(per).model_dump()
        for per in result
    ]
    return ResponseUtils.success(permissions)


# Create a new permission
@router.post("/create")
def create_permission(
    permission: PermissionCreate = Depends(get_permission_form_data),
    db: Session = Depends(get_db)
):
    existing_permission = (
        db.query(Permission)
        .filter(
            Permission.permission_name == permission.permission_name,
            Permission.status
        )
        .first()
    )

    if existing_permission:
        raise HTTPException(
            status_code=400, detail="Permission already exists"
        )

    new_permission = Permission(
        **permission.dict(),
        created_at=datetime.utcnow(),
    )
    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)

    return ResponseUtils.success(message="Permission added successfully")


@router.delete("/delete")
def delete_permission(
    permission_id: str = Form(...),
    db: Session = Depends(get_db)
):
    if not permission_id:
        raise Exception("Invalid permission ID")
    permission = db.query(Permission).filter(
        Permission.permission_id == int(permission_id)
    ).scalar()

    if not permission:
        raise HTTPException(
            status_code=400, detail="Permission not found"
        )

    if not permission.status:
        raise HTTPException(
            status_code=400, detail="Permission already deleted"
        )

    permission.status = False
    db.commit()

    return ResponseUtils.success(message="Permission deleted successfully")


# Assign a permission to a role for a menu
@router.post("/role-menu-permissions")
def assign_role_menu_permission(
    role_id: int, menu_id: int, permission_id: int,
    db: Session = Depends(get_db)
):
    new_permission = UserRolePermission(
        user_role_id=role_id, menu_id=menu_id, permission_id=permission_id
    )
    db.add(new_permission)
    db.commit()
    return ResponseUtils.success(message="Permission assigned successfully")


# Remove a permission from a role for a menu
@router.delete("/role-menu-permissions/{access_id}")
def remove_role_menu_permission(access_id: int, db: Session = Depends(get_db)):
    permission = db.query(UserRolePermission).filter_by(
        access_id=access_id
    ).first()

    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    db.delete(permission)
    db.commit()
    return ResponseUtils.success(message="Permission removed successfully")
