from app.core.database import engine
from sqlalchemy import text

print("--- Valid Mapping IDs (cross_dept_id) ---")
with engine.connect() as conn:
    mappings = conn.execute(text("SELECT cross_dept_id, faculty_user_id, to_dept_id FROM lms_cross_dept_users LIMIT 5")).fetchall()
    if not mappings:
        print("No mappings found! You need to run the POST /add endpoint first to create a mapping.")
    for m in mappings:
        print(f"Mapping ID: {m[0]} (Mentor: {m[1]}, To Dept: {m[2]})")
