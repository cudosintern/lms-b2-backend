from app.core.database import engine
from sqlalchemy import text

print("--- Valid Mentor IDs ---")
with engine.connect() as conn:
    users = conn.execute(text("SELECT erp_user_id, first_name FROM erp_users LIMIT 5")).fetchall()
    for u in users:
        print(f"Mentor ID: {u[0]}, Name: {u[1]}")
        
print("\n--- Valid Academic Batch IDs ---")
with engine.connect() as conn:
    batches = conn.execute(text("SELECT academic_batch_id, academic_batch_code FROM iems_academic_batch LIMIT 5")).fetchall()
    for b in batches:
        print(f"Batch ID: {b[0]}, Code: {b[1]}")
