from app.core.database import engine
from sqlalchemy import text

users_to_insert = [
    ('cse_fac1', '', 'cse_fac1@demo.com', 1, 'Amit',     'Kumar', 71),
    ('gen_fac1', '', 'gen_fac1@demo.com', 1, 'Priya',    'Sharma', 72),
    ('ece_fac1', '', 'ece_fac1@demo.com', 1, 'Rakesh',   'Patil', 73),
    ('bio_fac1', '', 'bio_fac1@demo.com', 1, 'Sneha',    'Rao', 75),
    ('inst_fac1','', 'inst_fac1@demo.com',1, 'Kiran',    'Joshi', 77),
    ('mech_fac1','', 'mech_fac1@demo.com',1, 'Vijay',    'Naik', 79),
    ('ipe_fac1', '', 'ipe_fac1@demo.com', 1, 'Anita',    'Shetty', 81),
    ('eee_fac1', '', 'eee_fac1@demo.com', 1, 'Mahesh',   'Kulkarni', 82),
    ('arch_fac1','', 'arch_fac1@demo.com',1, 'Deepa',    'Nair', 83)
]

with engine.connect() as conn:
    try:
        for u in users_to_insert:
            username, pwd, email, active, fname, lname, dept_id = u
            
            # Check if user exists
            existing = conn.execute(text("SELECT erp_user_id FROM erp_users WHERE username = :u"), {"u": username}).fetchone()
            if existing:
                print(f"User {username} already exists, skipping insert.")
                user_id = existing[0]
            else:
                # Insert into erp_users
                conn.execute(text("""
                    INSERT INTO erp_users (username, password, email_id, user_active, first_name, last_name, full_name, status)
                    VALUES (:uname, :pwd, :email, :act, :fname, :lname, :full, 1)
                """), {
                    "uname": username, "pwd": pwd, "email": email, "act": active, 
                    "fname": fname, "lname": lname, "full": f"{fname} {lname}"
                })
                user_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                
            # Check if department mapping exists
            mapping = conn.execute(text("""
                SELECT erp_user_id FROM erp_rbac_user_department 
                WHERE erp_user_id = :uid AND erp_dept_id = :did
            """), {"uid": user_id, "did": dept_id}).fetchone()
            
            if not mapping:
                conn.execute(text("""
                    INSERT INTO erp_rbac_user_department (erp_user_id, erp_dept_id, status)
                    VALUES (:uid, :did, 1)
                """), {"uid": user_id, "did": dept_id})
                
        conn.commit()
        print("All users successfully inserted into erp_users and erp_rbac_user_department!")
    except Exception as e:
        print("Error inserting data:", e)
