from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from .student_assignment_schema import *
from datetime import datetime
from fastapi.responses import FileResponse
from openpyxl import Workbook
import os


router = APIRouter(tags=["Student Assignment"])


# ✅ 1. ASSIGNMENT DROPDOWN API
@router.post("/assignment_list")
def get_assignment_list(data: AssignmentListRequest, db: Session = Depends(get_db)):
    try:
        print("Incoming Request:", data.dict())

        query = text("""
            SELECT DISTINCT 
    m.lms_assignment_id,
    a.assignment_name
FROM lms_map_assignment_to_students m
JOIN lms_manage_assignment a 
    ON a.lms_assignment_id = m.lms_assignment_id
WHERE a.crs_id = :course_id
AND a.semester_id = :semester_id
AND a.academic_batch_id = :academic_batch_id
        """)

        rows = db.execute(query, {
            "course_id": data.course_id,
            "semester_id": data.semester_id,
            "academic_batch_id": data.academic_batch_id
        }).mappings().all()

        print("Assignments Fetched:", rows)

        return {
            "status": True,
            "data": [
                {
                    "value": row["lms_assignment_id"],
                    "label": row["assignment_name"]
                }
                for row in rows
            ]
        }

    except Exception as e:
        return {
            "status": False,
            "error": str(e)
        }


# ✅ 2. STUDENT REPORT API  — fixed: convert mappings to plain dicts
@router.post("/report")
def get_student_assignment_report(
    data: StudentAssignmentReportRequest,
    db: Session = Depends(get_db)
):
    try:
        query = text("""
SELECT 
    m.student_usn,
    CONCAT(
        COALESCE(u.first_name, ''),
        ' ',
        COALESCE(u.middle_name, ''),
        ' ',
        COALESCE(u.last_name, '')
    ) AS student_name,
    m.secured_marks
FROM lms_map_assignment_to_students m
LEFT JOIN iems_students u 
    ON u.usno = m.student_usn   -- ✅ FIXED HERE
WHERE m.lms_assignment_id = :assignment_id
""")

        result = db.execute(
            query,
            {"assignment_id": data.assignment_id}
        ).mappings().all()

        return {
            "status": True,
            "data": [dict(row) for row in result]
        }

    except Exception as e:
        return {
            "status": False,
            "error": str(e)
        }

# ✅ 3. EXPORT EXCEL API
@router.post("/export")
def export_assignment_report(
    data: StudentAssignmentReportRequest,
    db: Session = Depends(get_db)
):
    try:
        query = text("""
SELECT 
    m.student_usn,
    CONCAT(
        COALESCE(u.first_name, ''),
        ' ',
        COALESCE(u.middle_name, ''),
        ' ',
        COALESCE(u.last_name, '')
    ) AS student_name,
    m.secured_marks
FROM lms_map_assignment_to_students m
LEFT JOIN iems_students u 
    ON u.usno = m.student_usn   -- ✅ FIXED HERE
WHERE m.lms_assignment_id = :assignment_id
""")
        result = db.execute(
            query,
            {"assignment_id": data.assignment_id}
        ).mappings().all()

        if not result:
            return {"status": False, "message": "No data found"}

        wb = Workbook()
        ws = wb.active
        ws.title = "Assignment Report"

        # ✅ Metadata
        ws.append(["Date of Export Report", datetime.now().strftime("%d-%m-%Y")])
        ws.append([])

        # ✅ Header (NO remark)
        ws.append(["Sl No", "Student USN", "Student Name", "Marks"])

        # ✅ Data rows
        for index, row in enumerate(result, start=1):
            ws.append([
                index,
                row["student_usn"],
                row["student_name"],
                row["secured_marks"]
            ])

        file_name = f"assignment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = f"./{file_name}"

        wb.save(file_path)

        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return {
            "status": False,
            "error": str(e)
        }