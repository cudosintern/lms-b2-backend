from pydantic import BaseModel, ConfigDict
from typing import Optional


class MenuBase(BaseModel):
    menu_name: Optional[str]
    parent: Optional[int]
    menu_level: Optional[int]
    menu_url: Optional[str]
    parent_class: str
    menu_class: Optional[str]
    menu_icon: Optional[str]
    menu_order: Optional[int]
    show_menu: Optional[bool]
    status: Optional[bool]
    module_id: Optional[int]


class MenuCreate(MenuBase):
    pass


class MenuUpdate(MenuBase):
    pass


class MenuResponse(MenuBase):
    menu_id: int

    model_config = ConfigDict(from_attributes=True)


class MenuForRolesData(BaseModel):
    menu_id: int
    menu_name: str
    menu_url: str
    status: bool
    user_role_id: int
    created_at: Optional[str] = None
    role_menu_id: Optional[int]
