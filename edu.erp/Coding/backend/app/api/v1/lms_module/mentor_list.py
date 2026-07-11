from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import (
    ErpCurriculum, Student, IEMStudents, IEMSUsers, IEMSAcademicBatch,
    LMSCrossDeptMentor, LMSGroupMentors, LMSMentorsGroup, LMSMentorsGroupTerms,
    LMSGroupMentees, ErpDepartment, IEMProgram, IEMSemester
)
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnException, returnSuccess

router = APIRouter(tags=["LMS-Mentor List"])


@router.get("/mentor-list/departments")
def get_mentor_list_departments(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    depts = db.query(ErpDepartment).filter(ErpDepartment.status == 1).order_by(ErpDepartment.erp_dept_name).all()
    return returnSuccess([
        {
            "dept_id": d.erp_dept_id,
            "dept_name": d.erp_dept_name
        }
        for d in depts
    ])


@router.get("/mentor-list/programs")
def get_mentor_list_programs(
    dept_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    programs = db.query(IEMProgram).filter(
        IEMProgram.dept_id == dept_id,
        IEMProgram.status == 1
    ).order_by(IEMProgram.pgm_title).all()
    return returnSuccess([
        {
            "pgm_id": p.pgm_id,
            "pgm_title": p.pgm_title,
            "pgm_acronym": p.pgm_acronym
        }
        for p in programs
    ])


@router.get("/mentor-list/curriculums")
def get_mentor_list_curriculums(
    dept_id: int,
    pgm_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("user_id")
    assigned_crclm_ids = []

    # 1. From Cross-Department Mentor
    assignments = db.query(LMSCrossDeptMentor.curriculum_id).filter(
        LMSCrossDeptMentor.mentor_user_id == user_id,
        LMSCrossDeptMentor.status == 1,
        LMSCrossDeptMentor.curriculum_id.isnot(None)
    ).distinct().all()
    assigned_crclm_ids.extend([a[0] for a in assignments])

    # 2. From LMSGroupMentors
    group_mentor_records = db.query(LMSGroupMentors).filter(
        LMSGroupMentors.mentor_id == user_id
    ).all()
    if group_mentor_records:
        terms_ids = [g.mentors_group_terms_id for g in group_mentor_records]
        terms = db.query(LMSMentorsGroupTerms).filter(
            LMSMentorsGroupTerms.mentors_group_terms_id.in_(terms_ids)
        ).all()
        batch_ids = [t.academic_batch_id for t in terms]
        if batch_ids:
            batches = db.query(IEMSAcademicBatch).filter(
                IEMSAcademicBatch.academic_batch_id.in_(batch_ids)
            ).all()
            for b in batches:
                matching_crclms = db.query(ErpCurriculum).filter(
                    ErpCurriculum.erp_pgm_id == b.pgm_id,
                    ErpCurriculum.erp_dept_id == b.dept_id,
                    ErpCurriculum.status == 1
                ).all()
                assigned_crclm_ids.extend([c.erp_crclm_id for c in matching_crclms])

    assigned_crclm_ids = list(set(assigned_crclm_ids))

    is_admin = current_user.get("super_admin", False) or current_user.get("technical_admin", False)
    query = db.query(ErpCurriculum).filter(
        ErpCurriculum.erp_dept_id == dept_id,
        ErpCurriculum.erp_pgm_id == pgm_id,
        ErpCurriculum.status == 1
    )
    
    if not is_admin and assigned_crclm_ids:
        query = query.filter(ErpCurriculum.erp_crclm_id.in_(assigned_crclm_ids))

    curriculums = query.order_by(ErpCurriculum.erp_crclm_name).all()

    return returnSuccess([
        {
            "crclm_id": c.erp_crclm_id,
            "crclm_name": c.erp_crclm_name,
            "start_year": c.erp_crclm_start_year,
            "end_year": c.erp_crclm_end_year
        }
        for c in curriculums
    ])


@router.get("/mentor-list/semesters")
def get_mentor_list_semesters(
    dept_id: int,
    pgm_id: int,
    curriculum_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batches_query = db.query(IEMSAcademicBatch).filter(
        IEMSAcademicBatch.dept_id == dept_id,
        IEMSAcademicBatch.pgm_id == pgm_id,
        IEMSAcademicBatch.status == 1
    )
    if curriculum_id:
        crclm = db.query(ErpCurriculum).filter(ErpCurriculum.erp_crclm_id == curriculum_id).first()
        if crclm:
            matching_batches = db.query(IEMSAcademicBatch).filter(
                IEMSAcademicBatch.dept_id == dept_id,
                IEMSAcademicBatch.pgm_id == pgm_id,
                IEMSAcademicBatch.start_year == crclm.erp_crclm_start_year,
                IEMSAcademicBatch.end_year == crclm.erp_crclm_end_year,
                IEMSAcademicBatch.status == 1
            ).all()
            if matching_batches:
                batch_ids = [b.academic_batch_id for b in matching_batches]
            else:
                batch_ids = [b.academic_batch_id for b in batches_query.all()]
        else:
            batch_ids = [b.academic_batch_id for b in batches_query.all()]
    else:
        batch_ids = [b.academic_batch_id for b in batches_query.all()]

    if not batch_ids:
        return returnSuccess([])

    semesters = db.query(IEMSemester).filter(
        IEMSemester.academic_batch_id.in_(batch_ids),
        IEMSemester.status == 1
    ).order_by(IEMSemester.semester).all()

    seen = set()
    data = []
    for s in semesters:
        if s.semester not in seen:
            seen.add(s.semester)
            data.append({
                "semester_id": s.semester_id,
                "semester": s.semester,
                "semester_desc": s.semester_desc
            })
    return returnSuccess(data)


@router.get("/mentor-list/students")
def get_mentor_list_students(
    dept_id: int,
    pgm_id: int,
    curriculum_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(IEMStudents).filter(
        IEMStudents.department_id == dept_id,
        IEMStudents.status == 1
    )
    if curriculum_id is not None:
        crclm = db.query(ErpCurriculum).filter(ErpCurriculum.erp_crclm_id == curriculum_id).first()
        if crclm:
            batches = db.query(IEMSAcademicBatch).filter(
                IEMSAcademicBatch.dept_id == dept_id,
                IEMSAcademicBatch.pgm_id == pgm_id,
                IEMSAcademicBatch.start_year == crclm.erp_crclm_start_year,
                IEMSAcademicBatch.end_year == crclm.erp_crclm_end_year,
                IEMSAcademicBatch.status == 1
            ).all()
            batch_ids = [b.academic_batch_id for b in batches]
            if batch_ids:
                query = query.filter(IEMStudents.academic_batch_id.in_(batch_ids))
        
    students = query.order_by(IEMStudents.name).all()
    return returnSuccess([
        {
            "student_id": s.student_id,
            "student_name": s.name,
            "student_usn": s.usno or s.regno or "",
            "student_email": s.email
        }
        for s in students
    ])


@router.get("/mentor-list/mentors-mentees")
def get_mentor_list_mentors_mentees(
    dept_id: int,
    pgm_id: int,
    curriculum_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batches_query = db.query(IEMSAcademicBatch).filter(
        IEMSAcademicBatch.dept_id == dept_id,
        IEMSAcademicBatch.pgm_id == pgm_id,
        IEMSAcademicBatch.status == 1
    )
    if curriculum_id:
        crclm = db.query(ErpCurriculum).filter(ErpCurriculum.erp_crclm_id == curriculum_id).first()
        if crclm:
            matching_batches = db.query(IEMSAcademicBatch).filter(
                IEMSAcademicBatch.dept_id == dept_id,
                IEMSAcademicBatch.pgm_id == pgm_id,
                IEMSAcademicBatch.start_year == crclm.erp_crclm_start_year,
                IEMSAcademicBatch.end_year == crclm.erp_crclm_end_year,
                IEMSAcademicBatch.status == 1
            ).all()
            if matching_batches:
                batches = matching_batches
            else:
                batches = batches_query.all()
        else:
            batches = batches_query.all()
    else:
        batches = batches_query.all()

    batch_ids = [b.academic_batch_id for b in batches]

    if not batch_ids:
        return returnSuccess([])

    groups = db.query(LMSMentorsGroup).filter(
        LMSMentorsGroup.academic_batch_id.in_(batch_ids)
    ).all()
    group_ids = [g.mentors_group_id for g in groups]

    if not group_ids:
        return returnSuccess([])

    terms_query = db.query(LMSMentorsGroupTerms).filter(
        LMSMentorsGroupTerms.mentors_group_id.in_(group_ids)
    )
    if semester_id is not None:
        terms_query = terms_query.filter(LMSMentorsGroupTerms.semester_id == semester_id)
    terms = terms_query.all()
    terms_ids = [t.mentors_group_terms_id for t in terms]

    if not terms_ids:
        return returnSuccess([])

    group_mentors = db.query(LMSGroupMentors).filter(
        LMSGroupMentors.mentors_group_terms_id.in_(terms_ids)
    ).all()

    response_data = []
    for gm in group_mentors:
        mentor_user = db.query(IEMSUsers).filter(IEMSUsers.id == gm.mentor_id).first()
        if not mentor_user:
            continue
        
        mentor_name = f"{mentor_user.first_name or ''} {mentor_user.last_name or ''}".strip() or mentor_user.username
        mentor_email = mentor_user.email

        terms_rec = db.query(LMSMentorsGroupTerms).filter(
            LMSMentorsGroupTerms.mentors_group_terms_id == gm.mentors_group_terms_id
        ).first()
        group_rec = db.query(LMSMentorsGroup).filter(
            LMSMentorsGroup.mentors_group_id == terms_rec.mentors_group_id
        ).first() if terms_rec else None
        
        dept_rec = db.query(ErpDepartment).filter(ErpDepartment.erp_dept_id == dept_id).first()
        dept_name = dept_rec.erp_dept_name if dept_rec else "N/A"

        group_mentees = db.query(LMSGroupMentees).filter(
            LMSGroupMentees.group_mentor_id == gm.group_mentor_id,
            LMSGroupMentees.mentors_group_terms_id == gm.mentors_group_terms_id
        ).all()

        mentees_list = []
        for g_mentee in group_mentees:
            student = db.query(IEMStudents).filter(IEMStudents.student_id == g_mentee.student_id).first()
            student_erp = db.query(Student).filter(Student.erp_student_id == g_mentee.student_id).first() if not student else None
            student_user = db.query(IEMSUsers).filter(IEMSUsers.id == g_mentee.student_id).first() if not student and not student_erp else None

            s_name = ""
            s_usn = ""
            s_email = ""

            if student:
                s_name = student.name
                s_usn = student.usno or student.regno or ""
                s_email = student.email or ""
            elif student_erp:
                s_name = student_erp.full_name or f"{student_erp.first_name or ''} {student_erp.last_name or ''}".strip()
                s_usn = student_erp.erp_student_usn or ""
                s_email = student_erp.email_id or ""
            elif student_user:
                s_name = f"{student_user.first_name or ''} {student_user.last_name or ''}".strip() or student_user.username
                s_usn = ""
                s_email = student_user.email or ""

            mentees_list.append({
                "student_id": g_mentee.student_id,
                "student_name": s_name,
                "student_usn": s_usn,
                "student_email": s_email
            })

        response_data.append({
            "group_mentor_id": gm.group_mentor_id,
            "mentor_id": gm.mentor_id,
            "mentor_name": mentor_name,
            "mentor_email": mentor_email,
            "mentor_dept": dept_name,
            "group_title": group_rec.mentors_pgm_title if group_rec else "Mentoring Group",
            "mentees": mentees_list
        })

    return returnSuccess(response_data)


from fpdf import FPDF
from io import BytesIO
from fastapi.responses import StreamingResponse

class MentorListPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Mentor - Mentee Allocation Report", ln=True, align="C")
        self.set_font("Arial", "", 10)
        self.cell(0, 5, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


@router.get("/mentor-list/export-pdf")
def export_mentor_list_pdf(
    dept_id: int,
    pgm_id: int,
    curriculum_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    batches_query = db.query(IEMSAcademicBatch).filter(
        IEMSAcademicBatch.dept_id == dept_id,
        IEMSAcademicBatch.pgm_id == pgm_id,
        IEMSAcademicBatch.status == 1
    )
    if curriculum_id:
        crclm = db.query(ErpCurriculum).filter(ErpCurriculum.erp_crclm_id == curriculum_id).first()
        if crclm:
            matching_batches = db.query(IEMSAcademicBatch).filter(
                IEMSAcademicBatch.dept_id == dept_id,
                IEMSAcademicBatch.pgm_id == pgm_id,
                IEMSAcademicBatch.start_year == crclm.erp_crclm_start_year,
                IEMSAcademicBatch.end_year == crclm.erp_crclm_end_year,
                IEMSAcademicBatch.status == 1
            ).all()
            if matching_batches:
                batches = matching_batches
            else:
                batches = batches_query.all()
        else:
            batches = batches_query.all()
    else:
        batches = batches_query.all()

    batch_ids = [b.academic_batch_id for b in batches]

    mentor_data = []
    if batch_ids:
        groups = db.query(LMSMentorsGroup).filter(
            LMSMentorsGroup.academic_batch_id.in_(batch_ids)
        ).all()
        group_ids = [g.mentors_group_id for g in groups]

        if group_ids:
            terms_query = db.query(LMSMentorsGroupTerms).filter(
                LMSMentorsGroupTerms.mentors_group_id.in_(group_ids)
            )
            if semester_id is not None:
                terms_query = terms_query.filter(LMSMentorsGroupTerms.semester_id == semester_id)
            terms = terms_query.all()
            terms_ids = [t.mentors_group_terms_id for t in terms]

            if terms_ids:
                group_mentors = db.query(LMSGroupMentors).filter(
                    LMSGroupMentors.mentors_group_terms_id.in_(terms_ids)
                ).all()

                for gm in group_mentors:
                    mentor_user = db.query(IEMSUsers).filter(IEMSUsers.id == gm.mentor_id).first()
                    if not mentor_user:
                        continue
                    
                    mentor_name = f"{mentor_user.first_name or ''} {mentor_user.last_name or ''}".strip() or mentor_user.username
                    mentor_email = mentor_user.email

                    terms_rec = db.query(LMSMentorsGroupTerms).filter(
                        LMSMentorsGroupTerms.mentors_group_terms_id == gm.mentors_group_terms_id
                    ).first()
                    group_rec = db.query(LMSMentorsGroup).filter(
                        LMSMentorsGroup.mentors_group_id == terms_rec.mentors_group_id
                    ).first() if terms_rec else None

                    dept_rec = db.query(ErpDepartment).filter(ErpDepartment.erp_dept_id == dept_id).first()
                    dept_name = dept_rec.erp_dept_name if dept_rec else "N/A"

                    group_mentees = db.query(LMSGroupMentees).filter(
                        LMSGroupMentees.group_mentor_id == gm.group_mentor_id,
                        LMSGroupMentees.mentors_group_terms_id == gm.mentors_group_terms_id
                    ).all()

                    mentees_list = []
                    for g_mentee in group_mentees:
                        student = db.query(IEMStudents).filter(IEMStudents.student_id == g_mentee.student_id).first()
                        student_erp = db.query(Student).filter(Student.erp_student_id == g_mentee.student_id).first() if not student else None
                        student_user = db.query(IEMSUsers).filter(IEMSUsers.id == g_mentee.student_id).first() if not student and not student_erp else None

                        s_name = ""
                        s_usn = ""
                        s_email = ""

                        if student:
                            s_name = student.name
                            s_usn = student.usno or student.regno or ""
                            s_email = student.email or ""
                        elif student_erp:
                            s_name = student_erp.full_name or f"{student_erp.first_name or ''} {student_erp.last_name or ''}".strip()
                            s_usn = student_erp.erp_student_usn or ""
                            s_email = student_erp.email_id or ""
                        elif student_user:
                            s_name = f"{student_user.first_name or ''} {student_user.last_name or ''}".strip() or student_user.username
                            s_usn = ""
                            s_email = student_user.email or ""

                        mentees_list.append({
                            "student_name": s_name,
                            "student_usn": s_usn,
                            "student_email": s_email
                        })

                    mentor_data.append({
                        "mentor_name": mentor_name,
                        "mentor_email": mentor_email,
                        "mentor_dept": dept_name,
                        "group_title": group_rec.mentors_pgm_title if group_rec else "Mentoring Group",
                        "mentees": mentees_list
                    })

    pdf = MentorListPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 10)
    dept_rec = db.query(ErpDepartment).filter(ErpDepartment.erp_dept_id == dept_id).first()
    pgm_rec = db.query(IEMProgram).filter(IEMProgram.pgm_id == pgm_id).first()
    
    pdf.cell(40, 7, "Department:", ln=False)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, dept_rec.erp_dept_name if dept_rec else str(dept_id), ln=True)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 7, "Program:", ln=False)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, pgm_rec.pgm_title if pgm_rec else str(pgm_id), ln=True)
    
    if curriculum_id:
        crclm_rec = db.query(ErpCurriculum).filter(ErpCurriculum.erp_crclm_id == curriculum_id).first()
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 7, "Curriculum:", ln=False)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 7, crclm_rec.erp_crclm_name if crclm_rec else str(curriculum_id), ln=True)
        
    pdf.ln(5)

    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(8, 7, "SL", border=1, fill=True, align="C")
    pdf.cell(42, 7, "Mentor Details", border=1, fill=True, align="L")
    pdf.cell(40, 7, "Group Title", border=1, fill=True, align="L")
    pdf.cell(45, 7, "Mentee Name", border=1, fill=True, align="L")
    pdf.cell(25, 7, "Mentee USN", border=1, fill=True, align="C")
    pdf.cell(30, 7, "Mentee Email", border=1, fill=True, align="L")
    pdf.ln()

    pdf.set_font("Arial", "", 8)
    sl_no = 1
    
    if not mentor_data:
        pdf.cell(190, 10, "No Mentor-Mentee allocation data found for selected filters.", border=1, align="C")
    else:
        for m in mentor_data:
            group_t = m['group_title']
            if not m['mentees']:
                pdf.cell(8, 10, str(sl_no), border=1, align="C")
                pdf.cell(42, 10, m['mentor_name'], border=1, align="L")
                pdf.cell(40, 10, group_t, border=1, align="L")
                pdf.cell(100, 10, "No Mentees Assigned", border=1, align="C")
                pdf.ln()
                sl_no += 1
            else:
                for idx, mentee in enumerate(m['mentees']):
                    pdf.cell(8, 8, str(sl_no) if idx == 0 else "", border="LRT" if idx == 0 else "LR")
                    pdf.cell(42, 8, m['mentor_name'] if idx == 0 else "", border="LRT" if idx == 0 else "LR")
                    pdf.cell(40, 8, group_t if idx == 0 else "", border="LRT" if idx == 0 else "LR")
                    
                    pdf.cell(45, 8, mentee['student_name'], border=1, align="L")
                    pdf.cell(25, 8, mentee['student_usn'], border=1, align="C")
                    pdf.cell(30, 8, mentee['student_email'], border=1, align="L")
                    pdf.ln()
                sl_no += 1

    stream = BytesIO()
    pdf_content = pdf.output(dest='S')
    if isinstance(pdf_content, str):
        pdf_content = pdf_content.encode('latin1')
    stream.write(pdf_content)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Mentor_Mentee_Report.pdf"}
    )
