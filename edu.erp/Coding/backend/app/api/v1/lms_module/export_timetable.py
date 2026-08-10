from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...utils.http_return_helper import returnException, returnSuccess

router = APIRouter(prefix="/export-timetable", tags=["Export Timetable"])


# Fetches timetable rows with faculty details for the selected academic filters.
def _fetch_timetable_rows(
    db: Session,
    academic_batch_id: int,
    semester_id: int,
    section_id: Optional[int] = None,
):
    query = """
        SELECT
            ls.lls_id AS schedule_id,
            ls.crs_id,
            ls.plan_date,
            ls.start_time,
            ls.end_time,
            ls.section_id,
            c.crs_code,
            c.crs_title,
            s.section,
            dm.day_id,
            dm.week_day_name,
            dm.allot_by AS faculty_id,
            u.username AS faculty_username,
            TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))) AS faculty_name
        FROM lms_lesson_schedule ls
        LEFT JOIN iems_courses c
          ON c.crs_id = ls.crs_id
        LEFT JOIN iems_section s
          ON s.id = ls.section_id
        LEFT JOIN lms_tt_time_table_day_mapping dm
          ON dm.tt_day_map_id = ls.tt_day_map_id
        LEFT JOIN iems_users u
          ON u.id = dm.allot_by
        WHERE ls.academic_batch_id = :academic_batch_id
          AND ls.semester_id = :semester_id
    """
    params = {
        "academic_batch_id": academic_batch_id,
        "semester_id": semester_id,
    }
    if section_id is not None:
        query += " AND ls.section_id = :section_id"
        params["section_id"] = section_id
    query += " ORDER BY ls.plan_date ASC, ls.start_time ASC, ls.end_time ASC"
    return db.execute(text(query), params).mappings().all()


# Renders timetable rows into a simple PDF document.
def _build_timetable_pdf(rows, title: str) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 40
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, title)
    y -= 24

    pdf.setFont("Helvetica", 10)
    for row in rows:
        course_label = row["crs_title"] or row["crs_code"] or "N/A"
        faculty_label = row["faculty_name"] or row["faculty_username"] or "Not Assigned"
        section_label = row["section"] or "N/A"
        weekday_label = row["week_day_name"] or ""
        line = (
            f"{row['plan_date']} {weekday_label} | "
            f"{row['start_time']} - {row['end_time']} | "
            f"{course_label} | Section {section_label} | {faculty_label}"
        )
        pdf.drawString(40, y, line[:140])
        y -= 18

        if y < 50:
            pdf.showPage()
            y = height - 40
            pdf.setFont("Helvetica", 10)

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


# Fetches timetable created along with faculty details for display in the UI.
@router.get("/list")
def get_export_timetable_list(
    academic_batch_id: int,
    semester_id: int,
    section_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    rows = _fetch_timetable_rows(
        db=db,
        academic_batch_id=academic_batch_id,
        semester_id=semester_id,
        section_id=section_id,
    )
    return returnSuccess({"total": len(rows), "items": rows})


# Exports the created timetable with faculty details to a PDF file.
@router.get("/pdf")
def export_timetable_pdf_report(
    academic_batch_id: int,
    semester_id: int,
    section_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    rows = _fetch_timetable_rows(
        db=db,
        academic_batch_id=academic_batch_id,
        semester_id=semester_id,
        section_id=section_id,
    )
    if not rows:
        return returnException("No timetable data found for the selected filters")

    title = f"Timetable Export - Batch {academic_batch_id} - Semester {semester_id}"
    if section_id is not None:
        title += f" - Section {section_id}"

    pdf_bytes = _build_timetable_pdf(rows, title)
    filename = f"timetable_{academic_batch_id}_{semester_id}"
    if section_id is not None:
        filename += f"_{section_id}"
    filename += ".pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
