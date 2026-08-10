from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db import models


def _optional_org_filter(column, org_id: Optional[int]):
    if org_id is None:
        return True
    return or_(column == org_id, column.is_(None))


def _resolve_semester_context(
    db: Session,
    academic_batch_id: int,
    requested_semester: Optional[int],
) -> Dict[str, Optional[int]]:
    context: Dict[str, Optional[int]] = {
        "input_semester_id": requested_semester,
        "resolved_crclm_term_id": None,
        "resolved_semester_id": None,
        "resolved_semester_number": None,
    }
    if requested_semester is None:
        return context

    requested_value = int(requested_semester)
    term_query = db.query(models.IEMSCrclmTerm).filter(
        models.IEMSCrclmTerm.crclm_id == academic_batch_id
    )
    semester_query = db.query(models.IEMSemester).filter(
        models.IEMSemester.academic_batch_id == academic_batch_id
    )

    term_row = term_query.filter(
        models.IEMSCrclmTerm.crclm_term_id == requested_value
    ).first()
    if term_row is not None:
        context["resolved_crclm_term_id"] = term_row.crclm_term_id
        context["resolved_semester_number"] = term_row.term_name
    else:
        semester_row = semester_query.filter(
            models.IEMSemester.semester_id == requested_value
        ).first()
        if semester_row is not None:
            context["resolved_semester_id"] = semester_row.semester_id
            context["resolved_semester_number"] = (
                semester_row.semester or semester_row.semester_id
            )
        else:
            semester_row = semester_query.filter(
                models.IEMSemester.semester == requested_value
            ).first()
            if semester_row is not None:
                context["resolved_semester_id"] = semester_row.semester_id
                context["resolved_semester_number"] = semester_row.semester
            else:
                context["resolved_semester_id"] = requested_value
                context["resolved_semester_number"] = requested_value

    if (
        context["resolved_semester_id"] is None
        and context["resolved_semester_number"] is not None
    ):
        semester_row = semester_query.filter(
            models.IEMSemester.semester == context["resolved_semester_number"]
        ).first()
        if semester_row is not None:
            context["resolved_semester_id"] = semester_row.semester_id

    if (
        context["resolved_crclm_term_id"] is None
        and context["resolved_semester_number"] is not None
    ):
        term_row = term_query.filter(
            models.IEMSCrclmTerm.term_name == context["resolved_semester_number"]
        ).first()
        if term_row is not None:
            context["resolved_crclm_term_id"] = term_row.crclm_term_id

    if context["resolved_semester_id"] is None:
        context["resolved_semester_id"] = context["resolved_semester_number"]

    return context


def _is_dummy_identifier(value: Optional[str]) -> bool:
    if value is None:
        return False
    normalized = str(value).strip()
    return normalized.isdigit()


