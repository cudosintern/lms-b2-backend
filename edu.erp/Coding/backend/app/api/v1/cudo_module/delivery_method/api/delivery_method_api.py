from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional

from app.api.v1.cudo_module.delivery_method.model.delivery_method_model import CudosDeliveryMethod
from app.api.v1.cudo_module.delivery_method.schema.delivery_method_schema import CreateDeliveryMethod, \
    UpdateDeliveryMethod, DeliveryMethodInDB
from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess, returnException

router = APIRouter(
    tags=["Delivery Method"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/")
def create_delivery_method(delivery_method: CreateDeliveryMethod, db: Session = Depends(get_db),
                           current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.get("user_id")
        data = delivery_method.dict()
        bloom_levels = data.pop("bloom_levels", [])

        db_delivery_method = CudosDeliveryMethod(
            **data,
            created_by=user_id,
            created_date=date.today()
        )
        db_delivery_method.bloom_levels = bloom_levels

        db.add(db_delivery_method)
        db.commit()
        db.refresh(db_delivery_method)
        # Serialize to include properties
        response_data = DeliveryMethodInDB.from_orm(db_delivery_method).dict()
        return returnSuccess(response_data, message="Delivery Method created successfully")
    except Exception as e:
        db.rollback()
        return returnException(f"Error creating Delivery Method: {str(e)}")


@router.get("/")
def get_all_delivery_methods(db: Session = Depends(get_db)):
    try:
        delivery_methods = db.query(CudosDeliveryMethod).all()
        # Serialize list to include properties
        data = [DeliveryMethodInDB.from_orm(dm).dict() for dm in delivery_methods]
        return returnSuccess(data)
    except Exception as e:
        return returnException(f"Error fetching Delivery Methods: {str(e)}")


@router.get("/{delivery_mtd_id}")
def get_delivery_method_by_id(delivery_mtd_id: int, db: Session = Depends(get_db)):
    try:
        db_delivery_method = db.query(CudosDeliveryMethod).filter(
            CudosDeliveryMethod.delivery_mtd_id == delivery_mtd_id).first()
        if db_delivery_method is None:
            return returnException("Delivery Method not found")
        # Serialize to include properties
        response_data = DeliveryMethodInDB.from_orm(db_delivery_method).dict()
        return returnSuccess(response_data)
    except Exception as e:
        return returnException(f"Error fetching Delivery Method: {str(e)}")


@router.put("/{delivery_mtd_id}")
def update_delivery_method(delivery_mtd_id: int, delivery_method: UpdateDeliveryMethod, db: Session = Depends(get_db),
                           current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.get("user_id")
        db_delivery_method = db.query(CudosDeliveryMethod).filter(
            CudosDeliveryMethod.delivery_mtd_id == delivery_mtd_id).first()
        if db_delivery_method is None:
            return returnException("Delivery Method not found")

        update_data = delivery_method.dict(exclude_unset=True)
        if "bloom_levels" in update_data:
            db_delivery_method.bloom_levels = update_data.pop("bloom_levels")

        for key, value in update_data.items():
            setattr(db_delivery_method, key, value)

        db_delivery_method.modified_by = user_id
        db_delivery_method.modified_date = date.today()

        db.commit()
        db.refresh(db_delivery_method)
        # Serialize to include properties
        response_data = DeliveryMethodInDB.from_orm(db_delivery_method).dict()
        return returnSuccess(response_data, message="Delivery Method updated successfully")
    except Exception as e:
        db.rollback()
        return returnException(f"Error updating Delivery Method: {str(e)}")


@router.delete("/{delivery_mtd_id}")
def delete_delivery_method(delivery_mtd_id: int, db: Session = Depends(get_db)):
    try:
        db_delivery_method = db.query(CudosDeliveryMethod).filter(
            CudosDeliveryMethod.delivery_mtd_id == delivery_mtd_id).first()
        if db_delivery_method is None:
            return returnException("Delivery Method not found")
        db.delete(db_delivery_method)
        db.commit()
        return returnSuccess(None, message="Delivery Method deleted successfully")
    except Exception as e:
        db.rollback()
        # return returnException(f"Error deleting Delivery Method: {str(e)}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content={"status": False, "message": f"Error deleting Delivery Method: {str(e)}", "data": None}
        )