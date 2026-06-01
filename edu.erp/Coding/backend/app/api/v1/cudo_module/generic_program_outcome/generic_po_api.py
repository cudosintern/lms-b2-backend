from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime
from typing import Optional, List

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess, returnException
from app.db.models import AccreditationType, PO
from .generic_po_schema import (
    AccreditationTypeCreate,
    AccreditationTypeUpdate,
    AccreditationTypeResponse,
    PoCreate,
    PoNestedUpdate,
    PoResponse
)
from app.api.v1.cudo_module.program_outcome.model.po_type_model import PoType

router = APIRouter()

# --- Accreditation Type Endpoints ---

@router.get("/accreditation_types")
def list_accreditation_types(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    org_id: Optional[int] = Header(None)
):
    """
    Fetch all Accreditation Types with their POs.
    """
    try:
        query = db.query(AccreditationType).options(joinedload(AccreditationType.pos))
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                func.lower(AccreditationType.atype_name).like(func.lower(search_term)) |
                func.lower(AccreditationType.atype_description).like(func.lower(search_term))
            )
        
        items = query.order_by(AccreditationType.atype_id.desc()).offset(skip).limit(limit).all()
        response_data = [AccreditationTypeResponse.model_validate(item).model_dump() for item in items]
        return returnSuccess(response_data)
    except Exception as e:
        return returnException(f"Error fetching Accreditation Types: {str(e)}")


@router.post("/accreditation_types")
def create_accreditation_type(
    request: AccreditationTypeCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    org_id: Optional[int] = Header(None)
):
    try:
        user_id = current_user.get('user_id')
        
        # Check for existing Accreditation Type by name
        existing = db.query(AccreditationType).filter(
            func.lower(AccreditationType.atype_name) == func.lower(request.atype_name.strip())
        ).first()
        if existing:
             return returnException(f"Accreditation Type '{request.atype_name}' already exists")

        # Create Accreditation Type
        new_item = AccreditationType(
            atype_name=request.atype_name.strip(),
            atype_description=request.atype_description.strip(),
            entity_id=request.entity_id,
            created_by=user_id,
            created_date=datetime.now()
        )
        db.add(new_item)
        db.flush() # Flush to get the ID for new_item

        # Process nested POs if present
        if request.pos:
            for po_data in request.pos:
                # Optional: Validate PO uniqueness or other constraints here if strictness is needed
                # For now, we trust the input and basic constraints
                
                # Check PO Type if provided
                if po_data.po_type_id:
                     po_type = db.query(PoType).filter(PoType.po_type_id == po_data.po_type_id).first()
                     if not po_type:
                         raise Exception(f"PO Type with ID {po_data.po_type_id} not found")

                new_po = PO(
                    po_code=po_data.po_code.strip(),
                    po_statement=po_data.po_statement.strip(),
                    po_reference=po_data.po_reference.strip() if po_data.po_reference else None,
                    pso_flag=po_data.pso_flag,
                    po_type_id=po_data.po_type_id,
                    crclm_id=po_data.crclm_id,
                    state_id=po_data.state_id,
                    po_minthreshhold=po_data.po_minthreshhold,
                    po_studentthreshhold=po_data.po_studentthreshhold,
                    justify=po_data.justify,
                    import_ref_po_id=po_data.import_ref_po_id,
                    direct_attainment=po_data.direct_attainment,
                    indirect_attainment=po_data.indirect_attainment,
                    extra_curricular=po_data.extra_curricular,
                    atype_id=new_item.atype_id, # Link to the new Accreditation Type
                    created_by=user_id,
                    create_date=datetime.now()
                )
                db.add(new_po)

        db.commit()
        db.refresh(new_item)
        # Re-fetch with relationships for response
        query = db.query(AccreditationType).filter(AccreditationType.atype_id == new_item.atype_id).options(joinedload(AccreditationType.pos))
        final_item = query.first()
        return returnSuccess(AccreditationTypeResponse.model_validate(final_item).model_dump(), message="Created successfully")
    except Exception as e:
        db.rollback()
        return returnException(f"Error creating Accreditation Type: {str(e)}")


