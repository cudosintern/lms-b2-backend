import uuid
from sqlalchemy import text
from app.core.database import SessionLocal

db = SessionLocal()

users = [
    ('cse_fac1', '', 'cse_fac1@demo.com', 1, 'Amit',     'Kumar', 1, 'F', 71, 71, 1, 1),
    ('gen_fac1', '', 'gen_fac1@demo.com', 1, 'Priya',    'Sharma', 1, 'F', 72, 72, 1, 1),
    ('ece_fac1', '', 'ece_fac1@demo.com', 1, 'Rakesh',   'Patil', 1, 'F', 73, 73, 1, 1),
    ('bio_fac1', '', 'bio_fac1@demo.com', 1, 'Sneha',    'Rao', 1, 'F', 75, 75, 1, 1),
    ('inst_fac1','', 'inst_fac1@demo.com',1, 'Kiran',    'Joshi', 1, 'F', 77, 77, 1, 1),
    ('mech_fac1','', 'mech_fac1@demo.com',1, 'Vijay',    'Naik', 1, 'F', 79, 79, 1, 1),
    ('ipe_fac1', '', 'ipe_fac1@demo.com', 1, 'Anita',    'Shetty', 1, 'F', 81, 81, 1, 1),
    ('eee_fac1', '', 'eee_fac1@demo.com', 1, 'Mahesh',   'Kulkarni', 1, 'F', 82, 82, 1, 1),
    ('arch_fac1','', 'arch_fac1@demo.com',1, 'Deepa',    'Nair', 1, 'F', 83, 83, 1, 1),
    ('auto_fac1','', 'auto_fac1@demo.com',1, 'Suresh',   'Hegde', 1, 'F', 85, 85, 1, 1)
]

try:
    for u in users:
        username = u[0]
        email = u[2]
        first_name = u[4]
        last_name = u[5]
        dept_id = u[8]
        
        # Check if user already exists
        existing = db.execute(text("SELECT erp_user_id FROM erp_users WHERE username = :username"), {"username": username}).fetchone()
        if existing:
            print(f"User {username} already exists, skipping.")
            continue
            
        unqkey = str(uuid.uuid4())
        
        insert_user_sql = """
            INSERT INTO erp_users 
            (erp_users_unqkey, username, password, email_id, first_name, last_name, status, user_active, create_date) 
            VALUES (:unq, :user, :pw, :email, :fn, :ln, 1, 1, NOW())
        """
        db.execute(text(insert_user_sql), {
            "unq": unqkey,
            "user": username,
            "pw": "",
            "email": email,
            "fn": first_name,
            "ln": last_name
        })
        
        # Get the new user ID
        new_user = db.execute(text("SELECT erp_user_id FROM erp_users WHERE username = :username"), {"username": username}).fetchone()
        new_user_id = new_user[0]
        
        dept_unq = str(uuid.uuid4())
        
        # Insert into erp_rbac_user_department
        insert_dept_sql = """
            INSERT INTO erp_rbac_user_department
            (erp_userdept_unqkey, erp_user_id, erp_dept_id, status)
            VALUES (:unq, :uid, :did, 1)
        """
        db.execute(text(insert_dept_sql), {
            "unq": dept_unq,
            "uid": new_user_id,
            "did": dept_id
        })
        
    db.commit()
    print("All users successfully inserted into erp_users and mapped to their departments!")
except Exception as e:
    db.rollback()
    print("Error:", e)
finally:
    db.close()
