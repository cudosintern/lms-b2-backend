from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

# ReportLab Imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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

        # ── Mentoring (Curriculum & Counsellor Name) ─────────────────
        curriculum = ""
        counsellor_name = ""
        try:
            mentoring_sql = """
                SELECT 
                    ab.academic_batch_code AS curriculum_name,
                    COALESCE(NULLIF(TRIM(CONCAT_WS(' ', u.first_name, u.last_name)), ''), u.username) AS counsellor_name
                FROM lms_group_mentees gme
                JOIN lms_group_mentors gm ON gme.group_mentor_id = gm.group_mentor_id
                LEFT JOIN iems_users u ON gm.mentor_id = u.id
                JOIN lms_mentors_group_terms mgt ON gme.mentors_group_terms_id = mgt.mentors_group_terms_id
                JOIN lms_mentors_group mg ON mgt.mentors_group_id = mg.mentors_group_id
                LEFT JOIN iems_academic_batch ab ON mg.academic_batch_id = ab.academic_batch_id
                WHERE gme.student_id = :sid
                LIMIT 1
            """
            mentoring_row = db.execute(text(mentoring_sql), {"sid": student_id}).mappings().first()
            if mentoring_row:
                curriculum = mentoring_row["curriculum_name"] or ""
                counsellor_name = mentoring_row["counsellor_name"] or ""
        except Exception:
            pass

        # ── Personal Info ────────────────────────────────────────────
        personal_info = {
            "full_name":      student.name or "",
            "usn":            student.usno or "",
            "application_no": student.application_no or "",
            "regno":          student.regno or "",
            "department":     department.dept_name if department else "",
            "program":        program.pgm_title if program else "",
            "curriculum":     curriculum,
            "counsellor_name": counsellor_name,
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
        # Pull directly from iems_students table columns using raw SQL since they are not mapped in SQLAlchemy model
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
            addr_sql = "SELECT permanent_address, present_address, city FROM iems_students WHERE student_id = :sid"
            addr_row = db.execute(text(addr_sql), {"sid": student_id}).mappings().first()
            if addr_row:
                addresses["permanent"]["address"] = addr_row["permanent_address"] or ""
                addresses["permanent"]["city"] = addr_row["city"] or ""
                addresses["correspondence"]["address"] = addr_row["present_address"] or ""
                addresses["correspondence"]["city"] = addr_row["city"] or ""
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
            if student and student.usno:
                att_sql = """
                    SELECT 
                        ma.semester_id AS semester,
                        c.crs_code AS course_code,
                        c.crs_title AS course_title,
                        ROUND(
                            SUM(CASE WHEN sa.attendance_status = 'Present' THEN ma.attendance_class_count ELSE 0 END) * 100.0 / 
                            NULLIF(SUM(ma.attendance_class_count), 0), 
                            2
                        ) AS attendance_percentage
                    FROM lms_map_student_attendance sa
                    JOIN lms_manage_attendance ma ON sa.attendance_id = ma.attendance_id
                    LEFT JOIN iems_courses c ON ma.crs_id = c.crs_id
                    WHERE sa.student_usn = :usn AND ma.status = 1
                    GROUP BY ma.semester_id, c.crs_code, c.crs_title
                """
                att_rows = db.execute(text(att_sql), {"usn": student.usno.strip()}).mappings().all()
                for r in att_rows:
                    attendance_details.append({
                        "course_code": r["course_code"] or "",
                        "course_title": r["course_title"] or "",
                        "attendance_percentage": float(r["attendance_percentage"]) if r["attendance_percentage"] is not None else None
                    })
                    marks_details.append({
                        "semester": r["semester"] or 1,
                        "course_code": r["course_code"] or "",
                        "course_title": r["course_title"] or "",
                        "occasions": []
                    })
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


@router.get("/export/pdf")
def export_student_pdf(
    usn: str,
    db: Session = Depends(get_db)
):
    if not usn or usn.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="USN is required"
        )
    
    usn = usn.strip()
    
    # ── Fetch Student Details ──
    student = db.query(IEMStudents).filter(
        IEMStudents.usno == usn
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student_id = student.student_id

    # ── Department ──────────────────────────────────────────────
    department = None
    if student.department_id:
        department = db.query(IEMSDepartment).filter(
            IEMSDepartment.dept_id == student.department_id
        ).first()
    
    if not department and student.academic_batch_id:
        try:
            dept_sql = """
                SELECT d.dept_name
                FROM iems_academic_batch ab
                JOIN iems_department d ON ab.dept_id = d.dept_id
                WHERE ab.academic_batch_id = :abid
                LIMIT 1
            """
            dept_row = db.execute(text(dept_sql), {"abid": student.academic_batch_id}).mappings().first()
            if dept_row:
                class MockDept:
                    def __init__(self, name):
                        self.dept_name = name
                department = MockDept(dept_row["dept_name"])
        except Exception:
            pass

    # ── Program ─────────────────────────────────────────────────
    program = None
    if student.program_id:
        program = db.query(IEMProgram).filter(
            IEMProgram.pgm_id == student.program_id
        ).first()

    # ── Mentoring (Curriculum & Counsellor Name) ─────────────────
    curriculum = ""
    counsellor_name = ""
    try:
        mentoring_sql = """
            SELECT 
                ab.academic_batch_code AS curriculum_name,
                COALESCE(NULLIF(TRIM(CONCAT_WS(' ', u.first_name, u.last_name)), ''), u.username) AS counsellor_name
            FROM lms_group_mentees gme
            JOIN lms_group_mentors gm ON gme.group_mentor_id = gm.group_mentor_id
            LEFT JOIN iems_users u ON gm.mentor_id = u.id
            JOIN lms_mentors_group_terms mgt ON gme.mentors_group_terms_id = mgt.mentors_group_terms_id
            JOIN lms_mentors_group mg ON mgt.mentors_group_id = mg.mentors_group_id
            LEFT JOIN iems_academic_batch ab ON mg.academic_batch_id = ab.academic_batch_id
            WHERE gme.student_id = :sid
            LIMIT 1
        """
        mentoring_row = db.execute(text(mentoring_sql), {"sid": student_id}).mappings().first()
        if mentoring_row:
            curriculum = mentoring_row["curriculum_name"] or ""
            counsellor_name = mentoring_row["counsellor_name"] or ""
    except Exception:
        pass

    # ── Personal Info ────────────────────────────────────────────
    personal_info = {
        "full_name":      student.name or "",
        "usn":            student.usno or "",
        "application_no": student.application_no or "",
        "regno":          student.regno or "",
        "department":     department.dept_name if department else "",
        "program":        program.pgm_title if program else "",
        "curriculum":     curriculum,
        "counsellor_name": counsellor_name,
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
        addr_sql = "SELECT permanent_address, present_address, city FROM iems_students WHERE student_id = :sid"
        addr_row = db.execute(text(addr_sql), {"sid": student_id}).mappings().first()
        if addr_row:
            addresses["permanent"]["address"] = addr_row["permanent_address"] or ""
            addresses["permanent"]["city"] = addr_row["city"] or ""
            addresses["correspondence"]["address"] = addr_row["present_address"] or ""
            addresses["correspondence"]["city"] = addr_row["city"] or ""
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

    # ── Marks & Attendance ───────────────────────────────────────
    marks_details = []
    attendance_details = []
    try:
        att_sql = """
            SELECT 
                ma.semester_id AS semester,
                c.crs_code AS course_code,
                c.crs_title AS course_title,
                ROUND(
                    SUM(CASE WHEN sa.attendance_status = 'Present' THEN ma.attendance_class_count ELSE 0 END) * 100.0 / 
                    NULLIF(SUM(ma.attendance_class_count), 0), 
                    2
                ) AS attendance_percentage
            FROM lms_map_student_attendance sa
            JOIN lms_manage_attendance ma ON sa.attendance_id = ma.attendance_id
            LEFT JOIN iems_courses c ON ma.crs_id = c.crs_id
            WHERE sa.student_usn = :usn AND ma.status = 1
            GROUP BY ma.semester_id, c.crs_code, c.crs_title
        """
        att_rows = db.execute(text(att_sql), {"usn": usn}).mappings().all()
        for r in att_rows:
            attendance_details.append({
                "course_code": r["course_code"] or "",
                "course_title": r["course_title"] or "",
                "attendance_percentage": float(r["attendance_percentage"]) if r["attendance_percentage"] is not None else None
            })
            marks_details.append({
                "semester": r["semester"] or 1,
                "course_code": r["course_code"] or "",
                "course_title": r["course_title"] or "",
                "occasions": []
            })
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
                })
    except Exception:
        pass

    data = {
        "personal_info":            personal_info,
        "addresses":                addresses,
        "education_details":        education_details,
        "marks_details":            marks_details,
        "attendance_details":       attendance_details,
        "questionnaire_responses":  questionnaire_responses,
    }

    # PDF generation path
    file_path = f"app/uploads/student_details_{usn}.pdf"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Setup document
    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#0F4C81'),
        alignment=1, # Center
        spaceAfter=15
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor('#1D3557'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    normal_text = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#2B2D42')
    )
    
    header_text = ParagraphStyle(
        'HeaderStyle',
        parent=normal_text,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    story = []
    
    # Document Header
    story.append(Paragraph("Student Profile & Academic Record", title_style))
    story.append(Spacer(1, 10))
    
    # Section: Personal Information
    story.append(Paragraph("Personal Information", section_heading))
    pi = data["personal_info"]
    pi_data = [
        [
            Paragraph("<b>USN:</b>", normal_text), Paragraph(str(usn), normal_text),
            Paragraph("<b>Full Name:</b>", normal_text), Paragraph(pi.get("full_name", ""), normal_text)
        ],
        [
            Paragraph("<b>Email:</b>", normal_text), Paragraph(pi.get("email") or "N/A", normal_text),
            Paragraph("<b>Contact:</b>", normal_text), Paragraph(pi.get("contact") or "N/A", normal_text)
        ],
        [
            Paragraph("<b>DOB:</b>", normal_text), Paragraph(pi.get("dob") or "N/A", normal_text),
            Paragraph("<b>Gender:</b>", normal_text), Paragraph(pi.get("gender") or "N/A", normal_text)
        ],
        [
            Paragraph("<b>Department:</b>", normal_text), Paragraph(pi.get("department") or "N/A", normal_text),
            Paragraph("<b>Program:</b>", normal_text), Paragraph(pi.get("program", ""), normal_text)
        ],
        [
            Paragraph("<b>Curriculum:</b>", normal_text), Paragraph(pi.get("curriculum", "N/A"), normal_text),
            Paragraph("", normal_text), Paragraph("", normal_text)
        ]
    ]
    t_pi = Table(pi_data, colWidths=[90, 180, 90, 180])
    t_pi.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F1FAEE')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#F1FAEE')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_pi)
    story.append(Spacer(1, 12))
    
    # Section: Addresses
    story.append(Paragraph("Address Details", section_heading))
    perm = data["addresses"]["permanent"]
    corr = data["addresses"]["correspondence"]
    
    perm_str = f"{perm['address']}<br/>{perm['city']}"
    corr_str = f"{corr['address']}<br/>{corr['city']}"
    
    addr_data = [
        [Paragraph("<b>Permanent Address</b>", header_text), Paragraph("<b>Correspondence Address</b>", header_text)],
        [Paragraph(perm_str, normal_text), Paragraph(corr_str, normal_text)]
    ]
    t_addr = Table(addr_data, colWidths=[270, 270])
    t_addr.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#457B9D')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_addr)
    story.append(Spacer(1, 12))
    
    # Section: Academic Performance percentages (10th & 12th)
    story.append(Paragraph("Education Qualifications", section_heading))
    edu = data["education_details"]
    edu_data = [
        [Paragraph("<b>Qualification</b>", header_text), Paragraph("<b>Board/University</b>", header_text), Paragraph("<b>Year of Passing</b>", header_text), Paragraph("<b>Percentage</b>", header_text)],
        [Paragraph("10th Standard / SSLC", normal_text), Paragraph(edu["tenth_board"] or "N/A", normal_text), Paragraph(str(edu["tenth_year"]) or "N/A", normal_text), Paragraph(f"{edu['tenth_percentage']}%" if edu['tenth_percentage'] else "N/A", normal_text)],
        [Paragraph("12th Standard / PUC", normal_text), Paragraph(edu["twelfth_board"] or "N/A", normal_text), Paragraph(str(edu["twelfth_year"]) or "N/A", normal_text), Paragraph(f"{edu['twelfth_percentage']}%" if edu['twelfth_percentage'] else "N/A", normal_text)]
    ]
    t_edu = Table(edu_data, colWidths=[150, 180, 100, 110])
    t_edu.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#457B9D')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (3,0), (3,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_edu)
    story.append(Spacer(1, 12))

    # Section: Questionnaire Responses
    story.append(Paragraph("Questionnaire Responses", section_heading))
    q_data = [
        [Paragraph("<b>Question</b>", header_text), Paragraph("<b>Response Value</b>", header_text), Paragraph("<b>Submitted At</b>", header_text)]
    ]
    for q in data["questionnaire_responses"]:
        q_data.append([
            Paragraph(q["question_text"], normal_text),
            Paragraph(q["response_value"], normal_text),
            Paragraph(q["submitted_at"], normal_text)
        ])
    t_q = Table(q_data, colWidths=[200, 240, 100])
    t_q.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#457B9D')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_q)
    story.append(Spacer(1, 12))
    
    # Section: Course-wise Attendance
    story.append(Paragraph("Course-wise Attendance Record", section_heading))
    att_data = [
        [Paragraph("<b>Course Code</b>", header_text), Paragraph("<b>Course Title</b>", header_text), Paragraph("<b>Attendance %</b>", header_text)]
    ]
    for att in data["attendance_details"]:
        att_data.append([
            Paragraph(att["course_code"], normal_text),
            Paragraph(att["course_title"], normal_text),
            Paragraph(f"{att['attendance_percentage']}%", normal_text)
        ])
    t_att = Table(att_data, colWidths=[100, 320, 120])
    t_att.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#457B9D')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (2,0), (2,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_att)
    story.append(Spacer(1, 12))
    
    # Section: Marks secured for all occasions & all semesters
    story.append(Paragraph("Semester-wise Academic Marks", section_heading))
    marks_rows_list = [
        [Paragraph("<b>Sem</b>", header_text), Paragraph("<b>Course Code</b>", header_text), Paragraph("<b>Course Title</b>", header_text), Paragraph("<b>Occasion Breakdown (Marks Secured / Max)</b>", header_text)]
    ]
    for course in data["marks_details"]:
        breakdown_parts = []
        for occ in course["occasions"]:
            breakdown_parts.append(f"{occ['occasion_name']}: <b>{occ['secured_marks']}</b>/{occ['total_marks']}")
        breakdown_str = " | ".join(breakdown_parts) if breakdown_parts else "No marks recorded"
        
        marks_rows_list.append([
            Paragraph(str(course["semester"]), normal_text),
            Paragraph(course["course_code"], normal_text),
            Paragraph(course["course_title"], normal_text),
            Paragraph(breakdown_str, normal_text)
        ])
    t_marks = Table(marks_rows_list, colWidths=[40, 80, 160, 260])
    t_marks.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#457B9D')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_marks)

    # Build PDF doc
    doc.build(story)
    
    return FileResponse(path=file_path, filename=f"student_profile_{usn}.pdf", media_type='application/pdf')
