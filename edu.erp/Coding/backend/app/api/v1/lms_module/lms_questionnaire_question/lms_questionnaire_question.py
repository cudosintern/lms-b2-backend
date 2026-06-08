from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import (
    returnSuccess,
    returnException
)

from app.db.models import LMSQuestionnairesQuestions

from .lms_questionnaire_question_schema import (
    QuestionnaireQuestionCreate
)

router = APIRouter()

@router.post("/save_question")
def save_question(
    question_data: QuestionnaireQuestionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("user_id")

    if question_data.questionnaire_que_id is None:

        question = LMSQuestionnairesQuestions(
            questionnaire_id=question_data.questionnaire_id,
            que_type_id=question_data.que_type_id,
            que_no=question_data.que_no,
            question=question_data.question,
            questionnaire_type_id=question_data.questionnaire_type_id,
            que_is_mandatory=question_data.que_is_mandatory,
            created_by=user_id,
            created_date=datetime.now()
        )

        db.add(question)
        db.commit()
        db.refresh(question)

    else:

        question = db.query(
            LMSQuestionnairesQuestions
        ).filter(
            LMSQuestionnairesQuestions.questionnaire_que_id ==
            question_data.questionnaire_que_id
        ).first()

        if not question:
            return returnException(
                "Question not found"
            )

        question.questionnaire_id = (
            question_data.questionnaire_id
        )

        question.que_type_id = (
            question_data.que_type_id
        )

        question.que_no = (
            question_data.que_no
        )

        question.question = (
            question_data.question
        )

        question.questionnaire_type_id = (
            question_data.questionnaire_type_id
        )

        question.que_is_mandatory = (
            question_data.que_is_mandatory
        )

        question.modified_by = user_id
        question.modified_date = datetime.now()

        db.commit()

    return returnSuccess({
        "questionnaire_que_id":
        question.questionnaire_que_id
    })
    
@router.get(
    "/get_questions_by_questionnaire/{questionnaire_id}"
)
def get_questions_by_questionnaire(
    questionnaire_id: int,
    db: Session = Depends(get_db)
):
    questions = db.query(
        LMSQuestionnairesQuestions
    ).filter(
        LMSQuestionnairesQuestions.questionnaire_id ==
        questionnaire_id
    ).order_by(
        LMSQuestionnairesQuestions.que_no
    ).all()

    result = []

    for row in questions:

        result.append({
            "questionnaire_que_id":
            row.questionnaire_que_id,

            "questionnaire_id":
            row.questionnaire_id,

            "que_type_id":
            row.que_type_id,

            "que_no":
            row.que_no,

            "question":
            row.question,

            "questionnaire_type_id":
            row.questionnaire_type_id,

            "que_is_mandatory":
            row.que_is_mandatory
        })

    return returnSuccess(result)

@router.delete(
    "/delete_question/{questionnaire_que_id}"
)
def delete_question(
    questionnaire_que_id: int,
    db: Session = Depends(get_db)
):
    question = db.query(
        LMSQuestionnairesQuestions
    ).filter(
        LMSQuestionnairesQuestions.questionnaire_que_id ==
        questionnaire_que_id
    ).first()

    if not question:
        return returnException(
            "Question not found"
        )

    db.delete(question)
    db.commit()

    return returnSuccess(
        "Question deleted successfully"
    )

