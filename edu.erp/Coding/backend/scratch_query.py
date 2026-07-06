from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("--- Departments ---")
    depts = db.execute(text("SELECT dept_id, dept_name, dept_acronym FROM iems_department")).fetchall()
    for d in depts:
        print(d)

    print("\n--- Programs ---")
    pgms = db.execute(text("SELECT pgm_id, pgm_title, dept_id FROM iems_program")).fetchall()
    for p in pgms:
        print(p)

    print("\n--- Academic Batches (Curriculum) ---")
    batches = db.execute(text("SELECT academic_batch_id, academic_batch_code, dept_id, pgm_id FROM iems_academic_batch")).fetchall()
    for b in batches:
        print(b)

    print("\n--- Mentors Group Terms ---")
    mgt = db.execute(text("SELECT mentors_group_terms_id, academic_batch_id, semester_id FROM lms_mentors_group_terms")).fetchall()
    for m in mgt:
        print(m)

    print("\n--- Group Mentors ---")
    gm = db.execute(text("SELECT group_mentor_id, mentors_group_terms_id, mentor_id FROM lms_group_mentors")).fetchall()
    for g in gm:
        print(g)

    print("\n--- Group Mentees ---")
    gme = db.execute(text("SELECT group_mentee_id, group_mentor_id, student_id FROM lms_group_mentees")).fetchall()
    for ge in gme:
        print(ge)

except Exception as e:
    print("Error:", e)
finally:
    db.close()
