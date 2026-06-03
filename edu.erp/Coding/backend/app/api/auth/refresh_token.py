from fastapi import APIRouter

router = APIRouter()

@router.post("/refresh-token/")
def refresh_token():
    return {"message": "Token refreshed"}
