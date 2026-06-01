from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.access_control.models.user_role import UserRole
from app.access_control.schemas.user_roles import (
    UserRoleCreate, UserRoleOut, UserRoleUpdate
)
from app.core.database import get_db
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/user-roles", tags=["user_roles"])


@router.get("/get_user_list", response_model=list[UserRoleOut])
def read_all(db: Session = Depends(get_db)):
    return get_all_user_roles(db)


@router.post("/", response_model=UserRoleOut)
def create(role: UserRoleCreate, db: Session = Depends(get_db)):
    return create_user_role(db, role)


@router.get("/{role_id}", response_model=UserRoleOut)
def read(role_id: int, db: Session = Depends(get_db)):
    role = get_user_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="User role not found")
    return role


@router.put("/{role_id}", response_model=UserRoleOut)
def update(role_id: int, updates: UserRoleUpdate, db: Session = Depends(get_db)):
    updated = update_user_role(db, role_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="User role not found")
    return updated


@router.delete("/{role_id}", response_model=UserRoleOut)
def delete(role_id: int, db: Session = Depends(get_db)):
    deleted = delete_user_role(db, role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User role not found")
    return deleted


def create_user_role(db: Session, role: UserRoleCreate):
    db_role = UserRole(**role.dict())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def get_user_role(db: Session, role_id: int):
    return (
        db.query(UserRole).filter(UserRole.user_role_map_id == role_id).first()
    )


def get_all_user_roles(db: Session):
    # return db.query(UserRole).all()
    user_roles = db.query(UserRole).options(
        joinedload(UserRole.user),
        joinedload(UserRole.role),
        joinedload(UserRole.organisation)
    ).all()

    return_data = [
        {
            "user_role_map_id": role.user_role_map_id,
            "user_id": role.user_id,
            "user_role_id": role.user_role_id,
            "org_id": role.org_id,
            "username": f"{role.user.first_name} {role.user.last_name}" if role.user else None,
            "role_name": role.role.role_name if role.role else None,
            "role_des": role.role.description if role.role else None,
            "org_name": role.organisation.org_name if role.organisation else None
        }
        for role in user_roles
    ]

    return JSONResponse(content={
        "status": True,
        "data": return_data
    })


def update_user_role(db: Session, role_id: int, updates: UserRoleUpdate):
    db_role = (
        db.query(UserRole).filter(UserRole.user_role_map_id == role_id).first()
    )
    if not db_role:
        return None
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(db_role, key, value)
    db.commit()
    db.refresh(db_role)
    return db_role


def delete_user_role(db: Session, role_id: int):
    db_role = (
        db.query(UserRole).filter(UserRole.user_role_map_id == role_id).first()
    )
    if db_role:
        db.delete(db_role)
        db.commit()
    return db_role
