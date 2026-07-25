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
    LMSIssuesObservations,
    LMSIssuesObservationsHistory,
    IEMStudents,
    IEMSUsers,
    IEMSAcademicBatch,
    IEMSemester,
    LMSMentorsGroupTerms,
    LMSGroupMentees
)

from .lms_stud_issues_observations_report_schema import *

router = APIRouter()

# ==========================================================
# GET STUDENT ISSUE & OBSERVATION REPORTS
# ==========================================================
@router.get("/get_student_issue_observations/{student_id}")
def get_student_issue_observations(
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

        for report in reports:

            mentor = db.query(
                IEMSUsers
            ).filter(
                IEMSUsers.id == report.mentor_users_id
            ).first()

            # Report Status
            if report.mentor_status == 2 and report.mentee_status == 1:
                report_status = "Finalized"
            else:
                report_status = "In Progress"

            # Show Agree Button
            can_agree = (
                report.mentor_status == 2 and
                report.mentee_status == 0
            )

            result.append({

                "lms_isnob_id": report.lms_isnob_id,

                "report_title": report.report_title,

                "counselling_date": report.counselling_date,

                "mentor_name": (
                    mentor.first_name if mentor else ""
                ),

                "mentor_status": report.mentor_status,

                "mentee_status": report.mentee_status,

                "report_status": report_status,

                "can_agree": can_agree

            })

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))
    
    # ==========================================================
# GET STUDENT ISSUE & OBSERVATION DETAILS
# ==========================================================
@router.get("/get_student_issue_observation/{lms_isnob_id}/{student_id}")
def get_student_issue_observation(
    lms_isnob_id: int,
    student_id: int,
    db: Session = Depends(get_db)
):

    try:

        report = db.query(
            LMSIssuesObservations
        ).filter(
            LMSIssuesObservations.lms_isnob_id == lms_isnob_id,
            LMSIssuesObservations.ssd_id == student_id,
            LMSIssuesObservations.is_deleted == 0
        ).first()

        if not report:

            return returnException(
                "Issue & Observation Report not found."
            )

        mentor = db.query(
            IEMSUsers
        ).filter(
            IEMSUsers.id == report.mentor_users_id
        ).first()

        # ----------------------------------------
        # Report Status
        # ----------------------------------------
        if report.mentor_status == 2 and report.mentee_status == 1:
            report_status = "Finalized"
        else:
            report_status = "In Progress"

        # ----------------------------------------
        # Show Agree Button
        # ----------------------------------------
        can_agree = (
            report.mentor_status == 2 and
            report.mentee_status == 0
        )

        result = {

            "lms_isnob_id": report.lms_isnob_id,

            "academic_batch_id": report.academic_batch_id,

            "semester_id": report.semester_id,

            "ssd_id": report.ssd_id,

            "student_usn": report.student_usn,

            "report_title": report.report_title,

            "counselling_date": report.counselling_date,

            "mentor_users_id": report.mentor_users_id,

            "mentor_name": mentor.first_name if mentor else "",

            "purpose_of_meeting_desc": report.purpose_of_meeting_desc,

            "observation_desc": report.observation_desc,

            "comm_parent_flag": report.comm_parent_flag,

            "comm_high_auth_flag": report.comm_high_auth_flag,

            "mentor_status": report.mentor_status,

            "mentee_status": report.mentee_status,

            "report_status": report_status,

            "can_agree": can_agree,

            "created_date": report.created_date,

            "modified_date": report.modified_date

        }

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))
    
    # ==========================================================
