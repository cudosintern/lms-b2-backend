# from fastapi import APIRouter, Depends, Query, HTTPException
# from fastapi.responses import FileResponse
# from sqlalchemy.orm import Session
# from sqlalchemy import text
# from typing import List, Optional
# from datetime import date
# import logging
# import tempfile
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas
# from reportlab.lib import colors
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.enums import TA_CENTER, TA_LEFT
# from app.core.database import get_db
# from .topic_coverage_schema import (
#     CurriculumResponse, TermResponse, CourseResponse, TopicResponse,
#     TopicStatusResponse, TopicDatesResponse, CourseTopicStatusItem, CourseTopicsStatusResponse,
#     TopicScheduleCreate, TopicScheduleUpdate
# )

# router = APIRouter(tags=["Topic Coverage and Tracking"])

# logger = logging.getLogger(__name__)

# # [Previous endpoints unchanged - copy from original file lines 44-446]

# # 1. GET /curriculum -> returns list of curriculum (id, name)
# @router.get("/curriculum", response_model=List[CurriculumResponse])
# def get_curriculum(db: Session = Depends(get_db)):
#     """Fetch list of curriculum from iems_academic_batch."""
#     try:
#         query = text("""
#             SELECT academic_batch_id as id, academic_batch_desc as name 
#             FROM iems_academic_batch 
#             WHERE status = 1
#         """)
#         result = db.execute(query).fetchall()
#         return [{"id": r.id, "name": r.name} for r in result]
#     except Exception as e:
#         logger.error(f"Error fetching curriculum: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# # [Copy all other endpoints exactly as they are until the PDF endpoint...]

# @router.get("/export-pdf")
# def export_topic_coverage_pdf(
#     academic_batch_id: int,
#     semester_id: int,
#     section_id: Optional[int] = None,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # 1. Fetch Metadata
#         batch_query = text("SELECT academic_batch_desc FROM iems_academic_batch WHERE academic_batch_id = :id")
#         batch_name = db.execute(batch_query, {"id": academic_batch_id}).scalar() or "N/A"

#         sem_query = text("SELECT semester_desc FROM iems_semester WHERE semester_id = :id")
#         sem_name = db.execute(sem_query, {"id": semester_id}).scalar() or "N/A"

#         # 2. Base Assignments Query
#         base_query = """
#         SELECT DISTINCT
#             s.id as section_id,
#             s.section,
#             c.crs_id,
#             c.crs_code,
#             c.crs_title,
#             u.first_name,
#             u.last_name
#         FROM cudos_map_courseto_course_instructor m       
#         JOIN iems_section s ON m.section_id = s.id        
#         JOIN iems_courses c ON m.crs_id = c.crs_id
#         LEFT JOIN iems_users u ON m.course_instructor_id = u.id  
#         WHERE m.academic_batch_id = :batch_id
#         AND m.semester_id = :sem_id
#         """

#         params = {
#             "batch_id": academic_batch_id,
#             "sem_id": semester_id
#         }

#         if section_id is not None:
#             base_query += " AND m.section_id = :sec_id"
#             params["sec_id"] = section_id

#         assignments_query = text(base_query)
#         all_assignments = db.execute(assignments_query, params).fetchall()

#         # 3. Group Data
#         grouped_data = {}
#         for row in all_assignments:
#             key = row.section
#             if key not in grouped_data:
#                 grouped_data[key] = []

#             # Fetch topics status (simplified)
#             topics_query = text("SELECT topic_id FROM cudos_topic WHERE course_id = :cid")
#             topics = db.execute(topics_query, {"cid": row.crs_id}).fetchall()

#             course_status = "LS not added"
#             status_color = colors.blue

#             if topics:
#                 tids = tuple([t.topic_id for t in topics])
#                 if tids:
#                     # Check if any topic has attendance
#                     att_query = text("""
#                         SELECT 1 FROM lms_ls_student_map stm
#                         JOIN lms_lesson_schedule ls ON stm.lls_id = ls.lls_id
#                         WHERE ls.topic_id IN :tids LIMIT 1
#                     """)
#                     if db.execute(att_query, {"tids": tids}).fetchone():
#                         course_status = "Completed"
#                         status_color = colors.green
#                     else:
#                         # Check planned
#                         planned_query = text("SELECT 1 FROM topic_lesson_schedule WHERE topic_id IN :tids LIMIT 1")
#                         if db.execute(planned_query, {"tids": tids}).fetchone():
#                             course_status = "In-progress"
#                             status_color = colors.orange
#                         else:
#                             course_status = "Not started"
#                             status_color = colors.red

