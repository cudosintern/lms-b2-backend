from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess, returnException
from app.db.models import (
    IEMStudents,
    IEMSDepartment,
    IEMProgram,
    LMSMenteeQuestionnaireResponse,
    LMSMenteeQuestionnaireResponseQue,
    LMSMenteeQuestionnaireResponseOption,
    LMSQuestionnairesQuestions,
    LMSQuestionnairesOptions,
    LMSMentoringSchedule,
)

router = APIRouter()


@router.get("/info")
def get_student_info(
    student_id: int = Query(..., description="Student ID"),
    db: Session = Depends(get_db)
):
    """
    Return full personal-profile + academic + marks + questionnaire info
    for the MMP Report page.
    Called by frontend:  GET api/v1/student-details/info?student_id=<id>
    """
    try:
        student = db.query(IEMStudents).filter(
            IEMStudents.student_id == student_id
        ).first()

        if not student:
            return returnException("Student not found")

        # ── Department ──────────────────────────────────────────────
        department = None
        if student.department_id:
            department = db.query(IEMSDepartment).filter(
                IEMSDepartment.dept_id == student.department_id
            ).first()

        # ── Program ─────────────────────────────────────────────────
        program = None
        if student.program_id:
            program = db.query(IEMProgram).filter(
                IEMProgram.pgm_id == student.program_id
            ).first()

        # ── Personal Info ────────────────────────────────────────────
        personal_info = {
            "full_name":      student.name or "",
            "usn":            student.usno or "",
            "application_no": student.application_no or "",
            "regno":          student.regno or "",
            "department":     department.dept_name if department else "",
            "program":        program.pgm_title if program else "",
            "curriculum":     "",
            "counsellor_name": "",
            "father_name":       student.fathers_name or "",
            "father_profession": student.fathers_occupation or "",
            "mother_name":       student.mothers_name or "",
            "mother_profession": student.mothers_occupation or "",
            "parent_guardian_name": student.guardian_name or "",
            "relationship":      "Guardian" if student.guardian_name else "",
            "home_phone":    student.fathers_phone or "",
            "cell_phone":    student.mobile or "",
            "contact":       student.mobile or "",
            "email":         student.email or "",
            "blood_group":   student.blood_group or "",
            "dob":           str(student.dob) if student.dob else "",
            "gender":        student.gender or "",
            "nationality":   student.nationality or "",
        }

        # ── Addresses ────────────────────────────────────────────────
        # Try to pull from iems_student_parents table or leave blank
        addresses = {
            "permanent": {
                "address":     "",
                "address2":    "",
                "city":        "",
                "state":       "",
                "country":     "",
                "postal_code": "",
            },
            "correspondence": {
                "address":     "",
                "address2":    "",
                "city":        "",
                "state":       "",
                "country":     "",
                "postal_code": "",
            },
        }

        try:
            addr_sql = """
                SELECT permanent_address1, permanent_address2,
                       permanent_city, permanent_state,
                       permanent_country, permanent_phone
                FROM iems_student_parents
                WHERE student_id = :sid
                LIMIT 1
            """
            addr_row = db.execute(text(addr_sql), {"sid": student_id}).fetchone()
            if addr_row:
                addresses["permanent"] = {
                    "address":     addr_row[0] or "",
                    "address2":    addr_row[1] or "",
                    "city":        addr_row[2] or "",
                    "state":       addr_row[3] or "",
                    "country":     addr_row[4] or "",
                    "postal_code": "",
                }
        except Exception:
            pass

        # ── Education Details (10th / 12th) ──────────────────────────
        education_details = {
            "tenth_board":      "",
            "tenth_year":       "",
            "tenth_percentage": "",
            "twelfth_board":    "",
            "twelfth_year":     "",
            "twelfth_percentage": "",
        }
        try:
            edu_sql = """
                SELECT education_qualification_master_id, pass_year, percentage, board_or_university_id
                FROM iems_student_educational_qualification
                WHERE student_id = :sid
                ORDER BY education_qualification_master_id ASC
            """
            edu_rows = db.execute(text(edu_sql), {"sid": student_id}).fetchall()

            for row in edu_rows:
                qual_id = row[0]
                year = str(row[1]) if row[1] else ""
                pct = str(row[2]) if row[2] else ""
                board = str(row[3]) if row[3] else ""
                if qual_id == 1:  # 10th
                    education_details["tenth_year"]       = year
                    education_details["tenth_percentage"] = pct
                    education_details["tenth_board"]      = board
                elif qual_id == 2:  # 12th / PUC
                    education_details["twelfth_year"]       = year
                    education_details["twelfth_percentage"] = pct
                    education_details["twelfth_board"]      = board
        except Exception:
            pass

        # ── Marks & Attendance ───────────────────────────────────────
        marks_details = []
        attendance_details = []
        try:
            marks_sql = """
                SELECT 
                    sc.semester_id         AS semester,
                    c.course_code          AS course_code,
                    c.course_title         AS course_title,
                    ot.occasion_name       AS occasion_name,
                    cm.secured_marks       AS secured_marks,
                    cm.total_marks         AS total_marks
                FROM iems_cia_marks cm
                JOIN iems_s_courses c        ON cm.course_id = c.course_id
                JOIN iems_s_occasion_type ot ON cm.occasion_type_id = ot.occasion_type_id
                JOIN iems_s_courses sc       ON cm.course_id = sc.course_id
                WHERE cm.student_id = :sid
                ORDER BY c.course_code, ot.occasion_name
            """
            marks_rows = db.execute(text(marks_sql), {"sid": student_id}).fetchall()

            # Group by course
            course_map: dict = {}
            for row in marks_rows:
                sem        = row[0]
                code       = row[1] or ""
                title      = row[2] or ""
                occ_name   = row[3] or ""
                sec_marks  = row[4]
                tot_marks  = row[5]

                if code not in course_map:
                    course_map[code] = {
                        "semester":    sem,
                        "course_code": code,
                        "course_title": title,
                        "occasions":   []
                    }
                course_map[code]["occasions"].append({
                    "occasion_name":  occ_name,
                    "secured_marks":  sec_marks,
                    "total_marks":    tot_marks,
                })

            marks_details = list(course_map.values())
        except Exception:
            pass

        try:
            att_sql = """
                SELECT c.course_code, 
                       ROUND(SUM(a.attended_count) * 100.0 / NULLIF(SUM(a.held_count), 0), 2) AS attendance_percentage
                FROM iems_attendance a
                JOIN iems_s_courses c ON a.course_id = c.course_id
                WHERE a.student_id = :sid
                GROUP BY c.course_code
            """
            att_rows = db.execute(text(att_sql), {"sid": student_id}).fetchall()
            attendance_details = [
                {"course_code": r[0], "attendance_percentage": float(r[1]) if r[1] else None}
                for r in att_rows
            ]
        except Exception:
            pass

        # ── Questionnaire Responses ──────────────────────────────────
        questionnaire_responses = []
        try:
            responses = db.query(
                LMSMenteeQuestionnaireResponse
            ).filter(
                LMSMenteeQuestionnaireResponse.student_id == student_id
            ).order_by(LMSMenteeQuestionnaireResponse.created_date.desc()).all()

            for resp in responses:
                # Get schedule/session info
                schedule = db.query(LMSMentoringSchedule).filter(
                    LMSMentoringSchedule.schedule_id == resp.schedule_id
                ).first()

                response_ques = db.query(LMSMenteeQuestionnaireResponseQue).filter(
                    LMSMenteeQuestionnaireResponseQue.questionnaire_response_id ==
                    resp.questionnaire_response_id
                ).all()

                for rq in response_ques:
                    que = db.query(LMSQuestionnairesQuestions).filter(
                        LMSQuestionnairesQuestions.questionnaire_que_id ==
                        rq.questionnaire_que_id
                    ).first()

                    # Build response value
                    response_value = rq.text_answer or ""
                    if not response_value:
                        sel_opts = db.query(
                            LMSMenteeQuestionnaireResponseOption,
                            LMSQuestionnairesOptions
                        ).join(
                            LMSQuestionnairesOptions,
                            LMSQuestionnairesOptions.questionnaire_options_id ==
                            LMSMenteeQuestionnaireResponseOption.questionnaire_options_id
                        ).filter(
                            LMSMenteeQuestionnaireResponseOption.questionnaire_response_que_id ==
                            rq.questionnaire_response_que_id
                        ).all()
                        if sel_opts:
                            response_value = ", ".join(
                                opt.specification for _, opt in sel_opts
                                if opt.specification
                            )

                    questionnaire_responses.append({
                        "question_text":  que.question if que else "",
                        "response_value": response_value,
                        "submitted_at":   resp.created_date.strftime("%Y-%m-%d %H:%M:%S")
                            if resp.created_date else "",
                        "session_agenda": schedule.session_agenda if schedule else "",
                    })
        except Exception:
            pass

        return returnSuccess({
            "personal_info":            personal_info,
            "addresses":                addresses,
            "education_details":        education_details,
            "marks_details":            marks_details,
            "attendance_details":       attendance_details,
            "questionnaire_responses":  questionnaire_responses,
        })

    except Exception as e:
        return returnException(str(e))
