from datetime import datetime
from operator import and_
import traceback
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func

from app.access_control.models.permission import Permission
from ..utils.response_utils import ResponseUtils
from sqlalchemy.orm import Session, aliased

from app.access_control.models.module_route import ModuleRoute
from app.access_control.models.user_role_permission import UserRolePermission
from app.access_control.schemas.module_routes import (
    BulkUserRolePermissionRequest,
    ModuleRoutesdData,
    ModuleRoutesdDataForUpdate,
)
from sqlalchemy.orm import joinedload

from ...core.database import get_db

router = APIRouter(tags=["Module routes"])


@router.get("/module-routes")
def fetch_module_routes(db: Session = Depends(get_db)):
    # return db.query(ModuleRoute).all()
    routes = (
        db.query(ModuleRoute)
        .options(joinedload(ModuleRoute.module))  # Eager load module to avoid N+1
        .all()
    )

    returnData = [
        {
            "route_id": route.route_id,
            "route_name": route.route_name,
            "route_path": route.route_path,
            "method": route.method,
            "module_id": route.module_id,
            "module_name": route.module.module_name if route.module else None,
            "status": route.status,
        }
        for route in routes
    ]

    return ResponseUtils.success(returnData)


@router.post("/add-module-routes")
def post_module_routes_by_user(
    module_routes_data: ModuleRoutesdData, db: Session = Depends(get_db)
):
    new_module_routes_data = ModuleRoute(
        route_name=module_routes_data.route_name,
        route_path=module_routes_data.route_path,
        method=module_routes_data.method,
        module_id=module_routes_data.module_id,
        status=module_routes_data.status,
    )

    db.add(new_module_routes_data)
    db.commit()
    return ResponseUtils.success(
        message="Module Route added successfully"
    )


@router.put("/update-module-routes/{route_id}")
def update_module_routes(
    route_id: int, module_routes_data: ModuleRoutesdData,
    db: Session = Depends(get_db)
):
    db.query(ModuleRoute).filter(ModuleRoute.route_id == route_id).update(
        {
            ModuleRoute.route_name: module_routes_data.route_name,
            ModuleRoute.route_path: module_routes_data.route_path,
            ModuleRoute.method: module_routes_data.method,
            ModuleRoute.module_id: module_routes_data.module_id,
            ModuleRoute.status: module_routes_data.status,
        },
        synchronize_session=False,
    )
    db.commit()

    return ResponseUtils.success(
        message="Module Route updated successfully"
    )


@router.delete("/delete-module-routes/{route_id}")
def delete_module_routes(route_id: int, db: Session = Depends(get_db)):
    module_routes_log = (
        db.query(ModuleRoute).filter(ModuleRoute.route_id == route_id).first()
    )
    if not module_routes_log:
        raise HTTPException(status_code=404, detail="module route not found")
    db.delete(module_routes_log)
    db.commit()
    return ResponseUtils.success(
        message="Module Route removed successfully"
    )

@router.get("/module-routes-by-user_role_id")
def fetch_module_routes_by_user_role_id(
    user_role_id: int, db: Session = Depends(get_db)
):
    # Define subquery to get unique permissions (CTE replacement)
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
        db.query(ModuleRoute, UserRolePermission, UniquePermission.c.permission_id.label("default_permission_id"))
        .outerjoin(
            UserRolePermission,
            and_(
                UserRolePermission.route_id == ModuleRoute.route_id,
                UserRolePermission.user_role_id == user_role_id,
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
            "user_role_permission": (
                user_role_permission.user_role_permission_id
                if user_role_permission else None
            ),
            "permission_id": (
                user_role_permission.permission_id
                if user_role_permission else default_permission_id
            ),
            "route_name": module_route.route_name,
            "route_path": module_route.route_path,
            "method": module_route.method,
            "module_id": module_route.module_id,
            "module_name": (
                module_route.module.module_name
                if module_route.module else None
            ),
            "status": user_role_permission.status
            if user_role_permission else False,
        }
        for module_route, user_role_permission, default_permission_id in routes
    ]
    return ResponseUtils.success(returnData)


