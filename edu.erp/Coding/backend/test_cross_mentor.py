from app.core.database import engine
from sqlalchemy import text

sql = """
    SELECT m.cross_dept_id AS mapping_id, u.erp_user_id AS mentor_id, u.first_name, u.last_name, u.email_id AS email, 
           d.dept_id AS home_dept_id, d.dept_name AS home_dept_name, 1 AS status
    FROM lms_cross_dept_users m
    JOIN erp_users u ON m.faculty_user_id = u.erp_user_id
    JOIN erp_rbac_user_department ud ON u.erp_user_id = ud.erp_user_id AND ud.status = 1
    JOIN iems_department d ON ud.erp_dept_id = d.dept_id
    WHERE m.to_dept_id = 1
"""
params = {"logged_in_dept": 1}
dept_id = 71
if dept_id is not None:
    sql += " AND ud.erp_dept_id = :dept_id"
    params["dept_id"] = dept_id

with engine.connect() as conn:
    try:
        res = conn.execute(text(sql), params).mappings().all()
        print("Success!", res)
    except Exception as e:
        print("Error:", e)
