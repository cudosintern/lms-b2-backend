from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db.models import BloomLevel
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess, returnException
from app.core.database import get_db
from pydantic import BaseModel
from typing import Optional
from app.api.v1.cudo_module.bloom_level.schema.bloom_level_schema import BloomLevelSchema, BloomLevelDeleteSchema

router = APIRouter()

# --- API 1: Get All Levels ---
@router.get("/get_bloom_levels")
def get_bloom_levels(
    org_id: int = Header(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        results = db.query(BloomLevel).all()
        return returnSuccess(results)
    except Exception as e:
        return returnException(str(e))

# --- API 2: Save / Update Level ---
@router.post("/save_bloom_level")
def save_bloom_level(
    request: BloomLevelSchema,
    org_id: int = Header(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("user_id")
        if user_id is None:
            user_id = 0
        duplicate_check = db.query(BloomLevel).filter(
            BloomLevel.level == request.level,
            BloomLevel.bloom_id != (request.bloom_id if request.bloom_id else -1)
        ).first() # type: ignore

        if duplicate_check:
            return returnException(f"Level '{request.level}' already exists!")

        if request.bloom_id:
            level_obj = db.query(BloomLevel).filter(BloomLevel.bloom_id == request.bloom_id).first() # type: ignore
            
            if not level_obj:
                return returnException("Bloom Level not found")
    
            level_obj.level = request.level # type: ignore
            level_obj.learning = request.learning # type: ignore
            level_obj.description = request.description # type: ignore
            level_obj.bloom_actionverbs = request.bloom_actionverbs # type: ignore
            level_obj.bld_id = request.bld_id # type: ignore
            level_obj.modified_by = user_id # type: ignore
            
        else:
            # --- CREATE NEW ---
            level_obj = BloomLevel(
                level=request.level,
                learning=request.learning,
                description=request.description,
                bloom_actionverbs=request.bloom_actionverbs,
                bld_id=request.bld_id,
                created_by=user_id,
                modified_by=user_id
            )
            db.add(level_obj)
            
        db.commit()
        db.refresh(level_obj)
        return returnSuccess({"message": "Saved Successfully", "id": level_obj.bloom_id}) # type: ignore


    except Exception as e:
        db.rollback()
        return returnException(str(e))

# --- API 3: Delete Level ---
@router.post("/delete_bloom_level")
def delete_bloom_level(
    request: BloomLevelDeleteSchema, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        if not request.bloom_id:
             return returnException("Bloom ID is required for deletion")

        level_obj = db.query(BloomLevel).filter(BloomLevel.bloom_id == request.bloom_id).first() # type: ignore

        if not level_obj:
            return returnException("Bloom Level not found")

        db.delete(level_obj)
        db.commit()
        
        return returnSuccess({"message": "Deleted Successfully"})

    except Exception as e:
        db.rollback()
        return returnException(str(e))