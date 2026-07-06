from app.core.database import engine
from sqlalchemy import text
from pprint import pprint

print("--- Testing Cross Department Mentor APIs ---")

with engine.connect() as conn:
    print("\n1. GET /from-other-departments")
    sql1 = """
        SELECT m.cross_dept_id AS mapping_id, u.erp_user_id AS mentor_id, u.first_name, u.last_name, u.email_id AS email, 
               d.dept_id AS home_dept_id, d.dept_name AS home_dept_name, 1 AS status
        FROM lms_cross_dept_users m
        JOIN erp_users u ON m.faculty_user_id = u.erp_user_id
        JOIN erp_rbac_user_department ud ON u.erp_user_id = ud.erp_user_id AND ud.status = 1
        JOIN iems_department d ON ud.erp_dept_id = d.dept_id
        WHERE m.to_dept_id = 71
    """
    res1 = conn.execute(text(sql1)).mappings().all()
    print("Found:", len(res1), "records")
    
    print("\n2. GET /from-other-departments (with filter dept_id=73)")
    sql2 = sql1 + " AND m.from_dept_id = 73"
    res2 = conn.execute(text(sql2)).mappings().all()
    print("Found:", len(res2), "records")
    if res2:
        print("Sample:", dict(res2[0]))

    print("\n3. GET /to-other-departments")
    sql3 = """
        SELECT m.cross_dept_id AS mapping_id, u.erp_user_id AS mentor_id, u.first_name, u.last_name, u.email_id AS email, 
               d.dept_id AS mapped_dept_id, d.dept_name AS mapped_dept_name, 1 AS status
        FROM lms_cross_dept_users m
        JOIN erp_users u ON m.faculty_user_id = u.erp_user_id
        JOIN iems_department d ON m.to_dept_id = d.dept_id
        WHERE m.from_dept_id = 73
    """
    res3 = conn.execute(text(sql3)).mappings().all()
    print("Found:", len(res3), "records")
    if res3:
        print("Sample:", dict(res3[0]))

    print("\n4. GET /available-mentors")
    sql4 = """
        SELECT u.erp_user_id AS mentor_id, u.first_name, u.last_name, u.email_id AS email, 
               d.dept_id AS home_dept_id, d.dept_name AS home_dept_name
        FROM erp_users u
        JOIN erp_rbac_user_department ud ON u.erp_user_id = ud.erp_user_id AND ud.status = 1
        JOIN iems_department d ON ud.erp_dept_id = d.dept_id
        WHERE ud.erp_dept_id != 71
          AND u.erp_user_id NOT IN (
              SELECT faculty_user_id FROM lms_cross_dept_users WHERE to_dept_id = 71
          )
        LIMIT 3
    """
    res4 = conn.execute(text(sql4)).mappings().all()
    print("Found:", len(res4), "records (limited to 3)")

print("\nAll queries executed successfully without SQL syntax errors!")
