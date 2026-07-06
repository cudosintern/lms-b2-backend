import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ----------------------------------------------------------------------
# Project root (backend) – adjust if the folder moves
# ----------------------------------------------------------------------
project_root = r"C:/Users/3win/Downloads/lms-b2-backend-main (1)/lms-b2-backend-main/edu.erp/Coding/backend"
sys.path.append(project_root)

# Import the Base and model definitions
from app.db.models import IEMSDepartment, Base

# ----------------------------------------------------------------------
# Engine configuration – reuse the same DB URL the app uses.
# The default URL is stored in the .env file (look for SQLALCHEMY_DATABASE_URL)
# ----------------------------------------------------------------------
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(project_root, ".env"))
db_url = os.getenv("SQLALCHEMY_DATABASE_URL")
if not db_url:
    raise RuntimeError("SQLALCHEMY_DATABASE_URL not found in .env")

engine = create_engine(db_url, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ----------------------------------------------------------------------
# Insert department 72
# ----------------------------------------------------------------------
def insert_department():
    dept_id = 72
    dept_name = "string"
    dept_acronym = "string"
    dept_code_usn = "string"
    dept_description = "string"
    status = True

    with SessionLocal() as db:
        # Ensure tables exist (no‑op if already created)
        Base.metadata.create_all(bind=engine)

        existing = db.query(IEMSDepartment).filter_by(dept_id=dept_id).first()
        if existing:
            print(f"Department {dept_id} already exists: {existing.dept_name}")
            return

        dept = IEMSDepartment(
            dept_id=dept_id,
            dept_name=dept_name,
            dept_acronym=dept_acronym,
            dept_code_usn=dept_code_usn,
            dept_description=dept_description,
            status=status,
        )
        db.add(dept)
        db.commit()
        print(f"Inserted department {dept_id}: {dept_name}")

if __name__ == "__main__":
    insert_department()
