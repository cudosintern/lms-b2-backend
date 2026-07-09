from datetime import datetime

from fastapi import (
    APIRouter,
    Depends
)

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
    IEMSUsers
)

from .lms_issues_observations_report_schema import *

router = APIRouter()

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
    