# STUDENT AGREE TO ISSUE & OBSERVATION REPORT
# ==========================================================
@router.put("/student_agree/{lms_isnob_id}/{student_id}")
def student_agree(
    lms_isnob_id: int,
    student_id: int,
    db: Session = Depends(get_db)
):

    try:

        report = db.query(
            LMSIssuesObservations
        ).filter(
            LMSIssuesObservations.lms_isnob_id == lms_isnob_id,
            LMSIssuesObservations.ssd_id == student_id,
            LMSIssuesObservations.is_deleted == 0
        ).first()

        if not report:

            return returnException(
                "Issue & Observation Report not found."
            )

        # ---------------------------------------------
        # Mentor should have clicked Save & Agree
        # ---------------------------------------------
        if report.mentor_status != 2:

            return returnException(
                "Mentor has not agreed yet."
            )

        # ---------------------------------------------
        # Already agreed
        # ---------------------------------------------
        if report.mentee_status == 1:

            return returnException(
                "Report already agreed."
            )

        # ---------------------------------------------
        # Update Student Agreement
        # ---------------------------------------------
        report.mentee_status = 1

        report.modified_by = student_id

        report.modified_date = datetime.now()

        # Uncomment if you add this column
        # report.mentee_agree_date = datetime.now()

        db.commit()

        db.refresh(report)

        return returnSuccess({
            "lms_isnob_id": report.lms_isnob_id,
            "message": "Report agreed successfully."
        })

    except Exception as e:

        db.rollback()

        return returnException(str(e))
    
# ==========================================================
# GET ACADEMIC BATCHES MAPPED TO STUDENT
# ==========================================================
@router.get("/get_student_academic_batches/{student_id}")
def get_student_academic_batches(
    student_id: int,
    db: Session = Depends(get_db)
):
    try:

        batches = (
            db.query(IEMSAcademicBatch)
            .join(
                LMSMentorsGroupTerms,
                LMSMentorsGroupTerms.academic_batch_id == IEMSAcademicBatch.academic_batch_id
            )
            .join(
                LMSGroupMentees,
                LMSGroupMentees.mentors_group_terms_id == LMSMentorsGroupTerms.mentors_group_terms_id
            )
            .filter(
                LMSGroupMentees.student_id == student_id
            )
            .distinct()
            .order_by(IEMSAcademicBatch.academic_batch_desc)
            .all()
        )

        result = []

        for batch in batches:
            result.append({
                "academic_batch_id": batch.academic_batch_id,
                "academic_batch_code": batch.academic_batch_code,
                "academic_batch_desc": batch.academic_batch_desc
            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))
# ==========================================================
# GET SEMESTERS MAPPED TO STUDENT
# ==========================================================
@router.get("/get_student_semesters/{student_id}/{academic_batch_id}")
def get_student_semesters(
    student_id: int,
    academic_batch_id: int,
    db: Session = Depends(get_db)
):
    try:

        semesters = (
            db.query(IEMSemester)
            .join(
                LMSMentorsGroupTerms,
                LMSMentorsGroupTerms.semester_id == IEMSemester.semester_id
            )
            .join(
                LMSGroupMentees,
                LMSGroupMentees.mentors_group_terms_id == LMSMentorsGroupTerms.mentors_group_terms_id
            )
            .filter(
                LMSGroupMentees.student_id == student_id,
                LMSMentorsGroupTerms.academic_batch_id == academic_batch_id
            )
            .distinct()
            .order_by(IEMSemester.semester_id)
            .all()
        )

        result = []

        for semester in semesters:
            result.append({
                "semester_id": semester.semester_id,
                "semester": semester.semester
            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))
    
    # ==========================================================
# MENTOR SAVE & AGREE
# ==========================================================
@router.put("/mentor_save_agree/{lms_isnob_id}")
def mentor_save_agree(
    lms_isnob_id: int,
    db: Session = Depends(get_db)
):

    try:

        report = db.query(
            LMSIssuesObservations
        ).filter(
            LMSIssuesObservations.lms_isnob_id == lms_isnob_id,
            LMSIssuesObservations.is_deleted == 0
        ).first()

        if not report:

            return returnException(
                "Issue & Observation Report not found."
            )

        # Already agreed
        if report.mentor_status == 2:

            return returnException(
                "Report is already agreed by mentor."
            )

        # Save & Agree
        report.mentor_status = 2

        report.modified_by = report.mentor_users_id

        report.modified_date = datetime.now()

        db.commit()

        db.refresh(report)

        return returnSuccess({

            "lms_isnob_id": report.lms_isnob_id,

            "mentor_status": report.mentor_status,

            "message": "Report saved and agreed successfully."

        })

    except Exception as e:

        db.rollback()

        return returnException(str(e))
    
    # ==========================================================
