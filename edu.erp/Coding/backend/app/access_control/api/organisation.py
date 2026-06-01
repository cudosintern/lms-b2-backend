from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.access_control.models.common_models import Organisation
from app.access_control.schemas.common_schema import OrganisationResponse
from ...core.database import get_db
from app.access_control.utils.response_utils import ResponseUtils

router = APIRouter(tags=["Organisation"])


@router.get("/organisation")
def fetch_organisation(db: Session = Depends(get_db)):
    """Fetch all/org_id Organisations."""
    org_data = db.query(Organisation).filter_by(status=True).all()

    org_data = [
        OrganisationResponse.model_validate(org).model_dump()
        for org in org_data
    ]

    return ResponseUtils.success(org_data)


@router.post("/organisation")
def post_organisation_by_user(
    organisation_data: OrganisationResponse, db: Session = Depends(get_db)
):
    new_organisation_data = Organisation(
        org_name=organisation_data.org_name,
        org_society=organisation_data.org_society,
        org_desc=organisation_data.org_desc,
        unv_id=organisation_data.unv_id,
        status=organisation_data.status,
        created_by=organisation_data.created_by,
        modified_by=organisation_data.modified_by,
        create_date=organisation_data.create_date,
        modify_date=organisation_data.modify_date,
        org_code=organisation_data.org_code,
        org_type_id=organisation_data.org_type_id,
        profile_image=organisation_data.profile_image,
        other_profile_image=organisation_data.other_profile_image
    )

    db.add(new_organisation_data)
    db.commit()
    return ResponseUtils.success(message="Organization added successfully")


@router.put("/organisation/{log_id}")
def update_organisation(
    log_id: int, organisation_data: OrganisationResponse,
    db: Session = Depends(get_db)
):
    db.query(Organisation).filter(Organisation.org_id == log_id).update(
        {
            Organisation.org_id: organisation_data.org_id,
            Organisation.org_name: organisation_data.org_name,
            Organisation.org_society: organisation_data.org_society,
            Organisation.org_desc: organisation_data.org_desc,
            Organisation.unv_id: organisation_data.unv_id,
            Organisation.status: organisation_data.status,
            Organisation.created_by: organisation_data.created_by,
            Organisation.modified_by: organisation_data.modified_by,
            Organisation.create_date: organisation_data.create_date,
            Organisation.modify_date: organisation_data.modify_date,
            Organisation.org_code: organisation_data.org_code,
            Organisation.org_type_id: organisation_data.org_type_id,
            Organisation.profile_image: organisation_data.profile_image,
            Organisation.other_profile_image: organisation_data.other_profile_image
        },
        synchronize_session=False,
    )

    return ResponseUtils.success(message="Organization updated successfully")


@router.delete("/organisation/{log_id}")
def delete_organisation(log_id: int, db: Session = Depends(get_db)):
    organisation_log = db.query(OrganisationResponse).filter(
        OrganisationResponse.org_id == log_id
    ).first()
    if not organisation_log:
        raise HTTPException(status_code=404, detail="organisation not found")
    db.delete(organisation_log)
    db.commit()
    return ResponseUtils.success(message="Organization removed successfully")
