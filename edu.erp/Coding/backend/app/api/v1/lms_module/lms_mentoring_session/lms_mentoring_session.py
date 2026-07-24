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

from .lms_mentoring_session_schema import *

import uuid
import shutil
import os
UPLOAD_DIR = "uploads/mentoring_comments"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

ALLOWED_EXTENSIONS = [
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "jpg",
    "jpeg",
    "png"
]

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB

def validate_attachment(file):

    if not file:
        return

    ext = file.filename.split(".")[-1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise Exception(
            "Only pdf, doc, docx, xls, xlsx, jpg, jpeg, png allowed"
        )

    content = file.file.read()

    if len(content) > MAX_FILE_SIZE:
        raise Exception(
            "Maximum file size allowed is 2 MB"
        )

    file.file.seek(0)

def save_uploaded_file(file):

    if not file:
        return None

    ext = file.filename.split(".")[-1]

    file_name = (
        str(uuid.uuid4())
        + "."
        + ext
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        file_name
    )

    with open(
        file_path,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    return file_name

router = APIRouter()


# ==========================================================
# GET CURRICULUM LIST
# ==========================================================
@router.get("/get_academic_batch_list")
def get_academic_batch_list(
    db: Session = Depends(get_db)
):
    try:

        batches = db.query(
            IEMSAcademicBatch
        ).filter(
            IEMSAcademicBatch.status == 1
        ).all()

        result = []

        for row in batches:
            result.append({
                "academic_batch_id": row.academic_batch_id,
                "academic_batch_code": row.academic_batch_code,
                "academic_batch_desc": row.academic_batch_desc,
                "curriculum_name": (
                    f"{row.academic_batch_code} - "
                    f"{row.academic_batch_desc}"
                )
            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))


# ==========================================================
# GET SEMESTERS BY CURRICULUM
# ==========================================================
@router.get("/get_semesters_by_academic_batch/{academic_batch_id}")
def get_semesters_by_academic_batch(
    academic_batch_id: int,
    db: Session = Depends(get_db)
):
    try:

        semesters = db.query(
            IEMSemester
        ).filter(
            IEMSemester.academic_batch_id == academic_batch_id
        ).order_by(
            IEMSemester.semester
        ).all()

        result = []

        for sem in semesters:
            result.append({
                "semester_id": sem.semester_id,
                "semester": sem.semester,
                "semester_desc": sem.semester_desc,
                "term_name": sem.term_name
            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))


# ==========================================================
# GET GROUPS BY CURRICULUM
# ==========================================================
@router.get("/get_groups_by_academic_batch/{academic_batch_id}")
def get_groups_by_academic_batch(
    academic_batch_id: int,
    db: Session = Depends(get_db)
):
    try:

        groups = db.query(
            LMSMentorsGroup
        ).filter(
            LMSMentorsGroup.academic_batch_id == academic_batch_id
        ).all()

        result = []

        for grp in groups:

            result.append({
                "mentors_group_id": grp.mentors_group_id,
                "group_name": grp.mentors_pgm_title,
                "mentors_pgm_title": grp.mentors_pgm_title,
                "questionnaire_id": grp.questionnaire_id
            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))


# ==========================================================
# GET GROUP MENTEES
# ==========================================================
@router.get("/get_group_mentees/{mentors_group_id}/{semester_id}")
def get_group_mentees(
    mentors_group_id: int,
    semester_id: int,
    db: Session = Depends(get_db)
):
    try:

        term = db.query(
            LMSMentorsGroupTerms
        ).filter(
            LMSMentorsGroupTerms.mentors_group_id == mentors_group_id,
            LMSMentorsGroupTerms.semester_id == semester_id
        ).first()

        if not term:
            return returnSuccess([])

        mentees = db.query(
            LMSGroupMentees,
            IEMStudents
        ).join(
            IEMStudents,
            IEMStudents.student_id ==
            LMSGroupMentees.student_id
        ).filter(
            LMSGroupMentees.mentors_group_terms_id ==
            term.mentors_group_terms_id
        ).all()

        result = []

        for mentee, student in mentees:

            result.append({
                "student_id": student.student_id,
                "usn": student.usno,
                "student_usn": student.usno,
                "student_name": student.name,
                "email": student.email,
                "student_email": student.email,
                "mobile": student.mobile
            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))


@router.get("/get_group_mentees/{mentors_group_id}")
def get_group_mentees_without_semester(
    mentors_group_id: int,
    db: Session = Depends(get_db)
):
    try:
        terms = db.query(
            LMSMentorsGroupTerms
        ).filter(
            LMSMentorsGroupTerms.mentors_group_id == mentors_group_id
        ).all()

        if not terms:
            return returnSuccess([])

        term_ids = [t.mentors_group_terms_id for t in terms]

        mentees = db.query(
            LMSGroupMentees,
            IEMStudents
        ).join(
            IEMStudents,
            IEMStudents.student_id ==
            LMSGroupMentees.student_id
        ).filter(
            LMSGroupMentees.mentors_group_terms_id.in_(term_ids)
        ).all()

        result = []
        seen_student_ids = set()

        for mentee, student in mentees:
            if student.student_id not in seen_student_ids:
                seen_student_ids.add(student.student_id)
                result.append({
                    "student_id": student.student_id,
                    "usn": student.usno,
                    "student_usn": student.usno,
                    "student_name": student.name,
                    "email": student.email,
                    "student_email": student.email,
                    "mobile": student.mobile
                })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))
    
