from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from app.core.database import get_db
from app.api.v1.lms_module.material.material_schema import *
from app.db.models import *

router = APIRouter()


# ── Dropdown helpers (no auth required, consistent with material routes) ────────

@router.get("/dropdown/batches")
def get_batch_dropdown(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT academic_batch_id, academic_batch_code, academic_batch_desc FROM iems_academic_batch ORDER BY academic_batch_id DESC LIMIT 50"
    )).mappings().all()
    return [dict(r) for r in rows]


@router.get("/dropdown/semesters")
def get_semester_dropdown(academic_batch_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT semester_id, semester, semester_desc FROM iems_semester WHERE academic_batch_id = :bid ORDER BY semester"
    ), {"bid": academic_batch_id}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/dropdown/courses")
def get_course_dropdown(academic_batch_id: int, semester_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT crs_id, crs_code, crs_title FROM iems_courses WHERE academic_batch_id = :bid ORDER BY crs_code"
    ), {"bid": academic_batch_id}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/dropdown/sections")
def get_section_dropdown(academic_batch_id: int, semester_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT MIN(id) AS id, section FROM iems_section WHERE academic_batch_id = :bid GROUP BY section ORDER BY section"
    ), {"bid": academic_batch_id}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/dropdown/all_sections")
def get_all_sections(db: Session = Depends(get_db)):
    """Returns every section row — used when batch/semester data doesn't exist yet."""
    rows = db.execute(text(
        "SELECT MIN(id) AS id, section FROM iems_section GROUP BY section ORDER BY section"
    )).mappings().all()
    return [dict(r) for r in rows]



from typing import List

@router.post("/create_material")
def create_material(
    academic_batch_id: int = Form(0),
    semester_id: int = Form(0),
    course_id: int = Form(0),
    section_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    created_by: int = Form(...),
    topic_id: str = Form(None),
    license: str = Form(None),
    notify_type: str = Form(None),
    additional_info: str = Form(None),
    doc_type: str = Form('document'),
    url: str = Form(None),
    files: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db)
):
    from datetime import datetime as _dt
    from sqlalchemy import text as _text
    
    # ---------- DB INSERT ----------
    # Convert 0 → None so FK constraints aren't violated when batch/semester data doesn't exist
    batch_id_val = academic_batch_id if academic_batch_id and academic_batch_id != 0 else None
    semester_id_val = semester_id if semester_id and semester_id != 0 else None
    course_id_val = course_id if course_id and course_id != 0 else None

    # Helper function to execute DB insert
    def _insert_material(f_name, f_url):
        # Check which optional columns exist in the table
        col_check = db.execute(_text("""
            SELECT GROUP_CONCAT(COLUMN_NAME) AS cols
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'lms_crs_material_upload'
              AND COLUMN_NAME IN ('doc_type', 'license')
        """)).mappings().first()
        existing_optional = set((col_check["cols"] or "").split(",")) if col_check and col_check["cols"] else set()

        extra_cols = ""
        extra_vals = ""
        extra_params = {}
        if "doc_type" in existing_optional:
            extra_cols += ", doc_type"
            extra_vals += ", :doc_type"
            extra_params["doc_type"] = doc_type
        if "license" in existing_optional:
            extra_cols += ", license"
            extra_vals += ", :license"
            extra_params["license"] = license

        base_params = {
            "document_name": title,
            "file_name": f_name,
            "docment_url": f_url,
            "description": description,
            "academic_batch_id": batch_id_val,
            "semester_id": semester_id_val,
            "crs_id": course_id_val,
            "section_ids": str(section_id),
            "topic_ids": topic_id,
            "created_by": created_by,
            "created_date": _dt.now(),
        }
        base_params.update(extra_params)

        db.execute(
            _text(f"""
                INSERT INTO lms_crs_material_upload
                    (document_name, file_name, docment_url, description,
                     academic_batch_id, semester_id, crs_id, section_ids,
                     topic_ids, created_by, created_date, update_cnt{extra_cols})
                VALUES
                    (:document_name, :file_name, :docment_url, :description,
                     :academic_batch_id, :semester_id, :crs_id, :section_ids,
                     :topic_ids, :created_by, :created_date, 0{extra_vals})
            """),
            base_params
        )

    # Handle URL-based materials (no file required)
    if doc_type == 'url':
        if not url or not url.strip():
            raise HTTPException(status_code=400, detail="URL is required for url type material")
        _insert_material(None, url.strip())
        db.commit()
    else:
        # Document type — validate and save files
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="At least one file is required for document type")
            
        allowed_types = ["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "png", "jpg", "jpeg"]
        upload_folder = "uploads/materials"
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        for file in files:
            if not file.filename: continue
            
            file_ext = file.filename.rsplit(".", 1)[-1].lower()
            if file_ext not in allowed_types:
                raise HTTPException(status_code=400, detail=f"Invalid file type '.{file_ext}'. Allowed: {', '.join(allowed_types)}")
                
            file_path_val = f"{upload_folder}/{file.filename}"
            with open(file_path_val, "wb") as buffer:
                buffer.write(file.file.read())
                
            _insert_material(file.filename, file_path_val)
            
        db.commit()

    return {
        "status": True,
        "message": "Material uploaded successfully"
    }


@router.post("/material_list")
def material_list(request: MaterialListRequest, db: Session = Depends(get_db)):

    # Detect which optional columns exist in the table
    col_check = db.execute(text("""
        SELECT GROUP_CONCAT(COLUMN_NAME) AS cols
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'lms_crs_material_upload'
          AND COLUMN_NAME IN ('doc_type', 'license')
    """)).mappings().first()
    existing_optional = set((col_check["cols"] or "").split(",")) if col_check and col_check["cols"] else set()

    doc_type_sel = "m.doc_type," if "doc_type" in existing_optional else "NULL AS doc_type,"
    license_sel  = "m.license,"  if "license"  in existing_optional else "NULL AS license,"

    # Build query with LEFT JOIN on topic so topic_title is returned alongside material
    sql = f"""
        SELECT
            m.mat_id,
            m.document_name,
            m.file_name,
            m.docment_url,
            {doc_type_sel}
            m.description,
            {license_sel}
            m.topic_ids,
            m.section_ids,
            m.academic_batch_id,
            m.semester_id,
            m.crs_id,
            m.created_by,
            m.created_date,
            COALESCE(t.topic_title, '') AS topic_title,
            COALESCE(t.topic_code, '')  AS topic_code
        FROM lms_crs_material_upload m
        LEFT JOIN cudos_topic t
            ON t.topic_id = CAST(NULLIF(TRIM(m.topic_ids), '') AS UNSIGNED)
        WHERE m.section_ids LIKE :section_id_like
    """
    params: dict = {"section_id_like": f"%{request.section_id}%"}

    if request.academic_batch_id and request.academic_batch_id != 0:
        sql += " AND m.academic_batch_id = :academic_batch_id"
        params["academic_batch_id"] = request.academic_batch_id
    if request.semester_id and request.semester_id != 0:
        sql += " AND m.semester_id = :semester_id"
        params["semester_id"] = request.semester_id
    if request.course_id and request.course_id != 0:
        sql += " AND m.crs_id = :course_id"
        params["course_id"] = request.course_id

    sql += " ORDER BY m.mat_id DESC"

    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]