#             faculty_name = f"Prof. {row.first_name or ''} {row.last_name or ''}".strip() or "N/A"

#             grouped_data[key].append({
#                 "code_title": f"{row.crs_code} - {row.crs_title}",
#                 "faculty": faculty_name,
#                 "status": course_status,
#                 "color": status_color
#             })

#         # 4. Build PDF
#         temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=".")
#         doc = SimpleDocTemplate(temp_file.name, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
#         elements = []

#         styles = getSampleStyleSheet()

#         title_style = ParagraphStyle(
#             'TitleStyle',
#             parent=styles['Title'],
#             fontName='Times-Bold',
#             fontSize=14,
#             textColor=colors.red,
#             alignment=TA_LEFT
#         )

#         header_style = ParagraphStyle(
#             'HeaderStyle',
#             fontName='Times-Roman',
#             fontSize=10,
#             alignment=TA_CENTER
#         )

#         normal_style = ParagraphStyle(
#             'NormalStyle',
#             fontName='Times-Roman',
#             fontSize=9
#         )

#         # Header table
#         header_table = Table([
#             [
#                 Paragraph("YOUR LOGO HERE", normal_style),
#                 Paragraph(
#                     "IonIdea Institute of Technology and Management<br/>Bangalore<br/>Department of Computer Science & Engineering",
#                     header_style
#                 )
#             ]
#         ], colWidths=[80, 440])

#         header_table.setStyle(TableStyle([
#             ('BOX', (0, 0), (0, 0), 1, colors.black),
#             ('ALIGN', (1, 0), (1, 0), 'CENTER'),
#         ]))

#         elements.append(header_table)
#         elements.append(Spacer(1, 10))

#         # Title
#         elements.append(Paragraph("Topic Coverage and Tracking Report", title_style))
#         elements.append(Spacer(1, 6))

#         # Meta
#         meta_table = Table([
#             [
#                 Paragraph(f"<b>Curriculum:</b> {batch_name}", normal_style),
#                 Paragraph(f"<b>Term:</b> {sem_name}", normal_style),
#             ]
#         ], colWidths=[270, 270])

#         meta_table.setStyle(TableStyle([
#             ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
#             ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
#         ]))

#         elements.append(meta_table)
#         elements.append(Spacer(1, 12))

#         # Main table
#         data = [["Sl. No.", "Course Code & Title", "Faculty Name", "Coverage Status", "Remarks"]]
#         sl_no = 1
#         row_index_map = []

#         for section, courses in grouped_data.items():
#             data.append([f"Section: {section}", "", "", "", ""])
#             row_index_map.append(len(data)-1)

#             for c in courses:
#                 data.append([
#                     str(sl_no),
#                     c["code_title"],
#                     c["faculty"],
#                     c["status"],
#                     ""
#                 ])
#                 sl_no += 1

#         table = Table(data, colWidths=[50, 230, 130, 90, 70])
#         table_style = TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#             ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
#             ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
#             ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
#             ('FONTSIZE', (0, 0), (-1, -1), 9),
#             ('ALIGN', (0, 0), (0, -1), 'CENTER'),
#             ('ALIGN', (3, 0), (3, -1), 'CENTER'),
#         ])

#         for row_idx in row_index_map:
#             table_style.add('BACKGROUND', (0, row_idx), (-1, row_idx), colors.grey)
#             table_style.add('FONTNAME', (0, row_idx), (-1, row_idx), 'Times-Bold')
#             table_style.add('SPAN', (0, row_idx), (-1, row_idx))

#         table.setStyle(table_style)
#         elements.append(table)
#         elements.append(Spacer(1, 15))

#         # Legend
#         legend = Table([
#             [
#                 Paragraph('<font color="blue">■</font> LS not added', normal_style),
#                 Paragraph('<font color="red">■</font> Not started', normal_style),
#                 Paragraph('<font color="orange">■</font> In-progress', normal_style),
#                 Paragraph('<font color="green">■</font> Completed', normal_style),
#             ]
#         ], colWidths=[130, 130, 130, 130])

#         legend.setStyle(TableStyle([
#             ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ]))

#         elements.append(legend)

#         doc.build(elements)

#         return FileResponse(
#             temp_file.name,
#             media_type="application/pdf",
#             filename=f"Topic_Coverage_Report_{batch_name.replace(' ', '_')}.pdf"
#         )

#     except Exception as e:
#         logger.error(f"Error generating PDF: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import logging
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import mm
from app.core.database import get_db
from .topic_coverage_schema import (
    CurriculumResponse, TermResponse, CourseResponse,
    CourseTopicsStatusResponse, CourseTopicStatusItem
)

