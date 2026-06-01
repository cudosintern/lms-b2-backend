from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional, List

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess, returnException
from .lab_category_model import LabCategory
from .lab_category_schema import (
    LabCategoryCreate,
    LabCategoryUpdate,
    LabCategoryResponse
)

router = APIRouter()

@router.get("/lab_categories")
def list_lab_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    try:
        query = db.query(LabCategory).filter(LabCategory.master_type_id == 9)
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                func.lower(LabCategory.lab_cat_name).like(func.lower(search_term)) |
                func.lower(LabCategory.lab_cat_description).like(func.lower(search_term))
            )
        
        items = query.offset(skip).limit(limit).all()
        response_data = [LabCategoryResponse.model_validate(item).model_dump() for item in items]
        return returnSuccess(response_data)
    except Exception as e:
        return returnException(f"Error fetching Lab Categories: {str(e)}")


@router.post("/lab_categories")
def create_lab_category(
    request: LabCategoryCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_id = current_user.get('user_id')
        
        existing = db.query(LabCategory).filter(
            func.lower(LabCategory.lab_cat_name) == func.lower(request.lab_cat_name.strip()),
            LabCategory.master_type_id == 9
        ).first()
        if existing:
             return returnException(f"Lab Category '{request.lab_cat_name}' already exists")

        new_item = LabCategory(
            lab_cat_name=request.lab_cat_name.strip(),
            lab_cat_description=request.lab_cat_description.strip() if request.lab_cat_description else None,
            created_by=user_id,
            created_date=datetime.now(),
            master_type_id=9,
            parent_id=0,
            mtd_status=0
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return returnSuccess(LabCategoryResponse.model_validate(new_item).model_dump(), message="Created Lab Category successfully")
    except Exception as e:
        db.rollback()
        return returnException(f"Error creating Lab Category: {str(e)}")


@router.put("/lab_categories/{id}")
def update_lab_category(
    id: int,
    request: LabCategoryUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_id = current_user.get('user_id')
        item = db.query(LabCategory).filter(
            LabCategory.lab_cat_id == id,
            LabCategory.master_type_id == 9
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail="Lab Category not found")

        if request.lab_cat_name and request.lab_cat_name.strip() != item.lab_cat_name:
             existing = db.query(LabCategory).filter(
                func.lower(LabCategory.lab_cat_name) == func.lower(request.lab_cat_name.strip()),
                LabCategory.lab_cat_id != id,
                LabCategory.master_type_id == 9
             ).first()
             if existing:
                 return returnException(f"Lab Category '{request.lab_cat_name}' already exists")
             item.lab_cat_name = request.lab_cat_name.strip()

        if request.lab_cat_description is not None:
            item.lab_cat_description = request.lab_cat_description.strip() if request.lab_cat_description else None
        
        item.modified_by = user_id
        item.modified_date = datetime.now()
        
        db.commit()
        db.refresh(item)
        return returnSuccess(LabCategoryResponse.model_validate(item).model_dump(), message="Updated Lab Category successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return returnException(f"Error updating Lab Category: {str(e)}")


@router.delete("/lab_categories/{id}")
def delete_lab_category(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        count = db.query(LabCategory).filter(
            LabCategory.lab_cat_id == id,
            LabCategory.master_type_id == 9
        ).delete()
        if count == 0:
            raise HTTPException(status_code=404, detail="Lab Category not found")
        db.commit()
        return returnSuccess(None, message="Deleted Lab Category successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return returnException(f"Error deleting Lab Category: {str(e)}")
