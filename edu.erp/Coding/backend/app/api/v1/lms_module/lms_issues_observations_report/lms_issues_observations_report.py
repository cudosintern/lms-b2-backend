from datetime import datetime

from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.utils.auth_helper import (
    get_current_user
)

from app.utils.http_return_helper import (
    returnSuccess,
    returnException
)

from app.db.models import (

    LMSIssuesObservations,
    LMSIssuesObservationsHistory,

    IEMStudents,
    IEMSemester,
    IEMSAcademicBatch,
    IEMSUsers,
    Curriculum,
    IEMSCurriculum,
    IEMSCrclmTerm
)

from .lms_issues_observations_report_schema import *

router = APIRouter()

# ==========================================================
# GET CURRICULUM & TERM BY ACADEMIC BATCH
# ==========================================================
@router.get("/get_crclm_term/{academic_batch_id}")
def get_crclm_term(
    academic_batch_id: int,
    db: Session = Depends(get_db)
):

    try:

        academic_batch = db.query(
            IEMSAcademicBatch
        ).filter(
            IEMSAcademicBatch.academic_batch_id ==
            academic_batch_id
        ).first()

        if not academic_batch:

            return returnException(
                "Academic Batch not found."
            )

        semesters = db.query(
            IEMSemester
        ).filter(
            IEMSemester.academic_batch_id ==
            academic_batch_id
        ).order_by(
            IEMSemester.semester.asc()
        ).all()

        semester_map = {}

        for semester in semesters:

            semester_key = semester.semester

            if semester_key is None:
                continue

            semester_map[semester_key] = {
                "term_id":
                    semester.semester_id,

                "term_name":
                    semester.term_name
                    or semester.semester_desc
                    or f"Semester {semester_key}",

                "sort_order":
                    semester.semester
            }

        legacy_curriculums = db.query(
            IEMSCurriculum
        ).filter(
            or_(
                and_(
                    IEMSCurriculum.pgm_id ==
                    academic_batch.pgm_id,

                    IEMSCurriculum.dept_id ==
                    academic_batch.dept_id,

                    IEMSCurriculum.start_year ==
                    academic_batch.start_year
                ),
                IEMSCurriculum.crclm_id ==
                academic_batch.import_ref_crclm_id
                if academic_batch.import_ref_crclm_id
                else False
            )
        ).all()

        legacy_curriculum_ids = []

        for legacy_curriculum in legacy_curriculums:

            if legacy_curriculum.crclm_id not in legacy_curriculum_ids:

                legacy_curriculum_ids.append(
                    legacy_curriculum.crclm_id
                )

        if academic_batch.import_ref_crclm_id and (
            academic_batch.import_ref_crclm_id
            not in legacy_curriculum_ids
        ):

            legacy_curriculum_ids.append(
                academic_batch.import_ref_crclm_id
            )

        curriculum_query = db.query(
            Curriculum
        ).filter(
            Curriculum.status == 1
        )

        if legacy_curriculum_ids:

            curriculum_query = curriculum_query.filter(
                or_(
                    Curriculum.import_ref_crclm_id.in_(
                        legacy_curriculum_ids
                    ),
                    Curriculum.crclm_id.in_(
                        legacy_curriculum_ids
                    )
                )
            )

        else:

            curriculum_query = curriculum_query.filter(
                Curriculum.pgm_id ==
                academic_batch.pgm_id,

                Curriculum.start_year ==
                academic_batch.start_year
            )

        curriculums = curriculum_query.order_by(
            Curriculum.crclm_name.asc()
        ).all()

        if not curriculums:

            return returnSuccess(
                [],
                "No curriculum-term mapping found for the selected academic batch."
            )

        resolved_legacy_ids = []

        for curriculum in curriculums:

            if curriculum.import_ref_crclm_id and (
                curriculum.import_ref_crclm_id
                not in resolved_legacy_ids
            ):

                resolved_legacy_ids.append(
                    curriculum.import_ref_crclm_id
                )

            elif curriculum.crclm_id not in resolved_legacy_ids:

                resolved_legacy_ids.append(
                    curriculum.crclm_id
                )

        term_rows = []

        if resolved_legacy_ids:

            term_rows = db.query(
                IEMSCrclmTerm
            ).filter(
                IEMSCrclmTerm.crclm_id.in_(
                    resolved_legacy_ids
                )
            ).order_by(
                IEMSCrclmTerm.term_name.asc(),
                IEMSCrclmTerm.crclm_term_id.asc()
            ).all()

        terms_by_curriculum = {}

        for term_row in term_rows:

            curriculum_key = term_row.crclm_id

            if curriculum_key not in terms_by_curriculum:

                terms_by_curriculum[curriculum_key] = []

            term_display = semester_map.get(
                term_row.term_name
            )

            if term_display:

                term_id = term_display["term_id"]
                term_name = term_display["term_name"]
                sort_order = term_display["sort_order"]

            else:

                term_id = term_row.crclm_term_id
                term_name = str(term_row.term_name)
                sort_order = term_row.term_name

            duplicate_term = next(
                (
                    item for item in
                    terms_by_curriculum[curriculum_key]
                    if item["term_id"] == term_id
                ),
                None
            )

            if duplicate_term:
                continue

            terms_by_curriculum[curriculum_key].append({
                "term_id":
                    term_id,

                "term_name":
                    term_name,

                "sort_order":
                    sort_order
            })

        result = []
        seen_curriculum_ids = set()

        for curriculum in curriculums:

            if curriculum.crclm_id in seen_curriculum_ids:
                continue

            seen_curriculum_ids.add(
                curriculum.crclm_id
            )

            legacy_curriculum_id = (
                curriculum.import_ref_crclm_id
                if curriculum.import_ref_crclm_id
                else curriculum.crclm_id
            )

            terms = terms_by_curriculum.get(
                legacy_curriculum_id,
                []
            )

            ordered_terms = sorted(
                terms,
                key=lambda item: (
                    item["sort_order"]
                    if item["sort_order"] is not None
                    else 9999,
                    item["term_id"]
                )
            )

            result.append({
                "academic_batch_id":
                    academic_batch_id,

                "curriculum_id":
                    curriculum.crclm_id,

                "curriculum_name":
                    curriculum.crclm_name,

                "terms": [
                    {
                        "term_id":
                            term["term_id"],

                        "term_name":
                            term["term_name"]
                    }
                    for term in ordered_terms
                ]
            })

        if not result:

            return returnSuccess(
                [],
                "No curriculum-term mapping found for the selected academic batch."
            )

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))

