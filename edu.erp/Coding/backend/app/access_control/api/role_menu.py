from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.access_control.schemas.role_menu import (
    RoleMenu,
    RoleMenuCreate,
    RoleMenuUpdate,
)
from ...core.database import get_db

router = APIRouter(prefix="/role-menus", tags=["Role Menus"])


@router.post("/", response_model=RoleMenu)
def create_role_menu(role_menu: RoleMenuCreate, db: Session = Depends(get_db)):
    db_role_menu = RoleMenu(**role_menu.dict())
    db.add(db_role_menu)
    db.commit()
    db.refresh(db_role_menu)
    return db_role_menu


@router.get("/", response_model=List[RoleMenu])
def get_role_menus(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(RoleMenu).offset(skip).limit(limit).all()


@router.get("/{role_menu_id}", response_model=RoleMenu)
def get_role_menu(role_menu_id: int, db: Session = Depends(get_db)):
    db_item = db.query(RoleMenu).filter(RoleMenu.role_menu_id == role_menu_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Role menu not found")
    return db_item


@router.put("/{role_menu_id}", response_model=RoleMenu)
def update_role_menu(
    role_menu_id: int, role_menu: RoleMenuUpdate, db: Session = Depends(get_db)
):
    db_item = db.query(RoleMenu).filter(RoleMenu.role_menu_id == role_menu_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Role menu not found")
    for key, value in role_menu.dict(exclude_unset=True).items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{role_menu_id}")
def delete_role_menu(role_menu_id: int, db: Session = Depends(get_db)):
    db_item = db.query(RoleMenu).filter(RoleMenu.role_menu_id == role_menu_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Role menu not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Role menu deleted successfully"}