# GET STUDENT ISSUE & OBSERVATION HISTORY
# ==========================================================
@router.get("/get_student_issue_observation_history/{lms_isnob_id}/{student_id}")
def get_student_issue_observation_history(
    lms_isnob_id: int,
    student_id: int,
    db: Session = Depends(get_db)
):

    try:

        # Verify report belongs to student
        report = db.query(
            LMSIssuesObservations
        ).filter(
            LMSIssuesObservations.lms_isnob_id == lms_isnob_id,
            LMSIssuesObservations.ssd_id == student_id,
            LMSIssuesObservations.is_deleted == 0
        ).first()

        if not report:
            return returnException(
                "Issue & Observation Report not found."
            )

        history = db.query(
            LMSIssuesObservationsHistory
        ).filter(
            LMSIssuesObservationsHistory.lms_isnob_id == lms_isnob_id
        ).order_by(
            LMSIssuesObservationsHistory.action_timestamp.desc()
        ).all()

        result = []

        for item in history:

            mentor = db.query(IEMSUsers).filter(
                IEMSUsers.id == item.mentor_users_id
            ).first()

            result.append({

                "history_id": item.history_id,

                "action_type": item.action_type,

                "action_timestamp": item.action_timestamp,

                "report_title": item.report_title,

                "counselling_date": item.counselling_date,

                "purpose_of_meeting_desc": item.purpose_of_meeting_desc,

                "observation_desc": item.observation_desc,

                "comm_parent_flag": item.comm_parent_flag,

                "comm_high_auth_flag": item.comm_high_auth_flag,

                "mentor_status": item.mentor_status,

                "mentee_status": item.mentee_status,

                "mentor_name": mentor.first_name if mentor else None

            })

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))


# ==========================================================
# GET STUDENT BY USN (for Issues & Observations lookup)
# ==========================================================
@router.get("/get_student_by_usn/{student_usn}")
def get_student_by_usn(
    student_usn: str,
    db: Session = Depends(get_db)
):
    try:
        student = db.query(IEMStudents).filter(
            IEMStudents.usno == student_usn
        ).first()

        if not student:
            return returnException("Student not found")

        return returnSuccess({
            "student_id": student.student_id,
            "student_name": student.name or "",
            "student_usn": student.usno or "",
            "academic_batch_id": student.academic_batch_id,
            "semester_id": student.semester_id,
            "email": student.email,
            "mobile": getattr(student, "mobile", None)
        })
    except Exception as e:
        return returnException(str(e))


# ==========================================================
# GET ISSUE OBSERVATIONS BY STUDENT ID (frontend alias)
# ==========================================================
@router.get("/get_issue_observations/{student_id}")
def get_issue_observations(
    student_id: int,
    db: Session = Depends(get_db)
):
    try:
        reports = db.query(LMSIssuesObservations).filter(
            LMSIssuesObservations.ssd_id == student_id,
            LMSIssuesObservations.is_deleted == 0
        ).order_by(LMSIssuesObservations.created_date.desc()).all()

        result = []
        for report in reports:
            mentor = db.query(IEMSUsers).filter(
                IEMSUsers.id == report.mentor_users_id
            ).first()
            result.append({
                "lms_isnob_id": report.lms_isnob_id,
                "report_title": report.report_title,
                "counselling_date": report.counselling_date,
                "mentor_name": mentor.first_name if mentor else "",
                "mentor_status": report.mentor_status,
                "mentee_status": report.mentee_status,
                "parent_guardian_status": report.parent_guardian_status
            })
        return returnSuccess(result)
    except Exception as e:
        return returnException(str(e))


# ==========================================================
# GET CURRICULUM TERMS BY ACADEMIC BATCH
# ==========================================================
@router.get("/get_crclm_term/{academic_batch_id}")
def get_crclm_term(
    academic_batch_id: int,
    db: Session = Depends(get_db)
):
    try:
        batch = db.query(IEMSAcademicBatch).filter(
            IEMSAcademicBatch.academic_batch_id == academic_batch_id
        ).first()

        if not batch:
            return returnException("Academic batch not found")

        terms = db.query(LMSMentorsGroupTerms).filter(
            LMSMentorsGroupTerms.academic_batch_id == academic_batch_id
        ).all()

        result = {
            "academic_batch_id": academic_batch_id,
            "curriculum_name": getattr(batch, "academic_batch_desc", "") or getattr(batch, "academic_batch_code", ""),
            "terms": [
                {
                    "term_id": t.mentors_group_terms_id,
                    "term_name": getattr(t, "term_name", None) or f"Term {t.mentors_group_terms_id}"
                }
                for t in terms
            ]
        }
        return returnSuccess(result)
    except Exception as e:
        return returnException(str(e))


