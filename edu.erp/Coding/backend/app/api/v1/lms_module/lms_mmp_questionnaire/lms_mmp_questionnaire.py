from datetime import datetime
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnException, returnSuccess

from .lms_mmp_questionnaire_schema import QuestionnaireCreate
from app.db.models import LMSQuestionnaires

router = APIRouter()


@router.post("/save_questionnaire")
def save_questionnaire(
    questionnaire_data: QuestionnaireCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("user_id")

    return commit_questionnaire(
        db,
        questionnaire_data,
        user_id
    )

def commit_questionnaire(
    db: Session,
    questionnaire_data: QuestionnaireCreate,
    user_id: int
):
    questionnaire = None

    if questionnaire_data.questionnaire_id is None:

        questionnaire = LMSQuestionnaires(
            questionnaire_name=questionnaire_data.questionnaire_name.strip(),
            message_to_mentees=questionnaire_data.message_to_mentees,
            access_level=questionnaire_data.access_level,
            parent_id=questionnaire_data.parent_id,
            created_by=user_id,
            created_date=datetime.now()
        )

        db.add(questionnaire)
        db.commit()
        db.refresh(questionnaire)

    else:

        questionnaire = db.query(
            LMSQuestionnaires
        ).filter(
            LMSQuestionnaires.questionnaire_id ==
            questionnaire_data.questionnaire_id
        ).first()

        if not questionnaire:
            return returnException(
                "Questionnaire not found"
            )

        questionnaire.questionnaire_name = questionnaire_data.questionnaire_name.strip()
        questionnaire.message_to_mentees = questionnaire_data.message_to_mentees
        questionnaire.access_level = questionnaire_data.access_level
        questionnaire.parent_id = questionnaire_data.parent_id
        questionnaire.modified_by = user_id
        questionnaire.modified_date = datetime.now()

        db.commit()

    return returnSuccess({
        "questionnaire_id": questionnaire.questionnaire_id,
        "questionnaire_name": questionnaire.questionnaire_name
    })

@router.get("/get_questionnaire_list")
def get_questionnaire_list(
    db: Session = Depends(get_db)
):
    data = db.query(
        LMSQuestionnaires
    ).order_by(
        LMSQuestionnaires.questionnaire_id.desc()
    ).all()

    result = []

    for row in data:
        result.append({
            "questionnaire_id": row.questionnaire_id,
            "questionnaire_name": row.questionnaire_name,
            "message_to_mentees": row.message_to_mentees,
            "access_level": row.access_level,
            "parent_id": row.parent_id
        })

    return returnSuccess(result)