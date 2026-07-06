from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # 1. Insert Dummy Student
    print("Inserting dummy student...")
    conn.execute(text("""
        INSERT INTO erp_student (first_name, last_name, erp_student_usn, email_id, status)
        VALUES ('John', 'Doe', '1XX20CS001', 'johndoe@test.com', 1)
    """))
    student_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    
    # 2. Insert Mentor Group Term for batch 10
    print("Inserting mentor group terms...")
    conn.execute(text("""
        INSERT INTO lms_mentors_group_terms (academic_batch_id)
        VALUES (10)
    """))
    mgt_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    
    # 3. Assign Mentor (User ID 1) to the Group Term
    print("Inserting group mentor...")
    conn.execute(text(f"""
        INSERT INTO lms_group_mentors (mentors_group_terms_id, mentor_id)
        VALUES ({mgt_id}, 1)
    """))
    gm_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    
    # 4. Assign Student to Mentor
    print("Inserting group mentee...")
    conn.execute(text(f"""
        INSERT INTO lms_group_mentees (group_mentor_id, student_id)
        VALUES ({gm_id}, {student_id})
    """))
    
    conn.commit()
    print(f"\\n✅ DUMMY DATA SEEDED SUCCESSFULLY! \\nCurriculum ID (Academic Batch ID) to test with is: 10")