@router.post("/save_mentoring_session")
def save_mentoring_session(
    req: MentoringSessionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    try:

        user_id = current_user.get("user_id")

        # --------------------------------------------------
        # Validate Group
        # --------------------------------------------------
        group = db.query(
            LMSMentorsGroup
        ).filter(
            LMSMentorsGroup.mentors_group_id ==
            req.mentors_group_id
        ).first()

        if not group:
            return returnException(
                "Invalid mentoring group selected"
            )

        # --------------------------------------------------
        # Validate Semester Mapping
        # --------------------------------------------------
        group_term = db.query(
            LMSMentorsGroupTerms
        ).filter(
            LMSMentorsGroupTerms.mentors_group_id ==
            req.mentors_group_id,

            LMSMentorsGroupTerms.semester_id ==
            req.semester_id
        ).first()

        if not group_term:
            return returnException(
                "Selected semester is not mapped to selected group"
            )

        # --------------------------------------------------
        # Get Allowed Mentees
        # --------------------------------------------------
        group_mentees = db.query(
            LMSGroupMentees.student_id
        ).filter(
            LMSGroupMentees.mentors_group_terms_id ==
            group_term.mentors_group_terms_id
        ).all()

        allowed_students = {
            row.student_id
            for row in group_mentees
        }

        # --------------------------------------------------
        # Duplicate Session Validation
        # --------------------------------------------------
        all_mentees = []

        for subgroup in req.sub_groups:
            all_mentees.extend(
                subgroup.mentee_ids
            )

        duplicate_students = db.query(
            LMSMapMenteeSchedule.student_id
        ).filter(
            LMSMapMenteeSchedule.student_id.in_(
                all_mentees
            )
        ).all()

        if duplicate_students:

            duplicate_ids = [
                row.student_id
                for row in duplicate_students
            ]

            return returnException(
                f"Mentees already mapped to another session : {duplicate_ids}"
            )

        # --------------------------------------------------
        # Create Schedule
        # --------------------------------------------------
        schedule = LMSMentoringSchedule(
            mentors_group_terms_id=
                group_term.mentors_group_terms_id,

            questionnaire_id=
                group.questionnaire_id,

            session_agenda=
                req.session_agenda,

            created_by=
                current_user["user_id"]
        )

        db.add(schedule)
        db.flush()

        # --------------------------------------------------
        # Create Sub Groups
        # --------------------------------------------------
        for subgroup in req.sub_groups:

            db_subgroup = LMSMentoringSubGroup(

                schedule_id=
                schedule.schedule_id,

                sub_group_name=
                subgroup.sub_group_name,

                location=
                subgroup.location,

                created_by=
                user_id
            )

            db.add(db_subgroup)
            db.flush()

            # ----------------------------------------------
            # Save Dates
            # ----------------------------------------------
            for dt in subgroup.dates:

                if dt.start_date > dt.end_date:

                    db.rollback()

                    return returnException(
                        "Start date cannot be greater than end date"
                    )

                if dt.start_time >= dt.end_time:

                    db.rollback()

                    return returnException(
                        "Start time must be less than end time"
                    )

                db_date = LMSMentoringSubGrpDate(

                    sub_group_id=
                    db_subgroup.sub_group_id,

                    start_date=
                    dt.start_date,

                    end_date=
                    dt.end_date,

                    start_time=
                    dt.start_time,

                    end_time=
                    dt.end_time,

                    created_by=
                    user_id
                )

                db.add(db_date)

            # ----------------------------------------------
            # Save Mentees
            # ----------------------------------------------
            for student_id in subgroup.mentee_ids:

                if student_id not in allowed_students:

                    db.rollback()

                    return returnException(
                        f"Student {student_id} is not part of selected mentoring group"
                    )

                db_mentee = LMSMapMenteeSchedule(

                    schedule_id=
                    schedule.schedule_id,

                    student_id=
                    student_id,

                    sub_group_id=
                    db_subgroup.sub_group_id
                )

                db.add(db_mentee)

        db.commit()

        return returnSuccess({
            "schedule_id":
            schedule.schedule_id
        })

    except Exception as e:

        db.rollback()

        return returnException(
            str(e)
        )
    
@router.get("/get_mentoring_sessions")
def get_mentoring_sessions(
    academic_batch_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):

    result = []

    groups_query = db.query(LMSMentorsGroup)
    if academic_batch_id is not None:
        groups_query = groups_query.filter(
            LMSMentorsGroup.academic_batch_id == academic_batch_id
        )
    groups = groups_query.all()

    for group in groups:

        group_terms = db.query(
            LMSMentorsGroupTerms
        ).filter(
            LMSMentorsGroupTerms.mentors_group_id ==
            group.mentors_group_id
        ).all()

        for term in group_terms:

            schedules = db.query(
                LMSMentoringSchedule
            ).filter(
                LMSMentoringSchedule.mentors_group_terms_id ==
                term.mentors_group_terms_id
            ).all()

            for schedule in schedules:

                sub_groups = db.query(
                    LMSMentoringSubGroup
                ).filter(
                    LMSMentoringSubGroup.schedule_id ==
                    schedule.schedule_id
                ).all()

                subgroup_list = []

                include_schedule = False

                for subgroup in sub_groups:

                    dates = db.query(
                        LMSMentoringSubGrpDate
                    ).filter(
                        LMSMentoringSubGrpDate.sub_group_id ==
                        subgroup.sub_group_id
                    ).all()

                    date_list = []

                    for dt in dates:

                        if (month is None or dt.start_date.month == month) and (year is None or dt.start_date.year == year):

                            include_schedule = True

                            mentee_count = db.query(
                                LMSMapMenteeSchedule
                            ).filter(
                                LMSMapMenteeSchedule.sub_group_id ==
                                subgroup.sub_group_id
                            ).count()

                            date_list.append({

                                "sub_group_date_id":
                                dt.sub_group_date_id,

                                "start_date":
                                dt.start_date,

                                "end_date":
                                dt.end_date,

                                "start_time":
                                dt.start_time,

                                "end_time":
                                dt.end_time,

                                "status":
                                dt.status,

                                "mentee_count":
                                mentee_count
                            })

                    if date_list or (month is None and year is None):
                        include_schedule = True
                        subgroup_list.append({

                            "sub_group_id":
                            subgroup.sub_group_id,

                            "sub_group_name":
                            subgroup.sub_group_name,

                            "location":
                            subgroup.location,

                            "dates":
                            date_list
                        })

                if include_schedule or (month is None and year is None):

                    result.append({

                        "schedule_id":
                        schedule.schedule_id,

                        "academic_batch_id":
                        group.academic_batch_id,

                        "mentors_group_id":
                        group.mentors_group_id,

                        "group_name":
                        group.mentors_pgm_title,

                        "semester_id":
                        term.semester_id,

                        "questionnaire_id":
                        schedule.questionnaire_id,

                        "session_agenda":
                        schedule.session_agenda,

                        "sub_groups":
                        subgroup_list
                    })

    return returnSuccess(result)

@router.get("/get_session_mentees/{schedule_id}")
def get_session_mentees(
    schedule_id: int,
    db: Session = Depends(get_db)
):

    mappings = db.query(
        LMSMapMenteeSchedule
    ).filter(
        LMSMapMenteeSchedule.schedule_id == schedule_id
    ).all()

    result = []

    for row in mappings:

        student = db.query(
            IEMStudents
        ).filter(
            IEMStudents.student_id == row.student_id
        ).first()

        subgroup = db.query(
            LMSMentoringSubGroup
        ).filter(
            LMSMentoringSubGroup.sub_group_id ==
            row.sub_group_id
        ).first()

        result.append({
            "map_mentee_schedule_id":
                row.map_mentee_schedule_id,

            "student_id":
                row.student_id,

            "student_name":
                student.name if student else None,

            "regno":
                student.regno if student else None,

            "sub_group_id":
                row.sub_group_id,

            "sub_group_name":
                subgroup.sub_group_name if subgroup else None
        })

    return returnSuccess(result)

@router.put("/update_mentoring_session/{schedule_id}")
def update_mentoring_session(
    schedule_id: int,
    req: MentoringSessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    schedule = db.query(
        LMSMentoringSchedule
    ).filter(
        LMSMentoringSchedule.schedule_id ==
        schedule_id
    ).first()

    if not schedule:
        return returnException(
            "Session not found"
        )

    schedule.session_agenda = req.session_agenda
    schedule.modified_by = current_user["user_id"]

    db.commit()

    return returnSuccess(
        "Session updated successfully"
    )

@router.delete(
    "/delete_mentoring_session/{schedule_id}"
)
def delete_mentoring_session(
    schedule_id: int,
    db: Session = Depends(get_db)
):

    session = db.query(
        LMSMentoringSchedule
    ).filter(
        LMSMentoringSchedule.schedule_id ==
        schedule_id
    ).first()

    if not session:
        return returnException(
            "Session not found"
        )

    db.delete(session)
    db.commit()

    return returnSuccess(
        "Session deleted successfully"
    )

@router.get("/get_mentoring_session_mentees/{schedule_id}")
def get_mentoring_session_mentees(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    try:

        data = (
            db.query(
                LMSMapMenteeSchedule.student_id,
                IEMStudents.regno,
                IEMStudents.name,
                LMSMapMenteeSchedule.sub_group_id
            )
            .join(
                IEMStudents,
                IEMStudents.student_id ==
                LMSMapMenteeSchedule.student_id
            )
            .filter(
                LMSMapMenteeSchedule.schedule_id ==
                schedule_id
            )
            .all()
        )

        result = []

        for row in data:
            result.append({
                "student_id": row.student_id,
                "regno": row.regno,
                "student_name": row.name,
                "sub_group_id": row.sub_group_id
            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))
    
@router.post("/get_mentee_questionnaire_response")
def get_mentee_questionnaire_response(
    req: MenteeResponseRequest,
    db: Session = Depends(get_db)
):
    try:

        response = (
            db.query(
                LMSMenteeQuestionnaireResponse
            )
            .filter(
                LMSMenteeQuestionnaireResponse.schedule_id ==
                req.schedule_id,
                LMSMenteeQuestionnaireResponse.student_id ==
                req.student_id
            )
            .first()
        )

        if not response:
            return returnSuccess([])

        result = []

        answers = (
            db.query(
                LMSMenteeQuestionnaireResponseQue,
                LMSQuestionnairesQuestions
            )
            .join(
                LMSQuestionnairesQuestions,
                LMSQuestionnairesQuestions.questionnaire_que_id ==
                LMSMenteeQuestionnaireResponseQue.questionnaire_que_id
            )
            .filter(
                LMSMenteeQuestionnaireResponseQue.questionnaire_response_id ==
                response.questionnaire_response_id
            )
            .all()
        )

        for ans, que in answers:

            options = (
                db.query(
                    LMSMenteeQuestionnaireResponseOption,
                    LMSQuestionnairesOptions
                )
                .join(
                    LMSQuestionnairesOptions,
                    LMSQuestionnairesOptions.questionnaire_options_id ==
                    LMSMenteeQuestionnaireResponseOption.questionnaire_options_id
                )
                .filter(
                    LMSMenteeQuestionnaireResponseOption.questionnaire_response_que_id ==
                    ans.questionnaire_response_que_id
                )
                .all()
            )

            selected_options = []

            for op, opt in options:
                selected_options.append({
                    "option_id": opt.questionnaire_options_id,
                    "option_name": opt.que_option,
                    "specification": op.specification
                })

            result.append({
                "question_id": que.questionnaire_que_id,
                "question": que.question,
                "text_answer": ans.text_answer,
                "selected_options": selected_options
            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))
    
@router.post(
    "/save_generic_comment"
)
def save_generic_comment(
    schedule_id: int = Form(...),
    comment: str = Form(...),
    suggestion_type: int = Form(0),
    user_type: int = Form(0),
    attachment: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    try:

        validate_attachment(
            attachment
        )

        file_name = save_uploaded_file(
            attachment
        )

        suggestion = db.query(
            LMSMMPSessionSuggestion
        ).filter(
            LMSMMPSessionSuggestion.schedule_id ==
            schedule_id
        ).first()

        if not suggestion:

            suggestion = LMSMMPSessionSuggestion(
                schedule_id=schedule_id,
                created_by=current_user["user_id"]
            )

            db.add(suggestion)
            db.flush()

        db_comment = (
            LMSMMPSessionSuggestionGenericComments(
                session_suggestion_id=
                    suggestion.session_suggestion_id,

                comment=comment,

                attachment=file_name,

                suggestion_type=suggestion_type,

                user_type=user_type,

                created_by=
                    current_user["user_id"]
            )
        )

        db.add(db_comment)

        db.commit()

        return returnSuccess(
            "Comment Saved Successfully"
        )

    except Exception as e:

        db.rollback()

        return returnException(
            str(e)
        )
    
@router.post("/save_individual_comment")
def save_individual_comment(
    schedule_id: int = Form(...),
    mentee_id: int = Form(...),
    comment: str = Form(...),
    suggestion_type: int = Form(0),
    attachment: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    try:

        validate_attachment(
            attachment
        )

        file_name = save_uploaded_file(
            attachment
        )

        suggestion = db.query(
            LMSMMPSessionSuggestion
        ).filter(
            LMSMMPSessionSuggestion.schedule_id ==
            schedule_id
        ).first()

        if not suggestion:

            suggestion = LMSMMPSessionSuggestion(
                schedule_id=schedule_id,
                created_by=current_user["user_id"]
            )

            db.add(suggestion)
            db.flush()

        db_comment = (
            LMSMMPSessionSuggestionIndividualComments(
                session_suggestion_id=
                    suggestion.session_suggestion_id,

                comment=comment,

                attachment=file_name,

                suggestion_type=
                    suggestion_type,

                from_user_id=
                    current_user["user_id"],

                mentee_id=
                    mentee_id,

                from_user_type=1,

                created_by=
                    current_user["user_id"]
            )
        )

        db.add(db_comment)

        db.commit()

        return returnSuccess(
            "Individual Comment Saved Successfully"
        )

    except Exception as e:

        db.rollback()

        return returnException(
            str(e)
        )
    
@router.get("/get_generic_comments/{schedule_id}")
def get_generic_comments(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    try:

        data = db.query(
            LMSMMPSessionSuggestionGenericComments,
            IEMSUsers.first_name
        ).join(
            LMSMMPSessionSuggestion,
            LMSMMPSessionSuggestion.session_suggestion_id ==
            LMSMMPSessionSuggestionGenericComments.session_suggestion_id
        ).outerjoin(
            IEMSUsers,
            IEMSUsers.id ==
            LMSMMPSessionSuggestionGenericComments.created_by
        ).filter(
            LMSMMPSessionSuggestion.schedule_id ==
            schedule_id
        ).all()

        result = []

        for row, user in data:

            result.append({
                "generic_comment_id":
                    row.generic_comment_id,

                "comment":
                    row.comment,

                "attachment":
                    row.attachment,

                "created_by":
                    user,

                "created_date":
                    row.created_date
            })

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))
    
@router.get(
    "/get_individual_comments/{schedule_id}/{mentee_id}"
)
def get_individual_comments(
    schedule_id: int,
    mentee_id: int,
    db: Session = Depends(get_db)
):
    try:

        data = db.query(
            LMSMMPSessionSuggestionIndividualComments
        ).join(
            LMSMMPSessionSuggestion,
            LMSMMPSessionSuggestion.session_suggestion_id ==
            LMSMMPSessionSuggestionIndividualComments.session_suggestion_id
        ).filter(
            LMSMMPSessionSuggestion.schedule_id ==
            schedule_id,

            LMSMMPSessionSuggestionIndividualComments.mentee_id ==
            mentee_id
        ).all()

        result = []

        for row in data:

            result.append({
                "individual_comment_id":
                    row.individual_comment_id,

                "comment":
                    row.comment,

                "attachment":
                    row.attachment,

                "mentee_id":
                    row.mentee_id,

                "from_user_id":
                    row.from_user_id,

                "created_date":
                    row.created_date
            })

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))