class StudentListRequest(BaseModel):
    section_id: int
    academic_batch_id: int = 0
    semester_id: int = 0

@router.post("/student_list")
def student_list(request: StudentListRequest, db: Session = Depends(get_db)):
    # Look up the section label so we can filter iems_students by section name
    section_row = db.execute(
        text("SELECT section FROM iems_section WHERE id = :id LIMIT 1"),
        {"id": request.section_id}
    ).mappings().first()
    section_label = section_row["section"] if section_row else None

    query = "SELECT student_id, usno, name, first_name, last_name, section, current_semester, academic_batch_id FROM iems_students WHERE status = 1 AND IFNULL(delete_status, 0) = 0"
    params = {}
    if request.academic_batch_id and request.academic_batch_id != 0:
        query += " AND academic_batch_id = :academic_batch_id"
        params["academic_batch_id"] = request.academic_batch_id
    if request.semester_id and request.semester_id != 0:
        query += " AND current_semester = (SELECT semester FROM iems_semester WHERE semester_id = :semester_id LIMIT 1)"
        params["semester_id"] = request.semester_id
    if section_label:
        query += " AND section = :section"
        params["section"] = section_label
    query += " ORDER BY student_id DESC"

    rows = db.execute(text(query), params).mappings().all()
    return {"data": [dict(r) for r in rows]}

@router.post("/share_material")
def share_material(request: ShareMaterialRequest, db: Session = Depends(get_db)):

    for student_usn in request.student_usns:

        mapping = LMSMapShareMaterialsToStudent(
            ssd_id=None,
            mat_id=request.material_id,
            academic_batch_id=request.academic_batch_id,
            section_id=request.section_id,
            student_usn=student_usn
        )

        db.add(mapping)

    db.commit()

    return {
        "status": True,
        "message": "Material shared successfully"
    }

