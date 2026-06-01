from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess, returnException
from app.api.v1.cudo_module.program_outcome.model.po_type_model import PoType
from app.api.v1.cudo_module.program_outcome.schema.po_type_schema import (
    PoTypeCreate,
    PoTypeUpdate,
    PoTypeResponse
)

router = APIRouter()


@router.get("")
def list_po_types(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        org_id: Optional[int] = Header(None)
):
    """
    Fetch all Program Outcomes with optional search and pagination.

    Parameters:
    - skip: Number of records to skip
    - limit: Maximum number of records to return
    - search: Optional search string to filter by Program Outcome name or description (case-insensitive)

    Returns:
    - List of Program Outcomes with total count
    """
    try:
        query = db.query(PoType)

        # Apply search filter if provided
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                func.lower(PoType.po_type_name).like(func.lower(search_term)) |
                func.lower(PoType.po_type_description).like(func.lower(search_term))
            )

        total = query.count()
        po_types = query.offset(skip).limit(limit).all()

        response_data = [PoTypeResponse.model_validate(po).model_dump() for po in po_types]

        return returnSuccess(response_data)
    except Exception as e:
        return returnException(f"Error fetching Program Outcomes: {str(e)}")


@router.get("/{po_type_id}")
def get_po_type_detail(
        po_type_id: int,
        db: Session = Depends(get_db),
        org_id: Optional[int] = Header(None)
):
    """
    Fetch a single Program Outcome by ID.
    
    Parameters:
    - po_type_id: Program Outcome ID
    
    Returns:
    - Single Program Outcome details
    """
    try:
        po_type = db.query(PoType).filter(PoType.po_type_id == po_type_id).first()
        
        if not po_type:
            raise HTTPException(status_code=404, detail="Program Outcome not found")
        
        response_data = PoTypeResponse.model_validate(po_type).model_dump()
        return returnSuccess(response_data)
    except HTTPException:
        raise
    except Exception as e:
        return returnException(f"Error fetching Program Outcome: {str(e)}")


@router.post("")
def create_po_type(
        request: PoTypeCreate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
        org_id: Optional[int] = Header(None)
):
    """
    Create a new Program Outcome with academic validations.
    
    Parameters:
    - request: Program Outcome data (po_type and po_description)
    - current_user: Authenticated user information
    
    Validations:
    - po_type is mandatory and must be unique (case-insensitive)
    - po_description is mandatory (as per frontend schema)
    - Maximum field lengths enforced
    
    Returns:
    - Created Program Outcome with po_id
    """
    try:
        user_id = current_user.get('user_id')
        
        # Academic Validation: Check if po_type_name already exists (case-insensitive)
        existing_po = db.query(PoType).filter(
            func.lower(PoType.po_type_name) == func.lower(request.po_type_name.strip())
        ).first()
        
        if existing_po:
            return returnException(f"Program Outcome Name '{request.po_type_name}' already exists")
        
        # Create new Program Outcome
        new_po = PoType(
            po_type_name=request.po_type_name.strip(),
            po_type_description=request.po_type_description.strip() if request.po_type_description else None,
            created_by=user_id,
            created_date=datetime.now()
        )
        
        db.add(new_po)
        db.commit()
        db.refresh(new_po)
        
        response_data = PoTypeResponse.model_validate(new_po).model_dump()
        return returnSuccess(response_data, message="Program Outcome created successfully")
    except Exception as e:
        db.rollback()
        return returnException(f"Error creating Program Outcome: {str(e)}")


@router.put("/{po_type_id}")
def update_po_type(
        po_type_id: int,
        request: PoTypeUpdate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
        org_id: Optional[int] = Header(None)
):
    """
    Update an existing Program Outcome with academic validations.
    
    Parameters:
    - po_type_id: Program Outcome ID to update
    - request: Updated Program Outcome data
    - current_user: Authenticated user information
    
    Validations:
    - Program Outcome must exist
    - po_type_name must be unique if being changed (case-insensitive)
    - Maximum field lengths enforced
    - Audit fields (modified_by, modified_date) are automatically updated
    
    Returns:
    - Updated Program Outcome details
    """
    try:
        user_id = current_user.get('user_id')
        
        # Fetch the Program Outcome
        po_type = db.query(PoType).filter(PoType.po_type_id == po_type_id).first()
        
        if not po_type:
            raise HTTPException(status_code=404, detail="Program Outcome not found")
        
        # Academic Validation: Check if new po_type_name already exists (if being changed)
        if request.po_type_name and request.po_type_name.strip() != po_type.po_type_name:
            existing_po = db.query(PoType).filter(
                func.lower(PoType.po_type_name) == func.lower(request.po_type_name.strip()),
                PoType.po_type_id != po_type_id
            ).first()
            
            if existing_po:
                return returnException(f"Program Outcome Name '{request.po_type_name}' already exists")
            
            po_type.po_type_name = request.po_type_name.strip()
        
        # Update optional fields
        if request.po_type_description is not None:
            po_type.po_type_description = request.po_type_description.strip() if request.po_type_description.strip() else None
        
        if request.status is not None:
            po_type.status = request.status
        
        # Update audit fields
        po_type.modified_by = user_id
        po_type.modified_date = datetime.now()
        
        db.commit()
        db.refresh(po_type)
        
        response_data = PoTypeResponse.model_validate(po_type).model_dump()
        return returnSuccess(response_data, message="Program Outcome updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return returnException(f"Error updating Program Outcome: {str(e)}")


@router.delete("/{po_type_id}")
def delete_po_type(
        po_type_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
        org_id: Optional[int] = Header(None)
):
    """
    Delete a Program Outcome (hard delete - permanently removes from database).

    Parameters:
    - po_type_id: Program Outcome ID to delete
    - current_user: Authenticated user information

    Notes:
    - This is a hard delete operation - the record is permanently removed from the database
    - Confirms the affected row count before returning success

    Returns:
    - Success message
    """
    try:
        # Perform hard delete and get affected row count
        affected_rows = db.query(PoType).filter(PoType.po_type_id == po_type_id).delete()

        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Program Outcome not found")

        db.commit()

        return returnSuccess(None, message="Program Outcome deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return returnException(f"Error deleting Program Outcome: {str(e)}")
