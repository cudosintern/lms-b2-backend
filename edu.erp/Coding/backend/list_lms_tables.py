from app.core.database import engine
from sqlalchemy import text

print("LMS Tables:")
with engine.connect() as conn:
    tables = conn.execute(text("SHOW TABLES LIKE 'lms_%'")).fetchall()
    for t in tables:
        print(t[0])