def _build_resolved_filters(
    request,
    semester_context: Dict[str, Optional[int]],
    section_row: Optional[models.IEMSection] = None,
    selected_course_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    return {
        "department_id": request.department_id,
        "academic_batch_id": request.academic_batch_id,
        "crclm_term_id": semester_context["resolved_crclm_term_id"],
        "semester_id": semester_context["resolved_semester_id"],
        "semester_number": semester_context["resolved_semester_number"],
        "section_id": request.section_id,
        "section_name": getattr(section_row, "section", None),
        "selected_course_ids": selected_course_ids or [],
        "include_total_marks": request.include_total_marks,
        "from_date": request.from_date,
        "to_date": request.to_date,
    }


def get_department_options(db: Session, org_id: Optional[int]) -> List[Dict[str, Any]]:
    rows = (
        db.query(models.IEMSDepartment)
        .filter(_optional_org_filter(models.IEMSDepartment.org_id, org_id))
        .order_by(models.IEMSDepartment.dept_name.asc())
        .all()
    )
    return [{"id": row.dept_id, "name": row.dept_name} for row in rows]


def get_curriculum_options(
    db: Session,
    org_id: Optional[int],
    department_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    query = (
        db.query(models.IEMSAcademicBatch, models.IEMSCurriculum)
        .outerjoin(
            models.IEMSCurriculum,
            models.IEMSCurriculum.crclm_id == models.IEMSAcademicBatch.academic_batch_id,
        )
        .filter(_optional_org_filter(models.IEMSAcademicBatch.org_id, org_id))
    )
    if department_id is not None:
        query = query.filter(models.IEMSAcademicBatch.dept_id == department_id)

    rows = query.order_by(models.IEMSAcademicBatch.academic_batch_desc.asc()).all()
    return [
        {
            "academic_batch_id": batch.academic_batch_id,
            "crclm_id": curriculum.crclm_id if curriculum else batch.academic_batch_id,
            "name": batch.academic_batch_desc or batch.academic_batch_code,
            "dept_id": batch.dept_id,
            "pgm_id": batch.pgm_id,
        }
        for batch, curriculum in rows
    ]


def get_term_options(db: Session, academic_batch_id: int) -> List[Dict[str, Any]]:
    rows = (
        db.query(models.IEMSCrclmTerm, models.IEMSemester)
        .outerjoin(
            models.IEMSemester,
            and_(
                models.IEMSemester.academic_batch_id == models.IEMSCrclmTerm.crclm_id,
                models.IEMSemester.semester == models.IEMSCrclmTerm.term_name,
            ),
        )
        .filter(models.IEMSCrclmTerm.crclm_id == academic_batch_id)
        .order_by(models.IEMSCrclmTerm.term_name.asc())
        .all()
    )
    return [
        {
            "crclm_term_id": term.crclm_term_id,
            "semester_id": semester.semester_id if semester else None,
            "semester_number": term.term_name,
            "name": getattr(semester, "semester_desc", None) or f"Semester {term.term_name}",
        }
        for term, semester in rows
    ]


def get_section_options(
    db: Session,
    academic_batch_id: int,
    semester_id: Optional[int] = None,
    crclm_term_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    semester_context = _resolve_semester_context(
        db,
        academic_batch_id,
        crclm_term_id or semester_id,
    )
    rows = (
        db.query(models.IEMSection)
        .filter(
            models.IEMSection.academic_batch_id == academic_batch_id,
            or_(
                models.IEMSection.semester_id == semester_context["resolved_semester_id"],
                models.IEMSection.semester_id == semester_context["resolved_semester_number"],
            ),
        )
        .order_by(models.IEMSection.section.asc())
        .all()
    )
    return [
        {"section_id": row.id, "section_name": row.section}
        for row in rows
        if row.section
    ]


def get_course_options(
    db: Session,
    academic_batch_id: int,
    semester_id: Optional[int] = None,
    crclm_term_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    semester_context = _resolve_semester_context(
        db,
        academic_batch_id,
        crclm_term_id or semester_id,
    )
    query = db.query(models.IEMSCourses).filter(
        models.IEMSCourses.academic_batch_id == academic_batch_id
    )
    if semester_context["resolved_semester_number"] is not None:
        query = query.filter(
            models.IEMSCourses.semester == semester_context["resolved_semester_number"]
        )

    rows = query.order_by(
        models.IEMSCourses.crs_order.asc(),
        models.IEMSCourses.crs_code.asc(),
    ).all()
    return [
        {
            "course_id": row.crs_id,
            "course_code": row.crs_code,
            "course_title": row.crs_title or row.crs_code,
            "semester": row.semester,
        }
        for row in rows
    ]


def _pick_mark_value(*values: Optional[float]) -> Optional[float]:
    for value in values:
        if value is not None:
            return float(value)
    return None


def _append_component(
    components: List[Dict[str, Any]],
    occasion_name: str,
    marks: Optional[float],
    max_marks: Optional[float] = None,
    source: Optional[str] = None,
) -> None:
    if marks is None:
        return
    components.append(
        {
            "occasion_name": occasion_name,
            "max_marks": float(max_marks) if max_marks is not None else None,
            "marks": float(marks),
            "source": source,
        }
    )


def _build_components(
    student_course: models.StudentCourse,
    course: Optional[models.IEMSCourses],
    detailed_components: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    components = list(detailed_components)
    has_detailed_cia = len(detailed_components) > 0

    if not has_detailed_cia:
        _append_component(
            components,
            "CIA Total",
            student_course.total_cia,
            getattr(course, "cia_max_marks", None),
            "student_course",
        )
        _append_component(
            components,
            "ISE Total",
            student_course.total_ise,
            getattr(course, "ise_max_marks", None),
            "student_course",
        )
        _append_component(
            components,
            "MSE Total",
            student_course.total_mse,
            getattr(course, "mse_max_marks", None),
            "student_course",
        )

    see_marks = _pick_mark_value(student_course.see_actual, student_course.see)
    _append_component(
        components,
        "SEE",
        see_marks,
        getattr(course, "see_max_marks", None),
        "student_course",
    )
    _append_component(
        components,
        "Viva",
        student_course.viva_marks,
        getattr(course, "viva_max_marks", None),
        "student_course",
    )
    tw_marks = _pick_mark_value(student_course.tw_marks_actual, student_course.tw_marks)
    _append_component(
        components,
        "TW",
        tw_marks,
        getattr(course, "tw_max_marks", None),
        "student_course",
    )

    if (
        not has_detailed_cia
        and student_course.cia_see is not None
        and student_course.total_cia is None
        and see_marks is None
    ):
        combined_max = None
        if course is not None:
            cia_max = getattr(course, "cia_max_marks", None) or 0
            see_max = getattr(course, "see_max_marks", None) or 0
            combined_max = cia_max + see_max if cia_max or see_max else None
        _append_component(
            components,
            "CIA + SEE",
            student_course.cia_see,
            combined_max,
            "student_course",
        )

    return components


def _build_course_lookup(
    db: Session,
    academic_batch_id: int,
    semester_number: Optional[int],
    selected_course_ids: Optional[List[int]],
) -> Dict[str, models.IEMSCourses]:
    query = db.query(models.IEMSCourses).filter(
        models.IEMSCourses.academic_batch_id == academic_batch_id
    )
    if semester_number is not None:
        query = query.filter(models.IEMSCourses.semester == semester_number)
    if selected_course_ids:
        query = query.filter(models.IEMSCourses.crs_id.in_(selected_course_ids))
    rows = query.all()
    return {row.crs_code: row for row in rows}


def _base_student_course_query(
    db: Session,
    academic_batch_id: int,
    semester_number: int,
    section_name: Optional[str],
):
    query = db.query(models.StudentCourse).filter(
        models.StudentCourse.batch_id == academic_batch_id,
        models.StudentCourse.semester == semester_number,
        models.StudentCourse.is_withdrawn == 0,
        models.StudentCourse.is_drop == 0,
    )
    if section_name:
        query = query.filter(models.StudentCourse.section == section_name)
    return query


def _fetch_detailed_components(
    db: Session,
    std_crs_ids: List[int],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Dict[int, List[Dict[str, Any]]]:
    if not std_crs_ids:
        return {}

    query = (
        db.query(
            models.IEMSCIAStudentCourses,
            models.IEMSCIOccasionType,
            models.IEMSCIAExamMaster,
        )
        .outerjoin(
            models.IEMSCIOccasionType,
            models.IEMSCIOccasionType.cia_occasion_type_id == models.IEMSCIAStudentCourses.occasion_id,
        )
        .outerjoin(
            models.IEMSCIAExamMaster,
            models.IEMSCIAExamMaster.id == models.IEMSCIAStudentCourses.cia_master_id,
        )
        .filter(models.IEMSCIAStudentCourses.std_crs_id.in_(std_crs_ids))
    )
    if from_date is not None:
        query = query.filter(models.IEMSCIAStudentCourses.result_year >= from_date)
    if to_date is not None:
        query = query.filter(models.IEMSCIAStudentCourses.result_year <= to_date)

    rows = query.all()
    component_map: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for student_course, occasion, exam_master in rows:
        occasion_name = (
            getattr(occasion, "cia_occasion_type_desc", None)
            or getattr(occasion, "cia_occasion_type_code", None)
            or f"Occasion {student_course.occasion_id}"
        )
        component_map[student_course.std_crs_id].append(
            {
                "occasion_name": occasion_name,
                "max_marks": float(exam_master.cia_max_marks)
                if exam_master and exam_master.cia_max_marks is not None
                else None,
                "marks": float(student_course.secured_marks)
                if student_course.secured_marks is not None
                else None,
                "source": "cia_student_courses",
            }
        )
    return component_map


def _fetch_student_lookup(
    db: Session,
    regnos: List[str],
    usnos: List[str],
) -> Dict[str, models.IEMStudents]:
    filters = []
    if regnos:
        filters.append(models.IEMStudents.regno.in_(regnos))
    if usnos:
        filters.append(models.IEMStudents.usno.in_(usnos))
    if not filters:
        return {}

    rows = db.query(models.IEMStudents).filter(or_(*filters)).all()
    lookup: Dict[str, models.IEMStudents] = {}
    for row in rows:
        if row.regno:
            lookup[f"regno:{row.regno}"] = row
        if row.usno:
            lookup[f"usno:{row.usno}"] = row
    return lookup


def _log_student_identity_mismatches(
    student_course_rows: List[models.StudentCourse],
    student_lookup: Dict[str, models.IEMStudents],
) -> None:
    mismatches = []
    for row in student_course_rows:
        usno_match = bool(row.usno and student_lookup.get(f"usno:{row.usno}"))
        regno_match = bool(row.regno and student_lookup.get(f"regno:{row.regno}"))
        if not usno_match and not regno_match:
            mismatches.append(
                {
                    "std_crs_id": row.std_crs_id,
                    "student_course_usno": row.usno,
                    "student_course_regno": row.regno,
                    "crs_code": row.crs_code,
                }
            )
        if len(mismatches) >= 5:
            break

    if mismatches:
        print("Consolidated marks student identity mismatches:", mismatches)


def _resolve_student_identity(
    student_course: models.StudentCourse,
    student_lookup: Dict[str, models.IEMStudents],
) -> Dict[str, Optional[str]]:
    student = None
    match_source = None

    if student_course.usno:
        student = student_lookup.get(f"usno:{student_course.usno}")
        if student is not None:
            match_source = "usno"

    if student is None and student_course.regno:
        student = student_lookup.get(f"regno:{student_course.regno}")
        if student is not None:
            match_source = "regno"

    resolved_usn = (
        getattr(student, "usno", None)
        or student_course.usno
        or (None if _is_dummy_identifier(student_course.regno) else student_course.regno)
        or f"STD-{student_course.std_crs_id}"
    )
    resolved_regno = getattr(student, "regno", None) or (
        None if _is_dummy_identifier(student_course.regno) else student_course.regno
    )

    resolved_name = None
    if student is not None:
        resolved_name = getattr(student, "name", None) or " ".join(
            [
                part
                for part in [
                    getattr(student, "first_name", None),
                    getattr(student, "middle_name", None),
                    getattr(student, "last_name", None),
                ]
                if part
            ]
        ).strip()

    if not resolved_name:
        if student_course.usno:
            resolved_name = f"Unknown Student ({student_course.usno})"
        elif not _is_dummy_identifier(student_course.regno):
            resolved_name = f"Unknown Student ({student_course.regno})"
        else:
            resolved_name = f"Unknown Student ({student_course.std_crs_id})"

    return {
        "student_usn": resolved_usn,
        "student_name": resolved_name,
        "regno": resolved_regno,
        "match_source": match_source,
        "student_identity_status": "matched" if student is not None else "fallback",
    }


def build_consolidated_student_marks_report(
    db: Session,
    request,
) -> Dict[str, Any]:
    print(
        "Consolidated marks incoming request:",
        {
            "academic_batch_id": request.academic_batch_id,
            "semester_id": request.semester_id,
            "crclm_term_id": request.crclm_term_id,
            "section_id": request.section_id,
            "course_ids": request.course_ids or [],
            "include_total_marks": request.include_total_marks,
            "from_date": request.from_date,
            "to_date": request.to_date,
        },
    )

    if (
        request.from_date is not None
        and request.to_date is not None
        and request.from_date > request.to_date
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="from_date cannot be greater than to_date",
        )

    requested_semester = request.crclm_term_id or request.semester_id
    if requested_semester is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="semester_id or crclm_term_id is required",
        )

    batch = db.query(models.IEMSAcademicBatch).filter(
        models.IEMSAcademicBatch.academic_batch_id == request.academic_batch_id
    ).first()
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic batch not found",
        )
    if request.department_id is not None and batch.dept_id != request.department_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic batch does not belong to the selected department",
        )

    semester_context = _resolve_semester_context(
        db,
        request.academic_batch_id,
        requested_semester,
    )
    if semester_context["resolved_semester_number"] is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to resolve semester for the selected term",
        )

    section_row = None
    if request.section_id is not None:
        section_row = db.query(models.IEMSection).filter(
            models.IEMSection.id == request.section_id
        ).first()
        if section_row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found",
            )
        if section_row.academic_batch_id != request.academic_batch_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section does not belong to the selected curriculum",
            )

    selected_course_ids = request.course_ids or []
    course_lookup = _build_course_lookup(
        db,
        request.academic_batch_id,
        semester_context["resolved_semester_number"],
        selected_course_ids,
    )
    if selected_course_ids:
        missing_course_ids = sorted(
            set(selected_course_ids) - {row.crs_id for row in course_lookup.values()}
        )
        if missing_course_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invalid course_ids for the selected curriculum/term: {missing_course_ids}",
            )

    selected_course_codes = list(course_lookup.keys())
    print(
        "Consolidated marks resolved selected courses:",
        [
            {
                "course_id": row.crs_id,
                "course_code": row.crs_code,
                "semester": row.semester,
            }
            for row in course_lookup.values()
        ],
    )

    roster_query = _base_student_course_query(
        db,
        request.academic_batch_id,
        semester_context["resolved_semester_number"],
        getattr(section_row, "section", None),
    )
    if section_row is not None and section_row.section:
        if section_row.semester_id not in {
            semester_context["resolved_semester_id"],
            semester_context["resolved_semester_number"],
        }:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section does not belong to the selected term",
            )
    roster_rows = roster_query.order_by(
        models.StudentCourse.regno.asc(),
        models.StudentCourse.crs_code.asc(),
    ).all()

    student_course_query = roster_query
    if selected_course_codes:
        student_course_query = student_course_query.filter(
            models.StudentCourse.crs_code.in_(selected_course_codes)
        )

    student_course_rows = student_course_query.order_by(
        models.StudentCourse.regno.asc(),
        models.StudentCourse.crs_code.asc(),
    ).all()
    print(
        "Consolidated marks roster size and filtered row count:",
        {
            "roster_rows": len(roster_rows),
            "filtered_rows": len(student_course_rows),
            "selected_course_codes": selected_course_codes,
        },
    )
    std_crs_ids = [row.std_crs_id for row in student_course_rows]
    detailed_component_map = _fetch_detailed_components(
        db,
        std_crs_ids,
        request.from_date,
        request.to_date,
    )
    student_lookup = _fetch_student_lookup(
        db,
        [row.regno for row in roster_rows if row.regno],
        [row.usno for row in roster_rows if row.usno],
    )
    _log_student_identity_mismatches(roster_rows, student_lookup)

    rows_by_student: Dict[str, Dict[str, Any]] = {}
    for student_course in roster_rows:
        identity = _resolve_student_identity(student_course, student_lookup)
        student_key = f"{identity['student_usn']}|{identity['regno'] or ''}"
        if student_key not in rows_by_student:
            rows_by_student[student_key] = {
                "student_usn": identity["student_usn"],
                "student_name": identity["student_name"],
                "regno": identity["regno"],
                "section": student_course.section,
                "student_identity_status": identity["student_identity_status"],
                "courses": [],
                "_course_map": {},
            }

    for student_course in student_course_rows:
        course = course_lookup.get(student_course.crs_code)
        if course is None:
            continue

        identity = _resolve_student_identity(student_course, student_lookup)
        student_key = f"{identity['student_usn']}|{identity['regno'] or ''}"
        components = _build_components(
            student_course,
            course,
            detailed_component_map.get(student_course.std_crs_id, []),
        )
        total_marks = None
        if request.include_total_marks:
            numeric_marks = [
                component["marks"]
                for component in components
                if component["marks"] is not None
            ]
            total_marks = round(sum(numeric_marks), 2) if numeric_marks else 0.0

        rows_by_student[student_key]["_course_map"][course.crs_id] = {
            "course_id": course.crs_id,
            "course_code": course.crs_code,
            "course_title": course.crs_title or course.crs_code,
            "components": components,
            "total_marks": total_marks,
            "data_available": len(components) > 0,
        }

    report_rows = []
    for index, student_row in enumerate(
        sorted(
            rows_by_student.values(),
            key=lambda item: (item["student_name"], item["student_usn"]),
        ),
        start=1,
    ):
        student_row["sl_no"] = index
        for course in course_lookup.values():
            if course.crs_id not in student_row["_course_map"]:
                student_row["_course_map"][course.crs_id] = {
                    "course_id": course.crs_id,
                    "course_code": course.crs_code,
                    "course_title": course.crs_title or course.crs_code,
                    "components": [],
                    "total_marks": 0.0 if request.include_total_marks else None,
                    "data_available": False,
                }
        student_row["courses"] = sorted(
            list(student_row["_course_map"].values()),
            key=lambda course_row: (course_row["course_code"], course_row["course_id"]),
        )
        del student_row["_course_map"]
        report_rows.append(student_row)

    return {
        "filters": _build_resolved_filters(
            request,
            semester_context,
            section_row=section_row,
            selected_course_ids=[course.crs_id for course in course_lookup.values()],
        ),
        "rows": report_rows,
    }