# @router.get("/module-routes-by-user_role_id")
# def fetch_module_routes_by_user_role_id(
#     user_role_id: int, db: Session = Depends(get_db)
# ):
#     # return db.query(ModuleRoute).all()
#     routes = (
#         db.query(ModuleRoute, UserRolePermission)
#         .outerjoin(
#             UserRolePermission,
#             and_(
#                 UserRolePermission.route_id == ModuleRoute.route_id,
#                 UserRolePermission.user_role_id == user_role_id,  # keep in JOIN!
#             ),
#         )
#         .options(joinedload(ModuleRoute.module))  # Eager load module to avoid N+1
#         .all()
#     )

#     returnData = [
#         {
#             "route_id": module_route.route_id,
#             "user_role_permission": (
#                 user_role_permission.user_role_permission_id
#                 if user_role_permission
#                 else None
#             ),
#             "permission_id": (
#                 user_role_permission.permission_id if user_role_permission else None
#             ),
#             "route_name": module_route.route_name,
#             "route_path": module_route.route_path,
#             "method": module_route.method,
#             "module_id": module_route.module_id,
#             "module_name": (
#                 module_route.module.module_name if module_route.module else None
#             ),
#             "status": user_role_permission.status if user_role_permission else False,
#         }
#         for module_route, user_role_permission in routes
#     ]

#     return ResponseUtils.success(returnData)


@router.post("/update-or-add-module-routes")
def update_or_add_module_routes(
    # user_role_id: int,
    # org_id: int,
    module_routes_data: ModuleRoutesdDataForUpdate,
    org_id: int = Header(...),
    db: Session = Depends(get_db),
):
    try:
        if module_routes_data.user_role_permission:
            # UPDATE logic
            db.query(UserRolePermission).filter(
                UserRolePermission.user_role_permission_id
                == module_routes_data.user_role_permission
            ).update(
                {UserRolePermission.status: module_routes_data.status},
                synchronize_session=False,
            )
            db.commit()
            return ResponseUtils.success(
                message="User role module route updated successfully"
            )
        else:
            # INSERT logic
            new_user_role_permission = UserRolePermission(
                status=True,
                user_role_id=module_routes_data.user_role_id,
                route_id=module_routes_data.route_id,
                permission_id=module_routes_data.permission_id,  # This can be None
                org_id=org_id,
                created_at=datetime.now()
            )
            db.add(new_user_role_permission)
            db.commit()
            return ResponseUtils.success(
                message="User role module route added successfully"
            )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-update-or-add-module-routes")
def bulk_update_or_add_module_routes(
    request_data: BulkUserRolePermissionRequest,
    org_id: int = Header(...),
    db: Session = Depends(get_db),
):
    try:
        created_count = 0
        updated_count = 0
        current_time = datetime.now()

        for item in request_data.data:
            if item.user_role_permission:  # UPDATE
                db.query(UserRolePermission).filter(
                    UserRolePermission.user_role_permission_id == item.user_role_permission
                ).update(
                    {UserRolePermission.status: item.status},
                    synchronize_session=False
                )
                updated_count += 1
            else:  # INSERT
                new_record = UserRolePermission(
                    user_role_id=item.user_role_id,
                    route_id=item.route_id,
                    permission_id=item.permission_id,
                    org_id=org_id,
                    status=item.status if item.status is not None else True,
                    created_at=current_time
                )
                db.add(new_record)
                created_count += 1

        db.commit()

        message_parts = []
        if created_count > 0:
            message_parts.append(f"{created_count} module route(s) inserted")
        if updated_count > 0:
            message_parts.append(f"{updated_count} module route(s) updated successfully")

        message = ", ".join(message_parts)

        return ResponseUtils.success(message=message)


    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))