from datetime import datetime

from fastapi import APIRouter, Depends, Form, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import (
    returnSuccess,
    returnException
)

from app.db.models import (
    IEMSAcademicBatch,
    IEMSemester,
    LMSMentorsGroup,
    LMSMentorsGroupTerms,
    LMSGroupMentees,
    LMSMentoringSchedule,
    LMSMentoringSubGroup,
    LMSMentoringSubGrpDate,
    LMSMapMenteeSchedule,

    LMSMenteeQuestionnaireResponse,
    LMSMenteeQuestionnaireResponseQue,
    LMSMenteeQuestionnaireResponseOption,

    LMSMMPSessionSuggestion,
    LMSMMPSessionSuggestionGenericComments,
    LMSMMPSessionSuggestionIndividualComments,

    LMSQuestionnairesQuestions,
    LMSQuestionnairesOptions,

    IEMStudents,
    IEMSUsers
)
from .mmp_report_schema import *

router = APIRouter()

@router.get("/test")
def test():
    return {"message": "MMP Report Working"}


@router.get(
    "/academic-batches",
    response_model=list[AcademicBatchResponse]
)
def get_academic_batches(db: Session = Depends(get_db)):

    batches = (
        db.query(IEMSAcademicBatch)
        .filter(IEMSAcademicBatch.status == 1)
        .order_by(IEMSAcademicBatch.academic_batch_code)
        .all()
    )

    return batches

@router.post("/get_students")
def get_students(
    req: StudentListRequest,
    db: Session = Depends(get_db)
):
    try:

        group_term = db.query(
            LMSMentorsGroupTerms
        ).filter(
            LMSMentorsGroupTerms.mentors_group_id == req.mentors_group_id,
            LMSMentorsGroupTerms.semester_id == req.semester_id
        ).first()

        if not group_term:
            return returnSuccess([])

        students = (
            db.query(
                IEMStudents.student_id,
                IEMStudents.usno,
                IEMStudents.name
            )
            .join(
                LMSGroupMentees,
                LMSGroupMentees.student_id == IEMStudents.student_id
            )
            .filter(
                LMSGroupMentees.mentors_group_terms_id ==
                group_term.mentors_group_terms_id
            )
            .order_by(IEMStudents.name)
            .all()
        )

        result = []

        for row in students:

            result.append({

                "student_id": row.student_id,

                "student_usn": row.usno,

                "student_name": row.name
            })

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))
    

@router.post("/get_student_details")
def get_student_details(
    req: StudentDetailsRequest,
    db: Session = Depends(get_db)
):

    try:

        student = db.query(
            IEMStudents
        ).filter(
            IEMStudents.usno == req.student_usn
        ).first()

        if not student:
            return returnException("Student not found")

        mentor_group = db.query(
            LMSMentorsGroup
        ).filter(
            LMSMentorsGroup.mentors_group_id ==
            req.mentors_group_id
        ).first()

        semester = db.query(
            IEMSemester
        ).filter(
            IEMSemester.semester_id ==
            req.semester_id
        ).first()

        result = {

            "student_id": student.student_id,

            "student_name": student.name,

            "student_usn": student.usno,

            "email": student.email,

            "mobile": student.mobile,

            "group_name":
            mentor_group.mentors_pgm_title if mentor_group else "",

            "semester":
            semester.term_name if semester else ""
        }

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))

@router.post("/get_student_questionnaires")
def get_student_questionnaires(
    req: StudentQuestionnaireRequest,
    db: Session = Depends(get_db)
):

    try:

        student = db.query(
            IEMStudents
        ).filter(
            IEMStudents.usno == req.student_usn
        ).first()

        if not student:
            return returnException("Student not found")

        responses = (

            db.query(

                LMSMenteeQuestionnaireResponse,

                LMSMentoringSchedule

            )

            .join(

                LMSMentoringSchedule,

                LMSMentoringSchedule.schedule_id ==

                LMSMenteeQuestionnaireResponse.schedule_id

            )

            .filter(

                LMSMenteeQuestionnaireResponse.student_id ==

                student.student_id

            )

            .all()

        )

        result = []

        for response, schedule in responses:

            result.append({

                "schedule_id": schedule.schedule_id,

                "questionnaire_response_id":
                response.questionnaire_response_id,

                "questionnaire_id":
                response.questionnaire_id,

                "submitted_date":
                response.created_date,

                "session_agenda":
                schedule.session_agenda

            })

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))