from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session
from fastapi.responses import Response

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess

from .consolidated_student_marks_schema import (
    ConsolidatedStudentMarksGraphResponse,
    ConsolidatedStudentMarksRequest,
    ConsolidatedStudentMarksResponse,
    CourseListResponse,
    CurriculumListResponse,
    DropdownListResponse,
    ExportRequest,
    SectionListResponse,
    TermListResponse,
)
from .consolidated_student_marks_service import (
    build_consolidated_student_marks_graph,
    build_consolidated_student_marks_report,
    get_course_options,
    get_curriculum_options,
    get_department_options,
    get_section_options,
    get_term_options,
    export_consolidated_student_marks_report,
)

router = APIRouter(tags=["Consolidated Student Marks Report"])


@router.get("/marks/departments", response_model=DropdownListResponse)
def get_marks_departments(
    db: Session = Depends(get_db),
    org_id: Optional[int] = Header(None),
):
    data = get_department_options(db, org_id or 1)
    return returnSuccess(data, "Success")


@router.get("/marks/curriculums", response_model=CurriculumListResponse)
def get_marks_curriculums(
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    org_id: Optional[int] = Header(None),
):
    data = get_curriculum_options(db, org_id or 1, department_id)
    return returnSuccess(data, "Success")


@router.get("/marks/terms", response_model=TermListResponse)
def get_marks_terms(
    academic_batch_id: int = Query(...),
    db: Session = Depends(get_db),
):
    data = get_term_options(db, academic_batch_id)
    return returnSuccess(data, "Success")


@router.get("/marks/sections", response_model=SectionListResponse)
def get_marks_sections(
    academic_batch_id: int = Query(...),
    semester_id: Optional[int] = Query(None),
    crclm_term_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    data = get_section_options(db, academic_batch_id, semester_id, crclm_term_id)
    return returnSuccess(data, "Success")


@router.get("/marks/courses", response_model=CourseListResponse)
def get_marks_courses(
    academic_batch_id: int = Query(...),
    semester_id: Optional[int] = Query(None),
    crclm_term_id: Optional[int] = Query(None),
    section_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    data = get_course_options(db, academic_batch_id, semester_id, crclm_term_id, section_id)
    return returnSuccess(data, "Success")


@router.post(
    "/consolidated-student-marks",
    response_model=ConsolidatedStudentMarksResponse,
)
def get_consolidated_student_marks(
    payload: ConsolidatedStudentMarksRequest,
    org_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
):
    data = build_consolidated_student_marks_report(db, payload, org_id or 1)
    message = "Success" if data["rows"] else "No records found"
    return returnSuccess(data, message)


@router.post(
    "/consolidated-student-marks/graph",
    response_model=ConsolidatedStudentMarksGraphResponse,
)
def get_consolidated_student_marks_graph(
    payload: ConsolidatedStudentMarksRequest,
    org_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
):
    data = build_consolidated_student_marks_graph(db, payload, org_id or 1)
    message = "Success" if data["courses"] else "No records found"
    return returnSuccess(data, message)


@router.post("/consolidated-student-marks/export")
def export_consolidated_student_marks(
    payload: ExportRequest,
    org_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
):
    content, media_type, extension = export_consolidated_student_marks_report(db, payload, org_id or 1)
    return Response(content=content, media_type=media_type, headers={
        "Content-Disposition": f'attachment; filename="consolidated-student-marks.{extension}"',
    })
