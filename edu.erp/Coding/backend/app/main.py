from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.routes import router as api_router
from .core.database import engine
from .db.models import Base
from app.api.v1.cudo_module.bloom_level import bloom_level as bloom_level_routes

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://10.91.0.213:3001",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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