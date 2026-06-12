from fastapi import APIRouter

router = APIRouter()
print("CONFIG TYPE LOADED")

@router.get("/list")
def list_config_type():
    return {"message": "List API Working"}

@router.post("/save")
def save_config_type():
    return {"message": "Save API Working"}

@router.put("/update/{id}")
def update_config_type(id: int):
    return {"message": f"Updated {id}"}

@router.delete("/delete/{id}")
def delete_config_type(id: int):
    return {"message": f"Deleted {id}"}

@router.get("/export-pdf")
def export_pdf():
    return {"message": "PDF Export Working"}