def build_consolidated_student_marks_graph(
    db: Session,
    request,
) -> Dict[str, Any]:
    report = build_consolidated_student_marks_report(db, request)
    course_stats: Dict[int, Dict[str, Any]] = {}
    course_thresholds: Dict[int, Optional[float]] = {}

    for student_row in report["rows"]:
        for course_row in student_row["courses"]:
            marks_value = course_row["total_marks"]
            if marks_value is None:
                marks_value = round(
                    sum(
                        component["marks"]
                        for component in course_row["components"]
                        if component["marks"] is not None
                    ),
                    2,
                )

            stats = course_stats.setdefault(
                course_row["course_id"],
                {
                    "course_id": course_row["course_id"],
                    "course_code": course_row["course_code"],
                    "course_title": course_row["course_title"],
                    "marks": [],
                },
            )
            stats["marks"].append(float(marks_value))

            if course_row["course_id"] not in course_thresholds:
                course = db.query(models.IEMSCourses).filter(
                    models.IEMSCourses.crs_id == course_row["course_id"]
                ).first()
                course_thresholds[course_row["course_id"]] = (
                    getattr(course, "min_passing_marks", None) if course else None
                )

    graph_rows = []
    for course_id, stats in sorted(
        course_stats.items(),
        key=lambda item: item[1]["course_code"],
    ):
        marks = stats["marks"]
        average = round(sum(marks) / len(marks), 2) if marks else 0.0
        highest = round(max(marks), 2) if marks else 0.0
        lowest = round(min(marks), 2) if marks else 0.0
        min_passing_marks = course_thresholds.get(course_id)
        pass_count = None
        fail_count = None
        if min_passing_marks is not None:
            pass_count = len(
                [mark for mark in marks if mark >= float(min_passing_marks)]
            )
            fail_count = len(marks) - pass_count

        graph_rows.append(
            {
                "course_id": stats["course_id"],
                "course_code": stats["course_code"],
                "course_title": stats["course_title"],
                "student_count": len(marks),
                "average_marks": average,
                "highest_marks": highest,
                "lowest_marks": lowest,
                "min_passing_marks": float(min_passing_marks)
                if min_passing_marks is not None
                else None,
                "pass_count": pass_count,
                "fail_count": fail_count,
            }
        )

    return {
        "filters": report["filters"],
        "courses": graph_rows,
    }