# ==========================================================
# GET ISSUE OBSERVATION DETAIL BY ID (simplified, no student_id required)
# ==========================================================
@router.get("/get_issue_observation/{lms_isnob_id}")
def get_issue_observation(
    lms_isnob_id: int,
    db: Session = Depends(get_db)
):
    try:
        report = db.query(LMSIssuesObservations).filter(
            LMSIssuesObservations.lms_isnob_id == lms_isnob_id,
            LMSIssuesObservations.is_deleted == 0
        ).first()

        if not report:
            return returnException("Issue & Observation Report not found.")

        mentor = db.query(IEMSUsers).filter(
            IEMSUsers.id == report.mentor_users_id
        ).first()

        return returnSuccess({
            "lms_isnob_id": report.lms_isnob_id,
            "academic_batch_id": report.academic_batch_id,
            "semester_id": report.semester_id,
            "ssd_id": report.ssd_id,
            "student_usn": report.student_usn,
            "report_title": report.report_title,
            "counselling_date": report.counselling_date,
            "mentor_users_id": report.mentor_users_id,
            "mentor_name": mentor.first_name if mentor else "",
            "purpose_of_meeting_desc": report.purpose_of_meeting_desc,
            "observation_desc": report.observation_desc,
            "comm_parent_flag": report.comm_parent_flag,
            "comm_high_auth_flag": report.comm_high_auth_flag,
            "mentor_status": report.mentor_status,
            "mentor_agreed_date": report.modified_date if report.mentor_status == 2 else None,
            "mentee_status": report.mentee_status,
            "parent_guardian_status": report.parent_guardian_status,
            "created_date": report.created_date
        })
    except Exception as e:
        return returnException(str(e))


# ==========================================================
# GET ISSUE OBSERVATION HISTORY BY REPORT ID (simplified)
# ==========================================================
@router.get("/get_issue_observation_history/{lms_isnob_id}")
def get_issue_observation_history(
    lms_isnob_id: int,
    db: Session = Depends(get_db)
):
    try:
        history = db.query(LMSIssuesObservationsHistory).filter(
            LMSIssuesObservationsHistory.lms_isnob_id == lms_isnob_id
        ).order_by(LMSIssuesObservationsHistory.action_timestamp.desc()).all()

        result = []
        for item in history:
            mentor = db.query(IEMSUsers).filter(
                IEMSUsers.id == item.mentor_users_id
            ).first()
            result.append({
                "history_id": item.history_id,
                "action_type": item.action_type,
                "report_title": item.report_title,
                "mentor_status": item.mentor_status,
                "mentee_status": item.mentee_status,
                "parent_guardian_status": item.parent_guardian_status,
                "modified_by": mentor.first_name if mentor else "",
                "action_timestamp": item.action_timestamp
            })
        return returnSuccess(result)
    except Exception as e:
        return returnException(str(e))


