from fastapi import APIRouter

router = APIRouter()

@router.post("/register/")
def register():
    return {"message": "User registered"}
