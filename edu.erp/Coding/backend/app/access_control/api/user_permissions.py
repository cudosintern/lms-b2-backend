from datetime import datetime
from operator import and_
import traceback
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.orm import joinedload, aliased

from app.access_control.models.module_route import ModuleRoute
from app.access_control.models.permission import Permission
from app.access_control.models.user_permission import UserPermission
from app.access_control.schemas.user_permissions import (
    ModuleRoutesDataForUpdate,
    UserPermissionCreate,
    UserPermissionResponse,
    UserPermissionUpdate,
)

from ...core.database import get_db

router = APIRouter(prefix="/user-permissions", tags=["User Permissions"])


@router.post("/", response_model=UserPermissionResponse)
def create_user_permission(
    permission: UserPermissionCreate, db: Session = Depends(get_db)
):
    # Ensure uniqueness on (user_id, route_id)
    existing = (
        db.query(UserPermission)
        .filter(
            UserPermission.user_id == permission.user_id,
            UserPermission.route_id == permission.route_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Permission for this user and route already exists"
        )

    db_item = UserPermission(**permission.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/", response_model=List[UserPermissionResponse])
def get_user_permissions(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return db.query(UserPermission).offset(skip).limit(limit).all()


@router.get("/module-routes-by-user_id")
def fetch_module_routes_by_user_id(user_id: int, db: Session = Depends(get_db)):
    # return db.query(ModuleRoute).all()
    unique_permissions_subq = (
        db.query(
            func.trim(func.lower(Permission.method)).label("method"),
            func.min(Permission.permission_id).label("permission_id")
        )
        .group_by(func.trim(func.lower(Permission.method)))
    ).subquery("unique_permissions")

    UniquePermission = aliased(unique_permissions_subq)

    # Main query joining ModuleRoute, UserRolePermission and UniquePermission
    routes = (
        db.query(ModuleRoute, UserPermission, UniquePermission.c.permission_id.label("default_permission_id"))
        .outerjoin(
            UserPermission,
            and_(
                UserPermission.route_id == ModuleRoute.route_id,
                UserPermission.user_id == user_id,
            ),
        )
        .outerjoin(
            UniquePermission,
            func.trim(func.lower(ModuleRoute.method)) == UniquePermission.c.method
        )
        .options(joinedload(ModuleRoute.module))
        .all()
    )

    # Prepare response
    returnData = [
        {
            "route_id": module_route.route_id,
            "user_permission_id": (
                user_permission.user_permission_id
                if user_permission else None
            ),
            "permission_id": (
                user_permission.permission_id
                if user_permission else default_permission_id
            ),
            "route_name": module_route.route_name,
            "route_path": module_route.route_path,
            "method": module_route.method,
            "module_id": module_route.module_id,
            "module_name": (
                module_route.module.module_name
                if module_route.module else None
            ),
            "status": user_permission.status
            if user_permission else False,
        }
        for module_route, user_permission, default_permission_id in routes
    ]
    return JSONResponse(content={"status": True, "data": returnData})
    # routes = (
    #     db.query(ModuleRoute, UserPermission)
    #     .outerjoin(
    #         UserPermission,
    #         and_(
    #             UserPermission.route_id == ModuleRoute.route_id,
    #             UserPermission.user_id == user_id,  # keep in JOIN!
    #         ),
    #     )
    #     .options(joinedload(ModuleRoute.module))  # Eager load module to avoid N+1
    #     .all()
    # )

    # returnData = [
    #     {
    #         "route_id": module_route.route_id,
    #         "user_permission_id": (
    #             user_permission.user_permission_id if user_permission else None
    #         ),
    #         "permission_id": (
    #             user_permission.permission_id if user_permission else None
    #         ),
    #         "route_name": module_route.route_name,
    #         "route_path": module_route.route_path,
    #         "method": module_route.method,
    #         "module_id": module_route.module_id,
    #         "module_name": (
    #             module_route.module.module_name if module_route.module else None
    #         ),
    #         "status": user_permission.status if user_permission else False,
    #     }
    #     for module_route, user_permission in routes
    # ]

    # return JSONResponse(content={"status": True, "data": returnData})


@router.get("/{user_permission_id}", response_model=UserPermissionResponse)
def get_user_permission(user_permission_id: int, db: Session = Depends(get_db)):
    item = (
        db.query(UserPermission)
        .filter(UserPermission.user_permission_id == user_permission_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="User permission not found")
    return item


@router.put("/{user_permission_id}", response_model=UserPermissionResponse)
def update_user_permission(
    user_permission_id: int,
    update_data: UserPermissionUpdate,
    db: Session = Depends(get_db),
):
    item = (
        db.query(UserPermission)
        .filter(UserPermission.user_permission_id == user_permission_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="User permission not found")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{user_permission_id}")
def delete_user_permission(user_permission_id: int, db: Session = Depends(get_db)):
    item = (
        db.query(UserPermission)
        .filter(UserPermission.user_permission_id == user_permission_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="User permission not found")
    db.delete(item)
    db.commit()
    return {"message": "User permission deleted successfully"}


@router.post("/update-or-add-module-routes-by-user-id")
def update_or_add_module_routes(
    # user_role_id: int,
    # org_id: int,
    module_routes_data: ModuleRoutesDataForUpdate,
    org_id: int = Header(...),
    db: Session = Depends(get_db),
):
    try:
        if module_routes_data.user_permission_id:
            # UPDATE logic
            db.query(UserPermission).filter(
                UserPermission.user_permission_id
                == module_routes_data.user_permission_id
            ).update(
                {UserPermission.status: module_routes_data.status},
                synchronize_session=False,
            )
            db.commit()
            return JSONResponse(
                content={
                    "status": True,
                    "message": "User role module route updated successfully",
                }
            )
        else:
            # INSERT logic
            new_user_role_permission = UserPermission(
                status=True,
                user_id=module_routes_data.user_id,
                route_id=module_routes_data.route_id,
                permission_id=module_routes_data.permission_id,  # This can be None
                org_id=org_id,
                created_at=datetime.now(),
            )
            db.add(new_user_role_permission)
            db.commit()
            return JSONResponse(
                content={
                    "status": True,
                    "message": "User role module route added successfully",
                }
            )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
