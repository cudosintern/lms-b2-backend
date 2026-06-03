from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.access_control.models.user_role_permission import UserRolePermission
from app.access_control.schemas.user_role_permissions import UserRolePermissionCreate, UserRolePermissionOut, UserRolePermissionUpdate
from app.core.database import get_db


router = APIRouter(prefix="/user-role-permissions", tags=["user_role_permissions"])


@router.post("/", response_model=UserRolePermissionOut)
def create(permission: UserRolePermissionCreate, db: Session = Depends(get_db)):
    return create_permission(db, permission)


@router.get("/{permission_id}", response_model=UserRolePermissionOut)
def read(permission_id: int, db: Session = Depends(get_db)):
    record = get_permission(db, permission_id)
    if not record:
        raise HTTPException(status_code=404, detail="Permission not found")
    return record


@router.get("/", response_model=list[UserRolePermissionOut])
def read_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_all_permissions(db, skip, limit)


@router.put("/{permission_id}", response_model=UserRolePermissionOut)
def update(
    permission_id: int, updates: UserRolePermissionUpdate, db: Session = Depends(get_db)
):
    updated = update_permission(db, permission_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Permission not found")
    return updated


@router.delete("/{permission_id}", response_model=UserRolePermissionOut)
def delete(permission_id: int, db: Session = Depends(get_db)):
    deleted = delete_permission(db, permission_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Permission not found")
    return deleted


def create_permission(db: Session, permission: UserRolePermissionCreate):
    db_permission = UserRolePermission(**permission.dict())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission


def get_permission(db: Session, permission_id: int):
    return (
        db.query(UserRolePermission)
        .filter(UserRolePermission.user_role_permission_id == permission_id)
        .first()
    )


def get_all_permissions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(UserRolePermission).offset(skip).limit(limit).all()


def update_permission(
    db: Session, permission_id: int, updates: UserRolePermissionUpdate
):
    db_obj = (
        db.query(UserRolePermission)
        .filter(UserRolePermission.user_role_permission_id == permission_id)
        .first()
    )
    if not db_obj:
        return None
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(db_obj, key, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_permission(db: Session, permission_id: int):
    db_obj = (
        db.query(UserRolePermission)
        .filter(UserRolePermission.user_role_permission_id == permission_id)
        .first()
    )
    if db_obj:
        db.delete(db_obj)
        db.commit()
    return db_obj