# ==========================================================
# GET STUDENT DETAILS BY USN
# ==========================================================
@router.get("/get_student_by_usn/{student_usn}")
def get_student_by_usn(
    student_usn: str,
    db: Session = Depends(get_db)
):

    try:

        student = db.query(
            IEMStudents
        ).filter(
            IEMStudents.usno == student_usn
        ).first()

        if not student:

            return returnException(
                "Student not found."
            )

        result = {

            "student_id":
                student.student_id,

            "student_name":
                student.name,

            "student_usn":
                student.usno,

            "academic_batch_id":
                student.academic_batch_id,

            "semester_id":
                student.current_semester,

            "email":
                student.email,

            "mobile":
                student.mobile
        }

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))
    
    # ==========================================================
# GET ALL REPORTS OF STUDENT
# ==========================================================
@router.get("/get_issue_observations/{student_id}")
def get_issue_observations(
    student_id: int,
    db: Session = Depends(get_db)
):

    try:

        reports = db.query(
            LMSIssuesObservations
        ).filter(
            LMSIssuesObservations.ssd_id == student_id,

            LMSIssuesObservations.is_deleted == 0
        ).order_by(
            LMSIssuesObservations.created_date.desc()
        ).all()

        result = []

        for row in reports:

            mentor = db.query(
                IEMSUsers
            ).filter(
                IEMSUsers.id ==
                row.mentor_users_id
            ).first()

            result.append({

                "lms_isnob_id":
                    row.lms_isnob_id,

                "report_title":
                    row.report_title,

                "counselling_date":
                    row.counselling_date,

                "mentor_name":
                    mentor.first_name if mentor else "",

                "mentor_status":
                    row.mentor_status,

                "mentee_status":
                    row.mentee_status,

                "parent_guardian_status":
                    row.parent_guardian_status
            })

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))
    
    # ==========================================================