@router.get("/download_material/{mat_id}")
def download_material(mat_id: int, db: Session = Depends(get_db)):

    # Check if doc_type column exists
    col_check = db.execute(text("""
        SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'lms_crs_material_upload'
          AND COLUMN_NAME = 'doc_type'
    """)).mappings().first()
    has_doc_type = col_check and col_check["cnt"] > 0

    doc_type_col = "doc_type" if has_doc_type else "NULL AS doc_type"
    sql = f"SELECT docment_url, file_name, {doc_type_col} FROM lms_crs_material_upload WHERE mat_id = :id"
    row = db.execute(text(sql), {"id": mat_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Material not found")

    if row["doc_type"] == 'url':
        # Safely return URL if someone accidentally tries to download it
        return {"url": row["docment_url"]}

    file_path = row["docment_url"]
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(file_path, filename=row["file_name"] or "material")

@router.put("/update_material/{material_id}")
def update_material(
    material_id: int,
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(None),
    doc_type: str = Form('document'),
    url: str = Form(None),
    section_id: str = Form(None),
    topic_id: str = Form(None),
    license: str = Form(None),
    db: Session = Depends(get_db)
):

    sql = "SELECT mat_id, file_name, docment_url FROM lms_crs_material_upload WHERE mat_id = :id"
    row = db.execute(text(sql), {"id": material_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Material not found")

    file_name_val = row["file_name"]
    file_path_val = row["docment_url"]

    if doc_type == 'url':
        file_name_val = None
        file_path_val = url.strip() if url else row["docment_url"]
    elif file and file.filename:
        allowed_types = ["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "png", "jpg", "jpeg"]
        file_ext = file.filename.rsplit(".", 1)[-1].lower()
        if file_ext not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")
        upload_folder = "uploads/materials"
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        file_path_val = f"{upload_folder}/{file.filename}"
        with open(file_path_val, "wb") as buffer:
            buffer.write(file.file.read())
        file_name_val = file.filename

    # Detect which optional columns exist for the UPDATE
    col_check2 = db.execute(text("""
        SELECT GROUP_CONCAT(COLUMN_NAME) AS cols
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'lms_crs_material_upload'
          AND COLUMN_NAME IN ('doc_type', 'license')
    """)).mappings().first()
    existing_upd = set((col_check2["cols"] or "").split(",")) if col_check2 and col_check2["cols"] else set()

    optional_sets = ""
    upd_params = {
        "title": title,
        "desc": description,
        "file_name": file_name_val,
        "url": file_path_val,
        "section_id": section_id,
        "topic_id": topic_id,
        "id": material_id
    }
    if "doc_type" in existing_upd:
        optional_sets += "doc_type = :doc_type,\n                "
        upd_params["doc_type"] = doc_type
    if "license" in existing_upd:
        optional_sets += "license = COALESCE(:license, license),\n                "
        upd_params["license"] = license

    db.execute(
        text(f"""
            UPDATE lms_crs_material_upload 
            SET document_name = :title,
                description = :desc,
                file_name = :file_name,
                docment_url = :url,
                {optional_sets}
                section_ids = COALESCE(:section_id, section_ids),
                topic_ids = COALESCE(:topic_id, topic_ids),
                update_cnt = update_cnt + 1
            WHERE mat_id = :id
        """),
        upd_params
    )
    db.commit()

    return {
        "status": True,
        "message": "Material updated successfully"
    }

@router.delete("/delete_material/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM lms_map_share_materials_to_student WHERE mat_id = :id"), {"id": material_id})
    res = db.execute(text("DELETE FROM lms_crs_material_upload WHERE mat_id = :id"), {"id": material_id})
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Material not found")
    return {"status": True, "message": "Material deleted successfully"}
@router.post("/material_mapping_list")
def material_mapping_list(request: MaterialMappingRequest, db: Session = Depends(get_db)):

    mappings = db.query(LMSMapShareMaterialsToStudent).filter(
        LMSMapShareMaterialsToStudent.mat_id == request.material_id
    ).all()

    result = []

    for m in mappings:
        # Look up student name from iems_students table (usno column)
        student_row = db.execute(
            text("SELECT name, first_name, last_name FROM iems_students WHERE usno = :usno LIMIT 1"),
            {"usno": m.student_usn}
        ).mappings().first()

        if student_row:
            first = student_row.get("first_name") or ""
            last  = student_row.get("last_name")  or ""
            name  = f"{first} {last}".strip() or student_row.get("name") or m.student_usn
        else:
            name = m.student_usn

        result.append({
            "student_usn": m.student_usn,
            "student_name": name,
            "section_id": m.section_id
        })

    return result
