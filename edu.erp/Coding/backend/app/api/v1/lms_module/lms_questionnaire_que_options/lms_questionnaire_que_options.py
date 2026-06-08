from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import (
    returnSuccess,
    returnException
)

from app.db.models import (
    LMSQuestionnairesOptions
)

from .lms_questionnaire_que_options_schema import (
    QuestionnaireQuestionOptionCreate
)

router = APIRouter()

@router.post("/save_question_option")
def save_question_option(
    option_data: QuestionnaireQuestionOptionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("user_id")

    if option_data.questionnaire_options_id is None:

        option = LMSQuestionnairesOptions(
            questionnaire_que_id=
            option_data.questionnaire_que_id,

            que_option=
            option_data.que_option.strip(),

            specify_flag=
            option_data.specify_flag,

            created_by=user_id,
            created_date=datetime.now()
        )

        db.add(option)

        db.commit()

        db.refresh(option)

    else:

        option = db.query(
            LMSQuestionnairesOptions
        ).filter(
            LMSQuestionnairesOptions
            .questionnaire_options_id ==
            option_data.questionnaire_options_id
        ).first()

        if not option:
            return returnException(
                "Option not found"
            )

        option.que_option = (
            option_data.que_option.strip()
        )

        option.specify_flag = (
            option_data.specify_flag
        )

        option.modified_by = user_id

        option.modified_date = (
            datetime.now()
        )

        db.commit()

    return returnSuccess({
        "questionnaire_options_id":
        option.questionnaire_options_id
    })

@router.get(
    "/get_question_options/{questionnaire_que_id}"
)
def get_question_options(
    questionnaire_que_id: int,
    db: Session = Depends(get_db)
):
    options = db.query(
        LMSQuestionnairesOptions
    ).filter(
        LMSQuestionnairesOptions
        .questionnaire_que_id ==
        questionnaire_que_id
    ).all()

    result = []

    for row in options:

        result.append({
            "questionnaire_options_id":
            row.questionnaire_options_id,

            "questionnaire_que_id":
            row.questionnaire_que_id,

            "que_option":
            row.que_option,

            "specify_flag":
            row.specify_flag
        })

    return returnSuccess(result)


@router.delete(
    "/delete_question_option/{questionnaire_options_id}"
)
def delete_question_option(
    questionnaire_options_id: int,
    db: Session = Depends(get_db)
):
    option = db.query(
        LMSQuestionnairesOptions
    ).filter(
        LMSQuestionnairesOptions
        .questionnaire_options_id ==
        questionnaire_options_id
    ).first()

    if not option:
        return returnException(
            "Option not found"
        )

    db.delete(option)

    db.commit()

    return returnSuccess(
        "Option deleted successfully"
    )

