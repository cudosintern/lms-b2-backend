from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from .....db.models import CudosMapLevelWeightage
from .....utils.auth_helper import get_current_user
from .....utils.http_return_helper import returnSuccess, returnException
from .....core.database import get_db
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()


class MapLevelWeightageItem(BaseModel):
    mlw_id: Optional[int] = None
    map_level_name: str
    map_level_name_alias: Optional[str] = None
    map_level_short_form: Optional[str] = None
    map_level: Optional[int] = None
    map_level_weightage: float
    status: int

@router.get("/get_map_level_weightage")
def get_map_level_weightage(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        items = db.query(CudosMapLevelWeightage).all()
        
        result = []
        for item in items:
            result.append({
                "mlw_id": item.mlw_id,
                "map_level_name": item.map_level_name,
                "map_level_name_alias": item.map_level_name_alias,
                "map_level_short_form": item.map_level_short_form,
                "map_level": item.map_level,
                "map_level_weightage": item.map_level_weightage,
                "status": item.status
            })
        return returnSuccess(result)
    except Exception as e:
        return returnException(str(e))

@router.post("/save_map_level_weightage")
def save_map_level_weightage(
    request: List[MapLevelWeightageItem],
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        user_id = current_user.get("user_id")
        
        for item in request:
            if item.mlw_id:
                # Update
                record = db.query(CudosMapLevelWeightage).filter(CudosMapLevelWeightage.mlw_id == item.mlw_id).first()
                if record:
                    record.map_level_name = item.map_level_name
                    record.map_level_name_alias = item.map_level_name_alias
                    record.map_level_short_form = item.map_level_short_form
                    # record.map_level = item.map_level # Optional update
                    record.map_level_weightage = item.map_level_weightage
                    record.status = item.status
                    record.modified_by = user_id
                    record.modified_date = datetime.now()
            else:
                # Create
                new_record = CudosMapLevelWeightage(
                    map_level_name=item.map_level_name,
                    map_level_name_alias=item.map_level_name_alias,
                    map_level_short_form=item.map_level_short_form,
                    map_level=item.map_level,
                    map_level_weightage=item.map_level_weightage,
                    status=item.status,
                    created_by=user_id,
                    created_date=datetime.now()
                )
                db.add(new_record)
        
        db.commit()
        return returnSuccess("Updated successfully")
    except Exception as e:
        db.rollback()
        return returnException(str(e))
