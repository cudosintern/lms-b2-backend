from datetime import datetime
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Header, Form
import traceback
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.access_control.models.user_permission import UserPermission
from app.db.models import (
    IEMSUserOrg,
    IEMSUsers,
)
from ..middleware.auth_middleware import rbac_bypass
from ..utils.response_utils import ResponseUtils
from app.utils.comman_validation import check_common_validation
from app.access_control.auth.auth_handler import get_current_user
from app.utils.set_password_helper import set_private_password, set_salt
from ...core.database import get_db
from ..models.user import User
from ..models.user_role import UserRole
from ..models.user_role_permission import UserRolePermission
from ..models.module import Module
from ..models.module_route import ModuleRoute
from ..schemas.modules import ModulesData
from ..schemas.user import (
    UserCreateUpdatePass, UserResponse, UserResponseAll, UserUpdate
)
from app.access_control.middleware.auth_middleware import authorize

router = APIRouter(prefix="/users", tags=["Users"])


# Fetch all users (Paginated)
@router.get("/users_list", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    try:
        """Fetch all users with pagination."""
        users = db.query(User).filter(User.student_id.is_(None)).all()
        users_data = [
            UserResponse.model_validate(
                {
                    **user.__dict__,
                    "designation_id": (
                        str(user.designation_id)
                        if user.designation_id is not None
                        else None
                    ),
                    "user_dept_id": (
                        str(user.user_dept_id)
                        if user.user_dept_id is not None
                        else None
                    ),
                    "user_role_id": [
                        ur.user_role_id for ur in user.user_roles
                    ],
                    "org_id": (
                        str(user.org_id)
                        if user.org_id is not None
                        else None
                    ),
                }
            ).model_dump()
            for user in users
        ]

        return ResponseUtils.success(users_data)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Fetch all users (Paginated)
@router.get("/users_all_list", response_model=List[UserResponseAll])
def get_all_users(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    try:
        """Fetch all users with pagination."""
        # users = db.query(User).filter(User.student_id.is_(None)).all()
        users = db.query(User).filter(User.student_id.is_(None),User.super_admin != 1).all()
        users_data = [
            UserResponseAll.model_validate(
                {
                    **user.__dict__,
                    "designation_id": (
                        str(user.designation_id)
                        if user.designation_id is not None
                        else None
                    ),
                    "user_dept_id": (
                        str(user.user_dept_id)
                        if user.user_dept_id is not None
                        else None
                    ),
                    "user_role_id": [
                        ur.user_role_id for ur in user.user_roles
                    ],
                    # "org_id": [
                    #     str(user.org_id) if user.org_id is not None else None
                    # ],
                    "org_id": [
                        user.org_id
                    ] if user.org_id is not None else None,
                }
            ).model_dump()
            for user in users
        ]

        return ResponseUtils.success(users_data)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me/", response_model=UserResponse)
def get_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    # both ways we can access user id
    # user_id = int(user.user_id)
    user_id = int(user.id)
    user = (
        db.query(User)
        .options(joinedload(User.user_roles).joinedload(UserRole.role))
        .filter(User.id == user_id)
        .first()
    )
    user_data = UserResponse.model_validate(user).model_dump()

    return ResponseUtils.success(user_data)


# Fetch a single user by ID
@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Fetch user details by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = UserResponse.model_validate(user).model_dump()

    return ResponseUtils.success(user_data)


# Update user details
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)
):
    """Update user details."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_data.email:
        setattr(user, "email", user_data.email)

    db.commit()
    db.refresh(user)
    return ResponseUtils.success(user)


# Delete a user
@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return ResponseUtils.success(message="User deleted successfully")


@router.post("/unlock/{user_id}")
async def unlock_user(user_id: int, db: Session = Depends(get_db)):
    """Unlock a user manually (Admin Action)."""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    setattr(user, "is_locked", False)
    setattr(user, "failed_login_attempts", 0)
    setattr(user, "lockout_until", None)
    db.commit()

    return ResponseUtils.success(message="User account unlocked successfully")


@router.post("/modules")
@rbac_bypass.exempt("/users/modules")
def get_user_modules(
    user_id: Optional[str] = Form(None),
    user=Depends(authorize),
    db: Session = Depends(get_db)
):
    """
    Returns a list of active modules accessible to the specified user
    based on their roles.

    - If `user_id` is omitted, it defaults to the authenticated user.
    """
    if not user_id:
        user_id = user.id

    modules = (
        db.query(Module)
        .join(Module.routes)
        .join(ModuleRoute.role_permissions)
        .join(
            UserRole,
            UserRole.user_role_id == UserRolePermission.user_role_id
        )
        .filter(UserRole.user_id == user_id)
        .filter(UserRolePermission.status == 1)
        .filter(Module.status.is_(True))
        .distinct()
        .all()
    )

    module_data = [
        ModulesData.model_validate(m).model_dump()
        for m in modules
    ]
    return ResponseUtils.success(module_data)


@router.post("/save_user")
def save_user(
    user: UserCreateUpdatePass,
    current_user: User = Depends(get_current_user),
    org_id: int = Header(...),
    db: Session = Depends(get_db),
):
    user_id = current_user.user_id
    add_user = commit_user(db, user, user_id, org_id)

    return ResponseUtils.success(add_user, "User added successfully")


def set_private_password_with_user_pswd(username, password):
    salt = set_salt(username)
    password_hash = hashlib.sha1(f"{salt}{password}".encode()).hexdigest()
    return {"password": password_hash, "salt": salt}


def commit_user(
    db: Session, user: UserCreateUpdatePass, current_user_id: int, org_id: int
):
    check_duplication = check_common_validation(
        db, "user_email", user.email, user.id, org_id
    )
    if check_duplication == 0:
        raise HTTPException(
            status_code=400, detail="Email id already exists."
        )
        # return returnException("Email id already exists.")
    username_duplication = check_common_validation(
        db, "username", user.username, user.id, org_id
    )
    if username_duplication == 0:
        raise HTTPException(
            status_code=400, detail="Username already exists."
        )
        # return returnException("Email id already exists.")
    usermobile_duplication = check_common_validation(
        db, "usermobile", user.mobile, user.id, org_id
    )
    if usermobile_duplication == 0:
        raise HTTPException(
            status_code=400, detail="Mobile number already exists."
        )
        # return returnException("Email id already exists.")

    if user.id is None:
        if user.is_system_pswd == 1:
            password_info = set_private_password(user.username.strip())
        else:
            password_info = set_private_password_with_user_pswd(
                user.username.strip(), user.password.strip()
            )  # Generate password

        try:
            user_data = {
                "username": user.username.strip(),
                "first_name": user.first_name.strip(),
                "last_name": user.last_name.strip(),
                "user_type": user.user_type.strip(),
                "email": user.email.strip(),
                "user_dept_id": user.department,
                "mobile": user.mobile,
                "designation_id": user.designation,
                "salt": password_info["salt"],
                "password": password_info["password"],
                "org_id": org_id,
                "created_by": current_user_id,
                "create_date": datetime.now(),
                "title": user.title,
            }

            new_user = IEMSUsers(**user_data)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            # for role_id in user.role:

            #     # Add Home page access to the new user using ORM
            #     role_permissions = (
            #         db.query(UserRolePermission)
            #         .filter(
            #             UserRolePermission.user_role_id == role_id,
            #             UserRolePermission.org_id == user.org[0],
            #         )
            #         .all()
            #     )
            #     for permission in role_permissions:
            #         db.add(
            #             UserPermission(
            #                 user_role_id=role_id,
            #                 user_id=new_user.id,
            #                 menu_id=permission.menu_id,
            #                 permission_id=permission.permission_id,
            #                 org_id=user.org[0],
            #             )
            #         )
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    else:  # Update existing user
        user_in_db = db.query(IEMSUsers).filter(
            IEMSUsers.id == user.id
        ).first()
        if not user_in_db:
            raise HTTPException(
                status_code=400, detail="User not found"
            )
            # return returnException("User not found")

        if user.is_system_pswd == "Updating_pswd":
            password_info = set_private_password_with_user_pswd(
                user.username.strip(), user.password.strip()
            )  # Generate password
            user_data = {
                "password": password_info["password"],
            }

        user_data = {
            "username": user.username.strip(),
            "first_name": user.first_name.strip(),
            "last_name": user.last_name.strip(),
            "user_type": user.user_type.strip(),
            "email": user.email.strip(),
            "user_dept_id": user.department,
            "mobile": user.mobile,
            "org_id": org_id,
            "designation_id": user.designation,
            "modified_by": current_user_id,
            "modify_date": datetime.now(),
            "title": user.title,
        }

        for key, value in user_data.items():
            setattr(user_in_db, key, value)

        db.commit()

        # Remove existing roles and organizations
        db.query(UserRole).filter(
            UserRole.user_id == user.id, UserRole.org_id == user.org[0]
        ).delete()
        db.query(IEMSUserOrg).filter(IEMSUserOrg.user_id == user.id).delete()

        # Remove old permissions
        db.query(UserPermission).filter(
            UserPermission.user_id == user.id,
            UserPermission.org_id == user.org[0],
            # UserPermission.user_role_id != 0,
        ).delete()

        # Insert new permissions for the updated user
        # role_permissions = (
        #     db.query(UserRolePermission)
        #     .filter(
        #         UserRolePermission.user_role_id == user.role,
        #         UserRolePermission.org_id == user.org[0],
        #     )
        #     .all()
        # )

        # for permission in role_permissions:
        #     db.add(
        #         UserPermission(
        #             user_role_id=user.role,
        #             user_id=user.id,
        #             menu_id=permission.menu_id,
        #             permission_id=permission.permission_id,
        #             org_id=user.org[0],
        #         )
        #     )

    for role_id in user.role:
        # Insert new user role
        db.add(
            UserRole(
                user_id=user.id or new_user.id,
                user_role_id=role_id,
                org_id=user.org[0],
            )
        )

    # Insert user organizations
    for org_id in user.org:
        db.add(IEMSUserOrg(user_id=user.id or new_user.id, org_id=org_id))

    db.commit()

    response_data = {
        "id": user.id or new_user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "user_type": user.user_type,
        "mobile": user.mobile,
        "email": user.email,
        "department": user.department,
        "designation": user.designation,
        "status": 1,
        "create_date": user_in_db.create_date if user.id else datetime.now(),
        "created_by": user_in_db.created_by if user.id else current_user_id,
        "modify_date": datetime.now(),
        "modified_by": current_user_id,
        "title": user.title,
    }

    user_data = UserResponse.model_validate(response_data).model_dump()
    # user_data = response_data

    return user_data
    # return returnSuccess(response_data)
