from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.core.database import get_db
from app.utils.auth_helper import get_current_user

router = APIRouter()

@router.get("/list")
def get_curriculum_list(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    sql = """
        SELECT 
            p.pgm_title AS program_name,
            ab.academic_batch_id AS curriculum_id,
            ab.academic_batch_code AS curriculum_name,
            d.dept_acronym AS department,
            ab.start_year AS from_year,
            ab.end_year AS to_year,
            u.full_name AS program_owner,
            ab.po_matrix_flag AS peo_po_creation_status
        FROM iems_academic_batch ab
        LEFT JOIN iems_program p ON ab.pgm_id = p.pgm_id
        LEFT JOIN iems_department d ON ab.dept_id = d.dept_id
        LEFT JOIN erp_users u ON ab.academic_batch_owner = u.erp_user_id
        WHERE ab.status = 1
        ORDER BY p.pgm_title, ab.start_year DESC
    """
    results = db.execute(text(sql)).mappings().all()

    # Format the status flag appropriately for the frontend
    formatted_results = []
    for row in results:
        data = dict(row)
        flag = data.get("peo_po_creation_status")
        if flag == 1:
            data["peo_po_creation_status"] = "Initiated"
        else:
            data["peo_po_creation_status"] = "Not Initiated"
        
        # Ensure owner string is clean
        if not data["program_owner"]:
            data["program_owner"] = "N/A"
            
        formatted_results.append(data)

    return {"status": "success", "data": formatted_results}
