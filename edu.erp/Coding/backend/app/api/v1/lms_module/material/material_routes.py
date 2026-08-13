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
async def create_material(
    academic_batch_id: int = Form(0),
    semester_id: int = Form(0),
    course_id: int = Form(0),
    section_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    created_by: int = Form(...),
    topic_id: str = Form(None),
    license: str = Form(None),  # 'Proprietary', 'Paid', 'Public'
    notify_type: str = Form(None),  # 'pre' or 'post'
    additional_info: str = Form(None),
    doc_type: str = Form('document'),
    url: str = Form(None),
    files: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db)
):
    from datetime import datetime as _dt
    from sqlalchemy import text as _text
    
    # Convert license string to license_flag (tinyint)
    license_flag_map = {
        'Proprietary': 1,
        'proprietary': 1,
        'Paid': 2,
        'paid': 2,
        'Public': 3,
        'public': 3
    }
    license_flag = license_flag_map.get(license, 0) if license else 0
    
    # Convert notify_type to before_after_class_flag (tinyint)
    # pre-reading = 1, post-reading = 2
    before_after_class_flag = 1 if notify_type == 'pre' else 2 if notify_type == 'post' else 0
    
    # Convert 0 → None so FK constraints aren't violated
    batch_id_val = academic_batch_id if academic_batch_id and academic_batch_id != 0 else None
    semester_id_val = semester_id if semester_id and semester_id != 0 else None
    course_id_val = course_id if course_id and course_id != 0 else None

    def _insert_material(f_name, f_url):
        db.execute(
            _text("""
                INSERT INTO lms_crs_material_upload
                    (document_name, file_name, docment_url, description,
                     academic_batch_id, semester_id, crs_id, section_ids,
                     topic_ids, created_by, created_date, update_cnt,
                     before_after_class_flag, license_flag)
                VALUES
                    (:document_name, :file_name, :docment_url, :description,
                     :academic_batch_id, :semester_id, :crs_id, :section_ids,
                     :topic_ids, :created_by, :created_date, 0,
                     :before_after_class_flag, :license_flag)
            """),
            {
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
                "before_after_class_flag": before_after_class_flag,
                "license_flag": license_flag
            }
        )

    # Handle URL-based materials
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
    sql = """
        SELECT
            m.mat_id,
            m.document_name,
            m.file_name,
            m.docment_url,
            m.description,
            m.topic_ids,
            m.section_ids,
            m.academic_batch_id,
            m.semester_id,
            m.crs_id,
            m.created_by,
            m.created_date,
            m.before_after_class_flag,
            m.license_flag,
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
    
    # Convert flags to readable values for frontend
    result = []
    for row in rows:
        row_dict = dict(row)
        
        # Convert license_flag to license string
        license_map = {1: 'Proprietary', 2: 'Paid', 3: 'Public'}
        row_dict['license'] = license_map.get(row_dict.get('license_flag', 0), '')
        
        # Convert before_after_class_flag to notify_type
        notify_map = {1: 'pre', 2: 'post'}
        row_dict['notify_type'] = notify_map.get(row_dict.get('before_after_class_flag', 0), '')
        
        result.append(row_dict)
    
    return result


class StudentListRequest(BaseModel):
    section_id: int
    academic_batch_id: int = 0
    semester_id: int = 0
    course_id: int = 0  # Make sure this exists

# @router.post("/student_list")
# def student_list(request: StudentListRequest, db: Session = Depends(get_db)):
#     # Look up the section label so we can filter iems_students by section name
#     section_row = db.execute(
#         text("SELECT section FROM iems_section WHERE id = :id LIMIT 1"),
#         {"id": request.section_id}
#     ).mappings().first()
#     section_label = section_row["section"] if section_row else None

#     query = "SELECT student_id, usno, name, first_name, last_name, section, current_semester, academic_batch_id FROM iems_students WHERE status = 1 AND IFNULL(delete_status, 0) = 0"
#     params = {}
#     if request.academic_batch_id and request.academic_batch_id != 0:
#         query += " AND academic_batch_id = :academic_batch_id"
#         params["academic_batch_id"] = request.academic_batch_id
#     if request.semester_id and request.semester_id != 0:
#         query += " AND current_semester = (SELECT semester FROM iems_semester WHERE semester_id = :semester_id LIMIT 1)"
#         params["semester_id"] = request.semester_id
#     if section_label:
#         query += " AND section = :section"
#         params["section"] = section_label
#     query += " ORDER BY student_id DESC"

#     rows = db.execute(text(query), params).mappings().all()
#     return {"data": [dict(r) for r in rows]}


@router.post("/student_list")
def student_list(request: StudentListRequest, db: Session = Depends(get_db)):
    try:
        print("\n========== STUDENT LIST API ==========")
        print("section_id:", request.section_id)
        print("academic_batch_id:", request.academic_batch_id)
        print("semester_id:", request.semester_id)
        print("course_id:", request.course_id)

        # Validate required parameters
        if not all([request.section_id, request.academic_batch_id, 
                   request.semester_id, request.course_id]):
            return {
                "success": False,
                "message": "All parameters are required",
                "data": []
            }

        # First verify the section exists in the mapping
        section_check = db.execute(
            text("""
                SELECT COUNT(*) as count 
                FROM cudos_map_courseto_student 
                WHERE academic_batch_id = :academic_batch_id
                    AND semester_id = :semester_id
                    AND crs_id = :course_id
                    AND section_id = :section_id
                LIMIT 1
            """),
            {
                "academic_batch_id": request.academic_batch_id,
                "semester_id": request.semester_id,
                "course_id": request.course_id,
                "section_id": request.section_id
            }
        ).mappings().first()

        if not section_check or section_check['count'] == 0:
            # Fallback: Try to get section from iems_section
            section_row = db.execute(
                text("SELECT section FROM iems_section WHERE id = :id LIMIT 1"),
                {"id": request.section_id}
            ).mappings().first()
            
            if section_row:
                section_label = section_row["section"]
                # Fallback query using iems_students
                query = """
                    SELECT 
                        student_id, 
                        usno, 
                        name, 
                        first_name, 
                        last_name, 
                        section, 
                        current_semester, 
                        academic_batch_id 
                    FROM iems_students 
                    WHERE status = 1 
                        AND IFNULL(delete_status, 0) = 0
                        AND academic_batch_id = :academic_batch_id
                        AND current_semester = :semester
                        AND section = :section
                    ORDER BY student_id DESC
                """
                params = {
                    "academic_batch_id": request.academic_batch_id,
                    "semester": request.semester_id,
                    "section": section_label
                }
                rows = db.execute(text(query), params).mappings().all()
                return {"data": [dict(r) for r in rows]}

        # Fetch students from cudos_map_courseto_student
        query = """
            SELECT DISTINCT
                s.student_id,
                s.usno,
                s.name,
                s.first_name,
                s.last_name,
                s.section,
                s.current_semester,
                s.academic_batch_id,
                mcs.crs_reg_flag,
                mcs.opel_crs_flag,
                mcs.mcstd_id
            FROM cudos_map_courseto_student mcs
            INNER JOIN iems_students s 
                ON s.student_id = mcs.student_id
                AND s.status = 1 
                AND IFNULL(s.delete_status, 0) = 0
            WHERE mcs.academic_batch_id = :academic_batch_id
                AND mcs.semester_id = :semester_id
                AND mcs.crs_id = :course_id
                AND mcs.section_id = :section_id
                AND (mcs.status = 1 OR mcs.status IS NULL)
            ORDER BY s.student_id DESC
        """
        
        params = {
            "academic_batch_id": request.academic_batch_id,
            "semester_id": request.semester_id,
            "course_id": request.course_id,
            "section_id": request.section_id
        }

        rows = db.execute(text(query), params).mappings().all()
        
        # Format response
        result = []
        for row in rows:
            student_data = dict(row)
            if not student_data.get('name'):
                first = student_data.get('first_name', '')
                last = student_data.get('last_name', '')
                student_data['name'] = f"{first} {last}".strip() or student_data.get('usno', '')
            result.append(student_data)

        print("Students found:", len(result))
        print("=====================================\n")

        return {"data": result}

    except Exception as e:
        import traceback
        print("\n========== STUDENT LIST ERROR ==========")
        print("Exception:", repr(e))
        traceback.print_exc()
        print("========================================\n")
        
        return {
            "success": False,
            "message": str(e),
            "data": []
        }

# @router.post("/share_material")
# def share_material(request: ShareMaterialRequest, db: Session = Depends(get_db)):

#     for student_usn in request.student_usns:

#         mapping = LMSMapShareMaterialsToStudent(
#             ssd_id=None,
#             mat_id=request.material_id,
#             academic_batch_id=request.academic_batch_id,
#             section_id=request.section_id,
#             student_usn=student_usn
#         )

#         db.add(mapping)

#     db.commit()

#     return {
#         "status": True,
#         "message": "Material shared successfully"
#     }

class ShareMaterialRequest(BaseModel):
    material_id: int
    academic_batch_id: int
    section_id: int
    student_ids: List[int]

@router.post("/share_material")
def share_material(request: ShareMaterialRequest, db: Session = Depends(get_db)):
    try:
        print("\n========== SHARE MATERIAL API ==========")
        print("Request:", request.dict())

        # Validate required parameters
        if not all([request.material_id, request.academic_batch_id, request.section_id]):
            return {
                "success": False,
                "message": "material_id, academic_batch_id, and section_id are required"
            }

        if not request.student_ids:
            return {
                "success": False,
                "message": "At least one student must be selected"
            }

        # Check if material exists
        material = db.execute(
            text("SELECT mat_id FROM lms_crs_material_upload WHERE mat_id = :id"),
            {"id": request.material_id}
        ).mappings().first()

        if not material:
            return {
                "success": False,
                "message": "Material not found"
            }

        # Verify section exists in cudos_master_type_details
        section = db.execute(
            text("SELECT mt_details_id FROM cudos_master_type_details WHERE mt_details_id = :id"),
            {"id": request.section_id}
        ).mappings().first()

        if not section:
            return {
                "success": False,
                "message": f"Section with ID {request.section_id} not found"
            }

        # Get existing student_ids for this material
        existing_students = db.execute(
            text("""
                SELECT ssd_id 
                FROM lms_map_share_materials_to_student 
                WHERE mat_id = :material_id 
                AND academic_batch_id = :academic_batch_id
                AND section_id = :section_id
            """),
            {
                "material_id": request.material_id,
                "academic_batch_id": request.academic_batch_id,
                "section_id": request.section_id
            }
        ).mappings().all()

        existing_student_ids = {row["ssd_id"] for row in existing_students}
        print(f"Existing student IDs: {existing_student_ids}")

        # Filter out students that are already mapped
        new_student_ids = [sid for sid in request.student_ids if sid not in existing_student_ids]
        print(f"New student IDs to insert: {new_student_ids}")

        if not new_student_ids:
            return {
                "success": True,
                "message": "All selected students are already mapped to this material",
                "data": {
                    "total_students": len(request.student_ids),
                    "existing_count": len(existing_student_ids),
                    "new_count": 0
                }
            }

        # Get student details for the new student IDs - FIXED VERSION
        # Build the IN clause with proper parameter binding
        placeholders = ', '.join([f':id_{i}' for i in range(len(new_student_ids))])
        params = {f'id_{i}': value for i, value in enumerate(new_student_ids)}
        
        query = text(f"""
            SELECT student_id, usno, name, first_name, last_name
            FROM iems_students 
            WHERE student_id IN ({placeholders})
            AND status = 1 
            AND IFNULL(delete_status, 0) = 0
        """)
        
        students = db.execute(query, params).mappings().all()

        if not students:
            return {
                "success": False,
                "message": "No valid students found"
            }

        # Insert new mappings only for students that don't already exist
        inserted_count = 0
        for student in students:
            # Insert new mapping
            db.execute(
                text("""
                    INSERT INTO lms_map_share_materials_to_student 
                    (ssd_id, mat_id, academic_batch_id, section_id, student_usn)
                    VALUES (:ssd_id, :mat_id, :academic_batch_id, :section_id, :student_usn)
                """),
                {
                    "ssd_id": student["student_id"],
                    "mat_id": request.material_id,
                    "academic_batch_id": request.academic_batch_id,
                    "section_id": request.section_id,
                    "student_usn": student["usno"]
                }
            )
            inserted_count += 1

        db.commit()
        print(f"Inserted {inserted_count} new mappings")
        print("=====================================\n")

        return {
            "success": True,
            "message": f"Material shared successfully with {inserted_count} new students",
            "data": {
                "total_students": len(request.student_ids),
                "existing_count": len(existing_student_ids),
                "new_count": inserted_count
            }
        }

    except Exception as e:
        import traceback
        print("\n========== SHARE MATERIAL ERROR ==========")
        print("Exception:", repr(e))
        traceback.print_exc()
        print("========================================\n")
        db.rollback()
        return {
            "success": False,
            "message": str(e)
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
    notify_type: str = Form(None),
    db: Session = Depends(get_db)
):
    # Convert license string to license_flag
    license_flag_map = {
        'Proprietary': 1,
        'proprietary': 1,
        'Paid': 2,
        'paid': 2,
        'Public': 3,
        'public': 3
    }
    license_flag = license_flag_map.get(license, 0) if license else 0
    
    # Convert notify_type to before_after_class_flag
    before_after_class_flag = 1 if notify_type == 'pre' else 2 if notify_type == 'post' else 0

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

    db.execute(
        text("""
            UPDATE lms_crs_material_upload 
            SET document_name = :title,
                description = :desc,
                file_name = :file_name,
                docment_url = :url,
                section_ids = COALESCE(:section_id, section_ids),
                topic_ids = COALESCE(:topic_id, topic_ids),
                license_flag = COALESCE(:license_flag, license_flag),
                before_after_class_flag = COALESCE(:before_after_class_flag, before_after_class_flag),
                update_cnt = update_cnt + 1,
                modified_date = NOW()
            WHERE mat_id = :id
        """),
        {
            "title": title,
            "desc": description,
            "file_name": file_name_val,
            "url": file_path_val,
            "section_id": section_id,
            "topic_id": topic_id,
            "license_flag": license_flag if license else None,
            "before_after_class_flag": before_after_class_flag if notify_type else None,
            "id": material_id
        }
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

# @router.post("/material_mapping_list")
# def material_mapping_list(request: MaterialMappingRequest, db: Session = Depends(get_db)):

#     mappings = db.query(LMSMapShareMaterialsToStudent).filter(
#         LMSMapShareMaterialsToStudent.mat_id == request.material_id
#     ).all()

#     result = []

#     for m in mappings:
#         # Look up student name from iems_students table (usno column)
#         student_row = db.execute(
#             text("SELECT name, first_name, last_name FROM iems_students WHERE usno = :usno LIMIT 1"),
#             {"usno": m.student_usn}
#         ).mappings().first()

#         if student_row:
#             first = student_row.get("first_name") or ""
#             last  = student_row.get("last_name")  or ""
#             name  = f"{first} {last}".strip() or student_row.get("name") or m.student_usn
#         else:
#             name = m.student_usn

#         result.append({
#             "student_usn": m.student_usn,
#             "student_name": name,
#             "section_id": m.section_id
#         })

#     return result

@router.post("/material_mapping_list")
def material_mapping_list(request: MaterialMappingRequest, db: Session = Depends(get_db)):
    try:
        print("\n========== MATERIAL MAPPING LIST ==========")
        print("material_id:", request.material_id)

        # First, check if the material exists
        material = db.execute(
            text("SELECT mat_id, document_name FROM lms_crs_material_upload WHERE mat_id = :id"),
            {"id": request.material_id}
        ).mappings().first()

        if not material:
            return {
                "success": False,
                "message": "Material not found",
                "data": []
            }

        print(f"Material found: {material['document_name']}")

        # Query to get all students mapped to this material
        mappings = db.execute(
            text("""
                SELECT 
                    msm.material_student_map_id,
                    msm.ssd_id,
                    msm.mat_id,
                    msm.academic_batch_id,
                    msm.section_id,
                    msm.student_usn,
                    s.name,
                    s.first_name,
                    s.last_name,
                    s.usno,
                    s.section as student_section,
                    mtd.mt_details_name as section_name
                FROM lms_map_share_materials_to_student msm
                LEFT JOIN iems_students s ON s.student_id = msm.ssd_id
                LEFT JOIN cudos_master_type_details mtd ON mtd.mt_details_id = msm.section_id
                WHERE msm.mat_id = :material_id
                ORDER BY msm.material_student_map_id DESC
            """),
            {"material_id": request.material_id}
        ).mappings().all()

        print(f"Found {len(mappings)} mappings")

        # Format the response
        result = []
        for m in mappings:
            # Build student name from first_name and last_name
            first = m.get("first_name") or ""
            last = m.get("last_name") or ""
            name = f"{first} {last}".strip()
            
            # If name is empty, use the name field or USN
            if not name:
                name = m.get("name") or m.get("student_usn") or m.get("usno") or "Unknown"
            
            result.append({
                "student_usn": m.get("student_usn") or m.get("usno") or "",
                "student_name": name,
                "student_id": m.get("ssd_id"),
                "section_id": m.get("section_id"),
                "section_name": m.get("section_name", ""),
                "student_section": m.get("student_section", "")
            })

        print(f"Returning {len(result)} students")
        print("=====================================\n")

        return {
            "success": True,
            "message": f"Found {len(result)} students mapped to this material",
            "data": result
        }

    except Exception as e:
        import traceback
        print("\n========== MATERIAL MAPPING LIST ERROR ==========")
        print("Exception:", repr(e))
        traceback.print_exc()
        print("========================================\n")
        return {
            "success": False,
            "message": str(e),
            "data": []
        }