@router.put("/accreditation_types/{id}")
def update_accreditation_type(
    id: int,
    request: AccreditationTypeUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    org_id: Optional[int] = Header(None)
):
    try:
        user_id = current_user.get('user_id')
        item = db.query(AccreditationType).filter(AccreditationType.atype_id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Accreditation Type not found")

        if request.atype_name and request.atype_name.strip() != item.atype_name:
             existing = db.query(AccreditationType).filter(
                func.lower(AccreditationType.atype_name) == func.lower(request.atype_name.strip()),
                AccreditationType.atype_id != id
             ).first()
             if existing:
                 return returnException(f"Accreditation Type '{request.atype_name}' already exists")
             item.atype_name = request.atype_name.strip()

        if request.atype_description is not None:
            item.atype_description = request.atype_description.strip()
        if request.entity_id is not None:
            item.entity_id = request.entity_id
        
        item.modified_by = user_id
        item.modified_date = datetime.now()

        # Handle Nested POs
        if request.pos is not None:
             # Fetch existing POs
             existing_pos = db.query(PO).filter(PO.atype_id == id).all()
             existing_po_map = {po.po_id: po for po in existing_pos}
             
             incoming_po_ids = set()
             
             for po_data in request.pos:
                 if po_data.po_id and po_data.po_id in existing_po_map:
                     # Update existing
                     existing_po = existing_po_map[po_data.po_id]
                     if po_data.po_code: existing_po.po_code = po_data.po_code.strip()
                     if po_data.po_statement: existing_po.po_statement = po_data.po_statement.strip()
                     if po_data.po_reference is not None: existing_po.po_reference = po_data.po_reference
                     if po_data.pso_flag is not None: existing_po.pso_flag = po_data.pso_flag
                     if po_data.po_type_id: existing_po.po_type_id = po_data.po_type_id
                     if po_data.crclm_id: existing_po.crclm_id = po_data.crclm_id
                     if po_data.state_id: existing_po.state_id = po_data.state_id
                     if po_data.po_minthreshhold is not None: existing_po.po_minthreshhold = po_data.po_minthreshhold
                     if po_data.po_studentthreshhold is not None: existing_po.po_studentthreshhold = po_data.po_studentthreshhold
                     if po_data.justify is not None: existing_po.justify = po_data.justify
                     if po_data.import_ref_po_id is not None: existing_po.import_ref_po_id = po_data.import_ref_po_id
                     if po_data.direct_attainment is not None: existing_po.direct_attainment = po_data.direct_attainment
                     if po_data.indirect_attainment is not None: existing_po.indirect_attainment = po_data.indirect_attainment
                     if po_data.extra_curricular is not None: existing_po.extra_curricular = po_data.extra_curricular
                     
                     existing_po.modified_by = user_id
                     existing_po.modify_date = datetime.now()
                     incoming_po_ids.add(po_data.po_id)
                 else:
                     # Create new PO
                     new_po = PO(
                         po_code=po_data.po_code.strip(),
                         po_statement=po_data.po_statement.strip(),
                         po_reference=po_data.po_reference.strip() if po_data.po_reference else None,
                         pso_flag=po_data.pso_flag,
                         po_type_id=po_data.po_type_id,
                         crclm_id=po_data.crclm_id,
                         state_id=po_data.state_id,
                         po_minthreshhold=po_data.po_minthreshhold,
                         po_studentthreshhold=po_data.po_studentthreshhold,
                         justify=po_data.justify,
                         import_ref_po_id=po_data.import_ref_po_id,
                         direct_attainment=po_data.direct_attainment,
                         indirect_attainment=po_data.indirect_attainment,
                         extra_curricular=po_data.extra_curricular,
                         atype_id=id,
                         created_by=user_id,
                         create_date=datetime.now()
                     )
                     db.add(new_po)
             
             # Delete missing POs
             for po_id, po in existing_po_map.items():
                 if po_id not in incoming_po_ids:
                     # Since we added cascade="all, delete-orphan", simply referencing item.pos usually works,
                     # but here we are manually querying. So manual delete is fine.
                     db.delete(po)

        db.commit()
        
        # Refresh and return
        query = db.query(AccreditationType).filter(AccreditationType.atype_id == id).options(joinedload(AccreditationType.pos))
        final_item = query.first()
        return returnSuccess(AccreditationTypeResponse.model_validate(final_item).model_dump(), message="Updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return returnException(f"Error updating Accreditation Type: {str(e)}")


@router.delete("/accreditation_types/{id}")
def delete_accreditation_type(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Check if item exists
        item = db.query(AccreditationType).filter(AccreditationType.atype_id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Accreditation Type not found")
            
        # Due to cascade="all, delete-orphan" in relationship, deleting item should delete POs.
        db.delete(item)
        db.commit()
        return returnSuccess(None, message="Deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return returnException(f"Error from delete: {str(e)}")
