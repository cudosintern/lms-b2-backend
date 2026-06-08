from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import (
    returnSuccess,
    returnException
)

from app.db.models import LMSMentorsGroup

from .lms_mentors_group_schema import (
    MentorsGroupCreate
)

router = APIRouter()

@router.post("/save_mentors_group")
def save_mentors_group(
    mentors_group_data: MentorsGroupCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user_id = current_user.get("user_id")

    if mentors_group_data.mentors_group_id is None:

        mentors_group = LMSMentorsGroup(
            academic_batch_id=
            mentors_group_data.academic_batch_id,

            semester_id=
            mentors_group_data.semester_id,

            config_type_id=
            mentors_group_data.config_type_id,

            questionnaire_id=
            mentors_group_data.questionnaire_id,

            mentors_pgm_title=
            mentors_group_data.mentors_pgm_title,

            created_by=user_id,
            created_date=datetime.now()
        )

        db.add(mentors_group)
        db.commit()
        db.refresh(mentors_group)

    else:

        mentors_group = db.query(
            LMSMentorsGroup
        ).filter(
            LMSMentorsGroup.mentors_group_id ==
            mentors_group_data.mentors_group_id
        ).first()

        if not mentors_group:
            return returnException(
                "Mentors Group not found"
            )

        mentors_group.academic_batch_id = (
            mentors_group_data.academic_batch_id
        )

        mentors_group.semester_id = (
            mentors_group_data.semester_id
        )

        mentors_group.config_type_id = (
            mentors_group_data.config_type_id
        )

        mentors_group.questionnaire_id = (
            mentors_group_data.questionnaire_id
        )

        mentors_group.mentors_pgm_title = (
            mentors_group_data.mentors_pgm_title
        )

        mentors_group.modified_by = user_id

        mentors_group.modified_date = (
            datetime.now()
        )

        db.commit()

    return returnSuccess({
        "mentors_group_id":
        mentors_group.mentors_group_id
    })

@router.get("/get_mentors_group_list")
def get_mentors_group_list(
    db: Session = Depends(get_db)
):

    data = db.query(
        LMSMentorsGroup
    ).order_by(
        LMSMentorsGroup.mentors_group_id.desc()
    ).all()

    result = []

    for row in data:

        result.append({
            "mentors_group_id":
            row.mentors_group_id,

            "academic_batch_id":
            row.academic_batch_id,

            "semester_id":
            row.semester_id,

            "config_type_id":
            row.config_type_id,

            "questionnaire_id":
            row.questionnaire_id,

            "mentors_pgm_title":
            row.mentors_pgm_title
        })

    return returnSuccess(result)

@router.get(
    "/get_mentors_group/{mentors_group_id}"
)
def get_mentors_group(
    mentors_group_id: int,
    db: Session = Depends(get_db)
):

    data = db.query(
        LMSMentorsGroup
    ).filter(
        LMSMentorsGroup.mentors_group_id ==
        mentors_group_id
    ).first()

    if not data:
        return returnException(
            "Record not found"
        )

    return returnSuccess({
        "mentors_group_id":
        data.mentors_group_id,

        "academic_batch_id":
        data.academic_batch_id,

        "semester_id":
        data.semester_id,

        "config_type_id":
        data.config_type_id,

        "questionnaire_id":
        data.questionnaire_id,

        "mentors_pgm_title":
        data.mentors_pgm_title
    })

@router.delete(
    "/delete_mentors_group/{mentors_group_id}"
)
def delete_mentors_group(
    mentors_group_id: int,
    db: Session = Depends(get_db)
):

    data = db.query(
        LMSMentorsGroup
    ).filter(
        LMSMentorsGroup.mentors_group_id ==
        mentors_group_id
    ).first()

    if not data:
        return returnException(
            "Record not found"
        )

    db.delete(data)
    db.commit()

    return returnSuccess(
        "Deleted Successfully"
    )