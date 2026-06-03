from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.cudo_module.delivery_method.model.delivery_method_model import CudosDeliveryMethod as MasterDeliveryMethod
from app.db.models import (
    CurriculumDeliveryMethod, 
    CurriculumDeliveryBloom, 
    BloomLevel,
    Curriculum
)

from app.api.v1.cudo_module.curriculum.delivery_method.curriculum_delivery_method_schema import (
    CurriculumDeliveryMethodSchema, 
    DeliveryMethodDeleteSchema
)

router = APIRouter()

class CurriculumDeliveryMethodPayload(BaseModel):
    curriculum_id: int

# --- 1. GET LIST (Restored DB Connection) ---
@router.post("/get_curriculum_delivery_methods")
def get_curriculum_delivery_methods(payload: CurriculumDeliveryMethodPayload, db: Session = Depends(get_db)):
    try:
        curr_id = payload.curriculum_id
        if not curr_id:
             return {"status": 0, "message": "Curriculum ID is required"}

        # Check if data exists for this curriculum
        count = db.query(CurriculumDeliveryMethod).filter(CurriculumDeliveryMethod.crclm_id == curr_id).count()
        
        # --- AUTO-INITIALIZATION BLOCK ---
        # If no methods exist for this curriculum, copy from Master Table
        if count == 0:
            master_methods = db.query(
                MasterDeliveryMethod.delivery_mtd_name, 
                MasterDeliveryMethod.delivery_mtd_desc
            ).all()
            
            if master_methods:
                for master in master_methods:
                    new_method = CurriculumDeliveryMethod(
                        crclm_id=curr_id,
                        delivery_mtd_name=master.delivery_mtd_name,
                        delivery_mtd_desc=master.delivery_mtd_desc,
                        created_by=None 
                    )
                    db.add(new_method)
                
                try:
                    db.commit()
                except Exception as commit_error:
                    db.rollback()
                    raise commit_error

        # --- FETCH DATA ---
        results = db.query(
            CurriculumDeliveryMethod,
            CurriculumDeliveryBloom.bloom_id,
            BloomLevel.level
        ).outerjoin(
            CurriculumDeliveryBloom, 
            CurriculumDeliveryBloom.crclm_dm_id == CurriculumDeliveryMethod.crclm_dm_id
        ).outerjoin(
            BloomLevel, 
            BloomLevel.bloom_id == CurriculumDeliveryBloom.bloom_id
        ).filter(
            CurriculumDeliveryMethod.crclm_id == curr_id
        ).all()

        final_data = []
        for row in results:
            method_obj, b_id, b_name = row
            final_data.append({
                "crclm_dm_id": method_obj.crclm_dm_id,
                "crclm_id": method_obj.crclm_id,
                "delivery_mtd_name": method_obj.delivery_mtd_name,
                "delivery_mtd_desc": method_obj.delivery_mtd_desc,
                "bloom_id": b_id,
                "bloom_level_name": b_name
            })

        return {"status": 1, "data": final_data}

    except Exception as e:
        return {"status": 0, "message": str(e)}

# --- GET CURRICULUM DROPDOWN ---
@router.get("/get_curriculum_dropdown")
def get_curriculum_dropdown(db: Session = Depends(get_db)):
    try:
        # Fetch all Active Curriculums (status=1)
        results = db.query(Curriculum.crclm_id, Curriculum.crclm_name)\
            .filter(Curriculum.status == 1)\
            .all()

        dropdown_data = [
            {"value": row.crclm_id, "label": row.crclm_name} 
            for row in results
        ]

        return {"status": 1, "data": dropdown_data}

    except Exception as e:
        return {"status": 0, "message": str(e)}

# --- 2. SAVE ---
@router.post("/save_curriculum_delivery_method")
def save_curriculum_delivery_method(
    request: CurriculumDeliveryMethodSchema,
    db: Session = Depends(get_db)
):
    try:
        # Check for duplicates (excluding current record if updating)
        dup = db.query(CurriculumDeliveryMethod).filter(
            CurriculumDeliveryMethod.crclm_id == request.crclm_id,
            CurriculumDeliveryMethod.delivery_mtd_name == request.delivery_mtd_name,
            CurriculumDeliveryMethod.crclm_dm_id != (request.crclm_dm_id if request.crclm_dm_id else -1)
        ).first()

        if dup: return {"status": 0, "message": "Duplicate Name!"}

        if request.crclm_dm_id:
            # UPDATE
            method_obj = db.query(CurriculumDeliveryMethod).filter(CurriculumDeliveryMethod.crclm_dm_id == request.crclm_dm_id).first()
            if not method_obj: return {"status": 0, "message": "Record not found"}
            method_obj.delivery_mtd_name = request.delivery_mtd_name
            method_obj.delivery_mtd_desc = request.delivery_mtd_desc
        else:
            # CREATE
            method_obj = CurriculumDeliveryMethod(
                crclm_id=request.crclm_id,
                delivery_mtd_name=request.delivery_mtd_name,
                delivery_mtd_desc=request.delivery_mtd_desc,
                created_by=None
            )
            db.add(method_obj)
            db.flush() # Flush to get the new ID for mapping
        
        # Handle Bloom Level Mapping
        map_obj = db.query(CurriculumDeliveryBloom).filter(
             CurriculumDeliveryBloom.crclm_dm_id == method_obj.crclm_dm_id
        ).first()

        if request.bloom_id:
             if map_obj:
                 map_obj.bloom_id = request.bloom_id
             else:
                 new_map = CurriculumDeliveryBloom(
                     crclm_dm_id=method_obj.crclm_dm_id,
                     bloom_id=request.bloom_id,
                     created_by=None
                 )
                 db.add(new_map)
        else:
             if map_obj: db.delete(map_obj)

        db.commit()
        return {"status": 1, "message": "Saved Successfully"}

    except Exception as e:
        db.rollback()
        return {"status": 0, "message": str(e)}

# --- 3. DELETE ---
@router.post("/delete_curriculum_delivery_method")
def delete_curriculum_delivery_method(
    request: DeliveryMethodDeleteSchema,
    db: Session = Depends(get_db)
):
    try:
        obj = db.query(CurriculumDeliveryMethod).filter(CurriculumDeliveryMethod.crclm_dm_id == request.crclm_dm_id).first()
        
        if obj:
            db.delete(obj)
            db.commit()
            return {"status": 1, "message": "Deleted Successfully"}
            
        return {"status": 0, "message": "Record not found"}

    except Exception as e:
        db.rollback()
        return {"status": 0, "message": str(e)}