# ==========================================================
# POST SAVE ISSUE OBSERVATION
# ==========================================================
@router.post("/save_issue_observation")
def save_issue_observation(
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from pydantic import BaseModel
        user_id = current_user.get("user_id")

        counselling_date = payload.get("counselling_date")
        if isinstance(counselling_date, str):
            from datetime import datetime as dt
            try:
                counselling_date = dt.strptime(counselling_date, "%Y-%m-%d")
            except Exception:
                counselling_date = None

        report = LMSIssuesObservations(
            academic_batch_id=payload.get("academic_batch_id"),
            semester_id=payload.get("semester_id"),
            ssd_id=payload.get("ssd_id"),
            student_usn=payload.get("student_usn"),
            report_title=payload.get("report_title", ""),
            counselling_date=counselling_date,
            mentor_users_id=payload.get("mentor_users_id"),
            purpose_of_meeting_desc=payload.get("purpose_of_meeting_desc"),
            observation_desc=payload.get("observation_desc"),
            comm_parent_flag=payload.get("comm_parent_flag", 0),
            comm_high_auth_flag=payload.get("comm_high_auth_flag", 0),
            mentor_status=payload.get("mentor_status", 0),
            mentee_status=payload.get("mentee_status", 0),
            parent_guardian_status=payload.get("parent_guardian_status", 0),
            created_by=user_id,
            is_deleted=0
        )
        db.add(report)
        db.flush()

        # Save history entry
        history = LMSIssuesObservationsHistory(
            lms_isnob_id=report.lms_isnob_id,
            academic_batch_id=report.academic_batch_id,
            semester_id=report.semester_id,
            ssd_id=report.ssd_id,
            student_usn=report.student_usn,
            report_title=report.report_title,
            counselling_date=report.counselling_date,
            mentor_users_id=report.mentor_users_id,
            purpose_of_meeting_desc=report.purpose_of_meeting_desc,
            observation_desc=report.observation_desc,
            comm_parent_flag=report.comm_parent_flag,
            comm_high_auth_flag=report.comm_high_auth_flag,
            mentor_status=report.mentor_status,
            mentee_status=report.mentee_status,
            parent_guardian_status=report.parent_guardian_status,
            created_by=user_id,
            is_deleted=0,
            action_type="CREATED",
            action_timestamp=datetime.now()
        )
        db.add(history)
        db.commit()

        return returnSuccess({
            "lms_isnob_id": report.lms_isnob_id,
            "message": "Issue & Observation Report saved successfully."
        })
    except Exception as e:
        db.rollback()
        return returnException(str(e))


# ==========================================================
# PUT UPDATE ISSUE OBSERVATION
# ==========================================================
@router.put("/update_issue_observation/{lms_isnob_id}")
def update_issue_observation(
    lms_isnob_id: int,
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_id = current_user.get("user_id")
        report = db.query(LMSIssuesObservations).filter(
            LMSIssuesObservations.lms_isnob_id == lms_isnob_id,
            LMSIssuesObservations.is_deleted == 0
        ).first()

        if not report:
            return returnException("Issue & Observation Report not found.")

        if "report_title" in payload:
            report.report_title = payload["report_title"]
        if "counselling_date" in payload and payload["counselling_date"]:
            from datetime import datetime as dt
            try:
                report.counselling_date = dt.strptime(payload["counselling_date"], "%Y-%m-%d")
            except Exception:
                pass
        if "purpose_of_meeting_desc" in payload:
            report.purpose_of_meeting_desc = payload["purpose_of_meeting_desc"]
        if "observation_desc" in payload:
            report.observation_desc = payload["observation_desc"]
        if "comm_parent_flag" in payload:
            report.comm_parent_flag = payload["comm_parent_flag"]
        if "comm_high_auth_flag" in payload:
            report.comm_high_auth_flag = payload["comm_high_auth_flag"]
        if "mentor_status" in payload:
            report.mentor_status = payload["mentor_status"]
        if "mentee_status" in payload:
            report.mentee_status = payload["mentee_status"]
        if "parent_guardian_status" in payload:
            report.parent_guardian_status = payload["parent_guardian_status"]

        report.modified_by = user_id
        report.modified_date = datetime.now()

        # Save history entry
        history = LMSIssuesObservationsHistory(
            lms_isnob_id=report.lms_isnob_id,
            academic_batch_id=report.academic_batch_id,
            semester_id=report.semester_id,
            ssd_id=report.ssd_id,
            student_usn=report.student_usn,
            report_title=report.report_title,
            counselling_date=report.counselling_date,
            mentor_users_id=report.mentor_users_id,
            purpose_of_meeting_desc=report.purpose_of_meeting_desc,
            observation_desc=report.observation_desc,
            comm_parent_flag=report.comm_parent_flag,
            comm_high_auth_flag=report.comm_high_auth_flag,
            mentor_status=report.mentor_status,
            mentee_status=report.mentee_status,
            parent_guardian_status=report.parent_guardian_status,
            modified_by=user_id,
            modified_date=datetime.now(),
            is_deleted=0,
            action_type="UPDATED",
            action_timestamp=datetime.now()
        )
        db.add(history)
        db.commit()

        return returnSuccess({
            "lms_isnob_id": report.lms_isnob_id,
            "message": "Issue & Observation Report updated successfully."
        })
    except Exception as e:
        db.rollback()
        return returnException(str(e))


# ==========================================================
# DELETE ISSUE OBSERVATION (soft delete)
# ==========================================================
@router.delete("/delete_issue_observation/{lms_isnob_id}")
def delete_issue_observation(
    lms_isnob_id: int,
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_id = current_user.get("user_id")
        report = db.query(LMSIssuesObservations).filter(
            LMSIssuesObservations.lms_isnob_id == lms_isnob_id,
            LMSIssuesObservations.is_deleted == 0
        ).first()

        if not report:
            return returnException("Issue & Observation Report not found.")

        report.is_deleted = 1
        report.delete_reason_desc = payload.get("delete_reason_desc", "")
        report.modified_by = user_id
        report.modified_date = datetime.now()

        # Save history entry
        history = LMSIssuesObservationsHistory(
            lms_isnob_id=report.lms_isnob_id,
            academic_batch_id=report.academic_batch_id,
            semester_id=report.semester_id,
            ssd_id=report.ssd_id,
            student_usn=report.student_usn,
            report_title=report.report_title,
            counselling_date=report.counselling_date,
            mentor_users_id=report.mentor_users_id,
            purpose_of_meeting_desc=report.purpose_of_meeting_desc,
            observation_desc=report.observation_desc,
            comm_parent_flag=report.comm_parent_flag,
            comm_high_auth_flag=report.comm_high_auth_flag,
            mentor_status=report.mentor_status,
            mentee_status=report.mentee_status,
            parent_guardian_status=report.parent_guardian_status,
            modified_by=user_id,
            modified_date=datetime.now(),
            is_deleted=1,
            delete_reason_desc=payload.get("delete_reason_desc", ""),
            action_type="DELETED",
            action_timestamp=datetime.now()
        )
        db.add(history)
        db.commit()

        return returnSuccess("Issue & Observation Report deleted successfully.")
    except Exception as e:
        db.rollback()
        return returnException(str(e))


# ==========================================================
# PUT MENTOR AGREE (frontend alias for mentor_save_agree)
# ==========================================================
@router.put("/mentor_agree/{lms_isnob_id}")
def mentor_agree(
    lms_isnob_id: int,
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_id = current_user.get("user_id")
        report = db.query(LMSIssuesObservations).filter(
            LMSIssuesObservations.lms_isnob_id == lms_isnob_id,
            LMSIssuesObservations.is_deleted == 0
        ).first()

        if not report:
            return returnException("Issue & Observation Report not found.")

        mentor_status = payload.get("mentor_status", report.mentor_status)
        report.mentor_status = mentor_status
        report.modified_by = user_id
        report.modified_date = datetime.now()

        # Save history entry
        history = LMSIssuesObservationsHistory(
            lms_isnob_id=report.lms_isnob_id,
            academic_batch_id=report.academic_batch_id,
            semester_id=report.semester_id,
            ssd_id=report.ssd_id,
            student_usn=report.student_usn,
            report_title=report.report_title,
            counselling_date=report.counselling_date,
            mentor_users_id=report.mentor_users_id,
            purpose_of_meeting_desc=report.purpose_of_meeting_desc,
            observation_desc=report.observation_desc,
            comm_parent_flag=report.comm_parent_flag,
            comm_high_auth_flag=report.comm_high_auth_flag,
            mentor_status=report.mentor_status,
            mentee_status=report.mentee_status,
            parent_guardian_status=report.parent_guardian_status,
            modified_by=user_id,
            modified_date=datetime.now(),
            is_deleted=0,
            action_type="MENTOR_AGREED",
            action_timestamp=datetime.now()
        )
        db.add(history)
        db.commit()

        return returnSuccess({
            "lms_isnob_id": report.lms_isnob_id,
            "message": "Mentor agreed successfully."
        })
    except Exception as e:
        db.rollback()
        return returnException(str(e))
