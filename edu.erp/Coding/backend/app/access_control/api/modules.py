from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.access_control.schemas.modules import ModulesData
from ..models.module import Module
from ..utils.response_utils import ResponseUtils
from ...core.database import get_db

router = APIRouter(tags=["Modules"])


@router.get("/modules")
def get_modules(
    db: Session = Depends(get_db)
):
    get_modules = db.query(Module).filter(Module.status.is_(True)).all()

    module_data = [
        ModulesData.model_validate(m).model_dump()
        for m in get_modules
    ]
    return ResponseUtils.success(module_data)


@router.post("/modules")
def post_modules_by_user(
    modules_data: ModulesData, db: Session = Depends(get_db)
):
    new_modules_data = Module(
        module_name=modules_data.module_name,
        description=modules_data.description,
        status=modules_data.status,
        created_at=modules_data.created_at
    )

    db.add(new_modules_data)
    db.commit()
    return ResponseUtils.success(message="Module added successfully")


@router.put("/modules/{module_id}")
def update_modules(
    module_id: int, modules_data: ModulesData, db: Session = Depends(get_db)
):
    db.query(Module).filter(Module.module_id == module_id).update(
        {
            Module.module_id: modules_data.module_id,
            Module.module_name: modules_data.module_name,
            Module.description: modules_data.description,
            Module.status: modules_data.status,
            Module.created_at: modules_data.created_at,
        },
        synchronize_session=False,
    )

    return ResponseUtils.success(message="Module updated successfully")


@router.delete("/modules/{module_id}")
def delete_modules(module_id: int, db: Session = Depends(get_db)):
    modules_log = db.query(Module).filter(Module.route_id == module_id).first()
    if not modules_log:
        raise HTTPException(status_code=404, detail="modules not found")
    db.delete(modules_log)
    db.commit()
    return ResponseUtils.success(message="Module removed successfully")