# GET REPORT DETAILS
# ==========================================================
@router.get("/get_issue_observation/{lms_isnob_id}")
def get_issue_observation(
    lms_isnob_id: int,
    db: Session = Depends(get_db)
):

    try:

        report = db.query(
            LMSIssuesObservations
        ).filter(
            LMSIssuesObservations.lms_isnob_id ==
            lms_isnob_id,

            LMSIssuesObservations.is_deleted == 0
        ).first()

        if not report:

            return returnException(
                "Report not found."
            )

        result = {

            "lms_isnob_id":
                report.lms_isnob_id,

            "academic_batch_id":
                report.academic_batch_id,

            "semester_id":
                report.semester_id,

            "ssd_id":
                report.ssd_id,

            "student_usn":
                report.student_usn,

            "report_title":
                report.report_title,

            "counselling_date":
                report.counselling_date,

            "mentor_users_id":
                report.mentor_users_id,

            "purpose_of_meeting_desc":
                report.purpose_of_meeting_desc,

            "observation_desc":
                report.observation_desc,

            "comm_parent_flag":
                report.comm_parent_flag,

            "comm_high_auth_flag":
                report.comm_high_auth_flag,

            "mentor_status":
                report.mentor_status,

            "mentor_agreed_date":
                report.mentor_agreed_date,

            "mentee_status":
                report.mentee_status,

            "parent_guardian_status":
                report.parent_guardian_status,

            "created_date":
                report.created_date
        }

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))
    
    # ==========================================================
