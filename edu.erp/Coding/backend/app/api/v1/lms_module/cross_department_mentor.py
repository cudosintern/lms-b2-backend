from fastapi import APIRouter, Depends
from app.utils.auth_helper import get_current_user

router = APIRouter()

@router.get("/list")
def list_cross_department_mentor(
    current_user: dict = Depends(get_current_user)
):
    return {"message": "List Cross Department Mentors"}

@router.get("/available-mentors")
def available_mentors(
    current_user: dict = Depends(get_current_user)
):
    return {"message": "Available Mentors"}

@router.post("/save")
def save_cross_department_mentor(
    current_user: dict = Depends(get_current_user)
):
    return {"message": "Cross Department Mentor Added"}

@router.put("/update/{id}")
def update_cross_department_mentor(
    id: int,
    current_user: dict = Depends(get_current_user)
):
    return {"message": f"Updated Mentor {id}"}

@router.delete("/delete/{id}")
def delete_cross_department_mentor(
    id: int,
    current_user: dict = Depends(get_current_user)
):
    return {"message": f"Deleted Mentor {id}"}
print("CROSS DEPARTMENT MENTOR LOADED")
