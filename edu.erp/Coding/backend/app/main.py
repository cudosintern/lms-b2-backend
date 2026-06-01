from fastapi import FastAPI
from .api.v1.routes import router as api_router
from fastapi.middleware.cors import CORSMiddleware
from .db.models import Base
from .core.database import engine
from app.api.v1.cudo_module.bloom_level import bloom_level as bloom_level_routes

# Disabled auto table creation - database schema is already finalized in HeidiSQL
# Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:3000",  # React frontend URL
    "http://10.91.0.213:3001",  # UAT React frontend URL
]
origins = [
    "http://localhost:3000",    # Your React Frontend
    "http://localhost:8000",    # Your Swagger UI
    "http://127.0.0.1:8000",    # Alternative Backend URL
    "*"                         # Allow ALL (Use with caution in production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(api_router)

app.include_router(
    bloom_level_routes.router,
    prefix="/api/v1/cudo_module", 
    tags=["Bloom Level"]
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to IonCudos API"}

@app.get("/")
def read_root():
    return {"Hello": "World"}