from fastapi import FastAPI
from app.api.v1.routes import router as api_router
from fastapi.middleware.cors import CORSMiddleware
from app.db.models import Base
from app.core.database import engine
# Disabled auto table creation - database schema is already finalized in HeidiSQL
# Base.metadata.create_all(bind=engine)

from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

origins = [
    "http://localhost:3000",  # React frontend URL
    "http://10.91.0.213:3001",  # UAT React frontend URL
]
origins = [
    # "http://localhost:3000",    # Your React Frontend
    "http://localhost:8000",    # Your Swagger UI
#     "http://127.0.0.1:8000",    # Alternative Backend URL
#     "*"                         # Allow ALL (Use with caution in production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://192.168.56.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(api_router)
# Preserve existing unprefixed routes while exposing the versioned paths used by the frontend.
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to IonCudos-LMS Interns API"}


# @app.get("/")
# def read_root():
#     return {"Hello": "World"}
