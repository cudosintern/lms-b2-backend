from pydantic import BaseModel, Field


class StudentRequest(BaseModel):
    student_id: int = Field(..., gt=0)
