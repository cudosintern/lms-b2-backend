from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# -------------------- ROUTERS --------------------
from app.api.v1.routes import router as api_router
from app.api.v1.lms_module.department import router as department_router
from app.api.v1.lms_module.config_type import router as config_type_router
from app.api.v1.cudo_module.bloom_level.bloom_level import router as bloom_level_router
from app.api.v1.lms_module.cross_department_mentor import router as cross_dept_router
from app.api.v1.lms_module.mentoring import router as mentoring_router
from app.api.v1.lms_module.mentor_mentee_details import router as mentor_mentee_details_router

# -------------------- DB --------------------
from app.core.database import get_db

app = FastAPI(
    title="LMS API",
    version="1.0.0"
)

# -------------------- CORS --------------------
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- ROUTER REGISTRATION --------------------

app.include_router(api_router, prefix="/api/v1", tags=["Common APIs"])

app.include_router(
    department_router,
    prefix="/api/v1/department",
    tags=["Department"]
)

app.include_router(
    config_type_router,
    prefix="/api/v1/config-type",
    tags=["Config Type"]
)

app.include_router(
    bloom_level_router,
    prefix="/api/v1/cudo-module",
    tags=["Bloom Level"]
)

app.include_router(
    cross_dept_router,
    prefix="/api/v1/cross-mentor",
    tags=["Cross Department Mentor"]
)

app.include_router(
    mentoring_router,
    prefix="/api/v1/mentoring",
    tags=["Mentoring"]
)

app.include_router(
    mentor_mentee_details_router,
    prefix="/api/v1/mentor-mentee",
    tags=["Mentor Mentee"]
)

# -------------------- HEALTH CHECK --------------------
@app.get("/")
def root():
    return {"message": "LMS Backend is running 🚀"}

@app.get("/db-test")
def db_test(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "database connected 🚀"}
    except Exception as e:
        return {"status": "error", "message": str(e)}