router = APIRouter(tags=["Topic Coverage And Tracking"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1. GET /curriculum  →  list of all curricula
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/curriculum", response_model=List[CurriculumResponse])
def get_curriculum(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("""
            SELECT academic_batch_id AS id, academic_batch_desc AS name
            FROM iems_academic_batch
            WHERE status = 1
            ORDER BY academic_batch_id ASC
        """)).fetchall()
        return [{"id": r.id, "name": r.name} for r in result]
    except Exception as e:
        logger.error(f"Error fetching curriculum: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 2. GET /terms/{curriculum_id}  →  terms for a curriculum
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/terms/{curriculum_id}", response_model=List[TermResponse])
def get_terms(curriculum_id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("""
            SELECT semester_id AS id,
                   CONCAT('Semester ', semester) AS name
            FROM iems_semester
            WHERE status = 1
            ORDER BY semester
        """)).fetchall()

        return [{"id": r.id, "name": r.name} for r in result]

    except Exception as e:
        logger.error(f"Error fetching terms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: determine topic status
#   Returns one of: "LS not added", "Not started", "In-progress", "Completed"
# ─────────────────────────────────────────────────────────────────────────────
def _get_topic_status(topic_id: int, mapping_id: Optional[int], db: Session) -> str:
    """
    Logic:
      - No mapping_id (not imported)         → "LS not added"
      - Has mapping, no schedules at all      → "Not started"
      - Has schedules, none have actual date  → "In-progress"
      - All schedules have actual date        → "Completed"
    """
    if not mapping_id:
        return "LS not added"

    # count total schedules for this mapping
    total = db.execute(text("""
        SELECT COUNT(*) FROM lms_lesson_schedule
        WHERE mapping_id = :mid
    """), {"mid": mapping_id}).scalar() or 0

    if total == 0:
        return "Not started"

    # count schedules that have an actual delivery date
    completed = db.execute(text("""
        SELECT COUNT(*) FROM lms_lesson_schedule
        WHERE mapping_id = :mid
        AND actual_delivery_date IS NOT NULL
    """), {"mid": mapping_id}).scalar() or 0

    if completed == total:
        return "Completed"
    return "In-progress"


STATUS_COLOR = {
    "LS not added": "blue",
    "Not started":  "red",
    "In-progress":  "orange",
    "Completed":    "green",
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. GET /courses  →  section-wise courses with status
#    Query params: academic_batch_id, semester_id
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/courses")
def get_courses(
    academic_batch_id: int,
    semester_id: int,
    db: Session = Depends(get_db)
):
    try:
        print("👉 INPUT:", academic_batch_id, semester_id)

        # ✅ STEP 1: GET SECTIONS
        sections = db.execute(text("""
            SELECT id, section
            FROM iems_section
            WHERE academic_batch_id = :batch_id
            AND semester_id = :sem_id
        """), {
            "batch_id": academic_batch_id,
            "sem_id": semester_id
        }).fetchall()

        print("👉 SECTIONS:", sections)

        # ❗ IMPORTANT: REMOVE semester filter for now (root fix)
        courses = db.execute(text("""
            SELECT crs_id, crs_code, crs_title, academic_batch_id
            FROM iems_courses
            WHERE academic_batch_id = :batch_id
        """), {
            "batch_id": academic_batch_id
        }).fetchall()

        print("👉 COURSES:", courses)

        if not sections:
            print("❌ No sections found")
            return []

        if not courses:
            print("❌ No courses found")
            return []

        # ✅ STEP 2: MAP
        result = []

        for sec in sections:
            section_data = {
                "section_id": sec.id,
                "section": sec.section,
                "courses": []
            }

            for c in courses:
                try:
                    topic = db.execute(text("""
                             SELECT status FROM iems_topics
            WHERE course_id = :cid
            LIMIT 1
                                            """), {"cid": c.crs_id}).fetchone()
                    status = "LS not added"
                    if topic:
                        topic_status = topic[0]

                        if topic_status == "Completed":
                            status = "Completed"
                        elif topic_status == "In-progress":
                            status = "In-progress"
                        elif topic_status == "Not started":
                            status = "Not started"

                except Exception as e:
                    print("⚠️ STATUS ERROR:", e)
                    status = "LS not added"

                section_data["courses"].append({
                    "course_id": c.crs_id,
                    "course_code": c.crs_code,
                    "course_title": c.crs_title,
                    "instructor": "N/A",
                    "section": sec.section,
                    "section_id": sec.id,
                    "status": status,
                    "color": STATUS_COLOR.get(status, "blue")
                })

            result.append(section_data)

        return result

    except Exception as e:
        print("❌ ERROR:", str(e))
        return []
    
# ─────────────────────────────────────────────────────────────────────────────
# 4. GET /course-topics  →  all topics of a course+section with status & dates
#    Query params: course_id, section_id, academic_batch_id, semester_id
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/course-topics")
def get_course_topics(
    course_id: int,
    section_id: int,
    semester_id: int,
    db: Session = Depends(get_db)
):
    try:
        print("🔥 INPUT:", course_id, section_id, semester_id)

        topics = db.execute(text("""
            SELECT t.topic_id, t.topic_code, t.topic_title
            FROM cudos_topic t
            JOIN lms_map_instructor_topic m 
                ON m.topic_id = t.topic_id
            WHERE m.crs_id = :course_id
              AND m.section_id = :section_id
              AND m.semester_id = :semester_id
        """), {
            "course_id": course_id,
            "section_id": section_id,
            "semester_id": semester_id
        }).fetchall()

        print("🔥 TOPICS FOUND:", len(topics))

        result = []

        for t in topics:
            result.append({
                "topic_id": t.topic_id,
                "topic_code": t.topic_code,
                "topic_title": t.topic_title,
                "status": "Not started",
                "color": "red",
                "class_dates": []
            })

        return result

    except Exception as e:
        print("❌ ERROR:", str(e))
        return []
    
# ─────────────────────────────────────────────────────────────────────────────
# 5. GET /export-pdf  →  download PDF report
#    Query params: academic_batch_id, semester_id
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/export-pdf")
def export_topic_coverage_pdf(
    academic_batch_id: int,
    semester_id: int,
    db: Session = Depends(get_db)
):
    try:
        import io
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.pagesizes import A4
        from fastapi.responses import StreamingResponse
        from sqlalchemy import text

        # ✅ Curriculum & Term (SAFE)
        batch_name = db.execute(text("""
            SELECT academic_batch_desc 
            FROM iems_academic_batch 
            WHERE academic_batch_id = :id
        """), {"id": academic_batch_id}).scalar() or "N/A"

        sem_name = db.execute(text("""
            SELECT semester_desc 
            FROM iems_semester 
            WHERE semester_id = :id
        """), {"id": semester_id}).scalar() or "N/A"

        # ✅ 🔥 FIXED QUERY (NO DUPLICATES)
        rows = db.execute(text("""
            SELECT DISTINCT
                sec.section,
                c.crs_id,
                c.crs_code,
                c.crs_title
            FROM iems_section sec
            JOIN iems_courses c 
                ON c.academic_batch_id = sec.academic_batch_id
            WHERE sec.academic_batch_id = :batch_id
              AND sec.semester_id = :sem_id
            ORDER BY sec.section, c.crs_code
        """), {
            "batch_id": academic_batch_id,
            "sem_id": semester_id
        }).fetchall()

        # ✅ GROUP BY SECTION
        grouped = {}
        for r in rows:
            grouped.setdefault(r.section, [])

            # 🔥 REMOVE DUPLICATES MANUALLY (DOUBLE SAFETY)
            if not any(x.crs_id == r.crs_id for x in grouped[r.section]):
                grouped[r.section].append(r)

        # ✅ PDF BUILD
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        styles = getSampleStyleSheet()
        elements = []

        # ✅ TITLE (MATCH IMAGE)
        elements.append(Paragraph(
            "<b><font size=14 color='red'>Topic Coverage and Tracking Report</font></b>",
            styles["Normal"]
        ))

        elements.append(Spacer(1, 10))

        # ✅ HEADER ROW (Curriculum + Term)
        header_table = Table([
            [f"Curriculum: {batch_name}", f"Term: {sem_name}"]
        ], colWidths=[250, 250])

        header_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke)
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 10))

        # ✅ MAIN TABLE HEADER
        data = [[
            "Sl No",
            "Course Code and Course Title",
            "Faculty Name",
            "Coverage Status",
            "Remarks"
        ]]

        sl = 1

        # ✅ SECTION + COURSES
        for section, courses in grouped.items():
            data.append([f"Section: {section}", "", "", "", ""])

            for c in courses:
                data.append([
                    str(sl),
                    f"{c.crs_code} - {c.crs_title}",
                    "N/A",
                    "LS not added",  # you can improve later
                    ""
                ])
                sl += 1

        # ✅ TABLE STYLE (MATCH YOUR IMAGE)
        table = Table(data, repeatRows=1)

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),

            # Section highlight
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ]))

        elements.append(table)

        doc.build(elements)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Topic_Coverage_Report.pdf"}
        )

    except Exception as e:
        print("❌ PDF ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))