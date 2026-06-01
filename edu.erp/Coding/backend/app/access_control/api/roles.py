from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..models.user_role_master import UserRoleMaster
from ...core.database import get_db
from ..schemas.role import RoleCreate, RoleResponse
from ..middleware.auth_middleware import role_required

router = APIRouter(tags=["User role master"])


# Get all roles
@router.get(
    "/roles",
    # dependencies=[Depends(role_required('COE', 'Staff'))]
)
def get_roles(db: Session = Depends(get_db)):
    roles = db.query(UserRoleMaster).filter(UserRoleMaster.status).all()
    return {"status": True, "data": roles}


# Get a specific role by ID
@router.get("/roles/{role_id}", response_model=RoleResponse)
def get_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(UserRoleMaster).filter(
        UserRoleMaster.user_role_id == role_id
    ).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


# Create a new role
@router.post("/roles", response_model=RoleResponse)
def create_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    existing_role = db.query(UserRoleMaster).filter(
        UserRoleMaster.role_name == role_data.role_name
    ).first()

    if existing_role:
        raise HTTPException(status_code=400, detail="Role already exists")

    new_role = UserRoleMaster(
        role_name=role_data.role_name,
        description=role_data.description,
        inherits_from=role_data.inherits_from,
        status=role_data.status
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


# Update an existing role
@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int, role_data: RoleCreate, db: Session = Depends(get_db)
):
    description = role_data.description
    updated_rows = db.query(UserRoleMaster).filter(
        UserRoleMaster.user_role_id == role_id
    ).update({
        UserRoleMaster.role_name: role_data.role_name,
        UserRoleMaster.description: description,
        UserRoleMaster.inherits_from: role_data.inherits_from,
        UserRoleMaster.status: role_data.status
    }, synchronize_session=False)

    if updated_rows == 0:
        raise HTTPException(status_code=404, detail="Role not found")

    db.commit()
    return {"message": "Role updated successfully"}


# Delete a role (soft delete by setting `status = False`)
@router.delete("/roles/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(UserRoleMaster).filter(
        UserRoleMaster.user_role_id == role_id
    ).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    setattr(role, "status", False)  # Soft delete
    db.commit()
    return {"message": "Role deleted successfully"}
