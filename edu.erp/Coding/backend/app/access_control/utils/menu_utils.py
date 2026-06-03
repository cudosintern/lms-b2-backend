from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import or_
from fastapi import HTTPException
from ..models.user_role import UserRole
from ..models.role_menu import RoleMenu
from ..models.menu import Menu
from ..models.module import Module
import logging

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)


async def get_user_menus(user_id: int, m: str, db: Session):
    try:
        # Step 1: Get user's role IDs
        result = db.execute(
            select(UserRole.user_role_id).where(UserRole.user_id == user_id)
        )
        role_ids = [row[0] for row in result]

        if not role_ids:
            logger.warning(f"No roles found for user {user_id}")
            return []

        # Step 2: Get menu IDs from role_menus
        result = db.execute(
            select(RoleMenu.menu_id).where(RoleMenu.user_role_id.in_(role_ids),RoleMenu.status == 1)
        )
        menu_ids = {row[0] for row in result}

        if not menu_ids:
            logger.info(
                f"No menus assigned to user {user_id} through roles {role_ids}"
            )
            return []

        # Step 3: Fetch menus
        query = query = db.query(Menu).join(Menu.module).filter(
            Menu.menu_id.in_(menu_ids),
            or_(Menu.status == 1, Menu.status.is_(None))
        )

        # module wise
        if m and m.strip():
            query = query.filter(Module.code == m)

        menus = query.all()

        # Step 4: Build hierarchical menu tree
        menu_tree = build_menu_tree(menus)

        return menu_tree

    except Exception as e:
        logger.error(f"Failed to fetch menus for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch menus")


def build_menu_tree(menus):
    if not menus:
        return []

    def to_dict(menu):
        return {
            "menu_id": menu.menu_id,
            "menu_name": menu.menu_name,
            "name": menu.menu_name,
            "menu_url": menu.menu_url,
            "href": menu.menu_url,
            "menu_icon": menu.menu_icon,
            "parent": menu.parent,
            "show_menu": False if menu.show_menu is None else menu.show_menu,
            "menu_order": menu.menu_order,
            "module_id": menu.module_id,
            "subItems": [],
        }

    menu_dict = {menu.menu_id: to_dict(menu) for menu in menus}
    root_menus = []

    for menu in menus:
        if menu.parent and menu.parent in menu_dict:
            parent = menu_dict[menu.parent]
            parent["subItems"].append(menu_dict[menu.menu_id])
        else:
            root_menus.append(menu_dict[menu.menu_id])

    # Sort subItems recursively with None menu_order last
    def sort_subItems(menu):
        menu["subItems"].sort(
            key=lambda x: (x["menu_order"] is None, x["menu_order"])
        )
        for child in menu["subItems"]:
            sort_subItems(child)

    for root in root_menus:
        sort_subItems(root)

    # Sort root menus as well
    root_menus.sort(key=lambda x: (x["menu_order"] is None, x["menu_order"]))

    return root_menus
