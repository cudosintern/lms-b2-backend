from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.access_control.models.common_models import OrganisationType
from app.access_control.schemas.organisation_type import OrganisationTypeData

from ...core.database import get_db

router = APIRouter(tags=["Organisation type"])


@router.get("/organisation_type")
def fetch_organisation_type(db: Session = Depends(get_db)):
    return db.query(OrganisationType).all()


@router.post("/organisation_type")
def post_organisation_type_by_user(
    organisation_type_data: OrganisationTypeData, db: Session = Depends(get_db)
):
    new_organisation_type_data = OrganisationType(
        org_type=organisation_type_data.org_type,
        org_type_desc=organisation_type_data.org_type_desc,
        unv_id=organisation_type_data.unv_id,
        status=organisation_type_data.status,
    )

    db.add(new_organisation_type_data)
    db.commit()
    return {"message": "organisation type added successfully"}


@router.put("/organisation_type/{log_id}")
def update_organisation_type(
    log_id: int,
    organisation_type_data: OrganisationTypeData,
    db: Session = Depends(get_db),
):
    db.query(OrganisationType).filter(OrganisationType.org_type_id == log_id).update(
        {
            OrganisationType.org_type_id: organisation_type_data.org_type_id,
            OrganisationType.org_type: organisation_type_data.org_type,
            OrganisationType.org_type_desc: organisation_type_data.org_type_desc,
            OrganisationType.unv_id: organisation_type_data.unv_id,
            OrganisationType.status: organisation_type_data.status,
        },
        synchronize_session=False,
    )

    return {"message": "organisation type updated successfully"}


@router.delete("/organisation_type/{log_id}")
def delete_organisation_type(log_id: int, db: Session = Depends(get_db)):
    organisation_type_log = (
        db.query(OrganisationType)
        .filter(OrganisationType.org_id == log_id)
        .first()
    )
    if not organisation_type_log:
        raise HTTPException(status_code=404, detail="organisation_type not found")
    db.delete(organisation_type_log)
    db.commit()
    return {"message": "organisation_type removed successfully"}