# SAVE ISSUE & OBSERVATION REPORT
# ==========================================================
@router.post("/save_issue_observation")
def save_issue_observation(
    req: IssueObservationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    try:

        # ----------------------------------------------
        # Validate Student
        # ----------------------------------------------
        student = db.query(
            IEMStudents
        ).filter(
            IEMStudents.student_id == req.ssd_id
        ).first()

        if not student:

            return returnException(
                "Student not found."
            )

        # ----------------------------------------------
        # Validate Academic Batch
        # ----------------------------------------------
        batch = db.query(
            IEMSAcademicBatch
        ).filter(
            IEMSAcademicBatch.academic_batch_id ==
            req.academic_batch_id
        ).first()

        if not batch:

            return returnException(
                "Invalid Academic Batch."
            )

        # ----------------------------------------------
        # Validate Semester
        # ----------------------------------------------
        semester = db.query(
            IEMSemester
        ).filter(
            IEMSemester.semester_id ==
            req.semester_id
        ).first()

        if not semester:

            return returnException(
                "Invalid Semester."
            )

        # ----------------------------------------------
        # Validate Mentor
        # ----------------------------------------------
        mentor = db.query(
            IEMSUsers
        ).filter(
            IEMSUsers.id ==
            req.mentor_users_id
        ).first()

        if not mentor:

            return returnException(
                "Invalid Mentor."
            )

        # ----------------------------------------------
        # Create Report
        # ----------------------------------------------
        report = LMSIssuesObservations(

            academic_batch_id=req.academic_batch_id,

            semester_id=req.semester_id,

            ssd_id=req.ssd_id,

            student_usn=req.student_usn,

            report_title=req.report_title,

            counselling_date=req.counselling_date,

            mentor_users_id=req.mentor_users_id,

            purpose_of_meeting_desc=req.purpose_of_meeting_desc,

            observation_desc=req.observation_desc,

            comm_parent_flag=req.comm_parent_flag,

            comm_high_auth_flag=req.comm_high_auth_flag,

            mentor_status=req.mentor_status,

            mentee_status=req.mentee_status,

            parent_guardian_status=req.parent_guardian_status,

            created_by=current_user["user_id"]
        )

        db.add(report)

        db.commit()

        db.refresh(report)

        return returnSuccess({

            "lms_isnob_id":
                report.lms_isnob_id,

            "message":
                "Issue & Observation Report saved successfully."
        })

    except Exception as e:

        db.rollback()

        return returnException(
            str(e)
        )
# ==========================================================
# UPDATE ISSUE & OBSERVATION REPORT
# ==========================================================
@router.put("/update_issue_observation/{lms_isnob_id}")
def update_issue_observation(

    lms_isnob_id: int,

    req: IssueObservationUpdate,

    db: Session = Depends(get_db),

    current_user: dict = Depends(get_current_user)

):

    try:

        report = db.query(
            LMSIssuesObservations
        ).filter(
            LMSIssuesObservations.lms_isnob_id ==
            lms_isnob_id,

            LMSIssuesObservations.is_deleted == 0
        ).first()

        if not report:

            return returnException(
                "Issue & Observation Report not found."
            )

        # ----------------------------------------------
        # Update only provided fields
        # ----------------------------------------------

        if req.report_title is not None:

            report.report_title = req.report_title

        if req.counselling_date is not None:

            report.counselling_date = req.counselling_date

        if req.purpose_of_meeting_desc is not None:

            report.purpose_of_meeting_desc = \
                req.purpose_of_meeting_desc

        if req.observation_desc is not None:

            report.observation_desc = \
                req.observation_desc

        if req.comm_parent_flag is not None:

            report.comm_parent_flag = \
                req.comm_parent_flag

        if req.comm_high_auth_flag is not None:

            report.comm_high_auth_flag = \
                req.comm_high_auth_flag

        if req.mentor_status is not None:

            report.mentor_status = \
                req.mentor_status

        if req.mentee_status is not None:

            report.mentee_status = \
                req.mentee_status

        if req.parent_guardian_status is not None:

            report.parent_guardian_status = \
                req.parent_guardian_status

        report.modified_by = current_user["user_id"]

        report.modified_date = datetime.now()

        db.commit()

        db.refresh(report)

        return returnSuccess({

            "lms_isnob_id":
                report.lms_isnob_id,

            "message":
                "Issue & Observation Report updated successfully."
        })

    except Exception as e:

        db.rollback()

        return returnException(
            str(e)
        )
    
    # ==========================================================
# DELETE ISSUE & OBSERVATION REPORT
# ==========================================================
@router.delete("/delete_issue_observation/{lms_isnob_id}")
def delete_issue_observation(
    lms_isnob_id: int,
    req: DeleteIssueObservation,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    try:

        report = db.query(
            LMSIssuesObservations
        ).filter(
            LMSIssuesObservations.lms_isnob_id ==
            lms_isnob_id,

            LMSIssuesObservations.is_deleted == 0
        ).first()

        if not report:

            return returnException(
                "Issue & Observation Report not found."
            )

        report.is_deleted = 1

        report.delete_reason_desc = \
            req.delete_reason_desc

        report.modified_by = \
            current_user["user_id"]

        report.modified_date = \
            datetime.now()

        db.commit()

        return returnSuccess(
            "Issue & Observation Report deleted successfully."
        )

    except Exception as e:

        db.rollback()

        return returnException(str(e))
    
# ==========================================================
# GET REPORT HISTORY
# ==========================================================
@router.get("/get_issue_observation_history/{lms_isnob_id}")
def get_issue_observation_history(
    lms_isnob_id: int,
    db: Session = Depends(get_db)
):

    try:

        history = db.query(
            LMSIssuesObservationsHistory
        ).filter(
            LMSIssuesObservationsHistory.lms_isnob_id ==
            lms_isnob_id
        ).order_by(
            LMSIssuesObservationsHistory.action_timestamp.desc()
        ).all()

        result = []

        for row in history:

            user = db.query(
                IEMSUsers
            ).filter(
                IEMSUsers.id ==
                row.modified_by
            ).first()

            result.append({

                "history_id":
                    row.history_id,

                "action_type":
                    row.action_type,

                "report_title":
                    row.report_title,

                "mentor_status":
                    row.mentor_status,

                "mentee_status":
                    row.mentee_status,

                "parent_guardian_status":
                    row.parent_guardian_status,

                "modified_by":
                    user.first_name if user else "",

                "action_timestamp":
                    row.action_timestamp
            })

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))
    
    # ==========================================================
# UPDATE MENTOR STATUS
# ==========================================================
@router.put("/mentor_agree/{lms_isnob_id}")
def mentor_agree(

    lms_isnob_id: int,

    req: MentorStatusUpdate,

    db: Session = Depends(get_db),

    current_user: dict = Depends(get_current_user)

):

    try:

        report = db.query(
            LMSIssuesObservations
        ).filter(
            LMSIssuesObservations.lms_isnob_id ==
            lms_isnob_id
        ).first()

        if not report:

            return returnException(
                "Report not found."
            )

        report.mentor_status = req.mentor_status

        report.mentor_agreed_date = datetime.now()

        report.modified_by = current_user["user_id"]

        report.modified_date = datetime.now()

        db.commit()

        return returnSuccess(
            "Mentor status updated successfully."
        )

    except Exception as e:

        db.rollback()

        return returnException(str(e))
    
