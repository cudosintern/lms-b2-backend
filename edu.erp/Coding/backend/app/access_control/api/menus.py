from fastapi import APIRouter, Depends, HTTPException, Form
from datetime import datetime
from operator import and_
from sqlalchemy.orm import aliased
import traceback
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from app.access_control.models.menu import Menu
from app.access_control.models.role_menu import RoleMenu
from app.access_control.schemas.menus import (
    MenuCreate,
    MenuForRolesData,
    MenuResponse,
    MenuUpdate,
)
from ..middleware.auth_middleware import rbac_bypass
from ..middleware.auth_middleware import authorize
from ..utils.menu_utils import get_user_menus
from ..utils.response_utils import ResponseUtils
from ...core.database import get_db
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/menus", tags=["Menus"])


@router.post(
    "/get_assigned_menus"
)
@rbac_bypass.exempt("/menus/get_assigned_menus")
async def get_assigned_menus(
    m: Optional[str] = Form(None),
    user=Depends(authorize),
    db: Session = Depends(get_db)
):
    if m is None:
        raise HTTPException(
            status_code=400,
            detail="Module not mentioned to fetch menus"
        )

    user_id = int(user.id)

    data = await get_user_menus(user_id, m, db)

    return ResponseUtils.success(data)


@router.post("/create_menu")
def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    db_menu = Menu(**menu.dict())
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return ResponseUtils.success(db_menu, "Menu added successfully")


@router.get("/get_all_menu", response_model=List[MenuResponse])
def list_menus(db: Session = Depends(get_db)):
    # return db.query(Menu).all()
    menus = db.query(Menu).options(joinedload(Menu.module)).all()

    returnData = [
        {
            "menu_id": menu.menu_id,
            "menu_name": menu.menu_name,
            "menu_level": menu.menu_level,
            "menu_url": menu.menu_url,
            "module_id": menu.module_id,
            "parent": menu.parent,
            "module_name": menu.module.module_name if menu.module else None,
            "menu_order": menu.menu_order,
            "status": menu.status,
        }
        for menu in menus
    ]

    return ResponseUtils.success(returnData)


@router.get("/menus-by-user-role-id")
def fetch_menus_by_user_role_id(
    user_role_id: int,
    db: Session = Depends(get_db)
):
    # return db.query(ModuleRoute).all()
    try:
        ParentMenu = aliased(Menu)  # Alias for self-join

        menus = (
            db.query(
                Menu,
                RoleMenu,
                func.ifnull(ParentMenu.menu_name, Menu.menu_name).label(
                    "parent"
                ),  # Use parent's name, fallback to self
            )
            .outerjoin(
                RoleMenu,
                and_(
                    RoleMenu.menu_id == Menu.menu_id,
                    RoleMenu.user_role_id == user_role_id,  # keep in JOIN!
                ),
            )
            .outerjoin(
                ParentMenu,
                ParentMenu.menu_id
                == Menu.parent,  # Self-join to get parent menu
            )
            .options(joinedload(Menu.module))  # Eager load module to avoid N+1
            .all()
        )

        returnData = [
            {
                "menu_id": menu.menu_id,
                "menu_name": menu.menu_name,
                "role_menu_id": (
                    user_role_permission.role_menu_id if user_role_permission else None
                ),
                "menu_url": menu.menu_url,
                "module_id": menu.module_id,
                "module_name": (menu.module.module_name if menu.module else None),
                "parent": parent if parent else None,
                "status": (
                    user_role_permission.status if user_role_permission else False
                ),
            }
            for menu, user_role_permission, parent in menus
        ]

        return ResponseUtils.success(returnData)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_parent_menu_list")
def list_parent_menus(db: Session = Depends(get_db)):
    returnData = db.query(Menu).filter(
        Menu.parent.is_(None),
        Menu.show_menu == 1
    ).all()

    data = [
        {
            "menu_id": m.menu_id,
            "menu_name": m.menu_name,
            "menu_level": m.menu_level,
            "menu_url": m.menu_url,
            "module_id": m.module_id,
            "menu_order": m.menu_order,
            "status": m.status,
        }
        for m in returnData
    ]
    return ResponseUtils.success(data)


@router.get("/{menu_id}", response_model=MenuResponse)
def get_menu(menu_id: int, db: Session = Depends(get_db)):
    menu = db.query(Menu).filter_by(menu_id=menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    return ResponseUtils.success(menu)


@router.put("/update_menu/{menu_id}", response_model=MenuResponse)
def update_menu(
    menu_id: int,
    menu_update: MenuUpdate,
    db: Session = Depends(get_db)
):
    menu = db.query(Menu).filter_by(menu_id=menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    for key, value in menu_update.dict(exclude_unset=True).items():
        setattr(menu, key, value)
    db.commit()
    db.refresh(menu)

    return ResponseUtils.success(menu, "Menu updated successfully")


@router.delete("/delete-menu/{menu_id}")
def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    menu = db.query(Menu).filter_by(menu_id=menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    db.delete(menu)
    db.commit()
    return ResponseUtils.success(message="Menu deleted successfully")


@router.post("/update-or-add-menus-for-roles")
def update_or_add_menus_for_roles(
    # user_role_id: int,
    # org_id: int,
    menu_for_roles_data: MenuForRolesData,
    db: Session = Depends(get_db),
):
    try:
        if menu_for_roles_data.role_menu_id:
            # UPDATE logic
            db.query(RoleMenu).filter(
                RoleMenu.role_menu_id == menu_for_roles_data.role_menu_id
            ).update(
                {RoleMenu.status: menu_for_roles_data.status},
                synchronize_session=False,
            )
            db.commit()
            return ResponseUtils.success(
                message="Role menu updated successfully"
            )
        else:
            # INSERT logic
            new_user_role_permission = RoleMenu(
                status=True,
                user_role_id=menu_for_roles_data.user_role_id,
                menu_id=menu_for_roles_data.menu_id,
                created_at=datetime.now(),
            )
            db.add(new_user_role_permission)
            db.commit()
            return ResponseUtils.success(
                message="Role menu added successfully"
            )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
